# Zero-Crash Environment

> Sleepy part. ~300 tokens. Load when: zero-crash, TTY, sandbox, process isolation, ^[[I, ^[[O.
> Auto-activated at DEEP+ tier when Bash tool runs long-running processes.

## Process Sandboxing (CD#14)
Long-running child processes MUST NOT inherit Claude Code's TTY file descriptors.
Use the sandbox wrapper for emulators, servers, display managers:
```bash
zero-crash-sandbox <command> [args...]  # Unix: setsid + redirect + PID capture
zero-crash-sandbox.cmd <command>        # Windows: Start-Process -NoNewWindow
```

## TTY Restoration
The `tty-restore.js` PostToolUse hook auto-disables DECSET 1004 focus reporting after Bash calls.
Prevents `^[[I^[[O` escape sequence leakage. No agent action needed.

## Quality Gate (Advisory by Default)
Stop hook runs compile + scaffold audit + tests on session end.
- Advisory: always continues, creates `BLOCKED_DELIVERY.md` as evidence
- Enforce: `export ZERO_CRASH_ENFORCE=true` to hard-block after 3 failures

## Risky Binary Detection
PreToolUse hook warns (never blocks) when Bash commands contain unredirected:
Xvfb, dolphin, emulator, ffmpeg, gunicorn, uvicorn.

## Quick Commands
| Action | Command |
|--------|---------|
| Sandbox process | `zero-crash-sandbox <cmd>` |
| View logs | `ls /tmp/zero-crash/` |
| Active PIDs | `cat /tmp/zero-crash/active_pids.txt` |
| Enable enforce | `export ZERO_CRASH_ENFORCE=true` |
