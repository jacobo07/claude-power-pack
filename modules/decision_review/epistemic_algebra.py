#!/usr/bin/env python3
"""epistemic_algebra.py -- CPCSC Tier-B B2: the epistemic-algebra join
(DRK-00 x DAIF-01 x ACIS).

Three owners each hold a piece of "how sure are we" and none holds the
arithmetic over it. ACIS (`modules/fable_distillation/epistemic_ladder.py`)
derives a single claim's E0-E7 level and writes nothing else. DAIF-01 Part
VIII types a Confidence field into a ten-status lattice mapped onto that
ladder ("an inference may never be typed as a fact") but DAIF-01 is
deliberately inert -- a schema the estate reads, not a pipeline (DAIF-01
1.5) -- so its own "Part XII checker" that would enforce the cardinal rule
was never built. DRK-03 composes the same ladder into an evidence-burden
table ("a single E3+ item lifts the ceiling; all-E2 support caps it") but
the only executable form of that rule lives inside
`decision_kernel.py::evidence_burden_met()`, hard-bound to DRK's own
`DecisionObject`. A fourth site, `providers.py::evidence_levels_for()`,
independently regex-parses "E0".."E7" to an int because nothing shared
does it. Three textual claims about one axis, zero shared arithmetic --
the exact drift DAIF-01 9.3/9.4 convicts for names, arriving instead for
levels.

This module is that arithmetic, decision-agnostic and reusable by any of
the three (or a future DAIF-02/04/07 consumer) without needing a
DecisionObject:

  acis_rank / acis_meets   -- the one canonical ACIS ordinal, accepting
                              either representation in the wild today (the
                              epistemic_ladder.py "E0".."E7" string and the
                              decision_kernel.py/providers.py plain int)
  acis_max / acis_min      -- the join/meet combinators: DRK-03's
                              "strongest-support level" rule (max) and its
                              dual, the weakest-link floor over a
                              conjunctive evidence set (min)
  fact_grade_permitted     -- DAIF-01 Part VIII 8.4's cardinal rule made
                              executable: a status is fact-grade
                              (observed/demonstrated/verified) only if the
                              ACIS derivation behind it clears the E3 gate
                              8.3 assigns to `demonstrated`

Composes, never re-narrates: no level is assigned here (that stays ACIS's
alone, per DRK-03's own discipline), no Confidence status is invented
(that stays DAIF-01's taxonomy), and DRK's own DecisionObject burden logic
is untouched -- this is the shared layer underneath it, not a replacement.

Fail-open ABSOLUTE on every function: an unrecognized or malformed input
degrades to the floor (E0 / not-permitted), never raises, never inflates.
"""
from __future__ import annotations

import argparse
import re

ACIS_LEVELS = ("E0", "E1", "E2", "E3", "E4", "E5", "E6", "E7")
_E_PATTERN = re.compile(r"^E([0-7])$")

# DAIF-01 Part VIII 8.2's three "assertoric, fact-grade" Confidence statuses
# (8.4: "A fact is a claim at observed, demonstrated, or verified status").
_FACT_GRADE = frozenset({"observed", "demonstrated", "verified"})
# 8.3: "demonstrated" is licensed once a claim is "proven at the ladder's E3
# gate"; "verified" requires the strictly higher UKDL rungs (8.3), so E3 is
# the conservative floor for the whole fact-grade set -- the gate a status
# must clear at minimum, never the gate it is guaranteed to satisfy.
_FACT_GRADE_FLOOR = "E3"


def acis_rank(level) -> int:
    """Canonical ordinal position (0-7) of an ACIS level.

    Accepts either representation already in use across the estate: the
    epistemic_ladder.py string form ("E0".."E7") or the plain int 0-7 that
    decision_kernel.py/providers.py carry once parsed -- this is the one
    place both resolve to the same ordinal, replacing the ad hoc regex
    parse duplicated in providers.py::evidence_levels_for.

    Fail-open -> 0: an unrecognized token can never rank above the floor.
    """
    try:
        if isinstance(level, bool):
            return 0
        if isinstance(level, int):
            return level if 0 <= level <= 7 else 0
        m = _E_PATTERN.match(str(level or "").strip().upper())
        return int(m.group(1)) if m else 0
    except Exception:  # noqa: BLE001 -- fail-open ABSOLUTE
        return 0


def acis_meets(level, floor) -> bool:
    """True iff `level` clears `floor` on the canonical ordinal.

    Fail-open -> False: malformed input can never satisfy a burden.
    """
    try:
        return acis_rank(level) >= acis_rank(floor)
    except Exception:  # noqa: BLE001 -- fail-open ABSOLUTE
        return False


def acis_max(*levels) -> str:
    """The join operator: DRK-03's "strongest-support level" rule, generalized --
    a single E3+ item lifts the ceiling; all-E2 support caps it.

    Empty or all-unrecognized input -> 'E0' (never inflated).
    """
    try:
        ranks = [acis_rank(lvl) for lvl in levels]
        return ACIS_LEVELS[max(ranks)] if ranks else "E0"
    except Exception:  # noqa: BLE001 -- fail-open ABSOLUTE
        return "E0"


def acis_min(*levels) -> str:
    """The meet operator: the weakest-link level across a conjunctive set,
    where every item must independently clear the result.

    Empty input -> 'E0' (a vacuous conjunction floors, it never inflates).
    """
    try:
        ranks = [acis_rank(lvl) for lvl in levels]
        return ACIS_LEVELS[min(ranks)] if ranks else "E0"
    except Exception:  # noqa: BLE001 -- fail-open ABSOLUTE
        return "E0"


def fact_grade_permitted(status, level) -> bool:
    """DAIF-01 Part VIII 8.4's cardinal rule, executable: "an inference may
    never be typed as a fact."

    True iff `status` is one of DAIF-01's fact-grade Confidence statuses
    (observed/demonstrated/verified) AND the ACIS level behind it clears
    the E3 gate 8.3 assigns to `demonstrated`. This is the Part XII
    "checker" DAIF-01 names but never builds -- DAIF-01 is deliberately
    inert (Part I 1.5: "runs no pipeline, gates no deploy, issues no
    verdict"); this is the mechanism, composing ACIS's ladder via
    `acis_meets` and never re-deriving a parallel scale.

    Fail-open -> False: an unmapped status or malformed level is never
    licensed as fact-grade.
    """
    try:
        status_norm = str(status or "").strip().lower()
        if status_norm not in _FACT_GRADE:
            return False
        return acis_meets(level, _FACT_GRADE_FLOOR)
    except Exception:  # noqa: BLE001 -- fail-open ABSOLUTE
        return False


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Epistemic algebra: ACIS rank/join/meet + DAIF-01 fact-grade check "
                     "(DRK-00 x DAIF-01 x ACIS join, CPCSC Tier-B B2)")
    ap.add_argument("--rank", metavar="LEVEL", help="ordinal rank of an ACIS level")
    ap.add_argument("--max", nargs="+", metavar="LEVEL", help="join (strongest) of levels")
    ap.add_argument("--min", nargs="+", metavar="LEVEL", help="meet (weakest) of levels")
    ap.add_argument("--fact-grade", nargs=2, metavar=("STATUS", "LEVEL"),
                     help="is a DAIF-01 Confidence status fact-grade at this ACIS level?")
    args = ap.parse_args(argv)
    if args.rank is not None:
        print(acis_rank(args.rank))
        return 0
    if args.max:
        print(acis_max(*args.max))
        return 0
    if args.min:
        print(acis_min(*args.min))
        return 0
    if args.fact_grade:
        print(fact_grade_permitted(*args.fact_grade))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
