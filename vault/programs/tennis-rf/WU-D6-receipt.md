# D6 receipt
Status: DONE
Commits: none in wt_tennis_rf (header unchanged: nothing certified). PP commit below.

## Claims
- NOT_PROVEN / RETRACTED: D5's only survivor `void fn_801D022C(void)`. Callee asm (GEX44 d5 tool dump) does `bl _savegpr_25; mr r25,r3; mr r26,r4; mr r27,r5; mr r28,r6; mr r29,r7`, `bne cr1` + stfd f1-f8 spill = variadic, reads r3..r7. Prototype is asm-false. Provenance + invalidator for the alternative (not certified, nothing unlocks): `void fn_801D022C(void *arg0, s32 arg1..arg4, ...)`.
- Unlock under asm-consistent prototypes: 0 (4 variants on the 43 dependents). Full corpus: lint-clean 276 -> 276, newly clean [], regressions [].
- cror (D5): unlock 0, not a fact. No other D5 SUPPORT. Certified facts: 0.
- Job 4: UNUSED (empty batch), JOBS.md row 4 updated; kept for later.
- Header test green: TENNIS_CONTEXT_DRILL=9/9 (evidence/d28/d6/test_tennis_context.txt), header untouched.
- Bug: entry_evidence prologue-call blindness -> KNOWLEDGE.md D6 entry.

## Commands (GEX44 M/out/d28/d6)
`KSR_DECOMP_TOOLS=/opt/ksr-decomp /opt/ksr-decomp/venv/bin/python -I tools/d6.py variants .` ; `... d6.py full . 3`; test: `gex44/test_tennis_context.py` in M/wt. Evidence copy: PP `evidence/d28/d6/`. Calls ~20, model calls 0.

## Next unit must know
- Single prototype deltas are exhausted at n=12 (D5) and the one SUPPORT was false; frontier needs joint deltas or fixing entry_evidence, then re-running D5 admission.
- D5 HELPER arity verdicts for _savegpr callees are suspect (CONTRADICTION ones were 'unlock 0' regardless, so they stand).

## Plan delta
MDG 12: first frontier collapse = 0 certified facts, 0 direct unlock (276 -> 276 lint-clean of 1,797); D5's 3-fn unlock retracted as asm-false. No compile-verified delta; job 4 unspent.
