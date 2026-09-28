#!/usr/bin/env python3
"""V-ROLLACT-* gates for the ACTIVE rollover path in context-watchdog.py.

Spec: vault/specs/interactive-context-rollover.md §7 (Owner decision 2026-09-28).

The chain is: wall asks `/kclear` -> rollover.py judges the capsule it sealed -> only a
SAFE_TO_FORGET verdict licenses `/clear` -> the successor runs `/kresume`. These gates own
the destructive half. Every refusal is paired with a control in which the verdict is good
and `/clear` IS dispatched, so a path that refused everything cannot pass here.

Hermetic: the gate is stubbed per case, the dispatcher is a recorder, and no keystroke is
ever produced. rollover.py's own judgement is proven in tools/test_rollover.py.
"""
from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WATCHDOG = ROOT / "modules" / "zero-crash" / "hooks" / "context-watchdog.py"

passes = fails = 0


def _ok(gate, ev):
    global passes
    passes += 1
    print(f"  PASS {gate}: {ev}")


def _fail(gate, ev):
    global fails
    fails += 1
    print(f"  FAIL {gate}: {ev}")


def check(gate, cond, ev):
    (_ok if cond else _fail)(gate, ev)


def load():
    sys.path.insert(0, str(WATCHDOG.parent))
    spec = importlib.util.spec_from_file_location("ctxwd_rollact", WATCHDOG)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["ctxwd_rollact"] = mod
    spec.loader.exec_module(mod)
    return mod


def sid() -> str:
    return f"rollact-{uuid.uuid4().hex[:12]}"


def clear(wd, s):
    for f in (wd.ROLLOVER_ASK_FLAG, wd.ROLLOVER_CLEAR_FLAG, wd.ROLLOVER_WAIT_FLAG,
              wd.ADVISORY_FLAG, wd.SNAPSHOT_FLAG):
        wd._clear_flag(s, f)


def main() -> int:
    wd = load()
    calls: list = []
    wd._dispatch_continuation = lambda s_, kind, **k: calls.append(dict(k, kind=kind)) or \
        {"route": "orca-exact", "pane_key": "stub"}

    def with_verdict(v, reasons=()):
        wd._rollover_gate = lambda s_: {"verdict": v, "reasons": list(reasons), "rc": 0}

    print("the destructive step: /clear is dispatched only on SAFE_TO_FORGET")

    # CONTROL. Without a case where /clear IS dispatched, every refusal below is satisfied
    # by a path that never dispatches anything at all.
    s = sid(); clear(wd, s); calls.clear()
    with_verdict("SAFE_TO_FORGET")
    out = wd._rollover_step(s, str(ROOT), "", 75.0)
    check("V-ROLLACT-GREEN-DISPATCHES-CLEAR",
          len(calls) == 1 and calls[0]["kind"] == "clear"
          and calls[0]["expect_prefix"] == "/clear" and calls[0]["expect_line"] == "/clear"
          and (out or {}).get("decision") == "block",
          f"calls={calls} decision={(out or {}).get('decision')}")
    check("V-ROLLACT-GREEN-TEXT-ASKS-FOR-CLEAR",
          "/clear" in (out or {}).get("reason", "") and "/kresume" in (out or {}).get("reason", ""),
          "the block names the line to emit and who picks the thread up")

    # Idempotence: the flag is set BEFORE the dispatch, so a second Stop cannot type twice.
    out2 = wd._rollover_step(s, str(ROOT), "", 75.0)
    check("V-ROLLACT-CLEAR-DISPATCHED-ONCE", len(calls) == 1 and out2 is None,
          f"second call dispatched={len(calls) - 1}")
    clear(wd, s)

    for gate, verdict, reasons in [
        ("V-ROLLACT-REFUSED-TYPES-NOTHING", "REFUSED", ["obligations: none found"]),
        ("V-ROLLACT-NO-CAPSULE-TYPES-NOTHING", "NO_CAPSULE", ["no capsule_sealed receipt"]),
    ]:
        s = sid(); clear(wd, s); calls.clear()
        with_verdict(verdict, reasons)
        out = wd._rollover_step(s, str(ROOT), "", 75.0)
        check(gate, calls == [] and out is None, f"verdict={verdict} calls={calls} out={out}")
        clear(wd, s)

    print("a capsule that never arrives falls back to /compact, never past the wall")
    s = sid(); clear(wd, s); calls.clear()
    with_verdict("NO_CAPSULE")
    wd._set_flag(s, wd.ADVISORY_FLAG)
    outs = [wd._rollover_step(s, str(ROOT), "", 75.0) for _ in range(wd.ROLLOVER_MAX_WAIT)]
    check("V-ROLLACT-FALLBACK-REARMS-COMPACT",
          calls == [] and all(o is None for o in outs)
          and not wd._flag_exists(s, wd.ADVISORY_FLAG),
          f"after {wd.ROLLOVER_MAX_WAIT} waits the advisory flag is cleared so /compact re-fires")
    check("V-ROLLACT-FALLBACK-STOPS-RETRYING", wd._flag_exists(s, wd.ROLLOVER_CLEAR_FLAG),
          "the rollover leg is closed for this cycle; it does not compete with the compact leg")
    clear(wd, s)

    print("the kill switch, and the ask flag as the entry condition")
    s = sid(); clear(wd, s); calls.clear()
    with_verdict("SAFE_TO_FORGET")
    os.environ["CPP_ROLLOVER_ACTIVE"] = "0"
    try:
        check("V-ROLLACT-KILLSWITCH-OFF", not wd._rollover_active(), "CPP_ROLLOVER_ACTIVE=0")
    finally:
        os.environ.pop("CPP_ROLLOVER_ACTIVE", None)
    check("V-ROLLACT-DEFAULT-ON", wd._rollover_active(),
          "unset is ON -- the Owner's default, on this host and on GEX44")

    # run() must not enter the rollover leg for a session the wall never asked.
    s = sid(); clear(wd, s); calls.clear()
    (Path(tempfile.gettempdir()) / wd.ORCH_THROTTLE_FLAG.format(session_id=s)).write_text(
        str(time.time()), encoding="utf-8")
    os.environ["_TEST_CONTEXT_PCT"] = "20.0"
    try:
        wd.run({"session_id": s, "cwd": str(ROOT), "transcript_path": ""})
    finally:
        os.environ.pop("_TEST_CONTEXT_PCT", None)
    check("V-ROLLACT-NO-ASK-NO-STEP", calls == [],
          "a session that never crossed the wall is never asked to clear")
    clear(wd, s)

    print(f"ROLLACT_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
