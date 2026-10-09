done_gate: C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe tools/test_wu_w3.py
work_tree: C:\Users\User\Apps\pp-gsdx-factory-2
receipt: vault/specs/gsdx-factory.RECEIPT-W3.json

# WU-W3 -- W3 S2/S3 residual: calls_unit, model-call counter, per-class g/r, R4 reconcile

Plan (binding, Owner "y" 2026-10-09): `vault/plans/gsdx-factory-master-plan.md` sections 2-3. Fresh worker, no Agents,
no GSD commands, never push, never Set-Location / cd (git -C and absolute paths; child-process cwd only). Pathspec commits
with a message file (one file per commit). Gate first: write the done_gate test before the work it proves, and make it
fail on the pre-state. Scripts you run for evidence must await every effect they start.

## 0. Facts (verified by the planner 2026-10-09)
- Waits on ce-lifecycle-v3 INST2 receipt (verified present 2026-10-09): `C:\Users\User\Apps\pp-ce-lifecycle-v3\vault\programs\cognitive-economy\lifecycle\WU-INST2-receipt.md`. Owned files of that programme (gsd_mission.py, hooks/session_budget_guard.js, modules/provider_routing/ledger.py, tools/mission_spend.py) may be edited ONLY because this unit has that wait; edit them in THIS worktree only, never the live skills tree; landing is the GEX44-port/steward step, not this unit.
- Master Plan W3: a `calls_unit` field on every budget; a model-call counter (by message.id) beside the tool counter; per-class g, r and closeout tail; R4 reconciliation; successor arming within the envelope. Canary: counters match the transcript, breaker denies on the intended unit, S1 replay priced >= 2.1M or split.
- Rows: L1 GRAPH U-W3 (14 rows: calls-unit, unit-typed budgets, s2-reported-purpose, phase-2-s2-call-unit-truth, s2-production-canary, reservation reconcile, phantom-reservation-prevention, unknown-is-not-free ...). Read their dispositions from l1/dispositions.json, not the sources.

## 1. Steps (commit after each green step)
1. Read WU-S4/S3 receipts of lc3 named in the L1 receipt; list what INST2 already delivered; shrink scope to the true residual.
2. Gate first: `tools/test_wu_w3.py` drives the counters against a recorded transcript fixture and the breaker deny branch (both poles).
3. Implement in <=3-file commits; keep existing suites green (tools/test_session_budget_guard.py, mission_spend tests).
4. S1 replay pricing check; done_gate exit 0.

## 3. Budget and closeout (protected)
About 22 model calls / 36 tool calls (n estimated from: files/gates named in section 1 plus jobs to wait on). At 29 tool calls stop new work, commit green, write the receipt
(PARTIAL allowed with remaining items). End your final message with `HANDOFF NOTE:` and one line.
