"""Architecture Horizon -- which part of the architecture stops being valid first.

R2 of the UPAC ownership audit. A VIEW over the real import graph, not a simulator:
it answers the structural form of the question (if this unit's contract changes,
what must change with it) and declares the stressors it cannot model.
"""
from .horizon import (
    build_graph,
    cycles,
    dependents,
    gate,
    invalidate,
    main,
    rank,
    render,
    transitive_dependents,
    CONCENTRATION_FLOOR,
    LOAD_BEARING_BASELINE,
    UNMODELLED_STRESSORS,
)

__all__ = [
    "build_graph", "cycles", "dependents", "gate", "invalidate", "main",
    "rank", "render", "transitive_dependents",
    "CONCENTRATION_FLOOR", "LOAD_BEARING_BASELINE", "UNMODELLED_STRESSORS",
]
