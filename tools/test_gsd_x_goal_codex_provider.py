#!/usr/bin/env python3
"""V-gates for the Codex epoch provider (C8).

Every shared-account control is driven in BOTH directions, against a stand-in
binary: this suite spends no quota, because the account under test is the
Owner's personal one and a test that burned it would be its own defect. The
real model call is exercised once, for real, by the first Codex epoch of G-001.

The binary itself is preflighted (`codex --version`), so "the provider is
wired" is not confused with "the thing it launches exists".

    python tools/test_gsd_x_goal_codex_provider.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.gsd_x.goal import epoch as ep                          # noqa: E402
from modules.gsd_x.goal.providers.codex import CodexProvider        # noqa: E402
from modules.gsd_x.goal.providers import codex as cx                # noqa: E402

GIT = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"   # PATH first: GEX44 (Linux) runs these
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}

# A stand-in for `codex exec`: it writes a file, commits it, and prints. It is
# NOT looser than the real thing at the contract boundary -- same argv shape,
# same cwd, same exit code, same stdout channel.
FAKE = """
import subprocess, sys, pathlib
import shutil
GIT = shutil.which("git") or r"C:\\Program Files\\Git\\cmd\\git.exe"
args = sys.argv[1:]
mode = "ok"
for a in args:
    if a.startswith("MODE="):
        mode = a.split("=", 1)[1]
if mode == "ratelimit":
    print("Error: 429 rate limit reached for this account")
    sys.exit(1)
if mode == "sleep":
    import time; time.sleep(120)
root = pathlib.Path.cwd()
(root / "written_by_codex.txt").write_text("work\\n", encoding="utf-8")
subprocess.run([GIT, "add", "."], cwd=root)
subprocess.run([GIT, "commit", "-qm", "codex work"], cwd=root)
print("codex: wrote written_by_codex.txt")
"""


def make_repo() -> Path:
    d = Path(tempfile.mkdtemp(prefix="gsdx_cx_repo_"))
    subprocess.run([GIT, "init", "-q", str(d)], check=True, env=ENV)
    (d / "seed.txt").write_text("seed\n", encoding="utf-8")
    subprocess.run([GIT, "-C", str(d), "add", "."], check=True, env=ENV)
    subprocess.run([GIT, "-C", str(d), "commit", "-qm", "seed"], check=True, env=ENV)
    return d


def wait_ended(prov, handle, timeout=90):
    end = time.time() + timeout
    while time.time() < end:
        if prov.observe(handle).state == ep.OBS_ENDED:
            break
        time.sleep(0.05)
    return prov.observe(handle)


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []

    def ok(g, ev):
        passes.append(g)
        print(f"  PASS {g}: {ev}")

    def bad(g, why):
        fails.append(g)
        print(f"  FAIL {g}: {why}")

    def check(g, cond, ev, why):
        (ok if cond else bad)(g, ev if cond else why)

    sandbox = Path(tempfile.mkdtemp(prefix="gsdx_cx_home_"))
    fake_py = sandbox / "fake_codex.py"
    fake_py.write_text(FAKE, encoding="utf-8")
    os.environ[cx.AUDIT_LOG_ENV] = str(sandbox / "codex_usage.jsonl")
    os.environ[cx.COOLDOWN_ENV] = str(sandbox / "cooldown.json")
    os.environ[cx.DISABLE_FLAG_ENV] = str(sandbox / "codex.disabled")
    os.environ.pop(cx.DISABLED_ENV, None)

    runs = Path(tempfile.mkdtemp(prefix="gsdx_cx_runs_"))
    home = sandbox / "codex_home"
    prov = CodexProvider(runs, wall_bound_s=60, max_per_day=3,
                         argv_prefix=[sys.executable, str(fake_py)], codex_home=home)
    ep.check_provider(prov)
    ok("V-CX-PROVIDER-CONTRACT", "the provider satisfies the contract with a 20-min-class bound")

    repo = make_repo()

    def spec(token, eid, prompt="do the thing", root=None):
        return {"epoch_id": eid, "revision": "rev1", "root": str(root or repo),
                "prompt": prompt, "scope_paths": ["."],
                "identity": {"run_token": token, "epoch_id": eid}}

    # --- the real binary exists ------------------------------------------------
    real = subprocess.run([os.environ.get(cx.BIN_ENV) or "codex", "--version"],
                          capture_output=True, text=True)
    check("V-CX-REAL-BINARY", real.returncode == 0 and real.stdout.strip(),
          f"the codex binary this provider launches exists: {real.stdout.strip()[:60]}",
          f"rc={real.returncode} err={real.stderr[:120]}")

    # --- kill switches ----------------------------------------------------------
    os.environ[cx.DISABLED_ENV] = "1"
    try:
        prov.dispatch(spec("t-dis", "ep-dis"))
        bad("V-CX-KILL-ENV", "dispatched while the kill switch env was set")
    except ep.EpochError as exc:
        check("V-CX-KILL-ENV", "disabled" in str(exc),
              "the CODEX_DISABLED env stops a dispatch", str(exc))
    os.environ.pop(cx.DISABLED_ENV)
    Path(os.environ[cx.DISABLE_FLAG_ENV]).write_text("off", encoding="utf-8")
    try:
        prov.dispatch(spec("t-flag", "ep-flag"))
        bad("V-CX-KILL-FLAG", "dispatched while the kill-switch FILE existed")
    except ep.EpochError as exc:
        # The REASON is asserted, not merely the refusal. Measured 2026-09-22:
        # with the kill switch removed this gate still passed, because the
        # account lock refused the dispatch instead -- a gate passing for a
        # reason that has nothing to do with what it is named for.
        check("V-CX-KILL-FLAG", "kill switch file" in str(exc),
              "the kill-switch file stops a dispatch with no restart", str(exc))
    Path(os.environ[cx.DISABLE_FLAG_ENV]).unlink()

    # --- shared cooldown ---------------------------------------------------------
    prov.trip_cooldown(300)
    try:
        prov.dispatch(spec("t-cool", "ep-cool"))
        bad("V-CX-COOLDOWN-BLOCKS", "dispatched while the shared cooldown was live")
    except ep.EpochError as exc:
        check("V-CX-COOLDOWN-BLOCKS", "rate-limited" in str(exc),
              "a live shared cooldown stops a dispatch", str(exc))
    Path(os.environ[cx.COOLDOWN_ENV]).unlink()

    # --- a real (stand-in) epoch --------------------------------------------------
    h = prov.dispatch(spec("t-ok", "ep-ok"))
    obs = wait_ended(prov, h)
    r = prov.harvest(h, spec("t-ok", "ep-ok"))
    check("V-CX-EPOCH-RUNS", obs.outcome == ep.COMPLETED and r.commits
          and (repo / "written_by_codex.txt").is_file(),
          f"the epoch ran in its worktree and its commit is in the receipt ({r.commits[:1]})",
          f"obs={obs} commits={r.commits}")
    check("V-CX-NO-VERDICT", r.verdicts == [],
          "codex writing code yields NO verdict: a gate epoch judges the work",
          f"verdicts={r.verdicts}")
    check("V-CX-AUDIT-ONE-LEDGER",
          sum(1 for ln in Path(os.environ[cx.AUDIT_LOG_ENV]).read_text(encoding="utf-8")
              .splitlines() if json.loads(ln)["endpoint"] == cx.ENDPOINT) >= 2,
          "dispatch and harvest are appended to the shared account ledger, tagged goal-epoch",
          "the shared ledger has no goal-epoch rows")

    # --- the lock ------------------------------------------------------------------
    h2 = prov.dispatch({**spec("t-slow", "ep-slow"), "prompt": "MODE=sleep"})
    try:
        prov.dispatch(spec("t-second", "ep-second"))
        bad("V-CX-LOCK", "two local codex epochs held the account at once")
    except ep.EpochError as exc:
        check("V-CX-LOCK", "holds the account" in str(exc),
              "a second local epoch is refused while one holds the account", str(exc))
    prov.cancel(h2)
    time.sleep(0.5)
    check("V-CX-LOCK-RELEASED", not prov._lock_path().is_file(),
          "cancelling releases the account lock", "the lock outlived the cancelled epoch")
    lockfile = prov._lock_path()
    lockfile.parent.mkdir(parents=True, exist_ok=True)
    lockfile.write_text(json.dumps({"pid": 999999, "epoch_id": "ep-dead", "at": time.time()}),
                        encoding="utf-8")
    try:
        prov.acquire_lock("ep-after-dead")
        ok("V-CX-LOCK-STALE-RECLAIMED", "a lock held by a dead process is reclaimed")
    except ep.EpochError as exc:
        bad("V-CX-LOCK-STALE-RECLAIMED", f"a dead holder kept the account locked: {exc}")
    prov.release_lock("ep-after-dead")

    # --- rate limit seen in the output ------------------------------------------------
    h3 = prov.dispatch({**spec("t-rl", "ep-rl"), "prompt": "MODE=ratelimit"})
    wait_ended(prov, h3)
    r3 = prov.harvest(h3, spec("t-rl", "ep-rl"))
    check("V-CX-RATELIMIT-TRIPS-COOLDOWN",
          prov.cooling_until() > time.time()
          and any(f["signature"] == "codex-rate-limited" for f in r3.failures),
          "a rate limit in the output writes the SHARED cooldown and is a named failure",
          f"cooling={prov.cooling_until()} failures={r3.failures}")
    Path(os.environ[cx.COOLDOWN_ENV]).unlink()

    # --- daily budget --------------------------------------------------------------
    check("V-CX-BUDGET-COUNTS", prov.used_today() == 3,
          f"the ledger counts today's goal-epoch dispatches ({prov.used_today()}/3)",
          f"used={prov.used_today()}")
    try:
        prov.dispatch(spec("t-over", "ep-over"))
        bad("V-CX-BUDGET-STOPS", "dispatched past the Owner's daily cap")
    except ep.EpochError as exc:
        check("V-CX-BUDGET-STOPS", "budget is spent" in str(exc),
              "the daily cap stops a dispatch and says what it spent", str(exc))

    # --- refusals and recovery ---------------------------------------------------------
    for sp, gate, needle, why in (
            ({**spec("t-x", "ep-x"), "prompt": "  "}, "V-CX-NEEDS-PROMPT", "needs a prompt",
             "a codex epoch with no prompt refused"),
            ({**spec("t-y", "ep-y"), "root": str(repo / "nope")}, "V-CX-NEEDS-WORKTREE",
             "worktree does not exist", "a codex epoch whose worktree does not exist refused")):
        try:
            prov.dispatch(sp)
            bad(gate, "accepted")
        except ep.EpochError as exc:
            # Reason asserted: any refusal would otherwise satisfy this gate.
            check(gate, needle in str(exc), why, f"refused for another reason: {exc}")
    check("V-CX-PROBE", (prov.probe({"run_token": "t-ok"}) or {}).get("pid") == h["pid"],
          "a run started before a crash is found by its pre-minted token", "probe failed")
    check("V-CX-PROBE-NONE", prov.probe({"run_token": "never"}) is None,
          "a token that never dispatched probes to None", "probe invented a run")

    total = len(passes) + len(fails)
    print(f"\nGSDX_CODEX_PROVIDER_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
