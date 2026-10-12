# W1 receipt
Status: DONE_WITH_LIMITS
Limits: test_gsd_mission.py exits non-zero (224/230) identically on unmodified HEAD (6 worktree-path V-MC FAILs because the checkout is a git worktree); no regression from W1. Main-tree gsd_mission.py was clean (step 0 printed nothing); change kept on ccr/v4, unmerged (X1 owns merge).
Done: envelope --ccr-class, admit_route ccr_contract, CPP_CCR_ADMISSION=enforce refusal, tools/test_gsd_mission_ccr_contract.py 5/5 (red on HEAD first), test_ccr_pgo 7/7, evidence vault/programs/ccr/evidence-v4-stage2-W1.md.
K7: estimate vs actual processed tokens: estimate not stated in packet; actual not measured by me (single session, ~16 calls, small context ~ well under 1M processed).

Coordinator verification 2026-10-13 00:30 (e10a9f08): in the worktree at 527d3fb4, test_gsd_mission.py MC_PASS=230/230 and test_gsd_mission_ccr_contract.py 5/5. The 224/230 limit did not reproduce; accepted via chain.json accept.
