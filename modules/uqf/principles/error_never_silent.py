"""P06 -- Error Never Silent.

Source: ECC/Affaan Mustafa MIT
       (AGENTS.md "Error handling" -- "Never silently swallow errors")

Detects two Python anti-patterns via ast:
  1. bare `except:` without a specific exception type
  2. except handler whose body is just `pass` (silent swallow)

Both leak failures and break debugging. Real-world handlers must
either re-raise, log with context, or convert to a typed error.
"""
import ast
from typing import Any

from modules.uqf.principles import Principle, PrincipleResult, register


class ErrorNeverSilent(Principle):
    name = "error_never_silent"
    description = (
        "Detect bare except: and silent pass in except handlers. "
        "Real handlers re-raise, log, or convert -- never swallow."
    )
    domains = ["code"]
    source = "ECC/Affaan Mustafa MIT"

    def check(self, target: Any, domain: str) -> PrincipleResult:
        code = ""
        if isinstance(target, str):
            code = target
        elif hasattr(target, "read"):
            try:
                code = target.read()
            except OSError:
                code = ""

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
                fix_hint="Fix the syntax error before re-running the check",
                source=self.source,
            )

        violations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                # bare except
                if node.type is None:
                    violations.append(
                        f"line {node.lineno}: bare 'except:' "
                        f"(no exception type)"
                    )
                # body is only Pass or only Ellipsis
                if (len(node.body) == 1 and
                        isinstance(node.body[0],
                                   (ast.Pass, ast.Expr)) and
                        (isinstance(node.body[0], ast.Pass) or
                         (isinstance(node.body[0].value, ast.Constant) and
                          node.body[0].value.value is Ellipsis))):
                    violations.append(
                        f"line {node.lineno}: silent except body (pass/...)"
                    )

        if not violations:
            return PrincipleResult(
                principle_name=self.name,
                domain=domain,
                passed=True,
                score=1.0,
                evidence=f"{len(code)} chars scanned, no silent errors",
                fix_hint="",
                source=self.source,
            )

        return PrincipleResult(
            principle_name=self.name,
            domain=domain,
            passed=False,
            score=0.0,
            evidence=f"{len(violations)} violations: {violations[:3]}",
            fix_hint=(
                "Replace bare except with specific exception types; "
                "replace 'pass' with re-raise, log+context, or "
                "explicit error conversion."
            ),
            source=self.source,
        )


register(ErrorNeverSilent())
