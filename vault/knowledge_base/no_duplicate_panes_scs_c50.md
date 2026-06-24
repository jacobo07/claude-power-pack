# SCS C50 — No-Duplicate-Panes-by-default

Sealed 2026-06-22. Companion: `docs/cursor-startup-and-reload.md`,
`feedback_cursor_reload_persistent_sessions_pane_map.md`,
extension `extension/`, `tools/build_pane_map.ps1`.

## Standard

One restore mechanism active at a time. When
`terminal.integrated.enablePersistentSessions: true`, the persistent pty host is
the **primary** reload restorer; `.vscode/tasks.json` `folderOpen` restore tasks
are a **cold-start fallback only** and must not fire on reload. Any script that
launches `claude --resume` is deduplication-guarded and fail-open (if the
liveness check fails, launch anyway — never lose a pane).

## Root cause (empirical, this host)

Cursor settings: `enablePersistentSessions: true`, `restoreTerminals: false`,
`task.allowAutomaticTasks: "on"`. Each active repo's `.vscode/tasks.json` carried
N `CPC-Restore` tasks, every one `runOn: folderOpen`, launching
`kclaude.bat --resume <sid>`. On a **Reload Window** both restorers fired:

1. persistent sessions reconnected the N live terminals (the real panes);
2. `allowAutomaticTasks:"on"` + `folderOpen` spawned N more `--resume` terminals.

→ 2× terminals per session. The duplication is *two restorers*, not a reload
fault. `folderOpen` is a binary trigger — it cannot distinguish reload (terminals
alive) from cold start (terminals gone), so a single dumb task layer can satisfy
reload-clean OR cold-restore, never both.

## Fix applied

`%APPDATA%\Cursor\User\settings.json`: `task.allowAutomaticTasks` `"on" → "off"`
(timestamped backup taken first). Global, reversible, touches zero repo files —
honors "don't mutate live repos' tasks.json mid-session" (multi-pane hazard).
Reload now restores exactly N via persistent sessions; cold start restores
manually via the PP Sessions panel / `pane_map.md`.

## Verification

- Settings edit confirmed: line reads `"task.allowAutomaticTasks": "off",`;
  file remains valid JSONC; `enablePersistentSessions` still `true`.
- E1 (reload → N == N pre-reload, zero duplicates): **Owner-run** — Reload Window
  is a UI-only action with no CLI, inherently Owner-driven.
- E2 (cold start auto = pane_map count): intentionally NOT auto under this fix;
  manual via PP Sessions. Full cold-start auto without reload duplication is the
  guarded-extension follow-up (Option C).

## Option C — SHIPPED 2026-06-24 (615ebbb)

Extension-as-sole-restorer, implemented in the PP Sessions extension (v0.2.0).
On activate (after a settle delay) it reads `pane_map.json` and counts live
`vscode.window.terminals`: on a cold start (zero live terminals) it launches
`claude --resume <sid>` for this repo's `live` panes; on a reload (terminals
already reconnected by persistent sessions) it launches NOTHING — the
terminal-count guard is what keeps reload duplicate-free. Pure decision in
`extension/src/restore_guard.js` (vscode-free), wired by
`extension/src/extension.js`. Setting `ppSessions.autoRestoreOnColdStart`
(default true) is the reversible kill switch; command
`PP Sessions: Restore cold-start panes now` (force-bypasses the terminal guard)
tests it without a real cold start.

This is why "History restored" still appeared after dae50c7: every active repo
already had a `tasks.json`, but `allowAutomaticTasks:"off"` gates the folderOpen
layer off on cold start too — so nothing auto-restored. Option C is the cold-
start restorer that does NOT re-introduce reload duplication. A second
`tasks.json` generator (e.g. teaching `build_pane_map.ps1` to write tasks.json)
is the WRONG fix — it re-creates the two-restorer race this card sealed.

Verification: `node tools/test_restore_guard.js` → RG_PASS=10/10 (cold-start
launch, reload guard, dedupe, cwd-filter, non-live exclusion, opt-out, path
norm). E1 (cold start → exact resume, no "History restored") and E2 (reload →
N == N, zero duplicates) remain Owner-run UI checks after
`tools/install_pp_extension.ps1`.
