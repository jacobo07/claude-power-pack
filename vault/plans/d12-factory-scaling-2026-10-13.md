# D12 Factory scaling -- addendum merged into D28 (2026-10-13)

Owner addendum, 2026-10-13 (D28 coordinator pane): D12 must measure the scaling law of the class 2-5 remainder
after shared semantic uncertainty is compressed, not a price per function. This file is the Master Continuation
Plan; the packets are `vault/programs/tennis-rf/WU-D12a.md` and `WU-D12b.md`. They supersede the unarmed
`WU-D12.md` (ecc8b20d), which was never launched.

## 1. Reality delta (measured 2026-10-13 20:00-20:15)

- HEAD 7f80e927 (merge; D28 last own commit ecc8b20d). Coordinator: this pane, main checkout.
- Chain: D1c..D10 and W8b closed (W8b DONE, 0.63M). D11 armed `m-4e4c2a58f2ef` PREPARED. D8, D9, D12 not armed.
- Goal tennis-rf: settled 84,721,187; open 750,000 (D11 lease); envelope 100M -> 14.5M executable.
- Jobs: approved 7, used 3 (1-3), job 4 unsent and assigned to D12, 5-6 D8, 7 D9. Jobs 8+ not approved.
- W13 packet exists (D10, class-1 per-function wave, needs jobs 8+). NOT in chain.json. Stays gated (section 7).
- W8b Scope A forecast (88M P50, `vault/plans/d21-tennis-token-budget-2026-10-12.md`) predates D12 and is a
  topology forecast without measured compounding: it is reconciled by D12b, not cited as the Tennis forecast.
- The "1,522 fns x 50-200K = 75-300M tokens, weeks" figure from this pane is the **NAIVE INDEPENDENT-FUNCTION
  UPPER BASELINE** (assumptions: 1,522 fns, 50-200K each assumed, no compounding). It is not a forecast.

Residual census sharing scan (read-only, `evidence/d28/d3/residuals.jsonl`, script kept in D12a evidence):
| reading | distinct vars | private (degree 1) | fns fully closed by first 400 vars-resolved order |
|---|---:|---:|---|
| offsets keyed by bare offset (optimistic, INVALID identity) | 3,962 | 3,158 | 400 fns at 227 vars |
| offsets keyed per function, m2c fns dropped (pessimistic) | 11,685 | 11,223 | 400 fns at 775 vars; 1,306 at 11,685 |

- 13,745 residual occurrences (= D10's number). Kinds: field_offset_untyped 8,274 (60%), helper 2,898, field_untyped
  1,134, field 962, qtype_local 400, m2c 157, m2c_failed 92, self_sig 77. 32 fns name no var (UNKNOWN).
- **Premise defect found:** D3's residual compiler v0 keys an untyped field offset by the bare offset (`0x24`),
  with no base object. So the sharing of 60% of the residual mass is UNMEASURED: it is neither shared (the
  optimistic reading merges unrelated structs) nor private (the pessimistic reading splits one struct's layout
  across its users). The Research Frontier lies between ~4k and ~11.7k vars and the two bounds give different
  scaling shapes. Measuring base-object identity is the first and cheapest experiment in D12.
- D5 proved visible vars are a lower bound where m2c failed (hidden co-blockers appear after cror): fns with an
  m2c-kind var carry an UNKNOWN residual until m2c succeeds.

Iteration check (iteracion-avanzada-universal phase 1): false premises = (a) WU-D12 v1 priced fns linearly,
(b) offset identity in the census. Both are root causes; both are fixed by the packets below.

## 2. Merge into D28

Smallest high-information change: D12 becomes two chained units after D9. Nothing done is repeated; D3 census,
D4 frontier, D5 asm check + intervention tooling, D7 dirty-set recompile and the W12 route are reused as is.

| unit | owner of | model on fns | job | route / cap |
|---|---|---|---|---|
| D12a | identity, hypergraph, joint delta, search scan, motif mass, Expected Bulk Unlock | none | none (GEX44 CPU) | route-S 1.6M |
| D12b | naive arm, shared-residual arm, held-out reuse, bulk verify, counterexamples, forecasts, W13 verdict | yes, bounded | job 4 | route-M 3.5M |

## 3. Lanes (admitted / stop-loss)

- **Census + identity (D12a 1).** Base-object provenance of every untyped offset access (arg rN, global label,
  helper return, loaded field), merged across call edges; conflicting widths at one offset = CONFLICT, kept.
  Output: struct_clusters.json, residual vars after collapse. Stop-loss: none, it is the denominator.
- **Hypergraph + closure curve (D12a 2).** fn -> set of collapsed vars (conjunctive). Closure curve, components,
  private fraction, distance-to-autonomy histogram. Structural scaling shape, labelled as structure, not cost.
- **Joint delta (D12a 3, Lane D).** Bundles chosen to CLOSE target sets, ranked by Expected Bulk Unlock = fns whose
  whole var set the bundle completes / bundle cost; degree is not an input. Only script-stateable components
  (HELPER via the D5 asm check, FIELD width from the access op). <= 10 bundles via the D7 dirty-set recompile.
  Complementarity = unlock(bundle) - sum unlock(singles). Controls: no-op, D5 wrong-delta, and a
  degree-and-size-matched bundle that closes no target set (perturbs the closure signal the claim depends on,
  PR-CONTROL-PERTURBS-THE-SIGNAL-001). Stop-loss: if the top 3 bundles unlock 0 with no hidden-blocker reveal,
  stop the lane and record.
- **Search scan (D12a 4, Lane F).** If decomp-permuter (or an equivalent) is already on GEX44: bounded CPU runs on
  the 9 W12 PARTIAL fns + D2 near_match. If absent: record ABSENT; do not build one in D12.
- **Motif mass (D12a 5, Lane E prep).** Share of class 2-5 instructions covered by VALID idioms/motifs (D1d), per class.
- **Naive arm (D12b 1, Lane A).** 8 fns, 2 per class 2-5, seeded, independent; the architecture to beat. Never
  extrapolated as the Factory forecast.
- **Shared-residual arm (D12b 2, Lanes B/C).** Top 2-3 struct clusters by Expected Bulk Unlock: the model resolves
  each layout ONCE from a whole-program evidence pack built from HALF the dependents; the layout enters the
  header; D7 propagates to all dependents. Held-out = the other half (no leakage). Measured: fns moved down the
  autonomy ladder, newly lint-clean, held-out vs in-sample, tokens per resolved uncertainty.
- **Dependency-dense bulk + verification (D12b 3, Lanes B/G).** Newly lint-clean dependents + naive 8 + 3 donors in
  ONE job 4. Marginal function cognition (model tokens on the nth dependent vs the first), Bulk Amortization
  Factor = naive tokens per verified MATCH x bulk verified / bulk-path tokens (measured both sides), verified
  per hour and per M tokens.
- **Counterexamples (D12b 4, Lane H).** Failures clustered by minimal signature (W12 near-match classifier):
  failures vs classes = Root-Cause Compression Ratio. Only if failures >= 10.
- **Synthesis (D12b 5).** Forecast separation (section 5), frontiers update, W13 verdict (section 7), KV/UKDL.

## 4. Token budget (M processed tokens; worker sessions incl. coordination)

| line | semantic lower | LOWER | P50 | P80 | P95 | HARD |
|---|---:|---:|---:|---:|---:|---:|
| remaining D28 chain (D11, D8, D9) | 1.5 | 3.0 | 5.0 | 6.5 | 8.0 | ledger |
| D12a total (lanes 1-5, no model on fns) | 0.5 | 0.9 | 1.5 | 2.0 | 2.3 | 1.6 + breaker closeout |
| D12b total | 1.2 | 2.0 | 3.0 | 3.8 | 4.3 | 3.5 + breaker closeout |
| - naive arm (8 fns) | 0.2 | 0.3 | 0.5 | 0.8 | 1.0 | in D12b |
| - shared-residual arm (2-3 layouts) | 0.2 | 0.3 | 0.6 | 0.9 | 1.2 | in D12b |
| - dependency-dense + bulk verify (1 job) | 0.1 | 0.2 | 0.4 | 0.6 | 0.8 | in D12b |
| - counterexample compression | 0 | 0.05 | 0.15 | 0.3 | 0.4 | in D12b |
| - forecast synthesis + KV/UKDL | 0.2 | 0.3 | 0.5 | 0.6 | 0.7 | in D12b |
| - joint delta / search / motif (D12a) | 0.2 | 0.4 | 0.7 | 1.0 | 1.2 | in D12a |
| closeout reserve (D28) | | | 1.0 | 1.0 | 1.0 | |
| **total to D28 close** | 3.2 | 6.9 | 10.5 | 13.3 | 15.6 | 14.5 executable |

Reconciliation: P80 13.3M fits the 14.5M executable; P95 does not. D12 P50 4.5M sits inside the 3-5M the Owner
approved; P80 5.8M is above that figure, and the ledger refuses any arm whose need exceeds what remains, so
nothing overspends silently. No new Owner gate now. If D8/D9 come in above P80, D12b is deferred and the Owner
is asked then, with the numbers.

## 5. Forecast contract (D12b writes all six, never merged into one headline)
1. NAIVE INDEPENDENT UPPER BASELINE: naive-arm tokens per verified MATCH x 1,522, stated with its n and labelled.
2. MEASURED CURRENT FACTORY: costs actually observed on the shared-residual + bulk path, per resolved uncertainty.
3. COMPOUNDING FORECAST: only if held-out transfer > 0 and marginal cognition decays; else UNPRICED.
4. 7-DAY FRONTIER and 5. 72-HOUR FRONTIER: conditions that must hold, recomputed from D12; never "reachable"
   without evidence.
6. THEORETICAL COMPRESSION FRONTIER: collapsed Research Frontier Size (vars after identity collapse, minus vars
   closed by scripts) vs raw outputs 1,522; reported as both counts.
Remaining work always reported as raw functions AND Research Frontier AND Effective Remaining Work.

## 6. Owner map (abridged)
Residual Census: EXTEND (identity). Evidence compiler: EXTEND (provenance pass). Dependency representation:
EXTEND (residuals.jsonl keyed by collapsed ids; no new graph). Joint-delta tooling: EXTEND d5.py. Incremental
semantic build: ALREADY_DONE (D7). Candidate generation: ACTIVE (m2c + header). Compiler-in-loop search: UNKNOWN
owner, D12a scans, no build. Verification factory: ACTIVE (W12 route). Counterexample compression: PARTIAL
(near-match classifier). Motifs/proof reuse: PARTIAL (D1d idioms; proof family UNKNOWN for most fns). Frontier
allocator / capital allocator: CONNECT (Expected Bulk Unlock feeds W13). W8b forecasting: DONE, reconciled by
D12b. W13: GATED. Mode: EXECUTION for every workstream; no owner is missing, so no ULTRA-PLAN.

## 7. W13 admission gate (jobs 8+)
W13 is not armed when D12 ends. Before any job 8+ request, the D12b receipt must answer, with numbers:
held-out transfer of a shared layout (yes/no, n); joint-delta unlock beyond singles; marginal cognition trend;
Root-Cause Compression Ratio (or "too few failures"); model-needed fraction after propagation; best verified
frontier reduction per M tokens across arms. W13 is then recompiled from the winning arm (joint-delta wave,
residual-class wave, motif wave, search expansion, or hybrid). If per-function model work still dominates, the
receipt says so and names the next shared abstraction to test before any scale request.

## 8. Root-cause matrix
NAIVE_PER_FUNCTION_FORECAST_MISFRAMED CONFIRMED (this pane's 75-300M). FACTORY_SCALING_UNMEASURED CONFIRMED.
D12_LINEAR_PRICING_RISK CONFIRMED (WU-D12 v1). SHARED_RESIDUAL_REUSE_UNMEASURED CONFIRMED (identity defect).
JOINT_DELTA_UNMEASURED CONFIRMED. COMPLEMENTARITY_UNMEASURED CONFIRMED. MOTIF_REUSE_UNMEASURED PARTIAL (cover
exists, transfer unmeasured). PROOF_REUSE_UNMEASURED CONFIRMED. SEARCH_SOLVABLE_FRACTION_UNDERMEASURED PARTIAL
(167 donor-exact is W7's lower bound; no search lane exists). COUNTEREXAMPLE_COMPRESSION_UNMEASURED PARTIAL (5/9
on W12). RESEARCH_FRONTIER_UNPRICED CONFIRMED. W13_PREMATURE_SCALE_RISK CONFIRMED (packet exists, gated).

## 9. Knowledge (written at D12b close, only what the evidence confirms)
Candidates: RAW_FUNCTION_COUNT_USED_AS_COGNITIVE_WORK (this pane, confirmed), RESIDUAL_IDENTITY_WITHOUT_BASE_OBJECT
(confirmed today), JOINT_DELTA_UNMEASURED / SINGLE_DELTA_ZERO_MISREAD (pending D12a), RESOURCE_SCALE_BEFORE_
ARCHITECTURE_SCALE (pending D12b). UKDL hard/process rules and traps from the addendum are promoted only after
D12 evidence and dedupe against PR-CONTROL-PERTURBS-THE-SIGNAL-001 and BL-2026-08-25.
