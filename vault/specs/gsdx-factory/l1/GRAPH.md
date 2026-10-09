# L1 GRAPH: proposed work units from non-terminal obligation rows

Source: l1/obligations.json (595 rows; dispose gate exit 0). Only work or wait rows appear; terminal rows
(ALREADY_SATISFIED, REUSE_EXISTING, MERGE, SUPERSEDED) are probed non-work. n is an ESTIMATE (rows/6 slim-t2, rows/4 top).
C(n) = n*F + g*n*(n-1)/2; slim-t2 F=19,000 g=1,700; top F=121,000 g=2,000.

| unit | rows | work class | tier | n | C(n) | dependency |
|---|---|---|---|---|---|---|
| U-CP50 | 3 | transfer canaries after P3/CP50 | top | 1 | 121,000 | WAIT CP50 criterion |
| U-DEFER | 1 | recorded, never funded | none | 0 | 0 | none |
| U-DOCTRINE | 41 | write enforcing text/gates for unenforced doctrine rows | slim-t2 | 7 | 168,700 | none |
| U-KB-W8 | 8 | W8 knowledge writer + PGO owner rows | slim-t2 | 2 | 39,700 | after W7 |
| U-W3 | 14 | W3 S2/S3 residual: calls_unit, per-class g/r, R4 reconcile | slim-t2 | 3 | 62,100 | WAIT ce-lifecycle-v3 INST2 |
| U-W5 | 8 | W5 port control plane to GEX44 (+UWCP evaluation) | top | 2 | 244,000 | WAIT GEX44 port prerequisites (DEPLOY rules) |
| U-W6 | 11 | W6 Part A A-G2..A-G5 after W3 | slim-t2 | 2 | 39,700 | WAIT W3 |
| U-W7 | 1 | W7 Part B coordination on GEX44 | top | 1 | 121,000 | WAIT W5 + P3 |
| U-ZERO | 15 | W4 reforecast / W8 closeout gates over receipts | ZERO_MODEL | 0 | 0 | after receipts exist |

Total modelled: 796,200 tokens (expected, before p_repair).

## Rows per unit
- **U-CP50** (3): cross-project-transfer-canary, reverse-transfer-canary, cross-project-transfer
- **U-DEFER** (1): full-wsr-scope
- **U-DOCTRINE** (41): mission-execution-mode, one-mission-law, context-first-reality-first-law, the-three-mutually-reinforcing-o, ultimate-economic-law, known-work-novel-work-law, opportunity-delegation-must-beco, source-ownership-levels, cognitive-economic-kernel, vmax-null-error, bug-failure-knowledge-contract, agent-teams, self-prompting-continuation-loop, micro-commit-law, ... +27
- **U-KB-W8** (8): automatic-amdahl-reprofiling, phase-14-profile-guided-optimiza, phase-15-cognitive-economics-glo, constitutive-baseline-ratchet-5, failure-knowledge, fios, optimizer-roi, autonomous-amdahl-loop
- **U-W3** (14): scope-preservation, autonomous-reservation-reconcili, program-authority-vs-process-lea, multidimensional-economic-leases, cognitive-purchase-order, cognitive-receipt, call-legitimacy, s2-reported-purpose, phase-2-s2-call-unit-truth, unit-typed-budgets, s2-production-canary, automatic-reservation-reconcilia, unknown-is-not-free, phantom-reservation-prevention
- **U-W5** (8): gex44-advantage, gex44-resource-economics, machine-restart-canary, cross-machine-continuation, gex44-resource-reality, gex44-execution-requirement-2, uwcp-3, resource-aware-gex44-execution
- **U-W6** (11): mission-a-minimum-done-gate, mission-a-canaries, mission-a-master-done-gate, mission-a-objective-rewrite, a-g2-through-a-g5-recompilation, mission-a-economic-done-gate, part-a-reported-state, phase-10-part-a-completion, a-g2-a-g3-learning-gate, part-a-done-gate, master-done-gate-part-a
- **U-W7** (1): part-b-coordination-economics
- **U-ZERO** (15): mission-b-master-done-gate, budget-master-done-gate, master-done-gate-2, economic-master-done-gate-2, do-not-inflate-all-old-rows, phase-13-cognitive-economic-auto, no-budget-inflation-learning, production-reality-gate-4, closeout-economics, master-done-gate-s1-s2-s3-l1, master-done-gate-part-b, master-done-gate-autonomy, master-done-gate-economics, master-done-gate-knowledge, ... +1
