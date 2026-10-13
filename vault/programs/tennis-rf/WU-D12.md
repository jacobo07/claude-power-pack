# WU-D12 -- pricing unit: joint-delta unlock + model price per function on classes 2-5 (GEX44, job 4)

Common brief: `D28-BRIEF.md`. Owner, 2026-10-13, in the D28 coordinator pane: "I approve that" (the pricing unit
proposed after D10, so the rest of Tennis can be estimated from measurements). Inputs: `WU-D3-receipt.md` and
`evidence/d28/d3/` (distance classes, residuals.jsonl), `evidence/d28/d4/frontier.json`, `evidence/d28/d5/`
(tools/d5.py intervention + re-eval, cror_unlock.json `not_unlocked`, causal_unlock.json), WU-D6/D7 receipts
(dirty-set recompile), `vault/plans/tennis-frontiers-2026-10-13.md`, MEASURE.md, JOBS.md.

Why: the frontiers file says the deterministic path ends at 100-198 MATCH of 1,797, and the ~1,522 functions of
classes 2-5 have no measured price. This unit measures two things and nothing else. It does not try to raise
MATCH for its own sake.

Steps:
1. **Joint delta (no model, no job).** Take the 56 cror-rewritten fns from D5 `cror_unlock.json` `not_unlocked`
   with their now-visible blockers. For each, apply ALL its HELPER blockers' asm-consistent prototypes at once
   (the D5 asm check decides what is admissible; a blocker with no admissible delta is recorded, not guessed),
   re-evaluate with the D7 dirty-set recompile (m2c + lint, 20 cores), and record per fn: blockers, deltas applied,
   lint-clean yes/no. Report `joint_unlock.json` and the count newly lint-clean against D5's single-delta 0.
   Controls: a no-op delta set (unlock 0, byte-identical) and the D5 wrong-delta set (rejected by the asm check).
2. **Model price (job 4).** Draw 20 fns from classes 2-5, recorded seed, stratified by class (5 per class, or
   proportional with the rule written down when a class has fewer than 5). For each, the model supplies the
   missing facts the class needs (struct layout, local types, signature) as header deltas, the W12 route
   compiles and judges them in ONE job, with 3 donor controls. Write the JOBS.md row 4 (Unit D12) BEFORE sending.
   Record per fn: model tokens (measured from the transcript or the route's own accounting, never estimated),
   verdict (MATCH / PARTIAL / BLOCKED_CONTEXT / compile_error), and the facts used.
3. **Price.** `pricing.json`: MATCH rate per class with Wilson95 and n, tokens per fn and per MATCH (median and
   P90, measured), and the extrapolation to the remaining class 2-5 population with its basis tagged M / D / H.
   Update the theoretical and 7-day sections of `vault/plans/tennis-frontiers-2026-10-13.md` with these figures,
   keeping the old numbers struck through, not deleted.
4. `test_d12.py`: reproduces step 1 from the recorded inputs (sha equal), the two controls, the seeded draw
   reproduces, every pricing figure traces to a row, donor controls 3/3 MATCH (else the job is INVALID and the
   price is not stated).

Limits: one job only (job 4). Jobs 8+ are NOT approved; if a second job is needed, write `Status: BLOCKED_HUMAN`
with the exact approval. No price is stated from fewer than the drawn n, and an empty class says UNKNOWN.
Done-check: `test_d12.py` exit 0 and the frontiers file updated and committed (pathspec).
Receipt: `WU-D12-receipt.md`.
