---
title: MC-ING-5 — claude-mem reality audit + repair runbook
generated: 2026-04-25
status: research-complete · install state was already non-zero
verdict: REPAIR-OR-RETIRE — defer activation until worker proven stable
---

# MC-ING-5 — claude-mem Reality Audit

The original prompt assumed a fresh `npx claude-mem install`. The reality on disk is more interesting: claude-mem **was installed in March, captured ~5 MB of session data over ~6 days, then the worker died and the plugin got disabled**. This audit documents the actual state and gives you a deterministic decision path.

## 1. Disk inventory (verified `ls`/`Read` results)

| Path | Status | Last modified | Size / Notes |
|------|--------|--------------|--------------|
| `~/.claude/plugins/marketplaces/thedotmack/` | Installed | 2026-03-04 11:27 | Full source clone, v10.4.1 |
| `~/.claude/plugins/cache/thedotmack/claude-mem/` | Cached | — | Plugin runtime cache |
| `~/.claude-mem/claude-mem.db` | Stale | 2026-03-06 14:04 | 958 KB — captured sessions |
| `~/.claude-mem/claude-mem.db-wal` | Stale | 2026-03-10 13:42 | 4.3 MB WAL — never flushed |
| `~/.claude-mem/chroma/` | Stale | 2026-03-10 14:04 | Vector index dir |
| `~/.claude-mem/observer-sessions/` | Stale | 2026-03-04 11:34 | Session capture buffer |
| `~/.claude-mem/logs/` | Active | 2026-04-23 17:57 | 30 log files Apr 14 → Apr 23 |
| `~/.claude-mem/.worker-start-attempted` | Empty marker | 2026-03-10 13:59 | Worker startup tried, never succeeded |
| `~/.claude-mem/settings.json` | Configured | — | Full config (sonnet-4-5, port 37777, etc.) |

## 2. Plugin enablement (verified from `~/.claude/settings.json` line 236)

```json
"enabledPlugins": {
  "claude-mem@thedotmack": false,
  ...
}
```

**Currently disabled.** Not just uninstalled — registered, configured, then turned off.

## 3. Why it's broken (verified from logs)

Every recent log file reports the same failure mode. From `claude-mem-2026-04-23.log` (most recent):

```
[2026-04-23 17:57:52.937] [INFO ] [SYSTEM] Claude-mem search server started
[2026-04-23 17:57:53.141] [ERROR] [SYSTEM] Worker not available {"workerUrl":"http://127.0.0.1:37777"}
[2026-04-23 17:57:53.143] [ERROR] [SYSTEM] Tools will fail until Worker is started
[2026-04-23 17:57:53.144] [ERROR] [SYSTEM] Start Worker with: npm run worker:restart
```

Same pattern in `2026-04-22`, `2026-04-21`, `2026-04-20`, going back. **The search server side starts fine; the worker (which writes to ChromaDB and SQLite) never comes up.** Something — likely a shell hook or MCP probe — keeps reattempting the search server but the worker is dead.

The DB was last successfully written to in early March; nothing has been captured for ~46 days even though the install is technically present.

## 4. Hook collision matrix (real, not predicted)

Power Pack's hook surface (verified from `~/.claude/settings.json`):

| Event | Power Pack hooks (count) | Critical timeouts |
|-------|--------------------------|-------------------|
| `PreToolUse` | 7 (hook-dispatcher, secret-scanner, quality-gate, process-sandbox, gatekeeper-semantic, anti-thrash, ovo-push-gate) | 15s + 5s + 5s + 3s + 5s = ~33s budget |
| `PostToolUse` | 3 (kg-sync-hook, hook-dispatcher, tty-restore) | 5s + 30s + 5s = 40s |
| `Stop` | **7** (zero-issue-gate **60s**, kobiiclaw-autoresearch, trace-flusher 15s, session-summary, scaffold-auditor 10s, lazarus-heartbeat 3s, lazarus-snapshot 10s) | **~98s worst-case** |
| `UserPromptSubmit` | 2 (hook-dispatcher, correction-guard) | 10s + 5s = 15s |
| `SessionStart` | 2 (lazarus_revive.py, token-shield-refresh) | 5s + 3s = 8s |

claude-mem's hook surface (per WebFetch + plugin manifest):

| Event | claude-mem behavior |
|-------|---------------------|
| `SessionStart` | Initialize session capture; load context observations (~50 by default) |
| `UserPromptSubmit` | Inject memory context into the user prompt |
| `PostToolUse` | Record tool execution to SQLite |
| `Stop` | Trigger semantic compression via Sonnet-4-5 (Claude Agent SDK call — variable latency) |
| `SessionEnd` | Finalize session data |

Per-event collision risk:

| Event | Conflict risk | Why |
|-------|--------------|-----|
| `SessionStart` | **LOW** | Independent: `lazarus_revive.py` reads pending_resume, claude-mem loads observations from its own DB. No shared file paths. |
| `UserPromptSubmit` | **MEDIUM** | Both want to influence the prompt. `hook-dispatcher` runs Power Pack sub-hooks first; claude-mem injects context observations. Order matters but neither rewrites the other's payload. Verifiable by inspecting prompt hook output ordering. |
| `PostToolUse` | **LOW** | Different sinks. `kg-sync-hook` writes to `_knowledge_graph/`; `tty-restore` resets stty; claude-mem writes to its own SQLite. |
| `Stop` | **HIGH** | Already 7 hooks with ~98s timeout budget. Adding claude-mem's Sonnet-4-5 compression call on every Stop pushes total Stop latency into 2-3 minutes. Also: **semantic overlap** with `lazarus-snapshot` (both capture session state, write to different paths but represent the same intent). |
| `SessionEnd` | **NONE** | Power Pack does not register `SessionEnd`. claude-mem owns this event uncontested. |

The single significant risk is **Stop-hook latency stacking**. Everything else is parallel-safe.

## 5. Configuration audit (verified from `~/.claude-mem/settings.json`)

Already-set values worth knowing:

| Key | Value | Note |
|-----|-------|------|
| `CLAUDE_MEM_MODEL` | `claude-sonnet-4-5` | Compression model — not an issue, just bills against Owner's quota |
| `CLAUDE_MEM_WORKER_PORT` | `37777` | Local HTTP worker port — verify nothing else binds it |
| `CLAUDE_MEM_SKIP_TOOLS` | `ListMcpResourcesTool,SlashCommand,Skill,TodoWrite,AskUserQuestion` | **Already excludes Skill calls** — no Skill-noise pollution in the memory store |
| `CLAUDE_MEM_CONTEXT_OBSERVATIONS` | `50` | Injects 50 past observations per session — substantial context spend |
| `CLAUDE_MEM_MAX_CONCURRENT_AGENTS` | `2` | 2 parallel compression workers |
| `CLAUDE_MEM_CHROMA_ENABLED` | `true` | Vector index active |
| License | AGPL-3.0 | Local use is fine; redistribution / network-service exposure triggers AGPL |

## 6. Three execution paths

### Path A — Repair existing v10.4.1

Cheapest experiment. Steps the **Owner runs via `!`** (sandbox-blocked otherwise):

```bash
# 1. Restart the worker per the log's own instruction
!cd ~/.claude/plugins/marketplaces/thedotmack && npm run worker:restart

# 2. Confirm the worker is listening
!curl -s http://127.0.0.1:37777/health || echo "WORKER_DOWN"

# 3. If healthy, flip the plugin enable bool
!python -c "import json,os; p=os.path.expanduser('~/.claude/settings.json'); d=json.load(open(p)); d['enabledPlugins']['claude-mem@thedotmack']=True; open(p,'w').write(json.dumps(d,indent=2))"
```

Pros: minimal change, preserves March DB. Cons: 2 majors behind; bug that killed the worker may still be present.

### Path B — Clean upgrade to v12.0.0

```bash
# 1. Archive existing data
!mv ~/.claude-mem ~/.claude-mem.backup-$(date +%Y%m%d)

# 2. Disable old plugin (already disabled, but make sure)
# Already done: claude-mem@thedotmack=false in settings.json

# 3. Reinstall fresh
!npx claude-mem@latest install

# 4. Verify the new install registers cleanly
!cat ~/.claude-mem/settings.json | head -20
!curl -s http://127.0.0.1:37777/health || echo "WORKER_DOWN"

# 5. Enable the plugin
# Same json edit as Path A step 3
```

Pros: gets v12 features, fresh DB. Cons: loses March data (probably fine — it's stale).

### Path C — Retire entirely

```bash
# Archive and uninstall
!mv ~/.claude-mem ~/.claude-mem.archived-$(date +%Y%m%d)
!rm -rf ~/.claude/plugins/marketplaces/thedotmack
# Then remove the enabledPlugins entry from settings.json
```

Recommended IF: you don't trust the Stop-hook latency stack to absorb claude-mem, OR if our existing `lazarus-snapshot` + `MEMORY.md` engine is enough.

## 7. Recommended path

**Path B (clean upgrade) — but run it next session, not this one.**

Reasoning:
- Path A has unknown root cause for the dead worker — repairing without diagnosing risks a re-break
- v10 → v12 is 2 majors; install changes have likely improved
- The March DB is too stale to be valuable (all from one week of testing)
- Backup-then-fresh-install is reversible

**Don't do this in the same session you do real work** — the install will run a Sonnet-4-5 compression on session end; you don't want that on a critical workflow.

## 8. Token-benchmark methodology (honest version)

Claim: "80% token reduction" is the project's marketing line.

**Real measurement plan:**
1. Pick 3 representative workflows (e.g. one /audit-all run, one feature implementation, one debug session).
2. **Baseline (claude-mem disabled):** run each workflow in 3 separate sessions. Capture tokens-used per session via Claude Code's status line / billing dashboard.
3. **Activated (claude-mem enabled, after install + 5 priming sessions to populate the memory):** run the same 3 workflows.
4. Compute: `(baseline_avg - activated_avg) / baseline_avg`. Report the actual percentage with N=3 std-dev.

This needs ~10 sessions of disciplined data collection. **Cannot be done in one turn.** Anyone reporting an 80% number from a single before/after run is selling you a single anecdote, not a measurement.

## 9. Stop-hook latency mitigation (if Path B is chosen)

Adding claude-mem's compression to a Stop chain that already runs ~98s is risky. Two mitigation options:

1. **Reorder + parallelize:** drop `lazarus-snapshot` from blocking Stop; run it as a `PostToolUse(Stop)` shim that fires-and-forgets. Power Pack's `lazarus-snapshot.js` is 244 lines, well-bounded; it can be made async-spawn.
2. **Conditional execution:** add a Stop-hook gate that skips claude-mem compression if the session was <5 tool calls (i.e. nothing meaningful happened). This costs a 100ms gate hook in exchange for skipping the 30-60s compression on noise sessions.

These are real follow-up MCs, not part of MC-ING-5 itself.

## 10. Decision

| Item | Status |
|------|--------|
| Install present | YES (v10.4.1) |
| Install working | NO (worker dead since ~Mar 10) |
| Hook collisions | LOW except Stop-latency stacking (1 HIGH) |
| Owner action needed | YES — run `!` commands to repair/upgrade |
| MC-ING-5 closeable this session | NO — needs Owner-side commands first |

**Verdict for this turn: A** — audit complete, three paths documented, blocked on Owner-run commands per the policy rail. Next session: post-install verification + worker health check + enabled-state collision test.

## 11. What changed from the original MC-ING-5 plan

The roadmap committed in `c7eb990` recommended "EXECUTE NEXT SESSION — `npx claude-mem install` + collision audit". Reality on disk: **install was done in March, audit can be performed now without re-running install**. The collision audit is THIS document. The actual install/upgrade decision is Owner's call between Path A / B / C.

Sources:
- [github.com/thedotmack/claude-mem](https://github.com/thedotmack/claude-mem) (verified v10.4.1 plugin manifest, AGPL-3.0)
- `~/.claude/settings.json` line 236 (plugin enablement bool)
- `~/.claude-mem/logs/claude-mem-2026-04-{14..23}.log` (worker-down evidence)
- `~/.claude-mem/settings.json` (configuration values)
