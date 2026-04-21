#!/usr/bin/env bash
# Sleepless QA — idempotent VPS installer.
#
# Installs Python deps, Playwright browsers, and verifies Node >= 20 + Dolphin
# (optional) availability. Safe to re-run. Supports --dry-run.
#
# Usage:
#   bash install.sh [--dry-run] [--skip-playwright] [--skip-mineflayer]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQUIREMENTS="${SCRIPT_DIR}/requirements.txt"
VENV_DIR="${HOME}/.cache/sleepless-qa/venv"
PLAYWRIGHT_CACHE="${HOME}/.cache/sleepless-qa-playwright"
MINEFLAYER_DIR="${HOME}/.cache/sleepless-qa/mineflayer"
STATE_DIR="${QA_STATE_DIR:-${HOME}/.claude/sleepless-qa}"

DRY_RUN=0
SKIP_PLAYWRIGHT=0
SKIP_MINEFLAYER=0

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --skip-playwright) SKIP_PLAYWRIGHT=1 ;;
    --skip-mineflayer) SKIP_MINEFLAYER=1 ;;
    -h|--help)
      sed -n '1,10p' "$0"
      exit 0
      ;;
    *)
      echo "[install.sh] Unknown arg: $arg" >&2
      exit 2
      ;;
  esac
done

log() { echo "[install.sh] $*"; }
run() {
  if [[ $DRY_RUN -eq 1 ]]; then
    log "DRY-RUN: $*"
  else
    eval "$@"
  fi
}

log "Sleepless QA installer — dry-run=${DRY_RUN}"
log "Script dir: ${SCRIPT_DIR}"
log "State dir: ${STATE_DIR}"
log "Venv dir: ${VENV_DIR}"

# -----------------------------------------------------------------------------
# 1. Precondition checks (fail fast with clear messages)
# -----------------------------------------------------------------------------

PY_BIN=""
for candidate in python3.12 python3.11 python3.10 python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    version=$("$candidate" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    major=$(echo "$version" | cut -d. -f1)
    minor=$(echo "$version" | cut -d. -f2)
    if [[ $major -ge 3 && $minor -ge 10 ]]; then
      PY_BIN="$candidate"
      log "Python: ${candidate} (${version}) OK"
      break
    fi
  fi
done
if [[ -z "$PY_BIN" ]]; then
  echo "[install.sh] ERROR: Python 3.10+ required. Install it first." >&2
  exit 1
fi

if [[ $SKIP_MINEFLAYER -eq 0 ]]; then
  if command -v node >/dev/null 2>&1; then
    node_major=$(node -e 'console.log(process.versions.node.split(".")[0])')
    if [[ $node_major -lt 20 ]]; then
      echo "[install.sh] ERROR: Node 20+ required for Mineflayer adapter. Found v${node_major}. Use --skip-mineflayer to bypass." >&2
      exit 1
    fi
    log "Node: v${node_major} OK"
  else
    echo "[install.sh] WARNING: Node not found. Mineflayer adapter will be unavailable. Pass --skip-mineflayer to silence." >&2
  fi
fi

if command -v dolphin-emu >/dev/null 2>&1; then
  log "Dolphin: available (Wii adapter enabled if configured)"
else
  log "Dolphin: not found (Wii adapter disabled — MC2.5 scope)"
fi

# -----------------------------------------------------------------------------
# 2. State directory
# -----------------------------------------------------------------------------
run "mkdir -p '${STATE_DIR}/runs' '${STATE_DIR}/heartbeat' '${STATE_DIR}/locks'"

# -----------------------------------------------------------------------------
# 3. Python venv + pip install
# -----------------------------------------------------------------------------
if [[ ! -d "$VENV_DIR" ]]; then
  run "${PY_BIN} -m venv '${VENV_DIR}'"
fi
run "'${VENV_DIR}/bin/pip' install --upgrade pip"
run "'${VENV_DIR}/bin/pip' install -r '${REQUIREMENTS}'"

# -----------------------------------------------------------------------------
# 4. Playwright browsers (optional skip)
# -----------------------------------------------------------------------------
if [[ $SKIP_PLAYWRIGHT -eq 0 ]]; then
  run "PLAYWRIGHT_BROWSERS_PATH='${PLAYWRIGHT_CACHE}' '${VENV_DIR}/bin/playwright' install --with-deps chromium"
  log "Playwright chromium installed at ${PLAYWRIGHT_CACHE}"
else
  log "Playwright install skipped (--skip-playwright)"
fi

# -----------------------------------------------------------------------------
# 5. Mineflayer node deps
# -----------------------------------------------------------------------------
if [[ $SKIP_MINEFLAYER -eq 0 ]]; then
  run "mkdir -p '${MINEFLAYER_DIR}'"
  if [[ ! -f "${MINEFLAYER_DIR}/package.json" ]]; then
    run "cd '${MINEFLAYER_DIR}' && npm init -y >/dev/null"
  fi
  run "cd '${MINEFLAYER_DIR}' && npm install mineflayer@4 --silent"
  log "Mineflayer installed at ${MINEFLAYER_DIR}"
fi

# -----------------------------------------------------------------------------
# 6. Env file template
# -----------------------------------------------------------------------------
if [[ ! -f /etc/sleepless-qa.env && $DRY_RUN -eq 0 ]]; then
  log "WARNING: /etc/sleepless-qa.env missing. Copy from config.example.env and fill in values before starting the systemd service."
fi

log "Install complete."
log "Next steps:"
log "  1. Copy config.example.env to /etc/sleepless-qa.env and fill ANTHROPIC_API_KEY"
log "  2. Run: ${VENV_DIR}/bin/python -m sleepless_qa heartbeat"
log "  3. If heartbeat alive: systemctl enable --now sleepless-qa.service"
