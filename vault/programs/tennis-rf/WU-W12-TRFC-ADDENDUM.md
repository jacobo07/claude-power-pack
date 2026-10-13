# WU-W12 TRF-C addendum -- consumed by the coordinator in W12a, NOT by the live W12 worker

The live W12 worker (mission m-0acd380966c2, armed 18:13 on Owner "activar ya") pinned `WU-W12.md` sha 0d305015;
that packet is left byte-identical. This addendum records what TRF-C adds around it. Fields the worker's records do
not carry are joined post hoc in W12a (family ids, structs, pairs) or marked UNKNOWN (per-stage wall time).
Binding plan: `vault/plans/tennis-rf-compounding-MASTER-PLAN-2026-10-12.md` rev 2 (capital packet 9ff2a9f9, programme 90M).

Executor of W12: worker m-0acd380966c2 (laptop). Coordinator: W12a analysis + W12-R launch on GEX44.
What this job measures: the m2c + certified Tennis context layer with NO model step, i.e. the deterministic-zone
baseline (autonomous reconstruction rate at generation 1). Model cost per function is W12-R, not this unit.

Steps:
1. Draw: DONE (MEASURE.md "W12 draw", seed 20261012). Do not redraw.
2. Prep: DONE on GEX44 (2ab62e70); laptop wt_tennis_rf already holds the post-prep header (content-identical, LF-normalised
   sha a97610866c653a65); laptop TENNIS_CONTEXT_DRILL 9/9. Outputs in `wst_tennis\w12\m2c\c\`, patch `patches/W12-prep-1.patch`.
3. C1 gate: DONE. source_lint MISSING_PRELUDE + UNDECLARED_TYPE (patch `patches/C1-1.patch`); SOURCE_LINT_PREREQ_DRILL 9/9
   (job-2 replay 26/26 refused, 22 composed W12 units clean); FANOUT_PRECONDITIONS 29/29. stage.py build calls lint_unit,
   so a prerequisite-less unit can no longer reach a send.
4. Units: compose the 22 included m2c outputs with `tennis_context.compose` and the presets W10c used. `stage.py build`
   -> `stage.py certify` -> JOBS.md row 3 BEFORE send -> send by the W10b custody route -> `stage wait` -> repatriate -> judge.
   Exactly ONE send. Job 4 stays recovery reserve.
5. Records: append one row per drawn function to `measure/records.jsonl` (schema below). Missing = UNKNOWN, never 0.
6. Restore and read back the custody state as W10b specified, even if the job failed.

Record schema (TRF-C plan s2, s5): fn, set (W5a|W12), lint, excluded_reason, closing_layer (m2c+context | excluded),
verdict (MATCH | PARTIAL % | FAIL class), compiles, model_calls (0 by construction), tokens (coordinator tokens for the
batch / n, labelled BATCH_SHARE), wall_s {prep, build, certify, queue, run, judge}, family_w7 {id, size},
pair_ordinal (fam 8: fn_803315A0/fn_80257978; fam 755: fn_80278FEC/fn_8025C600), structs_used [tags from the header],
structs_new_in_prep (bool), hazards (W12-prep: fn_8021F8BC ptr stride, fn_8021F3E4 ptmf r12), failure_capital
(counterexample | hypothesis | idiom | missing knowledge | NONE -> unproductive).

Done-check: JOBS.md row 3 judged; 24 records; MEASURE.md table: deterministic-layer MATCH rate with n, by W7 family size
(singleton vs family >=2) and by struct source (W11 vs prep); custody read back.
Receipt: written by the worker. W8b is held on `W8B-READY.md` (chain.json), so the W12 receipt does not arm it.

Next unit (W12-R, GEX44): one headless `claude -p` per non-MATCH function (stream-json usage = exact per-function tokens),
family-pair members in ordinal order with the first member's result in the second's context; candidates go into the
W13 job (job 5), not a separate job.
