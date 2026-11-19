"""test_bcap2_dbg.py -- CPP-DBG-001 done-gate (V-DBG-*). Run: python3 tools/test_bcap2_dbg.py ; exit 0 iff all pass.

Every fixture is a pole pair: a seeded-defect record the verifier must REJECT with its named code, and a
clean record it must VERIFY. V-DBG-REAL-BUG runs a real historical CPP bug (96b6f09a, S177M hold
"<path>@<sha>") red at the parent commit and green at the fix, through git, in a throwaway dir.
"""
from __future__ import annotations

import copy
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modules.craif.diagnosis import assess, classify_tier, required_clean_runs  # noqa: E402
from modules.skill_router.intent_classifier import classify_intent  # noqa: E402
from modules.skill_router.skill_index import build_index  # noqa: E402

P = F = 0


def ok(g, e):
    global P
    P += 1
    print(f"  [PASS] {g}: {e}")


def bad(g, d):
    global F
    F += 1
    print(f"  [FAIL] {g}: {d}")


def clean() -> dict:
    return {
        "claim": "FIXED", "tier": "STANDARD",
        "symptom": {"verbatim": "export returns 0 rows", "expected": "12 rows", "observed": "0 rows",
                    "commit": "abc1234", "worktree": "wt-1", "scope": "multi_component"},
        "loop": {"red_observed": True, "red_reason": "assertion", "oracle_kind": "exact", "entrypoint": "real",
                 "negative_control": True, "trigger": {"kind": "deterministic"}},
        "minimisation": {"steps": [{"removed": "cache", "bug_persisted": True}], "final_dropped": ["cache"]},
        "hypotheses": [
            {"id": "h1", "predicts_if_true": "row 3 missing", "disposition": "supported", "corroborations": 2},
            {"id": "h2", "predicts_if_true": "all rows missing", "disposition": "falsified"}],
        "instrumentation": {"markers": [{"tag": "DBG-1", "removed_proof": "grep clean"}], "redaction_applied": True},
        "harness": {"bounded": True, "orphan_pids": 0},
        "artifacts": [{"worktree": "wt-1", "commit": "abc1234"}],
        "fix": {"regression_seam": "real", "original_path_rerun": "green", "mutation_detects": True},
        "evidence_text": "plain output",
    }


def mut(fn):
    r = copy.deepcopy(clean())
    fn(r)
    return r


FIXTURES = [  # (n, name, mutation, expected code)
    (1, "false-red", lambda r: r["loop"].update(red_reason="import"), "DBG-C02-FALSE-RED"),
    (2, "weak-oracle", lambda r: r["loop"].update(oracle_kind="no_crash"), "DBG-C02-WEAK-ORACLE"),
    (3, "mock-mismatch", lambda r: r["loop"].update(entrypoint="mock"), "DBG-C02-CONTRACT-MISMATCH"),
    (4, "unfaithful-minimisation",
     lambda r: r["minimisation"]["steps"].append({"removed": "init-order", "bug_persisted": False})
     or r["minimisation"]["final_dropped"].append("init-order"), "DBG-C03-UNFAITHFUL-MINIMISATION"),
    (5, "visible-not-cause",
     lambda r: r.update(divergence={"causal_position": 2, "visible_position": 7, "cause_claimed_at": 7}),
     "DBG-C03-VISIBLE-SYMPTOM-IS-NOT-CAUSE"),
    (6, "uncorroborated-survivor",
     lambda r: r["hypotheses"][0].update(corroborations=1), "DBG-C04-INSUFFICIENT-CORROBORATION"),
    (7, "non-discriminating",
     lambda r: r["hypotheses"][1].update(predicts_if_true="row 3 missing"), "DBG-C04-NON-DISCRIMINATING"),
    (8, "flake-one-green",
     lambda r: (r["loop"].update(trigger={"kind": "probabilistic", "attempts": 100, "failures": 1}),
                r["fix"].update(clean_runs_after_fix=1)), "DBG-C05-FLAKE-UNDERPOWERED"),
    (9, "perf-confounded",
     lambda r: r.update(perf={"baseline_pinned": True, "host_load_stable": False, "same_inputs": True}),
     "DBG-C05-MEASUREMENT-CONFOUNDED"),
    (10, "shallow-seam",
     lambda r: r["fix"].update(regression_seam="unit", multi_caller_still_failing=True), "DBG-C06-SHALLOW-SEAM"),
    (11, "blind-regression-gate", lambda r: r["fix"].update(mutation_detects=False), "DBG-C06-BLIND-REGRESSION-GATE"),
    (12, "invented-rca", lambda r: r["loop"].update(red_observed=False), "DBG-C07-INVENTED-RCA"),
    (13, "hung-harness", lambda r: r["harness"].update(bounded=False, orphan_pids=2), "DBG-C07-UNBOUNDED-HARNESS"),
    (14, "har-secret", lambda r: (r.update(evidence_text="Authorization: Bearer abcdef0123456789"),
                                  r["instrumentation"].update(redaction_applied=False)), "DBG-C05-SECRET-LEAK"),
    (15, "leftover-instrumentation",
     lambda r: r["instrumentation"]["markers"].append({"tag": "DBG-2"}), "DBG-C08-LEFTOVER-INSTRUMENTATION"),
    (16, "mixed-worktree", lambda r: r["artifacts"].append({"worktree": "wt-2", "commit": "abc1234"}),
     "DBG-C05-UNBOUND-PROVENANCE"),
    (17, "original-still-broken", lambda r: r["fix"].update(original_path_rerun="red"), "DBG-C06-ORIGINAL-PATH-NOT-GREEN"),
    (18, "workaround-as-fix", lambda r: r["fix"].update(mitigation_only=True), "DBG-C06-MITIGATION-NOT-RESOLUTION"),
    (19, "promote-unresolved",
     lambda r: (r["hypotheses"][1].update(disposition="unresolved"), r.update(promotion={"requested": True})),
     "DBG-C08-PROMOTION-REFUSED"),
    (20, "trivial-bug-forensic",
     lambda r: (r.update(tier="FORENSIC", agents_used=4), r["symptom"].update(scope="single_line")),
     "DBG-C07-OVER-CEREMONY"),
]


def test_fixtures():
    v = assess(clean())
    (ok if v.status == "VERIFIED" else bad)("V-DBG-POSITIVE-CONTROL", f"clean record -> {v.status} {v.rejections}")
    for n, name, fn, code in FIXTURES:
        v = assess(mut(fn))
        g = f"V-DBG-FX{n:02d}-{name}"
        if v.status == "REJECTED" and code in v.rejections:
            ok(g, f"rejected with {code}")
        else:
            bad(g, f"expected {code}, got {v.status} {v.rejections}")


def test_honest_states():
    r = mut(lambda r: (r.update(claim="NOT_REPRODUCED", attempts=["3 bounded probes, no red"]),
                       r["loop"].update(red_observed=False)))
    v = assess(r)
    (ok if v.status == "HONEST_UNRESOLVED" else bad)("V-DBG-NOT-REPRODUCED-IS-VALID", f"{v.status} {v.rejections}")
    r2 = mut(lambda r: (r.update(claim="NOT_REPRODUCED"), r["loop"].update(red_observed=False)))
    v2 = assess(r2)
    (ok if "DBG-C07-NON-REPRODUCTION-UNDOCUMENTED" in v2.rejections else bad)(
        "V-DBG-NOT-REPRODUCED-NEEDS-ATTEMPTS", str(v2.rejections))
    v3 = assess(mut(lambda r: r.update(claim="SOLVED")))
    (ok if "DBG-CLAIM-UNKNOWN" in v3.rejections else bad)("V-DBG-UNKNOWN-CLAIM-REJECTED", str(v3.rejections))
    v4 = assess(mut(lambda r: r["fix"].pop("mutation_detects")))
    (ok if v4.status == "VERIFIED" and v4.unmeasured else bad)(
        "V-DBG-UNMEASURED-IS-REPORTED", f"{v4.status} unmeasured={v4.unmeasured}")
    v5 = assess(mut(lambda r: r.update(tier="LIGHT", hypotheses=[])))
    (ok if v5.status == "VERIFIED" else bad)("V-DBG-LIGHT-NO-RITUAL-HYPOTHESES", f"{v5.status} {v5.rejections}")


def test_math_and_tier():
    n = required_clean_runs(1, 100)
    (ok if n == 299 else bad)("V-DBG-FLAKE-MATH", f"1% flake needs {n} clean runs (expect 299)")
    (ok if required_clean_runs(0, 50) is None else bad)("V-DBG-FLAKE-ABSENT-NOT-ZERO", "no observed failure -> None")
    t = (classify_tier("single_line"), classify_tier("multi_component"), classify_tier("localised", intermittent=True))
    (ok if t == ("LIGHT", "STANDARD", "FORENSIC") else bad)("V-DBG-TIERS", str(t))


def test_routing():
    sk = build_index(force=True)
    for prompt, want in (("the login keeps failing after the last deploy", True),
                         ("why is the export so slow, it regressed", True),
                         ("hola, esto no funciona desde ayer", True),
                         ("fix a typo in the readme", False),
                         ("build a landing page", False)):
        r = classify_intent(prompt, sk)
        woke = r.should_wakeup and r.domain == "diagnose"
        (ok if woke == want else bad)(f"V-DBG-ROUTE[{prompt[:28]}]", f"domain={r.domain} wake={r.should_wakeup}")


def test_real_bug():
    """Historical CPP bug 96b6f09a: a hold evidence "<path>@<sha>" was read as one path."""
    rel = "vault/programs/ascension/autopilot/autopilot.py"
    ev = "evidence/ascension/s177m/checkpoint_s177m_r1b.md@74cbfef"
    want = "evidence/ascension/s177m/checkpoint_s177m_r1b.md"
    control = "evidence/ascension/s70w/checkpoint.md"  # negative control: a plain path is unchanged at both commits
    res = {}
    for label, rev in (("parent", "96b6f09a^"), ("fix", "96b6f09a")):
        with tempfile.TemporaryDirectory(prefix="dbg-real-") as d:
            ar = subprocess.run(f"git -C {ROOT} archive {rev} -- vault/programs/ascension/autopilot | tar -x -C {d}",
                                shell=True, capture_output=True, text=True)
            f = Path(d) / rel
            if ar.returncode != 0 or not f.is_file():
                bad("V-DBG-REAL-BUG", f"git archive {rev} failed: {ar.stderr.strip()[:120]}")
                return
            sys.path.insert(0, str(f.parent))  # sibling modules at THIS revision
            spec = importlib.util.spec_from_file_location(f"ap_{label}", f)
            m = importlib.util.module_from_spec(spec)
            sys.modules[f"ap_{label}"] = m
            try:
                spec.loader.exec_module(m)
                res[label] = (m.hold_checkpoint({"evidence": ev}), m.hold_checkpoint({"evidence": control}))
            except Exception as e:  # an import/crash is a FALSE red (fixture 1), not the bug
                bad("V-DBG-REAL-BUG", f"{label}: harness error {type(e).__name__}: {e}")
                return
            finally:
                sys.path.remove(str(f.parent))
                for k in [k for k in sys.modules if k in ("evolve",) or k.startswith(f"ap_{label}")]:
                    sys.modules.pop(k, None)
    red = res["parent"][0] != want and res["parent"][0] == ev          # bug: whole string taken as a path
    green = res["fix"][0] == want
    controls = res["parent"][1] == control and res["fix"][1] == control
    (ok if red else bad)("V-DBG-REAL-BUG-RED", f"parent returns {res['parent'][0]!r} (exact wrong output, not a crash)")
    (ok if green else bad)("V-DBG-REAL-BUG-GREEN", f"fix returns {res['fix'][0]!r}")
    (ok if controls else bad)("V-DBG-REAL-BUG-NEGATIVE-CONTROL", "plain path identical at both commits")


def main() -> int:
    for t in (test_fixtures, test_honest_states, test_math_and_tier, test_routing, test_real_bug):
        t()
    print(f"\nBCAP2_DBG_{'PASS' if F == 0 else 'FAIL'}: {P} PASS, {F} FAIL")
    return 0 if F == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
