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
                    f"{len(sources)} source file(s), "
                    f"{len(tests)} test file(s) in change set"
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


register(TDDWorkflow())
