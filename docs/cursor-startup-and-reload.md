# Cursor Startup, Reload & Pane Recovery

Operational notes for reloading Cursor without losing Claude Code panes, and for
making Cursor start clean. Companion to the **PP Sessions** extension
(`extension/`) and the pane-map generator (`tools/build_pane_map.ps1`).

## Reload without the extension popup

There is **no CLI command** that reloads a running Cursor window
(`cursor --reuse-window` only reuses a window to open a path; it does not reload).
To reload (e.g. to activate a freshly-installed extension whose popup was
dismissed):

> `Ctrl+Shift+P` → **Developer: Reload Window**

A reload is safe because:

- `terminal.integrated.enablePersistentSessions: true` — the pty host keeps
  integrated terminals alive across a window reload; running `claude` processes
  survive and reconnect.
- `terminal.integrated.restoreTerminals: false` — the anti-"History restored"
  fix is active.

If a pane ever does come back as a fresh "History restored" session, open the
**PP Sessions** panel and click **Resume** on that pane, or
`PP Sessions: Open pane_map.md` and paste the exact `claude --resume <sid>`.

## No duplicate panes on reload (folderOpen restore tasks)

Persistent sessions alone is non-destructive, but a **second** restorer used to
fire on top of it and double every pane. Each repo's `.vscode/tasks.json` holds
`CPC-Restore` tasks with `runOptions.runOn: "folderOpen"`, and a Cursor reload
re-triggers `folderOpen` when `task.allowAutomaticTasks` is `"on"`. So a reload
produced **two terminals per session**: the persistent (reconnected) one *and* a
fresh `kclaude.bat --resume <sid>` from the task. That is the duplication the
Owner saw — not a reload bug, a *redundant-restorer* bug.

`folderOpen` is a dumb trigger: it cannot tell a reload (terminals alive) from a
cold start (terminals gone). Fix — make persistent sessions the sole reload
restorer by disabling the auto-task layer in
`%APPDATA%\Cursor\User\settings.json`:

```jsonc
"task.allowAutomaticTasks": "off",
```

After this, a reload restores **exactly N panes** (the reconnected ones, no
duplicates). Trade-off: a **cold start** (full quit → reopen, pty host gone) no
longer auto-restores from tasks.json — restore manually from the **PP Sessions**
panel (one-click exact `--resume`) or `pane_map.md`. This matches the standing
model: persistent-sessions + pane_map are the net; reload is Owner-driven.

Re-enabling auto-restore for cold starts *without* re-introducing reload
duplication requires a guarded restorer (extension diffs `pane_map.json` against
live terminals by cwd, launches `--resume` only where no terminal exists) — a
deliberate follow-up, not the dumb `folderOpen` layer.

## Start straight in the editor (no welcome / Agents home)

Cursor opens the welcome / Agents home when `workbench.startupEditor` is unset
(default `welcomePage`). Fixed in `%APPDATA%\Cursor\User\settings.json`:

```jsonc
"workbench.startupEditor": "none",
```

This is the only lever in settings; there is no `cursor.*` key that forces the
Agents view. `window.restoreWindows: "all"` still reopens the previous windows.

## "Last session" terminal order — known limitation

The default terminal profile is `"Last session"`, which runs
`~/.claude/hooks/lazarus-shell-autoresume.bat` (plus slot variants `slot1/2/3`
via `LAZARUS_TERMINAL_KEY`). Which conversation a given terminal slot resumes is
decided by Lazarus' slot→session binding, **not** by a Cursor setting — so a new
"Pane 1" terminal can resume the most-recently-modified session rather than the
original Pane 1. This ordering is not configurable from Cursor settings.

**Deterministic workaround:** use the **PP Sessions** panel. It lists every
resumable pane keyed by `session_id` (not by slot order), each with a one-click
exact `claude --resume <sid>`. Pane identity there comes from the transcript on
disk, so it never drifts with slot ordering. Treat PP Sessions as the source of
truth for "which terminal is which conversation", and the `"Last session"`
profile as a best-effort convenience only.
