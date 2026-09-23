"""CLI shim over modules.tower.capsule. Produces the Mission Baseline Capsule.

The implementation moved to `modules/tower/capsule.py` when the prompt path
began reading it: a reader that `modules/gsd_x/tier.py` imports cannot live
under `tools/`, and duplicating the state-path logic here would have given the
capsule TWO owners -- the exact failure this mission spent its length measuring.

This file is the out-of-band entry point. G-3 (vault/audits/ucr_cif/
09_G3_DECISION.md) decided that lane: the producer never runs inside a chain
with a latency deadline, because 815 measured abandonments showed there is no
safe hook lane, not even SessionStart. Run it from a command, a scheduled task,
or by hand.

    python tools/tower_capsule.py [repo_path]

  exit 0  capsule produced (in whatever state)
  exit 2  repo identity unresolved -- nothing written
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, ".."))
if _PP_ROOT not in sys.path:
    sys.path.insert(0, _PP_ROOT)

from modules.tower.capsule import (  # noqa: E402
    AVAILABLE,
    PRODUCER_FAILURE,
    capsule_path,
    produce,
)


def main() -> int:
    target = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    cap = produce(target)
    if cap.get("state") == PRODUCER_FAILURE and "identity" in str(cap.get("reason")):
        print("CAPSULE: %s -- %s" % (cap["state"], cap["reason"]))
        return 2
    print("CAPSULE %s" % cap.get("state"))
    print("  repo        %s" % cap.get("repo"))
    print("  repo_key    %s" % cap.get("repo_key"))
    print("  family      %s" % cap.get("family"))
    print("  reason      %s" % cap.get("reason"))
    if cap.get("state") == AVAILABLE:
        print("  entries     %d  (verified: %d)"
              % (cap.get("entries", 0), cap.get("verified_entries", 0)))
        print("  destinations %s" % cap.get("destinations"))
    print("  written     %s" % capsule_path(target))
    return 0


if __name__ == "__main__":
    sys.exit(main())
