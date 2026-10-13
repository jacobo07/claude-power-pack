# WU-P5 receipt -- DONE
mission: id on the rehydration card is not visible to the worker (follows m-3964348fe5e4, Phase 4 DONE) | branch gsdx/pcc | nothing pushed
plans: Part A before 970ea212 | 05-01 970ea212 | 05-03 8e62abdb | 05-02 0f1b2aba | 05-04+05-05 73179700 | verify+STATE+ROADMAP+DENOMINATOR 7cbe52f6
gates (all Windows plane, logs/ under phases/05-*):
GSDX_JUDGE_VALIDATE_PASS=11/11  threshold=11/11
GSDX_REPLAY_PARALLEL_PASS=14/14  threshold=14/14
EVB_ABA_PASS=10/10  threshold=10/10
GSDX_REVIEW_PASS=12/12  threshold=12/12
regression: GSDX_JUDGE_PASS=11/11, EVB_PASS=21/21, GSDX_PCC_SEMANTICS_PASS=48/48, GSDX_PCC_REPLAY_PASS=28/28, GSDX_FRONTIER_PASS=40/40, GSDX_INVALIDATION_PASS=26/26; liveness reachability.py exit 0
DENOMINATOR moved: D15, D16, D17, R05 -> DONE (evidence in the row)
drills (Windows plane, isolated copy, control valid): d1 d2 d4 d5 d6 d7 d8 d9 d10 KILLED; d3 UNRUN (reaped for low memory, not retried)
for the coordinator's Linux plane: d3; tools/test_gsd_x_goal_mutation.py (mutates live files; judge.py anchors intact). STATE.md has an OWNER DECISION NEEDED entry (pick: a)
deviations: 05-03 ran before 05-02; no separate RED logs for 05-03/05-04 (drills prove the gates bite); replay/review declared PLANNED in the liveness registry (tools/ is outside the scanner aperture)
burn: end of Part A 6,280,980 tokens / 65 calls; at end 29399799 tokens / 243 calls (last read before the receipt commit)
open points: a Windows writer restoring mtime+inode defeats the live-read journal (snapshot read covers it); LEARNINGS_PENDING.md left untracked
Phase 6 size estimate: L (mutant farm W5, incl. R11 isolated-copy incumbent measurement and the Linux runs above); ~40-60M tokens