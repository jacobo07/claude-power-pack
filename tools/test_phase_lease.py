#!/usr/bin/env python
"""V-LEASE-* gates for tools/phase_lease.py. Every refusal is paired with a control that is admitted."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase_lease as pl  # noqa: E402

passes = fails = 0


def check(gate: str, cond: bool, evidence: str) -> None:
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {evidence}")
    else:
        fails += 1
        print(f"FAIL {gate}: {evidence}")


def lease(**kw):
    base = dict(phase="1", forecast=1_000_000, base=10_000_000, state_file="STATE.md", set_at=1.0)
    base.update(kw)
    return pl.make_lease(**base)


def raises(**kw) -> bool:
    try:
        lease(**kw)
    except pl.LeaseError:
        return True
    return False


def main() -> int:
    L = lease()
    # --- judge: the four verdicts
    v = pl.judge(L, 10_000_000 + 900_000, "1")
    check("V-LEASE-OK", v["verdict"] == pl.OK and v["spend"] == 900_000, f"under warn -> {v['verdict']}")
    v = pl.judge(L, 10_000_000 + 1_300_000, "1")
    check("V-LEASE-WARN", v["verdict"] == pl.WARN, f"1.3x forecast -> {v['verdict']}")
    v = pl.judge(L, 10_000_000 + 1_500_000, "1")
    check("V-LEASE-HARD-INCLUSIVE", v["verdict"] == pl.WARN, "exactly 1.5x is not yet a trip (strictly greater)")
    v = pl.judge(L, 10_000_000 + 1_500_001, "1")
    check("V-LEASE-TRIP", v["verdict"] == pl.TRIP and "reforecast" in v["reason"], f"1.5x+1 -> {v['verdict']}")
    # --- ambiguity is BLOCKED, never permission
    v = pl.judge(L, None, "1")
    check("V-LEASE-UNMEASURED", v["verdict"] == pl.BLOCKED, "spend None -> BLOCKED (control: measured -> OK above)")
    v = pl.judge(L, 10_100_000, None)
    check("V-LEASE-PHASE-UNREADABLE", v["verdict"] == pl.BLOCKED, "phase_now None -> BLOCKED")
    v = pl.judge(L, 10_100_000, "2")
    check("V-LEASE-PHASE-MOVED", v["verdict"] == pl.BLOCKED and "new lease" in v["reason"],
          "GSD moved to phase 2 under a phase-1 lease -> BLOCKED")
    v = pl.judge(L, 9_000_000, "1")
    check("V-LEASE-BASE-ABOVE-SPENT", v["verdict"] == pl.BLOCKED, "processed below base -> BLOCKED, not negative spend")
    check("V-LEASE-NONE", pl.judge(None, 5, "1")["verdict"] == pl.OK, "no lease -> nothing to judge")
    # --- model prose cannot move the verdict: judge is a pure function of (lease, spend, phase)
    over = pl.judge(L, 10_000_000 + 2_000_000, "1")
    again = pl.judge(L, 10_000_000 + 2_000_000, "1")
    check("V-LEASE-DETERMINISTIC", over == again and over["verdict"] == pl.TRIP, "same inputs, same TRIP")
    # --- constructor refusals, each paired with the valid control
    check("V-LEASE-CONTROL", not raises(), "valid lease constructs")
    check("V-LEASE-REJECT-PHASE", raises(phase="phase one"), "non-numeric phase refused")
    check("V-LEASE-REJECT-FORECAST", raises(forecast=0) and raises(forecast=-5) and raises(forecast=1.5),
          "zero, negative, float forecast refused")
    check("V-LEASE-REJECT-BOOL", raises(forecast=True), "bool is not a token count")
    check("V-LEASE-REJECT-RATIO", raises(warn=1.6) and raises(hard=1.1) and raises(warn=1.0),
          "need 1 < warn < hard")
    check("V-LEASE-REJECT-STATEFILE", raises(state_file=" "), "state_file required")
    check("V-LEASE-REJECT-BASE", raises(base=-1), "negative base refused")
    check("V-LEASE-WRITER", L["set_by"] == "envelope", "set_by is stamped envelope")
    # --- current_phase reads real STATE.md shapes
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "STATE.md"
        p.write_text("---\ncurrent_phase: 1 — Hard enforcement\nstatus: x\n---\n", encoding="utf-8")
        check("V-LEASE-PHASE-READ", pl.current_phase(p) == "1", f"read {pl.current_phase(p)!r}")
        p.write_text("---\ncurrent_phase: \"2.1\"\n---\n", encoding="utf-8")
        check("V-LEASE-PHASE-DECIMAL", pl.current_phase(p) == "2.1", f"read {pl.current_phase(p)!r}")
        p.write_text("﻿---\ncurrent_phase: 3\n---\n", encoding="utf-8")
        check("V-LEASE-PHASE-BOM", pl.current_phase(p) == "3", "BOM tolerated")
        p.write_text("---\nstatus: x\n---\n", encoding="utf-8")
        check("V-LEASE-PHASE-ABSENT", pl.current_phase(p) is None, "no key -> None")
        check("V-LEASE-PHASE-MISSING-FILE", pl.current_phase(Path(d) / "nope.md") is None, "no file -> None")
    print(f"PHASE_LEASE_PASS={passes}/{passes + fails}  threshold=N/N")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
