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
check("V-DONEGATE-UNKNOWN-NOT-PASS", s["CR-09"] == "UNKNOWN" and s["CR-17"] == "PASS" and dg.main(["--root", base]) == 1)
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
# quality file: raw per-run schema (L6). Stub refused; real shape flips; mutations bite.
def run(arm, proc, **kw):
    r = {"arm": arm, "finished": True, "receipt_matches_arm": True, "processed": proc, "correct": True, "page_faults": 0, "repairs": 0, "rereads": 0}
    r.update(kw); return r
def qfile(runs):
    q = fresh(); json.dump({"runs": runs}, open(q + "/main-canary-quality.json", "w")); return status(q)
good = [run("S", 500), run("E", 400)] * 3
check("V-DONEGATE-STUB-QUALITY-REFUSED", qfile([])["CR-17"] == "UNKNOWN")
sq = qfile(good)
check("V-DONEGATE-QUALITY-FLIPS", sq["CR-17"] == sq["CR-18"] == sq["CR-19"] == "PASS")
check("V-DONEGATE-MUT-RECEIPT-MISMATCH", qfile(good[:5] + [run("E", 400, receipt_matches_arm=False)])["CR-17"] == "UNKNOWN")
check("V-DONEGATE-MUT-WRONG-ANSWER", qfile(good[:5] + [run("E", 400, correct=False)])["CR-18"] == "FAIL")
check("V-DONEGATE-MUT-NO-SAVING", qfile([run("S", 400), run("E", 500)] * 3)["CR-17"] == "FAIL")
check("V-DONEGATE-MUT-PAGE-FAULT", qfile(good[:5] + [run("E", 400, page_faults=2)])["CR-19"] == "FAIL")
# replay: valid ESTIMATE flips CR-23; unlabelled or saving-less is refused
def rfile(doc):
    q = fresh(); json.dump(doc, open(q + "/replay-gex44-a7.json", "w")); return status(q)
cls = {c: {"sessions": 2, "X": 10, "X_prime": 8} for c in ("a", "b", "ksr_style")}
okdoc = {"label": "ESTIMATE (counterfactual)", "classes": cls, "total": {"X": 30, "X_prime": 24, "saving_pct": 20.0}}
sr = rfile(okdoc)
check("V-DONEGATE-REPLAY-FLIPS", sr["CR-23"] == "PASS" and sr["CR-22"] == "PASS")
check("V-DONEGATE-MUT-REPLAY-UNLABELLED", rfile({**okdoc, "label": "MEASURED"})["CR-23"] == "UNKNOWN")
check("V-DONEGATE-MUT-REPLAY-NO-SAVING", rfile({**okdoc, "total": {"X": 30, "X_prime": 30}})["CR-23"] == "UNKNOWN")
check("V-DONEGATE-MUT-REPLAY-NO-KSR", rfile({**okdoc, "classes": {"a": cls["a"], "b": cls["b"], "d": cls["a"]}})["CR-22"] == "UNKNOWN")
# GPF receipts (CR-11/14/15/29): each pole reachable from synthetic per-run files.
def gfile(succ, k29):
    g = tempfile.mkdtemp()
    json.dump({"runs": succ}, open(g + "/gpf-l1-successor.json", "w"))
    json.dump({"runs": k29}, open(g + "/gpf-cr29.json", "w"))
    return {k: v[0] for k, v in dg.conditions(base, REPO, g).items()}
good = {"label": "S", "successor": "x", "successor_first_prompt": "/kresume", "turn_completed": True, "frontier_basis": "capsule"}
kok = {"label": "K", "token": "T1", "done_txt": "T1", "first_correct_action": True, "seconds_to_first_correct_action": 40}
g = gfile([good], [kok])
check("V-DONEGATE-GPF-PASS", g["CR-11"] == g["CR-14"] == g["CR-15"] == g["CR-29"] == "PASS")
g = gfile([good, {**good, "frontier_basis": None}], [{**kok, "done_txt": "WRONG"}])
check("V-DONEGATE-GPF-LATEST-FAIL", g["CR-11"] == g["CR-14"] == g["CR-29"] == "FAIL")
g = gfile([], [{"label": "K1", "aborted": "trust dialog"}])
check("V-DONEGATE-GPF-ABORT-UNKNOWN", g["CR-11"] == g["CR-14"] == g["CR-15"] == g["CR-29"] == "UNKNOWN")
print("DONEGATE_PASS=%d/%d  threshold=N/N" % (passes, passes + fails))
sys.exit(0 if fails == 0 else 1)
