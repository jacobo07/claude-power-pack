#!/usr/bin/env python
"""V-RADM-* gates for tools/route_admission.py.

Every rejection has an admitted control, so an admission function that always (or never) says
ADMISSIBLE cannot go green. The two plan controls run against the REAL floor table:
  negative: W0r as the heavy topology (orchestrator + 3 gsd-executors) ~10.9M vs a 3.5M target;
  positive: the thin route, one top-level worker x 25 calls, ~3.45M with margin vs 3.5M.

Mutation drill: ROUTE_ADMISSION_DRILL_DIR holding a mutated route_admission.py is imported first.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
if os.environ.get("ROUTE_ADMISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["ROUTE_ADMISSION_DRILL_DIR"])
sys.path.insert(1 if os.environ.get("ROUTE_ADMISSION_DRILL_DIR") else 0, str(HERE))
import route_admission as ra  # noqa: E402

passes = fails = 0
M = 1_000_000
W0R_ENV = {"target": 3_500_000, "warn": 4_500_000, "stop": 5_500_000, "calls": 25}


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def raises(fn):
    try:
        fn()
    except ValueError:
        return True
    return False


def main() -> int:
    floors = ra.load_floors(HERE.parent / "vault" / "config" / "route-floors.json")   # repo table, drill or not
    profiles = floors["profiles"]
    check("V-RADM-TABLE-SANE", all(p["floor"] <= p["p50"] for p in profiles.values())
          and profiles["Explore"]["floor"] < profiles["gsd-executor"]["floor"] < profiles[ra.TOP_LEVEL]["floor"],
          "floor <= p50 everywhere; Explore < executor < top-level")
    # The table is derived from the measured snapshot (tools/subagent_floor.py); a hand edit that drifts
    # from the measurement goes red. top-level-worker is not a subagent and is not in the snapshot.
    snap = json.loads((HERE.parent / "vault" / "config" / "subagent-floor.json").read_text(encoding="utf-8"))
    measured = snap["by_agent_type"]
    drift = {k: (v["floor"], (measured.get(k) or {}).get("min")) for k, v in profiles.items()
             if k != ra.TOP_LEVEL and (v["floor"], v["p50"], v["n"]) != ((measured.get(k) or {}).get("min"),
                                                                          (measured.get(k) or {}).get("p50"),
                                                                          (measured.get(k) or {}).get("n"))}
    check("V-RADM-TABLE-MATCHES-SNAPSHOT", not drift and set(measured) <= set(profiles),
          f"drift {drift}; unlisted {sorted(set(measured) - set(profiles))}")

    heavy = {"envelope": W0R_ENV, "workers": [
        {"name": "orchestrator", "profile": ra.TOP_LEVEL, "calls": 40, "packet": 5_000},
        {"name": "exec-1", "profile": "gsd-executor", "calls": 20, "packet": 20_000},
        {"name": "exec-2", "profile": "gsd-executor", "calls": 20, "packet": 20_000},
        {"name": "exec-3", "profile": "gsd-executor", "calls": 20, "packet": 20_000}]}
    h = ra.admit(heavy, floors)
    check("V-RADM-HEAVY-REJECTED", h["verdict"] == ra.RECOMPILE and h["need"] > 10 * M,
          f"{h['verdict']} need {h.get('need'):,}: {h['reasons']}")
    thin = {"envelope": W0R_ENV, "workers": [
        {"name": "w0r", "profile": ra.TOP_LEVEL, "calls": 25, "packet": 4_000}]}
    t = ra.admit(thin, floors)
    check("V-RADM-THIN-ADMITTED", t["verdict"] == ra.ADMISSIBLE and t["need_with_margin"] <= W0R_ENV["target"],
          f"{t['verdict']} {t['need_with_margin']:,} <= {W0R_ENV['target']:,}")
    check("V-RADM-RECOMPILE-HINT", h["max_calls_single_worker"] >= 25,
          f"the hint names a single-worker budget of {h['max_calls_single_worker']} calls, which admits the thin route")

    # exact boundary on a synthetic table: margin 0, floor 100, 10 calls = 1000
    tiny = {"default_min_calls": 3, "profiles": {ra.TOP_LEVEL: {"floor": 100, "p50": 100, "write": True}}}

    def r(target, calls=10, env_calls=None):
        return {"envelope": {"target": target, "warn": target, "stop": target, "calls": env_calls},
                "workers": [{"name": "w", "profile": ra.TOP_LEVEL, "calls": calls}]}
    check("V-RADM-AT-TARGET-ADMITTED", ra.admit(r(1000), tiny, margin=0)["verdict"] == ra.ADMISSIBLE)
    check("V-RADM-OVER-TARGET-REJECTED", ra.admit(r(999), tiny, margin=0)["verdict"] == ra.RECOMPILE)
    check("V-RADM-MARGIN-COUNTS", ra.admit(r(1000), tiny, margin=0.1)["verdict"] == ra.RECOMPILE
          and ra.admit(r(1100), tiny, margin=0.1)["verdict"] == ra.ADMISSIBLE, "1000 x 1.1 = 1100")
    check("V-RADM-CALLS-REJECTED", ra.admit(r(10**9, calls=26, env_calls=25), tiny)["verdict"] == ra.RECOMPILE)
    check("V-RADM-CALLS-CONTROL", ra.admit(r(10**9, calls=25, env_calls=25), tiny)["verdict"] == ra.ADMISSIBLE)

    d = ra.admit(thin, floors, remaining=1 * M)
    check("V-RADM-DEFER", d["verdict"] == ra.DEFER, f"{d['verdict']}: {d['reasons']}")
    check("V-RADM-DEFER-CONTROL", ra.admit(thin, floors, remaining=4 * M)["verdict"] == ra.ADMISSIBLE)

    unk = {"envelope": W0R_ENV, "workers": [{"name": "x", "profile": "never-measured", "calls": 1}]}
    check("V-RADM-UNMEASURED-ESCALATES", ra.admit(unk, floors)["verdict"] == ra.ESCALATE,
          "an unknown floor is not zero")
    small = {"envelope": {"target": 300_000, "warn": 300_000, "stop": 300_000},
             "workers": [{"name": "w", "profile": ra.TOP_LEVEL, "calls": 3}]}
    e = ra.admit(small, floors)
    check("V-RADM-INFEASIBLE-ENVELOPE-ESCALATES", e["verdict"] == ra.ESCALATE, f"{e['reasons']}")
    roomy = {**small, "envelope": {"target": 400_000, "warn": 400_000, "stop": 400_000}}
    check("V-RADM-INFEASIBLE-CONTROL", ra.admit(roomy, floors)["verdict"] == ra.ADMISSIBLE,
          "3 x 110,835 x 1.2 = 399,006 <= 400,000")

    bad = [
        {"envelope": W0R_ENV, "workers": []},
        {"envelope": W0R_ENV, "workers": [{"profile": ra.TOP_LEVEL, "calls": 0}]},
        {"envelope": W0R_ENV, "workers": [{"profile": ra.TOP_LEVEL, "calls": True}]},
        {"envelope": W0R_ENV, "workers": [{"profile": ra.TOP_LEVEL, "calls": 1, "packet": -1}]},
        {"envelope": {"target": 5, "warn": 4, "stop": 6}, "workers": [{"profile": ra.TOP_LEVEL, "calls": 1}]},
        {"workers": [{"profile": ra.TOP_LEVEL, "calls": 1}]},
    ]
    check("V-RADM-MALFORMED-RAISES", all(raises(lambda b=b: ra.admit(b, floors)) for b in bad),
          f"{len(bad)} malformed routes refused")
    check("V-RADM-DIGEST-STABLE", ra.route_digest(thin) == ra.route_digest(json.loads(json.dumps(thin)))
          and ra.route_digest(thin) != ra.route_digest(heavy))

    with tempfile.TemporaryDirectory() as tmp:
        codes = []
        for name, route in (("thin", thin), ("heavy", heavy)):
            p = Path(tmp) / f"{name}.json"
            p.write_text(json.dumps(route), encoding="utf-8")
            codes.append(subprocess.run([sys.executable, str(HERE / "route_admission.py"), "admit", "--route", str(p)],
                                        capture_output=True, text=True, timeout=60).returncode)
    check("V-RADM-CLI-EXIT", codes == [0, 3], f"thin/heavy exit codes {codes}")

    print(f"RADM_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
