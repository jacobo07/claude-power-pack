# CE unify -- obligation ledger (WU-U1, 2026-10-09)

Input: `Downloads\Dataset CE Gen1 Gen2 Optimization and Evolution 1.md`, sha256 A15765B5...87B1 (verified, 1,343 lines per dossier; read as DATA).
Owners read: ce-a4 `ce-a4-estate-rearm-2026-10-08.md` (units W0-W3), `ESTATE_QUEUE.md`; lifecycle `RESUMPTION.md` (the file at that path is headed ce-lifecycle-v2; v3 units WU-S1..S3 and S6 are known from the dossier and commit f7711c81, their packets were not read).
HR-NOVELTY-001: no new programme. `goal-autopsy` is not mentioned in the ce-a4 estate-rearm plan or ESTATE_QUEUE (grep, step 1), so D-01 is an extension of ce-a4.
The dataset line numbers are the first line of the passage. The dataset is 62 numbered proposals plus an R5 status report (L2-31).

| id | line | obligation | owner | disposition |
|---|---|---|---|---|
| D-01 | 7 | goal-autopsy reaches LIVE tools/mission_spend.py (branch ce/a3b-r only) | ce-a4 W1a (integrate deltas by file) | EXTEND (ce-a4 W1a; no a4 doc names it) |
| D-02 | 10 | R5c closes R5: receipt, suites, mutation test | m-447ca8005684 (ce-a3b-r) | ALREADY-DONE (R5c COMPLETED; code 88d37fe9, 6902264d) |
| D-03 | 14 | failure-registry wiring | ce-lifecycle-v2 R4 (Amendment D, 3aa002af) | OWNED |
| D-04 | 28 | admission must read goal remaining (remaining=None) | ce-a4 W1b default binding | EXTEND (ce-a4 W1b) |
| D-05 | 28 | R1 guard not live until R3 | ce-lifecycle-v2 WU-INST (L5) | OWNED |
| D-06 | 29 | finished worker's reserve freed only by manual goal-reconcile | none found | UNKNOWN (decide: does the sweep call goal-reconcile on COMPLETED?) |
| D-07 | 102 | Gen1 results become conditional findings (workload, invalidators, reopen) | ce-a4 W3 UKDL via CEPS | EXTEND (ce-a4 W3) |
| D-08 | 143 | lever interaction matrix | none | UNKNOWN (decide: two levers measured on one Work Class after W1a) |
| D-09 | 184 | runtime reopen triggers for dormant negatives | ce-a4 W3 UKDL via CEPS | EXTEND (ce-a4 W3) |
| D-10 | 211 | negative knowledge blocks re-investment (non-investment proof) | ce-a4 W3 UKDL | EXTEND (ce-a4 W3) |
| D-11 | 238 | experiment ROIC / falsification value | ce-a4 W3 Semantic PGO | EXTEND (ce-a4 W3) |
| D-12 | 277 | classify workload by dominant bound (roofline) | ce-a4 W3 autopsy profile | EXTEND (ce-a4 W3) |
| D-13 | 347 | continuous observe-classify-replay-canary-promote loop | ce-a4 W3 (self-host, Canary 15) | OWNED |
| D-14 | 362 | ask why work exists, not only cost | none (slogan, no deliverable) | REJECT (no measurable output; covered by D-18/D-35) |
| D-15 | 399 | known-work fraction per call class | ce-a4 W2b Work Extinction | UNKNOWN (decide: one autopsied mission classified; gen2 says this lever is unmeasured) |
| D-16 | 455 | irreducible lower bound / overhead multiplier | none | UNKNOWN (decide: a definition of "decision" countable from receipts) |
| D-17 | 480 | KPI = novelty concentration / known-work tax, not token % | ce-a4 sec.9 deflation definition | EXTEND (ce-a4 W3) |
| D-18 | 505 | work-class learning curves | ce-a4 sec.9 one class before/after | EXTEND (ce-a4 W3) |
| D-19 | 563 | worker lifetime learned per class; epoch lifetime | ce-lifecycle (v3 S-units) | OWNED |
| D-20 | 594 | stochastic expected-verified-completion cost | ce-a4 W1c single routing table | EXTEND (ce-a4 W3 PGO) |
| D-21 | 623 | compile known plans (template + delta), plan check in software | ce-a4 W2b planner/reviewer extinction | OWNED |
| D-22 | 671 | meta-work tax SLO near zero | ce-a4 W3 Cognitive CI | EXTEND (CI clause) |
| D-23 | 702 | ownership-mapping (7.84M) becomes an owner index | ce-a4 W3 Read Extinction (dossier) | OWNED |
| D-24 | 727 | automatic Token Incident on cost outlier | ce-a4 W3 Cognitive CI | EXTEND (CI clause; first record is incident-ce-lifecycle-v2-overrun.md) |
| D-25 | 756 | profile-guided optimization from past missions | ce-a4 W3 Semantic PGO | OWNED |
| D-26 | 785 | counterfactual replay before building | gen2 W4 offline replay; ce-a4 W3 | EXTEND (ce-a4 W3) |
| D-27 | 812 | universal holdout (unseen Work Classes) | ce-a4 W1-gate Canary 1 (non-PP repo) | EXTEND (ce-a4 W1-gate) |
| D-28 | 831 | token delta CI on every CPP change | ce-a4 W3 Cognitive CI | OWNED |
| D-29 | 848 | Token NPV, CAPEX/OPEX split | ce-a4 W3 PGO | EXTEND (one NPV field in autopsy) |
| D-30 | 882 | capitalization rate, decision-surface metric, debt register, balance sheet | none | REJECT (new instruments; D-32 covers rent) |
| D-31 | 989 | cost-of-change per module as NFR | none | UNKNOWN (decide: autopsy per-file token attribution exists) |
| D-32 | 2406 | shrink constitution; token rent ledger by surface | ce-a4 W1c prompt extinction | EXTEND (CLAUDE.md linter 39,812 chars is the signal) |
| D-33 | 1029 | APIs make wrong decision impossible | none | REJECT (principle, no deliverable) |
| D-34 | 1137 | institutional cognitive deflation as supreme KPI | ce-a4 sec.9 | EXTEND (same as D-17; one class, stated normalisation) |
| D-35 | 1776 | extinction compilation per obligation; proof of no cognition | ce-a4 W2b + W1a dossier | OWNED |
| D-36 | 1844 | cost-based plan optimizer, superoptimizer, continuous partial evaluation | none | REJECT (new compiler = new programme; no measured basis) |
| D-37 | 1939 | common subexpression elimination, cross-goal derivation, singleflight | cost-collapse singleflight via ce-a4 W1a | EXTEND (ce-a4 W1a) |
| D-38 | 1981 | semantic state versions; no transcript inheritance | ce-a4 W2c ContextImage (Canary 5); capsule-v2 | OWNED |
| D-39 | 2025 | cognitive virtual memory (paging) | none | REJECT (new subsystem, nothing measured) |
| D-40 | 2050 | tool-schema linker; zero-copy tool output | none | UNKNOWN (decide: measure schema rent; Gen1 filtering was 2.67%, L1236) |
| D-41 | 2094 | proof compiler, executable proof transaction | ce-a4 W2b | OWNED |
| D-42 | 2149 | compiled research | none | REJECT (no owner, no measurement) |
| D-43 | 2170 | known failures handled by policy | ce-lifecycle (v2 R4, v3) | OWNED |
| D-44 | 2185 | tokenless handoff and scheduling | ce-a4 W2c parentless chain; lifecycle | OWNED |
| D-45 | 2223 | waiting costs zero (event wake) | ce-a4 W2c zero-hot WAITING | OWNED |
| D-46 | 2238 | route provider per Work Class; frontier purity | ce-a4 W1c one routing table | EXTEND (purity metric UNKNOWN, not built) |
| D-47 | 2343 | cognitive leases | ce-lifecycle (lease + reserve in RESUMPTION) | OWNED |
| D-48 | 2569 | capital allocator by ROIC | HR-NOVELTY-001 + per-goal caps already gate this | REJECT |
| D-49 | 2600 | finding to CBR global baseline | ce-a4 W3 CBR | OWNED |
| D-50 | 1186 | no invented global % target; certified capability or negative result | gen2 measured-only rule (MISSION.md) | ALREADY-DONE (gen2 MISSION rule; commit not read) |

Counts (50 rows): ALREADY-DONE=2, EXTEND=19, OWNED=16, REJECT=7, UNKNOWN=6
