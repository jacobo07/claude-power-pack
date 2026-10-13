# WU-D5 -- Ph5 causal unlock sweep (GEX44 cpu, deterministic intervention + falsification)

Common brief: `D28-BRIEF.md`. Plan Ph5, MDG 11. Inputs: D4 frontier.json / dominators.json, P1P2 hypotheses.json,
D2 shock attribution, D3 residuals.jsonl. Read `evidence/d28/d4/DISPOSITION.md` first.

Constraint (Owner, 2026-10-13): D4's candidate ranking is degree-driven and non-causal until independently
falsified or validated. D5 must not inherit rank as truth. Position in D4's top 30 grants no authority: D5 must
be able to find that a lower-degree candidate unlocks more, or that a top candidate unlocks nothing.

Each candidate goes through one causal chain, the same for all:
candidate unknown / blocker -> intervention (a concrete resolution delta) -> incremental re-evaluation (m2c + lint on
its dependent functions only, 20 cores) -> measured unlock (newly lint-clean fns, new errors anywhere in the
dependents) -> verdict SUPPORT (unlock > 0, no new errors) / CONTRADICTION (unlock 0 or new errors) / ABSTAIN (the
intervention cannot be stated without semantic judgement: MODEL_NEEDED with why; no model is called).

Steps:
1. `cror` FIRST, as its own experiment: it is D4's one proven sole blocker (51 fns sole, 67 total). Resolve it
   tool-side (an asm-preprocessing rewrite or m2c handling that is semantics-preserving; state which), rerun the 67
   dependents, measure the real unlock, and propagate it incrementally (functions whose only remaining blocker
   becomes a now-clean callee are rerun once; record that second wave separately). `cror_unlock.json`.
2. Candidate draw, NOT by rank: 11 more candidates = 6 from D4's top 30 + 5 from below it, drawn by a recorded
   seed, stratified by degree (blocked_direct quartiles). Record each candidate's D4 degree and rank beside it.
3. Per candidate: the competing hypotheses the asm admits (field width/signedness from load ops, pointer vs scalar
   from later deref, helper arity/return from callers' use), each as a concrete header/prelude delta applied to a
   COPY of the context header, run through the causal chain above. Several surviving hypotheses for one var =
   CONFLICT (kept, not resolved).
4. `causal_unlock.json`: per candidate, verdict and measured unlock. Report the rank correlation (Spearman) between
   D4 degree and measured unlock with its n, as evidence about whether degree ranking has causal value; do not
   claim either way past what n supports.
5. `test_d5.py` (V-D5-*): every SUPPORT reproduces on rerun; every CONTRADICTION has its falsifying result; the
   draw reproduces from the seed; control: a deliberately wrong delta (a width that contradicts a load op) is
   rejected; second control: a no-op delta yields unlock 0.
Done-check: test_d5 exit 0; cror's measured unlock and the per-candidate verdicts in the receipt; evidence to PP
`evidence/d28/d5/`. Receipt: `WU-D5-receipt.md`.
