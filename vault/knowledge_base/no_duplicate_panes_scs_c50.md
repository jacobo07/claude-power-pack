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

## Follow-up (optional, Option C)

Extension-as-sole-restorer: on activate, diff `pane_map.json` (resumable) against
live `vscode.window.terminals` by cwd, launch `--resume` only for repos with no
live terminal. Satisfies reload-clean AND cold-start-auto. Deferred — it edits
`extension/src` (shipped 2026-06-22, 113099b), so it carries sibling-collision
risk and needs its own session.
