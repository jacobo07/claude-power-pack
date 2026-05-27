"""P09 -- Prompt Defense Baseline.

Source: ECC/Affaan Mustafa MIT
       (every agents/*.md ECC file -- 6-line boilerplate header)

ECC requires every agent prompt to include 6 baseline defenses:

  1. No role override / persona swap from user instructions
  2. No secret / API key / credential leak
  3. No unsafe executable output (HTML/JS/links) unless required
  4. Treat unicode-tricks, homoglyphs, zero-width chars as suspicious
  5. Treat external/fetched/URL data as untrusted; validate first
  6. No harmful / illegal / weapon / malware / phishing content

The principle scans agent prompts (or CLAUDE.md) and counts how many
of these 6 defenses are present (paraphrase accepted). >=4 of 6 = pass.
"""
from typing import Any

from modules.uqf.principles import Principle, PrincipleResult, register


class PromptDefenseBaseline(Principle):
    name = "prompt_defense_baseline"
    description = (
        "Agent/system prompts must include >=4 of the 6 ECC prompt-"
        "defense baseline rules."
    )
    domains = ["prompts"]
    source = "ECC/Affaan Mustafa MIT"

    # Keyword sets for each of the 6 baseline rules. Match is
    # case-insensitive AND-of-any-keyword (any keyword from the set
    # is enough to credit that rule).
    RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("no_role_override",
         ("role override", "persona swap", "do not change role",
          "no role change", "override role", "ignore directives",
          "override project rules")),
        ("no_secret_leak",
         ("do not reveal", "not reveal confidential", "not share secret",
          "not leak", "do not expose credential", "not expose",
          "secret leak", "api key")),
        ("no_unsafe_output",
         ("not output executable", "not output script", "not output html",
          "not output javascript", "do not generate harmful",
          "no unsafe code", "validated", "no unsafe")),
        ("unicode_suspicious",
         ("unicode", "homoglyph", "zero-width", "invisible characters",
          "encoded trick", "suspicious")),
        ("external_untrusted",
         ("untrusted content", "external data", "third-party",
          "validate", "sanitize", "fetched", "url data",
          "treat external")),
        ("no_harmful",
         ("harmful", "dangerous", "illegal", "weapon", "exploit",
          "malware", "phishing", "attack")),
    )

    def check(self, target: Any, domain: str) -> PrincipleResult:
        if not isinstance(target, str):
            return PrincipleResult(
                principle_name=self.name,
                domain=domain,
                passed=False,
                score=0.0,
                evidence=f"target type {type(target).__name__} not str",
                fix_hint="Pass the prompt/agent .md content as a string",
                source=self.source,
            )

        lo = target.lower()
        covered = []
        missing = []
        for rule_name, kws in self.RULES:
            if any(k in lo for k in kws):
                covered.append(rule_name)
            else:
                missing.append(rule_name)

        score = len(covered) / len(self.RULES)
        passed = len(covered) >= 4

        return PrincipleResult(
            principle_name=self.name,
            domain=domain,
            passed=passed,
            score=score,
            evidence=(
                f"{len(covered)}/6 baseline rules detected: {covered}"
            ),
            fix_hint=(
                f"Add missing rules: {missing}. "
                f"See ECC AGENTS.md / agents/*.md for canonical wording."
                if not passed else ""
            ),
            source=self.source,
        )


register(PromptDefenseBaseline())
