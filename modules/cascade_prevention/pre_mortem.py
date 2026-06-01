"""Pre-mortem cascade detector -- BL-DATASET-BUILD M11.

Analyzes a plan description BEFORE execution; surfaces patterns that
historically trigger cascades. Heuristic-only v1. Returns a list of
Risk records; never raises.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# (regex, severity_label, message). Severity labels:
#   HIGH    -- pre-mortem strongly recommends a pause + review
#   MEDIUM  -- flag for awareness; not a halt
#   LOW     -- informational
_RISK_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (re.compile(
        r"deploy[^.]*\b(without|skip|no)\b[^.]*\btest",
        re.IGNORECASE),
     "HIGH",
     "deploy without tests -> C4 cascade risk (HR-CASCADE pending)"),
    (re.compile(r"--no-verify\b", re.IGNORECASE),
     "HIGH",
     "--no-verify skips git hooks -> commit-without-verify cascade"),
    (re.compile(r"\brm\s+-r?f|Remove-Item.*-Recurse", re.IGNORECASE),
     "HIGH",
     "destructive delete -- ensure backup before proceeding"),
    (re.compile(r"force.?push|push\s+--force\b", re.IGNORECASE),
     "MEDIUM",
     "force-push -> history-rewrite cascade risk"),
    (re.compile(r"reset\s+--hard|hard.reset", re.IGNORECASE),
     "MEDIUM",
     "git reset --hard -> loss-of-work cascade risk"),
    (re.compile(r"refactor[^.]*architecture|architecture[^.]*overhaul",
                re.IGNORECASE),
     "MEDIUM",
     "architectural refactor -> scope-drift cascade risk"),
    (re.compile(r"drop\s+(table|database|schema)", re.IGNORECASE),
     "HIGH",
     "destructive SQL DROP -> data-loss cascade"),
    (re.compile(r"hardcode|hard.code|inline.*secret|raw.?key|paste.*key",
                re.IGNORECASE),
     "HIGH",
     "hardcoded credential -> secret-leak cascade (HR-SECRET-001..005)"),
    (re.compile(r"\bgit\s+add\s+(-A|--all)\b|stage\s+all\b",
                re.IGNORECASE),
     "MEDIUM",
     "indiscriminate staging -> sibling-pane contamination risk"),
    (re.compile(r"migrate[^.]*production|prod[^.]*migration",
                re.IGNORECASE),
     "HIGH",
     "production migration -> rollback plan required"),
    (re.compile(r"disable[^.]*backup|skip[^.]*backup",
                re.IGNORECASE),
     "HIGH",
     "skipped backup -> delete-without-backup cascade risk"),
]


@dataclass(frozen=True)
class Risk:
    severity: str
    message: str
    matched_text: str


def analyze(plan: str) -> list[Risk]:
    """Return the list of Risk records flagged by `plan`. Empty -> clean."""
    if not plan:
        return []
    out: list[Risk] = []
    for pat, sev, msg in _RISK_PATTERNS:
        m = pat.search(plan)
        if m:
            out.append(Risk(
                severity=sev,
                message=msg,
                matched_text=m.group(0)[:60],
            ))
    return out


def summary(risks: list[Risk]) -> str:
    if not risks:
        return "pre-mortem: 0 risks detected"
    by_sev: dict[str, int] = {}
    for r in risks:
        by_sev[r.severity] = by_sev.get(r.severity, 0) + 1
    return "; ".join(
        f"{sev}={count}" for sev, count in sorted(by_sev.items())
    )
