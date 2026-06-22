# /kclear — Authoritative Flow Map

**Produced:** 2026-06-22 (restart-kclear recursive deep audit, RONDA 1 A2).
**Verified:** hermetically via `tools/test_restart_kclear.py` (V-KCLEAR-* gates, tmp-root isolation).

> Reality correction (PF-6): `/kclear` is a **checkpoint**, not a RAM-freer. It does
> NOT kill claude.exe and does NOT shrink the V8 heap. RAM is reclaimed by the
> subsequent **native `/clear`** (context reset), which `/kclear` only *suggests*.

## Live path (what actually runs)

```
/kclear (command)
  └─ ~/.claude/commands/kclear.md
       └─ echo '<json>' | python tools/session_checkpoint.py record --stdin
```

### session_checkpoint.py record — the mechanism

| Step | File:concept | Action | Atomicity / edge |
|---|---|---|---|
| 1 | `:257` `find_project_root(cwd)` | Walk up for `.git`/`.claude`/`CLAUDE.md`… (skips `$HOME`) | no marker → resolves to a PARENT project (hermeticity hazard — see gate) |
| 2 | `:266-267` | Write `memory/project_session_handoff.md` | `atomic_write` = mkstemp + `os.replace` |
| 3 | `:268` `append_insights` | Append to `_audit_cache/insights.json` | dedup by `SHA256(category\|title\|body)[:16]`; coexists w/ context-watchdog schema |
| 4 | `:272` `update_memory_index` | Rewrite the single `- [Session Handoff …]` line in `memory/MEMORY.md` | prior handoff line dropped, others kept |
| 5 | `:277-286` | Optional `lesson` → append `vault/knowledge_base/session_lessons.md` (≤600 ch) | bootstrapped on first write |
| — | `kclear.md:61` | **Suggest** native `/clear` | the actual RAM-free step (owner action) |

## What /kclear does NOT do (PF-6 corrections)

- **No RAM free / no process kill.** RAM-free belongs to native `/clear`.
- **No work_state save.** Structured `work_state` is saved by the **auto-reset** path, not manual /kclear:
  `context-watchdog.py` (Stop-chain) → `auto_reset_orchestrator.orchestrate()` →
  `context_monitor.assess()` (RAM 20/28 GB + jsonl + turns) → on pressure
  `work_state_saver.save_work_state()` → `~/.claude/state/work_state_<key>.json`.
- **No snapshot.** Crash snapshots are `ram_guard.ensure_snapshot()` / lazarus, not /kclear.

## RAM advisory surface (PF-3/PF-4, deduped)

| Hook | Metric / threshold | Registered | Status |
|---|---|---|---|
| `ram-watchdog.js` | tasklist Mem Usage (private WS) summed; **20480 MB** (was 1500) | Stop-chain:108 | LIVE, coarse backstop |
| `context_monitor` (via `context-watchdog.py`) | `WorkingSet64` 20 GB warn / 28 GB crit + jsonl + turns | Stop-chain:107 | LIVE, **authoritative** |
| `ram-guard-stop.js` → `ram_guard.py` CLI | gaming 8/12, normal 20/28 + snapshot | NOT registered | dormant/orphan-by-design (header-deprecated) |
| `ram_guard.claude_ram_mb()` | library fn | — | LIVE (used by context_monitor) |

Pre-fix: `ram-watchdog.js` fired at 1.5 GB → /kclear advisory on nearly every session
(alert fatigue). The 2026-06-04 sprint's 20/28 GB recalibration had reached only the
orphan (`ram_guard`); R2 raised the live hook to 20 GB so the two no longer double-fire.

## Independence (verified)

`/restart` ⟂ `/kclear`: `session_checkpoint.py` imports neither `cpc_os.restart` nor
`restart_resume`; `restart-claude.ps1` does not invoke `session_checkpoint`. No circular
dependency (V-RESTART-KCLEAR-INDEPENDENT).

## Honest gate (Reality Contract, PF-6)

`V-KCLEAR-RAM-DROPS` would be theater. The defensible gates assert: checkpoint integrity
(handoff + insights written atomically, hermetic tmp root, real tree untouched), the
`/clear` suggestion is emitted, and UKDL T-KCLEAR-RAM-SEMANTICS-001 attributes RAM-free to
native `/clear`. Empirical RAM-delta belongs to a native-/clear measurement.
