# Zero-Crash Environment

Prevents TTY corruption, session hangs, and "stop hook prevented continuation" errors in Claude Code.

## Problem

When Claude Code runs external tools (emulators, servers, display managers) via Bash, child processes can:
- Inherit the terminal's file descriptors, leaking escape sequences (`^[[I^[[O`) into the prompt
- Block session exit when quality gate hooks fail repeatedly
- Leave orphan processes consuming memory and file descriptors

## Solution

Three hooks + a sandbox wrapper that isolate child processes from Claude Code's TTY:

| Component | Type | Purpose |
|-----------|------|---------|
| `zero-crash-gate.js` | Stop hook | Advisory quality gate (compile + scaffold + tests) |
| `tty-restore.js` | PostToolUse hook | Resets terminal state after Bash commands |
| `process-sandbox.js` | PreToolUse hook | Warns when Bash runs risky binaries without I/O redirect |
| `sandbox-wrapper.sh` | CLI tool | Isolates any process (setsid + redirect + PID capture) |
| `sandbox-wrapper.ps1` | CLI tool | Windows equivalent (Start-Process -NoNewWindow) |

## Installation

### Automatic (via Claude Power Pack installer)
```bash
# Unix
bash install.sh

# Windows
.\install.ps1
```

### Manual hook registration
Add to `~/.claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [
      { "hooks": [{ "type": "command", "command": "node \"path/to/process-sandbox.js\"" }] }
    ],
    "PostToolUse": [
      { "hooks": [{ "type": "command", "command": "node \"path/to/tty-restore.js\"" }] }
    ],
    "Stop": [
      { "hooks": [{ "type": "command", "command": "node \"path/to/zero-crash-gate.js\"", "timeout": 60000 }] }
    ]
  }
}
```

## Configuration

Edit `config.json` or use environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ZERO_CRASH_ENFORCE` | `false` | Enable hard blocking after 3 gate failures |
| `ZERO_CRASH_LOG_DIR` | `/tmp/zero-crash` | Sandbox process log directory |
| `ZERO_CRASH_API_KEY` | (none) | Opt-in anonymous telemetry |
| `ZERO_CRASH_VPS_ENDPOINT` | `http://204.168.166.63:9879` | Telemetry receiver |

## How It Works

### TTY Corruption Fix
Windows Terminal and Cursor enable focus reporting (`DECSET 1004`). When child processes inherit the TTY,
focus-in (`^[[I`) and focus-out (`^[[O`) escape sequences leak into Claude Code's input buffer.
The `tty-restore.js` hook disables focus reporting after every Bash tool invocation.

### Advisory Quality Gate
Instead of blocking sessions (causing "stop hook prevented continuation"), the gate:
1. Runs compile + scaffold audit + tests
2. On failure: creates `BLOCKED_DELIVERY.md` with exact errors
3. Always returns `{continue: true}` (unless `ZERO_CRASH_ENFORCE=true`)

### Process Sandbox
The sandbox wrapper fully detaches child processes:
```
Parent (Claude Code TTY)
  |
  +-- setsid (new session, no TTY)
       |
       +-- child process
            stdin  = /dev/null
            stdout = /tmp/zero-crash/{timestamp}.log
            stderr = (same log)
```

## Community Telemetry

When opted in (`ZERO_CRASH_API_KEY`), anonymized crash reports help improve the module:
- Hook failure patterns (which gates fail most)
- TTY corruption frequency by platform
- Risky binary trigger rates

**Never collected:** code content, file paths (hashed only), user identity (UUID only), API keys.

## License

Part of Claude Power Pack. MIT License.
