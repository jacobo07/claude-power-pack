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
check("V-DONEGATE-36", len(s) == 36 and sorted(s) == ["CR-%02d" % i for i in range(1, 37)])
check("V-DONEGATE-CONTROL-PASS", s["CR-12"] == "PASS" and s["CR-21"] == "PASS" and s["CR-20"] == "PASS")
check("V-DONEGATE-UNKNOWN-NOT-PASS", s["CR-16"] == "UNKNOWN" and s["CR-17"] == "PASS" and dg.main(["--root", base]) == 1)
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
# GPF CR-33..36 (spec vault/specs/gpf-resident-admission.md): each row driven PASS and not-PASS.
check("V-DONEGATE-W0-PASS", s["CR-33"] == "PASS", "real W0 receipt (imported from 9ecdf2cfd)")
w = fresh(); d = json.load(open(w + "/floor-decomposition.json")); d["arms"]["no_rules"]["label"] = "ESTIMATE"
json.dump(d, open(w + "/floor-decomposition.json", "w"))
check("V-DONEGATE-MUT-W0-ESTIMATE", status(w)["CR-33"] == "FAIL")
w = fresh(); os.remove(w + "/floor-decomposition.json")
check("V-DONEGATE-MUT-W0-MISSING", status(w)["CR-33"] == "UNKNOWN")
def l2file(ctrl, trt, cor, n, budget=False, src=None):
    g = tempfile.mkdtemp()
    json.dump({"summary": {"control": ctrl, "treatment": trt}}, open(g + "/gpf-l2-laptop.json", "w"))
    json.dump({"summary": {"n": n}, "correct": cor}, open(g + "/gpf-l2-quality.json", "w"))
    if budget:
        open(g + "/resident_budget.json", "w").write("{}")
    return {k: v[0] for k, v in dg.conditions(base, REPO, g, src or g).items()}
C4, T4 = [78236, 78231, 78530, 78571], [71723, 72007, 72008, 72053]
g = l2file(C4, T4, {"C": 3, "T": 3}, [3, 3])
check("V-DONEGATE-GPF-L2-PASS", g["CR-34"] == g["CR-35"] == "PASS")
check("V-DONEGATE-MUT-L2-N3", l2file(C4[:3], T4[:3], {"C": 3, "T": 3}, [3, 3])["CR-34"] == "FAIL")
check("V-DONEGATE-MUT-L2-NO-DELTA", l2file(C4, C4, {"C": 3, "T": 3}, [3, 3])["CR-34"] == "FAIL")
check("V-DONEGATE-MUT-L2-WRONG", l2file(C4, T4, {"C": 3, "T": 2}, [3, 3])["CR-35"] == "FAIL")
# review findings 2/3: treatment spread >= 1 % fails (delta_ok checks control only); arm totals are per arm
check("V-DONEGATE-MUT-L2-TREATMENT-SPREAD", l2file(C4, [71000, 71000, 71000, 71720], {"C": 3, "T": 3}, [3, 3])["CR-34"] == "FAIL")
check("V-DONEGATE-MUT-L2-ARM-SKEW", l2file(C4, T4, {"C": 6, "T": 0}, [3, 3])["CR-35"] == "FAIL")
e = tempfile.mkdtemp(); ge = {k: v[0] for k, v in dg.conditions(base, REPO, e, e).items()}
check("V-DONEGATE-GPF-L2-MISSING", ge["CR-34"] == ge["CR-35"] == ge["CR-36"] == "UNKNOWN")
# CR-36 maps the floor gate's exit code: 0 PASS, 1 FAIL, anything else UNKNOWN (the gate itself is V-FLOOR-BUDGET-*)
real_run = dg.budget_run
for code, want in ((0, "PASS"), (1, "FAIL"), (2, "UNKNOWN"), (None, "UNKNOWN")):
    dg.budget_run = lambda repo, b, src, c=code: (c, "stub")
    got = l2file(C4, T4, {"C": 3, "T": 3}, [3, 3], budget=True)["CR-36"]
    check("V-DONEGATE-CR36-EXIT-%s" % code, got == want, "exit %s -> %s" % (code, got))
dg.budget_run = real_run
check("V-DONEGATE-CR36-NO-SRC", l2file(C4, T4, {"C": 3, "T": 3}, [3, 3], budget=True, src=e + "/absent")["CR-36"] == "UNKNOWN")
# Phase 5 CR-09/10/13 (spec vault/specs/ccr-safe-to-forget-main.md): read from phase5-safe-to-forget.json, each row both poles.
def p5run(arm, correct=True, proc=None, applied=None, forget=True, hoisted=1, durable=True):
    on = arm == "N"
    applied = on if applied is None else applied
    x = {"tool": "PowerShell", "agent": None, "bytes": 40000, "out": 7900 if applied else 7700, "applied": applied,
         "durable": (durable if on else None), "mainProject": True if on else None,
         "forget": ({"verdict": "FORGET", "reason": "safe-hoisted" if hoisted else "safe", "hoisted": hoisted, "named": []} if forget else None)}
    return {"arm": arm, "finished": True, "correct": correct, "processed": proc or (60000 if on else 90000),
            "receipts": {"start": {"compatible": True}, "project": [x], "faults": 0}}
def p5(runs, drop=False):
    q = fresh()
    path = q + "/phase5-safe-to-forget.json"
    if drop:
        if os.path.exists(path): os.remove(path)
    else:
        json.dump({"runs": runs}, open(path, "w"))
    st = status(q)
    return st["CR-09"], st["CR-10"], st["CR-13"]
GOOD5 = [p5run("F"), p5run("N")] * 3
check("V-DONEGATE-P5-PASS", p5(GOOD5) == ("PASS", "PASS", "PASS"))
check("V-DONEGATE-P5-MISSING", p5(None, drop=True) == ("UNKNOWN", "UNKNOWN", "UNKNOWN"))
check("V-DONEGATE-P5-N2", p5(GOOD5[:4]) == ("UNKNOWN", "UNKNOWN", "UNKNOWN"))
check("V-DONEGATE-MUT-P5-NOT-JUDGED", p5(GOOD5[:5] + [p5run("N", forget=False)])[0] == "FAIL")
check("V-DONEGATE-MUT-P5-WRONG-ANSWER", p5(GOOD5[:5] + [p5run("N", correct=False)])[1] == "FAIL")
check("V-DONEGATE-MUT-P5-UNDURABLE", p5(GOOD5[:5] + [p5run("N", durable=False)])[1] == "FAIL")
check("V-DONEGATE-MUT-P5-UNEXERCISED", p5([p5run("F"), p5run("N", hoisted=0)] * 3)[1] == "FAIL")
check("V-DONEGATE-MUT-P5-NOT-APPLIED", p5(GOOD5[:5] + [p5run("N", applied=False)])[2] == "FAIL")
check("V-DONEGATE-MUT-P5-NO-SAVING", p5([p5run("F", proc=60000), p5run("N", proc=60000)] * 3)[2] == "FAIL")
# 2026-11-03 null smoke: host 2.1.317 outside COMPAT (all shadow) / result host-persisted (no project receipt) -> not counted
inc = [{**r, "receipts": {**r["receipts"], "start": {"compatible": False}}} for r in GOOD5]
check("V-DONEGATE-P5-INCOMPATIBLE-NOT-COUNTED", p5(inc) == ("UNKNOWN", "UNKNOWN", "UNKNOWN"))
check("V-DONEGATE-P5-INVALID-NOT-COUNTED", p5([{**r, "invalid": "no-project-receipt"} for r in GOOD5]) == ("UNKNOWN", "UNKNOWN", "UNKNOWN"))
print("DONEGATE_PASS=%d/%d  threshold=N/N" % (passes, passes + fails))
sys.exit(0 if fails == 0 else 1)
