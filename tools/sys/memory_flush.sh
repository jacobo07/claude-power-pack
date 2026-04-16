#!/usr/bin/env bash
# Memory Flush Orchestrator — Bash wrapper for Git Bash / MSYS2 terminals
# Delegates to the PowerShell implementation on Windows

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PS_SCRIPT="$SCRIPT_DIR/memory_flush.ps1"
PS_ARGS=""

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --check-only) PS_ARGS="$PS_ARGS -CheckOnly"; shift ;;
        --verbose)    PS_ARGS="$PS_ARGS -Verbose"; shift ;;
        --help|-h)
            echo "Usage: memory_flush.sh [--check-only] [--verbose]"
            echo "  --check-only  Report RAM status only, touch nothing"
            echo "  --verbose     Show detailed output from each tool"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Windows detection
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    powershell.exe -ExecutionPolicy Bypass -File "$PS_SCRIPT" $PS_ARGS
    exit $?
else
    echo "[ERROR] memory_flush currently supports Windows only."
    echo "Existing tools (kill_zombies, electron_priority_manager) are PowerShell-based."
    exit 1
fi
