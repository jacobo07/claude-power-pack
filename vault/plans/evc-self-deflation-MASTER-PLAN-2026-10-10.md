# EVC self-deflation — master plan, 2026-10-10

Status: AWAITING OWNER APPROVAL. This file backs up the inline plan; the chat is where approval happens. It amends
`economic-engine-repair-MASTER-PLAN-2026-10-10.md` (88af526e) and the GSD workstream `evc` (pp-evc 9ad50f2c).
Nothing was mutated to produce it: no worker was stopped, no branch landed, no budget changed.

## Reality delta (measured, read-only, 2026-10-10 ~11:15-11:30 UTC)

- EVC mission m-d9f1ff05dfb0: BLOCKED. Worker 65aa58ea (pid 27228, alive) is waiting on a host permission prompt
  ("Entering worktree"). /gsd-autonomous called EnterWorktree at 11:03:40 although cwd was already the pp-evc
  worktree. It has spent 1,041,933 processed tokens in 7 calls (~149k per call; fresh floor 126.7k). No commits after
  9ad50f2c. Programme frontier ~0 %, so a full recompile costs only the 1.04M already sunk.
- Breaker authority conflict: the enforced limit is `mission_spend.judge` = 2.0 x token_estimate = 2 x 85M = 170M.
  The ROADMAP "hard stop 160M" is prose that no code enforces.
- Several units already exist, but outside live PP HEAD 88af526e:
  | Unit | Existing work | Where | Landed? |
  |---|---|---|---|
  | U1 price table | `tools/usage_index.py` prices every usage category per model | live HEAD | yes |
  | U2 autopsy + forecast | cost-collapse T2 2b5b0ea5 (T1 f3b503e6) | `cost-collapse/main`, `Apps/pp-cost-collapse` | no |
  | U3 claim-graph estimator | `tools/cost_to_completion.py` (150 lines, profiles, actuals, worker_floor, deopt) | live HEAD | yes |
  | U4 live reforecast | `tools/gsdx_reforecast.py` + test, 610808c5 (129 lines) | `gsdx-factory/v2` only (75 commits, 57k lines ahead; cherry-pick, do not merge) | no |
  | U5 spend stop | `hooks/session_budget_guard.js` deny budgets (drilled) | live HEAD | yes |
  | U6 lease epochs | dgl W1b V-gates c5f22af9, W2 closed-lease fence 31f9b5f4 in `hooks/lib/goal_binding.js` | `dgl/durable-goal-lease`, `Apps/pp-dgl` (19 commits, 9 code files) | no; `lease_epoch` has 0 hits in HEAD |
  | old-worker settle | `tools/mission_steward.py` R1-R3 | live HEAD | yes |
- Containment (U0) holds: deny budgets `stop: 1` exist for ec66dcff (intent/order, pid 39668 alive, 32.0M
  counted) and e0cd1dbb (Clock A, pid 13156 gone, 13.0M counted). Both state files were updated at 12:52 local.
- Fresh-floor contributors: `~/.claude/CLAUDE.md` 39,812 chars / 292 lines (its own rule says <100 lines; the 39.8K
  warning). TUA-X MEMORY.md 23,089 chars, close to the 24.4 KB read limit. PP `CLAUDE.md` 40,774 chars.

## Obligation ledger (disposition, processed-token price)

| Unit | Disposition | Price |
|---|---|---|
| U0 containment | DONE, verified above | 0 |
| U1 usage truth | SHRINK: price table exists. Remaining work: a freshness watermark and a stale-snapshot guard in the hold/status text | 3M |
| U2 autopsy/forecast | LAND cost-collapse T1+T2 by cherry-pick + its tests | 2M |
| U3 profiles/confidence | SHRINK: make `cost_to_completion` the primary estimator, remove the [1M,15M] clamp, add the confidence states | 4M |
| U4 distributions + reforecast | LAND 610808c5 alone, then add P50/P80/P95 output | 4M |
| U5 spend capability | SHRINK: hold/suspend writes the guard budget for the live worker, plus a canary drill | 4M |
| U6 TTL / epochs | LAND dgl W1b+W2 only (D15 stays parked for W3-W8) | 4M |
| U7 fresh-floor cut | KEEP, the largest lever. Includes an Owner-gated proposal to bring the global CLAUDE.md under its own 100-line rule (about 8k tokens per call, on every session) | 8M |
| U8 backtest | SHRINK to 2 traces (old Clock A, intent/order) plus 1 holdout | 4M |
| U9 canary / self-forecast | MERGE into U11 | 2M |
| U10 ratchet / retirements | SHRINK to KV/UKDL entries. Global no-opt-in defaults are DEFERRED to backlog | 2M |
| U11 recompile residuals | KEEP, then STOP (boundary 2) | 4M |
| Coordinator (≤20 %) | | included in the reserves below |

## Execution fixes (before relaunch)
1. Settle the blocked worker 65aa58ea through `mission_steward` (frontier ~0, nothing to salvage), then end it. Only
   after that, relaunch with one writer in pp-evc and **no EnterWorktree** (cwd is already the worktree;
   `--force-isolation none`).
2. One breaker authority: declare token_estimate = 32.5M so that the enforced 2.0x trip equals the plan's hard stop
   of 65M. Delete the 160M prose line from the ROADMAP in the same commit.

## Token budget (processed tokens)
Sunk 1.04M (the blocked worker; no output). Semantic lower bound 28M (land 3 branches + wire + verify).
**P50 41M · P80 52M · P95 62M · hard stop 65M (enforced).** The previous plan was P50 85M / prose 160M / enforced
170M: −52 % at P50 and −62 % at the enforced stop. Confidence EXPLORATORY until U8.
Not authorized: product execution of Clock A or intent/order beyond containment, and a second EVC writer.
