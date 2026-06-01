"""Cost Collapse Layer -- BL-COST-001.

Cheap-first model routing. Map a task description to a RouteClass +
model + max_budget. Public API: route, RouteResult, RouteClass,
MAX_BUDGET_*, MODEL_*.
"""
from .router import (
    MAX_BUDGET_MACRO,
    MAX_BUDGET_MICRO,
    MAX_BUDGET_NANO,
    MAX_BUDGET_ULTRA,
    MODEL_MACRO,
    MODEL_MICRO,
    MODEL_NANO,
    MODEL_ULTRA,
    RouteClass,
    RouteResult,
    route,
)

__all__ = [
    "MAX_BUDGET_MACRO",
    "MAX_BUDGET_MICRO",
    "MAX_BUDGET_NANO",
    "MAX_BUDGET_ULTRA",
    "MODEL_MACRO",
    "MODEL_MICRO",
    "MODEL_NANO",
    "MODEL_ULTRA",
    "RouteClass",
    "RouteResult",
    "route",
]
