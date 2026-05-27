"""P01 -- Pre-Report Gate for code-reviewer findings.

Source: ECC/Affaan Mustafa MIT
       (agents/code-reviewer.md "Pre-Report Gate" section)

Before any code-review finding is emitted, the reviewer must
answer four questions affirmatively:

  1. Can I cite the exact line?  (file:line precision)
  2. Can I describe the concrete failure mode?  (input/state/outcome)
  3. Have I read the surrounding context?  (callers, imports, tests)
  4. Is the severity defensible?  (no inflation)

If any answer is no/unsure, the finding must be downgraded or dropped.
This principle codifies the gate as a binary check on a finding dict.
"""
from typing import Any

from modules.uqf.principles import Principle, PrincipleResult, register


class PreReportGate(Principle):
    name = "pre_report_gate"
    description = (
        "Every code-review finding must answer 4 questions before "
        "being reported: exact line, concrete failure mode, "
        "surrounding context read, severity defensible."
    )
    domains = ["code", "prompts"]
    source = "ECC/Affaan Mustafa MIT"

    REQUIRED_KEYS = (
        "line",
        "failure_mode",
        "surrounding_context",
        "severity_defensible",
    )

    def check(self, target: Any, domain: str) -> PrincipleResult:
        if not isinstance(target, dict):
            return PrincipleResult(
                principle_name=self.name,
                domain=domain,
                passed=False,
                score=0.0,
                evidence=f"target not a dict (got {type(target).__name__})",
                fix_hint=(
                    "Pass a finding dict with keys: "
                    + ", ".join(self.REQUIRED_KEYS)
                ),
                source=self.source,
            )

        missing = []
        for k in self.REQUIRED_KEYS:
            v = target.get(k)
            if v is None or v == "" or v is False:
                missing.append(k)

        if not missing:
            return PrincipleResult(
                principle_name=self.name,
                domain=domain,
                passed=True,
                score=1.0,
                evidence=f"finding has all 4 gate keys",
                fix_hint="",
                source=self.source,
            )

        return PrincipleResult(
            principle_name=self.name,
            domain=domain,
            passed=False,
            score=max(0.0, (4 - len(missing)) / 4),
            evidence=f"missing gate keys: {missing}",
            fix_hint=(
                "Fill in the missing keys or drop the finding. "
                "ECC doctrine: a finding without the 4-question gate "
                "is review theater."
            ),
            source=self.source,
        )


register(PreReportGate())
