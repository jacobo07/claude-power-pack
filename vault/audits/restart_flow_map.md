# /restart — Authoritative Flow Map

**Produced:** 2026-06-22 (restart-kclear recursive deep audit, RONDA 1 A1).
**Verified:** empirically via `PP_RESTART_DRY_RUN=1` live dry-run (this host) + `tools/test_restart_and_lag.py` (15/15) + `tools/test_restart_kclear.py`.

> Source of truth = on-disk files, not prior docs. Each step cites file:concept.

## Live path (what actually runs)

```
/restart (command)
  └─ ~/.claude/commands/restart.md
       └─ !powershell ... ~/.claude/scripts/restart-claude.ps1
```

### restart-claude.ps1 — the mechanism (sealed 2026-05-31 evening)

| Step | File:concept | Action | Failure / edge |
|---|---|---|---|
| 1 | `restart-claude.ps1:52` | Capture `CLAUDE_CODE_SESSION_ID` (validates 36-char uuid) | invalid → `$sessionId=$null` → kclaude falls back to `--continue` |
| 2 | `:59-72` | Resolve `claude.exe` (`CLAUDE_CODE_EXECPATH` → PATH → `~/.local/bin`) | none found → `exit 3` |
| 3 | `:75-89` `Get-ClaudePid` | Walk parent chain (≤12) for `claude.exe` PID | not found → write markers, print "type /exit yourself", `exit 0` |
| 4 | `:92-99` | Write SID → `~/.claude/lazarus/kclaude-restart-sid.txt` (ASCII, no newline) | — |
| 5 | `:101-104` | Write flag → `%TEMP%\claude-restart-<pid>.flag` (ASCII) | kclaude.bat watches `claude-restart-*.flag` |
| 5b | `:106-137` | Write `~/.claude/state/restart_pending.json` (cwd+branch+sid+ts+note) **UTF-8 NO BOM** via `WriteAllText`+`UTF8Encoding($false)` | universal fallback marker for non-kclaude panes |
| 6 | `:139-147` | Copy `"<exe>" --resume "<sid>"` to clipboard | fallback for panes not under kclaude |
| DRY | `:166-173` | `PP_RESTART_DRY_RUN=1` → print intent, **skip** injection + fallback kill, `exit 0` | self-test path (used by this audit) |
| 7 | `:175-282` | Open `CONIN$` (CreateFileW) → `WriteConsoleInputW("/exit\r")` into the **shared console input buffer** | injection<=0 events OR no console → fallback |
| 8 | `:284-289` | **Fallback only:** `Stop-Process -Id <pid> -Force` (yellow `[FALLBACK]` warning) | reached only when CONIN$ injection fails |

### Resume (after claude exits)

- **kclaude.bat parent (zero-keystroke):** `~/.claude/kclaude.bat` scans `claude-restart-*.flag`, reads SID file, runs `claude --resume <sid>` (or `--continue` if no SID) in the SAME pane.
- **Universal fallback (any pane):** next SessionStart, `session_start_hub.js::hookRestartResume` reads `restart_pending.json`; if cwd matches AND < 5 min old → emits an `additionalContext` continuation HINT and consumes the marker. BOM-tolerant on read.

## SessionStart consumers of restart state

| Hook | Reads | Registered | Status |
|---|---|---|---|
| `session_start_hub.js::hookRestartResume` | `state/restart_pending.json` | settings.json:313 (hub) | **LIVE** — cwd-matched hint + consume |
| `restart_resume.js` (standalone) | `state/restart_pending.json` | NOT registered | reference-only (folded into hub, PF-7) |
| `restart-target-consumer.js` | `lazarus/restart-target.json` | settings.json:285 | **DEAD** — no producer (PF-1); always early-exits |
| `lazarus-janitor.js` (Step 9) | `lazarus/restart-target.json` | (janitor) | **DEAD** prune of a never-produced file (R2-1) |
| `cpc_os/restart.py::restart_intent` | (intent validation) | NO caller | orphan, intent-only-by-design (PF-5) |

## Key invariants (verified)

- **Graceful, not SIGKILL** (UKDL T-RESTART-001): `/exit` via CONIN$, `Stop-Process` is fallback-only. Dry-run proved injection is reached AND skipped without killing the session.
- **Session Safety §1:** `.jsonl` never touched; claude persists per-turn.
- **session_id is NOT preserved across resume by design** → the hub matches by **cwd**, not sid. This is *why* the `restart-target.json` sid-equality self-heal (PF-1) must stay retired, not revived: a revived producer would false-mismatch on every clean restart and spawn a spurious `lazarus-revive`.
- **No-BOM marker contract:** both producers (`restart-claude.ps1`, `compact_rescue.ps1` post-R2-2) write UTF-8 no-BOM.

## Resolved findings

PF-1 (dead self-heal → documented + Owner deregistration step), PF-2 (stale lesson → SUPERSEDED banner), PF-5 (intent-only documented), PF-7 (hub-fold documented), R2-1 (janitor third-reference documented), R2-2 (compact_rescue BOM fixed).
