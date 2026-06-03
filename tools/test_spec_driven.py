#!/usr/bin/env python3
"""test_spec_driven.py -- V-gates for spec-driven-auto + root-cause fixes.

Exercises the spec domain (skill_router), the spec gate, the premise
verifier, and cross-repo activation. V-gate convention per
rules/python/testing.md. Exit 0 iff all gates pass.

Gates:
  V-SPEC-DOMAIN-INDEX  >=1 spec-domain skill in the index
  V-SPEC-INTENT-LARGE  "build a complete ..." -> spec domain
  V-SPEC-INTENT-SMALL  "fix the typo ..."     -> NOT spec domain
  V-SPEC-GATE-L-NOSPEC L task in an empty cwd -> gate_passed=False
  V-SPEC-GATE-S        S task                 -> gate_passed=True
  V-PREMISE-FILE-TRUE  existing file          -> verified=True
  V-PREMISE-FILE-FALSE missing file           -> verified=False
  V-PREMISE-FN-TRUE    existing function       -> verified=True
  V-PREMISE-FN-FALSE   nonexistent function    -> verified=False + fix
  V-CROSS-REPO         build_index from a foreign cwd -> >=1 skill
  V-BASELINE-INTACT    the sleepy frontend suite still passes (no regress)
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS  {gate:<24} {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL  {gate:<24} {diag}")


def _check(gate: str, cond: bool, ev_ok: str, ev_fail: str) -> None:
    _ok(gate, ev_ok) if cond else _fail(gate, ev_fail)


def main() -> int:
    from modules.error_prevention.premise_verifier import verify_premises
    from modules.skill_router.intent_classifier import classify_intent
    from modules.skill_router.skill_index import build_index
    from modules.spec_gate.gate import check_spec_gate

    skills = build_index(force=True)

    spec = [s for s in skills if s.domain == "spec"]
    _check("V-SPEC-DOMAIN-INDEX", len(spec) >= 1,
           f"{len(spec)} spec skills", "no spec-domain skills")

    r = classify_intent("build a complete user auth system", skills)
    _check("V-SPEC-INTENT-LARGE", r.domain == "spec",
           f"domain={r.domain} conf={r.confidence:.2f}",
           f"domain={r.domain}")

    r = classify_intent("fix the typo in the readme", skills)
    _check("V-SPEC-INTENT-SMALL", r.domain != "spec",
           "did not trip spec", f"tripped spec (domain={r.domain})")

    empty = Path(tempfile.mkdtemp(prefix="spec_vg_"))
    g = check_spec_gate("Implement complete auth", cwd=empty, task_size="L")
    _check("V-SPEC-GATE-L-NOSPEC", (not g.gate_passed)
           and g.action == "create_spec",
           f"action={g.action}", "gate passed unexpectedly")

    g = check_spec_gate("Fix typo", task_size="S")
    _check("V-SPEC-GATE-S", g.gate_passed,
           "S always proceeds", "S task blocked")

    r = verify_premises([{"type": "file_exists",
                          "path": "tools/jit_skill_loader.py"}])
    _check("V-PREMISE-FILE-TRUE", r[0].verified,
           "existing file verified", r[0].evidence)

    r = verify_premises([{"type": "file_exists",
                          "path": "tools/does_not_exist_zzz.py"}])
    _check("V-PREMISE-FILE-FALSE", not r[0].verified,
           "absence detected", "false positive on missing file")

    r = verify_premises([{"type": "function_exists",
                          "module": "modules.one_shot.compiler",
                          "function": "compile_contract"}])
    _check("V-PREMISE-FN-TRUE", r[0].verified,
           "existing function verified", r[0].evidence)

    r = verify_premises([{"type": "function_exists",
                          "module": "modules.one_shot.compiler",
                          "function": "nope_zzz_fn"}])
    _check("V-PREMISE-FN-FALSE", (not r[0].verified)
           and bool(r[0].correction),
           "absence + correction emitted", "no correction emitted")

    foreign = tempfile.mkdtemp(prefix="foreign_repo_")
    code = ("import sys; sys.path.insert(0, r'%s'); "
            "from modules.skill_router.skill_index import build_index; "
            "print(len(build_index()))") % str(PP)
    cp = subprocess.run([sys.executable, "-c", code], cwd=foreign,
                        capture_output=True, text=True, timeout=30)
    n = cp.stdout.strip()
    _check("V-CROSS-REPO",
           cp.returncode == 0 and n.isdigit() and int(n) >= 1,
           f"{n} skills from foreign cwd",
           (cp.stderr.strip()[:60] or "no skills"))

    cp = subprocess.run(
        [sys.executable, str(PP / "tools" / "test_sleepy_skills.py")],
        capture_output=True, text=True, timeout=60)
    _check("V-BASELINE-INTACT", cp.returncode == 0,
           "sleepy frontend suite intact", "sleepy suite regressed")

    total = _passes + _fails
    print(f"SPEC_DRIVEN_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
