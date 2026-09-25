"""V-TSEL-* -- injection is bounded, and a bound never makes a rule disappear.

Spec 2026-09-24 §4 caps injection at 8 entries / 1,400 characters per family
and every family's B0 already holds 15. Read literally ("exceeding it is a
compiler failure") S4 could never inject for any family; selecting a top-8
silently would drop seven constitutive rules from sight. The compiler instead
selects deterministically, names every deferred entry with its reason, and
loses nothing: injected + deferred == the input, always. The done-gate (P5)
judges the full set regardless of what was injected.

Run: python tools/test_tower_select.py     (exit 0 = all gates pass)
"""
from __future__ import annotations

import os
import random
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, ".."))
if _PP_ROOT not in sys.path:
    sys.path.insert(0, _PP_ROOT)

from modules.tower import baselines as bl  # noqa: E402
from modules.tower import select as sel  # noqa: E402

_PASS = 0
_FAIL = 0


def _check(gate, cond, evidence, diagnostic):
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print("  PASS %-38s %s" % (gate, evidence))
    else:
        _FAIL += 1
        print("  FAIL %-38s %s" % (gate, diagnostic))


def _e(i, check="", status="reviewed", n=60):
    return {"id": "e%02d" % i, "requirement": ("r%02d " % i) + "x" * (n - 4),
            "check": check, "status": status}


def _ids(xs):
    return [e["id"] for e in xs]


def main() -> int:
    print("V-TSEL gates")

    s = sel.select_for_injection([])
    _check("V-TSEL-EMPTY", s.injected == [] and s.deferred == [] and not s.overflow,
           "no entries -> nothing injected, no overflow", s)

    three = [_e(1), _e(2), _e(3)]
    s = sel.select_for_injection(three)
    _check("V-TSEL-FITS-ALL", _ids(s.injected) == ["e01", "e02", "e03"] and not s.overflow,
           "under the ceiling everything is injected in file order", s)

    fifteen = [_e(i) for i in range(1, 16)]
    s = sel.select_for_injection(fifteen)
    chars = sum(len(e["requirement"]) for e in s.injected)
    _check("V-TSEL-CEILING-COUNT", len(s.injected) <= sel.MAX_ENTRIES,
           "%d injected <= %d" % (len(s.injected), sel.MAX_ENTRIES), s.injected)
    _check("V-TSEL-CEILING-CHARS", chars <= sel.MAX_CHARS,
           "%d chars <= %d" % (chars, sel.MAX_CHARS), chars)
    both = _ids(s.injected) + _ids(s.deferred)
    _check("V-TSEL-NOTHING-LOST",
           sorted(both) == sorted(_ids(fifteen)) and len(set(both)) == len(both),
           "injected + deferred == the input, disjoint", both)
    _check("V-TSEL-OVERFLOW-NAMED",
           s.overflow and all(s.reasons.get(e["id"]) for e in s.deferred),
           "overflow flagged and every deferred entry carries a reason", s.reasons)

    mixed = [_e(1, "grep things"), _e(2, "file:README.md"), _e(3, ""),
             _e(4, "registry:lobby-npc-gate"), _e(5, "", status="auto")]
    s = sel.select_for_injection(mixed, max_entries=3)
    _check("V-TSEL-RUNNABLE-FIRST", _ids(s.injected) == ["e02", "e04", "e01"],
           "static check, then delegated, then prose/empty in file order", _ids(s.injected))
    s = sel.select_for_injection([_e(1, status="auto"), _e(2)], max_entries=1)
    _check("V-TSEL-REVIEWED-BEFORE-AUTO", _ids(s.injected) == ["e02"],
           "a reviewed entry outranks an auto-promoted one", _ids(s.injected))

    big = [_e(1, n=sel.MAX_CHARS + 5), _e(2)]
    s = sel.select_for_injection(big)
    _check("V-TSEL-OVERSIZE-DEFERRED",
           _ids(s.injected) == ["e02"] and _ids(s.deferred) == ["e01"]
           and "longer" in s.reasons["e01"],
           "an entry longer than the whole budget is deferred with that reason", s.reasons)

    s1 = sel.select_for_injection(fifteen)
    s2 = sel.select_for_injection(list(fifteen))
    _check("V-TSEL-DETERMINISTIC", _ids(s1.injected) == _ids(s2.injected),
           "same input -> same selection", (_ids(s1.injected), _ids(s2.injected)))
    shuffled = list(fifteen)
    random.Random(7).shuffle(shuffled)
    s3 = sel.select_for_injection(shuffled)
    _check("V-TSEL-ORDER-IS-INPUT-ORDER", _ids(s3.injected) == _ids(shuffled)[:len(s3.injected)],
           "ties keep the generation's own order, not an id sort", _ids(s3.injected))

    for fam in ("web_surface", "persistent_state", "kobiicraft_mode", "wii_homebrew"):
        real = bl.active_entries(fam)
        s = sel.select_for_injection(real)
        both = _ids(s.injected) + _ids(s.deferred)
        chars = sum(len(e["requirement"]) for e in s.injected)
        _check("V-TSEL-REAL-%s" % fam.upper(),
               len(real) >= 15 and len(s.injected) <= sel.MAX_ENTRIES
               and chars <= sel.MAX_CHARS and sorted(both) == sorted(_ids(real)),
               "%d real -> %d injected (%d chars), %d deferred"
               % (len(real), len(s.injected), chars, len(s.deferred)),
               "real=%d injected=%d chars=%d" % (len(real), len(s.injected), chars))

    print()
    print("TOWER_SELECT_PASS=%d/%d  threshold=%d/%d"
          % (_PASS, _PASS + _FAIL, _PASS + _FAIL, _PASS + _FAIL))
    return 0 if _FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
