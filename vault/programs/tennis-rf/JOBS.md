# TRF GEX44 compute jobs (Owner-approved budget: 7; plan section 8)

Record a row BEFORE each send. A job that leaves no row is a breach of the programme's authority.
Phase-7 jobs and goal cp50-c2 are not this programme's.

Owner approved jobs 5-6 for D28 Ph8 (D8, one batch per pair of arms) and job 7 for D28 Ph9 (D9, only if D9's
step-0 gate admits). Owner, 2026-10-13, in the D28 coordinator pane: "D8/D9 do go to GEX44".
Job 4 was D6's; D6 did not send it. Owner, 2026-10-13, approved the post-D28 pricing unit ("I approve that"):
job 4 is reassigned to D12. After the Owner's Factory-scaling addendum (same day) D12 splits into D12a (no job) and
D12b, which owns job 4 (one bulk batch: shared-layout dependents + 8 naive fns + 3 donors, plan
`vault/plans/d12-factory-scaling-2026-10-13.md`). D12b rewrites row 4 before sending. The
budget stays 7; jobs 8+ (W13) are NOT approved.

| # | Unit | Purpose | Job id | Certificate sha | Sent at | Verdict |
|---|---|---|---|---|---|---|
| 1 | W10c | W3b A/A, 3 donors, candidate mode, cap1-d3ae262b286b (build candidate-20261011T222911Z) | ksrmb-20261011-223128 | a910a3c38e3146fc0abe117a9e58a94b2a0a0021469a916a050457a320767401 | 2026-10-11 22:31Z | PASS: judged 3/3 MATCH (objdiff 100, oracle2 MATCH) |
| 2 | W10c | W5a step 3 batch: 5 fns x presets + proto (26 units; 7 fns lint-refused UNK_FIELD) (build candidate-20261011T233329Z) | ksrmb-20261011-233503 | cb1552bad43192b3a7ed06ba00e46aed04d441f4e45c17c237bef0111450c1ff (inputs_hash) | 2026-10-11 23:35Z | JUDGED: 0/26 MATCH (1 fn compile_error, 4 fns BLOCKED_CONTEXT; 7 fns lint-refused pre-send) |
| 3 | W12 | 22 lint-clean composed m2c fns (O4p all + O2 for 17 within OUT budget; 42 units incl 3 donor controls) (build candidate-20261012T170916Z, cap1-5bf8cc7d7aac) | ksrmb-20261012-171117 | af8227f27f8b46d4ee5588d7e0200265e51ca331d12f06cca3f56e7e02772280 (inputs_hash) | 2026-10-12 17:11Z | JUDGED 17:24Z: 12/22 fns MATCH (O4p), 9 PARTIAL, 1 BLOCKED_CONTEXT; 3/3 donor controls MATCH; 42 rows |
| 4 | D6 | UNUSED: no certified fact, newly-clean batch empty (clean 276->276); not sent | - | - | - | NOT SENT, job 4 kept (WU-D6-receipt.md) |
| 5 | D8v2 | Ph8 tournament arm B: 14 lint-clean held-out fns (draw.json, seed 20261013) x O4p+O2 + 3 W3b donor controls = 31 units; arm D EMPTY (no motif->C emitter), E EMPTY, F=B (build candidate-20261014T114813Z, cap1-fee7b09f053d) | ksrmb-20261014-114911 | e33fd892a26150895bbc047606f3eb41eb94d00ff9581743a286a3b3c3545edd (inputs_hash) | 2026-10-14 11:49Z | JUDGED: donors 3/3 MATCH; arm B 12/14 fns MATCH at O4p (rejudge with batch L0; ledger rows read ORACLE_REFUSED, profile L0 lacked the held-out rows, see WU-D8v2-receipt.md) |
| 6 | D8v2 | UNUSED by D8v2: one batch carries arm B + donors (31 units, 16.7 MB est. under the 20 MB batch budget); D has no candidates | - | - | - | NOT SENT |
| 7 | D9 | Ph9 synthesis: fn_802128D4 (24 variants) + fn_8032CF78 (7 variants) at O4p only (O2 dropped: OUT_BUDGET 36.6MB>20MB) + 3 W3b donors = 34 units (build candidate-20261014T160717Z, cap1-fee7b09f053d) | NOT SENT (SEND=CAP_REACHED, phase 1: 4 queue adds recorded, cap 4) | c2e43d028547c4c17f97fae45fce46dadab321615937ecf3f21aa8ab73c927d4 (inputs_hash) | - | - |

