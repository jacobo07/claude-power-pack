#!/usr/bin/env python3
"""V-S9-* gates: the master done-gate (flow-compression Phase 8, plan 08-03). Prints S9_PASS=n/n.

Re-judges stored evidence; it never re-runs a suite. Every negative control below was run against the REAL judge
(s9_done_gate.judge_suite / seal_check) and its output read before the assertion that depends on it was written.
"""
from __future__ import annotations

import copy
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

os.environ["CPP_RESOURCE_ADMISSION"] = "off"
TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))
import s9_done_gate as dg  # noqa: E402

T0 = time.time()
PHASE = ROOT / ".planning/workstreams/flow-compression/phases/08-s9-knowledge-vault-ukdl-cbr-red-team-master-done-gate"
RESULTS: list[tuple[str, bool, str]] = []


def check(gate: str, cond, ev: str = "") -> None:
    RESULTS.append((gate, bool(cond), ev))
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def load_evidence() -> dict:
    committed = PHASE / "08-DONE-GATE.json"
    if committed.is_file():
        return json.loads(committed.read_text())["evidence"]
    for cand in (os.environ.get("S9_EVIDENCE"), "/tmp/s9-gate/evidence.json"):
        if cand and Path(cand).is_file():
            return json.loads(Path(cand).read_text())
    print("S9_INCONCLUSIVE no stored evidence; collect first: python3 tools/s9_done_gate.py collect --only test_rotation_invariant --out /tmp/s9-gate")
    sys.exit(2)


EVIDENCE = load_evidence()
CUR = dg.subject_tree()


def base_rec(name: str = "test_rotation_invariant") -> dict:
    """A real stored record re-bound to the tree judged now, so each crafted variant differs from it by exactly one fact."""
    rec = copy.deepcopy(EVIDENCE["suites"][name])
    rec["head"], rec["trees"], rec["bracket_moved"] = CUR["head"], CUR["trees"], False
    return rec


def run_judge(rec: dict) -> dict:
    return dg.judge_suite(rec, CUR)


# ------------------------------------------------------------------------------------------ suite rules
b = run_judge(base_rec())
check("V-S9-BASELINE-GREEN", b["status"] == "PASS", f"{b}")

r = base_rec()
r["fails"] = r["fails"] + ["V-ROT-INVENTED"]
r["exit"] = 1
v = run_judge(r)
check("V-S9-KNOWN-REDS-ONLY", v["status"] == "FAIL" and "outside the known set" in " ".join(v["reasons"]), f"{v}")

r = base_rec()
r["fails"] = ["V-AMCR-ONE-RESOLVER-INVENTORY"]
r["exit"] = 1
v = run_judge(r)
own = base_rec("test_mission_continuity") if "test_mission_continuity" in EVIDENCE["suites"] else None
check("V-S9-KNOWN-RED-OWN-SUITE", v["status"] == "FAIL", f"{v}")
if own is not None:
    own["fails"], own["exit"] = ["V-AMCR-ONE-RESOLVER-INVENTORY"], 1
    vo = run_judge(own)
    check("V-S9-KNOWN-RED-ALLOWED-IN-OWN-SUITE", vo["status"] == "PASS" and vo["known_reds_seen"] == ["V-AMCR-ONE-RESOLVER-INVENTORY"], f"{vo}")

r = base_rec()
r["tag_line"] = dict(r["tag_line"], total=r["tag_line"]["total"] - 1, passed=r["tag_line"]["passed"] - 1)
v = run_judge(r)
check("V-S9-FLOOR", v["status"] == "FAIL" and "fell below" in " ".join(v["reasons"]), f"{v}")

r = base_rec()
r["tag_line"] = None
v = run_judge(r)
check("V-S9-TAG-OR-RED", v["status"] == "FAIL" and "tag line missing" in " ".join(v["reasons"]), f"{v}")

r = base_rec()
r["trees"] = dict(r["trees"], tools="0" * 64)
v = run_judge(r)
check("V-S9-BOUND", v["status"] == "INCONCLUSIVE", f"{v}")

r = base_rec()
r["bracket_moved"] = True
v = run_judge(r)
check("V-S9-BRACKET", v["status"] == "INCONCLUSIVE", f"{v}")

r = base_rec()
r["exit"] = 3
v = run_judge(r)
check("V-S9-EXIT-UNEXPLAINED", v["status"] == "FAIL", f"{v}")

# ------------------------------------------------------------------------------------------ seal-check instrument
SEAL_FM = ("---\nphase: 08-s9-knowledge-vault-ukdl-cbr-red-team-master-done-gate\nverified: 2026-10-25T20:00:00Z\n"
           "status: {status}\nscore: \"control\"\n---\n\n# control verification\n")
seal_out = {}
# Every phase of the workstream, not a literal 8: phase 9 (red-team gap closure) made the literal stale.
TOTAL = sum(1 for d in PHASE.parent.iterdir() if d.is_dir() and d.name[:2].isdigit())
with tempfile.TemporaryDirectory(prefix="s9-seal-") as td:
    for status in ("passed", "gaps_found"):
        root = Path(td) / status
        shutil.copytree(ROOT / ".planning", root / ".planning", ignore=shutil.ignore_patterns("*.out"))
        (root / ".planning/workstreams/flow-compression/phases" / PHASE.name / "08-VERIFICATION.md").write_text(
            SEAL_FM.format(status=status), encoding="utf-8")
        seal_out[status] = (root, dg.seal_check(root, TOTAL), dg.seal_progress(root))
root8, (code8, msg8), prog8 = seal_out["passed"]
root7, (code7, msg7), prog7 = seal_out["gaps_found"]
check("V-S9-SEAL-CONTROL-8", prog8["completed_count"] == TOTAL and code8 == 0, f"{msg8}")
check("V-S9-SEAL-CONTROL-7", prog7["completed_count"] == TOTAL - 1 and code7 != 0, f"{msg7}")
check("V-S9-SEAL-ROOT-IS-TEMP", prog8["project_root"] == str(root8) and prog7["project_root"] == str(root7)
      and str(ROOT) not in (prog8["project_root"], prog7["project_root"]), f"{prog8['project_root']} | {prog7['project_root']}")
real_code, real_msg = dg.seal_check(ROOT, TOTAL)
check("V-S9-SEAL-REAL-PENDING", real_code in (0, 2), f"{real_msg}")
w_code, w_msg = dg.seal_check(Path(tempfile.gettempdir()), TOTAL)
check("V-S9-SEAL-WRONG-ROOT-REFUSED", w_code != 0 and "SEAL_OK" not in w_msg, f"{w_msg}")


# ------------------------------------------------------------------------------------------ mission judge (08-03 Task 2)
DOC = json.loads((PHASE / "08-DONE-GATE.json").read_text()) if (PHASE / "08-DONE-GATE.json").is_file() else None
if DOC is None:
    print("S9_INCONCLUSIVE no committed 08-DONE-GATE.json; run judge --write-gate first")
    sys.exit(2)
CTX, JT = DOC["context"], DOC["judged_tree"]


def judged(ctx=None, ev=None) -> dict:
    return dg.judge_all(ev if ev is not None else DOC["evidence"], ctx if ctx is not None else CTX, JT)


def mut(fn) -> dict:
    c = copy.deepcopy(CTX)
    fn(c)
    return judged(c)


def flips(gate: str, fn) -> bool:
    return (not mut(fn)["gates"][gate]["ok"]) and base["gates"][gate]["ok"]


base = judged()
check("V-S9-REJUDGE-REPRODUCES", base == DOC["judgement"], f"verdict {base['verdict']}")
check("V-S9-MJ-VERDICT-CLOSED", base["verdict"] in dg.VERDICTS and base["gates"]["V-S9-VERDICT"]["ok"], base["verdict"])
check("V-S9-MJ-STRUCTURAL-GATES-GREEN",
      all(r["ok"] for g, r in base["gates"].items() if g not in ("V-S9-SUITES", "V-S9-ACCEPTANCE")),
      str({g: r["ok"] for g, r in base["gates"].items()}))

check("V-S9-INCIDENTS-CONTROL", flips("V-S9-INCIDENTS", lambda c: c["incidents"]["findings"].append("bad citation")))
check("V-S9-UKDL-CONTROL", flips("V-S9-UKDL", lambda c: c["ukdl_findings"].append("missing")))
check("V-S9-SPEC-PREDICATE-CONTROL", flips("V-S9-SPEC-PREDICATE", lambda c: c["spec_findings"].append("drift")))
check("V-S9-REDTEAM-CONTROL-BLOB", flips("V-S9-REDTEAM", lambda c: c["redteam"].__setitem__("blob_equals_file", False)))
check("V-S9-REDTEAM-CONTROL-CLAIM15", flips("V-S9-REDTEAM", lambda c: c["redteam"]["claims"]["15"].__setitem__("verdict", "HELD")))
check("V-S9-REDTEAM-CONTROL-HELD-CONTROL", flips("V-S9-REDTEAM", lambda c: c["redteam"]["claims"]["4"].__setitem__("held_controls_fired", False)))
check("V-S9-BREACH-INCIDENT-IFF-CONTROL", flips("V-S9-BREACH-INCIDENT-IFF", lambda c: c["breach_incident"]["sections"].pop()))
check("V-S9-PREDICATE-AGREE-CONTROL", flips("V-S9-PREDICATE-AGREE", lambda c: c["redteam"].__setitem__("predicate_value", not c["spec_predicate"])))
check("V-S9-CORE-UNCHANGED-CONTROL", flips("V-S9-CORE-UNCHANGED", lambda c: c["core_diff"].append("gsd-core/bin/gsd-tools.cjs")))
check("V-S9-FRONTMATTER-CONTROL", flips("V-S9-FRONTMATTER", lambda c: c["frontmatter"]["bad"].append("08-02-SUMMARY.md")))
_saved = dict(dg.MILESTONES)
dg.MILESTONES.pop("S7")
_mm = judged()
dg.MILESTONES.clear()
dg.MILESTONES.update(_saved)
check("V-S9-MILESTONES-CONTROL", base["gates"]["V-S9-MILESTONES"]["ok"] and not _mm["gates"]["V-S9-MILESTONES"]["ok"])
_saved = dict(dg.FC_MAP)
dg.FC_MAP["FC-12"] = ()
_fm = judged()
dg.FC_MAP.clear()
dg.FC_MAP.update(_saved)
check("V-S9-FC-TABLE-CONTROL", base["gates"]["V-S9-FC-TABLE"]["ok"] and not _fm["gates"]["V-S9-FC-TABLE"]["ok"])

# the two suite-derived gates are red now only because of the ROUTE suite; a green copy must turn them green
ev_green = copy.deepcopy(DOC["evidence"])
for n, rec in ev_green["suites"].items():
    if rec["fails"] and n != "test_mission_continuity":
        rec["fails"], rec["exit"] = [], 0
g2 = judged(ev=ev_green)
check("V-S9-SUITES-CONTROL", (not base["gates"]["V-S9-SUITES"]["ok"]) and g2["gates"]["V-S9-SUITES"]["ok"], g2["gates"]["V-S9-SUITES"]["detail"])
check("V-S9-ACCEPTANCE-CONTROL", (not base["gates"]["V-S9-ACCEPTANCE"]["ok"]) and g2["gates"]["V-S9-ACCEPTANCE"]["ok"], g2["gates"]["V-S9-ACCEPTANCE"]["detail"])
check("V-S9-VERDICT-NOT-DONE-IFF-CAUSE", base["verdict"] == ("NOT_DONE" if base["causes"] else base["verdict"]) and
      g2["verdict"] != "NOT_DONE" and g2["verdict"] in ("DONE_WITH_RESIDUALS", "DONE"), f"{base['verdict']} -> {g2['verdict']}")
c3 = copy.deepcopy(CTX)
c3["redteam"]["claims"]["10"]["verdict"] = "BREACH"
check("V-S9-SAFETY-BREACH-IS-NOT-DONE", dg.judge_all(ev_green, c3, JT)["verdict"] == "NOT_DONE")
c4 = copy.deepcopy(CTX)
c4["redteam"]["claims"]["2"]["verdict"] = "BREACH"
c4["redteam"]["breaches"] = sorted(c4["redteam"]["breaches"] + [2])
c4["breach_incident"]["sections"] = list(c4["redteam"]["breaches"])
r4 = dg.judge_all(ev_green, c4, JT)
check("V-S9-NONSAFETY-BREACH-IS-RESIDUAL", r4["verdict"] == "DONE_WITH_RESIDUALS" and "claim 2 BREACH" in r4["residuals"], r4["verdict"])
print("S1_CONTEXT_ROTATION_LIVE", CTX["live"])


# ------------------------------------------------------------------------------------------ mutant drills (08-03 Task 3)
import hashlib  # noqa: E402
import importlib.util  # noqa: E402

SELF_SRC = (TOOLS / "s9_done_gate.py").read_text(encoding="utf-8")
# Bytes on both sides: read_text folds CRLF, so a Windows checkout never matched its own read_bytes.
SELF_SHA = hashlib.sha256((TOOLS / "s9_done_gate.py").read_bytes()).hexdigest()
MUTATIONS = {
    "known-reds-unrestricted": ('extra = sorted(set(rec.get("fails", [])) - allowed)', "extra = []"),
    "floor-ignored": ("elif floor is not None and tot < floor:", "elif False:"),
    "binding-ignored": ('if rec.get("trees") != current["trees"]:', "if False:"),
    "bracket-ignored": ('if rec.get("bracket_moved"):', "if False:"),
    "safety-breach-ignored": ("for c in SAFETY_CLAIMS:", "for c in ():"),
    "core-diff-ignored": ('if ctx["core_diff"]:\n        causes', 'if False:\n        causes'),
    "incident-gate-off": ('_gate(not ctx["incidents"]["findings"] and ', "_gate("),
    "claim15-gate-off": ('claim15.get("verdict") == "UNMEASURED" and ', ""),
    "breach-iff-off": ('bi["sections"] == red["breaches"]', "True"),
    "causes-never-not-done": ("    if causes:\n        verdict = \"NOT_DONE\"", "    if False:\n        verdict = \"NOT_DONE\""),
    "residuals-never-listed": ("    elif residuals:\n        verdict = \"DONE_WITH_RESIDUALS\"", "    elif False:\n        verdict = \"DONE_WITH_RESIDUALS\""),
    "red-item-ignored": ('if any(i["status"] == "RED" for i in sts) or', "if False or"),
}


def load_variant(src: str, tag: str, tmp: Path):
    f = tmp / f"s9_done_gate_{tag}.py"
    f.write_text(src, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(f"s9_variant_{tag}", f)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def probes(m) -> dict:
    """Each probe is True when the judge behaves correctly on one crafted fact; run against the real judge first."""
    out = {}
    cur = JT
    ev = copy.deepcopy(DOC["evidence"])
    evg = copy.deepcopy(ev)
    for n, rec in evg["suites"].items():
        if rec["fails"] and n != "test_mission_continuity":
            rec["fails"], rec["exit"] = [], 0
    ctx = lambda fn: (lambda c: (fn(c), c)[1])(copy.deepcopy(CTX))  # noqa: E731
    e1 = copy.deepcopy(evg); e1["suites"]["test_rotation_invariant"]["fails"] = ["V-ROT-INVENTED"]; e1["suites"]["test_rotation_invariant"]["exit"] = 0
    out["invented-red-is-fail"] = m.judge_all(e1, CTX, cur)["suites"]["test_rotation_invariant"]["status"] == "FAIL"
    e2 = copy.deepcopy(evg); t = e2["suites"]["test_rotation_invariant"]["tag_line"]; t["total"] -= 1; t["passed"] -= 1
    out["floor-drop-is-fail"] = m.judge_all(e2, CTX, cur)["suites"]["test_rotation_invariant"]["status"] == "FAIL"
    e3 = copy.deepcopy(evg); e3["suites"]["test_rotation_invariant"]["trees"] = dict(e3["suites"]["test_rotation_invariant"]["trees"], tools="0" * 64)
    out["unbound-is-inconclusive"] = m.judge_all(e3, CTX, cur)["suites"]["test_rotation_invariant"]["status"] == "INCONCLUSIVE"
    e4 = copy.deepcopy(evg); e4["suites"]["test_rotation_invariant"]["bracket_moved"] = True
    out["bracket-is-inconclusive"] = m.judge_all(e4, CTX, cur)["suites"]["test_rotation_invariant"]["status"] == "INCONCLUSIVE"
    out["green-has-residuals-not-done"] = m.judge_all(evg, CTX, cur)["verdict"] == "DONE_WITH_RESIDUALS"
    out["red-suite-is-not-done"] = m.judge_all(ev, CTX, cur)["verdict"] == "NOT_DONE"
    c5 = ctx(lambda c: c["redteam"]["claims"]["14"].__setitem__("verdict", "BREACH"))
    r5 = m.judge_all(evg, c5, cur)
    out["safety-breach-is-not-done"] = any("safety claim 14" in x for x in r5["causes"])
    out["core-change-is-not-done"] = any("GSD Core" in x for x in m.judge_all(evg, ctx(lambda c: c["core_diff"].append("x")), cur)["causes"])
    out["incident-finding-reds-gate"] = not m.judge_all(evg, ctx(lambda c: c["incidents"]["findings"].append("x")), cur)["gates"]["V-S9-INCIDENTS"]["ok"]
    out["claim15-held-reds-gate"] = not m.judge_all(evg, ctx(lambda c: c["redteam"]["claims"]["15"].__setitem__("verdict", "HELD")), cur)["gates"]["V-S9-REDTEAM"]["ok"]
    out["orphan-section-reds-gate"] = not m.judge_all(evg, ctx(lambda c: c["breach_incident"]["sections"].pop()), cur)["gates"]["V-S9-BREACH-INCIDENT-IFF"]["ok"]
    its = m.build_items(m.judge_suites(e1, cur), CTX)
    out["red-item-gives-not-met"] = any(m.row_status(k, its) == "NOT_MET" for k in m.MILESTONES.values())
    return out


with tempfile.TemporaryDirectory(prefix="s9-drill-") as td:
    tmp = Path(td)
    noop = probes(load_variant(SELF_SRC, "noop", tmp))
    check("V-S9-DRILL-NOOP-CONTROL", all(noop.values()) and len(noop) >= 12, str({k: v for k, v in noop.items() if not v}) or f"{len(noop)} probes all hold")
    MUTANT_FOR = {
        "invented-red-is-fail": ["known-reds-unrestricted"], "floor-drop-is-fail": ["floor-ignored"],
        "unbound-is-inconclusive": ["binding-ignored"], "bracket-is-inconclusive": ["bracket-ignored"],
        "green-has-residuals-not-done": ["residuals-never-listed"], "red-suite-is-not-done": ["causes-never-not-done"],
        "safety-breach-is-not-done": ["safety-breach-ignored"], "core-change-is-not-done": ["core-diff-ignored"],
        "incident-finding-reds-gate": ["incident-gate-off"], "claim15-held-reds-gate": ["claim15-gate-off"],
        "orphan-section-reds-gate": ["breach-iff-off"], "red-item-gives-not-met": ["red-item-ignored"],
    }
    applied, killed, bad = [], [], []
    for mid, (old, new_) in MUTATIONS.items():
        if SELF_SRC.count(old) != 1:
            bad.append(f"{mid} matches {SELF_SRC.count(old)}x")
            continue
        applied.append(mid)
        got = probes(load_variant(SELF_SRC.replace(old, new_), mid, tmp))
        expected = sorted(g for g, ms in MUTANT_FOR.items() if mid in ms)
        broke = sorted(g for g, ok in got.items() if not ok)
        if broke and set(expected) <= set(broke):
            killed.append(mid)
        else:
            bad.append(f"{mid}: expected {expected} broke {broke}")
check("V-S9-MUTANT-APPLIES", not [b for b in bad if "matches" in b] and len(applied) == len(MUTATIONS), str(bad))
check("V-S9-MUTANTS-KILLED", len(killed) == len(MUTATIONS) and not bad, f"{len(killed)}/{len(MUTATIONS)} killed {bad}")
check("V-S9-MUTANT-MAP", sorted(MUTANT_FOR) == sorted(noop) and sorted({m for ms in MUTANT_FOR.values() for m in ms}) == sorted(MUTATIONS),
      f"probes {len(noop)} mutants {len(MUTATIONS)}")
check("V-S9-DRILL-REAL-FILE-UNTOUCHED", hashlib.sha256((TOOLS / "s9_done_gate.py").read_bytes()).hexdigest() == SELF_SHA)


# ------------------------------------------------------------------------------------------ report (08-03 Task 3)
REPORT = PHASE / "08-REPORT.md"
fresh = dg.render_report(DOC)
check("V-S9-REPORT-REPRODUCES", REPORT.is_file() and REPORT.read_text(encoding="utf-8") == fresh, f"{len(fresh)} bytes")
cites = dg.cited_lines()
labels = {c[0] for c in cites}
w = [ln for lab, ln in cites if lab == "07-VERIFICATION.md"]
st = [ln for lab, ln in cites if lab == "STATE.md"]
src7 = (dg.P7 / "07-VERIFICATION.md").read_text(encoding="utf-8")
check("V-S9-RESIDUAL-CITED", len(w) == 5 and len(st) == 2 and all(ln in src7 for ln in w) and all(("> [" + lab + "] " + ln) in fresh for lab, ln in cites),
      f"W lines {len(w)} STATE lines {len(st)}")
check("V-S9-RESIDUAL-CITED-CONTROL", "- W1: " in fresh and not dg.cited_lines(Path(tempfile.gettempdir())), "an empty root cites nothing")
check("V-S9-ROUTE-RED-STATED", dg.ROUTE_STATEMENT in fresh and "test_cpp_gsd_long_routing" in " ".join(DOC["judgement"]["causes"]))

# ------------------------------------------------------------------------------------------ output
fails = [g for g, ok, _ in RESULTS if not ok]
print(f"wall={time.time() - T0:.1f}s")
print(f"S9_PASS={len(RESULTS) - len(fails)}/{len(RESULTS)}  threshold={len(RESULTS)}/{len(RESULTS)}")
sys.exit(0 if not fails else 1)
