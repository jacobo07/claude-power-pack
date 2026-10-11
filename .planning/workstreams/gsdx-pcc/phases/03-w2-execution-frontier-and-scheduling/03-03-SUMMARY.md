# 03-03 SUMMARY: decide becomes the first action of the compiled frontier

Status: DONE. RED `03-03-red.log` 18/26 (GLOBAL-WAIT, HARVEST-NOT-HIDDEN, NO-STARVE, STOP/BUDGET/BLOCKED-ON-HOLDS controls, WAIT-ONLY-EMPTY, LEGACY-EQUAL FAIL against the legacy-only `decide`; captured by temporarily restoring HEAD reconcile.py, then restoring the change). GREEN `03-03-green.log`.

Gate line: `GSDX_FRONTIER_PASS=26/26  threshold=26/26`. `GSDX_RECONCILE_PASS=22/22`.

Delivered: `reconcile.decide` is a wrapper; the old body is `_decide_legacy` (`git diff -w` shows additions only, no removed line). `frontier.decide_frontier(ctx, legacy)`: only a legacy WAIT is ever replaced; an ended sibling is harvested first; a new gate starts only if open < bound, every open epoch carries a stored unit, stop/closure/blocked_on/budget would not have stopped legacy, and the unit is independent of all open ones. Default posture (bound 1) is legacy by construction.

Evidence: V-FRONTIER-LEGACY-EQUAL compared 177 contexts (switch off and on) incl. every log prefix of both Phase 2 corpus goals (50 + 123), 0 differences.

Deviations: fixtures append DISPATCHING/RUNNING directly with the unit in the spec, because `epoch.begin` refuses a second open epoch until 03-04. Gate closure-holds passes against the old code too (legacy WAIT is already correct there); it is a hold, not a RED.
