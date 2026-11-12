#!/usr/bin/env python3
"""Gate for modules/tower/ratchet.promote_with_evidence (EVO E6, Owner "y" 2026-11-12): a baseline promotion needs a real
improvement, negative controls that really fail and reuse by a later run. Planted mutants of the predicate must turn it red.
Runs in a scratch baseline root; never touches a real family. Prints RATCHET_EVIDENCE_PASS=n/N."""
import importlib
import os
import sys
import tempfile

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, R)
from modules.tower import ratchet as rt  # noqa: E402
from modules.tower import baselines as bl  # noqa: E402

GOOD = {"improvement": {"run": "autopilot S33K", "measure": "lane outcome", "before": "PARKED", "after": "CERT 16"},
        "negative_controls": [{"name": "evo_same_family_allowed", "rc": 1}],
        "reuse": {"run": "autopilot S34K", "pointer": "evo_arm ledger row cites oracle_coverage_a2"}}
ENTRY = {"id": "EVO-TEST-1", "requirement": "r", "why": "w", "origin": "o", "class": "process"}


def cases(m):
    res = []

    def chk(name, cond):
        res.append((name, bool(cond)))
    chk("GOOD_ADMITTED", m.evidence_problems(GOOD) == [])
    chk("NO_EVIDENCE_REFUSED", m.evidence_problems(None) != [])
    chk("NO_CHANGE_REFUSED", m.evidence_problems(dict(GOOD, improvement=dict(GOOD["improvement"], after="PARKED"))) != [])
    chk("NO_RUN_REFUSED", m.evidence_problems(dict(GOOD, improvement=dict(GOOD["improvement"], run=""))) != [])
    chk("CONTROL_PASSED_REFUSED", m.evidence_problems(dict(GOOD, negative_controls=[{"name": "x", "rc": 0}])) != [])
    chk("CONTROL_RC_NOT_INT_REFUSED", m.evidence_problems(dict(GOOD, negative_controls=[{"name": "x", "rc": "1"}])) != [])
    chk("NO_CONTROLS_REFUSED", m.evidence_problems(dict(GOOD, negative_controls=[])) != [])
    chk("REUSE_SAME_RUN_REFUSED", m.evidence_problems(dict(GOOD, reuse={"run": "autopilot S33K", "pointer": "p"})) != [])
    chk("REUSE_MISSING_REFUSED", m.evidence_problems(dict(GOOD, reuse={})) != [])
    root = tempfile.mkdtemp(prefix="ratchet-ev-")
    try:
        m.promote_with_evidence("evo-test-family", [ENTRY], "reason", "authority", dict(GOOD, reuse={}), root=root)
        chk("WRITE_REFUSED_WITHOUT_REUSE", False)
    except m.RatchetRefusal:
        chk("WRITE_REFUSED_WITHOUT_REUSE", bl.latest("evo-test-family", root) is None)
    try:
        m.promote_with_evidence("evo-test-family", [ENTRY], "reason", "authority", GOOD, root=root)
        cur = bl.latest("evo-test-family", root)
        chk("WRITE_ADMITTED_RECORDS_EVIDENCE", cur and cur["entries"][-1].get("evidence") == GOOD)
    except m.RatchetRefusal:  # a mutant that let the reuse-less write through makes this one a duplicate: red
        chk("WRITE_ADMITTED_RECORDS_EVIDENCE", False)
    return res


real = cases(rt)
fails = [n for n, ok in real if not ok]
for n, ok in real:
    print(("PASS " if ok else "FAIL ") + n)
MUTANTS = {"accept_all": lambda m: setattr(m, "evidence_problems", lambda ev: []),
           "no_reuse_check": lambda m: setattr(m, "evidence_problems",
                                                (lambda orig: lambda ev: [p for p in orig(ev) if not p.startswith("reuse")])(m.evidence_problems)),
           "controls_may_pass": lambda m: setattr(m, "evidence_problems",
                                                  (lambda orig: lambda ev: [p for p in orig(ev) if not p.startswith("negative")])(m.evidence_problems)),
           "refuse_all": lambda m: setattr(m, "evidence_problems", lambda ev: ["no"])}
survivors = []
for name, mut in MUTANTS.items():
    m = importlib.reload(rt)
    mut(m)
    if all(ok for _n, ok in cases(m)):
        survivors.append(name)
importlib.reload(rt)
print("MUTANTS SURVIVED:", survivors or "none", f"({len(MUTANTS) - len(survivors)}/{len(MUTANTS)} killed)")
n = len(real)
print(f"RATCHET_EVIDENCE_PASS={n - len(fails)}/{n}" if not fails and not survivors else f"RATCHET_EVIDENCE_FAIL {fails} {survivors}")
sys.exit(1 if fails or survivors else 0)
