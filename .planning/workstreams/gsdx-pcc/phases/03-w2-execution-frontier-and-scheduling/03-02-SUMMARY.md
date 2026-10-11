# 03-02 SUMMARY: measured priors, ordering signals, postures, worker classes

Status: DONE. RED `03-02-red.log` 8/16 (seven gates FAIL "frontier absent", COMPILE-ORDERS FAIL on missing `Frontier.posture`); GREEN `03-02-green.log`.

Gate line: `GSDX_FRONTIER_PASS=16/16  threshold=16/16`. Reconcile suite unchanged and green.

Delivered in `modules/gsd_x/goal/frontier.py`: `duration_prior`, `failure_risk`, `info_gain`, `critical_path`, `order_units` (lexicographic, never a blended score), `posture`/`bound`/`class_bound`, `WORKER_CLASSES`; `Frontier` gains `critical_path, posture, bound, signals`; `compile_frontier` orders by measured signals and keeps legacy order with no history.

Choices: default posture ECONOMY (bound 1) so an undeclared goal behaves as before; `max_parallel` only lowers the bound and invalid values are ignored; LOST/CANCELLED/EXPIRED epochs are not measurements; a zero measured duration gives gain None.

Deviations: none. Note: G17 engine_identity changes (new .py in goal/), recorded in 03-06.
