#!/bin/bash
# Claude Power Pack v3.0 — Unix Installer
set -e
SKILL_DIR="${HOME}/.claude/skills/claude-power-pack"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Claude Power Pack v3.0 Installer"
echo "================================="
echo ""
echo "Step 1: Installing skill files..."
mkdir -p "${SKILL_DIR}/modules"
cp "${SCRIPT_DIR}/SKILL.md" "${SKILL_DIR}/"
cp -r "${SCRIPT_DIR}/modules/"* "${SKILL_DIR}/modules/"
echo "  OK: Installed to ${SKILL_DIR}"
echo ""
echo "Step 2: Checking Python dependencies..."
PYTHON=""
command -v python3 &>/dev/null && PYTHON=python3
[ -z "$PYTHON" ] && command -v python &>/dev/null && PYTHON=python
if [ -n "$PYTHON" ]; then
    $PYTHON -m pip install httpx feedparser -q 2>/dev/null && echo "  OK: httpx, feedparser" || echo "  WARN: pip failed"
else
    echo "  WARN: Python not found. Module G requires Python 3.10+"
fi
echo ""
read -p "Step 3: Setup autoresearch scheduler (2x/day)? [y/N] " yn
if [[ "$yn" =~ ^[Yy]$ ]] && [ -n "$PYTHON" ]; then
    $PYTHON "${SKILL_DIR}/modules/autoresearch/setup_schedule.py"
else
    echo "  Skipped."
fi
echo ""
echo "Done! Post-install:"
echo "  1. Edit modules/autoresearch/config.json"
echo "  2. Remove/throttle Stop hook in ~/.claude/settings.json"
echo "  3. python modules/executionos-lite/migrate.py <executionos.md> --verify"
echo "  4. Trigger 'deep optimize' in Claude Code"
