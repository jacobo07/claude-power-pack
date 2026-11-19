"""P07 -- TDD Workflow.

Source: ECC/Affaan Mustafa MIT
       (AGENTS.md "Testing Requirements" + rules/common/testing.md
        + agents/tdd-guide.md)

ECC mandates RED -> GREEN -> REFACTOR. For a commit/change set, the
heuristic check is: every new source file should have a corresponding
test file. The principle accepts either:
  - target: list of file paths in a change set
  - target: dict {sources: [...], tests: [...]}

A target of just one source file with no tests fails this principle
(reviewer should flag "Add a test or document why TDD is skipped").
"""
import os
from typing import Any

from modules.uqf.principles import Principle, PrincipleResult, register


class TDDWorkflow(Principle):
    name = "tdd_workflow"
    description = (
        "Every new source file should have a corresponding test file. "
        "If tests are missing, the change set must justify why."
    )
    domains = ["code", "tests"]
    source = "ECC/Affaan Mustafa MIT"

    SOURCE_EXTS = (".py", ".js", ".ts", ".rs", ".go", ".ex", ".exs")
    TEST_PATTERNS = ("test_", "_test.", ".test.", "spec_", "_spec.",
                     ".spec.")

    @classmethod
    def _is_test_path(cls, path: str) -> bool:
        base = os.path.basename(path).lower()
        if any(base.startswith(p) or p in base for p in cls.TEST_PATTERNS):
            return True
        return "/tests/" in path.replace("\\", "/").lower()

    @classmethod
    def _is_source_path(cls, path: str) -> bool:
        if cls._is_test_path(path):
            return False
        return path.lower().endswith(cls.SOURCE_EXTS)

    def check(self, target: Any, domain: str) -> PrincipleResult:
        sources: list[str] = []
        tests: list[str] = []

        if isinstance(target, dict):
            sources = list(target.get("sources", []))
            tests = list(target.get("tests", []))
        elif isinstance(target, list):
            for p in target:
                if not isinstance(p, str):
                    continue
                if self._is_test_path(p):
                    tests.append(p)
                elif self._is_source_path(p):
                    sources.append(p)
        else:
            return PrincipleResult(
                principle_name=self.name,
                domain=domain,
                passed=False,
                score=0.0,
                evidence=f"target type {type(target).__name__} not supported",
                fix_hint="Pass list[str] of paths or {sources, tests} dict",
                source=self.source,
            )

        if not sources:
            return PrincipleResult(
                principle_name=self.name,
                domain=domain,
                passed=True,
                score=1.0,
                evidence="no source files in change set",
                fix_hint="",
                source=self.source,
            )

        if tests:
            return PrincipleResult(
                principle_name=self.name,
                domain=domain,
                passed=True,
                score=1.0,
                evidence=(
                    f"HEURISTIC_ONLY: {len(sources)} source file(s), "
                    f"{len(tests)} test file(s) in change set "
                    "(file presence; not RED evidence -- see classify_slice)"
                ),
                fix_hint="",
                source=self.source,
            )

        return PrincipleResult(
            principle_name=self.name,
            domain=domain,
            passed=False,
            score=0.0,
            evidence=(
                f"{len(sources)} source file(s) but ZERO test files: "
                f"{sources[:3]}"
            ),
            fix_hint=(
                "Add a test file (RED) before/with the source. "
                "ECC TDD workflow: RED -> GREEN -> REFACTOR is "
                "mandatory, not advisory."
            ),
            source=self.source,
        )


# ---------------------------------------------------------------------------
# CPP-TDD-001: evidence-aware classification (BCAP-2 Phase 2).
# classify_slice judges a RECORD of observed facts; it runs nothing itself.
# Stage facts are mapped onto modules.done_gate.strength_ladder keys -- there
# is no competing completion enum. File presence stays the weaker signal above.
# ---------------------------------------------------------------------------
INVALID_RED_REASONS = frozenset(
    {"import", "syntax", "fixture", "env", "unrelated", "baseline_broken"})
VALID_RED_REASONS = frozenset({"assertion", "missing_behavior"})
MUTATION_OUTCOMES = ("KILLED", "SURVIVED", "UNMEASURABLE", "TIMEOUT",
                     "ERROR", "NOT_RUN")
MUTATION_LANGUAGES = frozenset({"python"})  # tools/test_gaps.py is pytest-only
_LADDER_WIRING = ("has_caller", "reachable_from_entrypoint",
                  "activation_path_exists")


def mutation_outcome(gaps_result: dict) -> str:
    """Map a tools/test_gaps.analyse() result onto the C5 vocabulary.

    Reuse of the existing mutator's verdicts; nothing is collapsed into PASS.
    Precedence is worst-first so a survivor can never hide behind a kill.
    """
    if not isinstance(gaps_result, dict):
        return "ERROR"
    if gaps_result.get("verdict") in ("UNMEASURABLE", "NO_CHANGES"):
        return "UNMEASURABLE" if gaps_result["verdict"] == "UNMEASURABLE" else "NOT_RUN"
    for key, name in (("errors", "ERROR"), ("timeout", "TIMEOUT"),
                      ("survived", "SURVIVED")):
        if gaps_result.get(key):
            return name
    return "KILLED" if gaps_result.get("killed") else "NOT_RUN"


def _applicability(rec: dict) -> tuple[str, str]:
    kind = rec.get("kind", "unknown")
    if kind == "docs_only":
        return "NOT_APPLICABLE", "documentation-only change"
    if kind == "pure_refactor":
        if rec.get("prior_passing_baseline") is True:
            return "NOT_APPLICABLE", "pure refactor under an observed passing baseline"
        return "UNRESOLVED", "pure refactor claimed without an observed passing baseline"
    if kind in ("legacy", "exploratory", "integration", "runtime_dependent"):
        return "CONDITIONAL", f"{kind} work needs characterization/alternative evidence"
    if kind == "behavior_change":
        if rec.get("seam") is False:
            return "UNRESOLVED", "no testable seam"
        return "APPLICABLE", "new or modified behavior"
    return "UNRESOLVED", f"unclassified kind {kind!r}"


def tautological_asserts(src: str) -> list[int]:
    """Line numbers of `assert call(...) == expected` where expected is recomputed, not stated.

    Refused: both sides structurally identical, or the non-call side contains no literal and is itself a
    computation (BinOp/Call) over names -- `assert add(a, b) == a + b`. Accepted: any literal on the expected
    side (`== 5`, `== [1, 2]`). Static heuristic; an unparseable source returns [] (absent is not clean:
    callers treat the oracle declaration as the authority then).
    """
    import ast
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    hits: list[int] = []
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Assert) and isinstance(n.test, ast.Compare)
                and len(n.test.ops) == 1 and isinstance(n.test.ops[0], ast.Eq)):
            continue
        l, r = n.test.left, n.test.comparators[0]
        if ast.dump(l) == ast.dump(r):
            hits.append(n.lineno)
            continue
        for call, exp in ((l, r), (r, l)):
            if isinstance(call, ast.Call) and isinstance(exp, (ast.BinOp, ast.Call)) \
                    and not any(isinstance(x, ast.Constant) for x in ast.walk(exp)):
                hits.append(n.lineno)
                break
    return hits


def _slice_facts(sl: dict, rec: dict, codes: list[str]) -> dict:
    ac = sl.get("acceptance_id")
    red = sl.get("red") or {}
    oracle = (sl.get("oracle") or {}).get("kind")
    green = sl.get("green") or {}
    red_ok = False
    if sl.get("worktree") != rec.get("worktree") or not sl.get("worktree"):
        codes.append(f"MISATTRIBUTED_WORKTREE:{ac}")
    elif not red.get("observed"):
        codes.append(f"RED_ABSENT:{ac}")
    elif red.get("test_before_impl") is not True:
        codes.append(f"POST_HOC_TEST:{ac}")
    elif red.get("reason") in INVALID_RED_REASONS:
        codes.append(f"INVALID_RED:{ac}:{red.get('reason')}")
    elif red.get("reason") not in VALID_RED_REASONS:
        codes.append(f"RED_REASON_UNCLASSIFIED:{ac}")
    elif not (red.get("test_rev") and red.get("runner")):
        codes.append(f"RED_PROVENANCE_MISSING:{ac}")
    else:
        red_ok = True
    if oracle == "independent" and (sl.get("oracle") or {}).get("source"):
        oracle_ok = True
    else:
        oracle_ok = False
        codes.append(("ORACLE_NOT_INDEPENDENT:" if oracle == "copied_from_impl"
                      else "ORACLE_UNRESOLVED:") + str(ac))
    if sl.get("test_source") and tautological_asserts(sl["test_source"]):
        oracle_ok = False
        codes.append(f"TAUTOLOGICAL_ASSERTION:{ac}")
    red_ok = red_ok and oracle_ok  # a self-fulfilling RED never credits
    green_ok = bool(red_ok and green.get("observed") and green.get("targeted_passed"))
    if red_ok and not green_ok:
        codes.append(f"GREEN_ABSENT:{ac}")
    ref = sl.get("refactor") or {}
    ref_ok = (not ref.get("applied")) or bool(ref.get("behavior_preserved"))
    if ref.get("applied") and not ref_ok:
        codes.append(f"REFACTOR_BROKE_BEHAVIOR:{ac}")
    mut = (sl.get("mutation") or {}).get("outcome")
    if mut is not None and mut not in MUTATION_OUTCOMES:
        codes.append(f"MUTATION_OUTCOME_UNKNOWN:{ac}")
        mut = "ERROR"
    if mut == "SURVIVED":
        codes.append(f"SURVIVOR_VISIBLE:{ac}")
    elif mut in ("UNMEASURABLE", "TIMEOUT", "ERROR"):
        codes.append(f"MUTATION_{mut}:{ac}")
    integ = sl.get("integration") or {}
    if integ.get("observed") and integ.get("state_valid") is not True:
        codes.append(f"INTEGRATION_INVALID_STATE:{ac}")
    return {"acceptance_id": ac, "red_ok": red_ok, "green_ok": green_ok,
            "refactor_ok": ref_ok and green_ok, "mutation": mut or "NOT_RUN",
            "survivor_unresolved": mut == "SURVIVED" and not (sl.get("mutation") or {}).get("disposition"),
            "integration": integ.get("state_valid") if integ.get("observed") else None}


def classify_slice(rec: dict) -> dict:
    """Judge a TDD evidence record. Stage facts, never a new completion enum.

    status is one of RED_VERIFIED / GREEN_VERIFIED / REFACTOR_VERIFIED /
    BEHAVIOR_VERIFIED / EVIDENCE_INCOMPLETE / BLOCKED / EXEMPT_SCOPED;
    ``certifies_tdd`` is True only for a status that observed RED then GREEN.
    """
    if not isinstance(rec, dict):
        return {"status": "EVIDENCE_INCOMPLETE", "certifies_tdd": False,
                "codes": ["RECORD_NOT_A_DICT"], "applicability": "UNRESOLVED"}
    codes: list[str] = []
    appl, why = _applicability(rec)
    sources, tests = rec.get("sources", []), rec.get("tests", [])
    heur = TDDWorkflow().check({"sources": sources, "tests": tests}, "code")
    out: dict = {"applicability": appl, "applicability_reason": why,
                 "heuristic": {"label": "HEURISTIC_ONLY", "passed": heur.passed},
                 "codes": codes, "slices": [], "certifies_tdd": False,
                 "ladder": None, "ladder_unknown": []}
    env = rec.get("environment") or {}
    if env.get("hook_event_lost") or (env.get("orphan_pids") or 0) > 0:
        codes.append("ENVIRONMENT_BLOCKED")
        out["status"] = "BLOCKED"
        return out
    if appl == "NOT_APPLICABLE":
        out["status"] = "EXEMPT_SCOPED"
        return out
    if appl in ("UNRESOLVED", "CONDITIONAL"):
        alt = rec.get("alternative_evidence")
        codes.append(f"APPLICABILITY_{appl}")
        if appl == "CONDITIONAL" and alt:
            out["status"] = "EXEMPT_SCOPED"
            out["alternative_evidence"] = alt
        else:
            out["status"] = "EVIDENCE_INCOMPLETE"
        return out

    required = list(rec.get("required_acceptance_ids") or [])
    baseline = set(rec.get("baseline_acceptance_ids") or [])
    if baseline - set(required):
        codes.append("RATCHET_ACCEPTANCE_DROPPED:" + ",".join(sorted(baseline - set(required))))
    facts = [_slice_facts(s, rec, codes) for s in (rec.get("slices") or [])]
    out["slices"] = facts
    if not facts:
        codes.append("NO_SLICE_EVIDENCE")
    covered = {f["acceptance_id"] for f in facts if f["green_ok"]}
    missing = [a for a in (sorted(baseline | set(required))) if a not in covered]
    if missing and facts:
        codes.append("ACCEPTANCE_UNOBSERVED:" + ",".join(missing))
    lang = rec.get("language", "python")
    if lang not in MUTATION_LANGUAGES:
        codes.append(f"MUTATION_UNSUPPORTED_LANGUAGE:{lang}")
    all_red = bool(facts) and all(f["red_ok"] for f in facts)
    all_green = all_red and all(f["green_ok"] for f in facts)
    all_ref = all_green and all(f["refactor_ok"] for f in facts)
    pinned = all_green and all(f["mutation"] == "KILLED" for f in facts)
    integ = [f["integration"] for f in facts]
    integ_ev = None if (not facts or any(i is None for i in integ)) else all(integ)
    blocked = (bool(missing) or any(f["survivor_unresolved"] for f in facts)
               or any(c.startswith(("RATCHET", "INTEGRATION_INVALID", "REFACTOR_BROKE")) for c in codes))
    out["certifies_tdd"] = all_green and not blocked
    # strength_ladder evidence: True / False / absent (None = nobody looked).
    ev = {"spec_exists": bool(required) or None,
          "artifact_on_disk": bool(sources) or None,
          "ran_at_least_once": True if any(
              (s.get("red") or {}).get("observed") for s in rec.get("slices") or []) else None,
          "assertions_observed": all_green if facts else None,
          "integration_boundary_exercised": integ_ev,
          "failure_branch_driven": all_red if facts else None,
          "regression_case_pinned": True if pinned else (False if facts and any(
              f["mutation"] == "SURVIVED" for f in facts) else None)}
    for k in _LADDER_WIRING:
        v = (rec.get("wiring") or {}).get(k)
        ev[k] = v if isinstance(v, bool) else None
    from modules.done_gate.strength_ladder import highest_supported
    if lang not in MUTATION_LANGUAGES:
        ev["regression_case_pinned"] = None  # unsupported: a ceiling, not a verdict
    out["ladder_evidence"] = ev
    out["ladder"], out["ladder_unknown"] = highest_supported(
        {k: v for k, v in ev.items() if v is not None})
    if not facts or missing or blocked or not all_red:
        out["status"] = "EVIDENCE_INCOMPLETE"
    elif not all_green:
        out["status"] = "RED_VERIFIED"
    elif not all_ref:
        out["status"] = "GREEN_VERIFIED"
    elif integ_ev is True and not missing and baseline | set(required):
        out["status"] = "BEHAVIOR_VERIFIED"
    elif any((s.get("refactor") or {}).get("applied") for s in rec.get("slices") or []):
        out["status"] = "REFACTOR_VERIFIED"
    else:
        out["status"] = "GREEN_VERIFIED"
    return out


register(TDDWorkflow())


if __name__ == "__main__":  # python3 -m modules.uqf.principles.tdd_workflow <record.json>
    import json
    import sys
    if len(sys.argv) != 2:
        sys.exit("usage: python3 -m modules.uqf.principles.tdd_workflow <record.json>")
    with open(sys.argv[1], encoding="utf-8") as fh:
        res = classify_slice(json.load(fh))
    print(json.dumps(res, indent=2))
    sys.exit(0 if res["certifies_tdd"] or res["status"] == "EXEMPT_SCOPED" else 1)
