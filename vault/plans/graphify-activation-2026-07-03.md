# Graphify + ADS Activation — Owner Runbook (2026-07-03)

One `Copy-Item` activates the whole Graphify kernel **and** the drifted ADS hook.
No restart. No new code. Everything is already built and committed.

---

## SYNC SAFETY REPORT (PASO -1, verified)

| Check | Result |
|---|---|
| Live dispatcher exists | Yes (`~/.claude/hooks/hook-dispatcher.js`) |
| Hooks in CANONICAL (repo) | `graph_first_gate` ×2, `ads_sync.py` ×1, `session_writeback.py` ×1 |
| Same hooks in LIVE | **0 refs** — fully inert |
| Lines only in LIVE (would be lost) | **NONE** — live is a strict subset of canonical |
| What the sync ADDS | ADS Stop hook + GK-08 session_writeback Stop hook + GK-12 graph_first_gate (Bash + Read/Grep chains) |
| Gate CLI path (real stdin) | Emits the advisory, exit 0 — verified |
| Dispatcher `node --check` | Clean |
| **Safe to sync** | **YES — additive only, nothing lost, revertible** |

The gate script itself needs NO copy (the dispatcher references it cross-tree via
`../skills/claude-power-pack/hooks/graph_first_gate.js`, which resolves into the
repo from `~/.claude/hooks/`). Only the dispatcher file syncs.

## The activation (run in PowerShell)

**1 — Back up the current live dispatcher (revert point):**
```powershell
Copy-Item "C:\Users\User\.claude\hooks\hook-dispatcher.js" `
          "C:\Users\User\.claude\hooks\hook-dispatcher.js.pre-graphify.bak" -Force
```

**2 — Sync canonical → live (the activation):**
```powershell
Copy-Item "C:\Users\User\.claude\skills\claude-power-pack\hooks\hook-dispatcher.js" `
          "C:\Users\User\.claude\hooks\hook-dispatcher.js" -Force
```

No restart: the dispatcher is spawned fresh per event and re-reads its CHAIN_MAP
from disk, so open sessions pick up the new hooks on their next tool call.

## What activates

- **GK-12 `graph_first_gate`** — on PreToolUse for Grep (Read|Grep chain) and a
  Bash grep/find/ls, surfaces a "navigate the graph first" advisory. Level-2,
  NEVER blocks, fail-open.
- **GK-08 `session_writeback`** — on Stop, re-indexes the current repo into
  `~/.claude/state/graphify/` (bounded: repos > 4000 md files defer). Fail-open,
  never blocks session close.
- **ADS auto-documentation** — on Stop, writes `docs/{prd,arch,constitution,
  changelog}` for changed modules. Never stages/commits; fail-open.

## Verify it worked (post-sync done-gate)

1. `Compare-Object (gc <canonical>) (gc <live>)` → no output = **IN SYNC**.
2. In an indexed repo, run a Grep → the Graph-First advisory appears in context.
3. Trigger Stop (or `/kclear`) → `~/.claude/state/graphify/writeback.log` gets a
   new receipt and `graphify_global.json` `updated_at` advances.
4. `python tools/scheduled_task_health.py` → 0 FAILING (sync broke nothing).
5. `python tests/test_graphify_live.py` → `GRAPHIFY_LIVE_PASS=3/3`.

## Rollback (if anything misbehaves)

```powershell
Copy-Item "C:\Users\User\.claude\hooks\hook-dispatcher.js.pre-graphify.bak" `
          "C:\Users\User\.claude\hooks\hook-dispatcher.js" -Force
```
Restores the exact prior live dispatcher. All three hooks fail-open, so even
without rollback a hook error degrades to a no-op, never a broken tool or Stop.

*Ref: [[graphify_live_scs_c72]] (SCS C72). Drift trap: T-HOOK-DISPATCHER-DRIFT-001
in [[graphify_hard_rules]].*
