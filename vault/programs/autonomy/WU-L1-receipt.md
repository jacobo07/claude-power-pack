# L1 receipt
Status: DONE

feat/ucda rebased onto live 228f3488 and LANDED ff-only via tools/land_worktree.py (landings/L1b-land.json, status LANDED).
Conflicts resolved keeping both semantics:
- S3 gsdx_chain.tick: live's per-goal Exclusive lock + _tick_locked kept; S3 parked/enabled=false early return added before the lock.
- EVC U5 gsd_mission.set_owner_hold: live's owner_hold kind (cost-breaker worker stop) kept; U5 hold_guard_budget(rec, reason) still called after the transition.
Open point (conservative, not blocking): for kind=cost holds both live's worker-stop and U5's stop=1 guard budget fire; they are compatible (both stop the worker).
Proven after rebase: CHAIN 19/19, REG 8/8, PROGRAMME_SPEND 13/13, MSPEND 34/34, HOLDGUARD 6/6, CTC 24/24, reforecast ALL PASS, OWNER_HOLD 32/32, COST_HOLD 23/23, ENVELOPE 67/67, PROGRAMME_STATUS 18/18, land_worktree pytest 10/10.
No LANDING_PENDING_OVERLAP: land was not refused for overlap.
