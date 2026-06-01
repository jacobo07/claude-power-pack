"""CPC-OS (Cursor Pane Coordination OS) -- BL-CPCOS-001 / acceptance §208.1.

Atomic pane registry + heartbeat + intent router + handoff records +
corruption recovery. Single-source-of-truth lives at
~/.claude/state/cpc_os_registry.json (atomic write via tempfile +
rename). Cursor-only by design -- no external terminal fallback.

Public API: PaneRegistry, PaneRecord, register/heartbeat/mark_dead;
IntentResult + route_intent; HandoffRecord + record_handoff;
mark_stale_panes + is_pane_alive; recover_corrupt_registry.
"""
from .handoff import HANDOFF_DIR, HandoffRecord, record_handoff
from .heartbeat import is_pane_alive, mark_stale_panes
from .recovery import recover_corrupt_registry
from .registry import (
    DEFAULT_REGISTRY_PATH,
    HEARTBEAT_INTERVAL_S,
    PaneRecord,
    PaneRegistry,
    STALE_THRESHOLD_S,
)
from .router import INTENT_STALE_THRESHOLD_S, IntentResult, route_intent

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
    "is_pane_alive",
    "mark_stale_panes",
    "recover_corrupt_registry",
    "record_handoff",
    "route_intent",
]
