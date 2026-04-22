#!/usr/bin/env bash
# run_vps.sh -- Local launcher for the VPS validation bundle.
#
# Pipes tools/vps_validation_handoff.sh over SSH stdin using a heredoc, so
# terminal-wrap of the command line cannot corrupt the remote payload.
#
# Usage (from the claude-power-pack working tree on the local Windows host):
#   bash tools/run_vps.sh              # logs to /tmp/vps.log
#   bash tools/run_vps.sh /tmp/x.log   # logs to a custom path
#
# Environment overrides:
#   VPS_HOST    default root@204.168.166.63
#   VPS_KEY     default ~/.ssh/kobicraft_vps
#   REPO_URL    default https://github.com/jacobo07/claude-power-pack.git
#   REPO_DIR    default /root/claude-power-pack (path on the VPS)

set -uo pipefail

HOST="${VPS_HOST:-root@204.168.166.63}"
KEY="${VPS_KEY:-$HOME/.ssh/kobicraft_vps}"
REPO_URL="${REPO_URL:-https://github.com/jacobo07/claude-power-pack.git}"
REPO_DIR="${REPO_DIR:-/root/claude-power-pack}"
LOG="${1:-/tmp/vps.log}"

echo "[run_vps] host=$HOST key=$KEY repo=$REPO_DIR log=$LOG"
echo "[run_vps] streaming handoff via ssh 'bash -s' -- heredoc payload is wrap-proof"

ssh -i "$KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=15 "$HOST" 'bash -s' <<REMOTE 2>&1 | tee "$LOG"
set -u
REPO="$REPO_DIR"
if [ ! -d "\$REPO" ]; then
    echo "[remote] cloning $REPO_URL -> \$REPO"
    git clone "$REPO_URL" "\$REPO"
fi
cd "\$REPO"
echo "[remote] git pull --ff-only"
git pull --ff-only
echo "[remote] bash tools/vps_validation_handoff.sh"
bash tools/vps_validation_handoff.sh
REMOTE

RC=${PIPESTATUS[0]}
echo ""
echo "[run_vps] ssh exit=$RC  log=$LOG  size=$(wc -c < "$LOG" 2>/dev/null || echo 0)B"
echo "[run_vps] tail:"
tail -20 "$LOG" 2>/dev/null
exit "$RC"
