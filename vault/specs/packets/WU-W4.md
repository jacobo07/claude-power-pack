done_gate: C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe tools/test_gsdx_reforecast.py
work_tree: C:\Users\User\Apps\pp-gsdx-factory-2
receipt: vault/specs/gsdx-factory.RECEIPT-W4.json

# WU-W4 -- reforecast: deterministic programme forecast over receipts and the goal ledger

Plan (binding): `vault/plans/gsdx-factory-master-plan.md` section 2 W4 and the section 3 table. Fresh worker, no Agents, no
GSD commands, never push, never Set-Location / cd. Work class: DETERMINISTIC TOOL (zero-model at run time).

## 0. Facts (verified by PLAN-2, 2026-10-10)
- Master Plan section 3 table: expected 26.6M, lower 9.8M, safety 55.5M; envelope 40M, hard 55M.
- Goal gsdx-factory-2 at 2026-10-10: used 7,601,452 (settled 6,851,452, open 750,000), cap 100M; read it with
  `python C:\Users\User\.claude\skills\claude-power-pack\tools\mission_spend.py goal-status --goal gsdx-factory-2` (read-only).
- Retired/superseded since the plan: recon P2/P3 and CP50/P8/P9 run on the gen3 track (not funded here); W3 residual is dgl /
  ce-lifecycle-v3 (chain.json deferred + accept_note). Reforecast must count them as 0 here and say so.
- OWNED FILES: do not edit mission_spend.py, gsd_mission.py, ledger.py, session_budget_guard.js, route_admission.py.

## 1. Steps (gate first; commit after each green step, pathspec only, -F msgfile)
1. Write `tools/test_gsdx_reforecast.py` first (fails pre-state): a fixture chain.json + receipts + a goal-status JSON ->
   `tools/gsdx_reforecast.py` prints lower/expected/safety remaining and total; both poles of the 25% rule (change > 25%
   vs the previous forecast sets `iterate: true`; <= 25% sets false) and of the 40M rule (total > 40M sets `owner_needed`).
2. Write `tools/gsdx_reforecast.py`: inputs chain.json, receipts, goal used (read-only call or `--goal-json`), previous
   forecast `vault/specs/gsdx-factory/forecast.json`; output the new forecast.json (lower/expected/safety, delta %, flags).
   Lines for units still in chain = their route targets x expected-real factor 0.35 (K7: live pricing over-prices ~2.8x),
   and the unfunded plan lines (GEX44 port, unmapped rows, reserves) from the Master Plan table. No model calls.
3. Run it on the live tree; commit forecast.json. Receipt `vault/specs/gsdx-factory.RECEIPT-W4.json` with the three numbers,
   delta vs PLAN-2's forecast, flags. Commit.

## 2. Budget and closeout (protected)
About 8 model calls / 19 tool calls. At 14 tool calls stop new work, commit green, write the receipt (PARTIAL allowed).
End your final message with `HANDOFF NOTE:` and one line.
