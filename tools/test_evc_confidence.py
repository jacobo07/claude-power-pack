#!/usr/bin/env python
"""V-EVC-CONF-* gates for tools/evc_confidence.py (pure state machine + miss taxonomy)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evc_confidence as ec  # noqa: E402

passes = fails = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global passes, fails
    if ok:
        passes += 1
        print(f"PASS {name}")
    else:
        fails += 1
        print(f"FAIL {name} {detail}")


def miss(ratio: float, kind: str | None = None, need: int = 100) -> dict:
    m = {"need": need, "actual": int(need * ratio)}
    if kind:
        m["kind"] = kind
    return m


# V-EVC-CONF-STATES
check("states: n=0", ec.state(0, []) == "UNKNOWN")
check("states: n=1,2", ec.state(1, []) == "EXPLORATORY" and ec.state(2, []) == "EXPLORATORY")
check("states: n=3,4", ec.state(3, []) == "PROVISIONAL" and ec.state(4, []) == "PROVISIONAL")
check("states: n>=5", ec.state(5, []) == "CALIBRATED" and ec.state(50, []) == "CALIBRATED")
check("states: control 1.1x hit stays CALIBRATED", ec.state(5, [miss(1.1)]) == "CALIBRATED")

# V-EVC-CONF-DEGRADED
check("degraded: one 2x miss", ec.state(5, [miss(2.0, "CALL_COUNT")]) == "DEGRADED")
check("degraded: control 1.25x exactly is no miss", ec.state(5, [miss(1.25)]) == "CALIBRATED")

# V-EVC-CONF-INVALIDATED-3
three = [miss(3.0, "CALL_COUNT")] * 3
check("inval3: three comparable", ec.state(6, three) == "INVALIDATED")
mixed = [miss(3.0, "CALL_COUNT"), miss(3.0, "CONTEXT_GROWTH"), miss(3.0, "REPAIR")]
check("inval3: control three kinds -> DEGRADED", ec.state(6, mixed) == "DEGRADED")

# V-EVC-CONF-INVALIDATED-OOM
check("oom: 10x -> INVALIDATED", ec.state(6, [miss(10.0, "RESOURCE_ANOMALY")]) == "INVALIDATED")
check("oom: isolated anomaly -> DEGRADED",
      ec.state(6, [miss(10.0, "RESOURCE_ANOMALY")], isolated_anomaly="host swap storm, log x") == "DEGRADED")
check("oom: control 9.9x -> DEGRADED", ec.state(6, [miss(9.9, "RESOURCE_ANOMALY")]) == "DEGRADED")

# V-EVC-CONF-TAXONOMY
WANT = ["CALL_COUNT", "CONTEXT_GROWTH", "WORK_CLASS_MISCLASSIFICATION", "PROOF_TAIL", "CLOSEOUT_TAIL", "REPAIR",
        "CONTROL_PLANE_LEAK", "SEMANTIC_SCOPE", "STALE_USAGE_TRUTH", "RESOURCE_ANOMALY",
        "PROVIDER_BEHAVIOR_CHANGE", "PROFILE_TRANSFER", "UNKNOWN"]
check("taxonomy: exactly 13", sorted(ec.TAXONOMY) == sorted(WANT) and len(ec.TAXONOMY) == 13)
check("taxonomy: calls", ec.classify_miss(100, 300, {"calls_ratio": 2.0, "ctx_ratio": 1.0}) == "CALL_COUNT")
check("taxonomy: ctx", ec.classify_miss(100, 300, {"ctx_ratio": 2.0}) == "CONTEXT_GROWTH")
check("taxonomy: empty -> UNKNOWN", ec.classify_miss(100, 300, {}) == "UNKNOWN")
check("taxonomy: FIOS_MAP complete",
      all(isinstance(ec.FIOS_MAP.get(k), str) and ec.FIOS_MAP[k] for k in ec.TAXONOMY))

# V-EVC-CONF-ADMIT
check("admit: UNKNOWN/INVALIDATED False", not ec.may_admit_large("UNKNOWN") and not ec.may_admit_large("INVALIDATED"))
check("admit: CALIBRATED/PROVISIONAL True", ec.may_admit_large("CALIBRATED") and ec.may_admit_large("PROVISIONAL"))
check("admit: DEGRADED only with tranche",
      not ec.may_admit_large("DEGRADED") and ec.may_admit_large("DEGRADED", tranche=True))
check("admit: control INVALIDATED+tranche False", not ec.may_admit_large("INVALIDATED", tranche=True))

print(f"{passes} passed, {fails} failed")
sys.exit(1 if fails else 0)
