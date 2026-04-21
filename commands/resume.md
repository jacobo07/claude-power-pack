---
name: resume
description: "Restore context from previous session via Lazarus Protocol. Use /resume last to warm up instantly."
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---

# Lazarus Protocol — Session Resume

Restore the mental model from the previous session in this project. Zero re-explanation needed.

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
