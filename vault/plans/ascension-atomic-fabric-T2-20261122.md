# Ascension Atomic Reconstruction Fabric: Tranche T2 plan (pane a52cc240, 2026-11-22 16:30Z)

Mode: PLAN MODE. The owners are clear, so an ULTRA-PLAN fork is not justified. EXECUTION follows the Owner's "y".
Carrier: `/cpp-gsd-long` mission on the PP worktree `gsd/ascension-throughput`. If the laptop is still under its 3 GB
RAM floor when arming (it had 1.2 GB free), the mission is refused, and the work runs inline as T1 did, under the same
authority.

## Reality Scan (measured 16:23Z on GEX44 and the laptop; source rs1.sh / rs2.sh in the pane scratchpad)
| fact | value |
|---|---|
| caps | day 500M (binding: today 487.1M), total 4.7B (ledger 3.09B, not binding), gen 25M, judge ask 6M |
| judge cost (n=324, measured) | p50 0.40M, p80 0.56M, p95 0.78M, p99 1.13M, max 2.40M |
| ledger mix | arm_reserve 3,043M (282) · plan 351M (490 calls for 280 arms) · judge 143M · topups 165M · lever_design 45M |
| close replay | 204 closed, all measured; booked-released == spend for 192; 12 differ (sum -84M, probably overruns booked on the close row: unreconciled) |
| **stranded escrow** | 78 generations armed and never closed hold 838.7M. **71 are HALTED (705.7M)**, 1 COMPLETED (10M), 6 RUNNING (76M). The release path runs only at `generation_closed` |
| W3 live | 0 `pool_floor_halt` rows since the deploy (the sample is too small for any J0 decision) |
| worker resident prefix | first call 73-91k tokens (cache creation 45-64k + read 13-27k; TENNIS about 90k), paid again on every tool call |
| slim worker | exists in `gsd_mission.py` (SLIM_PROFILES slim-t1/t2, `claude -p`) and is used by no Ascension lane. The 11-19 Owner proposal "(1) slim pilot on one lane" was never run |
| compile/diff cache | none in `agora/factory` (factory.py, perm_stage, twin compile every time) |
| lanes | RUNNING: FIFATC S306C, MKW S304M, TENNIS S305T, WIIPARTY S307W, WSR S267R · PARKED: FIFA, MKWLIB · STOPPED: KSR |

False premises in the addendum (CLASE 2):
- (a) "the backfill freed about 1.5B of lifetime room". The measured figure is 821M released lifetime. The larger
  number on the books is 705.7M stranded in HALTED missions.
- (b) "J0 on pool-floor is immediate". There are 0 halts so far.
- (c) "central population service". 4/4 sampled counts were hypothesis-specific tools, so no canonical population
  definition exists to centralise. It stays candidate-only.

## Ownership gate (EXTEND > MERGE > CONNECT > REUSE > CREATE)
- Accounting: `autopilot.py` ledger (spend_totals, reservation_release). EXTEND, no new ledger.
- Judgment: `autopilot.judge`, with O3 as the pattern. EXTEND.
- Worker context: `gsd_mission.py` slim profiles. CONNECT to the autopilot arm path.
- Lessons/UKDL contention: append-first candidate files beside the existing aggregates. EXTEND, no new store.
- Atom/proof DAG/residual IR/compile CAS/operator algebra/replay lab/quota market: no consumer this tranche. They stay
  CANDIDATE, and W5 measures the evidence to rank them.

## Waves (each wave = micro-commits; gate = GEX44 test_autopilot + control red + live tick)
**W1: truthful escrow and the M2 resolution (P50 5M).**
- SPENT, ESCROW and FORECAST become derived views over the existing ledger:
  - SPENT = measured calls + measured spend of closed generations.
  - ESCROW = open reservations of non-terminal missions.
  - FORECAST = the next arm ask per WAITING lane.
- Replay all 3,0xx rows to prove SPENT never decreases at any prefix, and reconcile the 12 diffs.
- M2 resolved by invariant: a release returns escrow in every scope the reservation was charged (its booking day, the
  total, its lane envelope), and it never touches SPENT. That is what the code does today; W1 adds the proof and
  pins it.
- Stranded sweep: a HALTED mission that is terminal is released at its measured spend (`mission_spend`).
  - Terminal means its lane has armed a later generation and no `continue:<mid>` is pending.
  - Unmeasured spend releases nothing and books `UNMEASURED`.
- Wire `reservation_overhead` into the digest (review L2): it is the ESCROW consumer.

**W2: the deterministic pool-floor path (P50 4M).**
- (a) J0: a POOL_FLOOR halt that names `via python3 tools/<x>.py` is re-counted by the autopilot at HEAD in a scratch
  worktree (`gate_rc_at` machinery), and its protected checks are run deterministically. If both hold, the verdict is
  INSTRUMENT_FAIL(population) with no model call. Anything else goes to the judge.
- (b) Pre-arm: when a planner's floor cites a counting tool that ALREADY exists at the base (repeat populations,
  e.g. TENNIS 8/21 class A), the autopilot runs it before arming. Below the floor, the plan returns with the count and
  no worker is started.
- Both ship SHADOW (log the decision only). ENFORCE after 3 live agreements with the judge. Sequential stopping, no
  fixed date.

**W3: context rent, the largest lever (P50 4.5M).**
- (a) Sub-attribute the 73-91k worker prefix from one real worker transcript plus its launch manifest: system,
  CLAUDE.md chain, skills/agents listing, tools, hook additionalContext, packet.
- (b) Champion/challenger: run the existing slim profile on ONE EXPLOIT lane (WIIPARTY) for 2 generations, with a
  per-lane kill switch.
  - Measure processed tokens per tool call, certs/M, outcome class and policy refusals against the same lane's last 4
    generations.
  - Promote only if certs/M holds and no gate or authority regression appears.
- (c) Planner rent: 490 plans for 280 arms cost 351M. Measure how much is policy re-plans, and fold the top refusal
  into the pre-check if it is deterministic.

**W4: institutional debt and the merge unblock (P50 2.5M).**
- Move T1's additions to `session_lessons.md` and `ukdl-universal.md` into new append-only candidate files. The branch
  then touches no foreign-dirty aggregate, and it merges into `feature/knowledge-acquisition`.
- Pin the OWNER_DECISION exemption (`mission_policy.py:385`) from both sides (review L1).
- Retire or register `backfill_releases`.
- Split `test_mission_decision_recovery` into a pure part (laptop) and an integration part (GEX44).

**W5: measure the next tranche, measurement only (P50 1.2M).**
- The duplicate-compile ratio in factory/perm_stage/twin logs (same source+flags+compiler hash). This feeds the
  compile-CAS decision.
- The share of unresolved functions per lane by residual class. This feeds a first Unknown Surface Area estimate.
- Ranked by lifetime NPV in the closeout.

Closeout 1.5M: UKDL candidates (append-first), Baseline Ratchet assessment, RESUMPTION, the meta-analysis questions
the evidence can answer.

## Budget (processed tokens, bottom-up at about 120k per tool call; T1 overran 3x, so the mission record enforces it)
| | lower | P50 | P80 | P95 |
|---|---|---|---|---|
| W1 | 3.0 | 5.0 | 6.5 | 8.0 |
| W2 | 2.5 | 4.0 | 5.0 | 6.5 |
| W3 | 3.0 | 4.5 | 6.0 | 7.5 |
| W4 | 1.5 | 2.5 | 3.0 | 4.0 |
| W5 | 0.8 | 1.2 | 1.8 | 2.5 |
| closeout | 1.0 | 1.5 | 1.5 | 2.0 |
| **total** | **11.8** | **18.7** | **23.8** | **30.5** |
- Hard authority 25M, 0 top-ups, max 6 cycles, max 24 h. The W3 pilot generations are lane spend inside the existing
  WIIPARTY caps.
- **Early value gate at 4M:** W1's replay verdict plus the measured stranded figure, or W4's merge unblock. If neither
  lands, METHOD_PIVOT_REQUIRED. Two-interval breaker as specified.

Expected value:
- W3: if slim removes about 55k of a 75k prefix per call, worker processed tokens fall about 40%. That is roughly 50M
  per day of day-cap room, about 2 more generations per day at today's binding cap. UNVERIFIED: quality is the risk,
  hence the challenger.
- W1: correctness, and up to 705.7M of lifetime room returned truthfully. Its throughput effect is nil today, because
  the total cap is not binding.
- W2: 0.4M per J0 plus up to about 4.6M per prevented repeat class-A generation. Small N.
- Break-even of the tranche, if W3 is promoted: under 1 day.

## Not this tranche (candidate-only, with the reason)
- Epistemic atoms, proof DAG, residual IR, operator algebra, unsat/symmetry, e-graphs, replay lab, quota market,
  digital twin: no consumer yet, and W5 supplies the ranking evidence.
- Pool population service: no canonical population (premise c).
- Push: never.
