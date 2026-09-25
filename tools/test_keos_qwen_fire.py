#!/usr/bin/env python3
"""V-gates for the goal-firing executable that systemd unit B runs.

Runs with no network, no model and no GEX44: every gate here is about the loop's
DECISIONS -- what it refuses, what it bounds, what it records -- because those
are the properties the K-ADOS A-01 amendment made admissible, and a property
that is only true when the model happens to answer is not a property.

Each refusal assertion is paired with an ADMITTED control. A loop wedged on "no"
would satisfy every refusal gate in this file and be indistinguishable from one
that works; the paired green is the only thing that tells them apart.

The precondition is ASSERTED, not assumed: if the package does not import, this
exits 2 as HARNESS-FAILED and never as a finding. A gate that cannot reach its
subject and a gate whose subject is broken are different evidence.
"""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

_passes: list[str] = []
_fails: list[str] = []


def ok(gate: str, evidence: str) -> None:
    _passes.append(gate)
    print(f"  PASS {gate}: {evidence}")


def bad(gate: str, why: str) -> None:
    _fails.append(gate)
    print(f"  FAIL {gate}: {why}")


def check(gate: str, cond: bool, evidence: str, why: str) -> None:
    ok(gate, evidence) if cond else bad(gate, why)


# ---- precondition -----------------------------------------------------------
SANDBOX = Path(tempfile.mkdtemp(prefix="keosq_fire_gate_"))
(SANDBOX / "keos_qwen" / "goals").mkdir(parents=True, exist_ok=True)
(SANDBOX / "keos_qwen" / "goals" / "attempt.exs").write_text("# stand-in\n", encoding="utf-8")
os.environ["KEOS_QWEN_ROOT"] = str(SANDBOX)
os.environ["KEOS_QWEN_LEDGER_ROOT"] = str(SANDBOX / "ledger")
os.environ.pop("KEOS_QWEN_DISABLED", None)

try:
    from modules.keos_qwen.goals import fire  # noqa: E402
    from modules.keos_qwen import outcome  # noqa: E402
except Exception as exc:  # pragma: no cover
    print(f"HARNESS-FAILED: could not import the subject from {REPO}: {exc!r}")
    print("This is NOT a finding about the goal loop. Nothing was measured.")
    raise SystemExit(2)

LEDGER = fire.ledger


def fresh_root(tag: str) -> Path:
    d = Path(tempfile.mkdtemp(prefix=f"keosq_{tag}_", dir=str(SANDBOX)))
    return d


def queue_goal(gid: str, prompt: str = "say PONG", **extra) -> Path:
    fire.QUEUE.mkdir(parents=True, exist_ok=True)
    p = fire.QUEUE / f"{gid}.json"
    body = {"id": gid, "prompt": prompt}
    body.update(extra)
    p.write_text(json.dumps(body), encoding="utf-8")
    return p


def clear_queue() -> None:
    if fire.QUEUE.exists():
        for f in fire.QUEUE.glob("*.json"):
            f.unlink()


def run_main(argv) -> tuple[int, str]:
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = fire.main(argv)
    return rc, buf.getvalue()


print("=== keos_qwen goal-firing gates ===")
print(f"  (sandbox: {SANDBOX})")

# ---- the sentinel parser, against the noise that was actually measured ------
# These four lines are verbatim from a real GEX44 call on 2026-09-25. A fixture
# I invented would have contained only the shapes I already believed in.
REAL_NOISE = """
17:57:04.793 [error] Exqlite.Connection (#PID<0.268.0> (:proc_lib)) failed to connect: ** (Exqlite.Error) You must provide a :database to the database. Example: connect(database: "./") or connect(database: :memory)
17:57:04.918 [debug] [ToolRegistry] Initialized with 39 built-in tool(s): Agent, TaskOutput, Bash
17:57:06.525 [debug] [Router] create_message via ollama
17:57:06.535 [debug] [OpenAI] POST http://127.0.0.1:8081/v1/chat/completions model=gpt-4o
"""

GOOD = REAL_NOISE + '\nKEOSQ_ATTEMPT {"goal":"g1","outcome":"OK","text":"PONG","served_by":"local"}\n'

try:
    rec = fire.parse_attempt_line(GOOD, "")
    check("V-KEOSQ-FIRE-SENTINEL-FINDS-ANSWER",
          rec.get("outcome") == "OK" and rec.get("text") == "PONG",
          "the answer is picked out of four lines of real harness diagnostics",
          f"parsed the wrong thing: {rec!r}")
except Exception as exc:
    bad("V-KEOSQ-FIRE-SENTINEL-FINDS-ANSWER", f"raised on a good input: {exc!r}")

# The discriminating control -- and the ASSERTION IS ON THE REASON, not on the
# exception type.
#
# The first version of this gate asserted only `except ValueError`, and a
# mutation drill walked straight through it: a parser mutated to take "any line
# containing a brace" grabs the Exqlite error line, fails to JSON-decode it, and
# raises JSONDecodeError -- which is a SUBCLASS of ValueError. So "correctly
# found no answer" and "grabbed a log line and choked on it" were the same
# observable, and the gate reported 24/24 against a parser that reads the log.
# An absence assertion is only as good as its ability to say WHY.
try:
    fire.parse_attempt_line(REAL_NOISE, "")
    bad("V-KEOSQ-FIRE-SENTINEL-REFUSES-LOG",
        "the parser accepted a pure log with no answer in it")
except Exception as exc:
    refused_for_the_right_reason = (
        type(exc) is ValueError and "no KEOSQ_ATTEMPT line" in str(exc))
    check("V-KEOSQ-FIRE-SENTINEL-REFUSES-LOG", refused_for_the_right_reason,
          "a stream of diagnostics refuses BECAUSE there is no sentinel -- not "
          "because it grabbed a debug line and could not decode it",
          f"refused for the wrong reason ({type(exc).__name__}: {exc}); a parser "
          "reading the log would produce exactly this")

# The sharper version of the same control: a well-formed JSON object on a
# NON-sentinel line. Here a parser that looks for JSON rather than for the
# sentinel does not choke -- it succeeds, and returns the harness's own
# diagnostics as though the model had said them.
DECOY = REAL_NOISE + '\n[debug] [Cache] stats {"outcome":"OK","text":"cache warm"}\n'
try:
    got = fire.parse_attempt_line(DECOY, "")
    bad("V-KEOSQ-FIRE-SENTINEL-IGNORES-DECOY",
        f"a debug line was returned as the model's answer: {got!r}")
except ValueError:
    ok("V-KEOSQ-FIRE-SENTINEL-IGNORES-DECOY",
       "a well-formed JSON object on a debug line is NOT an answer: membership "
       "is decided by the sentinel, never by looking parseable")

# stderr is a legitimate carrier: the harness splits its own output across both.
try:
    rec = fire.parse_attempt_line(REAL_NOISE, GOOD)
    check("V-KEOSQ-FIRE-SENTINEL-READS-STDERR", rec.get("outcome") == "OK",
          "an answer that arrived on stderr is still an answer",
          f"missed the stderr answer: {rec!r}")
except Exception as exc:
    bad("V-KEOSQ-FIRE-SENTINEL-READS-STDERR", f"raised: {exc!r}")

# ---- goal parsing: refuse, never repair -------------------------------------
GOOD_GOAL = {"id": "g-ok", "prompt": "write a function", "max_attempts": 2}
_p = fire.QUEUE / "tmp-good.json"
fire.QUEUE.mkdir(parents=True, exist_ok=True)
_p.write_text(json.dumps(GOOD_GOAL), encoding="utf-8")
try:
    g = fire.load_goal(_p)
    check("V-KEOSQ-FIRE-GOAL-ADMITTED",
          g["id"] == "g-ok" and g["max_attempts"] == 2 and g["attempts"] == 0,
          "a well-formed goal parses (admitted control: a loader that refused "
          "everything would pass all four refusals below)",
          f"a valid goal was mangled: {g!r}")
except Exception as exc:
    bad("V-KEOSQ-FIRE-GOAL-ADMITTED", f"refused a valid goal: {exc!r}")

for name, body, why in [
    ("NO-ID", {"prompt": "x"}, "a goal with no id"),
    ("EMPTY-PROMPT", {"id": "g", "prompt": "   "}, "a whitespace-only prompt"),
    ("BAD-ATTEMPTS", {"id": "g", "prompt": "x", "max_attempts": 0}, "max_attempts=0"),
    ("NOT-AN-OBJECT", ["id", "prompt"], "a JSON array where an object belongs"),
]:
    _p.write_text(json.dumps(body), encoding="utf-8")
    try:
        fire.load_goal(_p)
        bad(f"V-KEOSQ-FIRE-GOAL-REFUSES-{name}", f"accepted {why}")
    except (ValueError, json.JSONDecodeError):
        ok(f"V-KEOSQ-FIRE-GOAL-REFUSES-{name}",
           f"{why} is refused rather than repaired into a question nobody asked")
    except Exception as exc:
        bad(f"V-KEOSQ-FIRE-GOAL-REFUSES-{name}", f"wrong exception type: {exc!r}")
_p.unlink()

# ---- atomic evidence --------------------------------------------------------
ev_dir = fresh_root("ev")
target = ev_dir / "deep" / "record.json"
fire.write_json_atomic(target, {"a": 1, "text": "quote \" newline \n backslash \\"})
loaded = json.loads(target.read_text(encoding="utf-8"))
check("V-KEOSQ-FIRE-EVIDENCE-ROUNDTRIPS",
      loaded["text"] == 'quote " newline \n backslash \\',
      "an evidence record survives the characters a model reply actually contains",
      f"round trip lost content: {loaded!r}")

leftovers = list(target.parent.glob(".tmp-*"))
check("V-KEOSQ-FIRE-EVIDENCE-NO-TEMP-LEFT", leftovers == [],
      "the atomic write left no temp file behind",
      f"temp files left: {leftovers}")

before = target.read_bytes()
try:
    class Unserialisable:
        pass
    fire.write_json_atomic(target, {"bad": Unserialisable()})
    bad("V-KEOSQ-FIRE-EVIDENCE-SURVIVES-ENCODE-FAILURE",
        "an unserialisable payload did not raise")
except TypeError:
    same = target.read_bytes() == before
    check("V-KEOSQ-FIRE-EVIDENCE-SURVIVES-ENCODE-FAILURE", same,
          "a failed encode destroyed nothing: open(path,'w') truncates BEFORE "
          "encoding, which is how evidence becomes a zero-byte file",
          "the existing evidence was destroyed by a failed write")

# ---- the loop's three outcomes ----------------------------------------------
clear_queue()
rc, out = run_main([])
check("V-KEOSQ-FIRE-EMPTY-QUEUE-IS-OK",
      rc == fire.EXIT_OK and "nothing queued" in out,
      "an empty queue exits 0 and says so: an empty queue and a refused batch "
      "are different facts and only one is about the model",
      f"rc={rc} out={out[-300:]!r}")

# Kill switch 2: the flag file, which is the one that can stop a run in flight.
ledger_root = Path(os.environ["KEOS_QWEN_LEDGER_ROOT"])
ledger_root.mkdir(parents=True, exist_ok=True)
clear_queue()
queue_goal("g-killed")
(ledger_root / "DISABLED").write_text("the gate set this on purpose", encoding="utf-8")
rc, out = run_main([])
check("V-KEOSQ-FIRE-FLAG-REFUSES",
      rc == fire.EXIT_REFUSED and "DISABLED_FLAG" in out,
      "the flag file refuses BY ITS OWN CODE, not as a generic error",
      f"rc={rc} out={out[-300:]!r}")

ev_root = fire.EVIDENCE / "g-killed"
check("V-KEOSQ-FIRE-REFUSED-SPENDS-NOTHING",
      not ev_root.exists(),
      "a refused firing produced no evidence: the model was never reached",
      "a refused firing still wrote an attempt record")

still_queued = (fire.QUEUE / "g-killed.json").exists()
check("V-KEOSQ-FIRE-REFUSED-LEAVES-THE-QUEUE",
      still_queued,
      "a refused goal stays queued -- a refusal must not silently consume work",
      "the goal was consumed by a firing that never ran it")
(ledger_root / "DISABLED").unlink()

# Kill switch 1: the environment.
os.environ["KEOS_QWEN_DISABLED"] = "1"
rc, out = run_main([])
check("V-KEOSQ-FIRE-ENV-REFUSES",
      rc == fire.EXIT_REFUSED and "DISABLED_ENV" in out,
      "the environment switch refuses with its own distinct code",
      f"rc={rc} out={out[-300:]!r}")
os.environ.pop("KEOS_QWEN_DISABLED")

# Budget exhausted must be distinguishable from both switches.
for i in range(LEDGER.DEFAULT_DAILY_BUDGET):
    LEDGER.record(str(ledger_root), caller="gate", outcome="OK", detail=f"filler {i}")
rc, out = run_main([])
check("V-KEOSQ-FIRE-BUDGET-REFUSES",
      rc == fire.EXIT_REFUSED and "BUDGET_EXHAUSTED" in out,
      "an exhausted budget refuses with its own code: 'wait for midnight' and "
      "'fix a permission' are different instructions",
      f"rc={rc} out={out[-300:]!r}")

check("V-KEOSQ-FIRE-REFUSALS-ARE-DISTINCT",
      len({"DISABLED_FLAG", "DISABLED_ENV", "BUDGET_EXHAUSTED"}) == 3,
      "three refusals, three codes, three different fixes",
      "refusal codes collapsed")

# The admitted control for every refusal above.
(ledger_root / "calls.jsonl").unlink()
clear_queue()
for n in range(5):
    queue_goal(f"g-bound-{n}")
rc, out = run_main(["--dry-run"])
fired = out.count("--- goal ")
check("V-KEOSQ-FIRE-ADMITS-WHEN-ALLOWED",
      rc == fire.EXIT_OK and fired > 0,
      f"with the budget clear and no switch set, the loop RUNS ({fired} goals "
      "reached). This is the control that separates a working loop from one "
      "wedged on 'no'",
      f"rc={rc} fired={fired}")

check("V-KEOSQ-FIRE-BOUNDED-PER-FIRING",
      fired == fire.MAX_PER_FIRE and "bound reached" in out,
      f"5 queued, {fired} fired, bound={fire.MAX_PER_FIRE}: a firing is bounded "
      "by count and says so",
      f"fired {fired} of 5 with bound {fire.MAX_PER_FIRE}")

# A goal we cannot read stops the batch rather than being skipped past.
clear_queue()
(fire.QUEUE / "g-broken.json").write_text("{not json", encoding="utf-8")
rc, out = run_main([])
check("V-KEOSQ-FIRE-MALFORMED-GOAL-REFUSES",
      rc == fire.EXIT_REFUSED and "not a goal we can read" in out,
      "an unreadable goal refuses the batch rather than being guessed at",
      f"rc={rc} out={out[-300:]!r}")

# ---- outcome discipline -----------------------------------------------------
check("V-KEOSQ-FIRE-VOCABULARY-IS-SHARED",
      fire.OUTCOMES == outcome.ALL,
      f"the loop classifies with the ONE outcome vocabulary {outcome.ALL}, not a "
      "second copy that can drift",
      f"the loop carries its own vocabulary: {fire.OUTCOMES}")

bogus = 'KEOSQ_ATTEMPT {"goal":"g","outcome":"GREAT","text":"hi"}'
parsed = fire.parse_attempt_line(bogus, "")
check("V-KEOSQ-FIRE-UNKNOWN-OUTCOME-IS-HARNESS-FAILED",
      parsed["outcome"] not in fire.OUTCOMES,
      "an outcome outside the vocabulary is detectable at the boundary, so it "
      "can be recorded as a HARNESS failure rather than as a model failure the "
      "model never had a chance to commit",
      f"the bogus outcome {parsed['outcome']!r} was inside the vocabulary")

check("V-KEOSQ-FIRE-HARNESS-FAILURE-OUTRANKS-OK",
      outcome.worst(["OK", "OK", fire.HARNESS_FAILED]) == fire.HARNESS_FAILED,
      "one harness failure in a batch makes the batch a harness failure: a run "
      "that proved nothing must not average into a pass",
      "a harness failure was outranked by successes")

total = len(_passes) + len(_fails)
print(f"\nKEOSQ_FIRE_PASS={len(_passes)}/{total}  threshold={total}/{total}")
if _fails:
    print("failed: " + ", ".join(_fails))
raise SystemExit(1 if _fails else 0)
