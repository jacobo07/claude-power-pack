#!/usr/bin/env python3
"""test_epistemic_algebra.py -- V-gates for CPCSC Tier-B B2 (epistemic-algebra
join, DRK-00 x DAIF-01 x ACIS).

Verifies the shared arithmetic over ACIS's E0-E7 ladder that no owner held
before this module: a canonical rank across both representations already
live in the estate (string "E0".."E7" and plain int), the join/meet
combinators DRK-03 states only in prose, and DAIF-01 Part VIII 8.4's
cardinal rule ("an inference may never be typed as a fact") made
executable. The core discipline is observed to refuse: a non-fact-grade
status is never permitted regardless of how strong the ACIS level is
(catches "assumption laundering", DRK-03 line 223), and every malformed
input degrades to the floor rather than raising or inflating.

  V-EA-RANK-STRING            "E0".."E7" strings resolve to their ordinal
  V-EA-RANK-INT                plain-int levels (decision_kernel.py's form) agree
  V-EA-RANK-UNRECOGNIZED        bogus / out-of-range / None -> 0, never a guess
  V-EA-MEETS                    E4 clears an E3 floor; E2 does not
  V-EA-MAX-JOIN                  a single E3+ item lifts an all-E2 ceiling
  V-EA-MIN-MEET                   the weakest item floors a conjunctive set
  V-EA-EMPTY-FLOORS                 no items -> E0 for both combinators
  V-EA-FACT-GRADE-PERMITTED    demonstrated/verified at/above E3 -> True
  V-EA-FACT-GRADE-DENIED-BELOW-FLOOR   observed at E2 -> False (fact-grade status, weak level)
  V-EA-FACT-GRADE-DENIED-NON-FACT-STATUS  inferred at E7 -> False (assumption laundering blocked)
  V-EA-FAIL-OPEN                malformed input never raises, never inflates
  V-EA-DETERMINISTIC            identical input -> identical output on re-run

Hermetic: pure functions, no I/O, no global state. V-<DOMAIN>-<NAME>;
EA_VERDICT line for the done-gate grep.
"""
from __future__ import annotations

import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.decision_review import epistemic_algebra as EA  # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS {gate}: {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {gate}: {diag}")


def test_rank_string() -> None:
    # Arrange / Act
    ranks = [EA.acis_rank(f"E{i}") for i in range(8)]
    # Assert
    if ranks == list(range(8)):
        _ok("V-EA-RANK-STRING", f"E0..E7 -> {ranks}")
    else:
        _fail("V-EA-RANK-STRING", f"expected 0..7, got {ranks}")


def test_rank_int() -> None:
    # Arrange -- decision_kernel.py/providers.py's plain-int representation.
    # Act
    r1, r2 = EA.acis_rank(3), EA.acis_rank("E3")
    # Assert -- both representations resolve to the same ordinal.
    if r1 == r2 == 3:
        _ok("V-EA-RANK-INT", "int(3) and 'E3' agree at rank 3")
    else:
        _fail("V-EA-RANK-INT", f"expected 3/3, got {r1}/{r2}")


def test_rank_unrecognized() -> None:
    # Arrange / Act
    vals = [EA.acis_rank("bogus"), EA.acis_rank(None), EA.acis_rank(-1), EA.acis_rank(99)]
    # Assert -- never a guess; floor is 0.
    if vals == [0, 0, 0, 0]:
        _ok("V-EA-RANK-UNRECOGNIZED", "bogus/None/-1/99 all floor to 0")
    else:
        _fail("V-EA-RANK-UNRECOGNIZED", f"expected all 0, got {vals}")


def test_meets() -> None:
    # Arrange / Act
    above = EA.acis_meets("E4", "E3")
    below = EA.acis_meets("E2", "E3")
    # Assert
    if above is True and below is False:
        _ok("V-EA-MEETS", "E4>=E3 True, E2>=E3 False")
    else:
        _fail("V-EA-MEETS", f"expected True/False, got {above}/{below}")


def test_max_join() -> None:
    # Arrange -- DRK-03: "a single E3+ item lifts the ceiling; all-E2 caps it."
    lifted = EA.acis_max("E2", "E2", "E3")
    capped = EA.acis_max("E2", "E2")
    # Assert
    if lifted == "E3" and capped == "E2":
        _ok("V-EA-MAX-JOIN", "one E3 item lifts; all-E2 caps at E2")
    else:
        _fail("V-EA-MAX-JOIN", f"expected E3/E2, got {lifted}/{capped}")


def test_min_meet() -> None:
    # Arrange -- a conjunctive set; the weakest item is the binding one.
    weakest = EA.acis_min("E4", "E2", "E5")
    # Assert
    if weakest == "E2":
        _ok("V-EA-MIN-MEET", "weakest of E4/E2/E5 is E2")
    else:
        _fail("V-EA-MIN-MEET", f"expected E2, got {weakest}")


def test_empty_floors() -> None:
    # Arrange / Act
    mx, mn = EA.acis_max(), EA.acis_min()
    # Assert -- vacuous input never inflates.
    if mx == "E0" and mn == "E0":
        _ok("V-EA-EMPTY-FLOORS", "empty acis_max/acis_min both floor to E0")
    else:
        _fail("V-EA-EMPTY-FLOORS", f"expected E0/E0, got {mx}/{mn}")


def test_fact_grade_permitted() -> None:
    # Arrange -- DAIF-01 8.3: demonstrated needs E3; verified needs the higher rungs.
    demo = EA.fact_grade_permitted("demonstrated", "E3")
    verf = EA.fact_grade_permitted("verified", "E5")
    # Assert
    if demo is True and verf is True:
        _ok("V-EA-FACT-GRADE-PERMITTED", "demonstrated@E3 and verified@E5 both permitted")
    else:
        _fail("V-EA-FACT-GRADE-PERMITTED", f"expected True/True, got {demo}/{verf}")


def test_fact_grade_denied_below_floor() -> None:
    # Arrange -- fact-grade status, but the ACIS level behind it is inference-grade.
    denied = EA.fact_grade_permitted("observed", "E2")
    # Assert
    if denied is False:
        _ok("V-EA-FACT-GRADE-DENIED-BELOW-FLOOR", "observed@E2 denied (below the E3 gate)")
    else:
        _fail("V-EA-FACT-GRADE-DENIED-BELOW-FLOOR", f"expected False, got {denied}")


def test_fact_grade_denied_non_fact_status() -> None:
    # Arrange -- DAIF-01 8.4 cardinal rule: an inference may never be typed as a
    # fact, no matter how strong the underlying level (assumption laundering).
    denied = EA.fact_grade_permitted("inferred", "E7")
    # Assert
    if denied is False:
        _ok("V-EA-FACT-GRADE-DENIED-NON-FACT-STATUS",
            "inferred@E7 denied -- status label gates, not level alone")
    else:
        _fail("V-EA-FACT-GRADE-DENIED-NON-FACT-STATUS", f"expected False, got {denied}")


def test_fail_open() -> None:
    # Arrange -- malformed inputs across every function.
    r1 = EA.acis_rank([1, 2])
    r2 = EA.acis_rank(object())
    m1 = EA.acis_max("garbage", None)
    m2 = EA.acis_min(object(), "E9000")
    f1 = EA.fact_grade_permitted(None, None)
    f2 = EA.fact_grade_permitted(object(), object())
    # Assert -- none raised; all degrade to the floor / False.
    ok = (r1 == 0 and r2 == 0 and m1 == "E0" and m2 == "E0" and f1 is False and f2 is False)
    if ok:
        _ok("V-EA-FAIL-OPEN", "malformed input across every fn degrades, never raises")
    else:
        _fail("V-EA-FAIL-OPEN", f"expected all-floor, got {r1}/{r2}/{m1}/{m2}/{f1}/{f2}")


def test_deterministic() -> None:
    # Arrange / Act -- two independent calls with identical input.
    a1 = (EA.acis_rank("E5"), EA.acis_max("E2", "E4"), EA.acis_min("E2", "E4"),
          EA.fact_grade_permitted("verified", "E4"))
    a2 = (EA.acis_rank("E5"), EA.acis_max("E2", "E4"), EA.acis_min("E2", "E4"),
          EA.fact_grade_permitted("verified", "E4"))
    # Assert
    if a1 == a2:
        _ok("V-EA-DETERMINISTIC", f"identical output across runs: {a1}")
    else:
        _fail("V-EA-DETERMINISTIC", f"nondeterministic: {a1} != {a2}")


def main() -> int:
    print("== epistemic_algebra (CPCSC Tier-B B2, DRK-00 x DAIF-01 x ACIS) ==")
    for t in (test_rank_string, test_rank_int, test_rank_unrecognized, test_meets,
              test_max_join, test_min_meet, test_empty_floors,
              test_fact_grade_permitted, test_fact_grade_denied_below_floor,
              test_fact_grade_denied_non_fact_status, test_fail_open,
              test_deterministic):
        t()
    total = _passes + _fails
    print(f"\nEA_PASS={_passes}/{total}  threshold={total}/{total}")
    print(f"EA_VERDICT={'PASS' if _fails == 0 else 'FAIL'}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
