# 05-05 SUMMARY -- concurrency, regression, liveness

## Gates (laptop plane)
- `GSDX_FRONTIER_PASS=40/40`, `GSDX_INVALIDATION_PASS=26/26`, `GSDX_JUDGE_PASS=11/11`, `EVB_PASS=21/21` (logs/05-05-*.log)
- Liveness: `gsd_x/goal/replay` and `gsd_x/goal/review` declared PLANNED in vault/liveness/reachability_registry.json
  (same entrance as the rest of the goal engine); `reachability.py` exit 0, 0 gate offenders (logs/05-05-liveness-green.log).

## UNRUN for the coordinator's Linux plane
- `tools/test_gsd_x_goal_mutation.py` (mutates live files, never on the laptop)
- drill d3 (reaped for low memory, not retried)
