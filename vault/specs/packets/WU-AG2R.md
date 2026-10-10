done_gate: C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe tools/test_wu_ag2r.py
work_tree: C:\Users\User\Apps\pp-gsdx-factory-2
receipt: vault/specs/gsdx-factory.RECEIPT-AG2R.json

# WU-AG2R -- W6 Part A: recompile A-G2..A-G5 against current state and disposition every Mission A row

Plan (binding, Owner "y" 2026-10-09): `vault/plans/gsdx-factory-master-plan.md` sections 2-3 (W6). Fresh worker, no Agents,
no GSD commands, never push, never Set-Location / cd (git -C and absolute paths). Work class: CLASSIFICATION (data + one test).

## 0. Facts (verified by PLAN-2, 2026-10-10)
- W3 is accepted PARTIAL (chain.json accept_note); its residual belongs to dgl W3/W4 and ce-lifecycle-v3. Do not do it here.
- The 11 Part A rows sit in `vault/specs/gsdx-factory/l1/obligations.json` as WAIT_DEPENDENCY (depends_on W3): ids
  S-mission-a-minimum-done-gate, S-mission-a-canaries, S-mission-a-master-done-gate, S-mission-a-objective-rewrite,
  S-a-g2-through-a-g5-recompilation, S-mission-a-economic-done-gate, S-part-a-reported-state, S-phase-10-part-a-completion,
  S-a-g2-a-g3-learning-gate, S-part-a-done-gate, S-master-done-gate-part-a. Bodies: `l1/sections.json` (title match).
- Evidence for "what already exists": RECEIPT-AG1/S1/S4/W3 in `vault/specs/`, `vault/specs/gsdx-factory/obligations.json`
  (A-G1's 22 rows), gen3 receipts, ce-lifecycle-v3 receipts. Tools: `tools/gsd_dossier.py dispose`, `tools/test_gsd_dispose.py`.
- OWNED FILES (never edit): gsd_mission.py, hooks/session_budget_guard.js, modules/provider_routing/ledger.py,
  tools/mission_spend.py (ce-lifecycle-v3 / dgl), tools/route_admission.py (cost-collapse). This unit edits none.

## 1. Steps (gate first; commit after each green step, pathspec only, -F msgfile)
1. Write `tools/test_wu_ag2r.py` first (must fail on the pre-state): asserts `vault/specs/gsdx-factory/partA/obligations.json`
   exists, its expect list equals the 11 ids above, and `gsd_dossier.py dispose --check` on it exits 0 with no row left
   WAIT_DEPENDENCY on W3 (W3 is accepted) and no UNKNOWN without a stated reason.
2. For each of the 11 rows read title + first 20 body lines only; recompile against A-G1 receipt, capability state and
   W3 receipt. Disposition each with the vocabulary NO_WORK / ALREADY_SATISFIED / REUSE_EXISTING / MERGE (probe that passes now)
   or a work disposition naming the tier (slim-t1/slim-t2/strong) and the owned-file wait if any (wait = dgl W5-receipt.md
   `C:\Users\User\Apps\pp-dgl\vault\programs\dgl\W5-receipt.md` and WU-INST2-receipt.md). Write `partA/obligations.json`
   + `partA/dispositions.json`; run the dispose gate to exit 0.
3. Write `partA/UNITS.md` (<= 40 lines): the remaining A-G2..A-G5 work units, n estimated from files/gates named (one line
   how), C(n) slim-t2 F=19,000 g=1,700, and which wait on owned files. Do not compile packets for them; PLAN-3 does.
4. Receipt `vault/specs/gsdx-factory.RECEIPT-AG2R.json`: counts per disposition, gate line, commits, remaining units. Commit.

## 2. Budget and closeout (protected)
About 10 model calls / 24 tool calls. At 17 tool calls stop new work, commit green, write the receipt (PARTIAL allowed,
with remaining row ids). End your final message with `HANDOFF NOTE:` and one line.
