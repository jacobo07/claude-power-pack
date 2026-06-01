---
name: compact-rescue
description: "Emergency rescue when /compact freezes at 95%. Safely kills the stuck claude.exe and signals kclaude.bat to --resume from pre-compact state. Use only when /compact has been stuck >2 minutes. Transcript is preserved; only the in-flight summary is lost."
allowed-tools:
  - Bash
  - PowerShell
---

# /compact-rescue -- Emergency Compact Hang Recovery

**Use this only when** `/compact` is stuck at 95% for more than
2 minutes (BL-COMPACT-001 -- claude.exe binary bug in TTY render
layer; documented in
`vault/knowledge_base/compact-95-hang-repro.md`).

## What it does

1. Finds the most-likely-stuck `claude.exe` (highest RSS).
2. Verifies the session looks genuinely stuck (`.jsonl` idle
   `>= 120s` by default; aborts otherwise to protect active sessions).
3. Captures `sessionId` from env or `.jsonl` header.
4. Saves restart marker to `~/.claude/state/restart_pending.json`
   and `kclaude-restart-sid.txt`.
5. Force-kills the stuck `claude.exe`.
6. `kclaude.bat` parent loop auto-relaunches with `claude --resume <sid>`
   in the same Cursor pane (MC-LAZ-26 contract).

## What is lost vs kept

- **Lost:** the compact summary in mid-generation (the thing
  claude.exe was rendering when it froze).
- **Kept:** every transcript turn before the compact started.
  `.jsonl` is append-only; turns persist before /compact runs.

## Invocation

```powershell
# From PP repo root:
powershell -NoProfile -ExecutionPolicy Bypass `
  -File "$env:USERPROFILE\.claude\skills\claude-power-pack\tools\compact_rescue.ps1"
```

Or, if PP is shipped with global commands enabled:

```powershell
# Owner runs once to mirror to global commands dir:
Copy-Item `
  "$env:USERPROFILE\.claude\skills\claude-power-pack\commands\compact-rescue.md" `
  "$env:USERPROFILE\.claude\commands\compact-rescue.md"
```

## DryRun (recommended first time)

To verify the script picks the right process without killing
anything:

```powershell
powershell -File "$env:USERPROFILE\.claude\skills\claude-power-pack\tools\compact_rescue.ps1" `
  -DryRun
```

You'll see a JSON object with `target_pid`, `rss_mb`,
`session_id`. If the session looks active, the dry-run will
abort with `[ABORT]` -- that's the guard working, not a bug.

## Override (force a kill even when session looks active)

If you are certain `/compact` is stuck and the `.jsonl` recency
guard is being too conservative:

```powershell
powershell -File "$env:USERPROFILE\.claude\skills\claude-power-pack\tools\compact_rescue.ps1" `
  -IdleThresholdSeconds 0
```

This bypasses the recency guard. Use sparingly.

## After rescue

1. Claude Code closes; kclaude.bat relaunches with
   `claude --resume <sid>` (or you can run it manually if
   `kclaude.bat` is not your launcher).
2. The session loads the pre-compact transcript.
3. You can re-run `/compact` if context needs reducing -- or
   keep working without compacting.

## Hard rules

- **Never claim the bug is patched** -- this rescue does not
  fix the underlying claude.exe hang. It only gives you a
  clean escape.
- **Never use this on an active session** -- the recency guard
  enforces this by default; only override when you are sure.
- **Report upstream** -- the canonical fix is upstream in
  claude.exe; see `vault/knowledge_base/anthropic-issue-compact-95.md`
  for the issue body to file.

## Verification

After running, these should be true:

- `claude.exe` PID returned by the script is no longer in
  `Get-Process -Name claude`.
- `~/.claude/state/restart_pending.json` exists with the
  expected schema.
- `~/.claude/state/kclaude-restart-sid.txt` exists (if
  sessionId was captured).

If any fail, do not tell the user "rescued" -- report what
was missing.
