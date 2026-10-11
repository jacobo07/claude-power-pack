"""Gate for mission_spend.judge_predictive (predictive DRAINING edge). Zero model calls."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
fails = []

def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)

import importlib.util
MOD = os.environ.get("MS_UNDER_TEST", os.path.join(HERE, "mission_spend.py"))
spec = importlib.util.spec_from_file_location("ms_under_test", MOD)
ms = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ms)
jp = getattr(ms, "judge_predictive", None)
check("V-EVC-DRAIN-EXISTS", jp is not None)
if jp is None:
    print("FAILED: " + ", ".join(fails))
    sys.exit(1)

rec = {"token_estimate": 1_000_000}
auth = 1_000_000 * ms.DEFAULT_TRIP_RATIO

r = jp(rec, 1_200_000, 900_000)
check("V-EVC-DRAIN-EDGE red input drains", bool(r.get("drain")))
check("V-EVC-DRAIN-EDGE control no drain", jp(rec, 100_000, 200_000)["drain"] is None)
txt = r.get("drain") or ""
check("V-EVC-DRAIN-EDGE reason text", all(s in txt for s in ("1,200,000", "900,000", f"{int(auth):,}", "hard breaker", "not started")))

check("V-EVC-DRAIN-BEFORE-BREAKER silent breaker", ms.judge(rec, 1_200_000, None)["trip"] is None)
check("V-EVC-DRAIN-BEFORE-BREAKER control trips", ms.judge(rec, int(auth) + 1, None)["trip"] is not None)

check("V-EVC-DRAIN-FAILOPEN spent None", jp(rec, None, 900_000)["drain"] is None)
check("V-EVC-DRAIN-FAILOPEN no estimate", jp({}, 1_200_000, 900_000)["drain"] is None)
check("V-EVC-DRAIN-FAILOPEN p95 None", jp(rec, 1_200_000, None)["drain"] is None)

a = int(auth)
check("V-EVC-DRAIN-TAIL authority-1 passes", jp(rec, a - 1 - 900_000, 900_000)["drain"] is None)
check("V-EVC-DRAIN-TAIL tail=2 drains", bool(jp(rec, a - 1 - 900_000, 900_000, tail=2)["drain"]))
check("V-EVC-DRAIN-TAIL equality passes", jp(rec, a - 900_000, 900_000)["drain"] is None)
check("V-EVC-DRAIN-RATIO custom", bool(jp({"token_estimate": 1_000_000, "token_trip_ratio": 1.0}, 1_200_000, 900_000)["drain"]))

if fails:
    print("FAILED: " + ", ".join(fails))
    sys.exit(1)
print("ALL PASS")
