# RAM Optimization Sprint — Revised Plan (post-forensics)

**Date:** 2026-06-04
**Status:** awaiting Owner approval (FASE 2)
**Branch:** main | REMOTE_DELTA 0 0

## FASE -1 — Forensic findings (empirical, this session)

| Source | Measured | Controllable? |
|---|---|---|
| claude.exe (3 procs) | WS 25,089 MB / **Private 65,167 MB** (2 main procs ~32 GB each) | ❌ native V8 heap |
| node.exe (4 procs) | 378 MB at boot → **9.7 MB steady-state** (self-cleaned) | ✅ already clean |
| python.exe | 2.2 MB, 0 zombies | ✅ nothing to reap |
| **PP-controllable total** | **11.9 MB** | ✅ |
| CPC-OS registry | 44.2 KB — 115 panes (112 stale / 3 active / 0 dead) | ✅ prune |
| Walk/state caches | 190.5 KB total (skill-index 31.8 KB) | ✅ cap |
| TIS jsonl (this project, top-level) | 102.9 MB / 73 files (disk, not RAM) | ⚠️ behavioral |

**Verdict:** claude.exe is >99.9% of the controllable-vs-uncontrollable RAM split and grew
5.9 GB → 25 GB resident (65 GB committed) within one session. PP overhead is a flat ~12 MB.
The only lever on the GB-scale number is **context reduction** (`/kclear` / `/compact` / restart).

### Premise corrections (plan code is a hypothesis)
- **R3 (hub `unref()` audit) — already satisfied.** `session_start_hub.js` spawns are all
  `detached:true, stdio:'ignore', child.unref()` (lines 212-218); logged variant `closeSync`s (285-287). DROP.
- **R4 (lazarus purge kills zombies) — false.** `lazarus_orphan_purge.py` retires orphan
  `.jsonl.live` *disk files*, not RAM processes. 0 python zombies found. DROP.
- **R7 (RAM threshold on `budget_monitor.py`) — wrong tool.** It is a `$`-credit runway tracker
  with zero RAM code. Pre-crash RAM monitor is a NEW probe.

## REVISED PLAN

### BLOQUE A — Benchmark (the Reality Contract number)
- **A1** `bench_all.py` gains a `ram_footprint` benchmark via `Get-Process` subprocess (no psutil,
  no CIM — CIM hangs under `-NonInteractive`). Records: `claude_ws_mb`, `claude_private_mb`,
  `pp_overhead_mb` (node+python). TARGETS: `pp_overhead_mb` ≤ 300.
- **A2** `verify_spp.py` gains `V-RAM-PP-OVERHEAD`: FAIL if node+python > 300 MB.
  claude.exe is NOT gated (uncontrollable).

### BLOQUE B — Pre-crash monitor (the only real RAM lever)
- **B1** NEW `tools/ram_guard.py` (standalone, not bolted onto budget_monitor). Reads claude.exe WS.
  WS > 8 GB → advisory "/kclear recommended" + ensure snapshot. WS > 11 GB → CRITICAL + force
  snapshot now. Honest: advises, cannot kill claude.exe. Wired as Stop hook (advisory, fail-open).
- **B2** `commands/kclear-when.md` helper — when/how, with the empirical 8/11 GB thresholds.

### BLOQUE C — Cheap hygiene (KB-scale, honest about impact)
- **C1** Registry prune: stale panes > 24 h purged on SessionStart. 112 stale → ~3 active. Reclaims ~44 KB.
- **C2** Walk-cache TTL + max-size guard (skill-index.json etc). Currently 190 KB; keep it bounded.

### BLOQUE D — Standards + test
- **D1** `bench_all.py` before/after: baseline = claude WS ~25 GB / PP 12 MB; post = same PP +
  demonstrate `/kclear` dropping claude.exe RAM (the one number that moves).
- **D2** SCS C34 (honest): "PP RAM footprint < 300 MB (currently 12 MB). Registry pruned each
  SessionStart. Walk caches TTL+max-size. claude.exe RAM is native/uncontrollable — only lever is
  the ram_guard /kclear advisory at 8/11 GB."

## STOP #2 pre-declaration
C1-C2 reclaim KB on a 25 GB process → reduction will be **<1%**. Per STOP #2 this will be documented
as the real limit; no marginal-optimization chase. The materially-smaller number is achievable ONLY
via the ram_guard → /kclear cycle (BLOQUE B), which the benchmark will prove.
