# WU-E4 receipt (written by the coordinator; both E4 workers ended without one)
Status: DONE
- Commits (wt_ewc, ewc/closure): 90c441a0 closer-guard RECOMMENDATION_STOP (M6); b770016a child-result obligations,
  open obligations on the successor card + /kclear capsule, rubric sentence (M8, M10) -- committed by the coordinator
  from the workers' uncommitted tree, with one fix: the card's obligation block imported `modules.*` without the repo
  root on sys.path and was uncontained, so render_card raised (the chain's gate saw test_gsd_mission red). It now
  renders `OPEN OBLIGATIONS: UNKNOWN` instead of killing the relay card.
- Workers: m-f68aa978d123 (1.24M tokens), m-5df98f7578ab (1.78M tokens); both "no receipt".
- PROVEN (coordinator, 2026-10-11 ~22:30, on the tree committed as b770016a):
  test_ewc 39/39 (281 s), test_gsd_mission MC_PASS=227/227, test_autonomy_gate 22/22,
  test-closer-guard-recommendation 44/44 (fire 8, must-not-fire 10), test-closer-guard-uncontracted-wait 21/21,
  test-ewc-stop-gate 11/11.
- NOT_PROVEN: closer-guard drill counts BEFORE E4 (no pre-E4 baseline recorded); the precision figure on the fixtures
  beyond the 44/44 drill.
- E6 step: copy canonical hooks/closer-guard.js to ~/.claude/hooks after the merge (live copy is stale until then).
