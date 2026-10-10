done_gate: C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe tools/test_wu_agmin.py
work_tree: C:\Users\User\Apps\pp-gsdx-factory-2
receipt: vault/specs/gsdx-factory.RECEIPT-AGMIN.json

# WU-AGMIN -- W6 Part A: U-AG-MIN

Plan (binding, Owner "y" 2026-10-09): `vault/plans/gsdx-factory-master-plan.md` sections 2-3 (W6). Fresh worker, no Agents,
no GSD commands, never push, never Set-Location / cd (git -C and absolute paths). Work class: CLASSIFICATION/TEST (data + one test).

## 0. Facts (verified by PLAN-3, 2026-10-10)
- Units and basis: `vault/specs/gsdx-factory/partA/UNITS.md`; row dispositions: `partA/dispositions.json` (11 rows, unknown 0).
- Scope: minimum-done-gate (+master-done-gate): 7 capability probes over gsd_dossier, session_budget_guard, mission_spend outputs (read only) + 1 test.
- OWNED FILES (never edit): gsd_mission.py, hooks/session_budget_guard.js, modules/provider_routing/ledger.py,
  tools/mission_spend.py (ce-lifecycle-v3 / dgl), tools/route_admission.py (cost-collapse). This unit READS their outputs only.
- Chain waits: dgl W5-receipt.md and WU-INST2-receipt.md must exist before this unit arms.

## 1. Steps (gate first; commit after each green step, pathspec only, -F msgfile)
1. Write `tools/test_wu_agmin.py` first; it must fail on the pre-state (state the failing reason in the receipt).
2. Do the scope above, reading body text of the relevant partA rows (first 20 lines each) and the named receipts only.
3. Make the gate exit 0; commit. Write receipt `vault/specs/gsdx-factory.RECEIPT-AGMIN.json` (status, gate line, commits, remaining). Commit.

## 2. Budget and closeout (protected)
About 8 model calls / 20 tool calls. At (20 - 7) tool calls stop new work, commit green, write the receipt (PARTIAL
allowed, with remaining items). End your final message with `HANDOFF NOTE:` and one line.
