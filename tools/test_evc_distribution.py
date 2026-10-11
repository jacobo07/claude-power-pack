"""Gate for gsdx_reforecast distribution + repo-relative path. Zero model calls."""
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "gsdx_reforecast.py")
sys.path.insert(0, HERE)
fails = []

def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)

try:
    from gsdx_reforecast import distribution
except Exception as e:  # ImportError counts as RED
    print("IMPORT-RED", type(e).__name__, e)
    distribution = None

ORDER = ["lower", "p50", "p80", "p95", "ceiling"]

def ordered(d):
    v = [d[k] for k in ORDER]
    return all(a <= b for a, b in zip(v, v[1:]))

if distribution:
    d = distribution([x * 1e5 for x in range(1, 11)], 0)
    check("V-EVC-DIST-ORDER keys+order", all(k in d for k in ORDER) and ordered(d))
    check("V-EVC-DIST-ORDER control p50/p95", abs(d["p50"] - 5.5e5) <= 1 and d["p95"] >= 9.5e5)
    e = distribution([], 0)
    check("V-EVC-DIST-WIDE n==0 UNKNOWN", e["confidence"] == "UNKNOWN" and all(e[k] is None for k in ORDER))
    w = distribution([3e5], 0)
    check("V-EVC-DIST-WIDE n==1 WIDE ceiling>=2xp95", w["confidence"] == "WIDE" and w["ceiling"] >= 2 * w["p95"])
    w3 = distribution([1e5, 2e5, 3e5], 0)
    check("V-EVC-DIST-WIDE n==3", w3["confidence"] == "WIDE" and w3["ceiling"] >= 2 * w3["p95"] and ordered(w3))
    s12 = [float(i) * 1e5 for i in range(1, 13)]
    n12 = distribution(s12, 0)
    check("V-EVC-DIST-WIDE control n==12", n12["confidence"] == "NORMAL" and n12["ceiling"] == max(s12))
    o = distribution([4e5], 0)
    check("V-EVC-DIST-ONEPOINT p95>p50", o["p95"] > o["p50"] and ordered(o))
else:
    for n in ("ORDER", "WIDE", "ONEPOINT"):
        check("V-EVC-DIST-" + n, False)

def scan(text):
    return "C:\\Users\\User" in text

check("V-EVC-DIST-LIVEPATH scanner bites", scan('SPEND = r"C:\\Users\\User\\x.py"'))
src = open(TOOL, encoding="utf-8").read()
check("V-EVC-DIST-LIVEPATH no user path", not scan(src))
check("V-EVC-DIST-LIVEPATH derived from __file__", "os.path.abspath(__file__)" in src and '"mission_spend.py"' in src)

def run():
    d = tempfile.mkdtemp()
    def w(n, o):
        p = os.path.join(d, n)
        json.dump(o, open(p, "w"))
        return p
    w("route-A.json", {"envelope": {"target": 1000000}})
    w("route-B.json", {"envelope": {"target": 2000000}})
    w("rec-A.json", {"status": "DONE"})
    units = [{"id": i, "route": os.path.join(d, f"route-{i}.json"), "receipt": os.path.join(d, f"rec-{i}.json"),
              "accept": ["DONE"]} for i in "AB"]
    chain = w("chain.json", {"envelope": 40000000, "hard": 55000000, "units": units})
    goal = w("goal.json", {"used": 7_000_000})
    out = os.path.join(d, "forecast.json")
    r = subprocess.run([sys.executable, "-I", TOOL, "--chain", chain, "--goal-json", goal, "--out", out],
                       capture_output=True, text=True, timeout=60)
    return r, (json.load(open(out)) if os.path.exists(out) else None)

r, f = run()
check("V-EVC-DIST-CLI rc 0", r.returncode == 0)
check("V-EVC-DIST-CLI distribution emitted", bool(f) and "distribution" in f and "total_distribution" in f)
check("V-EVC-DIST-CLI old keys", bool(f) and all(k in f for k in ("remaining", "total", "iterate", "owner_needed")))
check("V-EVC-DIST-CLI stdout has distribution", '"distribution"' in r.stdout)
print("FAILED: %d" % len(fails) if fails else "ALL PASS")
sys.exit(1 if fails else 0)
