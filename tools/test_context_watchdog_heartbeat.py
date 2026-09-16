"""V-CWHB-* — the context watchdog's heartbeat.

WHY THIS EXISTS. Before the heartbeat the hook wrote nothing anywhere, so three
different worlds shared one appearance: it ran and declined, it ran and fired,
and the dispatcher killed it at its timeout and threw its stdout away. Only the
third silently cancels an unattended /cpp-gsd-long run, and nothing could tell
them apart (rules/guard-event-reachability.md).

The heartbeat is therefore a SAFETY-CRITICAL diagnostic, which cuts both ways:
it must record every outcome, and it must never be able to break the hook it
reports on. Both halves are asserted here, and the second one is the half that
gets left out -- a logger that raises on a read-only disk would convert a
working watchdog into a dead one, at exactly the moment a starved host is the
reason you wanted the log.

Every assertion is a DELTA over the window, never "the file is non-empty": this
log is append-only and shared with every other run on the machine, so a
non-emptiness check passes on somebody else's line.
"""
import importlib.util
import os
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WD = ROOT / "modules" / "zero-crash" / "hooks" / "context-watchdog.py"

_pass = 0
_fail = 0


def ok(gate, ev):
    global _pass
    print(f"  OK   {gate}: {ev}")
    _pass += 1


def bad(gate, ev):
    global _fail
    print(f"  FAIL {gate}: {ev}")
    _fail += 1


def load():
    spec = importlib.util.spec_from_file_location(f"ctxwd_{uuid.uuid4().hex[:6]}", WD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def lines(path):
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []


def drive(wd, pct, sid=None):
    sid = sid or f"cwhb-{uuid.uuid4().hex[:10]}"
    os.environ["_TEST_CONTEXT_PCT"] = str(pct)
    try:
        return sid, wd.run({"session_id": sid, "cwd": str(ROOT), "transcript_path": ""})
    finally:
        os.environ.pop("_TEST_CONTEXT_PCT", None)


def stub_side_effects(wd):
    """Tier 2 checkpoints, dumps telemetry and launches the SendKeys daemon --
    which types into whichever Cursor window has focus. Replaced for the
    duration; the heartbeat itself is untouched, since it is the subject."""
    saved = {n: getattr(wd, n) for n in
             ("_import_atomic_write", "_kclear_equivalent", "_dump_telemetry",
              "_write_trigger_flag", "_spawn_daemon", "_append_progress_md")}
    wd._kclear_equivalent = lambda *a, **k: {}
    wd._dump_telemetry = lambda *a, **k: None
    wd._write_trigger_flag = lambda *a, **k: None
    wd._spawn_daemon = lambda *a, **k: False
    wd._append_progress_md = lambda *a, **k: None
    return saved


def main():
    wd = load()
    log = wd.HEARTBEAT_LOG

    # --- a declining judgement is recorded, not only a firing one ------------
    before = len(lines(log))
    sid, out = drive(wd, 20.0)
    added = lines(log)[before:]
    mine = [ln for ln in added if sid in ln]
    if len(mine) == 1 and "outcome=pass" in mine[0]:
        ok("V-CWHB-PASS", f"one line for a declining judgement: {mine[0][-58:]}")
    else:
        bad("V-CWHB-PASS", f"expected 1 pass line for {sid}, got {mine!r}")

    # The percentage is what makes a `pass` readable. Without it the line says
    # the hook ran and not whether it SHOULD have fired.
    if mine and "used_pct=20.0" in mine[0]:
        ok("V-CWHB-PCT", "the judged percentage is on the line")
    else:
        bad("V-CWHB-PCT", f"used_pct absent or wrong: {mine!r}")

    # --- a real tier-2 crossing is recorded as a block -----------------------
    saved = stub_side_effects(wd)
    try:
        before = len(lines(log))
        sid, out = drive(wd, 75.0)
        mine = [ln for ln in lines(log)[before:] if sid in ln]
        drove = isinstance(out, dict) and out.get("decision") == "block"
        if not drove:
            bad("V-CWHB-BLOCK", f"tier 2 did not fire (decision={out!r}) — gate measured nothing")
        elif len(mine) == 1 and "outcome=block" in mine[0]:
            ok("V-CWHB-BLOCK", "a crossing is recorded as outcome=block")
        else:
            bad("V-CWHB-BLOCK", f"expected 1 block line, got {mine!r}")
    finally:
        for n, f in saved.items():
            setattr(wd, n, f)

    # --- a crash is recorded, and is not swallowed into looking like a pass --
    # This is the line that distinguishes "declined" from "died", which is the
    # whole point: without it a broken watchdog logs `pass` forever.
    fresh = load()
    boom = f"cwhb-boom-{uuid.uuid4().hex[:8]}"

    def explode(_event):
        raise RuntimeError("synthetic")

    fresh._run_inner = explode
    before = len(lines(log))
    raised = False
    try:
        fresh.run({"session_id": boom, "cwd": str(ROOT), "transcript_path": ""})
    except RuntimeError:
        raised = True
    mine = [ln for ln in lines(log)[before:] if boom in ln]
    if len(mine) == 1 and "outcome=error" in mine[0]:
        ok("V-CWHB-ERROR", f"a crashing judgement is recorded as error (propagated={raised})")
    else:
        bad("V-CWHB-ERROR", f"expected 1 error line, got {mine!r}")

    # --- the diagnostic must never be able to break its subject -------------
    # A logger that raises on an unwritable path turns a working watchdog into a
    # dead one on exactly the starved host that made you want the log.
    fresh2 = load()
    fresh2.HEARTBEAT_LOG = Path(fresh2.HEARTBEAT_LOG.drive + "\\") / "\x00nope" / "x.log"
    try:
        sid, out = drive(fresh2, 20.0)
        ok("V-CWHB-FAILOPEN", "an unwritable log path does not break the hook")
    except Exception as exc:
        bad("V-CWHB-FAILOPEN", f"heartbeat raised through run(): {type(exc).__name__}: {exc}")

    # --- positive control ---------------------------------------------------
    # An empty window satisfies every "expected N lines" assertion above if the
    # log were never written at all. Prove the instrument moved.
    if len(lines(log)) > 0:
        ok("V-CWHB-CONTROL", f"log has {len(lines(log))} lines — the sweep could observe something")
    else:
        bad("V-CWHB-CONTROL", "log is empty — every assertion above was vacuous")

    print(f"CWHB_PASS={_pass}/{_pass + _fail}  threshold={_pass + _fail}/{_pass + _fail}")
    return 0 if _fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
