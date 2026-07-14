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

You rarely need to run it by hand. When startup crosses an interruption, the SessionStart
gate (`tools/recovery_epoch_gate.py`) opens a **recovery epoch**, pins the topology recorded
BEFORE the interruption, judges what came back, and prints one line naming the panes that did
not. This command is the full receipt behind that line.

## The pinned reference (why the verdict can be trusted)

The reference is not "the newest snapshot". The newest snapshot is written by a task that
keeps running after a bad restore, so within ~20 minutes it records the DAMAGE -- and scoring
the damage against itself returns RECOVERED every time. While an epoch is open, the verdict is
scored against the snapshot pinned at the boundary, and that pin never advances until the
recovery is accepted or dismissed (`HR-RECOVERY-REFERENCE-001`).

Options:
- `--reference <path>` -- override the pin with a specific
  `~/.claude/state/pane_map_history/pane_map_*.json`.
- `--json` -- machine-readable verdict (includes `reference_source`: `pinned` or `newest`).
- `--no-receipt` -- do not write to `vault/recovery/`.

Epoch control:
- `python modules/session_resilience/epoch.py --show` -- the open interruption and its pin.
- `python modules/session_resilience/epoch.py --dismiss` -- close an epoch whose panes you do
  not want back. Explicit and recorded; a shortfall is never closed automatically.

## Reading the verdict

- **RECOVERED** (exit 0) -- every observable dimension matched. Completion is allowed.
- **PARTIAL / FAILED** (exit 3) -- a real shortfall, named per dimension. Completion is
  HELD. This is the signal that a restore silently dropped panes, collapsed several panes
  onto one session, or never reopened a repo window.
- **HELD** (exit 2) -- the verdict could not be computed (no reference snapshot). Never
  read this as a pass; an unevaluated recovery is not an accepted one.

A RECOVERED verdict closes the epoch. A shortfall keeps it OPEN and keeps surfacing at every
SessionStart until the panes are really back or you dismiss it -- a loss that stops being
mentioned is a loss that was silently accepted.

## Declared limitation

The interruption is detected by the two-signal rule: an ACTIVE beacon (the session never closed
gracefully) AND either the machine booted after that beacon, or a MEASURED zero live-terminal
count. Boot-crossing proves the reboot and OOM-reboot cases. An application-level kill that does
NOT reboot the host is only provable via a real live-terminal measurement, and none is trustworthy
at startup (pane_map's `live` flags are recomputed on a 5-minute cycle, so right after a cold start
they still describe the dead panes). Rather than fabricate a count -- which would either miss real
crashes or fire on every new pane opened beside live ones -- it is left UNMEASURED, and an
unmeasured count is never read as zero. For that case, run this command by hand with `--reference`.

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
