---
title: gsd-autonomous auto-compact — unattended multi-cycle runs
date: 2026-09-15
tier: T2
status: A+B SHIPPED, C PARTIAL 2026-09-15. Owner approved "daemon types the
  resume command"; the auto-mode classifier REFUSED that script (Tmux Self
  Drive) and it was not built or worked around. C degraded to the Owner's
  option 2 — one keystroke per compaction cycle. Gate 19/19, 5 mutants caught.
covers: [gsd_autonomous, autocompact, context_watchdog, autocompact_resume, gsd_autorun_marker, sendkeys_resume]
origin: Owner directive 2026-09-15 "quiero que hagas que /gsd-autonomous autocompacte"
---

# Spec — /gsd-autonomous auto-compact

## Objective

A `/gsd-autonomous` run survives an arbitrary number of context compactions
without a human keystroke: at each pressure crossing the run checkpoints,
compacts, and re-issues itself at the phase it had reached.

## What already exists (measured 2026-09-15, do not rebuild)

| Component | State | Evidence |
|---|---|---|
| `context-watchdog.py` tier-2 (>=70% used) | LIVE in `Stop-chain` | `hook-dispatcher.js:136` |
| checkpoint + trigger flag + daemon spawn | LIVE | `_kclear_equivalent` / `_write_trigger_flag` / `_spawn_daemon` |
| `auto-compact-sendkeys-daemon.ps1` | LIVE, fired 2026-09-14T16:28Z | `hooks/auto-compact-daemon.log` |
| metrics producer `claude-ctx-<sid>.json` | LIVE after the gsd-core 1.14.0 install | this session's file, `used_pct` present |

The chain already reaches `/compact`. It does NOT reach a second cycle, and it
does NOT come back.

## The three gaps this spec closes

**A — Contradictory instruction.** `gsd-context-monitor.js` injects "wrap up
current task" at 35% remaining and "stop immediately and save state" at 25%.
That is the opposite of "checkpoint, compact, continue". An autonomous run
obeys the nearer, louder advice and halts.

**B — Tier-2 fires once per session.** `ADVISORY_FLAG`
(`claude-ctxwd-adv-<sid>.flag`) is set and never cleared, so the second
crossing in a long run is silent. A 70h run needs N crossings, not one.

**C — Nothing resumes.** The SendKeys daemon sends `~` (Enter) only; it types
no text. After compaction the session sits idle with no `/gsd-autonomous
--from N`.

## Design

**Ownership constraint.** `~/.claude/gsd-core/**` is installer-managed (the
1.14.0 install moved 49 locally-modified files to `gsd-local-patches/`), and
writes to `~/.claude/hooks/` are denied to the agent. Therefore every file this
spec creates or edits lives in the Power Pack repo, and the existing live
daemon is NOT modified — the resume step is a new, separately-spawned
PP-owned script.

### Scope (in)

1. `modules/zero-crash/hooks/context-watchdog.py`
   - **Rearm**: when `used_pct` falls below `THRESHOLD_REARM_PCT` (45) and the
     advisory flag exists, delete it. A drop that large only happens through
     compaction or a fresh context, so the next crossing fires again. Closes B.
   - **Autorun awareness**: `_read_autorun_marker()` imports the marker's own
     contract (never a second copy of it) and `_resume_clause()` turns it into
     the sentence appended to the tier-2 message. Both fail-open.
2. ~~`modules/zero-crash/hooks/autocompact_resume_daemon.ps1`~~ **NOT BUILT.**
   The auto-mode classifier refused the write (`Tmux Self Drive`) — a
   guardrail against the agent building a mechanism that types commands into
   the Owner's own session. Not worked around, and reusing the existing Enter
   daemon to the same end was deliberately not attempted: that is the same
   capability the refusal names, so it is the Owner's call, not the agent's.
   The marker's reader is instead the tier-2 message, which makes the resume
   one keystroke per cycle rather than automatic.
3. `tools/gsd_autorun_marker.py` (new) — write / read / clear the marker at
   `~/.claude/state/gsd-autorun-<session_id>.json`. Validates at the write
   boundary: a command that is not a single slash-prefixed line free of
   SendKeys metacharacters is refused rather than stored for something to type.
4. `tools/gsd_long_run_config.py` (new) — lowers GSD's
   `hooks.context_warning_threshold` / `context_critical_threshold` to 12/8,
   below the 30%-remaining compaction point, parking the previous values so
   `--restore` is exact rather than a guess at the defaults. Closes A.
5. `commands/cpp-gsd-long.md` (new) — the launcher tying 4 + 3 + the run
   together, and its own cleanup block.
6. `tools/test_gsd_autocompact.py` (new) — V-GSDAC-* gates.

### Scope (out)

- No edit to any file under `~/.claude/gsd-core/`.
- No edit to `auto-compact-sendkeys-daemon.ps1`.
- No change to tier-1 (60%) behaviour or to the orchestrator overlay.
- Registering `cpp-gsd-long` into `~/.claude/commands/` is an Owner step
  (HR-001); this spec ships the PP-internal half only.

## Acceptance — MEASURED 2026-09-15

- `python tools/test_gsd_autocompact.py` → **19/19, exit 0**.
- Five mutants driven, five caught:
  rearm floor → 0 (never rearms): 2 gates red ·
  rearm floor → 55 (rearms mid-run): 1 red ·
  marker reader severed: 2 red ·
  restore inventing a default: 1 red ·
  warning threshold back to 35: 1 red.
- Negative control: with no marker, `_resume_clause()` returns `""`, so the
  tier-2 message is byte-identical for an ordinary session.
- **Instrument failure found and fixed mid-build:** the gate's first version
  derived its probe points from `THRESHOLD_REARM_PCT` itself, so the floor→0
  mutant scored 10/10. Probe points are now absolute (25% post-compaction,
  50% mid-run) and the floor is pinned independently. A gate that derives its
  subject from the thing it judges cannot fail.
- Negative control: with no marker, tier-2 behaves exactly as before
  (byte-identical message).
- Live gate (Owner-run, not claimable from tests): one real run with
  `_TEST_CONTEXT_PCT` forcing two consecutive crossings, observing two
  compactions and the run continuing at phase N+1 unattended.

## Rollback

Delete the three new files and revert the watchdog edit. Nothing else in the
Stop chain changes; the watchdog is fail-open on every added path, so a broken
addition degrades to today's single-cycle behaviour rather than to no watchdog.

## Honest limits

- SendKeys types into whichever window has focus. The daemon refuses unless
  the foreground process is Cursor, which is a guard, not a guarantee: moving
  to a different Cursor pane inside the dispatch window sends the text to that
  pane. This is the same accepted limit as the existing Enter dispatch (Owner
  1c), widened from one keystroke to a command string.
- A compaction that Claude Code performs natively (not through this chain)
  also trips the rearm — intended, and it means the marker's resume command
  can fire after a compaction this chain did not cause.
