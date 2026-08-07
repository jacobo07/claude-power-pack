#!/usr/bin/env python3
"""Done-gate for the CDICF dependency-scope hard filter (V-CDICF-SCOPE-*).

The Owner's ruling shapes every gate here: a missing dependency is CRITICAL
because it is observable in production on first render; a low score is a
judgment and is not. So the check is a HARD FILTER evaluated before the score,
never a `critical` Verdict -- a critical Verdict subtracts 25, and that would
change score composition, re-scoring surfaces nobody touched.

Two properties carry the suite:

  1. **Composition is preserved.** `review_gate` with no target must equal
     `score_review` exactly, and the §5 threshold must still be 80. This is
     asserted directly rather than inferred from "the tests still pass".
  2. **The gate catches what the installer structurally cannot.** The installer
     resolves dependencies at INSTALL time and refuses at exit 11. It cannot see
     a dependency removed from package.json a week later. That case is the
     reason this check exists, and it is exercised against a REAL install
     produced by the real emitter and installer, not a hand-written record.

Hermetic: temp projects only.

Run:  python tools/test_cdicf_scope.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from modules.cdio.scorer import (  # noqa: E402
    APPROVE_MIN, DEP_UNASSESSED, DEP_UNRESOLVED, Verdict,
    check_component_dependencies, review_gate, score_review,
)

FIXTURE = os.path.join(ROOT, "tests", "fixtures", "cdicf_dep_fixture.js")
DEP = "@radix-ui/react-slot"

PASSES = 0
FAILS = 0


def _ok(gate: str, evidence: str) -> None:
    global PASSES
    PASSES += 1
    print(f"  [PASS] {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global FAILS
    FAILS += 1
    print(f"  [FAIL] {gate}: {diagnostic}")


def _V(status: str, sev: str = "") -> Verdict:
    return Verdict(criterion="c", dimension="visual", status=status,
                   severity=sev, observed="x" if status == "fail" else "")


# The 82-scoring surface from the Owner's example: two majors + one minor.
SURFACE_82 = [_V("fail", "major"), _V("fail", "major"), _V("fail", "minor")]


def _build(target: str, declare: bool):
    args = ["node", FIXTURE, target, DEP] + (["--declare"] if declare else [])
    p = subprocess.run(args, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    try:
        return p.returncode, json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return p.returncode, {"stderr": p.stderr[:400]}


def _write_pkg(target: str, deps: dict) -> None:
    with open(os.path.join(target, "package.json"), "w", encoding="utf-8") as fh:
        json.dump({"name": "fixture", "dependencies": deps}, fh)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    print("V-CDICF-SCOPE -- dependency-scope hard filter before the score\n")
    tmp = tempfile.mkdtemp(prefix="cdicf_scope_")
    try:
        # -- 01 composition preserved: no target => identical to score_review
        sr = score_review(SURFACE_82)
        gr = review_gate(SURFACE_82)
        if (gr.score == sr.score == 82 and gr.verdict == sr.verdict == "APPROVE"
                and gr.reason == sr.reason and gr.is_done == sr.is_done):
            _ok("V-CDICF-SCOPE-01-COMPOSITION",
                "a surface scoring 82 still scores 82 and still APPROVEs; "
                "review_gate with no target is score_review exactly")
        else:
            _fail("V-CDICF-SCOPE-01-COMPOSITION",
                  f"gate={gr.score}/{gr.verdict} vs score={sr.score}/{sr.verdict}")

        # -- 02 the section-5 threshold did not move
        if APPROVE_MIN == 80 and review_gate([_V("fail", "major")] * 3).verdict == "REVISE":
            _ok("V-CDICF-SCOPE-02-GATE-80",
                "APPROVE_MIN is still 80; a 76 still REVISEs")
        else:
            _fail("V-CDICF-SCOPE-02-GATE-80", f"APPROVE_MIN={APPROVE_MIN}")

        # -- 03 a project with no CDICF components is not penalised
        clean = os.path.join(tmp, "clean")
        os.makedirs(clean)
        gr = review_gate(SURFACE_82, target=clean)
        if gr.verdict == "APPROVE" and gr.score == 82 and gr.hard_filters[0]["passed"]:
            _ok("V-CDICF-SCOPE-03-NO-COMPONENTS",
                "no install record -> the filter passes and the score is untouched")
        else:
            _fail("V-CDICF-SCOPE-03-NO-COMPONENTS", f"{gr.verdict}/{gr.score}")

        # -- 04 a REAL install with the dependency declared: resolved, no impact
        good = os.path.join(tmp, "resolved")
        rc, out = _build(good, declare=True)
        gr = review_gate(SURFACE_82, target=good)
        if rc == 0 and out.get("ok") and gr.verdict == "APPROVE" and gr.score == 82:
            _ok("V-CDICF-SCOPE-04-RESOLVED-NO-IMPACT",
                f"real install of {out['component']} with {DEP} declared -> "
                f"score still 82, verdict still APPROVE")
        else:
            _fail("V-CDICF-SCOPE-04-RESOLVED-NO-IMPACT",
                  f"rc={rc} out={out} gate={gr.verdict}/{gr.score}")

        # -- 05 THE CASE THE INSTALLER CANNOT SEE: the dep is removed later.
        _write_pkg(good, {})
        gr = review_gate(SURFACE_82, target=good)
        hf = gr.hard_filters[0]
        if (gr.verdict == "BLOCK" and gr.score is None
                and not gr.reached_score and hf["state"] == DEP_UNRESOLVED
                and DEP in hf["observed"]):
            _ok("V-CDICF-SCOPE-05-REMOVED-AFTER-INSTALL",
                "a dependency removed AFTER a valid install blocks the review; "
                "the install-time check structurally cannot see this")
        else:
            _fail("V-CDICF-SCOPE-05-REMOVED-AFTER-INSTALL",
                  f"{gr.verdict}/{gr.score} state={hf.get('state')}")

        # -- 06 CRITICAL does not lower the number -- it prevents reaching one
        if gr.score is None and score_review(SURFACE_82).score == 82:
            _ok("V-CDICF-SCOPE-06-NOT-A-DEDUCTION",
                "blocked review has NO score (not 82-25=57); the same verdicts "
                "scored alone are still 82, so composition never moved")
        else:
            _fail("V-CDICF-SCOPE-06-NOT-A-DEDUCTION", f"score={gr.score}")

        # -- 07 the installer refuses the same condition at install time (11)
        missing = os.path.join(tmp, "unresolved")
        rc, out = _build(missing, declare=False)
        if rc == 11 and out.get("refusal", {}).get("code") == "UNRESOLVED_DEPENDENCIES":
            _ok("V-CDICF-SCOPE-07-INSTALLER-STILL-REFUSES",
                "install time exits 11; the two guards cover different moments, "
                "they are not redundant")
        else:
            _fail("V-CDICF-SCOPE-07-INSTALLER-STILL-REFUSES", f"rc={rc} out={out}")

        # -- 08 a record predating dependency tracking is unassessed, not a pass
        legacy = os.path.join(tmp, "legacy")
        os.makedirs(os.path.join(legacy, ".cdicf"))
        with open(os.path.join(legacy, ".cdicf", "installed.json"), "w",
                  encoding="utf-8") as fh:
            json.dump({"schema": "cdicf/installed/1",
                       "components": {"primitives/button": {"checksum": "x"}}}, fh)
        hf = check_component_dependencies(legacy)
        gr = review_gate(SURFACE_82, target=legacy)
        if (hf.state == DEP_UNASSESSED and hf.passed
                and "primitives/button" in hf.observed and gr.score == 82):
            _ok("V-CDICF-SCOPE-08-UNASSESSED-DISTINCT",
                "a legacy record is reported as unassessed and does not block -- "
                "blocking would inert the gate, passing silently would launder "
                "an unknown into a yes")
        else:
            _fail("V-CDICF-SCOPE-08-UNASSESSED-DISTINCT",
                  f"state={hf.state} passed={hf.passed}")

        # -- 09 an unresolved REGISTRY dependency blocks too
        reg = os.path.join(tmp, "registry")
        os.makedirs(os.path.join(reg, ".cdicf"))
        with open(os.path.join(reg, ".cdicf", "installed.json"), "w",
                  encoding="utf-8") as fh:
            json.dump({"schema": "cdicf/installed/1", "components": {
                "primitives/button": {"dependencies": {
                    "npm": [], "registry": ["primitives/icon"]}}}}, fh)
        gr = review_gate(SURFACE_82, target=reg)
        if gr.verdict == "BLOCK" and "primitives/icon" in gr.hard_filters[0]["observed"]:
            _ok("V-CDICF-SCOPE-09-REGISTRY-DEP",
                "a registry dependency absent from installed.json blocks by name")
        else:
            _fail("V-CDICF-SCOPE-09-REGISTRY-DEP", f"{gr.verdict}")

        # -- 10 a scoped package is not mistaken for a version specifier
        scoped = os.path.join(tmp, "scoped")
        os.makedirs(os.path.join(scoped, ".cdicf"))
        with open(os.path.join(scoped, ".cdicf", "installed.json"), "w",
                  encoding="utf-8") as fh:
            json.dump({"schema": "cdicf/installed/1", "components": {
                "primitives/button": {"dependencies": {
                    "npm": ["@radix-ui/react-slot@^1.2.0"], "registry": []}}}}, fh)
        _write_pkg(scoped, {"@radix-ui/react-slot": "^1.2.0"})
        hf = check_component_dependencies(scoped)
        if hf.passed:
            _ok("V-CDICF-SCOPE-10-SCOPE-NOT-EATEN",
                "'@radix-ui/react-slot@^1.2.0' resolves against the scoped name; "
                "the specifier is stripped and the scope is not")
        else:
            _fail("V-CDICF-SCOPE-10-SCOPE-NOT-EATEN", hf.observed)

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    total = PASSES + FAILS
    print(f"\nCDICF_SCOPE_PASS={PASSES}/{total}  threshold={total}/{total}")
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
