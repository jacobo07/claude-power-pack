#!/usr/bin/env python
"""V-TIER-* gates for tools/tier_routing.py. Mutation drill: TIER_DRILL_DIR holds a mutated copy."""
from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if os.environ.get("TIER_DRILL_DIR"):
    sys.path.insert(0, os.environ["TIER_DRILL_DIR"])
sys.path.insert(1 if os.environ.get("TIER_DRILL_DIR") else 0, str(HERE))
import route_admission as ra  # noqa: E402
import tier_routing as tr  # noqa: E402

passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


check("V-TIER-01 classes map",
      [tr.tier_for(c) for c in ("deterministic", "known_transform", "bounded_coding", "novel", "owner_reality")]
      == [tr.ZERO_MODEL, tr.SLIM, tr.SLIM, tr.DEFAULT, tr.DEFAULT])
check("V-TIER-02 unknown/None class -> DEFAULT, not cheap",
      tr.tier_for("mystery") == tr.DEFAULT and tr.tier_for(None) == tr.DEFAULT)
e = tr.escalate(tr.SLIM, tr.FAILED)
check("V-TIER-03 failed verification raises one rung", e["tier"] == tr.DEFAULT and e["escalated"], e)
check("V-TIER-04 passed verification holds", not tr.escalate(tr.SLIM, tr.PASSED)["escalated"])
for v in (None, "", "UNKNOWN", "failed", "NOT_PROVEN"):
    r = tr.escalate(tr.SLIM, v)
    check(f"V-TIER-05 unobserved verification {v!r} never escalates",
          not r["escalated"] and r["tier"] == tr.SLIM, r["reason"])
check("V-TIER-06 failure at DEFAULT stops", tr.escalate(tr.DEFAULT, tr.FAILED)["stop"])
check("V-TIER-07 ZERO_MODEL has no worker", tr.worker_for("deterministic", "w", 3) is None)
floors = ra.load_floors()
check("V-TIER-08 PROFILE names exist in the floor table", all(p in floors["profiles"] for p in tr.PROFILE.values()))
env = {"target": 3_000_000, "warn": 4_000_000, "stop": 5_000_000, "calls": 30}
def cost(cls, n):
    return ra.admit({"envelope": env, "workers": [tr.worker_for(cls, "w", n, 6000)]}, floors).get("need")


# FINDING: the estimator charges slim-t2 quadratic growth x physical_ratio 2.4, so slim is cheaper only for
# short units; at 20 calls it already costs MORE than default (2.88M vs 2.34M). Measured 26k vs 137k per call
# was a 38-call renewal. Route slim units short and let escalation, not length, buy capability.
check("V-TIER-09 slim cheaper than default for a short unit (5 calls)", cost("known_transform", 5) < cost("novel", 5),
      (cost("known_transform", 5), cost("novel", 5)))
check("V-TIER-11 crossover is real: slim costs more at 20 calls (estimator finding, not hidden)",
      cost("known_transform", 20) > cost("novel", 20), (cost("known_transform", 20), cost("novel", 20)))
try:
    tr.escalate("BOGUS", tr.FAILED)
    check("V-TIER-10 unknown tier rejected", False)
except ValueError:
    check("V-TIER-10 unknown tier rejected", True)

print(f"{passes} passed, {fails} failed")
sys.exit(1 if fails else 0)
