"""CPC-OS (Cursor Pane Coordination OS) -- BL-CPCOS-001 / acceptance 208.x.

Atomic pane registry + heartbeat + intent router + handoff records +
corruption recovery, plus the section 208.2-208.5 acceptance contracts:
restart_intent (208.2), switch_intent (208.3), detect_crash_state
(208.4), plan_parallel_backlog (208.5). Single-source-of-truth lives at
~/.claude/state/cpc_os_registry.json (atomic write via tempfile +
rename). Cursor-only by design -- no external terminal fallback; the
208.2-208.5 layers validate intent + transition registry/handoff state,
they never control a process.

Public API: PaneRegistry, PaneRecord, register/heartbeat/pause/activate/
mark_dead; IntentResult + route_intent; HandoffRecord + record_handoff;
mark_stale_panes + is_pane_alive; recover_corrupt_registry +
detect_crash_state; restart_intent; switch_intent; plan_parallel_backlog.
"""
from .backlog import plan_parallel_backlog
from .handoff import HANDOFF_DIR, HandoffRecord, list_handoffs, record_handoff
from .heartbeat import is_pane_alive, mark_stale_panes
from .recovery import detect_crash_state, recover_corrupt_registry
from .registry import (
    DEFAULT_REGISTRY_PATH,
    HEARTBEAT_INTERVAL_S,
    PaneRecord,
    PaneRegistry,
    STALE_THRESHOLD_S,
)
from .restart import restart_intent
from .router import INTENT_STALE_THRESHOLD_S, IntentResult, route_intent
from .switch import switch_intent

__all__ = [
    "DEFAULT_REGISTRY_PATH",
    "HANDOFF_DIR",
    "HEARTBEAT_INTERVAL_S",
    "HandoffRecord",
    "INTENT_STALE_THRESHOLD_S",
    "IntentResult",
    "PaneRecord",
    "PaneRegistry",
    "STALE_THRESHOLD_S",
    "detect_crash_state",
    "is_pane_alive",
    "list_handoffs",
    "mark_stale_panes",
    "plan_parallel_backlog",
    "recover_corrupt_registry",
    "record_handoff",
    "restart_intent",
    "route_intent",
    "switch_intent",
]
