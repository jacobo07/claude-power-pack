#!/usr/bin/env python3
"""V-EED-* -- entropy is a direction, and it has to be measurable.

cognitive_load.measure() reports a LEVEL. A level cannot say whether a
body of work made the estate cheaper or more expensive to understand, so
EED's contribution is the DELTA -- owners added, context cost moved, entry
points left undeclared.

Asserted against synthetic before/after snapshots rather than real refs: a
gate that spawns two git worktrees would cost ~200s and would measure the
repo's current history instead of the reporting logic.
"""
from __future__ import annotations

import sys
from pathlib import Path

PP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PP))
sys.path.insert(0, str(PP / "tools"))

from eed_delta import report  # noqa: E402

EXPECTED_GATES = 5
_passes = 0
_fails = 0


def _ok(g: str, e: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS {g}: {e}")


def _fail(g: str, d: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {g}: {d}")


def _unit(cost, entry=True):
    return {"context_cost": cost, "declares_entry_point": entry}


def main() -> int:
    print("V-EED -- entropy delta between two states")

    base = {"a": _unit(10), "b": _unit(5)}

    out = report(base, {"a": _unit(10), "b": _unit(5)}, "x", "y")
    if "no structural change" in out:
        _ok("V-EED-NO-CHANGE-IS-SAID-PLAINLY",
            "identical snapshots report no structural change")
    else:
        _fail("V-EED-NO-CHANGE-IS-SAID-PLAINLY", out[:120])

    grown = {"a": _unit(10), "b": _unit(5), "c": _unit(7)}
    out = report(base, grown, "x", "y")
    if "+1 added" in out and "new owners: c" in out:
        _ok("V-EED-NEW-OWNER-IS-NAMED", "an added owner is named, not counted")
    else:
        _fail("V-EED-NEW-OWNER-IS-NAMED", out[:160])

    # A new unit nobody can find the start of is entropy even when the code
    # inside it is good.
    out = report(base, {**base, "c": _unit(7, entry=False)}, "x", "y")
    if "NO DECLARED ENTRY POINT" in out:
        _ok("V-EED-UNDECLARED-ENTRY-SURFACED",
            "a new owner with no entry point is called out")
    else:
        _fail("V-EED-UNDECLARED-ENTRY-SURFACED", out[:160])

    out = report(base, {"a": _unit(30), "b": _unit(5)}, "x", "y")
    if "+20" in out and "a" in out:
        _ok("V-EED-MOVED-COST-ATTRIBUTED",
            "an existing unit's cost rise is attributed to that unit")
    else:
        _fail("V-EED-MOVED-COST-ATTRIBUTED", out[:160])

    # Shrinking must be representable, or the metric can only ever grow and
    # would quietly become a ratchet.
    out = report({"a": _unit(30), "b": _unit(5)}, base, "x", "y")
    if "-20" in out and "1 removed" not in out:
        _ok("V-EED-REDUCTION-IS-REPRESENTABLE",
            "a fall in context cost is reported as a fall")
    else:
        _fail("V-EED-REDUCTION-IS-REPRESENTABLE", out[:160])

    total = _passes + _fails
    print(f"EED_DELTA_PASS={_passes}/{total}  "
          f"threshold={EXPECTED_GATES}/{EXPECTED_GATES}")
    if total != EXPECTED_GATES:
        print(f"FAIL: {total} gates executed, {EXPECTED_GATES} declared")
        return 1
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
