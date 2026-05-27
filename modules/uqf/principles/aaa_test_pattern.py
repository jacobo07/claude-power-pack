"""P08 -- AAA Test Pattern (Arrange-Act-Assert).

Source: ECC/Affaan Mustafa MIT
       (rules/common/testing.md "Test Structure (AAA Pattern)")

A test function follows AAA when its body has three distinct phases:
  Arrange: set up inputs / mocks / fixtures
  Act:     invoke the unit under test (the SINGLE operation tested)
  Assert:  verify the outcome (one or more asserts)

Heuristic detection (zero-dep, fast):
  - Function whose name starts with `test_` or matches `def test`
  - Body has >= 1 `assert` AND >= 2 statements before the first assert
    (those statements are the Arrange + Act phases combined)
  - OR contains comments `# Arrange` / `# Act` / `# Assert`
"""
import ast
from typing import Any

from modules.uqf.principles import Principle, PrincipleResult, register


class AAATestPattern(Principle):
    name = "aaa_test_pattern"
    description = (
        "Tests should follow Arrange-Act-Assert structure: setup, "
        "single operation, verification."
    )
    domains = ["tests"]
    source = "ECC/Affaan Mustafa MIT"

    def check(self, target: Any, domain: str) -> PrincipleResult:
        code = target if isinstance(target, str) else ""
        if not code.strip():
            return PrincipleResult(
                principle_name=self.name,
                domain=domain,
                passed=True,
                score=1.0,
                evidence="empty source -- nothing to check",
                fix_hint="",
                source=self.source,
            )

        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            return PrincipleResult(
                principle_name=self.name,
                domain=domain,
                passed=False,
                score=0.0,
                evidence=f"syntax error: {exc}",
                fix_hint="Fix the syntax error first",
                source=self.source,
            )

        tests_total = 0
        tests_aaa = 0
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            if not (node.name.startswith("test_") or
                    node.name == "test"):
                continue
            tests_total += 1

            body = node.body
            asserts = [n for n in body
                       if isinstance(n, ast.Assert) or
                       (isinstance(n, ast.Expr) and
                        isinstance(getattr(n, "value", None), ast.Call) and
                        isinstance(getattr(n.value.func, "attr", None),
                                   str) and
                        n.value.func.attr.startswith("assert"))]
            pre_first_assert = []
            for stmt in body:
                if isinstance(stmt, ast.Assert):
                    break
                pre_first_assert.append(stmt)

            has_aaa_comments = any(
                isinstance(s, ast.Expr) and
                isinstance(s.value, ast.Constant) and
                isinstance(s.value.value, str) and
                any(t in s.value.value.lower()
                    for t in ("arrange", "act", "assert"))
                for s in body
            )

            if (len(asserts) >= 1 and
                    (len(pre_first_assert) >= 2 or has_aaa_comments)):
                tests_aaa += 1

        if tests_total == 0:
            return PrincipleResult(
                principle_name=self.name,
                domain=domain,
                passed=True,
                score=1.0,
                evidence="no test functions detected",
                fix_hint="",
                source=self.source,
            )

        ratio = tests_aaa / tests_total
        passed = ratio >= 0.5
        return PrincipleResult(
            principle_name=self.name,
            domain=domain,
            passed=passed,
            score=ratio,
            evidence=f"{tests_aaa}/{tests_total} tests follow AAA",
            fix_hint=(
                "Structure each test as Arrange (setup), Act (one "
                "operation), Assert (verify). ECC rules/common/testing.md."
                if not passed else ""
            ),
            source=self.source,
        )


register(AAATestPattern())
