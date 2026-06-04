# /auto-reset — automatic context reset with work-state continuity

> Auto-Reset Orchestrator (2026-06-04, BL-AUTO-RESET-001). Composes the
> pieces that already existed (ram_guard, context-watchdog, snapshot,
> restart_resume) into one flow: **pausa limpia → comprime → continúa**,
> sin intervención del Owner, sin pérdida de contexto de trabajo.

## What it does

When a long session builds up context pressure, the system pauses cleanly,
saves *exactly* what you were doing, runs `/compact` or `/kclear` by severity,
and the next session resumes knowing the task, last commit, last file, and
what was pending. You don't lose your place.

## What triggers it

`modules/cpc_os/context_monitor.py` checks three proxies on every Stop
(RAM probe throttled to 180 s) and returns one of three states:

| State | Trigger (any proxy, env-tunable) | Action |
|---|---|---|
| `HEALTHY` | below all thresholds | nothing |
| `COMPACT_NEEDED` | claude.exe RAM ≥ 20 GB · jsonl ≥ 4 MB · turns ≥ 1200 | `/compact` |
| `KCLEAR_NEEDED` | claude.exe RAM ≥ 28 GB · jsonl ≥ 6 MB · turns ≥ 2400 | `/kclear` |

RAM is the primary signal (the reality contract: "la RAM sube > threshold").
Env overrides: `PP_RAM_WARN_GB`, `PP_RAM_CRIT_GB`, `PP_CTX_COMPACT_MB`,
`PP_CTX_KCLEAR_MB`, `PP_CTX_COMPACT_TURNS`, `PP_CTX_KCLEAR_TURNS`.

## The flow

```
Stop event
  └─ context-watchdog.py (Stop-chain)
       └─ orchestrator overlay (M4)
            ├─ context_monitor.assess()            → HEALTHY? fall through
            ├─ COMPACT/KCLEAR → work_state_saver    → ~/.claude/state/work_state_<sid>.json
            │     { task, last_file, last_commit, branch, pending, cwd }
            └─ decision:block + advisory  ──────────┐
                                                     │ (model re-invoked with advisory)
  model ends its reply with `/compact focus on <task>`  (or `/kclear`)
       └─ SendKeys daemon presses Enter (zero-keystroke if Cursor focused;
          1-keystroke fallback otherwise — BL-0003: a hook cannot self-fire
          a slash command)
  NEW session starts
       └─ session_start_hub.js → hookWorkStateResume(cwd)   (M5)
            └─ injects: "[auto-reset resume] Continuing… Task: X.
               Last commit: Y. Last file: Z. Pending: …"  (then consumes file)
```

## What the advisory looks like

```
AUTO-RESET [COMPACT_NEEDED] — context pressure: ram 21.4GB>=20GB.
Work-state SAVED (task + last commit + pending). Task: <your task>.
Last commit: <hash subj>. Last file: <path>. Pending: <files>.
End your next response with a SINGLE trailing line — exactly
`/compact focus on <task>` — no preface, no markdown. …
```

## What to do when it appears

Nothing manual is required. Let the chain run — the model emits the slash
line, the daemon dispatches it. If Cursor is **not** the focused window, press
Enter once (the daemon promotes to an honest 1-keystroke fallback). After the
reset, the new session starts with the `[auto-reset resume]` context already
injected — just continue.

## How to verify it worked

```powershell
# Current pressure verdict (real signals):
python -m modules.cpc_os.context_monitor --json --session-id <sid>

# What the orchestrator would do right now:
python -m modules.cpc_os.auto_reset_orchestrator --json

# Inspect / list saved work-states:
python modules/cpc_os/work_state_saver.py --load --cwd <repo>
```

A successful resume shows an `[auto-reset resume]` line in the new session's
opening context and the `work_state_<sid>.json` file is gone (consumed
single-shot).

## Honest limits

- **BL-0003**: a hook cannot auto-dispatch a slash command. The SendKeys
  daemon is the closest to zero-touch (Enter on your behalf when Cursor is
  focused); otherwise it is 1-keystroke. True zero-intervention slash dispatch
  is not available from a hook.
- The orchestrator overlay rides the existing `context-watchdog.py`, already in
  the dispatcher Stop-chain — no new hook registration needed. (The `ram_guard`
  Stop hook from the RAM sprint is a separate, optional advisory.)
