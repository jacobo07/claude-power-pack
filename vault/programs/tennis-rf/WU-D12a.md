# WU-D12a -- residual identity, conjunctive hypergraph, joint delta, search + motif scan (GEX44 CPU, no model on fns, no job)

Common brief: `D28-BRIEF.md`. Plan: `vault/plans/d12-factory-scaling-2026-10-13.md` (Owner addendum 2026-10-13: measure
the scaling law of the class 2-5 remainder after shared uncertainty is compressed; never price fns linearly).
Inputs: `evidence/d28/d3/` (residuals.jsonl, tools/residual.py), `evidence/d28/d4/frontier.json`, `evidence/d28/d5/`
(tools/d5.py asm check + intervention, cror_unlock.json), `evidence/d28/d7/` (dirty.py, d7.py), d1d idioms_status,
W12 evidence + D2 near_match.json. Reality-scan script: `evidence/d28/d12/tools/hg_scan.py` (its two readings are
the bounds in plan section 1; reproduce them first).

Steps (all deterministic; GEX44 CPU, 20 cores; laptop light only):
1. **Base-object identity.** For every `field_offset_untyped` / `field_untyped` occurrence in classes 2-5, trace the
   base register to its provenance root (arg rN of the fn, global label, helper return, value loaded from a known
   field) and merge roots across call edges (caller passes the same root as the callee's argument). Output
   `struct_clusters.json`: cluster id, member (fn, offset, access width, op), provenance evidence; two widths at one
   offset in one cluster = CONFLICT, kept. Rewrite the residual ids to `STRUCT:<cluster>+<off>` in a NEW
   `residuals_v1.jsonl` (D3's file is not modified). Report distinct vars before/after collapse.
2. **Conjunctive hypergraph.** From residuals_v1: closure curve (fns fully unblocked vs vars resolved, greedy as in
   hg_scan), components, private-var fraction, vars per fn quantiles, distance-to-autonomy histogram. Fns with an
   m2c-kind var are flagged RESIDUAL_UNKNOWN (D5: hidden co-blockers), reported apart, never counted as closed.
   `hypergraph.json`. Label every curve as STRUCTURE, not cost.
3. **Joint delta.** Candidate bundles = var sets that CLOSE a target set (every var of each target fn), all components
   script-stateable (HELPER prototype admitted by the D5 asm check; STRUCT field width from the access op).
   Expected Bulk Unlock = target fns closed / bundle size; degree is not an input. Run the top <= 10 bundles through
   the D7 dirty-set recompile (m2c + lint). Record per bundle: targets, newly lint-clean, hidden blockers revealed,
   new errors, complementarity = unlock(bundle) - sum of single-component unlocks (D5 values where measured, else
   run them). Controls: no-op (unlock 0, byte-identical), D5 wrong-delta (rejected), and a size- and degree-matched
   bundle closing no target set. Stop-loss: if the top 3 bundles unlock 0 and reveal nothing, stop and record.
   `joint_delta.json`.
4. **Search scan.** Is decomp-permuter (or an equivalent CPU search) already installed on GEX44? If yes: bounded runs
   (<= 30 min wall each, CPU only) on the 9 W12 PARTIAL fns and D2 near_match; record improved/MATCH. If no:
   record ABSENT and the install command; do not build or install a search tool in this unit.
5. **Motif mass.** Per class 2-5: instructions covered by VALID idioms/motifs (d1d) / total instructions; proof
   family coverage. `motif_mass.json`.
6. `test_d12a.py`: hg_scan bounds reproduce; residuals_v1 has one row per D3 row and the same fns; every collapsed
   id traces to provenance evidence; CONFLICTs preserved; closure curve reproduces; joint-delta controls behave;
   bundle selection uses no degree field (grep the selector).

Limits: no model calls on functions, no GEX44 job. A step that cannot be done deterministically is recorded as
MODEL_NEEDED with the reason, never guessed.
Done-check: `test_d12a.py` exit 0; evidence in `evidence/d28/d12/` committed (pathspec).
Receipt: `WU-D12a-receipt.md` (include: vars before/after collapse, closure curve, bundle table, search ABSENT/result,
motif mass, and the ranked struct clusters D12b should resolve first).
