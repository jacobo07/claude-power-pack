"""V-EPOCH-BESHADOW gates (CCR A4): the weighted break-even verdict is recorded beside the continuation ceiling's
decision and never changes it.
    python tools/test_gsd_epoch_breakeven_shadow.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import gsd_epoch as ge  # noqa: E402

passes = fails = 0
MODEL = {"cls": "generic", "n": 10, "capsule": 1000.0, "r": 3, "floor": 20000.0, "R": 5000.0, "rehyd_cost": 10000.0,
         "first_overhead": 500.0, "g": 2000.0, "lengths": [200] * 10}


def gate(name, cond, evidence):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"{'PASS' if cond else 'FAIL'} {name}: {evidence}")


def rec(**kw):
    base = {"mission_id": "m-test", "epoch": 3, "state": "RUNNING", "owner": {"session_id": "sess-1"}}
    base.update(kw)
    return base


def clear(_sid, _now):
    return {"verdict": "CLEAR", "pending": [], "unconsumed": []}


def main() -> int:
    ge.wall_evidence = lambda *a, **k: None
    ge._transcript = lambda sid: None
    with tempfile.TemporaryDirectory() as d:
        mp = Path(d) / "be.json"
        mp.write_text(json.dumps({"classes": {"generic": {"model": MODEL}}}))

        def shadow(r, sid, n):
            return ge.breakeven_shadow(r, sid, n, calls=lambda s: 20, model_path=mp)

        def run(n):
            return ge.decide_turn_end(rec(), 1000.0, tokens=lambda s: n, children=clear,
                                      last_turn_at=lambda s: None, shadow=shadow)

        lo = run(150_000)   # under the 300k ceiling, carry 124k > X* ~ 38k with 180 calls expected
        sb = lo["evidence"]["shadow_breakeven"]
        gate("V-EPOCH-BESHADOW-DISAGREES-RECORDED", lo["decision"] == ge.CONTINUE and sb["would"] == ge.ROTATE,
             f"ceiling={lo['decision']} shadow={sb}")
        small = run(40_000)
        gate("V-EPOCH-BESHADOW-BELOW-XSTAR", small["decision"] == ge.CONTINUE
             and small["evidence"]["shadow_breakeven"]["would"] == ge.CONTINUE, small["evidence"]["shadow_breakeven"])
        hi = run(310_000)
        gate("V-EPOCH-BESHADOW-CEILING-UNCHANGED", hi["decision"] == ge.ROTATE
             and hi["evidence"].get("trigger") == "economic_ceiling", hi["reason"])
        un = run(None)
        gate("V-EPOCH-BESHADOW-UNMEASURED", un["decision"] == ge.ROTATE
             and un["evidence"]["shadow_breakeven"]["would"] is None, un["evidence"]["shadow_breakeven"])
        broken = ge.breakeven_shadow(rec(), "sess-1", 150_000, calls=lambda s: 20, model_path=Path(d) / "missing.json")
        gate("V-EPOCH-BESHADOW-NEVER-RAISES", broken["would"] is None and "reason" in broken, broken)

        rows = []
        saved = ge.lr.ledger_append
        ge.lr.ledger_append = lambda mid, event, **f: rows.append((event, f)) or True
        try:
            ge.record_cause("m-test", rec(), lo, ge.RESUME, worker="sess-1")
        finally:
            ge.lr.ledger_append = saved
        row = rows[-1][1] if rows else {}
        gate("V-EPOCH-BESHADOW-LEDGER-ROW", rows and rows[-1][0] == "launch_cause"
             and (row.get("shadow_breakeven") or {}).get("would") == ge.ROTATE and row.get("mechanism") == ge.RESUME,
             f"launch_cause.shadow_breakeven={row.get('shadow_breakeven')}")
    print(f"EPOCH_BESHADOW_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
