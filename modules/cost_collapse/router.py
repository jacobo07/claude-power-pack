"""Cheap-first task router. Keyword-based v1; ML-tier escalation TBD."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RouteClass(Enum):
    NANO = "nano"
    MICRO = "micro"
    MACRO = "macro"
    ULTRA = "ultra"


# OD3-aligned budget ceilings per route class (USD).
MAX_BUDGET_NANO = 1.0
MAX_BUDGET_MICRO = 15.0
MAX_BUDGET_MACRO = 30.0
MAX_BUDGET_ULTRA = 100.0

# Model IDs (per ~/.claude/CLAUDE.md model registry, 2026-06-01).
MODEL_NANO = "claude-haiku-4-5"
MODEL_MICRO = "claude-sonnet-4-6"
MODEL_MACRO = "claude-opus-4-7"
MODEL_ULTRA = "claude-opus-4-7"  # same model, ULTRA budget tier


# Keyword sets. NANO/MACRO/ULTRA are explicit overrides; everything
# else routes to MICRO by default.
NANO_KEYWORDS: frozenset[str] = frozenset({
    "format", "formatting", "lint", "linting",
    "rename", "renaming", "indent", "indentation",
    "whitespace", "typo", "fix typo", "fix import", "imports",
    "comment fix", "docstring fix",
})

MACRO_KEYWORDS: frozenset[str] = frozenset({
    "architect", "architecture", "design system", "system design",
    "code review", "review the", "audit", "auditing",
    "refactor across", "cross-cutting", "design doc",
})

ULTRA_KEYWORDS: frozenset[str] = frozenset({
    "architecture major", "deep refactor", "monorepo migration",
    "migrate", "migration plan", "platform overhaul",
    "rewrite the system", "ground-up redesign",
})


@dataclass(frozen=True)
class RouteResult:
    route_class: RouteClass
    model: str
    max_budget: float
    reason: str


def _match(desc: str, kws: frozenset[str]) -> str | None:
    for kw in kws:
        if kw in desc:
            return kw
    return None


def route(description: str) -> RouteResult:
    """Map a task description to a route. Longer/more-specific keyword
    sets are matched first so ULTRA wins over MACRO wins over NANO."""
    desc = (description or "").lower()

    hit = _match(desc, ULTRA_KEYWORDS)
    if hit:
        return RouteResult(
            route_class=RouteClass.ULTRA,
            model=MODEL_ULTRA,
            max_budget=MAX_BUDGET_ULTRA,
            reason=f"matched ULTRA keyword: {hit!r}",
        )

    hit = _match(desc, MACRO_KEYWORDS)
    if hit:
        return RouteResult(
            route_class=RouteClass.MACRO,
            model=MODEL_MACRO,
            max_budget=MAX_BUDGET_MACRO,
            reason=f"matched MACRO keyword: {hit!r}",
        )

    hit = _match(desc, NANO_KEYWORDS)
    if hit:
        return RouteResult(
            route_class=RouteClass.NANO,
            model=MODEL_NANO,
            max_budget=MAX_BUDGET_NANO,
            reason=f"matched NANO keyword: {hit!r}",
        )

    return RouteResult(
        route_class=RouteClass.MICRO,
        model=MODEL_MICRO,
        max_budget=MAX_BUDGET_MICRO,
        reason="default route (no specific keyword matched)",
    )
