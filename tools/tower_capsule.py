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
    python tools/tower_capsule.py --all      one capsule per estate project

  exit 0  capsule produced (in whatever state)
  exit 1  --all: at least one capsule is PRODUCER_FAILURE
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


def produce_all() -> int:
    """One capsule per PROJECT in the estate. Produced on the MAIN repo, never
    on the worktree family_scan happens to keep as the population's
    representative: that choice depends on SCAN_ROOTS order (the Power Pack is
    represented by a worktree under Apps), and a capsule keyed to a worktree is
    one the main checkout's prompt path never reads."""
    sys.path.insert(0, _HERE)
    from family_scan import find_repos, main_repo_of
    repos = sorted({main_repo_of(r) for r in find_repos()})
    counts: dict[str, int] = {}
    for repo in repos:
        cap = produce(repo)
        state = cap.get("state", "?")
        counts[state] = counts.get(state, 0) + 1
        extra = "  family=%s" % (cap.get("family_layer") or {}).get("state")
        if state == AVAILABLE:
            extra += "  entries=%d own=%d inherited=%d verified=%d lessons=%d" % (
                cap.get("entries", 0), cap.get("own_entries", 0),
                cap.get("inherited_entries", 0), cap.get("verified_entries", 0),
                len(cap.get("lessons") or []))
        print("  %-18s %s%s" % (state, repo, extra))
    print()
    print("CAPSULES %d  %s" % (len(repos), counts))
    return 0 if PRODUCER_FAILURE not in counts else 1


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        return produce_all()
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
    fam = cap.get("family_layer") or {}
    print("  family      %s -- %s" % (fam.get("state"), fam.get("reason")))
    if cap.get("state") == AVAILABLE:
        print("  entries     %d  (inherited %d, harvested %d, verified %d)"
              % (cap.get("entries", 0), cap.get("inherited_entries", 0),
                 cap.get("harvested_entries", 0), cap.get("verified_entries", 0)))
        print("  destinations %s" % cap.get("destinations"))
        print("  lessons     %d handed to the prompt path" % len(cap.get("lessons") or []))
    print("  written     %s" % capsule_path(target))
    return 0


if __name__ == "__main__":
    sys.exit(main())
