"""P05 -- Severity Table Output Format.

Source: ECC/Affaan Mustafa MIT
       (agents/code-reviewer.md "Review Output Format" /
        "Summary Format" / "Approval Criteria")

Every code review ends with a severity table:
  CRITICAL=N  HIGH=N  MEDIUM=N  LOW=N
plus a verdict:
  APPROVE / WARNING / BLOCK

Mapping:
  CRITICAL > 0  -> BLOCK
  HIGH > 0      -> WARNING (no CRITICAL)
  otherwise     -> APPROVE
"""
from typing import Any

from modules.uqf.principles import Principle, PrincipleResult, register


class SeverityTableOutput(Principle):
    name = "severity_table_output"
    description = (
        "Code-review output must include CRITICAL/HIGH/MEDIUM/LOW "
        "counts + verdict (APPROVE/WARNING/BLOCK), verdict consistent "
        "with the counts."
    )
    domains = ["code"]
    source = "ECC/Affaan Mustafa MIT"

    VALID_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
    VALID_VERDICTS = {"APPROVE", "WARNING", "BLOCK"}

    @classmethod
    def derive_verdict(cls, counts: dict) -> str:
        """Compute the verdict from severity counts."""
        if counts.get("CRITICAL", 0) > 0:
            return "BLOCK"
        if counts.get("HIGH", 0) > 0:
            return "WARNING"
        return "APPROVE"

    def check(self, target: Any, domain: str) -> PrincipleResult:
        if not isinstance(target, dict):
            return PrincipleResult(
                principle_name=self.name,
                domain=domain,
                passed=False,
                score=0.0,
                evidence=f"target not a dict (got {type(target).__name__})",
                fix_hint=(
                    "Pass a dict: {findings: list, verdict: str} "
                    "or {counts: dict, verdict: str}"
                ),
                source=self.source,
            )

        # Accept either a findings list or a precomputed counts dict.
        findings = target.get("findings")
        counts = target.get("counts")
        if counts is None:
            if not isinstance(findings, list):
                return PrincipleResult(
                    principle_name=self.name,
                    domain=domain,
                    passed=False,
                    score=0.0,
                    evidence="missing 'findings' or 'counts'",
                    fix_hint=(
                        "Provide findings: list[dict] (each with "
                        "'severity') or counts: dict[str, int]"
                    ),
                    source=self.source,
                )
            counts = {s: 0 for s in self.VALID_SEVERITIES}
            for f in findings:
                if not isinstance(f, dict):
                    continue
                s = str(f.get("severity", "")).upper()
                if s in self.VALID_SEVERITIES:
                    counts[s] = counts.get(s, 0) + 1

        # Check all keys are valid severities (no LOWEST / TRIVIAL etc).
        invalid_keys = set(counts.keys()) - self.VALID_SEVERITIES
        if invalid_keys:
            return PrincipleResult(
                principle_name=self.name,
                domain=domain,
                passed=False,
                score=0.5,
                evidence=f"invalid severity keys: {invalid_keys}",
                fix_hint=(
                    "Use only CRITICAL / HIGH / MEDIUM / LOW. ECC "
                    "doctrine forbids novel severity names."
                ),
                source=self.source,
            )

        derived = self.derive_verdict(counts)
        verdict = str(target.get("verdict", "")).upper()

        if verdict not in self.VALID_VERDICTS:
            return PrincipleResult(
                principle_name=self.name,
                domain=domain,
                passed=False,
                score=0.5,
                evidence=f"verdict={verdict!r} not in {self.VALID_VERDICTS}",
                fix_hint="Use APPROVE / WARNING / BLOCK",
                source=self.source,
            )

        if verdict != derived:
            return PrincipleResult(
                principle_name=self.name,
                domain=domain,
                passed=False,
                score=0.6,
                evidence=(
                    f"verdict={verdict!r} does not match counts "
                    f"(derived={derived!r} from {counts})"
                ),
                fix_hint=(
                    "Verdict must follow counts: "
                    "CRITICAL>0 -> BLOCK, HIGH>0 -> WARNING, "
                    "else APPROVE."
                ),
                source=self.source,
            )

        return PrincipleResult(
            principle_name=self.name,
            domain=domain,
            passed=True,
            score=1.0,
            evidence=f"counts={counts} verdict={verdict} consistent",
            fix_hint="",
            source=self.source,
        )


register(SeverityTableOutput())
