---
description: Judge the last workspace restore against the topology PP recorded before the interruption. RECOVERED / PARTIAL / FAILED, with a receipt.
---

# /recovery-verdict

A restore that nobody scored is not a recovery -- it is a hope. This command makes the
recovery acceptance arbiter (`modules/session_resilience/acceptance.py`) judge the real
thing: the panes that were alive before the interruption versus the panes alive now.

Run:

```
python tools/recovery_verdict.py
```

Options:
- `--reference <path>` -- score against a specific `~/.claude/state/pane_map_history/pane_map_*.json`
  snapshot instead of the most recent one. Use this after a crash: pick the snapshot from
  BEFORE the crash, not the one taken while half the panes were already gone.
- `--json` -- machine-readable verdict.
- `--no-receipt` -- do not write to `vault/recovery/`.

## Reading the verdict

- **RECOVERED** (exit 0) -- every observable dimension matched. Completion is allowed.
- **PARTIAL / FAILED** (exit 3) -- a real shortfall, named per dimension. Completion is
  HELD. This is the signal that a restore silently dropped panes, collapsed several panes
  onto one session, or never reopened a repo window.
- **HELD** (exit 2) -- the verdict could not be computed (no reference snapshot). Never
  read this as a pass; an unevaluated recovery is not an accepted one.

## What it can and cannot see

`pane_map` witnesses **windows, terminals and conversations**. It knows nothing about
editor tabs, tab order, focus or scroll, so those four dimensions are excluded from the
denominator and reported as unwitnessed -- never scored as passing. A verdict that
silently credited dimensions it cannot observe would be the fake recovery this command
exists to end.

The pane -> conversation mapping is the sharp one: if a restore brings three panes back on
a single session id, the pane count still looks right while the conversation topology has
collapsed. That is the "only one recovered session per pane" symptom, and it is exactly
what the conversations dimension catches.
