# WU-S4 -- predictive lease edge + physical-call pricing (plan v3 S4, Owner "A" 2026-10-09)

Goal ce-lifecycle-v3. cwd = this worktree. Work class: IMPLEMENTATION (two small, separate edits + one test each).

Measured facts (do not re-derive; plan erratum af86e3dc, estimator-fit.md):
- Physical calls (every tool use) run ~2.4x the steps a packet declares: 1H4 had 17, 1H3 22.
- First call ~18.5K; growth ~1.7K per call. WU-S3 tripped at 975K vs stop 950K: the breaker was the first signal.

Read ONLY these ranges:
- hooks/session_budget_guard.js 100-170 (judge(), closeout()).
- tools/route_admission.py 61-130.
- vault/config/route-floors.json.

Budget: aim for <= 6 steps (about 15 physical calls). Commit each part as soon as its test is green.

Part A, the edge, in hooks/session_budget_guard.js judge():
- Before the warn branch: per = st.tokens / max(st.calls, 1); reserve = Number(budget.closeout_reserve_calls) || 3.
- If st.tokens + per * reserve > budget.stop, return advise() with this text: "LEASE EDGE: the remaining lease
  holds about <reserve> calls. Do no new substantive work. Now: commit what is green (pathspec, -F), write the
  receipt with Status: PARTIAL and the exact next step, end with HANDOFF NOTE."
- Keep the stop deny unchanged (the airbag). The edge must fire strictly before the stop deny.
- Kill switch: CPP_LEASE_EDGE=off.
- Tests: extend the existing guard test file (find it with Glob tools/test_session_budget_guard*.py or
  test_process_lifecycle.py; extend, do not fork):
  - V-LIFE-EDGE-BEFORE-STOP: a replay of WU-1H3 (10 calls, 645K, stop 500K) shows the edge first fires on a
    call whose tokens are < stop.
  - V-LIFE-EDGE-QUIET-EARLY: control, no edge at 20% of stop.
  - V-LIFE-EDGE-KILL: the kill switch works.
  - Mutant: drop the edge branch; EDGE-BEFORE-STOP must go red.

Part B, physical calls, in tools/route_admission.py:
- A profile field `physical_ratio` (slim-t2: 2.4, `physical_ratio_n`: 4).
- calls_physical = ceil(calls * physical_ratio) feeds the cost formula. Output both `calls` and `calls_physical`.
- tools/test_route_estimator.py:
  - V-EST-PHYSICAL-1H4: 7 declared calls predict within 25% of 442,155.
  - Control: a profile without the field is unchanged.
  - Mutant: ratio ignored.
- Also run test_gsd_mission_admission.py (43/43).

Then:
- WU-S4-receipt.md (<= 25 lines): gates, mutants, the live-install patch for Part A as `git diff --binary
  e86cafc4 -- hooks/session_budget_guard.js tools/route_admission.py vault/config/route-floors.json <test files>`
  saved to install/L2-edge.patch with its sha256. No deploy; the coordinator installs with
  tools/lifecycle_install_apply.ps1. Commit.
- If remaining - open >= 600,000 (goal-status ce-lifecycle-v3), arm WU-S5 with LIVE gsd_mission.py arm-chain
  (--parallel-unit lc3-WU-S5, packet WU-S5.md, route route-WU-S5.json, token-estimate 700000) IF both files exist.
  Otherwise write WAITING_FOR_AUTHORITY in the receipt.

NEVER write "needs a fresh pane" or "/kclear". End your final message with: HANDOFF NOTE: WU-S4 done
