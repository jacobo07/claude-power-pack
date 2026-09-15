---
name: lazarus
description: "Multi-session Lazarus restore. Default = current project's last session. /lazarus all = every project, every recent session (use this when reviving multiple windows). /lazarus windows = same as all, alias. (Native /resume remains the per-session picker.)"
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
argument-hint: "[all | windows | fresh | last | <project-id>]"
---

# Lazarus Protocol — Session Resume

Restore the mental model from previous session(s). Zero re-explanation needed.

## Argument routing

| `$ARGUMENTS` | Behavior |
|--------------|----------|
| (empty) / `last` | Single-session warm-up for the **current project** — the legacy flow below. Loads `last_session.json`, captures git state, reads session log + active plan. |
| `all` / `windows` | **Multi-session restore** — runs the new lister to surface every recent session across every project (every Cursor / VS Code / WindowsTerminal window you had open). Use this after a reboot to see what was alive. |
| `fresh` | **Resumeable-only listing for the cwd's project** — runs the lister with `--exclude-live` so every currently-open session (this one + any other Cursor terminal running claude) is filtered out. Use this when you want to pick a session to revive without seeing duplicates of windows you already have open. Same listing as `/resume` (the wrapper command) but scoped to one project. |
| `<project-id>` | Treat as a project-id filter for the multi-session listing (use the sanitized form, e.g. `C--Users-User-Desktop-Cursor-Projects-TUA-X`). |

## `fresh` path

When `$ARGUMENTS` is `fresh`, run:

!`python ~/.claude/skills/claude-power-pack/tools/lazarus_revive_all.py --mode auto --exclude-live --since 7d`

The `--exclude-live` flag drops every row whose status is CURRENT or LIVE — i.e., every session that is currently running in some Cursor window. What's left: CRASHED sessions (lost work to recover), CLEAN sessions (intentionally exited, may want to revive for context), and UNKNOWN. These are the actually-resumeable sessions; pick one and run the suggested `cd "<path>" && claude --resume <sid>` command.

## Multi-session path (when `$ARGUMENTS` is `all`, `windows`, or a project-id)

Run the lister and present its output verbatim — do NOT collapse the per-session table:

!`python ~/.claude/skills/claude-power-pack/tools/lazarus_revive_all.py --mode all --since 24h`

The lister already emits the recommended restoration commands for every LIVE/CRASHED row in its own "Restoration paths" block. Surface that block to the Owner; do not regenerate it manually.

Reading the table:
- `▶` CURRENT — this very session (auto-detected via freshest heartbeat in the cwd's project). **By default this row is filtered out** so the table never suggests reviving the window you're already in. Pass `--include-current` if you need to see it.
- `●` LIVE — heartbeat fresh in the last 5 min, session is currently running in another window
- `✗` CRASHED — heartbeat stale or session in `pending_resume.txt` without a clean exit
- `○` CLEAN — exited cleanly via Stop hook
- `?` UNKNOWN — partial state

Each row carries: session_id, age, branch, uncommitted-file count, terminal hint (PPID), last_tool, and active_plan if any. Under each project header, a `terminal-keys:` line surfaces the `bindings.json` map (e.g. `work→<sid8> | plan→<sid8>`) so you can match logical terminal identity (set via `LAZARUS_TERMINAL_KEY` env var) to the right session, even across Cursor restarts.

Skip rows that are CLEAN — those finished intentionally. The lister's "Restoration paths" already focuses on LIVE (other-window context) and CRASHED (lost work).

### Verifying the restore contract

To prove the chain works without a real crash, run the forensic harness — it builds a synthetic Lazarus state in an isolated temp HOME, asserts CURRENT is filtered, CRASHED gets a resume command, and `--include-current` still excludes the resume suggestion:

```
python ~/.claude/skills/claude-power-pack/tools/lazarus_forensic_test.py
```

20 assertions, exit 0 = green. Use `--verbose` for full lister output, `--keep` to retain the sandbox for inspection.

## Single-session path (legacy `/lazarus` and `/lazarus last`)

## Step 1: Load Lazarus Snapshot

Read the snapshot file for this project. The project ID is derived from the current working directory.

```
~/.claude/lazarus/{project-id}/last_session.json
```

If no snapshot exists for this project, check `~/.claude/lazarus/global_index.json` for the most recent session across all projects and report which project it was in.

## Step 2: Capture Current Git State

Run these commands to compare current state vs snapshot state:

```bash
git rev-parse --abbrev-ref HEAD
git status --porcelain
git log --oneline -5
```

Compare with snapshot's `branch`, `uncommitted_files`, and `recent_commits` to detect what changed since the last session.

## Step 3: Read Session Log

Read the session log file from `snapshot.session_log_path` (last 30 lines). Extract the action timeline — what was being worked on, which files were touched, what the last operations were.

## Step 4: Read Active Plan

If `snapshot.active_plan` points to a file that still exists, read it. This is the most important context — it shows what was planned but may not have been completed.

Also check `~/.claude/plans/` for any plan files modified since the snapshot timestamp.

## Step 5: Read Memory Context

Read the project's `MEMORY.md` for any persistent context that was saved during or after the previous session.

```
~/.claude/projects/{project-id}/memory/MEMORY.md
```

## Step 6: Present Warm-Up Summary

Output a structured restoration report:

```markdown
## Session Restoration (Lazarus Protocol)

**Last session:** {timestamp} ({age} ago)
**Branch:** {branch}
**Uncommitted:** {file list}

### Last Intent (from session log)
{last 5 tool descriptions from snapshot.last_intent}

### Active Plan
{plan file path and summary if exists}

### What Changed Since Last Session
- {new commits since snapshot}
- {files added/removed from uncommitted}
- {branch changes}

### Memory Context
{relevant MEMORY.md entries}

### Recommended Next Action
{Based on the plan state and git state, suggest what to do next}
```

## Important Notes

- The snapshot is created automatically by the `lazarus-snapshot.js` Stop hook on every session end.
- Snapshots are stored per-project at `~/.claude/lazarus/{project-id}/last_session.json`.
- The global index at `~/.claude/lazarus/global_index.json` tracks the most recent session across all projects.
- Snapshots older than 30 days are auto-pruned from the global index.
- If no snapshot exists, suggest the user start a session normally — the snapshot will be created when they close this session.
