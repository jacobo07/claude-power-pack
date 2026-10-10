# Economic engine repair (EVC) — master plan, 2026-10-10

Status: APPROVED as amended by `evc-self-deflation-MASTER-PLAN-2026-10-10.md` (P50 41M, enforced stop 65M, which
replaces the budget below; Owner reconfirmed 2026-10-10 evening). Backup of the inline plan; the chat is the approval surface.
Adopts backlog D22 (`vault/plans/deferred-backlog.md` §D22 cost-collapse / expected-completion; was D12 before the renumbering) and the `dgl` lease-epoch work;
creates no parallel engine.

## Reality delta (measured 2026-10-10 10:41 UTC from transcripts, deduped by message id, subagents included)

| Worker | Mission | Processed | Calls (main/sub) | Cache read | Output | In subagents | Mean ctx/call | Last model call | State |
|---|---|---|---|---|---|---|---|---|---|
| ec66dcff (pid 39668 alive) | intent/order m-cd548e5d2ada | 371.0M | 174/2,120 | 94.6 % | 0.9 % | 91 % | 160k | 06:25 UTC, HTTP 429 "weekly limit, resets Oct 13 4am Madrid" | hold set; worker alive, idle |
| e0cd1dbb (pid 13156 alive) | Clock A m-5709490db84c | 58.4M | 79/308 | 93.3 % | 1.0 % | 78 % | 149k | ~10:03 UTC | BLOCKED on founder items (Phase 10 done: bac6b195e) |
| be97307b | Clock A old m-f24648f187c5 (HALTED) | 245.8M | 236/1,311 | 93.1 % | 1.1 % | 83 % | 157k | 01:33 UTC | idle session |
Ledger figures match within 1 % (57.9M, 243.5M, 368.0M). Fresh context floor per call ~115k.

## Root causes (evidence)
1. Estimator clamp: auto envelope = (spent + headroom clamped to [1M, 15M]) / 2 (`mission-budget-defaults.json`): it cannot forecast above ~8M. Order-of-magnitude miss by construction.
2. Stale snapshot: the hold message froze 18.2M at trip time; the worker continued to 371M (20x). STALE_USAGE_PRESENTED_AS_CURRENT.
3. Hold blocks relay only: `session_budget_guard.js` (PreToolUse, Bash/Edit/Read/Agent) is opt-in per session file; mission workers never get one. PAUSE_DOES_NOT_STOP_SPEND. Only a provider 429 stopped intent/order.
4. Cost driver = calls x floor, not growth: 2,294 calls x ~160k; context flat across the session (autocompact 250k); 91 % inside GSD subagents each re-paying a ~115k floor.
5. 40M (pane error): used the stale 18M snapshot as current and a phase rate.
6. 24 h: `gsd_long_run.DEFAULT_MAX_HOURS = 24`, judged from mission `created_at` at relay (`gsd_mission.budget_exhausted`): couples process age to the semantic goal.
7. No price table anywhere in PP: monetary view UNKNOWN.
8. Quota: weekly limit hit on one Sonnet worker at 06:25; another Sonnet worker ran 06:51-10:03 without 429. Current quota UNKNOWN.

## Units (execution order; each a packet worker, fresh, scoped)
U0 containment: write deny budgets for both worker sids (guard), mark states RELAY_HELD truthfully, retire idle sessions only after proof of no in-flight call.
U1 usage truth: freshness watermark + stale-snapshot guard in hold/status text; usage categories; sourced price table (three economies).
U2 = cost-collapse T2: `mission_spend autopsy` + obligation forecast (units x calls x (floor + context image) x (1+repair)).
U3 work-class profiles + confidence state machine (UNKNOWN..INVALIDATED) + miss taxonomy + order-of-magnitude invalidation; remove the [1M,15M] clamp as primary estimator.
U4 distributions (lower/P50/P80/P95/ceiling) + live reforecast (E3C2 EAC usage wiring) + predictive lease edge (DRAINING before exhaustion).
U5 spend capability: hold/suspend writes the guard budget for the live worker (next tool boundary refused); breaker becomes containment fallback; canary drill.
U6 TTL: lease epochs (dgl GoalLedger) — relay past 24 h continues the same goal in a new epoch; predictive time-lease rotation.
U7 = cost-collapse T4: fresh-floor breakdown and cut for packet workers (largest saving lever).
U8 backtest: replay Clock A old/new, intent/order, DWS, recon-factory, gsdx-pcc traces; bias/coverage/miss class; one holdout class.
U9 live canary + self-hosting: the engine forecasts its own remaining units.
U10 KV / UKDL / CBR ratchet + retirements; global defaults with no opt-in.
U11 recompile Clock A + intent/order residual bottom-up; final plan + budget; STOP (boundary 2).

## Token budget (processed tokens; monetary after U1)
Engine lower 55M · P50 85M · P80 110M · P95 140M · hard stop 160M. Coordinator share cap 20 %. Confidence EXPLORATORY.
Includes: backtest 4-8M, canary 4-8M, proof reserve 10M, migration reserve 8M, final recompilation 4-8M.
Not authorized: any product execution of Clock A or intent/order beyond containment.
Supersedes the D12 cost-collapse goal cap (69.8M declared, 8.0M left): approval = the pending D-C cap decision.
