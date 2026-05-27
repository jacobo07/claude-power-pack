"""P02 -- Zero Findings Is Valid.

Source: ECC/Affaan Mustafa MIT
       (agents/code-reviewer.md "It Is Acceptable And Expected To Return
        Zero Findings" section)

A clean code review is a valid code review. LLM reviewers commonly
manufacture findings to "justify the invocation"; this is the #1
failure mode of agentic review. This principle scans a findings list
and detects:
  - Empty list: PASS (clean review is valid)
  - All findings have evidence (snippet OR file:line): PASS
  - Findings without evidence: degraded score (theater suspected)
"""
from typing import Any

from modules.uqf.principles import Principle, PrincipleResult, register


class ZeroFindingsValid(Principle):
    name = "zero_findings_valid"
    description = (
        "A clean review (zero findings) is a valid review. Findings "
        "must have concrete evidence (snippet or file:line) to count "
        "as real."
    )
    domains = ["code", "prompts"]
    source = "ECC/Affaan Mustafa MIT"

    def check(self, target: Any, domain: str) -> PrincipleResult:
        if not isinstance(target, list):
            return PrincipleResult(
                principle_name=self.name,
                domain=domain,
                passed=False,
                score=0.0,
                evidence=f"target not a list (got {type(target).__name__})",
                fix_hint="Pass a list of finding dicts",
                source=self.source,
            )

        if len(target) == 0:
            return PrincipleResult(
                principle_name=self.name,
                domain=domain,
                passed=True,
                score=1.0,
                evidence="0 findings -- clean review accepted",
                fix_hint="",
                source=self.source,
            )

        without_evidence = 0
        for f in target:
            if not isinstance(f, dict):
                without_evidence += 1
                continue
            has_snippet = bool(f.get("snippet"))
            has_line = bool(f.get("line"))
            has_file = bool(f.get("file"))
            if not (has_snippet or (has_file and has_line)):
                without_evidence += 1

        if without_evidence == 0:
            return PrincipleResult(
                principle_name=self.name,
                domain=domain,
                passed=True,
                score=1.0,
                evidence=f"{len(target)} findings all with evidence",
                fix_hint="",
                source=self.source,
            )

        evidence_ratio = (len(target) - without_evidence) / len(target)
        return PrincipleResult(
            principle_name=self.name,
            domain=domain,
            passed=False,
            score=evidence_ratio,
            evidence=(
                f"{without_evidence}/{len(target)} findings missing "
                f"snippet or file:line"
            ),
            fix_hint=(
                "Drop findings without evidence or add snippet+line. "
                "ECC doctrine: theater is the failure mode."
            ),
            source=self.source,
        )


register(ZeroFindingsValid())
