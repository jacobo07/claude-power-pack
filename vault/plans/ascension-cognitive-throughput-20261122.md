# Ascension Cognitive Throughput, Tranche 1 (plan, awaiting Owner approval)

Pane 37612bb0, 2026-11-22 ~12:30Z. Mode: PLAN (ownership is clear, so no ULTRA). Carrier after approval: `/cpp-gsd-long` in a
dedicated PP worktree (see Carrier). The inline chat copy is authoritative; this file is for context-wall recovery.

## Reality Scan (measured on GEX44 with the commands in the scratchpad q20/q21/q23; ledger 2,367 rows since 11-11)

Owners. `vault/programs/ascension/autopilot/autopilot.py` handles admission, judgment, arming and the day cap. It is
deployed as `/home/kobii/agora/ascension-autopilot/autopilot.py` (md5 66e48dbd3e2f, identical to the laptop copy).
`tools/account_governor.py` owns the weekly guard at 85%; `gsd_mission.py arm` calls it. `gsd_mission.py` owns the
mission lifecycle and leases. The factory (`agora/factory/lane.py`) owns match application.

| Premise in the Owner prompt | Measured | Verdict |
|---|---|---|
| "29M judgment reservation" | 29M = `GEN_CAP` 25M + 2 x `CALL_RESERVE` 2M, asked before judging (`autopilot.py:1731`). It reserves the NEXT generation, not the judge. | FALSE premise |
| Actual judgment cost | n=315, all measured. p50 0.40M, p80 0.56M, p95 0.85M, p99 1.15M, max 2.40M. AGREE p50 0.40M, DISAGREE p50 0.38M, INCONCLUSIVE p50 0.31M. | over-reservation is about 34x p95 |
| Day cap is real spend | Today's 477.4M = 411.7M `arm_reserve` (authority booked at arm, never released at close: `autopilot.py:2134-2144` books only the overrun) + 66M measured calls. Lifetime reservations 2,912M; spend of closed generations 1,416M. | the cap counts reservations |
| Generation authority vs spend | n=196 closed. Spend p50 6.5M vs authority p50 9.6M; 64% used overall. | 36% stranded |
| 5-minute polling burns model tokens | `budget wait` returns before any call (`autopilot.py:1737`), from a CPU-only cron. 0 tokens. | FALSE premise (log noise only) |
| Weekly guard blocks now | `account_governor status`: lower bound 69.29%, coverage FULL. Laptop $1,762, GEX44 $1,404, calibration $4,570 per 100% (ESTIMATE). Reset 11-18 17:00Z, next 11-25 17:00Z. The 86.7% refusals were on 11-19/20, the previous week. | not now; the guard is forecast to trip at about 85% around 11-23 early (at $875/day), leaving about 2.5 days of blackout |
| MKWLIB EnterWorktree deadlock | Confirmed. BLOCKED from about 08:32Z to 12:20Z on "approve Entering worktree"; the repo has no `origin` (remote `mkw-decomp-src`). **Fixed by hand**: decide D1 (local `git worktree add -b worktree-s296l ... lane/mkw` + `bind`), and the mission is RUNNING. | confirmed; architectural immunity still to do |
| FIFATC "not final" checkpoint | Judged INCONCLUSIVE for 183,084 measured tokens. All INCONCLUSIVE judgments together cost 7.8M lifetime. | real but small |

Where the spend goes, lifetime: generations 1,416M (about 74%), planner calls 342M (18%; p50 0.62M x 477), judges 141M (7%),
lever design 45M. Theory of constraints: **judges are not the cost**. The visible block is an admission artifact. The real rents
are generation yield and planner rent.

Yield (evo_decision classes over 279 decisions): CERT 39, MATCH 8, INFORMATION 95, NONE 64, **INSTRUMENT_FAIL 38 (about 14%,
roughly 250M at p50 spend)**, PLANNER_STOP 18. Per lane: KSR 23 CERT / 381M gens; TENNIS 9 / 308M; WIIPARTY 5 / 167M;
FIFATC 2 / 96M; MKW 6 MATCH / 121M; WSR 2 MATCH / 128M; FIFA 0 / 162M; MKWLIB 0 / 54M.

Refinement pass (iteracion-avanzada-universal, phase 1-2): three Owner premises were false (CLASE 2: an assumed repo state).
The plan is rebuilt on the measured state, not on the prompt's ordering.

## Tranche 1: waves (bottom-up by obligation)

W1, truthful capital (autopilot.py + test_autopilot.py)
- O1 Reservation release. At close, a generation's day booking becomes its measured spend (reservation only while open;
  attributed to its arm day, which is the current convention). New digest metric `reservation_overhead`. Changes what
  the Owner's 500M means: from "authority booked" to "measured + open reservations". **Owner decision Q1.**
- O2 Judge admission split. Judging asks `JUDGE_ASK` (judge p99 1.2M + planner p99 2.2M, rounded to 4M) instead of 29M.
  Arming keeps its 25M ask, and its wait keeps the judgment (1e2e488, already live). Effect: finished generations
  (TENNIS S297T, WIIPARTY, FIFATC) get judged during scarcity; at reset the next arm starts from a kept judgment with no
  re-judge.
- O3 Executability gate. A checkpoint marked not-final becomes a deterministic `JUDGMENT_NOT_EXECUTABLE`: no model call,
  a ledger row, and a regression test from both poles.

W2, weekly-aware admission + immunity
- O4 Joint eligibility. The autopilot asks `account_governor check --action arm` before arming. A refusal becomes one
  `weekly_wait` row with the next reset and a forecast of when the guard trips at the current burn, instead of a
  traceback inside `gsd_mission arm` on every tick.
- O5 MKWLIB immunity. A lane flag `local_worktree` (a repo without `origin`) makes the packet command instruct `git
  worktree add` + `bind`, and the worker launches with EnterWorktree denied, if `gsd_mission arm` can pass a tool deny
  list (UNKNOWN: verify; else add the pass-through). Regression test.
- O6 INSTRUMENT_FAIL census. Classify the 38 generations. If a recurring class is deterministic, it becomes a pre-arm
  gate in W3 (the largest measured waste).

W3 (gated on W1/W2 measured value; not approved by this plan): planner rent (342M) through a compact Lane State Image
input; yield-aware allocation inside weekly scarcity; the INSTRUMENT_FAIL gate.

Explicitly deferred, because no measured bottleneck points there yet: obligation graph, residual IR, operator library,
compiler twin, zero-model certification, Agent Teams. Re-rank after W2.

## Token budget (this mission's own spend; staged, the ceiling is not a target)

| | lower | P50 | P80 | P95 |
|---|---|---|---|---|
| W1 (O1-O3 + tests + deploy) | 3M | 5M | 7M | 10M |
| W2 (O4-O6 + tests + deploy) | 2M | 4M | 6M | 9M |
| closeout (UKDL, plan, reconcile) | 0.5M | 1M | 1.5M | 2M |
| total | 5.5M | 10M | 14.5M | 21M |

Hard authority requested: 15M (W1 8M, W2 5M, closeout 2M), 0 top-ups. Max cycles 6, max 24 h (Production Reality needs the
00:00Z reset). Planning ceiling: this plan (about 1.5M spent) plus at most one re-plan turn. First evidence deadline: O2 live on
GEX44 with a judgment run under the day cap before 00:00Z. Breaker: two intervals with no causal delta trigger METHOD_PIVOT_REQUIRED.

Expected value. O2 clears about 3 stranded judgments a night (WIP) at about 0.4M each, instead of 16 h idle. O1 turns about 36%
of phantom day booking into admissible capital on days the weekly guard has room. O5 removes the human-interrupt class
(about 4 h lost today). Break-even: O2+O5 alone are worth more than the W1 P50 on the first night. Honest limit: this week
the weekly guard, not the day cap, will bind from about 11-23; T1 does not create weekly tokens. It stops stranding them.

## Carrier
Arming a mission in the PP main tree would scaffold and archive the shared `.planning/` (other workstreams are dirty there).
Recommended: a PP worktree `worktree-ascension-throughput` plus a gsd-long mission (15M, 0 top-ups). Alternative: execute
inline in pane 37612bb0.

## Owner questions
Q1: Should the day cap count measured spend + open reservations instead of booked authority? (yes/no)
Q2: Carrier: mission in a PP worktree (recommended), or inline in this pane?
