"""V-EPOCH-CTXB gates: Context Budget is recorded as evidence of the epoch decision, never decides.
    python tools/test_gsd_epoch_context_budget.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import gsd_epoch as ge  # noqa: E402

passes = fails = 0


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
    ge.wall_evidence = lambda *a, **k: None  # no wall in these cases
    ge._transcript = lambda sid: None         # no transcript: size/age unmeasured

    d = ge.decide_turn_end(rec(), 1000.0, tokens=lambda s: 60_000, children=clear, last_turn_at=lambda s: None)
    cb = d["evidence"].get("context_budget") or {}
    gate("V-EPOCH-CTXB-RECORDED", cb.get("band") == "comfortable" and cb.get("state") in ("MEASURED", "PARTIAL"),
         f"decision={d['decision']} budget={ {k: cb.get(k) for k in ('state', 'pressure', 'band', 'coverage')} }")
    gate("V-EPOCH-CTXB-POLICY-UNCHANGED-LOW", d["decision"] == ge.CONTINUE, d["reason"])

    d = ge.decide_turn_end(rec(), 1000.0, tokens=lambda s: 310_000, children=clear, last_turn_at=lambda s: None)
    cb = d["evidence"]["context_budget"]
    gate("V-EPOCH-CTXB-POLICY-UNCHANGED-HIGH", d["decision"] == ge.ROTATE and cb.get("band") == "critical",
         f"{d['decision']} {d['reason']} band={cb.get('band')}")

    d = ge.decide_turn_end(rec(), 1000.0, tokens=lambda s: None, children=clear, last_turn_at=lambda s: None)
    cb = d["evidence"]["context_budget"]
    gate("V-EPOCH-CTXB-UNMEASURED", d["decision"] == ge.ROTATE and cb.get("state") == "UNMEASURED"
         and cb.get("pressure") is None, f"{d['decision']} state={cb.get('state')}")

    real = ge.budget_evidence
    import modules.context_budget as mcb
    saved = mcb.epoch_reading
    mcb.epoch_reading = lambda **k: (_ for _ in ()).throw(RuntimeError("meter broke"))
    try:
        ev = real("sess-1", 1, 300_000, None)
        d = ge.decide_turn_end(rec(), 1000.0, tokens=lambda s: 60_000, children=clear, last_turn_at=lambda s: None)
    finally:
        mcb.epoch_reading = saved
    gate("V-EPOCH-CTXB-NEVER-RAISES", ev.get("state") == "UNMEASURED" and "meter broke" in ev.get("reason", "")
         and d["decision"] == ge.CONTINUE, f"{ev} -> decision {d['decision']}")

    rows = []
    saved_append = ge.lr.ledger_append
    ge.lr.ledger_append = lambda mid, event, **f: rows.append((event, f)) or True
    try:
        dec = ge.decide_turn_end(rec(), 1000.0, tokens=lambda s: 60_000, children=clear, last_turn_at=lambda s: None)
        ge.record_cause("m-test", rec(), dec, ge.RESUME, worker="sess-1")
    finally:
        ge.lr.ledger_append = saved_append
    row = rows[-1][1] if rows else {}
    gate("V-EPOCH-CTXB-LEDGER-ROW", rows and rows[-1][0] == "launch_cause"
         and (row.get("context_budget") or {}).get("band") == "comfortable",
         f"launch_cause.context_budget={row.get('context_budget')}")

    print(f"EPOCH_CTXB_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
