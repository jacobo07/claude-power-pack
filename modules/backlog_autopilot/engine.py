"""what_now engine -- score = (priority bonus) + impact + (effort score)."""
from __future__ import annotations

from dataclasses import dataclass, field

# Score weights -- v1 defaults; expose for Owner tuning.
PRIORITY_BONUS_WEIGHT = 2  # multiplier on (PRIORITY_MAX+1 - priority)
PRIORITY_MAX = 3            # priorities 0..3 (0 = P0 highest)

# Effort: smaller effort is more attractive (faster wins).
EFFORT_SCORE: dict[str, int] = {"S": 4, "M": 3, "L": 2, "XL": 1}

# Impact: larger impact is more attractive.
IMPACT_SCORE: dict[str, int] = {
    "Critical": 8,
    "High": 5,
    "Medium": 3,
    "Low": 1,
}


@dataclass(frozen=True)
class BacklogItem:
    id: str
    title: str
    priority: int               # 0 = P0 (highest)
    effort: str                 # "S" | "M" | "L" | "XL"
    impact: str                 # "Critical" | "High" | "Medium" | "Low"
    blockers: tuple[str, ...] = field(default_factory=tuple)
    done: bool = False


@dataclass(frozen=True)
class WhatNowResult:
    recommended: BacklogItem | None
    score: int
    reasoning: str
    candidates_considered: int


def _score(item: BacklogItem) -> int:
    priority_bonus = (PRIORITY_MAX + 1 - item.priority) * PRIORITY_BONUS_WEIGHT
    return (
        priority_bonus
        + IMPACT_SCORE.get(item.impact, 0)
        + EFFORT_SCORE.get(item.effort, 0)
    )


def _is_actionable(item: BacklogItem) -> bool:
    return not item.done and not item.blockers


def what_now(backlog: list[BacklogItem]) -> WhatNowResult:
    candidates = [i for i in backlog if _is_actionable(i)]
    if not candidates:
        return WhatNowResult(
            recommended=None,
            score=0,
            reasoning="no actionable items in backlog",
            candidates_considered=0,
        )
    best = max(candidates, key=_score)
    s = _score(best)
    reasoning = (
        f"selected {best.id} (P{best.priority}, {best.impact}, "
        f"effort={best.effort}) with score {s}; "
        f"{len(candidates)} actionable of {len(backlog)} total"
    )
    return WhatNowResult(
        recommended=best,
        score=s,
        reasoning=reasoning,
        candidates_considered=len(candidates),
    )
