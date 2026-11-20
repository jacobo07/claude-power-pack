#!/usr/bin/env bash
# BCAP-2 Phase 9 canary: run the REAL ruflo 3.78.0 MCP server in an isolated container and drive one steps file.
# Isolation: --network none (proved per run by a NET probe that must FAIL), read-only rootfs, tmpfs HOME and workdir,
# install mounted read-only, cap-drop ALL, no-new-privileges, non-root user. Nothing leaves the container except stdout.
# usage: run_canary.sh <steps.json>      (on GEX44; needs docker group membership)
set -euo pipefail
S=/home/kobii/ruflo-sandbox-bcap2/run
HERE="$(cd "$(dirname "$0")" && pwd)"
STEPS="$(realpath "$1")"
IMG=node:24-bookworm
D=(docker run --rm -i --network none --read-only --tmpfs /tmp:exec --tmpfs /home/node --user node -e HOME=/home/node -e CI=1
   --cap-drop ALL --security-opt no-new-privileges -v "$S/install:/sb:ro" -v "$HERE:/drill:ro" -v "$STEPS:/steps.json:ro"
   -w /tmp "$IMG")
probe=$("${D[@]}" node -e 'require("https").get("https://registry.npmjs.org/",r=>console.log("NET_OK")).on("error",e=>console.log("NET_FAIL"))')
echo "{\"case\":\"isolation_probe\",\"text\":\"$probe\"}"
[ "$probe" = "NET_FAIL" ] || { echo '{"case":"ABORT","text":"network reachable inside the container"}'; exit 9; }
"${D[@]}" timeout 600 node /drill/driver.cjs /steps.json
