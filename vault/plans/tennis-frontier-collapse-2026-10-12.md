---
covers: [tennis-rf, frontier-collapse, w12a-plus, semantic-residual, lease-succession, claim-evidence, deterministic-first]
status: EXECUTED
owner_prompt: Owner 2026-10-12 ~22:00, "/cpp-gsd-long ... Frontier Collapse" (backlog D28); global optimization incl. CCR
---
# Tennis Frontier Collapse + global corrections -- Master Continuation Plan (2026-10-12)

## 0. Reality Delta Scan (measured 2026-10-12 ~22:00)
- PP HEAD 7e705ee7 (CCR pane); TRF-C closeout 4c7e15fa is below it. Branch feature/knowledge-acquisition, shared tree.
- wt_tennis_rf HEAD f720ee8 (W10b, 10-11 23:49). UNCOMMITTED there: C1 gate (source_lint.py +22, test_source_lint_prereq.py),
  W11/W12 knowledge (tennis_context.{h,h.m2c,py}, test_tennis_context.py), m2c_producer.py (+test), RESUMPTION_FILE.md
  (-146), vault/specs/salvage/. GEX44 copy M/wt has commit 2ab62e70 for the header + its test only. Two copies diverge.
- Authority: goal tennis-rf, programme 90,000,000; ONE lease L1 cap 55,000,000, used 64,104,806, not closed, no successor;
  settled 63,281,998; open 822,808; executable 25,895,194 (`mission_spend.py goal-lineage/programme-status`).
- Succession machinery EXISTS: `ledger.lease_open` (CAS on prev_lease, idempotent by succession_id, AUTHORITY_REQUIRED
  journalled when need > executable), CLI `goal-lease-open`. CCR used it manually (L1 closed 34.0M -> L2 40M, ccr:D:r2).
  Missing: the automatic trigger = D24 dgl W3 `tools/goal_succession.py` (parked: dgl envelope).
- GEX44: no Tennis worker; 62 GB / 55 GB available, load ~1. JOBS.md: 4 approved, 3 used (job 3 judged), job 4 = reserve.
- Laptop: 1.59 GB free of 31.3 GB, 33 claude.exe (other panes) -> below the heavy-worker floor; local work = light only.
- W12 truth: ledger 42 rows, 12/22 MATCH, 9 PARTIAL, 1 COMPILE_FAILED(context), donors 3/3 (`evidence/w12/records.py`).
- P1P2: facts 1,797; knowledge shock 175->276 (+101, 80 outside draws), reproduced; 7/9 gates; blockers.json ranked;
  hypotheses.json (top-10, unresolved); residual_structural per fn (structural only).
- CCR: Work-Class cost model + PoCN-like routing in tools/ccr_pgo.py, tools/gsd_mission.py, tools/tier_routing.py.

## 1. Root-cause matrix
| class | state | evidence |
|---|---|---|
| CLAIM_EVIDENCE_DIVERGENCE | CONFIRMED | W12 prose 14 vs ledger 12 |
| MODEL_BEFORE_DETERMINISTIC_WORK | CONFIRMED | P1P2 37 turns, factor.py written on the last turn, never run |
| DETERMINISTIC_ANALYSIS_KEYERROR | PARTIAL | fixed in place (gid defaults); no regression fixture yet |
| GLOBAL_KNOWLEDGE_NOT_PROPAGATED | PARTIAL | +101 lint-clean measured; the 80 outside-draw fns never compiled/judged |
| NEAR_MATCH_ROOT_CAUSE_COMPRESSION | UNKNOWN | 9 PARTIAL; prior flags: 8021F8BC pointer stride, 8021F3E4 ptmf r12; 6 SIZE +-1-2 words |
| IDIOM_METRIC_UNVALIDATED | CONFIRMED | idioms_test.txt absent |
| STRUCTURAL_CLUSTER_INCONCLUSIVE | CONFIRMED | red 588/524 vs real 926 (needs <=463) |
| MISSING_CONTEXT_ADMISSION_GAP | CONFIRMED | 80252F34 lint-clean yet COMPILE_FAILED context |
| PROGRAMME_LEASE_AUTHORITY_DIVERGENCE | CONFIRMED | capital-apply raised programme only; succession manual; D24 W3 parked |
| UNCOMMITTED_WAVE_STATE | CONFIRMED (worse) | whole C1+W11+W12 knowledge uncommitted in wt_tennis_rf; 2 diverging copies |
| GLOBAL_UNCERTAINTY_FRONTIER_MISSING | PARTIAL | blockers.json ranks items; no dependency edges / propagation |
| SEMANTIC_RESIDUAL_COMPILER_MISSING | PARTIAL | residual_structural exists, not semantic |
| INCREMENTAL_RECONSTRUCTION_MISSING | CONFIRMED | every rerun is whole-corpus |

## 2. Owner map
ALREADY_DONE: W12 records, knowledge-shock measurement, blocker index v0. ACTIVE: Recon Factory (stage/certify/judge), CCR.
EXTEND: P1P2 facts.jsonl -> Whole-Program Evidence Compiler (index, query CLI); blockers.json -> Global Uncertainty Frontier
(+ dependency edges, potential energy); tennis_context.py -> Program Knowledge Compiler (fact = scope/provenance/invalidators);
Technical Capital Allocator -> Frontier Allocator (no new allocator); FIOS/Knowledge Vault/UKDL/CBR.
CONNECT: ledger.lease_open -> automatic succession (D24 W3 scope); CCR Work-Class/PoCN -> deterministic-first gate.
IMPLEMENT (thin, Tennis-local first): Semantic Residual Compiler, Incremental Semantic Build (fact -> dependents ->
dirty set), Failure Causal Graph + counterexample classes (rows in one JSON, not a new graph engine).
RETIRE/ABSTAIN: structural_family and idiom counts as evidence until fixtures/red control pass. NO_WORK until justified:
motif algebra beyond the measured motif index; universal superoptimizer.

## 3. Phases, mode, done-gates (MDG = master done-gate number)
| Ph | Work | Mode | Plane | MDG |
|---|---|---|---|---|
| 0 | Seal: reconcile wt_tennis_rf vs M/wt; causal micro-commits (C1 gate / W11-W12 header+tests / m2c_producer / salvage untracked note); W12 certificate | EXEC | laptop light | 1 |
| 1a | Claim-evidence contract: receipt status derived from ledger; typed CLAIM_EVIDENCE_DIVERGENCE row; regression = W12 14/12 | EXEC | laptop | 2 |
| 1b | Programme->Lease: auto successor lease inside programme (bounded tranche, CAS, idempotent), live breaker reads it; regression = tennis-rf L1 stale | PLAN (touches live hooks: DEPLOY class) | laptop | 3 |
| 1c | Deterministic-first gate: WU class DETERMINISTIC/.../OWNER_REQUIRED in packet; deterministic steps run by the launcher BEFORE model admission; regression = P1P2 | EXEC | laptop | 4 |
| 1d | KeyError fixture (partition-outsider case) + idiom pos/neg fixtures or ABSTAIN + cluster abstention flag | EXEC | GEX44 cpu | 5 |
| 2 | W12A+ autopsy: exact causality (facts used per fn), near-match minimal mismatch signatures -> classes, root-cause compression ratio, 80252F34 dependency + admission story, 175->276 attribution per header fact (leave-one-fact-out m2c+lint reruns) | EXEC | GEX44 cpu | 6,7,8 |
| 3 | Global Residual Census + Semantic Residual Compiler v0 + distance-to-autonomy 0-5 + effective remaining work | EXEC | GEX44 cpu | 9,17,18 |
| 4 | Uncertainty frontier + semantic dominators + potential energy (ranges) + failure causal graph + counterexample compression | EXEC | GEX44 cpu | 10,11,14,15 |
| 5 | Knowledge Shock Sweep: top candidates (helpers fn_800B4508 x89, fn_801CD7D0 x64, cror x67, branch-target x52, jump-table x37 ...) with hypotheses from whole-program evidence + deterministic falsification | EXEC | GEX44 cpu | 11 |
| 6 | First frontier collapse: certify top 1-3 facts, extend header, measure direct unlock (lint-clean/compilable) | EXEC (+ model only for surviving hypotheses) | GEX44 cpu + 1 job | 12 |
| 7 | Incremental recompile: dirty closure from the fact delta only; direct vs transitive unlock | EXEC | GEX44 cpu | 13 |
| 8 | Reuse tournament: arms B (header), D (motif), E (dominator), F (hybrid) on a held-out draw; A from W10c/W12 history (no rerun) | PLAN | 1-2 jobs | 16,19 |
| 9 | Synthesis probe (bounded compiler-in-the-loop on <=16-insn PARTIAL fns), only if Ph2 shows flag/codegen classes | PLAN, gated | GEX44 cpu + job | -- |
| 10 | W13 compiled from evidence; 7-day / 72-hour / theoretical frontiers; W8b+ (static, compounding, frontier, theoretical, separate) | EXEC | laptop | 20,21,22 |
| 11 | Scale Readiness PASS/NO_SCALE; KV/FIOS/UKDL (hard/process/traps)/CBR ratchet incl. CCR | EXEC | laptop | 23-27 |
ULTRA-PLAN: not needed. Every capability has an owner to extend; the only new architecture (residual compiler, incremental
build) starts as Tennis-local JSON + scripts and is promoted to CBR only after Ph7 proves it.

## 4. Key designs (short)
- Authoritative result: `receipt.status := f(ledger)`; worker prose stored as `claim`; mismatch -> divergence row, receipt
  shows ledger number, steward/chain read only the certified field.
- Successor lease: on breaker refusal `budget_spent` with programme executable > tranche: `lease_open(succession_id=
  <goal>:auto:<n>, cap=min(tranche, executable - recovery), prev_lease=latest)` then close prior lease; tranche = P80 of
  the next declared unit (default 8M); never the whole programme; AUTHORITY_REQUIRED (journalled) when the programme is
  short -> that is the only Owner boundary. Lives in the ledger/breaker path for ALL goals (CCR, dgl, tennis-rf).
- Deterministic-first: WU front matter `class:` + `pre: [commands]`; launcher runs `pre` and attaches outputs; the model
  receives only unresolved residual; a DETERMINISTIC unit with model_calls>0 and no typed UNKNOWN/CONFLICT = gate FAIL.
- Residual = facts(fn) - certified(header facts, idioms with fixtures, motif cover, proof) -> {unresolved vars, conflicts,
  obligations, expected unlock}; frontier = residuals grouped by unresolved var; dominator score = blocked fns (direct +
  transitive range) / resolution cost; potential energy reported as [low, high].
- Incremental build: fact id -> dependents (from facts.jsonl access/call/type edges); a delta reruns m2c+lint (+compile
  via job) only on the dirty closure; unchanged targets are never re-reasoned.

## 5. Token budget (this optimization mission only, not Scope B)
Grounding: W12 worker 3.45M/52 calls, P1P2 worker 4.39M/37 turns, W11 3.02M, this coordinator closeout ~2-3M.
| item | P50 |
|---|---|
| Ph0 reality seal + worktree commits | 0.6M |
| Ph1a claim-evidence | 0.8M |
| Ph1b programme->lease (live path, mutation drill) | 2.5M |
| Ph1c deterministic-first gate | 1.5M |
| Ph1d KeyError + idiom fixtures + abstention | 1.0M |
| Ph2 W12A+ (incl. near-match decomposition, shock attribution) | 2.0M |
| Ph3 census + residual compiler | 1.5M |
| Ph4 frontier/dominators/causal graph/counterexamples | 1.5M |
| Ph5 knowledge shock sweep | 1.0M |
| Ph6 first collapse | 2.5M |
| Ph7 incremental recompile | 1.0M |
| Ph8 tournament | 2.5M |
| Ph9 synthesis probe (if admitted) | 1.5M |
| Ph10 W13 + frontiers + W8b+ | 1.5M |
| Ph11 scale gate + KV/FIOS/UKDL/CBR | 1.2M |
| recovery reserve | 1.5M |
| meta-optimization tax (coordination, reads) | 1.4M |
Semantic lower bound 6M (deterministic phases only, no tournament) | LOWER 14M | P50 25.5M | P80 31M | P95 38M.
HARD AUTHORITY requested: programme stays 90M if the mission is cut at P50 (fits 25.9M executable with ~0.4M slack:
too thin); recommended programme 100M (+10M) -> executable ~35.9M covers P80 + reserve. Confidence: medium (units
priced from 3 measured workers; Ph1b and Ph8 carry most variance).

## 6. Resource budget
GEX44 jobs: approved 4, used 3, job 4 reserve. Mission needs: Ph6 1 job (compile-verify the collapse), Ph8 1-2 jobs.
Request: job 4 released for Ph6 + 2 new (jobs 5-6) for Ph8/Ph9, each row-before-send, certified. Deterministic CPU on
GEX44 (m2c/lint/index) does not consume a job slot (as P1P2). Laptop: light coordinator only, 0 heavy workers (1.59 GB
free); heavy-worker concurrency: GEX44 1 headless worker at a time; stop-loss: GEX44 available RAM < 16 GB or laptop
free < 1 GB -> pause new work; no process is killed.

## 7. 7-day / 72-hour / theoretical frontiers (preliminary, falsifiable)
- 7-day Scope B after maturity: needs model-needed fraction <= ~25% of 1,797, verification >= ~400 fns/day (job batches
  of ~40 units today -> needs ~10 jobs/day or larger batches), autonomous rate >= ~200 fns/day, exception queue < 150.
  Evidence: deterministic-layer verified rate 12/22 on lint-clean fns; lint-clean 276/1,797 (15%). UNKNOWN: compile rate
  of the other 254 lint-clean fns, per-root-cause unlock. Measure in Ph6-Ph8.
- 72-hour: needs >= ~60% of fns in DETERMINISTIC/SEARCH-SOLVABLE zones, i.e. several more 100-fn knowledge shocks
  (helper/cror/jump-table blockers already rank 37-89 fns each) and batch verification >= ~600 fns/day.
- Theoretical: lower bound = distinct semantic residuals after all shared facts (unknown; Ph3/Ph4 give the first number).

## 8. Approval surface
Scope: Ph0-Ph11 above, Tennis-local first; global pieces (claim-evidence, auto-succession, deterministic-first) land
for all goals incl. CCR, through tests + mutation drill; the live-hook install (Ph1b) is DEPLOY class and runs its HR
ritual. Authority: programme 90M -> 100M; successor lease L2 = 8M tranche opened by TRF-C now (inside programme, no new
authority), later tranches automatic once Ph1b lands. GEX44: job 4 + jobs 5-6. Gated (returns to Owner): Scope B scale,
any job beyond 6, programme beyond 100M, deleting/rewriting anything outside tennis-rf files. Rollback: every phase is a
pathspec micro-commit, revertible; live-hook change ships with its revert line.

## Outcome (WU-D11, 2026-10-13)
EXECUTED = every phase run to its gate or named blocked; Ph8/Ph9 are not run. Verdict `SCALE-READINESS.md`: **NO_SCALE**.
| Ph | Unit | Status | MDG value | Commit |
|---|---|---|---|---|
| 0 | seal | DONE | 1 | wt_tennis_rf 88d36ff |
| 1a | - | DONE | 2: receipt status from ledger | 729f7387 |
| 1b | - | DONE | 3: auto successor lease (L2..L23) | 3c98097b |
| 1c | D1c | DONE_WITH_LIMITS | 4 | be6060ed |
| 1d | D1d | DONE | 5: structural_family, idiom_family INCONCLUSIVE; 7/7 idioms VALID | 76f2cf5d |
| 2 | D2 | DONE | 6: 22 rows; 7: 5 classes/9 PARTIAL = 0.556; 8: 16 tag + 85 prototype of 101 | f9f4baef |
| 3 | D3 | DONE | 9/17/18: distances 12/263/1307/92/92/31; 1,522 fns unpriced | 4524d258 |
| 4 | D4 | PARTIAL (Owner-accepted) | 10/11/14/15: 3,429 vars; red control falls | e16e8036 |
| 5 | D5 | DONE | 11: 1 SUPPORT, 11 CONTRADICTION of 12 | c2c3b5c0 |
| 6 | D6 | DONE | 12: 0 certified facts, 276 -> 276 | 87231844 |
| 7 | D7 | DONE | 13: closure 44/1797, 5-6x | a921761c |
| 8 | D8 | NOT_RUN (jobs 5-6 approved, no receipt) | 16,19 open | - |
| 9 | D9 | NOT_RUN (job 7 approved, gated) | - | - |
| 10 | D10 | DONE_WITH_LIMITS | 20,21 (7d/72h not reachable), 22 | d8b5812e |
| 11 | D11 | DONE | 23-27: NO_SCALE; promotions in `WU-D11-receipt.md` | this commit |
Tokens (`goal-lineage --goal tennis-rf`, 2026-10-13): programme 100M, settled 84.72M, total used 85.47M, open lease L23 750k at read; L1 63.28M, D-unit leases 0-2.9M each (D2 2.88M, D4 1.73M, D6 1.54M).
