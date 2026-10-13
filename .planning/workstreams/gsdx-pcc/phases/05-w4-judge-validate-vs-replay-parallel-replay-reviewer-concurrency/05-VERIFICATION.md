---
phase: 5
workstream: gsdx-pcc
status: passed
verified: 2026-10-13
head_at_verification: 73179700
---

# Phase 5 Verification -- W4 Judge VALIDATE vs REPLAY, parallel replay, reviewer concurrency

Every check below was run by the worker. **Windows plane** = the laptop (hermetic temp roots). **Linux plane** = GEX44: nothing in Phase 5 ran there; the two items it owns are listed UNRUN at the end.

## Gates (Windows plane, logs under logs/)
- GSDX_JUDGE_VALIDATE_PASS=11/11  threshold=11/11 (D15)
- GSDX_JUDGE_PASS=11/11  threshold=11/11 (regression after replay wiring)
- GSDX_REPLAY_PARALLEL_PASS=14/14  threshold=14/14 (D16; RED 12/14 against the serial judge)
- EVB_ABA_PASS=10/10  threshold=10/10 (R05)
- EVB_PASS=21/21  threshold=21/21 (regression)
- GSDX_REVIEW_PASS=12/12  threshold=12/12 (D17, includes a real lost-race retry and a cross-client case)
- GSDX_PCC_SEMANTICS_PASS=48/48, GSDX_PCC_REPLAY_PASS=28/28 (Phase 2, re-baselined for the sixth new type)
- GSDX_FRONTIER_PASS=40/40, GSDX_INVALIDATION_PASS=26/26 (Phase 3/4 regression)
- Liveness: python modules/liveness/reachability.py exit 0, 0 gate offenders (replay and review declared PLANNED)

## Mutation drills (Windows plane, isolated copy, control valid)
d1 KILLED, d2 KILLED, d4 KILLED, d5 KILLED, d6 KILLED, d7 KILLED, d8 KILLED, d9 KILLED, d10 KILLED.

## UNRUN -- for the coordinator's Linux plane
- d3: reaped for low laptop memory, not retried (spec: drills/d3.json, log logs/05-01-d3.log).
- tools/test_gsd_x_goal_mutation.py: mutates live files; never run on the laptop. judge.py anchor lines are textually intact.

## Residual limit
A Windows writer that restores mtime and inode defeats the live-read journal; only the snapshot read proves that case.
