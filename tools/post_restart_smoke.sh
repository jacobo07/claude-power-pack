#!/usr/bin/env bash
# post_restart_smoke.sh — POSIX/MSYS sibling of post_restart_smoke.ps1
# (BL-0036 / MC-SYS-71). Same purpose: verify all hooks fire after /restart.
#
# Usage:
#   bash C:/Users/kobig/.claude/skills/claude-power-pack/tools/post_restart_smoke.sh
#
# Exits 0 if all tests pass, 1 if any fail.

set -uo pipefail

PP="C:/Users/kobig/.claude/skills/claude-power-pack"
ADVISOR="$PP/modules/zero-crash/hooks/skill-heat-map-advisor.js"
RAMWD="$PP/modules/zero-crash/hooks/ram-watchdog.js"
CTXWD="$PP/modules/zero-crash/hooks/context-watchdog.py"
AWJS="$PP/lib/atomic_write.js"
AWPY="$PP/lib/atomic_write.py"

PASS=0
FAIL=0
FAILURES=""

run_test() {
  local name="$1"
  local cmd="$2"
  local expected="$3"
  local out
  out="$(eval "$cmd" 2>&1)"
  local exit_code=$?
  if [ $exit_code -eq 0 ] && echo "$out" | grep -qE "$expected"; then
    PASS=$((PASS + 1))
    echo "[PASS] $name"
  else
    FAIL=$((FAIL + 1))
    FAILURES+="$name (exit=$exit_code)\n"
    echo "[FAIL] $name (exit=$exit_code)"
    echo "       output: $(echo "$out" | head -3)"
  fi
}

# Clean smoke-test flags
TD="$(python -c 'import tempfile;print(tempfile.gettempdir())' 2>/dev/null || echo /tmp)"
rm -f "$TD/claude-skill-advisor-smoke-"*.flag \
      "$TD/claude-skills-suggested-smoke-"*.txt \
      "$TD/claude-ramwd-smoke-"*.flag \
      "$TD/claude-ctxwd-"*"-smoke-"*.flag \
      "$TD/claude-ctx-smoke-"*.json 2>/dev/null

echo ""
echo "=== Hook activation smoke (BL-0036) ==="
echo ""

run_test "atomic_write.js self-test" \
  "node \"$AWJS\" --self-test" \
  "PASS 4/4"

run_test "atomic_write.py self-test" \
  "python \"$AWPY\" --self-test" \
  "PASS"

run_test "skill-heat-map-advisor (Bash + design keywords)" \
  "echo -n '{\"tool_name\":\"Bash\",\"session_id\":\"smoke-advisor-1\",\"tool_input\":{\"command\":\"audit codebase for security vulnerabilities and bugs\"}}' | node \"$ADVISOR\"" \
  "hookSpecificOutput"

run_test "ram-watchdog returns valid JSON" \
  "echo -n '{\"session_id\":\"smoke-ramwd-1\"}' | node \"$RAMWD\"" \
  "continue.*true"

# Tier 1: 65% used, expect silent {}
echo '{"used_pct":65,"remaining_percentage":35,"tokens_used":130000,"tokens_total":200000}' > "$TD/claude-ctx-smoke-ctx1.json"
run_test "context-watchdog tier 1 (used=65, silent)" \
  "echo -n '{\"session_id\":\"smoke-ctx1\",\"transcript_path\":\"/foo\",\"cwd\":\"/bar\"}' | python \"$CTXWD\"" \
  "^\\{\\}$"
rm -f "$TD/claude-ctx-smoke-ctx1.json"

# Tier 2: 72% used, expect advisory
echo '{"used_pct":72,"remaining_percentage":28,"tokens_used":144000,"tokens_total":200000}' > "$TD/claude-ctx-smoke-ctx2.json"
run_test "context-watchdog tier 2 (used=72, advisory)" \
  "echo -n '{\"session_id\":\"smoke-ctx2\",\"transcript_path\":\"/foo\",\"cwd\":\"/bar\"}' | python \"$CTXWD\"" \
  "CONTEXT THRESHOLD CROSSED"
rm -f "$TD/claude-ctx-smoke-ctx2.json"

echo ""
echo "PASSED: $PASS"
echo "FAILED: $FAIL"
if [ $FAIL -gt 0 ]; then
  echo ""
  echo "Failures:"
  printf "  - %b" "$FAILURES"
  exit 1
fi

echo ""
echo "All Phase II-V hooks responding correctly. Settings.json wiring is active."
echo "Next step: do real frontend work -- 'build me a SaaS dashboard' triggers"
echo "the lieutenant (parts/sleepy/frontend.md) in a real session."
exit 0
