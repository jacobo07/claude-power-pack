#!/usr/bin/env python3
"""V-DONEGATE-*: the ctx-rent-x done-gate must be able to return the other answer (mutation drill)."""
import copy, importlib.util, json, os, shutil, sys, tempfile

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(REPO, "vault", "programs", "ctx-rent-x")
spec = importlib.util.spec_from_file_location("done_gate", os.path.join(SRC, "done_gate.py"))
dg = importlib.util.module_from_spec(spec); spec.loader.exec_module(dg)
passes = fails = 0


def check(name, cond, ev=""):
    global passes, fails
    if cond: passes += 1; print("OK   %s %s" % (name, ev))
    else: fails += 1; print("FAIL %s %s" % (name, ev))


def fresh():
    d = tempfile.mkdtemp()
    for f in os.listdir(SRC):
        if f.endswith(".json") or f.endswith(".txt"):
            shutil.copy(os.path.join(SRC, f), d)
    return d


def status(root):
    return {k: v[0] for k, v in dg.conditions(root, REPO).items()}


base = fresh()
s = status(base)
check("V-DONEGATE-32", len(s) == 32 and sorted(s) == ["CR-%02d" % i for i in range(1, 33)])
check("V-DONEGATE-CONTROL-PASS", s["CR-12"] == "PASS" and s["CR-21"] == "PASS" and s["CR-20"] == "PASS")
check("V-DONEGATE-UNKNOWN-NOT-PASS", s["CR-17"] == "UNKNOWN" and dg.main(["--root", base]) == 1)
# mutation 1: treatment worse than control -> FAIL, not PASS
m = fresh(); d = json.load(open(m + "/floor-diet-results.json"))
d["rows"]["rules_to_skills"]["treatment"] = d["rows"]["rules_to_skills"]["control"]
json.dump(d, open(m + "/floor-diet-results.json", "w"))
check("V-DONEGATE-MUT-NO-DELTA", status(m)["CR-12"] == "FAIL")
# mutation 2: noisy control -> FAIL
d = json.load(open(m + "/floor-diet-results.json")); d["rows"]["rules_to_skills"]["treatment"] = [1, 1, 1, 1]; d["rows"]["rules_to_skills"]["control"] = [100, 200, 100, 200]
json.dump(d, open(m + "/floor-diet-results.json", "w"))
check("V-DONEGATE-MUT-NOISY-CONTROL", status(m)["CR-12"] == "FAIL")
# mutation 3: delete receipts -> UNKNOWN
e = fresh(); os.remove(e + "/main-canary-A.json"); os.remove(e + "/waiting-gex44-w0.json")
se = status(e)
check("V-DONEGATE-MUT-MISSING", se["CR-21"] == "UNKNOWN" and se["CR-20"] == "UNKNOWN")
# quality file present flips CR-17 (positive control for the UNKNOWN reason)
q = fresh(); json.dump({"n": 3}, open(q + "/main-canary-quality.json", "w"))
check("V-DONEGATE-STUB-QUALITY-REFUSED", status(q)["CR-17"] == "UNKNOWN")
json.dump({"pairs": 3, "delta_processed": 5, "correct_all": True, "page_faults": 0, "repairs": 0, "rereads": 1}, open(q + "/main-canary-quality.json", "w"))
sq = status(q)
check("V-DONEGATE-QUALITY-FLIPS", sq["CR-17"] == sq["CR-18"] == sq["CR-19"] == "PASS")
print("DONEGATE_PASS=%d/%d  threshold=N/N" % (passes, passes + fails))
sys.exit(0 if fails == 0 else 1)
