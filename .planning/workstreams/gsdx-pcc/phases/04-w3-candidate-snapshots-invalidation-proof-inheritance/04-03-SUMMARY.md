# 04-03 SUMMARY -- proof inheritance and invalidation

Plane: Windows laptop (local), hermetic temp roots.

## Delivered
- `modules/gsd_x/goal/inherit.py` (new): observe -> plan -> apply in the sweep; `inherited_ids` is a pure log projection.
  Eligible classes: DETERMINISTIC, COMPOSITIONAL, ENVIRONMENT_SENSITIVE. REALITY plane, legacy contracts, nondeterministic
  elements, TEMPORAL / FRESH_REQUIRED / UNKNOWN are never inherited.
- `convergence.goal_closure(..., inherited=frozenset())`: a SATISFIED claim with an agreeing `proof.inherited` event no longer
  needs `tree_equal`.
- `reconcile.inherited_for(ctx)`, `frontier` (4 call sites) and `sweep.sweep_goal` (plan/apply block) consume it.
- `tools/test_gsd_x_goal_invalidation.py`: 19 gates (was 10).

## Gates observed
- Invalidation suite green (log `logs/04-03-run1.log`); replay 28/28, semantics 48/48, certificate, reconcile, convergence, sweep green.
- Frontier suite 40/40: 36 in `04-03-frontier-fast.log`, 4 slow in `04-03-frontier-slow1.log` / `slow2.log`.
- `git diff --stat -- modules/gsd_x/goal/judge.py` empty: closure remains necessary-not-sufficient.

## Deviations
- `Context` cannot gain fields (V-PCC-DECIDE-SIG), so the inherited set is derived from the log via `inherited_for(ctx)`.
- Frontier slow gates run in bounded groups (host load), not one chained call.

## Open
- `candidate.py` still unwired from `sweep.py`; 04-04/04-05 wire it or declare it for liveness.
