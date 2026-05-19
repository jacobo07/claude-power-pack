#!/usr/bin/env bash
# Claude Power Pack — global installer (POSIX bash wrapper)
#
# Sibling of install.sh (per-project doctrine scaffolder; do NOT
# confuse — that one templates a per-project CLAUDE.md). This script
# installs / updates the Power Pack into ~/.claude/ for any user.
# Pure-Python logic lives in tools/install_global_core.py; this
# wrapper handles banner + env-scrub + invocation.
#
# Usage:
#   ./install-global.sh               # apply
#   ./install-global.sh --dry-run     # preview every action; no mutation
#   ./install-global.sh --settings <path>  # custom settings.json
#
# Doctrine (Lesson 2, 2026-05-19): this script NEVER writes into
# permissions.allow — it PRINTS the rules the Owner pastes. See
# vault/standards/feature-completion-standard.md.

set -euo pipefail

echo "============================================================"
echo "  Claude Power Pack -- install-global.sh"
echo "  Banner: PER-USER GLOBAL installer (NOT per-project!)"
echo "  Sibling: install.sh (per-project CLAUDE.md scaffolder)"
echo "============================================================"

# Locate the Python interpreter. Honor an explicit override; else
# fall back to python3 / python on PATH. Fail loud if missing.
if [ -n "${CLAUDE_PY_EXE:-}" ] && [ -x "${CLAUDE_PY_EXE}" ]; then
  PY="${CLAUDE_PY_EXE}"
elif command -v python3 >/dev/null 2>&1; then
  PY="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  PY="$(command -v python)"
else
  echo "install-global.sh: cannot find python3 / python." >&2
  echo "Install Python 3.10+ or set CLAUDE_PY_EXE." >&2
  exit 5
fi

# Resolve the core script relative to THIS file (no hardcoded paths
# — gap 2 doctrine).
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CORE="${HERE}/tools/install_global_core.py"
if [ ! -f "${CORE}" ]; then
  echo "install_global_core.py not found at ${CORE}" >&2
  exit 5
fi

# Env scrub (gap 4): strip parent-session markers before spawning the
# Python core (which spawns settings_merger.py).
unset CLAUDECODE CLAUDE_PROJECT_DIR 2>/dev/null || true
for v in $(env | awk -F= '/^CLAUDE_CODE_/ {print $1}'); do
  unset "$v" 2>/dev/null || true
done

echo "Invoking: ${PY} ${CORE} $*"
echo
"${PY}" "${CORE}" "$@"
RC=$?

if [ "${RC}" -ne 0 ]; then
  echo
  echo "install-global.sh: FAILED (exit ${RC})" >&2
  exit "${RC}"
fi
echo
echo "install-global.sh: OK"
exit 0
