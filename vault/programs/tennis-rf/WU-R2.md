# WU-R2 -- function dossier + closure router classes + decomp-permuter backend (admission only)

Plan: `vault/plans/recon-factory-locality-routing-2026-10-15.md` sections 7, 8, 12, 15 (Owner approved 2026-10-15 "y").
Common brief: `D28-BRIEF.md`. Code lives in wt_tennis_rf `tools/wros/binary/decomp/` (D). Budget: this unit <= 3.0M; stop and
write the receipt at 2.6M.

Inputs: `evidence/d28/d2/near_match.json` (9 PARTIAL, `primary` + `signals`), `wst_tennis/w10/F/candidate_ledger.jsonl`
(136 rows; misses carry miss_class), `evidence/d28/d9/synthesis.json` (31 failed variants, 802128D4 + 8032CF78),
D/router.py (existing Resort tiers: EXTEND, do not fork), D/gex44/candidate.py (judge; read-only in this unit).

Steps:
1. `D/dossier.py`: build(fn) -> {fn, entity, preset, best_source_path, target locator (L0 row: start, insns, bytes_sha256),
   near-match signals, prior attempts (ledger rows for the entity: producer, variant, objdiff, miss_class), family_key}.
   family_key = near_match `primary` + sub-signal + size delta (e.g. `SIZE_-1@9:beq`). No whole-programme context.
2. Router classes in D/router.py: DETERMINISTIC_FIX (POINTER_STRIDE, known idiom), FLAG_SEARCH (sda21_vs_ha_l,
   preset-sensitive), SOURCE_SEARCH (REGALLOC, SIZE_+-n, bool_idiom), SEMANTIC (PTMF_R12, RESIDUAL_UNKNOWN, unknown),
   PROOF_ONLY. Each class -> ordered backends [deterministic, prior, flag_sweep, permuter, model, deep_re]. Choice =
   min expected cost / P(close), P from per-class history in `factory/priors.jsonl` (Laplace (w+1)/(n+2)). A backend whose
   (fn, class, backend, space digest) is in `factory/negative.jsonl` is skipped. Seed negative.jsonl from D9 (31 variants,
   two fns) and the 7 unrun D12 bundles (reason: T2 flat, D12c 0/91).
3. decomp-permuter on GEX44: `git clone https://github.com/simonlindholm/decomp-permuter /opt/ksr-decomp/permuter`, record
   the commit sha; separate venv `/opt/ksr-decomp/permuter-venv` with `pip install toml`. compile.sh from the repo's
   `mwcceppc_compile_example.sh`, using the mwcceppc.exe + wibo from a job's work/tools (copy to /opt/ksr-decomp/mwcc/,
   sha256 must equal the ledger's `compiler_sha256`) and the preset flags from D/match.py. Target .o built from the DOL
   words of the L0 locator (reuse candidate.py/K.dol_words logic; do not edit candidate.py).
4. `D/gex44/permute.py`: dossier -> permuter dir (fn .c, target .o, compile.sh, settings.toml) -> run with budget
   {wall_s, -j, stall_s, max_iter}; emit {best_score, best_source, iterations, cpu_s, wall_s, stop_reason}. Never a verdict.
5. ADMISSION TEST (the gate): a sealed MATCH donor (W3b donor from the ledger) must score 0 at iteration 0 with our
   compile.sh + target .o. Also a red check: the same donor with one constant changed scores > 0. If either fails:
   permuter = TOOL_INCOMPATIBLE, record why, do not run it on Tennis fns.
6. `D/test_router.py`: class per near_match signal (all 9 fns); negative skip; budget termination of permute.py on a
   fake runner; admission gate both poles.

Limits: no GEX44 job (no stage/send), no model calls on functions, no capsule edit, no candidate.py edit.
Done-check: test_router.py exit 0 and the admission result recorded (ADMITTED or TOOL_INCOMPATIBLE with evidence).
Commit by pathspec in wt_tennis_rf. Receipt `WU-R2-receipt.md`: dossier fields, class of each of the 9 fns, permuter sha +
admission result (both poles), cpu_s of the admission, files committed.
