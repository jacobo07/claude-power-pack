#!/usr/bin/env bash
# KEOS-Qwen -- install the two systemd units on GEX44.
#
# Authorised 2026-09-24 by the Owner, verbatim: "autorizo esto tambien: [unidad
# systemd (seria el demonio que prohibe la carta K-ADOS), tocar
# keos-llm.service, y reemplazar el modelo de :8081] porque lo necesito".
#
# That sentence authorises THREE things. This script exercises ONE, and the
# other two are enforced-by-absence exactly as the harness installer did it:
#
#   IN SCOPE      the two user units, their environment file, their scripts
#   NOT EXERCISED keos-llm.service is never started, stopped or reconfigured
#   NOT EXERCISED the model on 127.0.0.1:8081 is never replaced
#
# The two unexercised permissions are recorded as authorised-and-unused, which
# is a different state from forbidden. Replacing a served model today would be
# promoting on the strength of a permission rather than of evidence: there is no
# frozen corpus, no baseline, no candidate and no proven rollback. A permission
# is not a reason.
#
# USER UNITS, NOT SYSTEM UNITS, and that is the safety argument rather than a
# convenience. A user manager has no authority over keos-llm.service, so the
# first two "not exercised" lines above are true by PERMISSION and cannot be
# undone by a future edit to a script.
#
# Three outcomes, never two:
#   exit 0  OK                   both units are installed and unit A proved the
#                                harness serviceable end to end
#   exit 2  ABORTED_PRECONDITION the host could not host them; nothing was
#                                installed and nothing is claimed
#   exit 1  FAILED               a step ran and failed; see the named step
set -uo pipefail

# ---- SCOPE AS CONSTANTS -----------------------------------------------------
KEOS_USER="kobii"
KEOS_ROOT="/home/kobii/keos"
PKG_DIR="${KEOS_ROOT}/keos_qwen"
UNIT_SRC="${PKG_DIR}/units"
GOALS_SRC="${PKG_DIR}/goals"
SYSTEMD_USER_DIR="/home/kobii/.config/systemd/user"
GOALS_TREE="${KEOS_ROOT}/goals"
LEDGER_ROOT="${KEOS_ROOT}/ledger"
SVC_UNIT="keos-qwen-svc.service"
GOALS_UNIT="keos-qwen-goals.service"
GOALS_TIMER="keos-qwen-goals.timer"
LLM_SERVICE="keos-llm.service"
DISK_FLOOR_GB=20
# -----------------------------------------------------------------------------

step()  { printf '\n=== STEP: %s ===\n' "$1"; }
abort() { printf '\nABORTED_PRECONDITION: %s\n' "$1"; exit 2; }
fail()  { printf '\nFAILED: %s\n' "$1"; exit 1; }

step "preflight: identity"
me="$(whoami)"
printf 'whoami=%s expected=%s\n' "$me" "$KEOS_USER"
[ "$me" = "$KEOS_USER" ] || abort "running as ${me}, not ${KEOS_USER}"
# Refusing root is not pedantry: as root these become system units, and a system
# unit CAN restart keos-llm.service. The containment argument above is only true
# while this runs unprivileged.
[ "$(id -u)" != "0" ] || abort "running as root would install SYSTEM units, which can reach keos-llm.service"

step "preflight: disk"
avail_gb="$(df -BG --output=avail "$KEOS_ROOT" | tail -1 | tr -dc '0-9')"
printf 'avail_gb=%s floor_gb=%s\n' "$avail_gb" "$DISK_FLOOR_GB"
[ "${avail_gb:-0}" -ge "$DISK_FLOOR_GB" ] || abort "only ${avail_gb}GB free at ${KEOS_ROOT}"

step "preflight: the user manager must be able to own units that survive logout"
# `is-system-running` exits NON-ZERO for "degraded", which means the manager is
# perfectly usable and some unit somewhere has failed. Reading that as "no
# manager" made this installer SELF-LOCKING: the broken unit it exists to repair
# put the manager into degraded, and the installer then refused to install the
# repair. Measured 2026-09-25 -- it cost a whole cycle and read like a host
# problem.
#
# A preflight has to be about ITS OWN precondition. "Is there a manager" and
# "are all its units healthy" are different questions, and this step is only
# entitled to ask the first.
sysstate="$(systemctl --user is-system-running 2>/dev/null || true)"
printf 'user manager state: %s\n' "${sysstate:-unreachable}"
case "$sysstate" in
  running|degraded|starting|maintenance|stopping) : ;;
  *) abort "no usable systemd --user manager for ${KEOS_USER} (state='${sysstate:-unreachable}')" ;;
esac
if [ "$sysstate" = "degraded" ]; then
  printf 'degraded -- these units are in a failed state (information, not a blocker):\n'
  systemctl --user list-units --state=failed --no-pager --no-legend 2>/dev/null | sed 's/^/    /'
fi
linger="$(loginctl show-user "$KEOS_USER" -p Linger --value 2>/dev/null || echo unknown)"
printf 'Linger=%s\n' "$linger"
# Without lingering the units die at logout and never start at boot -- which
# makes an "installed" timer that silently does not exist most of the time.
[ "$linger" = "yes" ] || abort "lingering is '${linger}'; these units would not survive logout or reach boot"

step "preflight: the inference service, BEFORE -- so the postflight can prove pid identity"
llm_before="$(systemctl is-active "$LLM_SERVICE" 2>/dev/null || true)"
llm_pid_before="$(systemctl show -p MainPID --value "$LLM_SERVICE" 2>/dev/null || echo 0)"
printf 'llm=%s main_pid=%s\n' "$llm_before" "$llm_pid_before"
[ "$llm_before" = "active" ] || abort "${LLM_SERVICE} is '${llm_before}'; refusing to install a goal loop beside a down endpoint"

step "preflight: the payload this script is supposed to install"
for f in "${UNIT_SRC}/keos-qwen.env" "${UNIT_SRC}/serviceable.sh" \
         "${UNIT_SRC}/${SVC_UNIT}" "${UNIT_SRC}/${GOALS_UNIT}" "${UNIT_SRC}/${GOALS_TIMER}" \
         "${GOALS_SRC}/fire.py" "${GOALS_SRC}/attempt.exs" \
         "${PKG_DIR}/ledger/ledger.py" "${PKG_DIR}/outcome.py" "${PKG_DIR}/__init__.py"; do
  [ -f "$f" ] || abort "missing payload member ${f}"
done
printf 'all 10 payload members present\n'

step "prepare the trees the units are allowed to write to"
# These are the ONLY paths in the units' ReadWritePaths. If a unit ever needs a
# path that is not created here, that is a scope change and it should fail
# loudly rather than be granted quietly.
mkdir -p "$LEDGER_ROOT" "${GOALS_TREE}/queue" "${GOALS_TREE}/evidence" "${GOALS_TREE}/done" \
  || fail "could not create the writable trees"
chmod 700 "$LEDGER_ROOT" "$GOALS_TREE"
printf 'ledger=%s goals=%s\n' "$LEDGER_ROOT" "$GOALS_TREE"

step "make the scripts executable"
chmod +x "${UNIT_SRC}/serviceable.sh" || fail "chmod serviceable.sh"
printf 'serviceable.sh: %s\n' "$(ls -l "${UNIT_SRC}/serviceable.sh" | awk '{print $1}')"

step "install the unit files"
mkdir -p "$SYSTEMD_USER_DIR" || fail "could not create ${SYSTEMD_USER_DIR}"
for u in "$SVC_UNIT" "$GOALS_UNIT" "$GOALS_TIMER"; do
  cp -f "${UNIT_SRC}/${u}" "${SYSTEMD_USER_DIR}/${u}" || fail "could not install ${u}"
  src_sha="$(sha256sum "${UNIT_SRC}/${u}" | cut -d' ' -f1)"
  dst_sha="$(sha256sum "${SYSTEMD_USER_DIR}/${u}" | cut -d' ' -f1)"
  printf '%s  src=%s dst=%s\n' "$u" "${src_sha:0:12}" "${dst_sha:0:12}"
  # A copy is not a deployment until the bytes match. This is the same check
  # that proved the deployed ledger.py was not a drifting second copy.
  [ "$src_sha" = "$dst_sha" ] || fail "${u} does not match its source after copy"
done

step "daemon-reload, then let systemd PARSE the units before we trust them"
systemctl --user daemon-reload || fail "daemon-reload"
for u in "$SVC_UNIT" "$GOALS_UNIT" "$GOALS_TIMER"; do
  load="$(systemctl --user show -p LoadState --value "$u" 2>/dev/null || echo unknown)"
  printf '%s LoadState=%s\n' "$u" "$load"
  # "the file is on disk" and "systemd accepted it" are different facts.
  [ "$load" = "loaded" ] || fail "${u} did not load: LoadState=${load}"
done

step "DRIVE the containment claims -- do not read them"
# The first version of this step ran `systemctl show -p ProtectHome ...` and
# printed the configured values, which all looked right. They were not: on
# 2026-09-25 a unit carrying ProtectHome=read-only wrote /home/kobii and a unit
# carrying IPAddressDeny=any reached 1.1.1.1:443.
#
# `systemctl show` reports CONFIGURATION. Only a probe reports ENFORCEMENT, and
# systemd DEGRADES silently for a user manager that cannot build the namespace,
# so the two are routinely different. Every probe below carries both poles: a
# refusal with no paired admission is indistinguishable from a sandbox that
# refuses everything, and an admission with no paired refusal proves nothing.
probe() {  # probe <label> <sandbox-args...> -- <command>
  local label="$1"; shift
  local args=(); while [ "$1" != "--" ]; do args+=("$1"); shift; done; shift
  local out
  out="$(systemd-run --user --wait --collect --quiet --pipe "${args[@]}" \
         /bin/bash -c "$1" 2>&1)"
  printf '    %-34s %s\n' "$label" "$(printf '%s' "$out" | tr '\n' ' ')"
}

printf '  NoNewPrivileges (the load-bearing one: kobii has passwordless sudo)\n'
probe "with the directive:" -p NoNewPrivileges=yes -- \
  'sudo -n true 2>/dev/null && echo "ESCALATED -- NOT ENFORCED" || echo "refused: cannot escalate (ENFORCED)"'
probe "without it (control):" -- \
  'sudo -n true 2>/dev/null && echo "escalated, as expected without it" || echo "refused -- the control is broken, sudo is not available to kobii at all"'

printf '  Filesystem confinement\n'
probe "write outside ReadWritePaths:" -p ProtectHome=read-only \
  -p "ReadWritePaths=${LEDGER_ROOT} ${GOALS_TREE}" -- \
  'f=/home/kobii/.keosq_containment_probe; if echo x > $f 2>/dev/null; then unlink $f; echo "WROTE IT -- NOT ENFORCED"; else echo "refused (ENFORCED)"; fi'
probe "write inside (control):" -p ProtectHome=read-only \
  -p "ReadWritePaths=${LEDGER_ROOT} ${GOALS_TREE}" -- \
  "f=${LEDGER_ROOT}/.keosq_containment_probe; if echo x > \$f 2>/dev/null; then unlink \$f; echo 'wrote it, as it must'; else echo 'REFUSED -- the sandbox refuses everything, so the test above proves nothing'; fi"

printf '  Network confinement\n'
probe "egress to a public address:" -p IPAddressAllow=localhost -p IPAddressDeny=any -- \
  'timeout 6 bash -c "</dev/tcp/1.1.1.1/443" 2>/dev/null && echo "EGRESS SUCCEEDED -- NOT ENFORCED" || echo "refused (ENFORCED)"'
probe "loopback to :8081 (control):" -p IPAddressAllow=localhost -p IPAddressDeny=any -- \
  'timeout 6 bash -c "</dev/tcp/127.0.0.1/8081" 2>/dev/null && echo "loopback reachable, as it must be" || echo "LOOPBACK REFUSED -- the units cannot work"'

printf '  systemd build and kernel policy, which decide the three answers above:\n'
printf '    %s\n' "$(systemctl --version | head -1)"
printf '    BPF_FRAMEWORK: %s\n' "$(systemctl --version | grep -o '[+-]BPF_FRAMEWORK' || echo unknown)"
printf '    apparmor_restrict_unprivileged_userns: %s\n' \
  "$(cat /proc/sys/kernel/apparmor_restrict_unprivileged_userns 2>/dev/null || echo 'not present')"
printf '  NOTE: a NOT ENFORCED above is not a reason to stop. It is a reason not to\n'
printf '        CLAIM that fence. The unit files record which is which.\n'

step "unit A: enable and start -- this SPENDS exactly one metered call, on purpose"
systemctl --user enable "$SVC_UNIT" >/dev/null 2>&1 || fail "enable ${SVC_UNIT}"
systemctl --user start "$SVC_UNIT"
svc_rc="$(systemctl --user show -p ExecMainStatus --value "$SVC_UNIT" 2>/dev/null || echo unknown)"
svc_state="$(systemctl --user is-active "$SVC_UNIT" 2>/dev/null || true)"
printf '%s active=%s exit=%s\n' "$SVC_UNIT" "$svc_state" "$svc_rc"
journalctl --user -u "$SVC_UNIT" -n 40 --no-pager 2>/dev/null | sed 's/^/    /'

case "$svc_rc" in
  0) printf '\nunit A: SERVICEABLE\n' ;;
  2) abort "unit A reported NOT_SERVICEABLE (exit 2). The units are installed but \
the harness could not be proven; unit B will refuse to start, which is the \
designed behaviour and not a bug." ;;
  *) fail "unit A exited ${svc_rc}, which is neither SERVICEABLE (0) nor NOT_SERVICEABLE (2)" ;;
esac

step "unit B: enable the TIMER, do not fire"
# Enabling is safe because the QUEUE is the real switch: an empty queue exits 0
# having made no call at all. A first firing should be a deliberate act by
# somebody watching, not a side effect of installing.
queued="$(find "${GOALS_TREE}/queue" -name '*.json' 2>/dev/null | wc -l)"
printf 'queued goals: %s\n' "$queued"

# PROVE UNIT B CAN START, BEFORE ARMING A TIMER THAT POINTS AT IT.
#
# The first version of this installer enabled the timer and reported OK. Unit B
# could not start at all: ProtectKernelModules=yes exits 218/CAPABILITIES under
# an unprivileged user manager. The timer read "armed", `systemctl --user
# list-timers` showed a NEXT, and the whole autonomous leg was dead -- and would
# have stayed dead invisibly, because an empty queue ALSO exits 0 without doing
# anything, so "no evidence appeared" looks identical to "nothing was queued".
#
# An empty queue makes this smoke test free: fire.py exits 0 having made no call.
if [ "$queued" -eq 0 ]; then
  printf 'firing unit B once against the EMPTY queue -- a free proof that the unit starts\n'
  systemctl --user start "$GOALS_UNIT"
  b_rc="$(systemctl --user show -p ExecMainStatus --value "$GOALS_UNIT" 2>/dev/null || echo unknown)"
  b_res="$(systemctl --user show -p Result --value "$GOALS_UNIT" 2>/dev/null || echo unknown)"
  printf '%s exit=%s result=%s\n' "$GOALS_UNIT" "$b_rc" "$b_res"
  journalctl --user -u "$GOALS_UNIT" -n 12 --no-pager 2>/dev/null | sed 's/^/    /'
  case "$b_rc" in
    0|2) printf 'unit B starts and exits honestly.\n' ;;
    218) fail "unit B exits 218/CAPABILITIES: a hardening directive cannot be applied by \
an unprivileged user manager. Bisect the Protect*/Restrict* lines -- \
ProtectKernelModules is the known offender on this host." ;;
    *) fail "unit B exited ${b_rc} (result=${b_res}) on an EMPTY queue, which should be a \
no-op exit 0. The unit cannot run; arming a timer over it would hide that." ;;
  esac
else
  printf 'queue is not empty, so the free smoke test is skipped. UNIT B HAS NOT BEEN \
PROVEN TO START in this run -- that is an unmeasured gap, not a pass.\n'
fi

step "unit B: arm the timer"
# Enabling is safe because the QUEUE is the real switch: an empty queue exits 0
# having made no call. A first firing on real goals should be a deliberate act
# by somebody watching, not a side effect of installing.
systemctl --user enable "$GOALS_TIMER" >/dev/null 2>&1 || fail "enable ${GOALS_TIMER}"
systemctl --user start "$GOALS_TIMER" || fail "start ${GOALS_TIMER}"
systemctl --user list-timers "$GOALS_TIMER" --no-pager 2>/dev/null | sed 's/^/    /'

step "postflight: prove by PID IDENTITY that the inference service was never touched"
llm_after="$(systemctl is-active "$LLM_SERVICE" 2>/dev/null || true)"
llm_pid_after="$(systemctl show -p MainPID --value "$LLM_SERVICE" 2>/dev/null || echo 0)"
printf 'llm=%s main_pid=%s (was %s)\n' "$llm_after" "$llm_pid_after" "$llm_pid_before"
# "still active" is satisfied by a service that was restarted and came back.
[ "$llm_pid_after" = "$llm_pid_before" ] || \
  fail "${LLM_SERVICE} pid moved ${llm_pid_before} -> ${llm_pid_after}: something restarted it"

step "postflight: the model on :8081 is the one that was there"
ss -ltnp 2>/dev/null | grep ':8081' | sed 's/^/    /' || printf '    (ss unavailable)\n'

printf '\nOK: %s (active, proven) + %s (armed) installed as USER units.\n' "$SVC_UNIT" "$GOALS_TIMER"
printf 'Kill switches:\n'
printf '  stop a run in flight : touch %s/DISABLED\n' "$LEDGER_ROOT"
printf '  stop future firings  : systemctl --user disable --now %s\n' "$GOALS_TIMER"
printf '  stop everything      : systemctl --user stop %s %s\n' "$GOALS_TIMER" "$SVC_UNIT"
exit 0
