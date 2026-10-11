# 03-01 Summary: frontier core

Status: complete. Suite `tools/test_gsd_x_goal_frontier.py` RED (1/8, `03-01-red.log`) then GREEN (see `03-01-green.log`, last line `GSDX_FRONTIER_PASS=8/8  threshold=8/8`). Reconcile suite unchanged: `GSDX_RECONCILE_PASS=22/22`.

Delivered: `modules/gsd_x/goal/frontier.py` (`frontier_enabled`, `gate_unit`, `independent_units` = `proof.independent`, `stored_unit`, `Frontier`, `compile_frontier`).

Deviations from the plan, all recorded:
- `proof.switch_on` is generic (proof.py:57), so `frontier_enabled` reuses it instead of a private token table (the plan-check warning assumed otherwise).
- An empty gate class on a non-reality plane is treated as `unit`, because that is what the sweep dispatches (sweep.py:365); CONTEXT D07 said undeclared. A REALITY obligation with no runtime class, or an unknown class, stays undeclared. The log itself refuses both at accept time, so those rows are built with `dataclasses.replace` in the gates.
- `reads` always includes the gate pin files; `tree:*` is added when the contract declares no causal paths.