done_gate: C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe tools/test_wu_doctrine.py
work_tree: C:\Users\User\Apps\pp-gsdx-factory-2
receipt: vault/specs/gsdx-factory.RECEIPT-DOCTRINE.json

# WU-DOCTRINE -- U-DOCTRINE: enforcing text or gates for the 41 unenforced doctrine rows

Plan (binding, Owner "y" 2026-10-09): `vault/plans/gsdx-factory-master-plan.md` sections 2-3. Fresh worker, no Agents,
no GSD commands, never push, never Set-Location / cd (git -C and absolute paths; child-process cwd only). Pathspec commits
with a message file (one file per commit). Gate first: write the done_gate test before the work it proves, and make it
fail on the pre-state. Scripts you run for evidence must await every effect they start.

## 0. Facts (verified by the planner 2026-10-09)
- L1 GRAPH U-DOCTRINE: 41 rows dispositioned CHEAP_COGNITION 'doctrine without an enforcer' (ids in vault/specs/gsdx-factory/l1/GRAPH.md and dispositions.json). No row may be claimed satisfied without a probe that passes.
- Edit scope: new/own files only (vault/specs/gsdx-factory/doctrine/*.md, tools/ own scripts, this tree's tests). No edit to gsd_mission.py, session_budget_guard.js, ledger.py, mission_spend.py, route_admission.py.

## 1. Steps (commit after each green step)
1. Cluster the 41 rows by enforcing surface (existing rule file / hook / gate); most map to an existing HARD-RULE or UKDL id: add a MERGE/REUSE probe instead of new text.
2. Gate first: tools/test_wu_doctrine.py re-runs `gsd_dossier dispose --check` on a copy where each row now carries a passing probe or a gate it points to; fails on the pre-state.
3. Write enforcing text/gates for the genuinely unenforced rows (smallest gate that bites); update l1/review.json; rerun dispose --check exit 0.
4. done_gate exit 0.

## 3. Budget and closeout (protected)
About 22 model calls / 36 tool calls (n estimated from: files/gates named in section 1 plus jobs to wait on). At 29 tool calls stop new work, commit green, write the receipt
(PARTIAL allowed with remaining items). End your final message with `HANDOFF NOTE:` and one line.
