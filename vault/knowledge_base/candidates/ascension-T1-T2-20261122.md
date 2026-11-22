# UKDL and session-lesson candidates: Ascension T1 + T2 (2026-11-22, panes 37612bb0 and a52cc240)

Append-only candidate record (T2 W4). It replaces in-place edits of `vault/knowledge_base/ukdl-universal.md` and
`session_lessons.md`. Those two aggregates had another writer's uncommitted edits, which blocked the merge of
`gsd/ascension-throughput`. A promotion pass folds these entries into the aggregates; this file stays as their
source.

## Session lesson (T1, session 37612bb0)
Measure the cost distribution behind an admission number before redesigning around it: the 29M 'judge reservation'
was the next generation's caps.

## UKDL PROMOTIONS -- Ascension Cognitive Throughput T1 (2026-11-22, pane 37612bb0; PP 0dfaec10, 5e03e129; plan vault/plans/ascension-cognitive-throughput-20261122.md). Proof plane named per line.
- PROCESS RULE PR-ADMIT-BY-THE-NEXT-CALL-NOT-THE-NEXT-GENERATION-001: an admission gate asks for the cost of the step
  it admits. The autopilot asked 29M (the next generation's caps) to judge, when judging measured p99 1.15M. Finished
  generations then waited 16 h unjudged at 477M/500M. Live on GEX44 14:45Z: TENNIS, WIIPARTY and FIFATC were judged
  at 485M and the arm waited "(judgment kept)" (V-AP-JUDGE-ASK-*).
- PROCESS RULE PR-RELEASE-RESERVATIONS-AT-CLOSE-001: a reservation booked against a cap is released at close down to
  the measured spend, on the day it was booked. Unmeasured spend releases nothing. Lifetime 3,020M reserved and 821M
  never spent (27%). The backfill took the day from 486.8M to 399.8M. Live: the FIFATC S298C close released 4.85M
  (V-AP-RELEASE-*, V-AP-BACKFILL-*).
- PROCESS RULE PR-COUNT-THE-POOL-BEFORE-THE-GENERATION-001 (candidate, not built): 21 to 23 of 38 INSTRUMENT_FAIL
  generations (97M of 201M) failed because a control pool or population sat below a floor their own plan declared.
  That count is a CPU check before arming (vault/programs/ascension/throughput/O6_INSTRUMENT_FAIL_CENSUS.md).
- TRAP T-RESERVATION-READ-AS-JUDGE-COST-001: the "29M judgment reservation" was the next generation's 25M + 2x2M, not
  the judge's cost. 315 measured judges: p50 0.40M, p95 0.85M. Measure the distribution before redesigning the judge.
- TRAP T-BUDGET-WAIT-READ-AS-MODEL-POLLING-001: the 5-minute `budget wait` lines come from a CPU-only cron that returns
  before any model call. They cost 0 tokens. Converting them to event wakes saves nothing; measure before
  re-architecting a wait.
- TRAP T-DAILY-RESET-MEANS-RUNNABLE-001: at the daily reset the weekly guard (85%) can still refuse. The 11-19/20 arms
  died as MissionError + arm_refund per tick. The arm path now asks account_governor first and waits with the judgment
  kept (V-AP-WEEKLY-*). Unit-proven; first live refusal not yet observed.
- TRAP T-WORKTREE-PROMPT-AS-OWNER-GATE-001: the host raises "approve Entering worktree" although EnterWorktree is
  pre-approved. It was typed HOST_GATE and parked MKWLIB about 4 h, plus 3 earlier missions. Its answer (plain `git
  worktree add` + bind) is the runtime's: now QUESTION_RESOLVABLE, the only live prompt plan_next judges. Live on GEX44
  PP (mission_policy 56/56, decision_recovery 29/29).

## UKDL candidates -- Ascension T2 (2026-11-22, pane a52cc240; PP b1492e15, 41fd9c13). Proof plane named per line.
- HARD-RULE candidate HR-SPENT-IS-MONOTONIC-001: a reservation release may return only booking above the measured
  spend. A settled generation books exactly its measured spend (`booked_net == spend`). An authority-based release
  broke this once (FIFATC S95C: authority 12.5M, booked 9.5M, 3M of measured spend erased). Live on GEX44 after the
  sweep: `autopilot.py conservation` = 265 settled, 265 conserved (V-AP-CONSERVATION-*, V-AP-SWEEP-*).
- PROCESS RULE PR-SETTLE-EVERY-TERMINAL-GENERATION-001: release ran only on `generation_closed`. 64 generations that
  ended HALTED never settled, and terminal overruns were never booked. Every terminal generation is now settled
  (release above spend, `spend_correction` below it) and marked `generation_settled`. Live 16:53Z: 110,975,377
  released, 354,213 corrected, ledger -111,895,067 exact; a second sweep books 0.
- PROCESS RULE PR-OWNER-GRANTS-ARE-ESCROW-001: Owner top-ups and grants booked against a cap are escrow like any
  reservation. They were never released (KSR S181K kept 4.0M, S53K 0.27M).
- TRAP T-STRANDED-BOOKING-READ-AS-UNSPENT-001: "78 armed, never closed, 838.7M booked" (71 HALTED, 705.7M) read as
  stranded capital. The measured unspent part was 111M, because halted missions had spent most of their authority.
  Measure the spend before sizing a release.
- TRAP T-POOL-FLOOR-SERVICE-WITHOUT-A-POPULATION-001: a central population counter needs a canonical population. In
  4/4 sampled class-A checkpoints the counting tool was specific to one hypothesis, so there is none yet (W3 step 0).
- PROCESS RULE PR-APPEND-FIRST-INSTITUTIONAL-WRITES-001: a mission writes its lessons and UKDL candidates to its own
  new file, never in place into a shared aggregate. The T1 branch could not merge while another pane held uncommitted
  edits in both aggregates. This file is the remedy, applied.
