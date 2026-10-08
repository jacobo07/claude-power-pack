# R2 receipt -- goal-reconcile (goal ce-a3b-r)

decision: reconcile = one pass under the ledger lock. LIVE if a kclaude-pane beacon names the sid or its transcript
was written within idle_s (1800, same two signals as session_titles_sweep); UNKNOWN if no transcript or it cannot be
stat'd/read; else settle at session_tokens(transcript, goal since) and close every open lease/agent hold of the sid.

effect: tools/mission_spend.py goal_reconcile + CLI `goal-reconcile --goal G [--idle-s N]`. Rows are `settle`
(reason: reconcile) through the ledger `_append`. Only sids with open holds are visited, so a second run adds no rows.

proof: RED f07b9ea7 (0/5). GREEN 10bf871b: test_goal_budget_admission.py GOAL_PASS=72/72 exit 0;
test_session_budget_guard.py 16/16 (two earlier runs read V-SBG-LATENCY 257 ms under load, 40 ms on rerun -- known flaky).
Mutation drill (isolated copy, control passed): liveness-by-beacon check dropped -> KILLED, V-GOAL-RECONCILE-LIVE red.

unknowns: the run on goal ce-a3b was NOT executed. Its state lives under ~/.claude/state, which this unit may not edit;
before/after is UNKNOWN. Coordinator/Owner step: `python tools/mission_spend.py goal-reconcile --goal ce-a3b`, then
confirm used == 6.67M. A sid whose transcript is under another host/projects root reads UNKNOWN (stays counted). A pane
idle >30 min without a beacon is treated dead and settled; a later renew by it still re-settles via the watermark
(no double count).

refs: R2.md, R1-receipt.md, ledger.py _gfold/settle watermark; commits f07b9ea7, 10bf871b.

actual vs forecast 1.2M: about 25 tool calls; token total not metered here (UNKNOWN), under the ~30-call envelope.
