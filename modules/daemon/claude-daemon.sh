#!/usr/bin/env bash
# Claude Power Pack — Dynamic Daemon & Crash Recovery (Part P)
# Hardware-aware Node.js memory tuning + automatic crash recovery loop.
#
# Usage:
#   claude-daemon [claude args...]
#   claude-daemon --help

CONFIG_FILE="$HOME/.claude/daemon/config"
MIN_RAM=2048
MAX_RAM=8192
MAX_RETRIES=5

# 1. RAM Detection (hardware-aware)
detect_ram_mb() {
    if command -v free &>/dev/null; then
        # Linux: free -b returns bytes
        free -b | awk '/^Mem:/ { printf "%d", $2 / 1048576 }'
    elif command -v sysctl &>/dev/null; then
        # macOS: hw.memsize returns bytes
        sysctl -n hw.memsize | awk '{ printf "%d", $1 / 1048576 }'
    else
        echo "8192"  # fallback 8GB
    fi
}

# 2. Calculate 25% with min/max clamp
calculate_node_mem() {
    local total_mb="$1"
    local target=$(( total_mb / 4 ))

    [ "$target" -lt "$MIN_RAM" ] && target=$MIN_RAM
    [ "$target" -gt "$MAX_RAM" ] && target=$MAX_RAM
    echo "$target"
}

# 3. Load user override from config file
load_override() {
    if [ -f "$CONFIG_FILE" ]; then
        local override
        override=$(grep -E "^MAX_OLD_SPACE_SIZE=" "$CONFIG_FILE" 2>/dev/null | tail -1 | cut -d= -f2)
        if [ -n "$override" ]; then
            echo "$override"
            return 0
        fi
    fi
    return 1
}

# 4. Configure memory
total_ram=$(detect_ram_mb)
if override=$(load_override); then
    node_mem="$override"
    echo "[daemon] Using manual override: ${node_mem}MB"
else
    node_mem=$(calculate_node_mem "$total_ram")
    echo "[daemon] System RAM: ${total_ram}MB -> Node.js heap: ${node_mem}MB (25%)"
fi

export NODE_OPTIONS="--max-old-space-size=${node_mem}"

# 5. Immortality Loop
retries=0
while true; do
    claude "$@"
    exit_code=$?

    # Clean exits — do not restart
    [ "$exit_code" -eq 0 ] && exit 0
    [ "$exit_code" -eq 130 ] && exit 130   # Ctrl+C / SIGINT
    [ "$exit_code" -eq 143 ] && exit 143   # SIGTERM

    retries=$((retries + 1))
    if [ "$retries" -ge "$MAX_RETRIES" ]; then
        echo ""
        echo "[STOP] Claude Code crashed $MAX_RETRIES times consecutively. Stopping."
        echo "       Check logs or adjust memory: claude-daemon-set-ram <MB>"
        exit 1
    fi

    echo ""
    echo "[WARNING] Claude Code crashed (exit code: $exit_code). Recovering... (attempt $retries/$MAX_RETRIES)"
    echo "          Restarting in 2 seconds..."
    sleep 2
done
