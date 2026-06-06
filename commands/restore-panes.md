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
powershell ... restore_panes.ps1 -AutoRun        # auto-resume, no pasting
```

## Auto-run mode (`-AutoRun`)

By default you paste the printed `claude --resume <id>` line into each pane.
`-AutoRun` removes that last step: it writes a `.vscode/tasks.json` into every
repo so Cursor AUTO-RUNS the resume command(s) when the folder opens -- one
dedicated terminal per distinct pane session, each launching straight into its
exact conversation.

```
powershell -ExecutionPolicy Bypass -File <pp>\tools\restore_panes.ps1 -AutoRun
```

- **First time per repo:** Cursor shows "Allow Automatic Tasks in Folder" --
  click Allow once. (VS Code/Cursor requires this trust step before any
  `folderOpen` task runs; it is one-time, not per-restore.)
- **Non-destructive:** if a repo already has a `tasks.json`, your tasks are
  preserved -- only `CPC-Restore:`-labelled tasks are (re)written, and the
  prior file is copied to `tasks.json.cpc-bak` first.
- **Point-in-time:** session ids change every session, so re-run `-AutoRun`
  at each restore to refresh the tasks.json. The generator is
  `modules/cpc_os/vscode_autorun.py` (also runnable directly, with `--dry-run`).
- **To remove:** delete the `CPC-Restore:`-labelled tasks (or the generated
  `.vscode/tasks.json`) from a repo.

## Proactive auto-restore (background, zero-action)

`-AutoRun` is manual. For a crash you did not see coming -- a 3am reboot, a hard
lock -- the `tasks.json` must already be on disk BEFORE the crash.
`tools/snapshot_auto_writer.ps1` keeps them fresh: a Task Scheduler job
(`pp-snapshot-writer`, every 15 min, no admin) that each cycle (1) regenerates
`session_snapshot.json` from the live registry and (2) writes the per-repo
`.vscode/tasks.json` -- WITHOUT opening any Cursor window (idempotent-skip leaves
unchanged repos untouched). So whenever you reopen Cursor after a crash, the
auto-run tasks are already there and every pane resumes itself.

```
powershell -File <pp>\tools\snapshot_auto_writer.ps1 -Action start    # install
powershell -File <pp>\tools\snapshot_auto_writer.ps1 -Action status   # state + coverage
powershell -File <pp>\tools\snapshot_auto_writer.ps1 -Action stop     # uninstall
```

Distinct from the daily `\ClaudePP-SessionSnapshot` task (that one zips
`~/.claude/projects/` for disaster recovery; this one refreshes the pane
manifest + tasks.json for crash restore).

> **Process rule:** before a long nocturnal session, or any session with
> Minecraft / a heavy workload open, confirm the writer is active --
> `snapshot_auto_writer.ps1 -Action status` should report `State: Ready`.
> Without it, the restore is only as fresh as the last manual `-AutoRun`.

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
- Default mode: `cursor <path>` reopens the window and Cursor restores its
  panes, but does not auto-run claude in them -- you paste the printed resume
  line. Use `-AutoRun` (see above) to skip the paste and have each pane resume
  itself on folder open.
- Requires the `cursor` CLI on PATH. If absent, the resume manifest still
  prints so you can restore by hand.

## Pairs with

- `/panes` -- the live registry view (active / stale / dead).
- `modules/cpc_os/snapshot.py` -- the writer that produces the snapshot the
  restore reads. Together: snapshot WRITES, restore READS and REOPENS.
