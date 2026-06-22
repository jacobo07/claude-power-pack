# /restart bug — SendKeys pane eviction when claude.exe IS the shell

> ⚠️ **SUPERSEDED (2026-06-22, restart-kclear recursive audit PF-2).** The fix prescribed
> below — *"always open a new top-level terminal window"* (external-window approach) — was
> itself **reverted on 2026-05-31**. The current, shipped `/restart` is **in-pane**: it
> injects `/exit\r` into the shared console input buffer (`CONIN$` + `WriteConsoleInputW`)
> so claude exits gracefully and `kclaude.bat` resumes the SAME pane via `claude --resume
> <sid>`. See `~/.claude/commands/restart.md`, `~/.claude/scripts/restart-claude.ps1`, and
> the authoritative UKDL entry **T-RESTART-001**. Do NOT re-introduce the external-window /
> SendKeys design from this lesson — it is kept only as the historical record of the
> 2026-05-24 SendKeys-eviction bug. The `Write-RestartTarget` removal noted at the bottom
> of this file is also why the `restart-target.json` self-heal is now permanently inert
> (see UKDL **T-RESTART-SELFHEAL-OBSOLETE-001**).

**Sealed:** 2026-05-24 (Owner report: "/restart cierra el pane actual y manda 'claude resume' como mensaje al pane equivocado")
**Component:** `~/.claude/scripts/restart-claude.ps1`, `~/.claude/commands/restart.md`

## What the bug looked like

`/restart` was supposed to relaunch the current claude session "in place" inside the Cursor integrated terminal:
1. Capture `CLAUDE_CODE_SESSION_ID`.
2. Spawn a detached PowerShell helper.
3. Helper kills claude.exe, waits, then uses `SendKeys` against the focused Cursor terminal pane to type `"<claude.exe>" --resume "<sid>"`.
4. User stays in the same pane, claude resumes, end-of-story.

What actually happened in the failing case:
- The pane where `/restart` ran was a Cursor integrated terminal whose **shell process was claude.exe itself** (typical when the user opens a terminal with `claude` as the command).
- Killing claude.exe killed the shell, which made VS Code / Cursor close the pane (default behavior when the integrated terminal's shell exits with non-zero or is force-killed).
- The SendKeys helper then woke up, called `AppActivate(cursor)` + `Ctrl+`` (focus toggle), and typed `claude --resume <sid>` + Enter — into whichever pane had received focus after the eviction.
- If that pane was ANOTHER claude session, the literal text `claude --resume <sid>` was sent as a **chat message** into that other session. Visible symptom from the Owner's side: the original pane gone, a stranger pane suddenly has a weird message in its input.

## Why the helper logic was wrong

Path 2 (`Test-InsideCursor` branch) assumed: "after claude.exe dies, the cmd.exe prompt comes back in the same pane". That assumption holds ONLY if cmd.exe was the pane's shell and claude was a child process inside it. It breaks when claude IS the shell — exactly the configuration most users have when they alias `claude` as their default terminal command in Cursor.

There is no reliable way for the helper to tell the difference (it can inspect the parent process tree at script-launch time, but by the time SendKeys runs, the parent is already gone). The whole "send keys to the same pane" approach is fragile by construction.

## Fix

Drop Path 2 entirely. Replace with: **always open a new top-level terminal window**, leaving the current pane alone. `Start-Process` (Windows Terminal `wt.exe` preferred, `cmd.exe /k` fallback) gives the Owner a clean new console running `claude --resume <sid>`. The current claude session keeps running in the original pane; the Owner closes whichever they don't want.

Side-effects:
- No more SendKeys, no more focus races, no more pane eviction.
- Two claude sessions briefly coexist. They share the same `.jsonl` if both write, but in practice the Owner is reading the new resumed one and abandoning the original. Not a data-race in normal use.
- Removed the `Restore-LiveJsonl` and `Write-RestartTarget` machinery — both only made sense when we were killing the current claude. If the Owner kills the original pane manually later, the .jsonl.live mark gets cleaned up by the existing Stop hook anyway.

## What to keep doing

- The `--resume <sid>` (NOT bare `--continue`) approach is still right: it pins to THIS pane's session, robust against sibling panes writing to the same project's most-recent .jsonl.
- ASCII-only .ps1 (see [[powershell-5-1-script-encoding]]). The new restart-claude.ps1 is 7-bit ASCII; verified at write time.
- Resolve `claude.exe` from `CLAUDE_CODE_EXECPATH` first (env var the harness exports), then PATH, then `~/.local/bin/claude.exe`. The new cmd window doesn't inherit our PATH reliably.

## Cross-ref

- ~/.claude/scripts/restart-claude.ps1
- ~/.claude/commands/restart.md
- vault/lessons/powershell-5-1-script-encoding.md (the file format trap that bit boot_server.ps1 in the same session)
