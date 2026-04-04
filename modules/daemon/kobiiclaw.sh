#!/usr/bin/env bash
# KobiiClaw 2.0 — Persistent Claude Code on VPS via tmux
#
# Usage:
#   kobiiclaw [session-name] [workspace-path]
#   kobiiclaw                                    # default session + workspace
#   kobiiclaw mundicraft /home/kobicraft/workspace/MundiCraft
#   kobiiclaw attach                             # reattach to existing session
#
# What it does:
#   1. SSH into VPS (204.168.166.63)
#   2. Attach to existing tmux session OR create new one
#   3. Inside tmux: run claude-daemon with crash recovery + memory tuning
#   4. If your terminal dies: SSH back in and run `kobiiclaw` again — session is alive
#
# Part of Claude Power Pack — Infrastructure Resiliency Protocol.

set -euo pipefail

VPS_HOST="${KOBIICLAW_VPS_HOST:-204.168.166.63}"
VPS_USER="${KOBIICLAW_VPS_USER:-kobicraft}"
SSH_KEY="${KOBIICLAW_SSH_KEY:-$HOME/.ssh/kobicraft_vps}"
SESSION="${1:-kobiiclaw}"
WORKSPACE="${2:-/home/kobicraft/workspace}"

# Special command: attach to existing session
if [ "$SESSION" = "attach" ]; then
    echo "[KobiiClaw] Reattaching to existing tmux session..."
    ssh -t -i "$SSH_KEY" "${VPS_USER}@${VPS_HOST}" "tmux attach || tmux list-sessions"
    exit $?
fi

# Special command: list sessions
if [ "$SESSION" = "list" ] || [ "$SESSION" = "ls" ]; then
    ssh -i "$SSH_KEY" "${VPS_USER}@${VPS_HOST}" "tmux list-sessions 2>/dev/null || echo 'No tmux sessions running'"
    exit $?
fi

# Special command: kill session
if [ "$SESSION" = "kill" ]; then
    TARGET="${2:-kobiiclaw}"
    ssh -i "$SSH_KEY" "${VPS_USER}@${VPS_HOST}" "tmux kill-session -t '${TARGET}' 2>/dev/null && echo 'Session ${TARGET} killed' || echo 'Session ${TARGET} not found'"
    exit $?
fi

echo "[KobiiClaw 2.0] Connecting to VPS ${VPS_HOST} as ${VPS_USER}..."
echo "[KobiiClaw 2.0] tmux session: ${SESSION} | workspace: ${WORKSPACE}"
echo "[KobiiClaw 2.0] If disconnected, run: kobiiclaw attach"
echo ""

# -A flag: attach if session exists, create if not
# -c flag: set working directory
# Inner command: claude-daemon (crash recovery + memory tuning) with fallback
ssh -t -i "$SSH_KEY" "${VPS_USER}@${VPS_HOST}" \
    "tmux new-session -A -s '${SESSION}' -c '${WORKSPACE}' \
     'echo \"[KobiiClaw] Session ${SESSION} active. Ctrl+B D to detach.\"; \
      if command -v claude-daemon >/dev/null 2>&1; then \
        claude-daemon; \
      elif command -v claude >/dev/null 2>&1; then \
        claude; \
      else \
        echo \"[KobiiClaw] Claude not found. Starting shell in ${WORKSPACE}\"; \
        exec bash; \
      fi'"
