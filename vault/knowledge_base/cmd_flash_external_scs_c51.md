# SCS C51 — windowsHide on ALL spawn paths (external sources)

Sealed 2026-06-23. Extends F0 (commit b144eba, repo-scoped) and fulfills the
"SCS C48 addendum" the cmd-flash plan requested (C48/kclaude-wrapper was never
sealed, so this is filed as the next sequential SCS). Companion:
`tools/audit_spawn_windows.py`, UKDL T-CMD-FLASH-EXTERNAL-001 +
T-LIVE-ONLY-HOOK-FLASH-001.

## Standard

`windowsHide:true` (Node) / `-WindowStyle Hidden` (PowerShell launcher) is
required on EVERY spawn path that can flash a console on Windows, not just the PP
repo: (1) PP-owned hooks (repo), (2) `~/.claude/settings.json` hook command
launchers, (3) live-only hooks in `~/.claude/hooks/` that have no canonical copy.
`audit_spawn_windows.py --settings --live` is the coverage instrument.

## What was fixed (this host)

- `settings.json:342` orphan-dev-server-reaper: `+ -WindowStyle Hidden` (backup
  `settings.json.bak.20260623-*` taken first). SessionEnd flash closed.
- `~/.claude/hooks/bug-hunter-learning.js:127`: `execSync('git status
  --porcelain')` `+ windowsHide:true`. This is the per-PROMPT culprit — it is
  registered directly in settings.json PostToolUse/Bash, so it fired (and
  flashed) on EVERY Bash tool call.
- `~/.claude/hooks/zero-issue-gate.js:132`: `+ windowsHide:true` (live mirror of
  the F0 canonical fix; explicitly allow-listed).
- `audit_spawn_windows.py`: added `--settings` (gates settings.json launchers)
  and confirmed `--live` enumerates global hooks. PP 42/42 + settings 0 fails.

## FLASH SOURCE MAP — verdict

| Source | State |
|---|---|
| settings.json PS launchers (reaper) | FIXED |
| bug-hunter-learning.js (per-Bash) | FIXED |
| zero-issue-gate.js (live mirror) | FIXED |
| dead stdio MCPs (coplay/magic) | ALREADY GONE (`mcpServers:{}`) |
| gsd-context-monitor.js | DORMANT (registered nowhere) |
| vibe-ads statusline chain | already `windowsHide:true` |
| ~9 dispatcher-fired live hooks (kobiiclaw-autoresearch, lazarus-snapshot, quality-skill-gate, prd-keyword-sentinel, baseline-translator, dna-flywheel, lazarus-heartbeat, session-init) | ENUMERATED — batch behind one Owner approval (multi-pane hazard); same `+windowsHide` pattern |
| Claude Code native (Bash/PowerShell tool + hook process spawning), plugin MCP children | NOT PP-CONTROLLABLE — documented honestly |

## Verification

- `audit_spawn_windows.py --settings`: PP 42/42, settings 0 fails, exit 0.
- `node --check` clean on the two live JS edits.
- Empirical zero-flash over 3 consecutive prompts: **Owner-run** (the screen is
  not observable headless). If flashes persist after the 3 confirmed fixes, the
  next suspects are the enumerated dispatcher-fired live hooks (offer to batch)
  then CC-native spawning (uncontrollable).
