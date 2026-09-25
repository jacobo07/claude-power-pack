#!/usr/bin/env python3
"""Unit B's executable: fire a BOUNDED batch of goals at the pinned local model.

This is the thing the K-ADOS A-01 amendment was written for, so it is built to
the six conditions that amendment enforces rather than to a comment claiming it.

  1. It cannot reach production. It holds no Pterodactyl credential, no server
     path and no command channel; its unit's ReadWritePaths are the ledger and
     the goals tree, and nothing else on the host is writable to it.
  2. It is metered. Every firing consults the one ledger implementation before
     doing anything, and the provider consults it again per call. Neither
     reimplements the budget.
  3. Two kill switches, one of which stops a run already in flight: the
     environment variable KEOS_QWEN_DISABLED for a firing that has not begun,
     and the DISABLED flag file for one that has -- this loop re-decides before
     EVERY goal, so dropping the flag file stops the batch mid-flight.
  4. Bounded per firing: MAX_PER_FIRE goals, one attempt each, each attempt
     under a wall-clock timeout, with the unit holding an outer timeout too.
  5. Fails closed. A ledger that cannot be read, a goal that cannot be parsed
     and an exit code we have not seen all refuse. None of them proceeds.
  6. It leaves evidence: one durable record per attempt, carrying what was
     asked, what came back, where it came from, and the identity of the
     environment that produced it.

Three outcomes, never two:
  exit 0  OK          the batch ran, or there was honestly nothing to do
  exit 2  REFUSED     the ledger said no, or a precondition was absent. Nothing
                      is claimed about the model and nothing was spent.
  exit 1  FAILED      a step ran and failed; see the named step.

WHY REPEATED ATTEMPTS AT ONE PROMPT ARE THE POINT, not waste. A goal is not
retired on its first answer. It is asked once per firing until max_attempts is
reached, because the question this corpus has to answer is whether a failure
REPLICATES. The one real measurement taken so far says that matters: a failure
characterised from n=1 as "violates explicit constraints silently" occurred 1/5
at n=5 -- stochastic, not systematic -- while the bare `import judge` failure
reproduced 5/5. Those two need different fixes, and only repetition tells them
apart.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

# ---- SCOPE AS CONSTANTS -----------------------------------------------------
ROOT = Path(os.environ.get("KEOS_QWEN_ROOT", "/home/kobii/keos"))
PKG = ROOT / "keos_qwen"
GOALS = ROOT / "goals"
QUEUE = GOALS / "queue"
EVIDENCE = GOALS / "evidence"
DONE = GOALS / "done"
ATTEMPT_EXS = PKG / "goals" / "attempt.exs"

MAX_PER_FIRE = 3
DEFAULT_MAX_ATTEMPTS = 3
ATTEMPT_TIMEOUT_S = 300
MAX_TEXT_CHARS = 100_000
SENTINEL = "KEOSQ_ATTEMPT "

EXIT_OK, EXIT_FAILED, EXIT_REFUSED = 0, 1, 2
# -----------------------------------------------------------------------------

# The package is `keos_qwen` where it is DEPLOYED (/home/kobii/keos/keos_qwen)
# and `modules.keos_qwen` where it is DEVELOPED (the power-pack repo). Both are
# tried, because a file whose gate cannot import it is a file whose gate proves
# nothing -- and the deployment layout is not the repo layout here: the repo's
# `svc/` is deployed as `keos_qwen_svc/`, which is exactly the kind of drift
# that makes an inferred path wrong.
sys.path.insert(0, str(ROOT))
_HERE = Path(__file__).resolve()
sys.path.insert(0, str(_HERE.parents[2]))  # repo: .../modules
sys.path.insert(0, str(_HERE.parents[3]))  # repo: .../claude-power-pack

_import_errors = []
for _pkg in ("keos_qwen", "modules.keos_qwen"):
    try:
        _outcome = __import__(f"{_pkg}.outcome", fromlist=["outcome"])
        _ledger_mod = __import__(f"{_pkg}.ledger.ledger", fromlist=["ledger"])
        break
    except Exception as exc:  # noqa: BLE001 - every failure shape is a precondition
        _import_errors.append(f"{_pkg}: {exc!r}")
        _outcome = _ledger_mod = None

if _outcome is None or _ledger_mod is None:
    # A precondition of the whole file, asserted rather than assumed. If the
    # package does not import, this run has measured NOTHING about any model,
    # and saying so is the only honest exit.
    print("PRECONDITION: keos_qwen is not importable. " + " | ".join(_import_errors))
    sys.exit(EXIT_REFUSED)

OUTCOMES = _outcome.ALL
OK, UNAVAILABLE, HARNESS_FAILED = _outcome.OK, _outcome.UNAVAILABLE, _outcome.HARNESS_FAILED
worst = _outcome.worst
ledger = _ledger_mod


def say(msg: str) -> None:
    print(msg, flush=True)


def utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha256_file(p: Path) -> str:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return "unreadable"


def write_json_atomic(path: Path, payload: dict) -> None:
    """Encode first, then replace.

    `open(path, "w")` truncates BEFORE encoding, so a UnicodeEncodeError leaves a
    zero-byte file where evidence used to be. Encoding to bytes first means a
    failure destroys nothing.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=True, indent=2).encode("utf-8")
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def load_goal(path: Path) -> dict:
    """Parse one goal, refusing anything we cannot read as a goal.

    A malformed goal is REFUSED rather than repaired. Guessing an id from a
    filename or a prompt from a partial parse would put a question the Owner
    never asked into a corpus that exists to be trusted.
    """
    raw = path.read_text(encoding="utf-8")
    obj = json.loads(raw)
    if not isinstance(obj, dict):
        raise ValueError("a goal must be a JSON object")
    gid = obj.get("id")
    prompt = obj.get("prompt")
    if not isinstance(gid, str) or not gid.strip():
        raise ValueError("a goal needs a non-empty string 'id'")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("a goal needs a non-empty string 'prompt'")
    ma = obj.get("max_attempts", DEFAULT_MAX_ATTEMPTS)
    if not isinstance(ma, int) or ma < 1:
        raise ValueError("'max_attempts' must be an integer >= 1")
    obj["attempts"] = int(obj.get("attempts", 0))
    obj["max_attempts"] = ma
    return obj


def parse_attempt_line(stdout: str, stderr: str) -> dict:
    """Find the ONE sentinel line among the harness's diagnostics.

    Measured: a single call interleaves Exqlite connection errors, a
    ToolRegistry banner and two Router debug lines with the answer. Reading the
    last line, or the first thing shaped like JSON, reads the log and calls it a
    result.
    """
    for stream in (stdout, stderr):
        for line in stream.splitlines():
            if line.startswith(SENTINEL):
                return json.loads(line[len(SENTINEL):])
    raise ValueError("no KEOSQ_ATTEMPT line in either stream")


def run_attempt(goal: dict, env_identity: dict) -> dict:
    """One attempt. Returns the evidence record; never raises for a model failure."""
    started = utc_now()
    t0 = time.time()

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".prompt",
                                     delete=False) as fh:
        fh.write(goal["prompt"])
        prompt_path = fh.name

    env = dict(os.environ)
    env["KEOS_PROMPT_FILE"] = prompt_path
    env["KEOS_GOAL_ID"] = goal["id"]
    env["KEOS_MAX_TOKENS"] = str(goal.get("max_tokens", 1024))

    record = {
        "goal_id": goal["id"],
        "attempt_index": goal["attempts"] + 1,
        "started_utc": started,
        "prompt_sha256": sha256_text(goal["prompt"]),
        "prompt": goal["prompt"],
        "environment": env_identity,
    }

    try:
        proc = subprocess.run(
            ["elixir", str(ATTEMPT_EXS)],
            env=env, capture_output=True, text=True,
            timeout=ATTEMPT_TIMEOUT_S, cwd=str(ROOT),
        )
    except subprocess.TimeoutExpired:
        record.update(outcome=UNAVAILABLE, exit_code=None,
                      reason=f"the attempt did not return within {ATTEMPT_TIMEOUT_S}s")
        record["wall_s"] = round(time.time() - t0, 2)
        return record
    except OSError as exc:
        record.update(outcome=HARNESS_FAILED, exit_code=None,
                      reason=f"could not launch elixir: {exc!r}")
        record["wall_s"] = round(time.time() - t0, 2)
        return record
    finally:
        try:
            os.unlink(prompt_path)
        except OSError:
            pass

    record["exit_code"] = proc.returncode
    record["wall_s"] = round(time.time() - t0, 2)

    try:
        emitted = parse_attempt_line(proc.stdout, proc.stderr)
    except (ValueError, json.JSONDecodeError) as exc:
        # The attempt produced no verdict of its own. That is a HARNESS failure
        # and NOT a model failure -- the distinction is the entire point of the
        # outcome vocabulary, and collapsing it would seed the corpus with a
        # "failure" the model never had a chance to commit.
        record.update(outcome=HARNESS_FAILED,
                      reason=f"unreadable attempt output: {exc}",
                      stdout_tail=proc.stdout[-2000:], stderr_tail=proc.stderr[-2000:])
        return record

    outcome = emitted.get("outcome")
    if outcome not in OUTCOMES:
        record.update(outcome=HARNESS_FAILED,
                      reason=f"attempt reported an outcome outside the vocabulary: {outcome!r}")
        record["emitted"] = emitted
        return record

    text = emitted.get("text", "")
    if len(text) > MAX_TEXT_CHARS:
        emitted["text"] = text[:MAX_TEXT_CHARS]
        emitted["text_truncated_from"] = len(text)

    record.update(emitted)
    record["outcome"] = outcome
    return record


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    dry = "--dry-run" in argv

    say(f"keos-qwen goal firing  utc={utc_now()}  dry_run={dry}")

    if not ATTEMPT_EXS.exists():
        say(f"PRECONDITION: no attempt script at {ATTEMPT_EXS}")
        return EXIT_REFUSED

    for d in (QUEUE, EVIDENCE, DONE):
        try:
            d.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            say(f"PRECONDITION: could not create {d}: {exc}")
            return EXIT_REFUSED

    env_identity = {
        # Resolved, never inferred from PATH[0]. Which interpreter actually ran
        # is the difference between an OTP-26 build and the OTP-27 one still on
        # disk that core-dumped the VM, and evidence that guesses it is evidence
        # about a run that may not have happened the way it says.
        "elixir": shutil.which("elixir") or "NOT-ON-PATH",
        "erl_libs": os.environ.get("ERL_LIBS", "unset"),
        "ledger_root": os.environ.get("KEOS_QWEN_LEDGER_ROOT", "unset"),
        "attempt_exs_sha256": sha256_file(ATTEMPT_EXS),
        "fire_py_sha256": sha256_file(Path(__file__)),
    }

    pending = sorted(p for p in QUEUE.glob("*.json") if p.is_file())
    if not pending:
        say("nothing queued. This is a result, not a failure: an empty queue and a "
            "refused batch are different facts and only one of them is about the model.")
        return EXIT_OK

    say(f"{len(pending)} queued, firing at most {MAX_PER_FIRE}")

    fired = 0
    outcomes: list[str] = []

    for path in pending:
        if fired >= MAX_PER_FIRE:
            say(f"bound reached: {MAX_PER_FIRE} per firing. {len(pending) - fired} left for next time.")
            break

        # RE-DECIDED BEFORE EVERY GOAL, not once per batch. That is what makes
        # the DISABLED flag file able to stop a run already in flight -- an env
        # var cannot, because this process already has its environment.
        try:
            decision = ledger.decide(os.environ.get("KEOS_QWEN_LEDGER_ROOT"))
        except ledger.LedgerError as exc:
            say(f"REFUSED: the ledger could not answer: {exc}")
            say("Failing closed. An unreadable budget does not authorise spend on a "
                "host carrying 15 production services.")
            return EXIT_REFUSED

        if not decision.allowed:
            say(f"REFUSED: {decision.verdict} -- {decision.reason}")
            say(f"used_today={decision.used_today}/{decision.budget}. "
                f"{len(pending) - fired} goals left untouched.")
            return EXIT_REFUSED

        try:
            goal = load_goal(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            say(f"REFUSED: {path.name} is not a goal we can read: {exc}")
            say("Refusing rather than repairing: a guessed prompt is a question the "
                "Owner never asked, in a corpus that exists to be trusted.")
            return EXIT_REFUSED

        say(f"\n--- goal {goal['id']}  attempt {goal['attempts'] + 1}/{goal['max_attempts']}  "
            f"budget {decision.used_today}/{decision.budget} ---")

        if dry:
            say("dry run: not calling the model")
            fired += 1
            continue

        record = run_attempt(goal, env_identity)
        outcomes.append(record["outcome"])

        stamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        ev = EVIDENCE / goal["id"] / f"{stamp}-a{record['attempt_index']}.json"
        write_json_atomic(ev, record)

        detail = record.get("reason") or record.get("served_by", "")
        say(f"outcome={record['outcome']} wall={record.get('wall_s')}s "
            f"served_by={record.get('served_by', 'n/a')} {detail}")
        say(f"evidence -> {ev}")

        goal["attempts"] = record["attempt_index"]
        goal["last_outcome"] = record["outcome"]
        goal["last_attempt_utc"] = record["started_utc"]

        if goal["attempts"] >= goal["max_attempts"]:
            goal["retired_utc"] = utc_now()
            write_json_atomic(DONE / path.name, goal)
            try:
                os.unlink(path)
            except OSError as exc:
                say(f"FAILED: retired {goal['id']} but could not clear {path}: {exc}")
                return EXIT_FAILED
            say(f"retired after {goal['attempts']} attempts -> {DONE / path.name}")
        else:
            write_json_atomic(path, goal)

        fired += 1

    if not outcomes:
        say(f"\nfired={fired} (no calls made)")
        return EXIT_OK

    agg = worst(outcomes)
    say(f"\nfired={fired} outcomes={outcomes} worst={agg}")

    if agg == OK:
        return EXIT_OK
    if agg == HARNESS_FAILED:
        say("A harness failure is NOT a model failure. This run measured nothing "
            "about the model and must not seed the corpus as if it had.")
        return EXIT_FAILED
    # UNAVAILABLE / TRUNCATED: the model was reached and could not complete. That
    # is a real observation, it is already on disk as evidence, and it is not a
    # reason for systemd to call the firing broken.
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
