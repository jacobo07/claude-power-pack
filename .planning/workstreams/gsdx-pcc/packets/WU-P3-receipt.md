# WU-P3 receipt -- DONE
mission: m-84c6e0072a10 | branch gsdx/pcc | nothing pushed
plans: Part A 65120b23 70fee4cb 715f177d 7be97f65 | 03-01 d1f9fe5d | 03-02 4c919e92 | 03-03 785fd756 | 03-04 eb9b0e99 bf37ef3c | 03-05 8e2f6ce8 | 03-06 270f0f8f ea34b4cd 51eb4ad0 20c0f56f 356984cb 298ba2c6 edc5f0c8 | verify 3a11e4c2 | DENOMINATOR 41bdf37f | STATE 4d43e9fe | ROADMAP 8b955a5f
gates (verbatim):
GSDX_FRONTIER_PASS=40/40  threshold=40/40   (Linux plane, GEX44, 9 runs at 298ba2c6; laptop run not completed, last laptop read 39/39 at 8e2f6ce8)
GSDX_PCC_SEMANTICS_PASS=48/48  threshold=48/48  GSDX_PCC_REPLAY_PASS=28/28  GSDX_GOAL_MUTATIONS_CAUGHT=58/58 (laptop)
GSDX_RECONCILE_PASS=22/22  GSDX_GOAL_SWEEP_PASS=14/14  GSDX_SWEEP_ALL_PASS=11/11  GSDX_GOAL_EPOCH_PASS=19/19  GSDX_ENGINE_ID_PASS=14/14 (laptop)
drills: m1-m8 all KILLED on the Linux plane (valid controls); m1, m2 also on the laptop. liveness exit 0.
DENOMINATOR moved to DONE: D04 D05 D06 D07 D08 D09 D27 D28 D33 D34. D25, D26 stay OPEN (policy + ledger only).
deviations: dry-run reports only first dispatch; gate ending mid-pass harvested next pass; first epoch carries its unit when bound>1; fixtures append raw epoch events; D25/D26 admit and report only, nothing executes; frontier PLANNED in liveness; V-PCC-ADDITIVE-ONLY re-scoped to Phase 2 git range (Owner option b); sweep fixture made deterministic (release-file gates) after a 38/39 read; claude_providers 19/20 once under load; harness killed 3 laptop runs for low memory (not restarted); drills m3-m8 run by the coordinator on GEX44.
burn: Part A about 0.42M (unmeasured estimate); end 35,529,754 tokens from session-budget state file (target 52M, warn 56M not reached).
open points: (1) executed speculation and racing (D25/D26) belong to Phase 4. (2) Frontier suite at 298ba2c6 has no completed laptop run; re-run when RAM allows. (3) Engine-identity before-value not captured.
phase 4 estimate: large, about 1.5x Phase 3 (candidate snapshots plus executed speculation and racing).

HANDOFF NOTE: WU-P3 done -- Phase 4 (W3 candidate snapshots) ready to compile