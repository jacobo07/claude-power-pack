#!/usr/bin/env python3
"""V-EVCLASS-* gates for the evidence-class axis in modules/done_gate/strength_ladder.py (X6)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.done_gate.strength_ladder import (LADDER_FAILED, OVERSTATED, SUPPORTED,  # noqa: E402
                                               UNDETERMINED, assess_evidence_class, weakest_class)

passes = fails = 0


def check(gate, cond, good, bad):
    global passes, fails
    if cond:
        passes += 1
        print(f"  PASS {gate}: {good}")
    else:
        fails += 1
        print(f"  FAIL {gate}: {bad}")


def main() -> int:
    a = assess_evidence_class("REMOTE_REALITY", {"REMOTE_REALITY": True})
    check("V-EVCLASS-SUPPORTED", a.outcome == SUPPORTED, "an observed class supports its own claim", f"{a}")
    a = assess_evidence_class("PRODUCTION_REALITY", {"MODEL_CHECKED": True, "LOCAL_REALITY": True,
                                                     "REMOTE_REALITY": True})
    check("V-EVCLASS-NO-PROMOTION", a.outcome == UNDETERMINED and a.highest_supported == "REMOTE_REALITY",
          "remote evidence does not become production evidence (UNDETERMINED, best=REMOTE)", f"{a}")
    a = assess_evidence_class("REMOTE_REALITY", {"MODEL_CHECKED": True})
    check("V-EVCLASS-MODEL-IS-NOT-REALITY", a.outcome == UNDETERMINED,
          "a model check never supports a reality claim", f"{a}")
    a = assess_evidence_class("LOCAL_REALITY", {"REMOTE_REALITY": True})
    check("V-EVCLASS-NO-SIDEWAYS", a.outcome == UNDETERMINED,
          "a plane that sorts higher is still a different plane: remote does not prove local", f"{a}")
    a = assess_evidence_class("HARDWARE_REALITY", {"SIMULATED": True, "HARDWARE_REALITY": False})
    check("V-EVCLASS-NEGATIVE", a.outcome == OVERSTATED and a.missing == ["HARDWARE_REALITY"],
          "an observed failure is OVERSTATED, distinct from never-observed", f"{a}")
    a = assess_evidence_class("local-reality", {"local reality": True})
    check("V-EVCLASS-NORMALISE", a.outcome == SUPPORTED, "spelling variants normalise", f"{a}")
    for claim, obs in (("PROVEN", {}), ("LOCAL_REALITY", {"CLOUD_REALITY": True})):
        a = assess_evidence_class(claim, obs)
        check(f"V-EVCLASS-UNKNOWN-NAME-{claim}", a.outcome == LADDER_FAILED,
              "an unrecognised class is refused, never mapped", f"{a}")
    check("V-EVCLASS-WEAKEST", weakest_class(["REMOTE_REALITY", "MODEL_CHECKED", "LOCAL_REALITY"])
          == "MODEL_CHECKED" and weakest_class([]) == "THEORETICAL",
          "a composite claim is as strong as its weakest link; nothing observed = THEORETICAL", "wrong")
    print(f"EVCLASS_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
