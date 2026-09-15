---
name: restart
description: In-pane restart of claude.exe in the current Cursor terminal via the kclaude.bat wrapper contract. Same session resumes automatically; falls back to clipboard paste if the pane isn't under kclaude.
allowed-tools:
  - Bash
---

# /restart -- in-pane restart with kclaude.bat integration

Force-exits the current `claude.exe` in **this** Cursor terminal pane and queues a resume of the **same** session via the existing `kclaude.bat` wrapper contract (MC-LAZ-26 doctrine).

## Two delivery modes

- **kclaude.bat parent (zero-keystroke, recommended)** -- if your Cursor pane was launched via `kclaude.bat` (true for the "Last session" profile via `lazarus-shell-autoresume.bat`, and for the "Claude" profile after the 2026-05-31 consolidation), kclaude detects the flag file + SID file written by /restart and relaunches `claude --resume <uuid>` in the same pane. Automatic, no keystrokes.

- **Direct claude.exe (2 keystrokes, fallback)** -- if your pane was launched with `claude.exe` directly (no kclaude wrapping), the kill drops you into the parent cmd shell. The resume command is on your Windows clipboard. Press **Ctrl+V** then **Enter**.

## What happens (in order)

1. Captures this session's `CLAUDE_CODE_SESSION_ID`.
2. Resolves `claude.exe` from `CLAUDE_CODE_EXECPATH` / PATH / `~/.local/bin/claude.exe`.
3. Walks PowerShell's parent process chain to find the running `claude.exe` PID.
4. Writes the session id to `%USERPROFILE%\.claude\lazarus\kclaude-restart-sid.txt`.
5. Writes an empty flag file at `%TEMP%\claude-restart-<claude-pid>.flag` (kclaude.bat scans `claude-restart-*.flag`).
6. Copies `"<claude.exe>" --resume "<uuid>"` to the Windows clipboard.
7. **Injects `/exit\r` into the SHARED console input buffer** via `CreateFileW("CONIN$")` + `WriteConsoleInputW`. claude.exe and PowerShell share the same console (verified via `GetConsoleProcessList`); the injected key events land in claude's input queue as if the Owner typed them. claude exits **gracefully** -- no `Stop-Process -Force`.
8. kclaude.bat (if parent) loops: reads SID file, deletes flag, runs `claude --resume <uuid>`. Otherwise: Owner pastes from clipboard.

### Why /exit and not Stop-Process -Force (sealed 2026-05-31 evening)

The earlier same-day rewrite used `Stop-Process -Force` (effectively SIGKILL on Windows). The Owner reported on 2026-05-31 that the original pre-2026-05-24 `/restart` did NOT kill claude -- it issued `/exit`, the pane stayed at cmd briefly, then resumed. That graceful behavior is restored here.

Architectural detail: `Get-CimInstance Win32_Process` confirms claude.exe is the parent of PowerShell (Cursor -> claude.exe -> bash tool -> PowerShell). `GetConsoleProcessList` returns BOTH PIDs, proving they share the same console host. The shared console's input buffer is reachable from PowerShell by opening `CONIN$` directly -- PowerShell's own STDIN is a pipe (claude redirected it for tool JSON-RPC) and does NOT reach claude's input queue. `WriteConsoleInputW` into CONIN$ delivers the keys to whichever process next calls `ReadConsoleInput` -- normally claude, since PowerShell is `-NonInteractive`.

### Fallback when injection cannot complete

If `CreateFileW("CONIN$")` returns INVALID_HANDLE_VALUE (no shared console -- rare; Cursor's terminal profile is non-standard) OR `WriteConsoleInputW` writes 0 events, the script falls through to `Stop-Process -Force` and prints a yellow `[FALLBACK]` warning. The Owner is never left with a hung claude.exe.

## Session safety

The `.jsonl` is **never** touched by automation -- only the live `claude.exe` process is killed. claude.exe persists session events to the `.jsonl` synchronously per turn, so a force-kill at a quiet moment loses no conversation state. Session Safety Contract §1 (no `.jsonl` destroyed by automation) is preserved by definition.

## The kclaude.bat contract (reference)

`~/.claude/kclaude.bat` is the canonical wrapper. It launches `claude.exe`, and after each exit:

- Scans `%TEMP%\claude-restart-*.flag`. Any match -> set RESTART=1.
- Reads `%USERPROFILE%\.claude\lazarus\kclaude-restart-sid.txt` -> SID.
- If SID present: relaunches `claude --resume <sid>`. Else: `claude --continue`.
- Loops back to the scan.
- No flag -> exit cleanly.

Sets `KCLAUDE_WRAPPER=1` for downstream detection by other scripts.

## Cursor terminal profiles (2026-05-31 consolidation)

- **"Last session"** -- already launches `lazarus-shell-autoresume.bat`, which prefers `kclaude.bat` per its MC-LAZ-26 logic. /restart is in-pane out of the box.
- **"Claude"** -- after consolidation, launches `cmd /K kclaude.bat <original-args>`. /restart is in-pane out of the box.
- **Other profiles** (Command Prompt, PowerShell, Git Bash, VPS variants) -- not claude-aware. /restart falls back to clipboard mode if invoked from those.

## Why this replaces the 2026-05-24 external-window approach

The earlier `/restart` (sealed 2026-05-24) spawned a NEW Windows Terminal window. Owner-reported on 2026-05-31:

- **Wrong target.** Owner wanted in-pane, not an external sibling window.
- **Quoting bug.** `cmd /K "<path>" --resume "<uuid>"` had two quote-pairs that cmd.exe mangled, producing "no se reconoce como un comando interno o externo".
- **Duplicate infrastructure.** The first 2026-05-31 rewrite introduced `claude-wrapper.cmd`, unaware of the pre-existing `kclaude.bat` MC-LAZ-26 contract. Now consolidated: `claude-wrapper.cmd` deleted; restart-claude.ps1 writes to kclaude's existing flag + SID files.

The morning 2026-05-31 rewrite added kclaude.bat integration but kept `Stop-Process -Force`. The Owner reported in the evening that the OLDER behavior (pre-2026-05-24) did NOT force-kill -- it sent /exit, claude exited gracefully, and kclaude.bat resumed. The current design restores that:

- **In-pane**: same pane as before.
- **Graceful**: `/exit\r` via WriteConsoleInputW into the shared CONIN$, not SIGKILL.
- **Same-session resume**: kclaude.bat flag + SID files unchanged; the wrapper picks up and runs `claude --resume <uuid>` automatically.
- **Self-tested**: PP_RESTART_DRY_RUN=1 exercises all the file machinery without firing /exit or the fallback kill (used during development verification).

## Execute

!`powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command '& "$env:USERPROFILE\.claude\scripts\restart-claude.ps1"'`

> **Why the single-quoted `-Command` form?** The slash command body is executed by bash on Windows. Bash does not understand PowerShell's `$env:VAR` syntax, so `$env:USERPROFILE` inside a bash-evaluated argument expands to nothing -- leaving `:USERPROFILE\...` as a literal and PowerShell then rejects the malformed path. Wrapping the whole payload in single quotes keeps bash from touching it, and PowerShell's own parser handles `$env:USERPROFILE` correctly inside the double-quoted string.
