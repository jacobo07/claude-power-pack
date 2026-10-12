# WU-P3 receipt -- PARTIAL
mission: m-84c6e0072a10 | branch gsdx/pcc | nothing pushed
plans: Part A plan 65120b23 70fee4cb 715f177d 7be97f65 | 03-01 d1f9fe5d | 03-02 4c919e92 | 03-03 785fd756 | 03-04 eb9b0e99 bf37ef3c | 03-05 8e2f6ce8 | 03-06 partial 270f0f8f (+ this receipt commit)
gates (verbatim):
GSDX_FRONTIER_PASS=39/39  threshold=39/39
GSDX_RECONCILE_PASS=22/22  GSDX_GOAL_SWEEP_PASS=14/14  GSDX_SWEEP_ALL_PASS=11/11  GSDX_GOAL_EPOCH_PASS=19/19  GSDX_ENGINE_ID_PASS=14/14
GSDX_GOAL_MUTATIONS_CAUGHT=58/58  GSDX_PCC_REPLAY_PASS=28/28
GSDX_PCC_SEMANTICS_PASS=47/48  threshold=48/48   <- FAIL: V-PCC-ADDITIVE-ONLY (legacy files edited by Phase 3, see STATE.md)
frontier drills: m1 KILLED, m2 KILLED, m3-m8 UNRUN (harness killed the command for low memory; not restarted). liveness exit 0.
DENOMINATOR rows moved: none (drill and Phase 2 regression gates unmet).
deviations: dry-run reports only the first dispatch; a gate ending mid-pass is harvested next pass; first epoch carries its unit when bound > 1; fixtures append raw epoch events; D25/D26 admit and report only, nothing speculative or racing executes; frontier declared PLANNED in the liveness registry; claude_providers read 19/20 once under load, 20/20 on rerun (unexplained).
burn: end of Part A about 0.42M; now about 0.85M (token counter from 15M; no real instrument).
open points: (1) OWNER DECISION NEEDED in STATE.md: re-pin the legacy hashes for V-PCC-ADDITIVE-ONLY (my pick), narrow it, or revert. (2) Run drills m3-m8 one per call (each runs the suite twice, ~7 min), specs in the job tmp dir m1..m8.json. (3) Then 03-VERIFICATION.md, 03-EVIDENCE.md, DENOMINATOR rows, STATE current_phase 4, ROADMAP tick.
phase 4 estimate: large, about 1.5x Phase 3 (candidate snapshots plus executed speculation and racing left open here).

HANDOFF NOTE: WU-P3 PARTIAL -- 03-06 -- V-PCC-ADDITIVE-ONLY needs an Owner decision; drills m3-m8 unrun after a low-memory kill
