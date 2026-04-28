#!/usr/bin/env bash
# design-md — wrapper around @google/design.md, resolves the CLI from the
# Claude Power Pack repo's local node_modules so it works on any machine
# that has run install.sh.
#
# Usage: design-md <lint|diff|export|spec> [args...]
# Examples:
#   design-md lint DESIGN.md
#   design-md export --format tailwind DESIGN.md > tailwind.theme.json
#   design-md spec --format json
set -e

# Resolve the Power-Pack repo. When this wrapper has been copied to
# ~/.claude/bin/design-md it can no longer compute the skill dir from $0,
# so prefer the canonical install path and only fall back to relative
# resolution when running from the repo itself.
if [ -n "$CLAUDE_POWER_PACK_DIR" ] && [ -d "$CLAUDE_POWER_PACK_DIR" ]; then
  SKILL_DIR="$CLAUDE_POWER_PACK_DIR"
elif [ -d "$HOME/.claude/skills/claude-power-pack" ]; then
  SKILL_DIR="$HOME/.claude/skills/claude-power-pack"
else
  SKILL_DIR="$(cd "$(dirname "$(readlink -f "$0" 2>/dev/null || echo "$0")")/../.." && pwd)"
fi

ENTRY="$SKILL_DIR/node_modules/@google/design.md/dist/index.js"

if [ ! -e "$ENTRY" ]; then
  echo "design-md: CLI entry not found at $ENTRY" >&2
  echo "design-md: run '$SKILL_DIR/install.sh' (Node 18+ + npm required) to provision it." >&2
  exit 127
fi

if ! command -v node >/dev/null 2>&1; then
  echo "design-md: 'node' not on PATH — install Node 18+ and retry." >&2
  exit 127
fi

exec node "$ENTRY" "$@"
