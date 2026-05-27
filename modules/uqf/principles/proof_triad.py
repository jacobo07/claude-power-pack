"""P04 -- HIGH/CRITICAL Proof Triad.

Source: ECC/Affaan Mustafa MIT
       (agents/code-reviewer.md "HIGH / CRITICAL Require Proof" section)

For any finding tagged HIGH or CRITICAL, the reviewer must include:

  1. The exact snippet and line number
  2. The specific failure scenario (input + state + outcome)
  3. Why existing guards (types, validation, framework defaults)
     do NOT catch it

Without all three, the finding must be demoted to MEDIUM or dropped.
LOW/MEDIUM findings have no proof triad requirement.
"""
from typing import Any

from modules.uqf.principles import Principle, PrincipleResult, register


class HighCriticalProofTriad(Principle):
    name = "high_critical_proof_triad"
    description = (
        "HIGH/CRITICAL findings require snippet + scenario + "
        "why-guards-fail. Otherwise demote or drop."
    )
    domains = ["code"]
    source = "ECC/Affaan Mustafa MIT"

    HIGH_CRITICAL = {"HIGH", "CRITICAL"}

    def check(self, target: Any, domain: str) -> PrincipleResult:
        if not isinstance(target, dict):
            return PrincipleResult(
                principle_name=self.name,
                domain=domain,
                passed=False,
                score=0.0,
                evidence=f"target not a dict (got {type(target).__name__})",
                fix_hint="Pass a finding dict with severity field",
                source=self.source,
            )

        severity = str(target.get("severity", "")).upper()
        if severity not in self.HIGH_CRITICAL:
            return PrincipleResult(
                principle_name=self.name,
                domain=domain,
                passed=True,
                score=1.0,
                evidence=f"severity={severity!r} -- triad not required",
                fix_hint="",
                source=self.source,
            )

        has_snippet = bool(target.get("snippet"))
        has_scenario = bool(target.get("scenario") or
                            target.get("failure_mode"))
        has_why_guards = bool(target.get("why_guards_fail") or
                              target.get("why_guards"))

        present = sum([has_snippet, has_scenario, has_why_guards])
        if present == 3:
            return PrincipleResult(
                principle_name=self.name,
                domain=domain,
                passed=True,
                score=1.0,
                evidence=f"{severity}: full triad present",
                fix_hint="",
                source=self.source,
            )

        missing = []
        if not has_snippet:
            missing.append("snippet")
        if not has_scenario:
            missing.append("scenario/failure_mode")
        if not has_why_guards:
            missing.append("why_guards_fail")

        return PrincipleResult(
            principle_name=self.name,
            domain=domain,
            passed=False,
            score=present / 3.0,
            evidence=(
                f"{severity}: missing triad piece(s): {missing}"
            ),
            fix_hint=(
                f"Add missing pieces OR demote severity to MEDIUM. "
                f"ECC doctrine: severity inflation erodes trust faster "
                f"than missed findings."
            ),
            source=self.source,
        )


register(HighCriticalProofTriad())
