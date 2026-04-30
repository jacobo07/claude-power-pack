---
name: resume
description: "Filtered session picker — shows only RESUMEABLE sessions (excludes ones currently LIVE in other Cursor terminals). Use /resume last for legacy single-session warm-up of this project's last_session.json."
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
argument-hint: "[last | <project-id>]"
---

# /resume — filtered session picker

**Default behavior (no args):** runs the Lazarus lister scoped to the
current project with `--exclude-live`, so any session currently open in
another Cursor terminal of THIS or any other window is filtered out of the
picker. You only see CLEAN / CRASHED / UNKNOWN sessions — the ones that
are actually free to revive without conflict.

This addresses the common scenario: you have N terminals open inside one
Cursor window, each running its own claude session. You open terminal N+1
and want to pick a session to revive WITHOUT seeing the N already-attached
ones in the list.

## Argument routing

| `$ARGUMENTS` | Behavior |
|---|---|
| (empty) | Filtered picker (`--exclude-live`) for this project |
| `last` | Legacy single-session warm-up — load `~/.claude/lazarus/<project-id>/last_session.json` directly. See § Legacy warm-up below. |
| `<project-id>` | Filtered picker scoped to that project |

## Default path — filtered picker

When `$ARGUMENTS` is empty:

!`python ~/.claude/skills/claude-power-pack/tools/lazarus_revive_all.py --mode auto --exclude-live --since 7d`

The lister enumerates `~/.claude/projects/<project-id>/heartbeats/<sid>.lock`
files and `/tmp/claude-ctx-<session_id>.json` metric files, classifies each
session as CURRENT / LIVE / CRASHED / CLEAN / UNKNOWN, and with
`--exclude-live` drops CURRENT + LIVE rows. The remaining table is the
"free pool" — sessions you can revive with `claude --resume <sid>`
without colliding with another open terminal.

Read the table verbatim, then surface the recommended `cd <path> && claude
--resume <sid>` line for whatever the user picks. Do NOT pre-select.

## Live-detection mechanism (BL-0010)

A session is LIVE iff:
- its heartbeat lock file (`~/.claude/projects/<project-id>/heartbeats/<sid>.lock`) has mtime within `--live-window` (default 300s), OR
- its statusline metric file (`/tmp/claude-ctx-<session_id>.json`) has mtime within `--current-window` (default 90s)

A session is CURRENT iff it's the freshest heartbeat in the cwd's project AND `_THIS_ session matches`. The lister uses statusline + heartbeat redundantly so a single missed write doesn't downgrade a real LIVE session to CRASHED.

Why this works: every active claude session writes the statusline metric
file every ~5 sec via `gsd-statusline.js`. If the file is fresh, the
terminal is alive. If stale > 5 min, the session crashed or exited.

## Legacy warm-up — `/resume last`

When `$ARGUMENTS` is `last`:

1. Read `~/.claude/lazarus/{project-id}/last_session.json`. If missing, fall back to `~/.claude/lazarus/global_index.json` and report which project had the most recent session.
2. Capture current git state: `git rev-parse --abbrev-ref HEAD`, `git status --porcelain`, `git log --oneline -5`.
3. Read `snapshot.session_log_path` (last 30 lines) for the action timeline.
4. Read `snapshot.active_plan` if it points to an existing file.
5. Read `~/.claude/projects/{project-id}/memory/MEMORY.md`.
6. Emit the structured restoration report (see § Output format below).

## Output format — `/resume last`

```markdown
## Session Restoration (Lazarus Protocol)

**Last session:** {timestamp} ({age} ago)
**Branch:** {branch}
**Uncommitted:** {file list}

### Last Intent
{last 5 tool descriptions from snapshot.last_intent}

### Active Plan
{plan file path and summary if exists}

### What Changed Since Last Session
- {new commits}
- {files added/removed from uncommitted}

### Memory Context
{relevant MEMORY.md entries}

### Recommended Next Action
{Based on plan + git state}
```

## Notes

- Snapshot creation: `lazarus-snapshot.js` Stop hook on every session end.
- Snapshots stored per-project at `~/.claude/lazarus/{project-id}/last_session.json`.
- Global index at `~/.claude/lazarus/global_index.json` tracks most-recent across all projects.
- Snapshots older than 30 days auto-pruned.
- For multi-project listing: use `/lazarus all` (shows EVERY project, includes LIVE rows for cross-window context recovery).
- For repo-scoped listing including LIVE rows: `/lazarus all --include-current` (rarely needed).

## Hardware Law

**BL-0010** (sealed in `vault/baseline_ledger.jsonl`): `/resume` default flow
MUST filter LIVE sessions. Showing a picker that includes already-attached
sessions is a UX failure — the user expects "resume" to mean "pick something
that isn't already running".
