# E2 receipt
Status: DONE_WITH_LIMITS
Limits: (1) no max_calls cap is derived from data: PGO needs 3 finished units and 1 real transcript exists (49c0ae70, 103 calls); (2) no lease with max_calls set on a live mission, only injected-meter tests; (3) test_mission_spend.py 40/41 (V-MSPEND-HOLD-PLAN-NONE) fails identically at 1cbd1cb5, before this unit.
Done: tools/boundary_ledger.py (ledger + PGO suggest; reproduces the plan's hand counts on 49c0ae70: 103 calls, 37 parallel, 17 tests, gsd_mission.py read 24x); max_calls boundary authority in phase_lease, set_envelope (measured calls_base), _phase_breaker, --phase-max-calls; mission_spend.processed_calls. BOUNDARY_PASS=22/22, PHASE_LEASE 23/23 and 15/15, ADM 43/43.
Correction: 15b71b82 (E1) misplaced a block in gsd_mission.py (SyntaxError at that commit, pushed); repaired in the E2 commit.
Reforecast: E1 actual far below its 1,500,000 target, eligible.
K7: estimate 1,200,000; actual not summed from the transcript meter in this unit (one session, in this pane).
Evidence: vault/programs/ccr/v5/evidence-E2.md
