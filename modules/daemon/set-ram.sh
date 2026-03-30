#!/usr/bin/env bash
# Claude Power Pack — Manual RAM Override for Daemon (Part P)
#
# Usage:
#   claude-daemon-set-ram <MB>       # Force specific heap size
#   claude-daemon-set-ram --reset    # Back to auto-detect (25% of system RAM)

CONFIG_DIR="$HOME/.claude/daemon"
CONFIG_FILE="$CONFIG_DIR/config"

if [ "$1" = "--reset" ]; then
    rm -f "$CONFIG_FILE"
    echo "[OK] RAM override removed. Will use auto-detection (25% of system RAM)."
    exit 0
fi

if [ -z "$1" ] || ! [[ "$1" =~ ^[0-9]+$ ]]; then
    echo "Usage: claude-daemon-set-ram <MB>"
    echo "       claude-daemon-set-ram --reset"
    echo ""
    echo "Examples:"
    echo "  claude-daemon-set-ram 4096     # Force 4GB heap"
    echo "  claude-daemon-set-ram 8192     # Force 8GB heap"
    echo "  claude-daemon-set-ram --reset  # Back to auto-detect"
    exit 1
fi

mkdir -p "$CONFIG_DIR"
echo "MAX_OLD_SPACE_SIZE=$1" > "$CONFIG_FILE"
echo "[OK] Node.js heap override set to ${1}MB. Effective on next claude-daemon launch."
