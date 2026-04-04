# Zero-Crash Environment — Core Rules

> Sleepy module. ~350 tokens. Zero cost when dormant.
> Activation: keywords "zero-crash", "TTY", "sandbox", "process isolation", "^[[I", "^[[O"
> Auto-activated at DEEP+ tier when Bash tool runs long-running processes.

## Rules

### 1. Process Sandboxing (CD#14)
Long-running child processes (emulators, servers, display managers) MUST NOT inherit Claude Code's TTY.
Use the sandbox wrapper:
```bash
# Unix
zero-crash-sandbox <command> [args...]

# Windows
zero-crash-sandbox.cmd <command> [args...]
```
The wrapper: redirects stdin from /dev/null, stdout/stderr to log file, detaches via setsid, captures PID.

### 2. TTY Restoration
After Bash tool invocations, the tty-restore hook automatically disables focus reporting (`DECSET 1004`)
to prevent `^[[I^[[O` escape sequence leakage. No action needed from the agent.

### 3. Quality Gate (Advisory)
Stop hooks run compile + scaffold audit + tests on session end.
- Default: advisory mode — always allows session to continue, creates `BLOCKED_DELIVERY.md` as evidence
- Opt-in enforcement: `export ZERO_CRASH_ENFORCE=true`

### 4. Risky Binary Detection
The process-sandbox PreToolUse hook warns (never blocks) when Bash commands contain risky binaries
without I/O redirection. Current watchlist: Xvfb, dolphin, emulator, ffmpeg, gunicorn, uvicorn.

## Commands

| Action | Command |
|--------|---------|
| Sandbox a process | `zero-crash-sandbox <command> [args...]` |
| Check active sandboxed PIDs | `cat /tmp/zero-crash/active_pids.txt` |
| View sandbox logs | `ls -la /tmp/zero-crash/` |
| Enable enforcement mode | `export ZERO_CRASH_ENFORCE=true` |
| Check hook status | Review `~/.claude/settings.json` Stop hooks section |

## Telemetry (Opt-in)
Set `ZERO_CRASH_API_KEY` to enable anonymous crash telemetry to the community dashboard.
Reports: hook failures, TTY corruption events, gate pass/fail rates. Never: code, file paths, identity.
