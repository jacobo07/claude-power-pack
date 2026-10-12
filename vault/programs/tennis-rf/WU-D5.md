# WU-D5 -- Ph5 knowledge shock sweep (GEX44 cpu, deterministic falsification)

Common brief: `D28-BRIEF.md`. Plan Ph5, MDG 11. Inputs: D4 top-30 dominators, P1P2 hypotheses.json, D2 shock
attribution. Known candidates: helper fn_800B4508 (blocks 89), fn_801CD7D0 (64), cror (67), branch-target (52),
jump-table (37).

Steps:
1. For each top candidate (at most 12, by dominator score): the competing hypotheses the asm admits (field width/
   signedness from load ops, pointer vs scalar from later deref, helper arity/return from callers' use), each as a
   concrete header/prelude delta.
2. Falsify deterministically: apply each delta to a COPY of the context header, rerun m2c + lint on the
   candidate's dependent functions only (20 cores). A hypothesis survives if it raises lint-clean and introduces no
   new lint error elsewhere in the dependents. Record per hypothesis: dependents tested, newly clean, new errors.
3. Survivors only, ranked by unlock: `shock_candidates.json`. Ties or several survivors for one var = CONFLICT
   (kept, not resolved). No model: if a candidate needs semantic judgement, mark it MODEL_NEEDED with why.
4. `test_d5.py` (V-D5-*): every survivor's unlock reproduces; every rejected hypothesis has its falsifying result;
   control: a deliberately wrong delta (e.g. a width that contradicts a load op) is rejected.
Done-check: test_d5 exit 0; top survivors in the receipt; evidence to PP `evidence/d28/d5/`.
Receipt: `WU-D5-receipt.md`.
