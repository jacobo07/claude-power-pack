"""Gate for gsdx_reforecast: both poles of the 25% rule and the 40M rule. Zero model calls."""
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "gsdx_reforecast.py")
fails = []

def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)

def run(used, prev_expected, extra_target=0, plan_scale=1.0):
    d = tempfile.mkdtemp()
    def w(n, o):
        p = os.path.join(d, n)
        json.dump(o, open(p, "w"))
        return p
    w("route-A.json", {"envelope": {"target": 1000000}})
    w("route-B.json", {"envelope": {"target": 2000000 + extra_target}})
    w("route-C.json", {"envelope": {"target": 5000000}})
    w("rec-A.json", {"status": "DONE"})
    w("rec-C.json", {"status": "DONE"})
    units = [{"id": i, "route": os.path.join(d, f"route-{i}.json"), "receipt": os.path.join(d, f"rec-{i}.json"),
              "accept": ["DONE"]} for i in "ABC"]
    chain = w("chain.json", {"envelope": 40000000, "hard": 55000000, "units": units})
    goal = w("goal.json", {"used": used})
    prev = w("prev.json", {"total": {"expected": prev_expected}})
    out = os.path.join(d, "forecast.json")
    cmd = [sys.executable, "-I", TOOL, "--chain", chain, "--goal-json", goal, "--previous", prev, "--out", out]
    if plan_scale != 1.0:
        cmd += ["--plan-scale", str(plan_scale)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return r, (json.load(open(out)) if os.path.exists(out) else None)

# B only is pending: 2.0M * 0.35 = 0.7M chain; plan lines expected 12.0 -> remaining 12.7; used 7.0 -> 19.7
r, f = run(7_000_000, 19_700_000)
check("runs rc 0", r.returncode == 0)
check("only pending unit counted", f and f["chain"]["pending"] == ["B"])
check("chain expected = 0.35 x target", f and abs(f["remaining"]["expected"] - 12_700_000) < 1)
check("total = used + remaining", f and abs(f["total"]["expected"] - 19_700_000) < 1)
check("ordering lower<expected<safety", f and f["total"]["lower"] < f["total"]["expected"] < f["total"]["safety"])
t = f["total"] if f else {}
check("P50<=P80<=P95 and P80 labelled chosen", f and t["P50"] == t["expected"] and t["P50"] <= t["P80"] <= t["P95"]
      and t["P95"] == t["safety"] and "CHOSEN" in t["P80_basis"])
check("change <= 25% -> iterate false", f and f["iterate"] is False)
check("under 40M -> owner_needed false", f and f["owner_needed"] is False)
# change > 25%
r, f = run(7_000_000, 10_000_000)
check("change > 25% -> iterate true", f and f["iterate"] is True and f["delta_pct"] > 25)
# exactly boundary-ish below
r, f = run(7_000_000, 19_700_000 / 1.25)
check("change == 25% -> iterate false", f and f["iterate"] is False)
# 40M pole
r, f = run(7_000_000, 19_700_000, plan_scale=3.0)
check("total > 40M -> owner_needed true", f and f["owner_needed"] is True)
print("FAILED: %d" % len(fails) if fails else "ALL PASS")
sys.exit(1 if fails else 0)
