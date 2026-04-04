#!/usr/bin/env bash
# Zero-Crash Sandbox Wrapper — Isolates child process from parent TTY
#
# Usage:
#   zero-crash-sandbox <command> [args...]
#   zero-crash-sandbox -- long-command --with-flags
#
# What it does:
#   1. Creates a new session (setsid) — fully disconnects from terminal
#   2. Redirects stdin from /dev/null — no focus event leakage
#   3. Redirects stdout+stderr to timestamped log file
#   4. Captures PID for later cleanup
#   5. Returns immediately (non-blocking)
#
# Part of Claude Power Pack — Zero-Crash Environment module.

set -euo pipefail

# Configuration
LOG_DIR="${ZERO_CRASH_LOG_DIR:-/tmp/zero-crash}"
mkdir -p "$LOG_DIR"

# Parse arguments
if [ $# -eq 0 ]; then
  echo "Usage: zero-crash-sandbox <command> [args...]"
  echo "       zero-crash-sandbox -- <command> --with-flags"
  exit 1
fi

# Skip "--" separator if present
if [ "$1" = "--" ]; then
  shift
fi

COMMAND_NAME="$(basename "$1")"
TIMESTAMP="$(date +%s)"
LOG_FILE="$LOG_DIR/${TIMESTAMP}-${COMMAND_NAME}.log"
PID_FILE="$LOG_DIR/active_pids.txt"

# Launch sandboxed process
echo "[Zero-Crash] Sandboxing: $*"
echo "[Zero-Crash] Log: $LOG_FILE"

if command -v setsid >/dev/null 2>&1; then
  # Linux: use setsid for full session isolation
  setsid "$@" < /dev/null > "$LOG_FILE" 2>&1 &
else
  # macOS/BSD: nohup + disown as fallback
  nohup "$@" < /dev/null > "$LOG_FILE" 2>&1 &
  disown
fi

PID=$!
echo "$PID" >> "$PID_FILE"

echo "[Zero-Crash] SANDBOXED: PID=$PID"
echo "[Zero-Crash] Monitor: tail -f $LOG_FILE"
echo "[Zero-Crash] Kill: kill $PID"
