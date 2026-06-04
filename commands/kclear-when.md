# /kclear-when — when (and why) to clear context for RAM

> RAM Optimization Sprint (2026-06-04). Companion to `tools/ram_guard.py`
> and `hooks/ram-guard-stop.js`.

## The one fact that matters

FASE -1 forensics measured the Claude stack on this host:

| Source | RAM | Controllable? |
|---|---|---|
| `claude.exe` (V8 heap + active context) | **5.9 GB → 25 GB in one session** | ❌ only via context reset |
| PP hooks (node) + python, steady-state | **~12 MB** | ✅ already minimal |

The PP cannot shrink `claude.exe`. **The only lever on the GB-scale number
is reducing context** — `/kclear`, `/compact`, or a session restart. There is
no process to kill, no cache to drop, that reclaims those gigabytes.

## When to act

`hooks/ram-guard-stop.js` samples `claude.exe` working-set every 5 minutes
and surfaces an advisory automatically:

- **WARN — `claude.exe` ≥ 20 GB** → "consider `/kclear` soon". A snapshot is
  ensured so nothing is lost if the host OOMs.
- **CRITICAL — `claude.exe` ≥ 28 GB** → run `/kclear` (or `/compact`) **now**.
  A fresh crash-recovery snapshot is forced before the likely crash.

Thresholds are env-tunable (defaults recalibrated from the literal plan's
8/11 GB, which would fire every long session — the forensics observed 25 GB
stable without a crash):

```
setx PP_RAM_WARN_GB 20
setx PP_RAM_CRIT_GB 28
```

## What `/kclear` does vs `/compact`

- **`/kclear`** — writes a token-lean checkpoint/handoff, then you start a
  fresh session: claude.exe RAM drops to its cold baseline. Use when the
  conversation is long and you want a clean slate with continuity.
- **`/compact`** — summarizes in place; frees some V8 heap without a full
  restart. Lighter, keeps the same session.

Either reduces the resident context that drives the heap. `/kclear` reclaims
the most RAM; `/compact` is the lower-friction option mid-task.

## Manual check anytime

```powershell
python tools\ram_guard.py            # one-line verdict
python tools\ram_guard.py --json     # machine-readable
```

## Owner-side hook registration (HR-001)

Auto-mode cannot self-register hooks in `~/.claude/settings.json`. To activate
the proactive advisory, add to the `"hooks"` object and `/restart`:

```json
"Stop": [
  { "hooks": [
    { "type": "command",
      "command": "node \"C:\\Users\\User\\.claude\\skills\\claude-power-pack\\hooks\\ram-guard-stop.js\"" }
  ] }
]
```

The hook is throttled (5-min) and fail-open — it never blocks a Stop event.
