# WU-P3 receipt -- PARTIAL
mission: m-84c6e0072a10 | branch gsdx/pcc | nothing pushed
plans: Part A 65120b23 70fee4cb 715f177d 7be97f65 | 03-01 d1f9fe5d | 03-02 4c919e92 | 03-03 785fd756 | 03-04 eb9b0e99 bf37ef3c | 03-05 8e2f6ce8 | 03-06 partial 270f0f8f ea34b4cd 51eb4ad0 (+ this commit)
gates (verbatim, last committed green run):
GSDX_FRONTIER_PASS=39/39  threshold=39/39   (a later clean-copy run inside drill m3 read 38/39: V-FRONTIER-SWEEP-BOUND, cause unknown)
GSDX_RECONCILE_PASS=22/22  GSDX_GOAL_SWEEP_PASS=14/14  GSDX_SWEEP_ALL_PASS=11/11  GSDX_GOAL_EPOCH_PASS=19/19  GSDX_ENGINE_ID_PASS=14/14
GSDX_GOAL_MUTATIONS_CAUGHT=58/58  GSDX_PCC_REPLAY_PASS=28/28  GSDX_PCC_SEMANTICS_PASS=48/48  threshold=48/48
drills: m1 KILLED, m2 KILLED, m3 CONTROL_INVALID (control 38/39), m4-m8 UNRUN. liveness exit 0.
DENOMINATOR rows moved: none (drill gate unmet).
deviations: dry-run reports only first dispatch; gate ending mid-pass harvested next pass; first epoch carries its unit when bound>1; fixtures append raw epoch events; D25/D26 admit and report only; frontier PLANNED in liveness; V-PCC-ADDITIVE-ONLY re-scoped to the Phase 2 git range (Owner option b); claude_providers 19/20 once under load; harness killed two memory-pressure runs (not restarted).
burn: Part A about 0.42M (my estimate, unmeasured); end 30,965,658 tokens from session-budget state file (written 12:15); warn 56M not reached.
open: (1) diagnose V-FRONTIER-SWEEP-BOUND red under load (run the suite alone when memory allows, 3 times; if time-dependent, fix the fixture, never weaken the gate). (2) m3-m8 one per call, specs in job tmp m3..m8.json. (3) then 03-EVIDENCE/03-VERIFICATION, DENOMINATOR rows, STATE current_phase 4, ROADMAP tick.
phase 4 estimate: large, about 1.5x Phase 3.

HANDOFF NOTE: WU-P3 PARTIAL -- 03-06 -- drill m3 CONTROL_INVALID (V-FRONTIER-SWEEP-BOUND red under load, diagnosis killed by low memory); m4-m8 unrun
