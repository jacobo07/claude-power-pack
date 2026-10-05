# Gen3 T2 -- InfinityOps odr-device-trust Phase 4 canary (2026-10-05)

Unit: processed tokens (input + cache_write + cache_read + output, deduped by message id). Measured externally from each
transcript (`t2_agents` logic; pane via `stage0/self_spend.py`), not from the agents' self-reports.
Worktree `C:\Users\User\Apps\io-odr-p4-canary`, branch `canary/odr-p4-packets` (from f2e1f560). Not pushed, not merged, not deployed.

## Spend -- 44.25M total, OVER the Owner-raised 42M cap by 2.25M
| step | commit | model | processed (measured) | self-reported | cap |
|---|---|---|---|---|---|
| compiler (obligations + packets + coverage) = c | 69c87616 | Sonnet | 6,178,832 | 5.62M | 5M (over) |
| E1 PK-01 nginx block + vhost test + spec | f320bd90 | Sonnet | 4,567,994 | 4.39M | 5M |
| E2 PK-02 mint client + PK-04 probe | afdc7e8e, 45a80a6b | Sonnet | 8,718,084 | 8.49M | 6M (over) |
| E3 PK-03 founder-only page/action/nav | 4443aaf3 | Sonnet | 6,168,758 | ~6.0M | 9M |
| E4 PK-05 CI + deploy probe step + wiring test | 312e0db5 | Sonnet | 6,920,521 | 5.2M | 4M (over) |
| GEN-20 independent review | -- | Opus | 2,366,399 | -- | ~25 calls |
| parent orchestration (this Opus pane, ~330k/call) | -- | Opus | ~9.33M | -- | -- |
Agents self-meter late or low (3 of 5 over cap, E4 under-reported by 1.7M): a prompt instruction is not a breaker.

## Result vs champion (scope-normalized as far as evidence allows)
- Champion = the old grammar's Phase 4 remainder estimate 54-100M, central ~70M (plans x average; an ESTIMATE, not a run).
  Phases 1-3 measured 116.5M / 127.4M / 89.1M. Candidate = 44.25M for the whole remaining Phase 4 up to the deploy boundary.
- c (planner + plan-checker replaced by compilation) = 6.18M vs historical planner 14.6M/run + checker.
- Verdict: **PARTIAL WIN / NEW BOTTLENECK.** ~37% below the champion's central estimate, but the champion was not run, so
  the saving is not causally measured. New bottleneck = parent orchestration in a long Opus pane (9.3M, 21%) and
  ~190k cache-read per worker call.

## Scope ledger (04-OBLIGATIONS.md, 329 obligations, coverage 329/329 + red control)
- Closed with proof on the LOCAL plane: PK-01..PK-05 claimed sets (vitest 80/0, ExUnit 154/0 + 47/0, probe selftest 18/18,
  tsc 0; drills M47-M65 red then hash-restored green). Review GEN-20: APPROVE, 0 C/H/M, 1 LOW.
- OPEN, not dropped: 4 OWNER-GATED (prod deploy/wss, live vhost + prod probe, D-09 digest attestation, certbot);
  2 CONDITIONAL; eslint unrunnable (no eslint.config, pre-existing on base); CAP-08/13/14/20 source-scan only (no rendered/jsdom);
  CI steps not observed in CI; no real nginx -t / websocket upgrade through nginx; LOW: holdings-client.server.ts maps every
  409 to too_many_pending without reading body.error (fix: match too_many_pending_codes, else unavailable, + red case).

## Lessons (candidates)
- Trap: check_coverage.py regenerates 04-COVERAGE.md and erases the recorded green/red run evidence when re-run.
- Trap: agent-solo guard tracker is estate-wide; another pane's Explore blocked this pane twice (KNOWN_FALSE_POSITIVES).
- Process: agent spend caps need an external breaker (mission_spend-style), not prompt self-metering.
- Process: orchestrate from a fresh short-lived pane; a long Opus parent cost more than any single executor.