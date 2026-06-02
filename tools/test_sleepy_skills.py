#!/usr/bin/env python3
"""test_sleepy_skills.py -- V-gates for the Sleepy Skills frontend pilot.

Exercises skill_index (catalog), intent_classifier (wakeup/sleep logic),
and the LIVE JIT-loader wiring (_skill_router_inject decorator on run()).
V-gate convention per rules/python/testing.md. Exit 0 iff all gates pass.

Gates:
  V-SKILL-INDEX-BUILDS  build_index() catalogs >=1 skill (real, on disk)
  V-SKILL-FRONTEND      get_frontend_skills() returns >=1
  V-INTENT-WAKEUP       React+Tailwind prompt -> wakeup + >=1 skill
  V-INTENT-SLEEP        JWT/API backend prompt -> no wakeup (negative veto)
  V-INTENT-CTX-FORCE    context_pct=0.8 -> forced sleep regardless of intent
  V-INTENT-ACCURACY     >=5/6 of the pilot prompt set classified correctly
  V-JIT-INTEGRATION     run() injects the card on FE, stays clean on BE
  V-BASELINE-INTACT     run() on a neutral prompt -> continue:true, no crash
"""
from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))
sys.path.insert(0, str(PP / "tools"))

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS  {gate:<26} {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL  {gate:<26} {diag}")


def main() -> int:
    from modules.skill_router.skill_index import (
        build_index, get_frontend_skills)
    from modules.skill_router.intent_classifier import classify_intent

    # V-SKILL-INDEX-BUILDS
    all_skills = build_index(force=True)
    if len(all_skills) >= 1:
        _ok("V-SKILL-INDEX-BUILDS", f"{len(all_skills)} skills indexed")
    else:
        _fail("V-SKILL-INDEX-BUILDS", "0 skills indexed")

    # V-SKILL-FRONTEND
    frontend = get_frontend_skills()
    if len(frontend) >= 1:
        _ok("V-SKILL-FRONTEND", f"{len(frontend)} frontend skills")
    else:
        _fail("V-SKILL-FRONTEND", "0 frontend skills")

    # V-INTENT-WAKEUP
    r = classify_intent(
        "create a React component with Tailwind for a dashboard", all_skills)
    if r.should_wakeup and r.matching_skills:
        _ok("V-INTENT-WAKEUP",
            f"conf={r.confidence:.2f} -> {[s.name for s in r.matching_skills]}")
    else:
        _fail("V-INTENT-WAKEUP", f"did not wake (conf={r.confidence:.2f})")

    # V-INTENT-SLEEP
    r = classify_intent(
        "fix the JWT authentication bug in the API", all_skills)
    if not r.should_wakeup:
        _ok("V-INTENT-SLEEP", f"slept (domain={r.domain})")
    else:
        _fail("V-INTENT-SLEEP", "woke on a backend prompt")

    # V-INTENT-CTX-FORCE
    r = classify_intent("create a React component", all_skills,
                        context_pct=0.8)
    if not r.should_wakeup:
        _ok("V-INTENT-CTX-FORCE", "context 0.8 -> forced sleep")
    else:
        _fail("V-INTENT-CTX-FORCE", "woke at 80% context")

    # V-INTENT-ACCURACY
    cases = [
        ("Create a React component with shadcn/ui", True),
        ("Build a Tailwind landing page", True),
        ("Fix the database query performance", False),
        ("Add a button to the form", True),
        ("Deploy the API to production", False),
        ("Write a TypeScript interface", False),
    ]
    correct = sum(1 for p, exp in cases
                  if classify_intent(p, all_skills).should_wakeup == exp)
    if correct >= 5:
        _ok("V-INTENT-ACCURACY", f"{correct}/{len(cases)} correct")
    else:
        _fail("V-INTENT-ACCURACY", f"only {correct}/{len(cases)} correct")

    # V-JIT-INTEGRATION (live wiring through run())
    import jit_skill_loader as j
    tmp = tempfile.mkdtemp(prefix="sleepy_vgate_")  # empty cwd: no Apollo/spec
    sfx = str(int(time.time() * 1000))
    fe_ac = j.run({"prompt": "build me a Tailwind landing page",
                   "cwd": tmp,
                   "session_id": f"vg-fe-{sfx}"}).get("additionalContext", "")
    be_ac = j.run({"prompt": "fix the JWT auth bug in the API",
                   "cwd": tmp,
                   "session_id": f"vg-be-{sfx}"}).get("additionalContext", "")
    if "[sleepy-skill]" in fe_ac and "[sleepy-skill]" not in be_ac:
        _ok("V-JIT-INTEGRATION", "FE card injected; BE clean")
    else:
        _fail("V-JIT-INTEGRATION",
              f"fe_card={'[sleepy-skill]' in fe_ac} "
              f"be_card={'[sleepy-skill]' in be_ac}")

    # V-BASELINE-INTACT (loader still fail-open / unchanged on neutral input)
    neutral = j.run({"prompt": "hola", "cwd": tmp,
                     "session_id": f"vg-n-{sfx}"})
    if isinstance(neutral, dict) and neutral.get("continue") is True:
        _ok("V-BASELINE-INTACT", "neutral prompt -> continue:true, no crash")
    else:
        _fail("V-BASELINE-INTACT", f"unexpected result: {neutral!r}")

    total = _passes + _fails
    print(f"SLEEPY_SKILLS_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
