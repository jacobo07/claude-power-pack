#!/usr/bin/env python
"""V-EST-* gates for the growth estimator and three-miss DEGRADED rule in tools/route_admission.py.
Hermetic: a temp floors file. Mutation drill: ROUTE_ADMISSION_DRILL_DIR holds a mutated copy."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
if os.environ.get("ROUTE_ADMISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["ROUTE_ADMISSION_DRILL_DIR"])
sys.path.insert(1 if os.environ.get("ROUTE_ADMISSION_DRILL_DIR") else 0, str(HERE))
import route_admission as ra  # noqa: E402

passes = fails = 0
ENV = {"target": 50_000_000, "warn": 60_000_000, "stop": 70_000_000}
G = 1725
# (calls, first-call cost, actual total) from estimator-fit.md
FIT = [(19, 18332, 909_247), (19, 18236, 742_614), (22, 18514, 680_606), (17, 18585, 442_155)]


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def floors(tmp, growth=True, misses=None):
    prof = {"floor": 13507, "write": True}
    if growth:
        prof["growth"] = G
    if misses is not None:
        prof["misses"] = misses
    p = Path(tmp) / "floors.json"
    p.write_text(json.dumps({"default_min_calls": 1, "profiles": {"slim-t2": prof}}), encoding="utf-8")
    return p


def need(p, calls, packet=0):
    route = {"envelope": ENV, "workers": [{"name": "w", "profile": "slim-t2", "calls": calls, "packet": packet}]}
    return ra.admit(route, ra.load_floors(p))


def main():
    with tempfile.TemporaryDirectory() as tmp:
        p = floors(tmp)
        pred = sum(need(p, c, f - 13507)["need"] for c, f, _ in FIT)
        act = sum(a for _, _, a in FIT)
        check("V-EST-GROWTH-QUADRATIC", abs(pred - act) <= 0.25 * act and need(p, 7)["estimator"] == "growth",
              f"pooled predicted {pred:,} vs actual {act:,}")
        n7 = need(p, 7, 6360)["need"]
        check("V-EST-GROWTH-1H4-ABOVE-FLOOR", n7 == 7 * (13507 + 6360) + G * 21, f"{n7:,} (1H4 actual 448,589: known gap)")
        q = floors(tmp, growth=False)
        r = need(q, 7, 6360)
        check("V-EST-NO-GROWTH-UNCHANGED", r["need"] == 7 * (13507 + 6360) and r["estimator"] == "floor", str(r["need"]))
        r = floors(tmp)
        base = need(r, 5)["need"]
        for i in range(2):
            ra.record_actual("slim-t2", 100, 200, r)
        check("V-EST-TWO-MISSES-NOT-DEGRADED", "DEGRADED" not in " ".join(need(r, 5)["reasons"]))
        ra.record_actual("slim-t2", 100, 300, r)
        res = need(r, 5)
        check("V-EST-THREE-MISS-DEGRADED", any("estimator DEGRADED for slim-t2" in x for x in res["reasons"]), str(res["reasons"]))
        check("V-EST-DEGRADED-PRICES-UP", res["need"] == base * 3 and res["need"] > base, f"{res['need']:,} vs {base:,}")
        ra.record_actual("slim-t2", 100, 110, r)
        res2 = need(r, 5)
        check("V-EST-HIT-CLEARS", ra.load_floors(r)["profiles"]["slim-t2"]["misses"] == [] and res2["need"] == base
              and not res2["reasons"], str(res2["reasons"]))
        # Part B: physical calls (every tool use runs ~2.4x the declared steps)
        ph = Path(tmp) / "phys.json"
        ph.write_text(json.dumps({"default_min_calls": 1, "profiles": {"slim-t2": {
            "floor": 13507, "write": True, "growth": G, "physical_ratio": 2.4, "physical_ratio_n": 4}}}), encoding="utf-8")
        rp = need(ph, 7, 18585 - 13507)
        check("V-EST-PHYSICAL-1H4", abs(rp["need"] - 442_155) <= 0.25 * 442_155 and rp["calls"] == 7
              and rp["calls_physical"] == 17, f"{rp['need']:,} vs 442,155; calls={rp['calls']} physical={rp['calls_physical']}")
        rc = need(floors(tmp), 7, 6360)
        check("V-EST-PHYSICAL-CONTROL", rc["need"] == 7 * (13507 + 6360) + G * 21 and rc["calls_physical"] == 7, str(rc["need"]))
    print(f"EST_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
