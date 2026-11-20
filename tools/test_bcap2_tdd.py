"""test_bcap2_tdd.py -- CPP-TDD-001 done-gate (V-TDD-*). Run: python3 tools/test_bcap2_tdd.py ; exit 0 iff all pass.

The 14 adversarial fixtures of vault/backlog/2026-10-11_tdd-evidence-first-vertical-slice-ratchet.md are poles:
each seeded defect must be refused with its named code and each clean twin must certify. Mutation outcomes
come from the REAL tools/test_gaps.py run on a throwaway pytest project (no second mutator).
"""
from __future__ import annotations

import copy
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from modules.skill_router.intent_classifier import classify_intent  # noqa: E402
from modules.skill_router.skill_index import build_index  # noqa: E402
from modules.uqf.principles.tdd_workflow import (TDDWorkflow, classify_slice, mutation_outcome)  # noqa: E402

P = F = 0


def ok(g, e):
    global P
    P += 1
    print(f"  [PASS] {g}: {e}")


def bad(g, d):
    global F
    F += 1
    print(f"  [FAIL] {g}: {d}")


def check(g, cond, detail):
    (ok if cond else bad)(g, detail)


def clean() -> dict:
    return {
        "kind": "behavior_change", "language": "python", "worktree": "wt-1",
        "sources": ["pkg/a.py"], "tests": ["tests/test_a.py"],
        "required_acceptance_ids": ["AC-1"], "baseline_acceptance_ids": ["AC-1"],
        "slices": [{
            "acceptance_id": "AC-1", "worktree": "wt-1", "test": "tests/test_a.py::test_ac1",
            "red": {"observed": True, "reason": "missing_behavior", "test_rev": "t1", "impl_rev": "i1",
                    "test_before_impl": True, "runner": "pytest -x"},
            "oracle": {"kind": "independent", "source": "AC-1"},
            "green": {"observed": True, "targeted_passed": True},
            "refactor": {"applied": True, "behavior_preserved": True},
            "mutation": {"outcome": "KILLED"},
            "integration": {"observed": True, "state_valid": True}}],
        "environment": {"hook_event_lost": False, "orphan_pids": 0},
        "wiring": {"has_caller": True, "reachable_from_entrypoint": True, "activation_path_exists": True},
    }


def mut(fn):
    r = copy.deepcopy(clean())
    fn(r)
    return r


def sl(r):
    return r["slices"][0]


def test_fixtures():
    c = classify_slice(clean())
    check("V-TDD-CLEAN", c["status"] == "BEHAVIOR_VERIFIED" and c["certifies_tdd"], f"{c['status']} ladder={c['ladder']}")

    # 1: heuristic passes on one test + several sources, proof does not
    f1 = {"kind": "behavior_change", "sources": ["a.py", "b.py", "c.py"], "tests": ["tests/test_a.py"],
          "worktree": "wt-1", "required_acceptance_ids": ["AC-1"]}
    heur = TDDWorkflow().check({"sources": f1["sources"], "tests": f1["tests"]}, "code")
    r = classify_slice(f1)
    check("V-TDD-F01-ONE-TEST-MANY-SOURCES", heur.passed and "HEURISTIC_ONLY" in heur.evidence
          and not r["certifies_tdd"] and r["status"] == "EVIDENCE_INCOMPLETE" and "NO_SLICE_EVIDENCE" in r["codes"],
          f"heuristic.passed={heur.passed} proof={r['status']}")

    def run(name, rec, code, status=None, certifies=False):
        r = classify_slice(rec)
        hit = any(c.startswith(code) for c in r["codes"])
        good = hit and r["certifies_tdd"] == certifies and (status is None or r["status"] == status)
        check(name, good, f"status={r['status']} codes={r['codes'][:3]}")

    run("V-TDD-F02-POST-HOC-TEST", mut(lambda r: sl(r)["red"].update(test_before_impl=False)), "POST_HOC_TEST")
    for why in ("import", "fixture", "syntax", "env", "unrelated", "baseline_broken"):
        run(f"V-TDD-F03-INVALID-RED[{why}]", mut(lambda r, w=why: sl(r)["red"].update(reason=w)), "INVALID_RED")
    r = classify_slice(mut(lambda r: sl(r)["red"].update(reason="assertion")))
    check("V-TDD-F04-VALID-RED", r["slices"][0]["red_ok"] and r["certifies_tdd"], f"status={r['status']}")
    run("V-TDD-F05-ORACLE-COPIED", mut(lambda r: sl(r).update(oracle={"kind": "copied_from_impl"})), "ORACLE_NOT_INDEPENDENT")
    run("V-TDD-F05b-ORACLE-UNRESOLVED", mut(lambda r: sl(r).update(oracle={"kind": "inferred"})), "ORACLE_UNRESOLVED")
    run("V-TDD-F05d-TAUTOLOGY", mut(lambda r: sl(r).update(test_source="def test_a():\n    assert add(a, b) == a + b\n")),
        "TAUTOLOGICAL_ASSERTION")
    run("V-TDD-F05e-TAUTOLOGY-SELF", mut(lambda r: sl(r).update(test_source="def test_a():\n    assert f(x) == f(x)\n")),
        "TAUTOLOGICAL_ASSERTION")
    rl = classify_slice(mut(lambda r: sl(r).update(test_source="def test_a():\n    assert add(2, 3) == 5\n")))
    check("V-TDD-F05f-LITERAL-EXPECTED-ACCEPTED", rl["certifies_tdd"] and not any(c.startswith("TAUTOLOGICAL") for c in rl["codes"]),
          f"status={rl['status']} codes={rl['codes']}")
    run("V-TDD-F05c-ORACLE-NO-SOURCE", mut(lambda r: sl(r).update(oracle={"kind": "independent"})), "ORACLE_UNRESOLVED")
    # 6: pure refactor with a passing baseline is a scoped exemption, without it it is not
    r6 = classify_slice({"kind": "pure_refactor", "prior_passing_baseline": True, "sources": ["a.py"], "tests": []})
    check("V-TDD-F06-REFACTOR-EXEMPT", r6["status"] == "EXEMPT_SCOPED" and r6["slices"] == [] and not r6["certifies_tdd"],
          f"{r6['status']} (no synthetic RED, no TDD certification)")
    r6b = classify_slice({"kind": "pure_refactor", "prior_passing_baseline": False, "sources": ["a.py"]})
    check("V-TDD-F06b-REFACTOR-NO-BASELINE", r6b["status"] == "EVIDENCE_INCOMPLETE", r6b["status"])
    run("V-TDD-F07-SURVIVOR-VISIBLE", mut(lambda r: sl(r).update(mutation={"outcome": "SURVIVED"})), "SURVIVOR_VISIBLE",
        status="EVIDENCE_INCOMPLETE")
    run("V-TDD-F07b-SURVIVOR-DISPOSED", mut(lambda r: sl(r).update(
        mutation={"outcome": "SURVIVED", "disposition": "equivalent mutant: dead branch"})), "SURVIVOR_VISIBLE",
        certifies=True)
    for o in ("TIMEOUT", "UNMEASURABLE", "ERROR"):
        r = classify_slice(mut(lambda r, o=o: sl(r).update(mutation={"outcome": o})))
        check(f"V-TDD-F08-{o}-NOT-PASS", f"MUTATION_{o}:AC-1" in r["codes"] and r["ladder_evidence"]["regression_case_pinned"] is None
              and r["certifies_tdd"], f"codes={r['codes']} (honest: measured RED/GREEN stay, no pin, not a pass)")
    run("V-TDD-F09-INVALID-ARCH-STATE", mut(lambda r: sl(r).update(integration={"observed": True, "state_valid": False})),
        "INTEGRATION_INVALID_STATE", status="EVIDENCE_INCOMPLETE")
    run("V-TDD-F10-HOOK-LOST", mut(lambda r: r["environment"].update(hook_event_lost=True)), "ENVIRONMENT_BLOCKED", status="BLOCKED")
    run("V-TDD-F10b-ORPHAN", mut(lambda r: r["environment"].update(orphan_pids=2)), "ENVIRONMENT_BLOCKED", status="BLOCKED")

    def f11(r):
        r["required_acceptance_ids"] = ["AC-1", "AC-2"]
        r["baseline_acceptance_ids"] = ["AC-1", "AC-2"]
    run("V-TDD-F11-GREEN-BUT-AC-UNOBSERVED", mut(f11), "ACCEPTANCE_UNOBSERVED:AC-2", status="EVIDENCE_INCOMPLETE")
    r = classify_slice(mut(lambda r: r.update(language="typescript")))
    check("V-TDD-F12-UNSUPPORTED-LANGUAGE-CEILING", "MUTATION_UNSUPPORTED_LANGUAGE:typescript" in r["codes"]
          and r["ladder_evidence"]["regression_case_pinned"] is None, f"codes={r['codes']}")
    check("V-TDD-F12b-SUPPORTED-LANGUAGE-PINS", classify_slice(clean())["ladder_evidence"]["regression_case_pinned"] is True,
          "python KILLED slice pins the regression case")

    def f13(r):
        r["required_acceptance_ids"] = ["AC-1"]
        r["baseline_acceptance_ids"] = ["AC-1", "AC-2"]
    run("V-TDD-F13-RATCHET-DROPPED-AC", mut(f13), "RATCHET_ACCEPTANCE_DROPPED", status="EVIDENCE_INCOMPLETE")
    run("V-TDD-F14-OTHER-WORKTREE", mut(lambda r: sl(r).update(worktree="wt-OTHER")), "MISATTRIBUTED_WORKTREE")
    run("V-TDD-RED-PROVENANCE-MISSING", mut(lambda r: sl(r)["red"].pop("runner")), "RED_PROVENANCE_MISSING")
    run("V-TDD-GREEN-ABSENT", mut(lambda r: sl(r).update(green={"observed": True, "targeted_passed": False})), "GREEN_ABSENT")
    run("V-TDD-REFACTOR-BROKE", mut(lambda r: sl(r).update(refactor={"applied": True, "behavior_preserved": False})),
        "REFACTOR_BROKE_BEHAVIOR")
    check("V-TDD-NOT-A-DICT", classify_slice("x")["status"] == "EVIDENCE_INCOMPLETE", "non-dict refused")
    # C1 vocabulary
    for kind, want in (("docs_only", "NOT_APPLICABLE"), ("legacy", "CONDITIONAL"), ("exploratory", "CONDITIONAL"),
                       ("mystery", "UNRESOLVED"), ("behavior_change", "APPLICABLE")):
        check(f"V-TDD-C1[{kind}]", classify_slice({"kind": kind})["applicability"] == want, want)
    check("V-TDD-C1-UNRESOLVED-NOT-SUCCESS", classify_slice({"kind": "mystery"})["status"] == "EVIDENCE_INCOMPLETE", "UNRESOLVED != success")


def test_ladder_mapping():
    """Stage facts land on strength_ladder keys; no new enum, three-valued evidence preserved."""
    from modules.done_gate.strength_ladder import LADDER
    c = classify_slice(clean())
    # TDD evidence alone must NOT reach the production rungs: it supplies no production_like/real_boundary facts.
    check("V-TDD-LADDER-CEILING", c["ladder"] == "ADVERSARIALLY-VERIFIED" and c["ladder"] in LADDER
          and "production_like_env_exercised" in c["ladder_unknown"], f"{c['ladder']} unknown={c['ladder_unknown']}")
    r = classify_slice(mut(lambda r: r.pop("wiring")))
    check("V-TDD-LADDER-UNKNOWN-IS-NOT-PASS", LADDER.index(r["ladder"]) < LADDER.index("WIRED") and "has_caller" in r["ladder_unknown"],
          f"ladder={r['ladder']} unknown={r['ladder_unknown']}")
    r = classify_slice(mut(lambda r: sl(r).update(mutation={"outcome": "SURVIVED", "disposition": "ok"})))
    check("V-TDD-LADDER-SURVIVOR-NOT-PINNED", r["ladder_evidence"]["regression_case_pinned"] is False, str(r["ladder_evidence"]))


def mini_project(d: Path, test_src: str):
    (d / "m.py").write_text("def double(x):\n    return x * 2\n")
    (d / "test_m.py").write_text(test_src)


def test_mutation_oracle():
    """REAL tools/test_gaps.py, two poles: an asserting test kills, a smoke test lets the mutant survive."""
    import test_gaps  # tools/test_gaps.py (the existing mutator; none is written here)
    py = os.environ.get("BCAP2_TDD_PYTHON", sys.executable)  # interpreter with pytest+pytest-cov+coverage
    if subprocess.run([py, "-c", "import pytest, pytest_cov, coverage"], capture_output=True).returncode != 0:
        bad("V-TDD-MUT-REAL", f"{py} lacks pytest/pytest-cov/coverage: mutation oracle NOT measured (set BCAP2_TDD_PYTHON)")
        return
    outs = {}
    for label, body in (("strong", "from m import double\n\ndef test_d():\n    assert double(3) == 6\n"),
                        ("weak", "from m import double\n\ndef test_d():\n    double(3)\n")):
        with tempfile.TemporaryDirectory(prefix="tdd-mut-") as d:
            mini_project(Path(d), body)
            res = test_gaps.analyse(Path(d), files=["m.py"], max_mutants=5, baseline_timeout=120, python=py)
            outs[label] = (mutation_outcome(res), res.get("verdict"))
    check("V-TDD-MUT-REAL-KILLED", outs["strong"][0] == "KILLED", f"strong -> {outs['strong']}")
    check("V-TDD-MUT-REAL-SURVIVED", outs["weak"][0] == "SURVIVED", f"weak -> {outs['weak']}")
    # an already-failing base suite is UNMEASURABLE, never pass/fail
    with tempfile.TemporaryDirectory(prefix="tdd-mut-") as d:
        mini_project(Path(d), "from m import double\n\ndef test_d():\n    assert double(3) == 7\n")
        res = test_gaps.analyse(Path(d), files=["m.py"], max_mutants=5, baseline_timeout=120, python=py)
        check("V-TDD-MUT-REAL-BASE-RED-UNMEASURABLE", mutation_outcome(res) == "UNMEASURABLE", f"verdict={res.get('verdict')}")
    # mapping, pure poles
    for res, want in (({"verdict": "UNMEASURABLE"}, "UNMEASURABLE"), ({"timeout": [1]}, "TIMEOUT"), ({"errors": [1]}, "ERROR"),
                      ({"survived": [1], "killed": [1]}, "SURVIVED"), ({"killed": [1]}, "KILLED"), ({"verdict": "NO_CHANGES"}, "NOT_RUN"),
                      ("junk", "ERROR")):
        check(f"V-TDD-MUT-MAP[{want}]", mutation_outcome(res) == want, str(res))


def test_routing():
    sk = build_index(force=True)
    for prompt, want in (("implement a retry budget for the export job", True),
                         ("add support for csv export in the report tool", True),
                         ("implementa la nueva funcionalidad de exportar", True),
                         ("fix a typo in the readme", False),
                         ("refactor the parser to be cleaner", False),
                         ("update the documentation for the api", False),
                         ("build a landing page", False),
                         ("the login keeps failing after the last deploy", False)):
        r = classify_intent(prompt, sk)
        woke = r.should_wakeup and r.domain == "tdd"
        check(f"V-TDD-ROUTE[{prompt[:30]}]", woke == want, f"domain={r.domain} wake={r.should_wakeup}")
    # the diagnose gate must still route the bug prompts (no cross-capture)
    r = classify_intent("the login keeps failing after the last deploy", sk)
    check("V-TDD-ROUTE-DIAGNOSE-INTACT", r.domain == "diagnose", r.domain)


def test_real_slice():
    """Real historical slice 96b6f09a (shared seam with Phase 1): RED observed at the parent, GREEN at the fix, through git."""
    rel = "vault/programs/ascension/autopilot/autopilot.py"
    ev = "evidence/ascension/s177m/checkpoint_s177m_r1b.md@74cbfef"
    want = "evidence/ascension/s177m/checkpoint_s177m_r1b.md"
    got = {}
    # "~1", never "^": shell=True runs cmd.exe on Windows, where ^ is the escape char and "96b6f09a^ " silently
    # became "96b6f09a " -- the "parent" archive was the fix, so the bug never reproduced (2026-11-20).
    for label, rev in (("parent", "96b6f09a~1"), ("fix", "96b6f09a")):
        with tempfile.TemporaryDirectory(prefix="tdd-real-") as d:
            ar = subprocess.run(f"git -C {ROOT} archive {rev} -- vault/programs/ascension/autopilot | tar -x -C {d}",
                                shell=True, capture_output=True, text=True)
            f = Path(d) / rel
            if ar.returncode != 0 or not f.is_file():
                bad("V-TDD-REAL-SLICE", f"git archive {rev} failed: {ar.stderr.strip()[:120]}")
                return
            sys.path.insert(0, str(f.parent))
            spec = importlib.util.spec_from_file_location(f"tdd_ap_{label}", f)
            m = importlib.util.module_from_spec(spec)
            sys.modules[f"tdd_ap_{label}"] = m
            try:
                spec.loader.exec_module(m)
                got[label] = m.hold_checkpoint({"evidence": ev})
            except Exception as e:  # import/crash = INVALID red, not the missing behavior
                got[label] = f"HARNESS_ERROR {type(e).__name__}"
            finally:
                sys.path.remove(str(f.parent))
                for k in [k for k in sys.modules if k == "evolve" or k.startswith(f"tdd_ap_{label}")]:
                    sys.modules.pop(k, None)
    red_wrong_output = got["parent"] == ev and not str(got["parent"]).startswith("HARNESS_ERROR")
    green = got["fix"] == want
    rec = clean()
    rec["slices"][0]["red"]["reason"] = "assertion" if red_wrong_output else "import"
    rec["slices"][0]["green"] = {"observed": True, "targeted_passed": green}
    rec["slices"][0]["red"]["observed"] = red_wrong_output
    rec["slices"][0].pop("mutation")  # honest: not measured on this slice
    r = classify_slice(rec)
    check("V-TDD-REAL-SLICE-RED", red_wrong_output, f"parent returns {got['parent']!r}")
    check("V-TDD-REAL-SLICE-GREEN", green, f"fix returns {got['fix']!r}")
    check("V-TDD-REAL-SLICE-CLASSIFIED", r["certifies_tdd"] and r["slices"][0]["mutation"] == "NOT_RUN",
          f"status={r['status']} (mutation NOT_RUN stays visible)")
    # and the same observed facts with a harness crash as 'red' must not certify
    rec2 = copy.deepcopy(rec)
    rec2["slices"][0]["red"]["reason"] = "import"
    check("V-TDD-REAL-SLICE-FALSE-RED-REFUSED", not classify_slice(rec2)["certifies_tdd"], "import-class red refused")


def test_p07_reachable():
    """P07 is only registered; the card + CLI are its first real entrypoints. Prove the CLI runs and exits by verdict."""
    import json
    with tempfile.TemporaryDirectory(prefix="tdd-cli-") as d:
        a, b = Path(d) / "ok.json", Path(d) / "no.json"
        a.write_text(json.dumps(clean()))
        b.write_text(json.dumps(mut(lambda r: sl(r)["red"].update(test_before_impl=False))))
        ra = subprocess.run([sys.executable, "-m", "modules.uqf.principles.tdd_workflow", str(a)], cwd=ROOT, capture_output=True, text=True)
        rb = subprocess.run([sys.executable, "-m", "modules.uqf.principles.tdd_workflow", str(b)], cwd=ROOT, capture_output=True, text=True)
    check("V-TDD-CLI", ra.returncode == 0 and rb.returncode == 1, f"clean rc={ra.returncode} posthoc rc={rb.returncode}")


def main() -> int:
    for t in (test_fixtures, test_ladder_mapping, test_mutation_oracle, test_routing, test_real_slice, test_p07_reachable):
        t()
    print(f"\nBCAP2_TDD_{'PASS' if F == 0 else 'FAIL'}: {P} PASS, {F} FAIL")
    return 0 if F == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
