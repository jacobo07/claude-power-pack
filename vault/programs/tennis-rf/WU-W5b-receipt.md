# W5b receipt
Status: DONE

Slice done: step 1 (6 hard fns, >=3 unresolved types) and step 5 (claims.jsonl read by transform). Steps 2-4 NOT run; stop-loss (plan 7) triggered. Zero GEX44 jobs, zero compiles, JOBS.md untouched, no code in wt_tennis_rf.
Commits: PP only (evidence/w5b/*, measure/claims.jsonl, this receipt).

- PROVEN: hard pool in W3 sample60 is only 12 L1 fns with ut>=3; 6 drawn (seed 20261012, stratified by insns). `python -I evidence/w5b/w5b_transform.py`: unresolved `?` 13,6,8,12,5,20 -> 8,1,6,12,5,15. 7 prototypes learned (call-site inference), written to measure/claims.jsonl; the transform loads `proto <fn>` rows from it (second run reproduces the same output, 7 claims, reads them first).
- PROVEN: no function fully closed model-free (0 of 6 reach 0 `?`; 3 of 6 abstain on unresolved callees, unk fields 0-67 remain).
- NOT_PROVEN: any verdict (no Tennis oracle, W3b refusal; no tennis-capsule unit exists), that inferred void/s32 prototypes match asm.
- UNKNOWN: sequence curve (member -> new-cognition tokens): not run, no model members executed, no session-token measurement. Holdouts (tooling, Haiku routing): skipped, they need a verdict oracle to judge.
- Stop-loss finding: W5a + these 6 = 0 verified, 0 model-free closures => Tennis A/B cost can only be reported on oracle-less layers; compile-verified rates UNKNOWN until a tennis capsule (W3b option a, >1 unit) is built.
- Next unit must know: transform gains are prototype arity only; SDK-header/struct resolution (unk fields) is the missing deterministic layer. Calls ~7.
