"""P03 -- Common False Positives Catalog.

Source: ECC/Affaan Mustafa MIT
       (agents/code-reviewer.md "Common False Positives - Skip These"
        section, lines 76-111)

ECC enumerates 12+ patterns that LLM reviewers commonly mis-flag:
"consider adding error handling" on already-handled paths, "magic
number" on obvious constants, "N+1 query" on fixed-cardinality loops,
security theater on Math.random in non-crypto contexts, etc.

This principle scans a finding's text against the catalog and FAILS
the finding (marks it as likely false positive) when it matches. The
caller then decides whether to drop it or surface it with a low
severity.
"""
import re
from typing import Any

from modules.uqf.principles import Principle, PrincipleResult, register


class CommonFalsePositivesCatalog(Principle):
    name = "common_false_positives_catalog"
    description = (
        "Filter findings that match the ECC catalog of common LLM "
        "review false positives."
    )
    domains = ["code"]
    source = "ECC/Affaan Mustafa MIT"

    # 12+ patterns from ECC code-reviewer.md. Order matters only for
    # the `evidence` field (first match wins).
    CATALOG: tuple[tuple[str, str], ...] = (
        ("consider adding error handling",
         "may be handled by caller/framework"),
        ("missing input validation",
         "internal function -- trace one caller before flagging"),
        ("magic number",
         "200/404/1000/60/24 etc. are well-known constants"),
        ("function too long",
         "exhaustive switch / config object / test table != complex"),
        ("missing jsdoc",
         "single-purpose internal helper is self-describing"),
        ("missing docstring",
         "single-purpose internal helper is self-describing"),
        ("prefer const over let",
         "the variable may be reassigned -- read the function first"),
        ("possible null dereference",
         "may be type-narrowed upstream"),
        ("n+1 query",
         "may be fixed-cardinality or DataLoader-batched"),
        ("missing await",
         "may be intentional fire-and-forget (logging/metrics)"),
        ("should use typescript",
         "do not propose stack change in a review"),
        ("should have types",
         "do not propose stack change in a review"),
        ("hardcoded value",
         "test fixtures should have hardcoded expectations"),
        ("math.random",
         "non-crypto context: animation/jitter/sampling is fine"),
        ("eval is dangerous",
         "plugin systems explicitly use eval/Function as code-loading"),
    )

    def check(self, target: Any, domain: str) -> PrincipleResult:
        text = ""
        if isinstance(target, str):
            text = target
        elif isinstance(target, dict):
            text = str(target.get("text") or target.get("message") or "")

        if not text:
            return PrincipleResult(
                principle_name=self.name,
                domain=domain,
                passed=True,
                score=1.0,
                evidence="no finding text to evaluate",
                fix_hint="",
                source=self.source,
            )

        lo = text.lower()
        for pattern, reason in self.CATALOG:
            if pattern in lo:
                return PrincipleResult(
                    principle_name=self.name,
                    domain=domain,
                    passed=False,
                    score=0.0,
                    evidence=f"matched FP pattern: {pattern!r}",
                    fix_hint=(
                        f"This is a common LLM review FP. Reason: "
                        f"{reason}. Drop the finding unless you have "
                        f"codebase-specific evidence."
                    ),
                    source=self.source,
                )

        return PrincipleResult(
            principle_name=self.name,
            domain=domain,
            passed=True,
            score=1.0,
            evidence=f"no FP pattern matched in {len(text)} chars",
            fix_hint="",
            source=self.source,
        )


register(CommonFalsePositivesCatalog())
