"""CPC-OS Switch -- section 208.3 Switch Acceptance Contract.

INTENT + STATE-TRANSITION only (no process control). Validates a
/switch-session intent, then parks the source pane (paused) and brings
the target to active. Refuses when the target is already active -- you
cannot steal focus from a live pane.

section 208.3 acceptance: source handoff safe, target validated, target
not active elsewhere, registry updated, source marked paused, target
confirmed active.

Composition: route_intent() gates the SOURCE (unknown / dead pane,
stale intent); this layer adds the target validation + the atomic
paused/active transition.
"""
from __future__ import annotations

import time

from .handoff import record_handoff
from .registry import PaneRegistry
from .router import route_intent


def switch_intent(
    source_pane_id: str,
    target_pane_id: str,
    intent_ts: float | None = None,
    registry: PaneRegistry | None = None,
) -> dict:
    """Validate + execute a pane switch (state only).

    Returns {"safe": bool, "action": "switch"|"block", "reason": str,
    ...}. Pass ``registry`` for tests; default loads the shared one.
    """
    now = time.time()
    ts = now if intent_ts is None else intent_ts
    reg = registry if registry is not None else PaneRegistry.load()

    # Base safety on the SOURCE (unknown / dead / stale intent).
    routed = route_intent(reg, source_pane_id, "switch", ts)
    if not routed.accepted:
        return {"safe": False, "action": "block", "reason": routed.reason}

    if source_pane_id == target_pane_id:
        return {"safe": False, "action": "block",
                "reason": "source and target are the same pane"}

    if target_pane_id not in reg.panes:
        return {"safe": False, "action": "block",
                "reason": f"unknown target pane: {target_pane_id}"}

    target = reg.panes[target_pane_id]
    if target.status == "dead":
        return {"safe": False, "action": "block",
                "reason": f"target {target_pane_id} is dead"}

    # section 208.3 target not active elsewhere -- refuse stealing focus.
    if target.status == "active":
        return {"safe": False, "action": "block",
                "reason": f"target {target_pane_id} is already active"}

    # Atomic state transition: source -> paused, target -> active.
    reg.pause_pane(source_pane_id)
    reg.activate_pane(target_pane_id)
    record_handoff(source_pane_id, "switch",
                   f"switch {source_pane_id} -> {target_pane_id}",
                   dry_run=False)

    return {
        "safe": True, "action": "switch",
        "source": source_pane_id, "target": target_pane_id,
        "source_status": reg.panes[source_pane_id].status,
        "target_status": reg.panes[target_pane_id].status,
        "reason": "section 208.3 contract satisfied",
    }
