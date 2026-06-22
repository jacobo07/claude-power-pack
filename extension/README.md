# PP Sessions

A read-only side panel for Cursor / VS Code that lists your **resumable Claude Code
panes** and lets you re-open any of them in the correct repo with one click — the
exact `claude --resume <session_id>`, never a fresh "History restored" session.

## How it works

PP Sessions does **not** derive pane data itself. It reads a single source of truth:

```
~/.claude/state/pane_map.json
```

That file is generated from disk truth (the session snapshot cross-checked against
the actual transcript `.jsonl` on disk) by `tools/build_pane_map.ps1`. The extension
watches the file and refreshes the panel automatically when it changes.

## Panel

Panes are grouped by status:

- **Resumable (active)** — exact `session_id` with a transcript on disk. Click to
  open a terminal in the repo running `claude --resume <id>`.
- **Resumable (old >48h)** — same, but last activity is old (likely already closed).
- **Transcript lost — new chat** — a `session_id` was recorded but its transcript is
  gone; exact resume is impossible, so the action opens a fresh `claude` in that repo.

The status-bar item `PP: N` shows the number of active resumable panes; click it to
focus the panel.

## Commands

- `PP Sessions: Refresh` — re-read `pane_map.json`.
- `PP Sessions: Resume in new terminal` — open the pane (also the click action).
- `PP Sessions: Copy resume command` — copy the exact command to the clipboard.
- `PP Sessions: Open pane_map.md` — open the human-readable recovery map.

## Install

```powershell
pwsh tools/install_pp_extension.ps1
```

Packages the extension to a `.vsix` and installs it into Cursor. A window reload
activates it.
