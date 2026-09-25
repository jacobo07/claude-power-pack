#!/usr/bin/env bash
# Unit A's whole job: decide whether the harness is SERVICEABLE, and publish the
# answer as systemd state so unit B has a precondition it cannot talk its way past.
#
# WHY UNIT A IS NOT A RESIDENT BEAM, WHICH IS WHAT I PROPOSED.
#
# The plan called for a resident node so goal firings would not pay boot cost.
# Measured on GEX44, 2026-09-25, against the already-compiled tree:
#
#     module reachable, no Mix                    0.58 s
#     39 applications started                     1.63 s   rss 92 MB
#     end-to-end call to the pinned model         2.41 s   rss 97 MB
#                                                 -> text="PONG"
#                                                 -> served_by={:local,"llama.cpp"}
#
# Residency therefore buys about 1.6 s per firing, and costs a permanent 92 MB
# BEAM, an epmd, a cookie and a distribution socket on a host already carrying
# 15 production services with 5.9 GB of free RAM. On a timer that fires a few
# bounded epochs an hour that trade is not close, and an agentic epoch amortises
# the boot inside itself anyway. The measurement refuted the design, so the
# design changed rather than the measurement being explained away.
#
# What DOES need serving is the thing the same measurement found broken: the
# harness has no reproducible environment. `mix` does not run from a clean
# shell, the shims do not resolve, and a stale OTP-27 Elixir that core-dumps the
# VM is still on disk one PATH entry away. Unit A owns that environment, proves
# it end to end, and holds `active` for exactly as long as the proof stood up.
#
# Three outcomes, never two:
#   exit 0  SERVICEABLE           every rung was climbed, including a real call
#   exit 2  NOT_SERVICEABLE       a precondition is absent; nothing is claimed
#                                 about the harness, and unit B must not fire
#   exit 1  CHECK_FAILED          a rung ran and failed; see the named rung
set -uo pipefail

# ---- SCOPE AS CONSTANTS -----------------------------------------------------
EXPECT_ELIXIR="/home/kobii/keos/mise-data/installs/elixir/1.17.3-otp-26/bin/elixir"
EXPECT_OTP_MAJOR="26"
EXPECT_ELIXIR_VSN="1.17.3"
SVC_DIR="/home/kobii/keos/keos_qwen_svc"
EBIN_GLOB="${SVC_DIR}/_build/dev/lib/keos_qwen/ebin"
LEDGER_SCRIPT="/home/kobii/keos/keos_qwen/ledger/ledger.py"
LEDGER_ROOT="${KEOS_QWEN_LEDGER_ROOT:-/home/kobii/keos/ledger}"
LLM_SERVICE="keos-llm.service"
LLM_ENDPOINT="127.0.0.1:8081"
PROBE_MAX_TOKENS=16
# The OTP-27 Elixir that aborted the VM on install run 1. Named so a PATH that
# reaches it is a FINDING and not a coincidence nobody looked at.
POISON_ELIXIR="/home/kobii/keos/mise-data/installs/elixir/1.17.3-otp-27/bin/elixir"
# -----------------------------------------------------------------------------

rung()  { printf '\n--- RUNG: %s ---\n' "$1"; }
nope()  { printf '\nNOT_SERVICEABLE: %s\n' "$1"; exit 2; }
fail()  { printf '\nCHECK_FAILED: %s\n' "$1"; exit 1; }

rung "identity"
me="$(whoami)"
printf 'whoami=%s\n' "$me"
[ "$me" = "kobii" ] || nope "running as ${me}, not kobii"

rung "the inference service, BEFORE -- so we can prove by pid identity we left it alone"
llm_before="$(systemctl is-active "$LLM_SERVICE" 2>/dev/null || true)"
llm_pid_before="$(systemctl show -p MainPID --value "$LLM_SERVICE" 2>/dev/null || echo 0)"
printf 'llm=%s main_pid=%s\n' "$llm_before" "$llm_pid_before"
[ "$llm_before" = "active" ] || nope "${LLM_SERVICE} is '${llm_before}'; the harness has nothing to talk to"

rung "the exact interpreter, by PATH and not by name"
[ -x "$EXPECT_ELIXIR" ] || nope "no executable at ${EXPECT_ELIXIR}"
resolved="$(command -v elixir || true)"
printf 'command -v elixir = %s\n' "$resolved"
[ "$resolved" = "$EXPECT_ELIXIR" ] || \
  fail "PATH resolves elixir to '${resolved}', not the pinned ${EXPECT_ELIXIR}. \
This is the exact shape that made install run 1 core-dump: an Elixir built for \
another OTP, reached by name."

rung "poison check: the OTP-27 build must not be reachable first"
if [ -e "$POISON_ELIXIR" ] && [ "$resolved" = "$POISON_ELIXIR" ]; then
  fail "PATH reaches the OTP-27 Elixir that aborts this VM (core dumped, run 1)"
fi
if [ -e "$POISON_ELIXIR" ]; then
  printf 'note: the OTP-27 build is still on disk at %s and is NOT on our PATH. \
It is left in place deliberately -- deleting it would hide the hazard rather \
than pin against it.\n' "$POISON_ELIXIR"
fi

rung "MATCH, not minimum: the Elixir build and the running VM must name the same OTP"
ver_out="$("$EXPECT_ELIXIR" --version 2>&1)" || fail "elixir --version did not run: ${ver_out}"
printf '%s\n' "$ver_out"
vm_otp="$(printf '%s' "$ver_out" | grep -oE 'Erlang/OTP [0-9]+' | head -1 | grep -oE '[0-9]+$')"
built_otp="$(printf '%s' "$ver_out" | grep -oE 'compiled with Erlang/OTP [0-9]+' | head -1 | grep -oE '[0-9]+$')"
ex_vsn="$(printf '%s' "$ver_out" | grep -oE 'Elixir [0-9]+\.[0-9]+\.[0-9]+' | head -1 | grep -oE '[0-9.]+$')"
printf 'vm_otp=%s built_otp=%s elixir=%s\n' "${vm_otp:-?}" "${built_otp:-?}" "${ex_vsn:-?}"
[ -n "$vm_otp" ] && [ -n "$built_otp" ] || fail "could not read both OTP numbers out of: ${ver_out}"
# The assertion install run 1 did not have. Its check printed "Erlang/OTP 26"
# next to "compiled with Erlang/OTP 27" and PASSED, because it only asserted
# otp >= 26. A precompiled artifact asserts MATCH. (HR-KEOSQ-01)
[ "$vm_otp" = "$built_otp" ] || \
  fail "Elixir was built for OTP ${built_otp} but the VM is OTP ${vm_otp}. Not a \
minimum -- these must be EQUAL, and run 1 died exactly here."
[ "$vm_otp" = "$EXPECT_OTP_MAJOR" ] || fail "OTP ${vm_otp}, expected ${EXPECT_OTP_MAJOR}"
[ "$ex_vsn" = "$EXPECT_ELIXIR_VSN" ] || fail "Elixir ${ex_vsn}, expected ${EXPECT_ELIXIR_VSN}"

rung "locale: a latin1 VM malfunctions on utf8 source"
printf 'LANG=%s LC_ALL=%s\n' "${LANG:-unset}" "${LC_ALL:-unset}"
case "${LC_ALL:-${LANG:-}}" in
  *UTF-8|*utf8) : ;;
  *) fail "locale is '${LC_ALL:-${LANG:-unset}}'; the VM warns it runs with native name encoding latin1" ;;
esac

rung "the compiled artifact is where ERL_LIBS says it is"
printf 'ERL_LIBS=%s\n' "${ERL_LIBS:-unset}"
[ -n "${ERL_LIBS:-}" ] || nope "ERL_LIBS is not set; the unit's EnvironmentFile did not load"
[ -d "$EBIN_GLOB" ] || nope "no compiled keos_qwen at ${EBIN_GLOB}; the project has not been built"
beams="$(find "$EBIN_GLOB" -name '*.beam' 2>/dev/null | wc -l)"
apps="$(find "${SVC_DIR}/_build/dev/lib" -maxdepth 1 -mindepth 1 -type d 2>/dev/null | wc -l)"
printf 'keos_qwen beams=%s  built apps=%s\n' "$beams" "$apps"
[ "$beams" -ge 1 ] || nope "keos_qwen/ebin holds no .beam files"
[ "$apps" -ge 30 ] || nope "only ${apps} built applications; the harness tree looks incomplete"

rung "the ledger answers, and its three exit codes still mean what the provider reads"
[ -f "$LEDGER_SCRIPT" ] || nope "no ledger at ${LEDGER_SCRIPT}"
led_out="$(python3 "$LEDGER_SCRIPT" status --root "$LEDGER_ROOT" 2>&1)"; led_rc=$?
printf 'ledger status rc=%s out=%s\n' "$led_rc" "$led_out"
[ "$led_rc" -eq 0 ] || fail "the ledger could not answer (rc=${led_rc}): ${led_out}"

rung "the endpoint is listening on loopback"
if command -v ss >/dev/null 2>&1; then
  ss -ltn 2>/dev/null | grep -q "$LLM_ENDPOINT" || nope "nothing is listening on ${LLM_ENDPOINT}"
  printf 'listening on %s\n' "$LLM_ENDPOINT"
else
  printf 'ss is absent; skipping the socket rung (the call rung below is the one that matters)\n'
fi

rung "END TO END -- the only rung that proves a harness rather than a filesystem"
# This spends exactly one metered call. Every rung above can pass against a tree
# that cannot actually answer, so a serviceability unit that stopped short of a
# real call would be asserting about files.
probe_out="$("$EXPECT_ELIXIR" -e '
{:ok, _} = Application.ensure_all_started(:claude_code)
res = KeosQwen.Provider.ask("Reply with exactly the word PONG and nothing else.",
        ledger_script: System.get_env("KEOS_QWEN_LEDGER_SCRIPT"),
        ledger_root: System.get_env("KEOS_QWEN_LEDGER_ROOT"),
        max_tokens: String.to_integer(System.get_env("KEOS_PROBE_MAX_TOKENS") || "16"))
case res do
  {:ok, m} ->
    text = m |> Map.get(:content, []) |> Enum.map(&Map.get(&1, :text, "")) |> Enum.join()
    {where, server} = KeosQwen.Provider.served_by(m)
    IO.puts("PROBE where=" <> to_string(where) <> " server=" <> inspect(server) <>
            " model=" <> inspect(Map.get(m, :model)) <> " text=" <> inspect(text))
  {:refused, code, why} -> IO.puts("PROBE refused=" <> code <> " " <> inspect(why))
  {:unavailable, why}   -> IO.puts("PROBE unavailable=" <> inspect(why))
  other                 -> IO.puts("PROBE error=" <> inspect(other))
end
' 2>&1)" || true
printf '%s\n' "$probe_out" | tail -5

probe_line="$(printf '%s' "$probe_out" | grep -o 'PROBE .*' | head -1)"
[ -n "$probe_line" ] || fail "the probe produced no PROBE line at all; the harness did not run"

case "$probe_line" in
  # A refusal is the ledger working. The harness is serviceable; we are simply
  # out of budget or switched off. That must NOT read as a broken harness, and
  # it must not read as serviceable either -- unit B has nothing to spend.
  *refused=*)     printf '\n'; nope "the ledger refuses right now: ${probe_line}" ;;
  *unavailable=*) fail "could not consult the ledger: ${probe_line}" ;;
  *error=*)       fail "the call reached the harness and failed: ${probe_line}" ;;
esac

case "$probe_line" in
  *"where=local"*) : ;;
  *"where=remote"*) fail "THE REQUEST EGRESSED. ${probe_line} -- this is T-KEOSQ-02: a \
local-model harness silently falling back to a remote API is a data-egress surface." ;;
  *) fail "could not establish where the response came from: ${probe_line}" ;;
esac

case "$probe_line" in
  *PONG*) : ;;
  *) fail "the model answered, but not the probe: ${probe_line}" ;;
esac

rung "postflight: prove by PID IDENTITY that we did not touch the inference service"
llm_after="$(systemctl is-active "$LLM_SERVICE" 2>/dev/null || true)"
llm_pid_after="$(systemctl show -p MainPID --value "$LLM_SERVICE" 2>/dev/null || echo 0)"
printf 'llm=%s main_pid=%s (was %s)\n' "$llm_after" "$llm_pid_after" "$llm_pid_before"
# "still active" is satisfied by a service that was restarted and came back. Only
# the pid says the process we measured before is the process running now.
[ "$llm_pid_after" = "$llm_pid_before" ] || \
  fail "${LLM_SERVICE} pid moved ${llm_pid_before} -> ${llm_pid_after}: something restarted it"

printf '\nSERVICEABLE: %s\n' "$probe_line"
printf 'environment: elixir=%s otp=%s erl_libs=%s ledger_root=%s\n' \
  "$EXPECT_ELIXIR" "$vm_otp" "$ERL_LIBS" "$LEDGER_ROOT"
exit 0
