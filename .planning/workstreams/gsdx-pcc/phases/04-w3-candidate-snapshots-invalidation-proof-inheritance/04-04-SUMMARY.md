# 04-04 SUMMARY -- algebra, minimal verification set, fresh islands, drift substrate

Plane: Windows laptop (local), hermetic temp roots.

## Delivered
- `proof.combine_states(op, states, k)`: AND / OR / SEQ / QUORUM(k) over FRESH / INHERITED / STALE / UNKNOWN. Only FRESH and
  INHERITED satisfy; changed (STALE, SUPERSEDED) outranks unknown; empty list, unknown operator or bad k is UNKNOWN.
- `inherit.verification_set(state, root, candidate, now)` -> `{run, inherit, fresh, islands, full, reasons}`. One source of
  truth with `inherited_ids` (no second scheduler). A skip needs evidence (FRESH verdict, or an agreeing `proof.inherited`
  event); a planned but unrecorded inheritance is still in `run`. `full` is true when a premise or the candidate is unknown.
- `inherit.fresh_islands(state)`: FRESH_REQUIRED (includes risk-tagged) and REALITY-plane claims.
- `inherit.promoted_drift(state, current_oid)`: newest `candidate.promoted` vs the current tree; None on no event or unknown.
  `inherit.py` imports `candidate.py`, so the candidate module is now reachable from `sweep.py`.
- `sweep_goal` appends one `verification set run=... inherit=... fresh=... islands=... full=...` line, only on a sweep that
  recorded inheritance/invalidation events (a quiet sweep stays quiet, so drain loops are unaffected).
- Task 1 confirmed: `frontier._runnable_gate_obligations` reaches inheritance through `rc.inherited_for(ctx)` -> `inherited_ids`.

## Gates observed (log files under `logs/04-04-*`)
- `GSDX_INVALIDATION_PASS=26/26` (7 new: ALGEBRA-TRUTH, NONAND-RUNS-FULL, VSET-SKIPS-ONLY-WITH-EVIDENCE, VSET-UNKNOWN-FULL,
  FRESH-ISLANDS, VSET-NO-OVERLAP, DRIFT-SUBSTRATE). RED first: `04-04-red.log` = 19/26, the 7 new failing on absent code.
- `GSDX_PCC_REPLAY_PASS=28/28`; frontier 40/40 (36 fast + 4 slow, `04-04-frontier-*.log`).
- SWEEP-E2E strengthened to require the report line.

## Dispositions
- D11 PARTIAL (minimal verification set computed and reported; the sweep still dispatches per claim through the frontier).
- D24 OPEN (substrate only: drift + moved-under-verification; the watcher is Phase 9).

## Deviations
- The `Inh` fixture gained a `combine` knob popped from the element dict (so non-AND contracts can be built).
- Report line emitted only when events were recorded, to keep idempotent sweeps silent.
