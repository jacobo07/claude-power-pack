# EVC relaunch by packet units — proposal, 2026-10-10 (awaiting Owner approval)

## Why
Epoch 2 (m-79dbb97c5017, session 968dfb18) ran /gsd-autonomous: 31.80M processed in 197 calls, cache read 94 %, max ctx
218k, and produced only Phase 1 research + 3 plans (1,093 lines, 4be2ea2d). The Phase 1 disposition was 3M. The GSD
research/plan/verify ritual, at ~160k context per call, is the cost driver, not the work. Stopped by Owner ("sí"):
hold + deny budget + `claude stop`.

Sunk EVC total: 2.64M (epoch 1) + 31.80M (epoch 2) = **34.44M**.

## Mechanism
One mission per work unit via `gsd_mission arm-chain --wu-packet <WU.md> --route <ROUTE.json> --token-estimate <E>`.
`route_admission` must say ADMISSIBLE (calls x (profile floor + packet)) or nothing launches. The worker receives the
packet, not /gsd-autonomous: no researcher/planner/verifier subagents. cwd = `.claude/worktrees/evc` (evc/e2), with the
worktree's `.claude/settings.local.json` MCP-disabled.

## Wave 1 — land what already exists (measure actuals before wave 2)
| WU | Content | Calls cap | Envelope |
|---|---|---|---|
| WU-1 | cherry-pick cost-collapse T1+T2 (f3b503e6, 2b5b0ea5) + their tests green | 15 | 2.5M |
| WU-2 | cherry-pick 610808c5 (gsdx_reforecast + test) alone | 8 | 1.5M |
| WU-3 | cherry-pick dgl W1b+W2 (c5f22af9 .. 31f9b5f4) + test_workspace_lease green | 15 | 2.5M |
| WU-4 | Phase 1 core only: the stale-snapshot guard + freshness watermark in hold/status text (from 01-0x-PLAN.md), gate red/green | 20 | 3M |
Wave 1 total ≤ 9.5M, run sequentially (one writer).

## Then
Reforecast phases 3-11 from wave-1 actuals (per-call floor, calls per unit). The remaining dispositions are ~38M at
P50, so the programme total is ~72M against the 65M stop: the Owner decides at that boundary whether to raise the
stop or move Phases 7/8/10 to backlog.
