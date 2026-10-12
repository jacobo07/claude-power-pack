# WU-W11 -- Tennis context: make the W5a draw sendable (local only, zero GEX44 jobs)

Common brief: `PROGRAMME.md`. Owner "si" 2026-10-12 (continue Tennis after W9 HANDOFF section 7). Read first:
`WU-W10c-receipt.md`, `MEASURE.md` (W10c section), `KNOWLEDGE.md`, `JOBS.md` row 2.

Job 2 (ksrmb-20261011-233503) gave 0/26 MATCH. 4 fns BLOCKED_CONTEXT (fn_80203FEC, fn_8022621C, fn_80257978,
fn_8025C600), 1 fn compile_error (fn_801BD194), and 7 of the 12 were refused by the source lint before send
(UNK_FIELD). This unit makes the 12-function W5a draw compile-ready with Tennis context. It does NOT send.

Steps:
1. Classify fn_801BD194's compile_error from the job 2 return tree (compiler log of that unit), and add a KNOWLEDGE.md
   entry. If it is a tool defect, gate it RED first.
2. Build a Tennis context header from evidence only: SportsPackEP.dol symbols/splits, SDA/data refs and xrefs from
   step0..step3 evidence, struct offsets cited from the asm. Each struct or field cites its source. Precedent (read
   only, never write there): CP50 R3b `wt_cp50_c2\tools\wros\binary\decomp\arm_a_context.h` and the m2c `--context`
   option in that tree's `m2c_producer.py`. Port what you need into wt_tennis_rf with a test.
3. Regenerate m2c for the 12 functions with that context. Never weaken `gex44/source_lint.py` and never hand-edit m2c
   output. A function that still lints dirty is EXCLUDED with its finding listed (the only exclusion allowed).
4. Re-run the W10c build and certify path (`stage.py build` -> `stage.py certify`) locally, WITHOUT send. The receipt
   records: units prepared vs excluded, presets per unit, certificate sha / inputs_hash, output budget (sum of .o and
   trimmed diff, plus log ceiling, <= 20,971,520).
5. Tests green (the ones your edits touch, plus the W1/W2 gates: send guard, source lint, SEND_CERT_DRILL).
Done-check: a certified, unsent build of the draw with zero lint findings on the included functions, or the exclusion
list; KNOWLEDGE entries; receipt. Zero local compiles, zero GEX44 jobs, JOBS.md untouched.
Receipt: `vault/programs/tennis-rf/WU-W11-receipt.md` (Status line per PROGRAMME.md step 3). K7 row: estimate vs
actual processed tokens (goal ledger delta, every session of this unit).
