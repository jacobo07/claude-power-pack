# Playwright MCP Transport Disconnect — Reproducción empírica

**Fecha:** 2026-05-31
**Sealed by:** BL-PLAYWRIGHT-001 (Option A — stale process killer + watchdog)
**Severity:** Operational (interrumpe flujo, no destruye datos — Process Rule, NOT Hard Rule)

## Diagnóstico empírico

Capturado en sesión 2026-05-31:

- **6 procesos `node.exe` vivos** ejecutando `@playwright/mcp/cli.js` desde
  `C:\Users\User\AppData\Local\pnpm\global\v11\...\node_modules\@playwright\mcp\cli.js`.
- **Claude Code runtime: `mcp__plugin_playwright_*` tools = DISCONNECTED**.
  (Confirmado por system-reminder ambient: "MCP server disconnected — do not search for them".)
- Mecanismo de carga: **`enabledPlugins.playwright@claude-plugins-official: true`** en
  `~/.claude/settings.json:460`. NO está en `mcpServers`.
- Root cause: **idle transport IPC disconnect, NOT process crash**.
- Confirmado por:
  - System reminder (Claude Code runtime perspective)
  - PowerShell `Get-CimInstance Win32_Process` (host perspective: procesos vivos)
  - Contradicción entre las dos vistas = transport stale

## Patrón de fallo

```
Owner no usa Playwright N minutos (idle)
    ↓
Transport IPC entre Claude Code SDK y los node.exe playwright procesos se rompe
(razón interna del SDK: keepalive timeout, socket close, pipe drain, etc.)
    ↓
Procesos node.exe siguen vivos pero su transport está muerto
    ↓
Próximo uso de cualquier tool mcp__plugin_playwright_*:
    "MCP disconnected" / "spawn error" / "connection refused"
    ↓
Owner debe recargar Claude Code o esperar plugin auto-restart
```

## Fix sellado (Option A — sealed 2026-05-31)

**Stale-process killer watchdog** que mata procesos playwright con idle > N min
proactivamente. Cuando Claude Code necesita Playwright la próxima vez, el plugin
loader spawnea procesos frescos con transport limpio (< 5s).

**No intentamos**:
- Tocar `enabledPlugins` o `settings.json` (rompe el plugin loader).
- Añadir `mcpServers.playwright` (undefined behavior si plugin + mcpServer coexisten).
- Reconectar el transport roto (no hay API user-facing para eso).

**Implementación**:
- `tools/playwright_stale_killer.ps1` — invocable manual o por watchdog.
- `tools/playwright_watchdog.ps1` — auto-instala en Task Scheduler.
- `tools/check_playwright_mcp.py` — health check ejecutable on demand.

## Por qué NO es Hard Rule

Hard Rules (per CLAUDE.md router) son kill-switches que se aplican antes de:
1. Writes a producción / configs load-bearing
2. Deploys a server live
3. Declarar "done" / commit shipping
4. Install/update de plugins

Este bug es **operational**: interrumpe el flujo del Owner pero no destruye
estado, no afecta producción de otro servicio, no es deploy. Por tanto
clasificación correcta = **Process Rule + UKDL Trap**, no Hard Rule. La
diferencia: Hard Rule = STOP + Owner-reporting; Process Rule = check + fix.

## Recognizer (cómo identificar este bug en el futuro)

Si ves cualquiera de estos síntomas → es **este** bug, aplicar Option A:

1. Tool names con prefijo `mcp__plugin_playwright_*` marcados como disconnected
   en system-reminder ambient.
2. `Get-CimInstance Win32_Process -Filter "Name='node.exe'"` muestra N procesos
   con `@playwright/mcp/cli.js` en CommandLine.
3. El Owner reporta "lleva 5-30 min sin usar Playwright y ahora no responde".
4. Restart de Claude Code arregla el síntoma pero vuelve a pasar.

**Quick fix manual (si pasa AHORA mismo)**:
```powershell
powershell -File tools\playwright_stale_killer.ps1
# Espera 3 segundos → reintenta el comando Playwright
```

## Cross-refs

- `tools/playwright_stale_killer.ps1` — el killer
- `tools/playwright_watchdog.ps1` — el orquestador Task Scheduler
- `tools/check_playwright_mcp.py` — el health check
- `vault/knowledge_base/ukdl-universal.md` §PR-PW-001 + §T-PW-001
- SCS v10 C20 — MCP-Plugin-Resilience-by-default (sealed 2026-05-31)
