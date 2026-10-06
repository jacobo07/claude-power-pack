---
covers: [orca-p4-canary, compiled-execution, planner-extinction, proof-of-non-work, model-boundary-budget, p4-reforecast]
status: APPROVED (Owner "y" 2026-10-06, covers S0 hold, S1 GEX44 deploy, 75M canary cap); S0 DONE (GEX44 seq 9, plan at 05:01Z = none)
parent: vault/specs/goal-governed-mission-control.md; vault/specs/mission-envelope-and-compiled-wu.md; gen2/evidence/gen3_t2/README.md (T2 canary)
---

# Orca X P4 as a compiled-execution canary (challenger to the ~664M forecast)

## Verified reality (2026-10-06T20:07Z, GEX44)
- m-eaf2843afb16: PREPARED, epoch 0, no owner, no worker; quota hold until 2026-10-07T05:00Z. Live install 4db97ab0.
  Envelope: token_estimate 135,000,000, autocompact 160k, continue_max_tokens 160,000, note + CE directive (seq 7).
- Closure HEAD 963c53977 (1 dirty). 04-CONTEXT.md (37,890 B) written AT 963c53977: reality delta for P4 = 0.
  It holds a file:line exists/missing scan per criterion, D-01..D-08 (D-08 = proposed plan split), a real-app
  proof plan per criterion, Windows-lane rows and Owner-reserved items.
- GEX44 supervisor only CARRIES wu_packet on renewal; the launch path that sends a packet (spec
  mission-envelope-and-compiled-wu, c3) exists only on the laptop branch.

## Economic semantics (one interpretation)
- token_estimate = per-ATTEMPT envelope, metered from the record's created_at (mission_spend); trip at
  token_trip_ratio x estimate (default 2.0 -> 270M) parks the attempt under an Owner hold (never a kill).
- Budget clock = created_at + max_hours (48 h) -> halt + renewal at 2026-10-07T18:12Z; the renewal is a NEW
  record whose meter restarts at 0 and carries the estimate (C1). So no lineage-level cap exists.
- ~664M = a forecast for P4-P9 (pane-written), enforced nowhere. Mismatch: the directive calls 135M "Phase 4"
  while the attempt can roll into P5 before tripping, and renewals reset the meter.
- Canary resolution: the attempt's scope IS P4 (packet scope), estimate and trip are P4's, and the attempt ends
  at the P4 boundary for a reforecast; lineage cap = the canary's total (below).

## Replay (deterministic, transcripts of P1/P2/P3/P8, 839.56M)
| role | spawns | calls/spawn | share | tool mix | tool-only calls |
|---|---|---|---|---|---|
| executor | 36 | 47 | 33.0% | edit 6.5%, test 23.7%, other shell 49.7%, read 16.8% | 20% |
| planner | 6 | 121 | 23.5% | read 42%, plan-file writes 24% | 36% |
| main | 7 | 71 | 14.8% | read 21%, other 57% | 20% |
| fixer | 10 | 69 | 13.7% | test 38% | 21% |
| reviewer | 16 | 42 | 11.2% | read 30% | 26% |
Executor context ~160k/call, spawn floor ~78k median. 27 planning files read by >=3 spawns (STATE.md 7, one plan 17x).
Reading: executors mostly drive build/e2e; planners re-read; the control loop, not coding judgment, dominates.

## Champion / challengers (P4 only)
- Champion: current envelope + directive under /gsd-autonomous: ~134M central (median phase 198M x 0.676).
- Challenger A (selected): T2 pattern, measured once (InfinityOps P4 44.25M vs 89-127M phases): compile
  04-CONTEXT into obligations + packets (no planner), proof-of-non-work closes EXISTS rows, one fresh Sonnet
  executor per packet via the mission (supervisor sequences; no Opus parent pane), proof by the committed
  combined-tree gate in an affected-spec mode, one independent review on the durable-exit seam only.
- Challenger B (partial, inside A): one deterministic proof transaction (build + xvfb e2e + HEAD assert ->
  structured receipt) so executors stop composing the recipe call by call. Full interrupt runtime deferred
  until P4 telemetry shows the remaining control-loop share.
- Hypothesis to falsify: P4 in 25-60M (central ~40M) at the same scope, proof and planes.

## Slices
S0 hold m-eaf2843afb16 before 05:00Z (zero model). S1 deploy the envelope + wu_packet launch commits to GEX44
(cherry-pick, smoke both planes, rollback point). S2 compile P4: obligations, non-work receipts, packets,
per-packet token + boundary budgets, the gate script (Sonnet, cap 7M). S3 proof transaction (inside packet 0).
S4 run P4 as the mission with wu_packet (estimate 40M, token_trip_ratio 1.5 -> hold at 60M). S5 review, tip
gate, economics vs champion, P5-P9 reforecast, KV/UKDL/CBR. Canary total cap 75M; over -> hold, never silent.

## Master Done-Gate
`python tools/orca_p4_canary_gate.py` (written in S2, before execution) exits 0 only if: every P4 obligation is
terminal with evidence (no UNKNOWN), non-work closures cite file:line + a check, each packet has a receipt
(tokens, calls, interrupt reasons, proof refs), the combined-tree gate summary is GREEN at the P4 tip SHA ==
closure HEAD, Windows claims sit in WINDOWS-LANE as PENDING (never PASS), the review verdict exists with 0
CRITICAL/HIGH open, metered spend <= 75M with the champion comparison recorded, a P5-P9 reforecast file
exists, and the KV/UKDL/CBR entries named in the receipt exist.
