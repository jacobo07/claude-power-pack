"""Heartbeat helpers -- staleness detection / liveness check."""
from __future__ import annotations

import time

from .registry import PaneRegistry, STALE_THRESHOLD_S


def mark_stale_panes(registry: PaneRegistry) -> int:
    """Demote active panes whose last heartbeat is older than
    STALE_THRESHOLD_S to status='stale'. Returns count promoted."""
    now = time.time()
    count = 0
    for rec in registry.panes.values():
        if rec.status == "active":
            if (now - rec.last_heartbeat_at) > STALE_THRESHOLD_S:
                rec.status = "stale"
                count += 1
    if count:
        registry.save()
    return count


def is_pane_alive(registry: PaneRegistry, pane_id: str) -> bool:
    rec = registry.panes.get(pane_id)
    if rec is None or rec.status != "active":
        return False
    return (time.time() - rec.last_heartbeat_at) <= STALE_THRESHOLD_S
