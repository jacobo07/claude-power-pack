# Part A remaining units (WU-AG2R, 2026-10-10)
Cost model: C(n) = F + g*n, slim-t2 F=19,000 g=1,700 tokens; n = model calls estimated per unit.
Eleven rows: 2 satisfied, 4 merged away, 5 work rows -> 5 units. Packets are PLAN-3 job.

| unit | rows | tier | n (basis) | C(n) = F+g*n | waits on owned files |
|---|---|---|---|---|---|
| U-AG-MIN | minimum-done-gate (+master-done-gate) | slim-t2 | 8 (7 capability probes, 1 test; files: gsd_dossier, session_budget_guard, mission_spend) | 32,600 | dgl W5 + WU-INST2 receipts |
| U-AG-CAN | canaries A2, A3 | slim-t2 | 6 (2 canaries x run+assert, 1 receipt) | 29,200 | W5 (A3 ContextImage path) |
| U-AG-ECON | economic-done-gate | strong | 12 (8 rates defined from ledger fields, 4 test/receipt) | est. 2x slim-t2: 78,800 | W5, INST2 (ledger.py, mission_spend.py read-only) |
| U-AG-LEARN | A-G2/A-G3 learning gate | slim-t2 | 6 (read AG1/S1 incident receipts, one comparator test) | 29,200 | W5 (profiles) |
| U-AG-DONE | part-a-done-gate (+master-done-gate-part-a) | slim-t2 | 5 (aggregate over dispositions+receipts, 1 test) | 27,500 | all above |

Total n ~ 37 calls; slim-t2 sum ~ 197,300 tokens (strong unit priced at 2x). Order: MIN, CAN, LEARN, ECON (parallel after W5), DONE last.
Every unit is gated only on dgl W5/INST2 because they READ ledger/mission_spend outputs; none edits an owned file.
