#!/usr/bin/env python3
"""One meaning of DONE across the three layers that state it.

Phase III section 30 asked whether `software-best-practices` and the always-read
core layer are correctly layered or accidentally duplicative. Measured, three
separate files carried completion vocabulary:

  parts/core.md                        LAW IX -- thirteen graded rungs
  modules/governance-overlay/core.md   "Complete = every route responds ..."
  ~/.claude/skills/software-best-practices/instructions.md
                                       a 5-gate cascade, "anything less = NOT
                                       complete"

Two of those are binary and one is graded, and the subordination chain ran
software-best-practices -> governance-overlay and stopped there. The overlay did
not know LAW IX existed, so the graded authority sat at the top of the always-read
layer with nothing pointing at it. That is a split-brain: not a contradiction
anyone had hit yet, but three independent restatements of one decision, each
free to drift.

The resolution is one semantic owner with projections, not a merge. LAW IX owns
the verdict; the gate cascades PRODUCE evidence for it; the routes-and-screens
line is the web instantiation and must not be applied to firmware. This suite
pins that shape so it cannot quietly come apart.

It reads the global skill but never writes it. HR-001 reserves writes under
~/.claude/ to the Owner, and a detector does not need write access to notice
drift -- so if that file's subordination clause is ever removed, this goes red
and names the Owner-side edit rather than performing it.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent

CORE = _ROOT / "parts" / "core.md"
OVERLAY = _ROOT / "modules" / "governance-overlay" / "core.md"
SBP = Path.home() / ".claude" / "skills" / "software-best-practices" / "instructions.md"

PASSES = 0
FAILS = 0


def check(gate: str, cond: bool, evidence: str) -> None:
    global PASSES, FAILS
    if cond:
        PASSES += 1
        print(f"  OK   {gate}  {evidence}")
    else:
        FAILS += 1
        print(f"  FAIL {gate}  {evidence}")


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


def main() -> int:
    core, overlay, sbp = _read(CORE), _read(OVERLAY), _read(SBP)

    # Positive control. Every assertion below is a substring test, and a
    # substring test against an unreadable file passes nothing but also
    # accuses nothing useful -- so prove the documents were actually loaded.
    check("V-AUTH-SOURCES-READ",
          len(core) > 1000 and len(overlay) > 1000,
          f"core.md {len(core)}B, overlay core.md {len(overlay)}B")

    # --- the authority owns the verdict ------------------------------------
    check("V-AUTH-LADDER-IS-AUTHORITY",
          "LAW IX" in core and "strength_ladder" in core,
          "parts/core.md carries LAW IX and names its grader")
    check("V-AUTH-LADDER-ALWAYS-READ",
          "core.md" in _read(_ROOT / "SKILL.md"),
          "the router declares parts/core.md always-read, so the authority is "
          "warm for every task without being requested")

    # --- the projections defer to it ---------------------------------------
    check("V-AUTH-OVERLAY-DEFERS",
          "LAW IX" in overlay and "parts/core.md" in overlay,
          "governance-overlay names LAW IX as the authority for its gates")
    check("V-AUTH-OVERLAY-EVIDENCE-NOT-VERDICT",
          "PRODUCE evidence" in overlay and "do not issue the verdict" in overlay,
          "the overlay's gates are declared evidence producers, not judges")
    check("V-AUTH-LAW2-PRECEDES",
          "LAW II" in overlay and "EXECUTED" in overlay,
          "the overlay records that a green gate is a proxy and caps the claim")

    # --- the web instantiation is marked as one --------------------------
    # The failure this prevents is a firmware or CLI task being graded against
    # routes and screens it does not have, which is how a universal law turns
    # into one domain's checklist wearing a universal label.
    check("V-AUTH-DOMAIN-SCOPED",
          "instantiation" in overlay,
          "routes/screens/forms is marked as the web projection, not the law")

    # --- the global skill's end of the chain -------------------------------
    if not sbp:
        check("V-AUTH-SBP-PRESENT", False,
              f"the incumbent global skill was not readable at {SBP}")
    else:
        check("V-AUTH-SBP-PRESENT", True, f"incumbent read, {len(sbp)}B")
        check("V-AUTH-SBP-SUBORDINATES",
              "OVERRIDE this skill's own completion criteria" in sbp
              and "governance-overlay" in sbp,
              "software-best-practices still defers its completion criteria to "
              "the overlay, so it inherits LAW IX transitively")
        # It must not grow its own rival grading vocabulary. Deferring while
        # also defining rungs would be the split-brain returning by another
        # route.
        check("V-AUTH-SBP-NO-RIVAL-LADDER",
              "PRODUCTION-REALITY-VERIFIED" not in sbp
              and "REGRESSION-PROVEN" not in sbp,
              "the incumbent states no competing rung vocabulary of its own")

    print(f"COMPLETION_AUTHORITY_PASS={PASSES}/{PASSES + FAILS}  "
          f"threshold={PASSES + FAILS}/{PASSES + FAILS}")
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
