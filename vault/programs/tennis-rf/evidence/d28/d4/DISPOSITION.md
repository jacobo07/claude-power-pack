# D4 disposition: PARTIAL / INCONCLUSIVE, accepted with a certified limitation

Owner decision, 2026-10-13 (D28 coordinator pane). The receipt `WU-D4-receipt.md` is left exactly as the worker
wrote it: `Status: PARTIAL`, `test_d4.py` exit 1 on `V-D4-RED-FALLS`. That red is evidence, not debt: it is
never to be made green by weakening the gate. The chain closes D4 with `accept: ["DONE", "PARTIAL"]` so D5 can
arm; it does NOT read as DONE or PASS.

## Certified (what D4 proved)
- The frontier is reproducible: 3,429 unresolved vars over 1,521 non-clean fns; reruns give equal sha256
  (`V-D4-REPRO` PASS).
- 29 of the top 30 dominators are HELPER prototypes, deterministically fillable (cost 1-2).
- `M2C:unknown instruction cror` is the proven sole blocker of 51 functions (67 in total).

## Not certified (what D4 did not prove)
- The remaining dominator ranking is NOT validated as causal structure. Those are candidates ranked by degree,
  not proven semantic or causal dominators. Each HELPER's low bound is 0 (every function also has its own
  per-function blockers), so no prototype's unlock is proven alone.

## Why the control could not decide
The direct-count score is a degree count. The red control shuffled while preserving degree, so it preserved
exactly the statistic the score is computed from: it could not have fallen. Transitive-only control: real 6.67
against shuffled mean 6.19, max 8.63. The control is non-discriminating; the claim it was meant to test stays
untested, neither confirmed nor refuted.

## What follows
- D4 did not prove semantic dominators.
- D4 showed that its degree-preserving red control has no discriminative value.
- D4 produced a reproducible candidate frontier.
- D4 proved one concrete blocker, `cror`, with a 51-function causal scope.
- D5 tests causal unlock, not structural rank (constraint in `WU-D5.md`).

Not spent: both D4 residuals (`m-13e710106e99` halted after ~144k with the hold kept; `m-f3fa70353c8e` halted
before launch). A control with unlock semantics would be a new instrument with its own contract, opened only if
its expected information value exceeds what D5 gives.
