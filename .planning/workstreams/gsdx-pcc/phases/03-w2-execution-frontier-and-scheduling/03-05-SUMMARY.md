# 03-05 SUMMARY -- speculation admission and yield ledger (D25, D26)

Status: done. Admission is decided and reported; nothing speculative is executed.

## Delivered
- `frontier.admit_speculative(unit, ctx)`: UNDECLARED, WRITES_OUTSIDE_RUN_DIR, SHARED_RESOURCE, NOT_UNIT_CLASS,
  UNKNOWN_COST, NOT_WORTH_IT, else ADMITTED (saving > cost, both from the goal's own measured runs).
- `frontier.admit_race(candidates)`: TOO_FEW, UNDECLARED, SAME_ROOT, CONTRACT_MISMATCH, NOT_REVERSIBLE, else ADMITTED.
  Cancelling a loser uses the existing CANCELLED outcome.
- `frontier.yield_ledger(state)`: per mode (speculative, race) completed / cancelled / failed / other / total.
- `sweep._speculation_report`: after the dispatch pass, only when the posture bound is above 1 and the switch is on,
  one line per gate still waiting ("speculative <ob>: admitted|refused -- <reason>") plus a yield line.
  Default (ECONOMY) output is unchanged.

## Evidence
- RED: `03-05-red.log` -- five new gates fail "RED-first: ... absent"; `GSDX_FRONTIER_PASS=34/39`.
- GREEN: `03-05-green.log` -- `GSDX_FRONTIER_PASS=39/39  threshold=39/39`.
- Regression (`03-05-regress.log`): reconcile 22/22, sweep 14/14, sweep_all 11/11, epoch 19/19, engine_identity 14/14.

## Open (carried to Phase 4)
Executed speculation and executed racing remain open: no speculative or race epoch is started anywhere.
V-FRONTIER-REPORTED-NOT-EXECUTED pins that. The yield ledger reads zeros until something executes.
