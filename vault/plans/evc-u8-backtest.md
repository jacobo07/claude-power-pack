# EVC U8 backtest (WU-S5b)

Verdict: **NOT_PROVEN** for P50/P80/P95 coverage, bias and miss class. Reason: the estimator input (a claim graph:
`compile_cost` refuses anything else) does not exist for any of the three traces. No claim graph file was found under the
TUA-X brand001 worktrees (clock-a, intent-order) or in this repo. Reconstructing one after the fact from the transcript
would fit the answer to the outcome, so it was not done. A missing input is NOT_PROVEN, never zero.

## Observed actuals (PROVEN, measured from the transcripts)
Sum of usage (input + cache_creation + cache_read + output), de-duplicated by message id, main jsonl + all subagent jsonl.
| trace | role | measured | stated in packet |
|---|---|---|---|
| be97307b | old Clock A | 243.5M (main 42.8M + 37-file tree 200.7M) | 245.8M |
| ec66dcff | intent/order | 368.0M (main 32.0M + 28-file tree 336.0M) | 371.0M |
| e0cd1dbb | holdout, Clock A new | 57.9M (main 13.0M + 10-file tree 44.9M) | 58.4M |
Measured is about 1% below the stated figure in all three (same method gap), so the actuals are usable as `observed`.

## What the estimator would need (arithmetic only, not a coverage claim)
Priors: novel = 15 calls x 140k = 2.1M per claim (P50), ceiling 3x = 6.3M. To reach the actuals at P50 alone the graph
would need about 116 (be97307b), 175 (ec66dcff), 28 (e0cd1dbb) novel claims. Whether the old planning graphs had that many
is unknown; that unknown IS the gap.

## Next step to prove it
Record a claim graph at arm time (now possible: `claim_graph` path on the mission record, see
`gsd_mission.claim_cost_for`); the backtest then runs on the next mission whose graph predates its spend.
Until a graph precedes a spend there is nothing to cover. INVALIDATED (observed > ceiling) is the only miss class the
code can emit today; it needs `observed` set to the actual at close.
