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
