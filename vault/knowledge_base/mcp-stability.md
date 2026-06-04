# MCP Stability -- BL-MCP-STABILITY-001 (sealed 2026-06-04)

> "Nunca mas -32000. Nunca mas desconexion silenciosa."
> Reality contract: `/mcp` shows servers CONNECTED; disconnects are detected
> and recovered (where architecturally possible) before the Owner notices.

## FASE -1 forensic finding (the premise correction)

The request assumed **three identical `-32000` failures** fixable by **one
universal watchdog + launcher**. Forensics disproved this:

| Server | Mechanism | Reality | Correct fix |
|---|---|---|---|
| **playwright** | `enabledPlugins` plugin (loader owns lifecycle) | transport-stale (procs alive, IPC dead) | **external watchdog WORKS** -- already built (T-PW-001) |
| **magic** (`magic-ui`) | `mcpServers` **stdio** (claude owns the pipe) | process DEAD -> `-32000` | **config + Claude-side reconnect**; external relaunch CANNOT help (T-MCP-RECONNECT-001) |
| **coplay-mcp** | `mcpServers` stdio | process DEAD | same as magic |
| **notion** | `mcpServers` stdio | HEALTHY | n/a |
| **shadcn** | -- not configured -- | covered by `ui-ux-pro-max` plugin; no standalone server | out of scope (Owner decision) |

**All configured servers are local-spawned-by-client (stdio or plugin); none
are remote SSE/HTTP.** This is decisive: a relauncher can only restart a
*remote* server that the client reconnects to by URL. For a stdio child of
`claude.exe`, only the client can respawn it. See T-MCP-RECONNECT-001.

## The two recovery models (do not mix them)

1. **Plugin (playwright):** loader respawns clean transport on next tool use.
   Killing stale procs IS recovery. -> `tools/playwright_watchdog.ps1`
   (Task Scheduler, every 8 min, reaps procs idle >= 10 min). TRUE hands-off
   auto-recovery. The Owner never has to act.
2. **stdio mcpServer (magic, coplay, notion):** child of `claude.exe`. External
   relaunch = orphan, not reconnection. Recovery is DETECTION + ADVISORY +
   Claude-side `/mcp` reconnect (or restart). Death-mode is being classified
   via telemetry before any config fix is asserted (T-MCP-IDLE-001 PENDING).

## Components shipped

- `tools/mcp_health_check.py` -- unified probe (both mechanisms). Reuses the
  sealed `check_playwright_mcp.py`. Output: `HEALTHY / DEAD / NEEDS_WATCHDOG`
  per server. Flags: `--json`, `--source <tag>`, `--no-log`, `--strict`.
- `tools/verify_mcp_health.py` -- verify_spp row `mcp-health`. 5 STRICT V-gates
  on PP-controllable machinery (tool present, detection works, watchdog
  installed, telemetry active). stdio liveness is ADVISORY (operational, not a
  PP defect -- no-classified-FAILs doctrine).
- `vault/telemetry/mcp_health/mcp_state.jsonl` -- append-only classification
  log (M3); one row per run, used to seal T-MCP-IDLE-001 empirically.
- Playwright leg reuses the existing T-PW-001 tooling (watchdog now INSTALLED).

## M5 -- SessionStart detection (Owner registration step)

Per HR-001, the agent does NOT write hook registrations into
`~/.claude/settings.json` in auto-mode. To get an at-startup MCP advisory,
the Owner registers this hook ONCE:

```jsonc
// ~/.claude/settings.json  ->  "hooks" -> "SessionStart": [ ... add: ]
{
  "type": "command",
  "command": "python \"C:/Users/User/.claude/skills/claude-power-pack/tools/mcp_health_check.py\" --source session_start"
}
```

It runs the probe at session start, appends a telemetry row, and prints any
DEAD-server reconnect advisory + a watchdog-not-installed warning. It mutates
nothing and is fail-open (exit 0 without `--strict`).

Until registered, run manually anytime:
`python tools/mcp_health_check.py` (or `--strict` for a gate).

## Quick operator playbook

- **A server shows `-32000` / disconnected right now:**
  - playwright -> `powershell -File tools\playwright_stale_killer.ps1`, then
    retry the Playwright tool (loader respawns clean transport).
  - magic / coplay / notion (stdio) -> `/mcp` in Claude Code -> reconnect the
    server. If that fails, restart Claude Code. NEVER launch it externally.
- **Verify the whole MCP surface:** `python tools/mcp_health_check.py`
- **Gate it:** `python tools/verify_spp.py --row mcp-health`

## SCS C37 -- MCP-Stability-by-default

Watchdog active for the externally-recoverable MCP (playwright); SessionStart
detection (Owner-registered) + telemetry classification for stdio MCPs;
`verify_spp` `mcp-health` row fails if the PP-controllable machinery is absent
(NOT if a stdio server is merely disconnected -- that is advisory). The
universal-watchdog premise is rejected in doctrine: stdio `-32000` is
Claude-side-recoverable only (T-MCP-RECONNECT-001).
