# WU-D12b -- naive arm vs shared-residual Factory arm, one bulk job, forecasts, W13 verdict (job 4)

Common brief: `D28-BRIEF.md`. Plan: `vault/plans/d12-factory-scaling-2026-10-13.md` (sections 3, 5, 7). Inputs:
`WU-D12a-receipt.md` and `evidence/d28/d12/` (struct_clusters.json, residuals_v1.jsonl, hypergraph.json,
joint_delta.json, motif_mass.json), D3/D5/D7 evidence, W12 route, JOBS.md, `goal-lineage --goal tennis-rf`.
If D12a's receipt is not DONE / DONE_WITH_LIMITS, write `Status: BLOCKED` naming what is missing and stop.

Steps:
1. **Naive arm (control).** Seeded draw of 8 fns, 2 per class 2-5, from fns NOT in the clusters chosen in step 2.
   Per fn, one independent attempt with the current header only. Measure model tokens per attempt (from the
   transcript or the route's accounting, never estimated), verdict, repairs, facts discovered.
2. **Shared-residual arm.** Take the top 2-3 struct clusters from D12a's ranking (by Expected Bulk Unlock, not
   degree). For each: build ONE evidence pack from a seeded half of its dependents (accesses, widths, ops,
   callers, provenance); the model resolves the layout once; the layout enters the header as a fact; D7 dirty-set
   recompile propagates to ALL dependents. Held-out = the dependents not in the pack. Measure per cluster: tokens,
   fns moved down the distance ladder, newly lint-clean, in-sample vs held-out, conflicts.
3. **One bulk job (job 4).** Newly lint-clean dependents + the naive 8 + 3 donor controls, W12 route. Row 4 of
   JOBS.md (Unit D12b) BEFORE sending. Model work only on residual left after the header (record which fns got
   any). Measure verified per hour and per M tokens, marginal model tokens per added dependent in send order,
   donors 3/3 MATCH (else the job is INVALID and no rate is stated).
4. **Counterexamples.** If >= 10 failures: cluster by minimal signature (W12 near-match classifier); report failures
   vs classes (Root-Cause Compression Ratio). Repair classes, not fns, only if budget remains; else list them.
5. **Synthesis.** `scaling.json` + receipt with: naive baseline, dependency-dense sample, shared residual classes,
   joint-delta result (from D12a), motif/proof reuse, search-solvable fraction, bulk throughput, counterexample
   compression, Bulk Amortization Factor (measured both sides), marginal function and residual cognition,
   model-needed fraction after propagation, autonomy promotion, Research Frontier Size, Effective Remaining Work
   (separate from raw 1,522), and the six forecasts of plan section 5, each labelled, never one headline. A value
   without evidence is UNPRICED, never a linear fill. Scaling verdict: STRONG / MODERATE / WEAK / INSUFFICIENT.
   Update `vault/plans/tennis-frontiers-2026-10-13.md` (old numbers struck through, not deleted) and reconcile W8b's
   Scope A forecast. W13: recommended architecture + admission verdict per plan section 7; do NOT arm W13 and do not
   request jobs 8+ (state the exact request, if any).
6. Knowledge: only patterns this evidence confirms, deduped against PR-CONTROL-PERTURBS-THE-SIGNAL-001: a
   knowledge_vault core BL file + UKDL entry (pathspec, only your hunk if the file has another writer's hunk).
7. `test_d12b.py`: draws reproduce from seeds; held-out set disjoint from evidence packs; every forecast figure
   traces to a row; naive baseline and Factory forecast are separate fields; donors 3/3.

Limits: one job only (job 4). Stop-loss: if the first cluster's held-out dependents gain nothing (no ladder move,
no lint-clean), do not resolve a third cluster. Needing a second job -> `Status: BLOCKED_HUMAN` with the request.
Done-check: `test_d12b.py` exit 0; frontiers file updated; evidence committed (pathspec).
Receipt: `WU-D12b-receipt.md`.
