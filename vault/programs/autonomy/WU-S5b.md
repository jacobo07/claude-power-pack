# WU-S5b -- Autonomy Convergence unit S5b (continuation of S5)

Read `vault/programs/autonomy/PROGRAMME.md` first. Done already (do not redo): 17a5029c U3/U4, 647514fb U1/U4,
944ed790 U5; U7 proposal `vault/plans/evc-u7-fresh-floor-OWNER-PROPOSAL.md`; notes `vault/plans/WU-S5-progress.md`.

## Do
1. EVC U8 backtest: traces be97307b (old Clock A, 245.8M) and ec66dcff (intent/order, 371.0M) + holdout e0cd1dbb
   (Clock A new, 58.4M) against the new estimator (compile_cost / cost_to_completion with observed=actual): P50/P80/P95
   coverage, bias, miss class. A missing transcript = NOT_PROVEN, never zero. Output `vault/plans/evc-u8-backtest.md`.
2. Populate `claim_cost` where a unit's claim graph exists (or record exactly why nothing can populate it yet).
3. If budget remains: wire U1's watermark where it is not vacuous (a stale snapshot shown to a human: hold/status
   text), else record NOT_PROVEN with the reason.
Close by call 22 at the latest (see PROGRAMME.md reserve rule). Receipt: `vault/programs/autonomy/WU-S5b-receipt.md`.
