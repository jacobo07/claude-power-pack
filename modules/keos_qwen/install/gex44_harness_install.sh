#!/usr/bin/env bash
# KEOS-Qwen -- install the agentic harness on GEX44.
#
# Authorised 2026-09-24 by HR-04: "AUTHORIZED: deploy directo porque necesito
# ese harness". The scope of that phrase lives HERE, as constants, not in the
# plan that requested it. Incident W14 (2026-09-17) wrote to five production
# backends because its scope lived in prose; the same day's correct execution
# carried the uuid and filenames as constants so it could not overflow even if
# the operator forgot. This file is built the second way.
#
# Three outcomes, never two:
#   exit 0  OK                     the harness is installed and compiled
#   exit 2  ABORTED_PRECONDITION   the host could not host the install; nothing
#                                  about the harness is claimed either way
#   exit 1  FAILED                 a step ran and failed; see the named step
#
# NOT IN SCOPE, and enforced by absence rather than by comment:
#   - no systemd unit is written by this script
#   - keos-llm.service is never stopped, restarted or reconfigured
#   - the model served on 127.0.0.1:8081 is never replaced
# Those three were authorised separately on 2026-09-24 and are deliberately not
# exercised here: a phrase covers exactly what it says, and an install that
# quietly restarts the inference service is not an install.
set -euo pipefail

# ---- SCOPE AS CONSTANTS -----------------------------------------------------
KEOS_USER="kobii"
KEOS_ROOT="/home/kobii/keos"
KEOS_MARKER="${KEOS_ROOT}/.keos-install-marker"
HARNESS_REPO="https://github.com/Miosa-osa/osa-claude-code.git"
HARNESS_DIR="${KEOS_ROOT}/osa-claude-code"
DISK_FLOOR_GB=100
REQUIRED_OTP_MAJOR=26
# EXACT, not "1.17". Run 1 of this script pinned the minor version only, mise
# resolved it to 1.17.3-otp-27, and the OTP-27 precompiled Elixir aborted the
# OTP-26 VM with "size_object: matchstate term not allowed (core dumped)" on the
# first mix command. An Elixir build is specific to the OTP that compiled it.
REQUIRED_ELIXIR="1.17.3-otp-26"
BUILD_DEPS="autoconf automake libtool libncurses-dev"
LLM_SERVICE="keos-llm.service"
# -----------------------------------------------------------------------------

export MISE_DATA_DIR="${KEOS_ROOT}/mise-data"
export MISE_CONFIG_DIR="${KEOS_ROOT}/mise-config"
export MISE_CACHE_DIR="${KEOS_ROOT}/mise-cache"
MISE="${KEOS_ROOT}/bin/mise"

step() { printf '\n=== STEP: %s ===\n' "$1"; }
abort() { printf '\nABORTED_PRECONDITION: %s\n' "$1"; exit 2; }
fail()  { printf '\nFAILED: %s\n' "$1"; exit 1; }

step "preflight: identity"
me="$(whoami)"
printf 'whoami=%s expected=%s\n' "$me" "$KEOS_USER"
[ "$me" = "$KEOS_USER" ] || abort "running as ${me}, not ${KEOS_USER}"

step "preflight: disk floor"
# The host was measured at 93 percent and draining on its own (the Hive
# ingestion pulls video with --max-filesize 2G). A build that starts on a full
# disk fails halfway and leaves a tree nobody can classify.
avail_gb="$(df -BG --output=avail / | tail -1 | tr -dc '0-9')"
printf 'avail_gb=%s floor_gb=%s\n' "$avail_gb" "$DISK_FLOOR_GB"
[ "$avail_gb" -ge "$DISK_FLOOR_GB" ] || abort "only ${avail_gb}GB free, floor is ${DISK_FLOOR_GB}GB"

step "preflight: inference service must be up BEFORE, so we can prove we left it alone"
llm_before="$(systemctl is-active "$LLM_SERVICE" || true)"
llm_pid_before="$(systemctl show -p MainPID --value "$LLM_SERVICE" || echo 0)"
printf 'llm_before=%s main_pid=%s\n' "$llm_before" "$llm_pid_before"
[ "$llm_before" = "active" ] || abort "${LLM_SERVICE} is ${llm_before}; refusing to install beside a down inference service"

step "preflight: ours to resume, or someone else's to leave alone"
# A marker written by US is what distinguishes "this script's half-finished run"
# from "a directory somebody else owns". Bare existence cannot tell those apart,
# and the first version of this script aborted on both -- which made a mid-way
# failure unresumable. Same shape as the epoch marker codex.py writes BEFORE the
# spawn so a lost handle is distinguishable from a process that never started.
if [ -e "$KEOS_ROOT" ] && [ ! -f "$KEOS_MARKER" ]; then
  abort "${KEOS_ROOT} exists without our marker; refusing to write into a tree this script did not create"
fi
mkdir -p "$KEOS_ROOT"
printf 'keos-qwen install marker; created %s\n' "$(date -Is)" >> "$KEOS_MARKER"

step "build dependencies (stock Ubuntu archive, no third-party repo, no GPG key)"
sudo -n apt-get update -qq || fail "apt-get update"
# shellcheck disable=SC2086
sudo -n DEBIAN_FRONTEND=noninteractive apt-get install -y -qq $BUILD_DEPS || fail "apt-get install ${BUILD_DEPS}"
for h in /usr/include/ncurses.h /usr/include/openssl/ssl.h /usr/include/zlib.h; do
  [ -f "$h" ] || fail "header still missing after install: ${h}"
done
command -v autoconf >/dev/null || fail "autoconf still absent after install"
printf 'build deps present\n'

step "mise (user-local version manager, ${KEOS_ROOT} only)"
if [ ! -x "$MISE" ]; then
  curl -fsSL https://mise.run | MISE_INSTALL_PATH="$MISE" sh || fail "mise install"
fi
[ -x "$MISE" ] || fail "mise not executable at ${MISE}"
"$MISE" --version || fail "mise --version"

step "erlang OTP ${REQUIRED_OTP_MAJOR}"
"$MISE" use -g "erlang@${REQUIRED_OTP_MAJOR}" || fail "erlang install"

step "elixir ${REQUIRED_ELIXIR}"
"$MISE" use -g "elixir@${REQUIRED_ELIXIR}" || fail "elixir install"

step "verify the toolchain by RUNNING it, and by COMPARING what it prints"
eval "$("$MISE" activate bash)" || fail "mise activate"
otp="$(erl -noshell -eval 'io:format("~s",[erlang:system_info(otp_release)]),halt().')" || fail "erl did not run"
printf 'runtime_otp=%s\n' "$otp"
[ "$otp" -ge "$REQUIRED_OTP_MAJOR" ] || fail "OTP ${otp} is below required ${REQUIRED_OTP_MAJOR}"
elixir --version || fail "elixir did not run"
elixir_otp="$(elixir --version | grep -oE 'compiled with Erlang/OTP [0-9]+' | grep -oE '[0-9]+$')" \
  || fail "could not read the OTP version Elixir was compiled with"
printf 'elixir_built_for_otp=%s runtime_otp=%s\n' "$elixir_otp" "$otp"
# THE ASSERTION THAT RUN 1 DID NOT HAVE, and the reason it cost a run:
# run 1 executed both tools, PRINTED "Erlang/OTP 26" beside "compiled with
# Erlang/OTP 27", asserted only that otp >= 26, and passed. The gate printed the
# evidence of its own failure next to its verdict and did not read it. A verdict
# that contradicts the evidence it quotes means the check is wrong, not the world.
[ "$elixir_otp" = "$otp" ] || fail \
  "Elixir was built for OTP ${elixir_otp} but the runtime is OTP ${otp}. A precompiled Elixir is specific to the OTP that compiled it; run 1 of this script hit exactly this and the VM aborted with 'size_object: matchstate term not allowed (core dumped)' on the first mix command."

step "clone the harness"
if [ ! -d "${HARNESS_DIR}/.git" ]; then
  git clone --depth 1 "$HARNESS_REPO" "$HARNESS_DIR" || fail "git clone"
fi
cd "$HARNESS_DIR"
printf 'harness_head=%s\n' "$(git rev-parse HEAD)"

step "compile the harness"
export MIX_ENV=prod
mix local.hex --force || fail "mix local.hex"
mix local.rebar --force || fail "mix local.rebar"
mix deps.get || fail "mix deps.get"
mix compile || fail "mix compile"

step "postflight: prove we left the inference service alone"
llm_after="$(systemctl is-active "$LLM_SERVICE" || true)"
llm_pid_after="$(systemctl show -p MainPID --value "$LLM_SERVICE" || echo 0)"
printf 'llm_after=%s main_pid=%s\n' "$llm_after" "$llm_pid_after"
[ "$llm_after" = "active" ] || fail "${LLM_SERVICE} is ${llm_after} after the install"
# A restarted service comes back active with a DIFFERENT pid. "Still active" is
# not the claim; "same process, never touched" is.
[ "$llm_pid_after" = "$llm_pid_before" ] || fail "${LLM_SERVICE} pid moved ${llm_pid_before} -> ${llm_pid_after}: something restarted it"

step "postflight: disk delta"
avail_after="$(df -BG --output=avail / | tail -1 | tr -dc '0-9')"
printf 'avail_gb_before=%s avail_gb_after=%s consumed_gb=%s\n' \
  "$avail_gb" "$avail_after" "$((avail_gb - avail_after))"

step "postflight: no systemd unit was written by this script"
if systemctl list-unit-files 2>/dev/null | grep -q 'keos-qwen'; then
  fail "a keos-qwen unit exists; this script does not write one and must not have"
fi

printf '\nOK: harness installed at %s\n' "$HARNESS_DIR"
printf 'To point it at the local model the caller sets OLLAMA_HOST=http://127.0.0.1:8081\n'
printf 'That is deliberately NOT done here: this script installs, it does not configure a runtime.\n'
exit 0
