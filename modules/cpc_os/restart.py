"""CPC-OS Restart -- §208.2 Restart Acceptance Contract.

INTENT-ONLY by design. This module validates a /restart intent and
records an audit handoff; it NEVER kills or relaunches a process and
NEVER writes ~/.claude/state/restart_pending.json -- that file belongs
to the legacy restart_resume.js / session_start_hub.js flow, and the
actual in-pane relaunch stays with the existing /restart command +
kclaude wrapper. Mixing a second writer into restart_pending.json would
destabilise the session-restart path (BL-LAZ-STALE-001 neighbourhood).

§208.2 acceptance: same pane, same Cursor terminal, same cwd, same
conversation/session id, handoff safe, intent consumed once, registry
updated, no duplicate session, no infinite loop.

Composition: route_intent() supplies the base safety gate (unknown /
dead pane, stale intent); this layer adds the cwd + session-id + dedup
invariants specific to restart.
"""
from __future__ import annotations

import time

from .handoff import list_handoffs, record_handoff
from .registry import PaneRegistry
from .router import route_intent

# A second restart handoff for the same pane inside this window is a
# duplicate (double-submit / infinite-loop guard) and is refused.
DUPLICATE_HANDOFF_WINDOW_S = 60


def restart_intent(
    pane_id: str,
    cwd: str,
    session_id: str | None = None,
    intent_ts: float | None = None,
    registry: PaneRegistry | None = None,
) -> dict:
    """Validate a restart intent.

    Returns {"safe": bool, "action": "restart"|"block", "reason": str,
    ...}. Never raises on a known pane; never executes the restart.
    Pass ``registry`` to operate on a specific registry (tests); when
    omitted the shared default registry is loaded.
    """
    now = time.time()
    ts = now if intent_ts is None else intent_ts
    reg = registry if registry is not None else PaneRegistry.load()

    # Base safety: unknown / dead pane, stale intent -> block.
    routed = route_intent(reg, pane_id, "restart", ts)
    if not routed.accepted:
        return {"safe": False, "action": "block", "reason": routed.reason}

    rec = reg.panes[pane_id]

    # §208.2 same cwd.
    if rec.cwd != cwd:
        return {
            "safe": False, "action": "block",
            "reason": f"cwd mismatch: registry={rec.cwd!r} request={cwd!r}",
        }

    # §208.2 same session id -- only when BOTH sides know it (no guessing).
    if (session_id is not None and rec.session_id is not None
            and rec.session_id != session_id):
        return {
            "safe": False, "action": "block",
            "reason": (
                f"session mismatch: registry={rec.session_id} "
                f"request={session_id}"
            ),
        }

    # §208.2 intent consumed once / no infinite loop: refuse a second
    # restart handoff for this pane inside the dedup window.
    for h in list_handoffs(pane_id):
        if h.kind == "restart" and (now - h.created_at) < DUPLICATE_HANDOFF_WINDOW_S:
            return {
                "safe": False, "action": "block",
                "reason": (
                    "restart already in flight for this pane "
                    f"({now - h.created_at:.0f}s ago)"
                ),
            }

    # Record the handoff (audit trail) and sync the session id forward.
    record_handoff(pane_id, "restart", f"restart pane={pane_id} cwd={cwd}",
                   dry_run=False)
    if session_id is not None and rec.session_id is None:
        rec.session_id = session_id
        reg.save()

    return {
        "safe": True, "action": "restart",
        "reason": "section 208.2 contract satisfied",
        "pane_id": pane_id, "session_id": rec.session_id,
    }
