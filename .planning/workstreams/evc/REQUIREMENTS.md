# Requirements: evc

Source: `vault/plans/economic-engine-repair-MASTER-PLAN-2026-10-10.md` and the Owner's EVC prompt (2026-10-10).

| ID | Requirement | Phase |
|---|---|---|
| EVC-01 | Live usage truth with freshness watermark; stale spend never shown as current; subagents included | 1 |
| EVC-02 | Three economies: processed, API-equivalent (sourced prices, else UNKNOWN), cognitive composition | 1, 2 |
| EVC-03 | Quota awareness (429 / weekly limit, reset horizon) | 1 |
| EVC-04 | Autopsy + obligation forecast; phase x average only as old-execution reference | 2 |
| EVC-05 | Semantic progress accounting (verified transitions; no-progress spend detector) | 2, 3 |
| EVC-06 | Work-Class profiles, hierarchical resolution, confidence state machine, invalidation, miss taxonomy | 3 |
| EVC-07 | Distributions lower/P50/P80/P95/ceiling, context-growth aware, live reforecast | 4 |
| EVC-08 | Predictive lease edge (DRAINING before hard exhaustion) | 4 |
| EVC-09 | Precise lease states; RELAY_HELD never shown as paused | 5 |
| EVC-10 | Spend capability enforced at the worker's next boundary; breaker = containment | 5 |
| EVC-11 | Durable goal across execution leases; 24 h TTL decoupled; predictive time lease | 6 |
| EVC-12 | Strategy comparison (keep worker / fresh / slim / split / fuse / reuse proof / NO_WORK) | 4, 11 |
| EVC-13 | Fresh-floor cut for packet workers | 7 |
| EVC-14 | Historical backtest with holdout | 8 |
| EVC-15 | Live landing, canary, self-hosting | 9 |
| EVC-16 | KV / UKDL / CBR ratchet, retirements, global default | 10 |
| EVC-17 | Recompiled Clock A + intent/order remaining plan and budget; STOP | 11 |
