# Cold-Boot Evidence -- Playwright MCP Plugin Resilience

**Date:** 2026-05-31T14:15:00Z
**Build:** BL-PLAYWRIGHT-001 (Option A sealed 2026-05-31)
**Result:** STRICT PASS (11/11 V-gates + verify_spp probe + commit ladder green)

## Empirical timeline

| Step | Tool | Outcome |
|---|---|---|
| Preflight | `git fetch origin` + `git status` | clean on `main`, no behind/ahead |
| PASO 0 diag | `Get-CimInstance Win32_Process` | 5-6 node.exe @playwright/mcp procs alive |
| PASO 0 diag | system-reminder ambient | `mcp__plugin_playwright_*` tools DISCONNECTED |
| PASO 0 diag | `~/.claude/settings.json:460` grep | `enabledPlugins.playwright@claude-plugins-official: true` |
| PASO 0 diag | `claude_desktop_config.json` grep | NO playwright entry (only n8n-full + video-analyzer) |
| **Architecture decision** | Owner-approved Option A | killer + watchdog + healthcheck, no settings.json edit |
| M0 | `vault/knowledge_base/playwright-transport-repro.md` (3911 B) | committed 146af44 |
| M1 | `tools/playwright_stale_killer.ps1` (3079 B, ASCII) | DryRun PASS (5 procs, 11min idle, would-kill 5) -- committed 146af44 |
| M2 | `tools/playwright_watchdog.ps1` (6484 B, ASCII) | -Action status PASS (WARN: not installed, 5 procs alive) -- committed b6db224 |
| M3 | `tools/check_playwright_mcp.py` (5409 B, ASCII output) | rc=0, 5 procs detected, watchdog WARN -- committed f0a0282 |
| M4 | `vault/knowledge_base/ukdl-universal.md` +78 lines | PR-PW-001 + T-PW-001 markers present -- committed db3f93c |
| M5 | `modules/pp_agents/signals/health.py` +58 lines | `check_playwright_mcp_plugin()` returns `{'status': 'stale_risk', 'count': 5, ...}` -- committed e9d7cfc |
| M6 | `tools/test_playwright_resilience.py` (171 lines, 11 V-gates) | 11/11 PASS in test run -- committed b2cbb30 |
| M7 | `tools/verify_spp.py` +3 lines (new row) | `--row playwright-resilience` STRICT PASS 1/1 in 7.05s -- committed 451fa1c |
| M8 | `knowledge_vault/core/apex-completion-standard.md` +v12 axis | C20 MCP-Plugin-Resilience-by-default sealed |

## V-gate detail (test_playwright_resilience.py)

```
================================================================
PLAYWRIGHT MCP RESILIENCE TEST -- BL-PLAYWRIGHT-001
================================================================
  PASS  V-PW-KILLER-EXISTS      (3079 bytes)
  PASS  V-PW-WATCHDOG-EXISTS    (6484 bytes)
  PASS  V-PW-CHECK-EXISTS       (5409 bytes)
  PASS  V-PW-REPRO-DOC          (3911 bytes)
  PASS  V-PW-UKDL-PR            (PR-PW-001 marker present)
  PASS  V-PW-UKDL-TRAP          (T-PW-001 marker present)
  PASS  V-PW-PLUGIN-SIGNAL      ({'status': 'stale_risk', 'count': 5, ...})
  PASS  V-PW-CHECK-RUNS         (rc=0, status banner present)
  PASS  V-PW-WATCHDOG-STATUS    (rc=0, output contains state)
  PASS  V-PW-KILLER-DRYRUN      (rc=0, log mtime advanced: True)
  PASS  V-BASELINE-INTACT       (modules.pp_agents.signals.health: import OK)

RESULT: 11 PASS / 0 FAIL (11 total)
```

## Owner activation (one-shot, post-push)

```powershell
# From PP repo root, one time:
powershell -File tools\playwright_watchdog.ps1 -Action start

# Verify:
powershell -File tools\playwright_watchdog.ps1 -Action status
# Expected: "OK: Watchdog ACTIVE"

# If disconnected right now (manual quick-fix):
powershell -File tools\playwright_stale_killer.ps1
# Wait ~3s, then retry the Playwright command.
```

## Commit ladder (scoped, NO git add -A)

```
146af44  feat(playwright): stale_killer + transport-repro empirical diagnosis
b6db224  feat(playwright): watchdog.ps1 -- Task Scheduler auto-install
f0a0282  feat(playwright): check_playwright_mcp.py plugin-aware health check
db3f93c  docs(ukdl): PR-PW-001 + T-PW-001 playwright transport resilience
e9d7cfc  feat(monitor): playwright plugin signal in health.py
b2cbb30  test(playwright): 11/11 V-PW-* resilience gates
451fa1c  feat(verify-spp): playwright-resilience probe row
<M8 pending>  docs(apex): v12 MCP-Plugin-Resilience axis + cold-boot evidence
```

## Non-regression note

This work touched **0 files** outside the PP repo. No mutation to
`~/.claude/settings.json`, `~/.claude/commands/`, `~/.claude/hooks/`,
or `claude_desktop_config.json`. No changes to existing tools/scripts
beyond the one append to `verify_spp.py` rows_spec and the one append
to `health.py` (both purely additive).

verify_spp baseline pre-existing STRICT FAILs (mirror-parity,
drift-report, paths+secrets, rtk-fusion, l3-engine) are **NOT**
regressions caused by this work; they pre-date BL-PLAYWRIGHT-001 and
are documented in the existing umbrella output.
