"""Intent router -- safety checks before dispatching a pane action.

Refuses: unknown panes, dead panes, stale intents (older than
INTENT_STALE_THRESHOLD_S). Per the §208.1 contract: no guessing
session identity -- verify or block.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from .registry import PaneRegistry

# Intents older than this are stale and refused -- prevents replay
# of a buffered/abandoned restart command after a long pause.
INTENT_STALE_THRESHOLD_S = 60


@dataclass(frozen=True)
class IntentResult:
    accepted: bool
    reason: str


def route_intent(
    registry: PaneRegistry,
    pane_id: str,
    intent: str,
    intent_ts: float,
) -> IntentResult:
    now = time.time()
    if pane_id not in registry.panes:
        return IntentResult(False, f"unknown pane: {pane_id}")
    rec = registry.panes[pane_id]
    if rec.status == "dead":
        return IntentResult(False, f"pane {pane_id} is dead")
    age = now - intent_ts
    if age > INTENT_STALE_THRESHOLD_S:
        return IntentResult(
            False,
            f"intent stale (age {age:.1f}s > {INTENT_STALE_THRESHOLD_S}s)",
        )
    return IntentResult(
        True, f"intent {intent!r} accepted for pane {pane_id}",
    )
