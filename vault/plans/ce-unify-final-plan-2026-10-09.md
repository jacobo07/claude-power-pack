# CE unify -- final plan (2026-10-09)

Status: PROPOSED. Goal ce-unify (WU-U1, analysis only). No new programme (HR-NOVELTY-001). No authority beyond existing caps.
Inputs: `vault/programs/cognitive-economy/unify/obligation-ledger.md` (50 rows), `.../incident-ce-lifecycle-v2-overrun.md`, `vault/plans/ce-unify-reality-delta-2026-10-09.md`.
Budget formula: calls x 18K + 15K x calls x (calls-1)/2 (measured worker model: ~18K floor + ~15K growth per call, WU-S1/S3).
Funding test: owner remaining - open (dossier, 11:30Z). ce-a4: 14,654,307 - 563,845 = 14,090,462. ce-lifecycle-v3: 1,434,095 - 1,896,885 = -462,790.

| unit | owner goal | inputs | done gate | calls | budget (arithmetic) | funded? |
|---|---|---|---|---|---|---|
| P1 land goal-autopsy on LIVE (ledger D-01) | ce-a4 (W1a) | branch ce/a3b-r tools/mission_spend.py, test_goal_autopsy.py (10/10 there) | LIVE `mission_spend.py goal-autopsy` reproduces the ce-a3b table; suite green on HEAD | 6 | 6x18K=108,000 + 15K x 15 = 225,000 -> 333,000 | yes (ce-a4) |
| P2 fold EXTEND rows into ce-a4 W0/W1/W3 packets (D-04,07,09-12,17,18,20,22,24,26,27,29,32,34,37,46) | ce-a4 | ledger | each EXTEND row appears as a named line in an owner packet; no new file type | 5 | 90,000 + 15K x 10 = 150,000 -> 240,000 | yes (ce-a4) |
| P3 Cognitive CI clauses: hot-token delta (D-28), meta-work share (D-22), token-incident trigger (D-24) | ce-a4 (W3) | cep_gen2 + reachability.py | each clause has a planted-violation test that goes red | 8 | 144,000 + 15K x 28 = 420,000 -> 564,000 | yes (ce-a4) |
| P4 confirm L1 bounds the retroactive settle (incident residual) | ce-lifecycle-v3 (S-unit) | L1 3f9b57cc tests, journal seq 91-94 | replay of a Set-Location bind books 0 retroactive settle on a branch with L1 | 4 | 72,000 + 15K x 6 = 90,000 -> 162,000 | NO: -462,790 -> WAITING_FOR_AUTHORITY |
| P5 CI clause: Close step using `arm` without `--no-launch` fails (R5c strays, 866,883) | ce-a4 (W3) | ENTRY_MATRIX launch sites | planted Close with bare `arm` goes red | 4 | 72,000 + 90,000 = 162,000 | yes (ce-a4) |
| P6 decide the UNKNOWN rows (D-06,08,15,16,31,40) | ce-a4 (W0) | ledger, one autopsied mission | each row becomes OWNED/EXTEND/REJECT with a measured line, or stays UNKNOWN with the missing number named | 5 | 90,000 + 150,000 = 240,000 | yes (ce-a4) |

Total budget: 333,000 + 240,000 + 564,000 + 162,000 + 162,000 + 240,000 = **1,701,000**.
By owner: ce-a4 1,539,000 (covered by 14,090,462); ce-lifecycle-v3 162,000 (WAITING_FOR_AUTHORITY, no request made here).
Order: P1, P2, P6, P3, P5; P4 only when v3 remaining - open covers 162,000.
Rules for every unit: absolute paths and `git -C`, never Set-Location into another Apps\pp-* root; any `arm` uses `--no-launch`; two-strike stop; caps never raised.
