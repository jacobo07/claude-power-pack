#!/usr/bin/env python
"""V-CTX-* gates for route_admission.context_check (WU-E1 part 3, context admission at arm).
Hermetic: in-memory floors and measured tables. Each verdict is driven from both poles."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import route_admission as ra  # noqa: E402

passes = fails = 0
FLOORS = {"profiles": {"top-level-worker": {"floor": 110835}, "slim-t2": {"floor": 13507}}}


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def route(*profiles):
    return {"workers": [{"name": f"w{i}", "profile": p, "calls": 3} for i, p in enumerate(profiles)]}


def m(median, n=5):
    return {"median": median, "n": n, "source": "test"}


def main():
    ok = ra.context_check(route("top-level-worker"), FLOORS, {"top-level-worker": m(82_298, 41)})
    check("V-CTX-OK", ok["verdict"] == "OK" and ok["workers"][0]["status"] == "OK", str(ok["verdict"]))

    under = ra.context_check(route("slim-t2"), FLOORS, {"slim-t2": m(13507 * 1.25 + 1)})
    check("V-CTX-UNDERSTATED", under["verdict"] == "UNDERSTATED", str(under["workers"][0]["status"]))
    edge = ra.context_check(route("slim-t2"), FLOORS, {"slim-t2": m(int(13507 * 1.25))})
    check("V-CTX-BOUNDARY-IS-OK", edge["verdict"] == "OK", "median == 1.25 x floor is not a miss")

    few = ra.context_check(route("slim-t2"), FLOORS, {"slim-t2": m(99_999, ra.MIN_MEASURED_N - 1)})
    check("V-CTX-FEW-SAMPLES-UNMEASURED", few["verdict"] == "UNMEASURED",
          "a huge median on n<3 is not trusted either way")
    none = ra.context_check(route("slim-t2"), FLOORS, {})
    check("V-CTX-ABSENT-IS-NOT-OK", none["verdict"] == "UNMEASURED", str(none["verdict"]))
    nofloor = ra.context_check(route("ghost"), FLOORS, {"ghost": m(1000)})
    check("V-CTX-NO-FLOOR-UNMEASURED", nofloor["verdict"] == "UNMEASURED", str(nofloor["verdict"]))
    check("V-CTX-EMPTY-ROUTE-UNMEASURED", ra.context_check({"workers": []}, FLOORS, {})["verdict"] == "UNMEASURED")

    mixed = ra.context_check(route("top-level-worker", "slim-t2"), FLOORS, {"top-level-worker": m(82_298, 41)})
    check("V-CTX-MIXED-UNMEASURED", mixed["verdict"] == "UNMEASURED", "one OK + one unmeasured")
    worst = ra.context_check(route("top-level-worker", "slim-t2"), FLOORS,
                             {"top-level-worker": m(82_298, 41), "slim-t2": m(40_000)})
    check("V-CTX-UNDERSTATED-WINS", worst["verdict"] == "UNDERSTATED", str(worst["verdict"]))

    check("V-CTX-MISSING-FILE-EMPTY", ra.load_measured(Path("no-such-measured-file.json")) == {})
    print(f"CTX_PASS={passes}/{passes + fails}  threshold=all")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
