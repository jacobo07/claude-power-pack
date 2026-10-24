# Phase 2 verification — PASSED
- Gates: `python3 tools/test_arm_preflight.py` PRE_PASS=16/16 (mutant always-pass turns the wired refusal red; kill switch; unmeasured is not pass).
- Regression: test_gsd_mission 233/233, test_gsd_mission_chain 11/11, test_gsd_mission_goal_control 27/27, test_arm_worker_guard 6/6.
- Historical replay (this host ledger, 6052 rows): 53 `relay_held` + 1 `mission_blocked` carrying NO_PHASES, all one mission, first at epoch 1 -> that case is PREVENTED at arm (and the 53 repeats are the S3 loop). No low-memory refusal rows exist in the ledger on this host (unmeasured, not zero-cost). Custody/COPIA cases: not replayed (lineage is supervise-time by design).
- Debt: an arm in a dir where GSD is UNAVAILABLE still proceeds (unmeasured by design).
