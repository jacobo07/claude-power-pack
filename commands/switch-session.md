---
name: switch-session
description: Route a restart or switch intent to a specific Cursor pane via the CPC-OS router (BL-CPCOS-001). Refuses unknown panes, dead panes, and stale intents (>60s old). Logs the handoff to ~/.claude/state/handoffs/handoff_<pane>_<ts>.json so the action is auditable. Use this to safely restart a sibling pane or hand off work mid-session.
---

# /switch-session -- safe pane handoff via CPC-OS

## What it does

Routes a restart / switch intent through the CPC-OS router. The router
checks three safety preconditions BEFORE the intent is dispatched:

1. **Pane known**     -- the target `pane_id` exists in the registry.
2. **Pane not dead**  -- the target's status is `active` or `stale`.
3. **Intent fresh**   -- intent age < 60 s (prevents replay of an
                          abandoned restart command).

If any check fails, the intent is REFUSED with a reason. Otherwise
a handoff record is written to `~/.claude/state/handoffs/` and the
caller proceeds with the dispatch.

## Usage

```
/switch-session <target-pane-id> <kind> [--dry-run] [--reason "<text>"]

  kind ::= restart | switch
```

Examples:

```
/switch-session test-pane-1 restart --reason "claude.exe stuck"
/switch-session pane-3 switch --dry-run --reason "moving work to pane-3"
```

## Programmatic equivalent

```python
import time
from modules.cpc_os import PaneRegistry, route_intent, record_handoff

reg = PaneRegistry.load()
ir = route_intent(reg, "test-pane-1", "restart", time.time())
if not ir.accepted:
    print("REFUSED:", ir.reason)
else:
    record_handoff("test-pane-1", "restart", "claude.exe stuck")
    print("ACCEPTED:", ir.reason)
```

## Safety rationale (§208.1)

"No guessing session identity -- verify or block." Routing a restart
to the wrong pane could kill the user's active work. The router's
fail-closed posture (unknown / dead / stale -> refuse) means the
worst case of an unsafe call is a no-op + diagnostic, never an
accidental restart of the wrong session.

## Pairs with

- `/panes` -- see which panes are registered + alive BEFORE issuing
  a handoff intent.
