# WU-J3 -- C2b job 3, Phase-7 slot 3 of 4, two arms on the SAME slot (goal cp50-c2)
Plan: vault/plans/cpx-control-plane-extinction-cp50-2026-10-11.md sections 5, 7c. Authorized by cp50-run-plan D4 (Owner y 2026-10-09): do NOT ask again. Needs R3, R6 and R3b DONE.
1. REFUSE to send without a READY verdict in vault/programs/cp50-c2/R3b-certificate.md (it supersedes R3-certificate.md, which was NOT_READY) (W1 port fa8aaf0 + trim + output budget <= 20,971,520 + job-key exactly-once + CURRENT_CAPSULE).
2. Before prepare: check vault/programs/tennis-rf/JOBS.md and the TRF job dirs for a prepared-unsent job holding the shared CURRENT_CAPSULE. Serialize behind it; stop BLOCKED_HUMAN only if it cannot be serialized.
3. Exactly ONE send, max_residuals 0. Two arms on the same slot: arm A current pipeline vs arm A+dossier (R6).
4. Per function record: tokens, provider context, model calls, discovery calls, evidence retrieved without a model, proof, wall time, verdict, reusable knowledge written.
5. Repatriate, judge via receipt_judge, records to cp50\c2b_records_1_5.jsonl.
6. Job 4 only if job 3 fails for an infrastructure cause that has since got a local regression gate; never after an unexplained failure.
Done-check: records file with both arms, or a named infra failure + gate. Route: route-M.json.
Common: no Monitor, no waiting call, no Agent spawns, no GSD commands. Pathspec commits on feature/knowledge-acquisition (no push), message ends with the Co-Authored-By line from the commit attribution. Never tick a chain by hand. Receipt K7 row: estimate vs actual processed tokens. Receipt line 1 '# <ID> receipt', line 2 'Status: DONE'.
Receipt path: C:\Users\User\.claude\skills\claude-power-pack\vault\programs\cp50-c2\WU-J3-receipt.md
