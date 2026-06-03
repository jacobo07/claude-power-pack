---
name: restore-panes
description: Crash recovery for Cursor panes. Reads ~/.claude/state/session_snapshot.json and reopens every repo that was open (deduped) as a Cursor window via `cursor <path>`, then prints the exact `claude --resume <id>` line per pane so each terminal returns to its EXACT conversation -- not just the cwd. Runs from any terminal; Claude Code does NOT need to be open. Pairs with /panes (the live registry view) and snapshot.py (the writer).
---

# /restore-panes -- one-command crash recovery

## TL;DR (post-crash, from ANY terminal)

```
powershell -ExecutionPolicy Bypass -File "C:\Users\User\.claude\skills\claude-power-pack\tools\restore_panes.ps1"
```

You do NOT need Claude Code open to run it. It reopens each repo as a
Cursor window and prints the exact resume command for every pane.

## What it does

1. Reads `~/.claude/state/session_snapshot.json` (the machine sidecar that
   `modules/cpc_os/snapshot.py` writes on every SessionStart).
2. Dedups the panes by repo -- the real restore unit is one Cursor window
   per repo, which reopens and restores its own terminal panes.
3. For each repo, runs `cursor <path>` to reopen the window.
4. Prints, per repo, the exact `claude --resume <id>` line(s) to paste into
   each restored terminal so the EXACT conversation comes back:
   - `[exact]`       -- the pane's own captured session_id (transcript verified).
   - `[repo-latest]` -- the repo's most-recent conversation, recovered from
     `~/.claude/projects/<encoded-cwd>/<uuid>.jsonl` when the registry never
     captured a per-pane session_id.

## Usage

```
/restore-panes                 # reopen all repos + print resume manifest
```

Direct (no Claude Code needed):

```
powershell -ExecutionPolicy Bypass -File <pp>\tools\restore_panes.ps1
powershell ... restore_panes.ps1 -DryRun         # preview, opens nothing
powershell ... restore_panes.ps1 -SnapshotPath X # alternate snapshot
```

## The recovery flow

```
1. Crash happens -- Cursor dies, host reboots, every pane gone.
2. Open any terminal (cmd / PowerShell / Run box).
3. Run the restore command above.
4. Each repo reopens as a Cursor window (panes restored by Cursor).
5. In each restored terminal, paste the printed `claude --resume <id>`
   line -> that pane is back on its exact conversation.
```

## Honest limitations

- A repo with multiple panes that all predate the session_id capture can
  only be resolved to the repo's single latest conversation (`repo-latest`);
  panes opened after the capture landed each restore exactly (`[exact]`).
- `cursor <path>` reopens the window; Cursor restores its panes, but does
  not auto-run claude in them -- you paste the printed resume line. (A fully
  auto-run-claude profile is a separate, more invasive opt-in.)
- Requires the `cursor` CLI on PATH. If absent, the resume manifest still
  prints so you can restore by hand.

## Pairs with

- `/panes` -- the live registry view (active / stale / dead).
- `modules/cpc_os/snapshot.py` -- the writer that produces the snapshot the
  restore reads. Together: snapshot WRITES, restore READS and REOPENS.
