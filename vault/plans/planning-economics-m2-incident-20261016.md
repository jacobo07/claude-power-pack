---
covers: [planning-necessity, work-class-capsule, m2-planning-incident, owner-pause-stop, p25-canary, prereg-lint]
status: APPROVED 2026-10-16 (Owner "a 1. 30.5M 2. b 3. a": tranche 30.5M hard; P25 from a PP clone on GEX44,
  live install untouched; bootstrap in the interactive pane, no Ralph mission)
progress: |
  E1 DONE: d466d977 hold --stop (owner_pause; V-OP 5/5, drill 2 red), 2f61b594 session-tree (V-STR 4/4; real M2
     tree on GEX44 = 29,947,551 exactly). PP clone on GEX44: ~/missions/pp-tbm2 (git archive of 2f61b594).
  E2 DONE: ae7c45c2 planning_gate.py + arm --work-unit/--planning-override (V-PNG 17/17; drills 9 + 1 red).
  E3 DONE: TB ac66192 capsule .planning/capsules/TB-DISC-PROBE.json + c79728f tools/prereg_lint.py
     (test_prereg_lint 15/15 laptop AND GEX44; in-memory mutants of the TIME and CLOSED checks go red; the t300
     and portrait blockers are fixtures). GEX44 ~/missions/tb-m2 main fast-forwarded to c79728f by bundle
     (worktree-m2-phase5 untouched); invalidator sha256 identical on Linux. ~/missions/pp-tbm2 got the 3 E2 files
     (LF, blob-identical to ae7c45c2; the E1 archive there is CRLF via autocrlf, content = E1): V-PNG 17/17 there,
     and planning_gate on a P25 unit (2 unknowns) -> DELTA_PLAN, 1M authority, no planner agent.
  BUDGET GATE (measured 2026-10-16 ~14:05Z, mission_spend._file_tokens deduped, since the approval message
     13:23:01Z): predecessor 56c349b4 19,956,064 (avg ctx 278k, peak 454k: context rent) + successor efadfbcc
     7,334,378 (avg 154k) = 27,290,442 of the 30.5M tranche. 25M "hard stop" (sec. 32) passed; ~3.2M left
     cannot cover E5 (P95 8M). STOPPED for the Owner: raise/second tranche, or run E5 as a fresh small-context
     Sonnet worker on GEX44 (the compiled-unit path this plan forecasts at <=70k ctx), not from an Opus pane.
  OWNER 2026-10-16 "a": +10M (tranche 40.5M); E5 runs as a fresh small-context Sonnet worker on GEX44.
  NEXT E5 P25 (unit JSON -> planning_gate -> prereg -> lint ->
     PROBES entry editing the Cantina .scp -> build -> tb_local on GEX44; bounded worker or this pane), E6
     reforecast, E7 CCR shadow receipt + UKDL/vault. Spend this pane from approval must be measured with
     mission_spend session-tree, never a line sum.
created: 2026-10-16
owner_surface: chat (this file is the backup)
---

# Planning economics after the M2 incident: master plan (Reality Delta + staged tranche)

## 0. What the scan changed (read this first)
The prompt's premises came from MY numbers in chat, and two of them are false:
- **65.4M is wrong. Real M2 spend: 29,947,551 processed tokens** (deduped by message id). Claude writes one
  transcript line per content block and repeats the message `usage` on each; my sum counted those lines. Raw
  line sum = 65,398,743 (2.18x).
- **The breaker DID see the subagents.** `mission_spend.processed_tokens` walks the session dir with `rglob`,
  which includes `<sid>/subagents/agent-*.jsonl`. It read 25,377,536 at 14:26; the reviser kept running to 14:49
  and added the remaining ~4.6M. There is no descendant-invisibility bug.
- **The "1-3M per probe" prior is also mine, and unmeasured.** Measured (deduped, laptop transcripts, commit
  windows): P22 4.56M (31 turns, Opus); P24 9.09M (42 turns, Opus); P23's window is 30.9M, but the same pane
  also wrote the M2 plan inside it, so it cannot be separated (contaminated).
Consequence: the incident is real, but it is a **~30M planning loop that produced zero execution, about 3-6x the
cost of a whole precedent probe**, not 16-30x. The programme is cut to what the evidence supports.

## 1. Current M2 reality
- Goal `tb-m2` (130M, declared on the laptop install only). Mission `m-f9290d78278f`, GEX44, state RUNNING +
  owner_hold, no live worker: `claude agents` is empty; stopped with `claude stop 505ddd34`, 14:51.
- Envelope: token_estimate 60M, stall budget 15M, work_dir = the worktree (set 14:2x today).
- Laptop mission `m-0fdcc50a311b`: HALTED + hold; 1.59M spent (cost_mark).
- M2 spent so far: 29.95M (GEX44) + ~1.6M (laptop) = **~31.5M of 130M; ~98.5M remains** (the prompt's 63M
  was derived from 65.4M).
- Uncommitted: the reviser's edits to 05-01..05-05 in `worktree-m2-phase5`; committed: `e13c2d0` (plans v1).

## 2. Exact cost tree (deduped; GEX44; all Sonnet 5.5)
| Node | Type | Turns | Processed | Avg ctx/turn | Peak ctx |
|---|---|---|---|---|---|
| 505ddd34 worker (coordinator) | main | 24 | 3,194,820 | 132,814 | 161,131 |
| aa37b5f3 "Plan phase 5" | gsd-planner | 128 | 17,418,378 | 136,057 | 214,566 |
| a8cb5a88 "Check phase 5 plans" | gsd-plan-checker | 26 | 3,212,251 | 123,522 | 155,770 |
| a4319f3c "Revise phase 5 plans" | gsd-planner (replan) | 43 | 5,936,347 | 138,039 | 200,391 |
| a7c29714 "Recheck phase 5 plans" | gsd-plan-checker | 3 | 185,755 | 61,904 | 62,533 |
| **Total** | | **224** | **29,947,551** | | |
Planning 23.35M (78%), review 3.40M (11%), coordination 3.19M (11%), execution 0.

## 3. Accounting gap (actual, not assumed)
| Claimed gap | Verdict | Evidence |
|---|---|---|
| Subagents invisible to the breaker | FALSE | rglob over the session dir; 25.4M read at 14:26 included the subagents |
| My chat report double-counted | TRUE (instrument error) | raw 65.4M vs dedup 29.9M |
| Hold does not stop a live worker | TRUE on GEX44 | the GEX44 install 30fdbf0f (10-09) predates spec mission-cost-hold-stops-worker (laptop has stop_owner via `claude stop`) |
| Stall fingerprint blind to the worktree | TRUE on GEX44 | work_dir was None, so the fp read the clone root (`ef2dadc0`, frozen); the laptop has AMCR binding |
| Daemon resurrects paused work | PARTLY | I sent a raw SIGTERM; the Claude daemon treats that as a crash and resumes (correct behaviour). `claude stop` was durable. An Owner hold, by contract, does not stop the worker |
| GEX44 PP install drift | TRUE, root | no goal-declare, arm-chain, cost-hold stop, binding, calibration |

## 4. Root-cause matrix (29.9M)
1. **Topology**: `/gsd-autonomous` always runs plan-phase (planner, then checker, then replanner) for every phase. Nothing
   asks whether the work class already has a precedent. Cost 26.7M of the 29.9M.
2. **Context rent**: every turn carries ~136k of context (the GSD workflow plus PROJECT/ROADMAP/STATE/CONTEXT plus growing
   plans). 128 planner turns x 136k = 17.4M. Output was ~180 KB, about 45k tokens, so **~0.3% of processed
   tokens became plan text**.
3. **Scope inflation**: 5 plans, 4 waves, STRIDE registers, mutant validators, a 2nd reproducibility run,
   conditional follow-up discs, re-verifying the portrait (82 mentions; P24 closed it).
4. **GEX44 install drift**: the breaker tripped at ~10.6M (13:40), but the hold could not stop the worker, which spent ~19M more.
Iteration standard: CLASS 2 (the plan assumed repo/runtime state that was false: a fresh install on GEX44, no
precedent reuse) + CLASS 4 (the hold "succeeded" while the spend continued) + CLASS 5 on my side (I reported
an unverified total).

## 5-7. Boundary amplification, context rent, novelty
- Planning boundaries: 224 model turns for a unit whose irreducible decisions are about 6: which .scp hosts the
  camera, CameraCut syntax, Force condition, CreateCreatures args, capture timeline, verdict rule.
  Necessity ratio ~6/224 = 0.027.
- Context rent: avg 132-138k/turn; peak 214k. Precedent and doctrine re-read every turn.
- Novelty: the P25 delta is the .scp edits plus a new timeline. Build, tb_local, capture, judging, ledger and the prereg
  shape are identical to P22-P24. Text duplication vs precedent was not measured by tokens; qualitatively, most of the
  180 KB is harness/threat/proof boilerplate. It will be measured in P25 by the lint, not asserted.

## 8. P22-P24 precedent matrix (Work Class `TB-DISC-PROBE`)
| | P22 | P23 | P24 |
|---|---|---|---|
| Delta | main.dol name-table swap | icon files + icon= | none (route + build identity) |
| Prereg | docs/PREREG_P22 (1 page) | PREREG_P23 | PREREG_P24 |
| Build | build_two_builders RECIPE | same | same, Linux wit, byte-identical |
| Run | tb_client queue | tb_client queue | tb_local (GEX44) |
| Timeline | P22 grid | P22 grid | P22 grid |
| Judge | frames by eye | frames by eye | frames by eye + P23 comparison |
| Ledger | AUTHORIZED/CONSUMED | same | same |
| Measured | 4.56M | (contaminated) | 9.09M |
Stable across all three: the prereg shape, RECIPE+PROBES build, timeline grammar, capture/judge, ledger, commit.
Variant: the run route (queue to local; local is now the canonical one on GEX44).

## 9. P25 delta (from RESUMPTION + 05-CONTEXT, not expanded)
Cantina probe on RECIPE: CameraCut on Player0 (front camera) and `PlayerUsingForce` -> `CreateCreatures` womprat
next to Madzia, as loose `.scp` edits; one tb_local run; judge the camera and the spawn. The portrait is CLOSED (P24) and excluded.
Open unknowns (the real planning content): is a loose .scp honoured (P5-SCP), and does PlayerUsingForce fire (P5-FORCE).

## 10-24. Components: build / reuse / not build
| Section | Decision | Size |
|---|---|---|
| 10 Planning Necessity Gate | BUILD minimal: `tools/planning_gate.py`. Inputs: capsule match, novelty flags, irreversibility. Out: DIRECT_TEMPLATE / DELTA_PLAN / FULL_PLAN / OWNER. Wired at mission arm: a capsule match arms COMPILED_UNIT (`--wu-packet`) instead of `/gsd-autonomous` | ~150 lines + tests |
| 11 Planning Authority | REUSE the envelope: a FULL_PLAN unit gets its own token_estimate; no new ledger | config |
| A Mission Cost Tree | REUSE mission_spend (already counts children, deduped). ADD a `tree` report per session/subagent (it exists for sessions: `tree` flag line 581) so nobody hand-sums again | ~40 lines |
| 12-16 Plan compiler / IR / Delta compiler / CSE | NOT BUILT now. The capsule (a parameterised template) + delta fields is the IR at the size the evidence supports; a general compiler has no second consumer yet | 0 |
| 14 Work-Class Capsule | BUILD `TB-DISC-PROBE` in the TB repo from P22-P24: template prereg, PROBES entry pattern, run/judge/ledger commands, invalidators (route, wit, harness sha) | 1 file |
| 17 Plan linter | BUILD `tools/prereg_lint.py` (TB): every cited t in the capture list; claims not in `closed_obligations` (portrait to P24); probe key exists; disc sha matches | ~120 lines + tests |
| 18-19 Risk / proof compiler | NOT BUILT as a system: the capsule carries a fixed risk class (reversible personal mod, low) and "proof = one run + frames"; reproducibility only if the verdict is ambiguous | 0 |
| 20-21 Review / replan necessity | Folded into the gate: DIRECT_TEMPLATE = no semantic reviewer; lint failures are patched in place | 0 extra |
| 22 Owner pause | BUILD `gsd_mission.py hold --stop` (Owner hold that also runs stop_owner = `claude stop` + wait) + test; deploy the pause/cost-hold/binding fixes to GEX44 (see Q2) | ~30 lines |
| 23 CCR | SHADOW only: in `agent.spawn`, receipt `planner_spawn` with subagentType + mission; not enforce (no proof that middleware refusal is supported; CCR is not installed on GEX44) | ~15 lines |
| 24 Cognitive deopt | Covered by the existing stall breaker once binding/stop are deployed on GEX44 | 0 |

## 25-27. P25 canary, old vs new, learning curve
P25 runs as a COMPILED_UNIT: a fresh Sonnet worker on GEX44, wu_packet = capsule + P25 delta, small context,
no planner, no checker. Done-gates P25-DONE-1..15 from the prompt, all observable.
| | Old M2 path (measured) | Compiled P25 (forecast) |
|---|---|---|
| Planner/review turns | 197 | 0 (lint only) |
| Coordinator turns | 24 | ~25-40 (execution) |
| Avg ctx | ~136k | target <=70k (packet, not the GSD workflow) |
| Spend | 29.95M, 0 executed | P50 3M / P80 5M / P95 8M, executed + judged |
Learning curve: P22 4.56M, P23 n/a (contaminated), P24 9.09M (interactive Opus pane, ~215k ctx/turn), P25 forecast 3M.
If the worker's measured spend passes 8M before the run: STOP and report.

## 28-29. M2 6-14 reforecast, Two Builders gate
After P25: classify each phase (6 faces = capsule; 7 CHG archaeology = novel RE; 8 writer = novel; 9-11 hair/kitten =
capsule after 8; 12 Kitten Call = partial; 13 extras = capsule; 14 = mixed) and route each through the gate;
new P50/P80/P95 from P25's measured cost. M2 stays held until that table exists and is approved.

## 30. Mode by workstream
Reality Delta: done (EXECUTION). Cost tree report, lint, capsule, pause --stop: EXECUTION. Planning gate: PLAN
(this file) then EXECUTION. CCR: shadow EXECUTION. P25: EXECUTION. Reforecast: EXECUTION. No ULTRA-PLAN: no
owner conflict was found.

## 31. Micro-commits
PP: (1) this plan; (2) cost-tree report + test; (3) hold --stop + test; (4) planning_gate + test + arm wiring;
(5) CCR planner_spawn receipt; (6) UKDL/vault. TB (on GEX44 branch): (7) capsule; (8) prereg_lint + test;
(9) P25 prereg; (10) P25 result; (11) reforecast.

## 32. Staged budget (processed tokens; this pane is Opus, so routine pieces go to Sonnet subagents where they are cheaper)
| Env | Scope | Lower bound | Lower | P50 | P80 | P95 | Hard | Conf |
|---|---|---|---|---|---|---|---|---|
| E0 | Reality Delta (spent) | - | - | ~4M | | | - | measured after |
| E1 | cost-tree report + hold --stop + tests | 0.5 | 1 | 2 | 3 | 4 | 5 | med |
| E2 | planning_gate + arm wiring + tests | 0.8 | 1.5 | 2.5 | 4 | 5 | 6 | med |
| E3 | capsule + prereg_lint + tests | 0.6 | 1 | 2 | 3 | 4 | 5 | med |
| E4 | GEX44 install update (if Q2 = yes) | 0.3 | 0.5 | 1 | 2 | 3 | 3 | med |
| E5 | P25 canary (worker) | 1.5 | 2 | 3 | 5 | 8 | 10 | low |
| E6 | reforecast 6-14 | 0.5 | 1 | 1.5 | 2 | 3 | 3 | med |
| E7 | CCR shadow + UKDL/vault/CBR | 0.5 | 1 | 1.5 | 2.5 | 3.5 | 4 | med |
| **Tranche** | | | **8** | **13.5** | **21.5** | **30.5** | **25 (hard stop)** | |
Capital law check: P50 13.5M < 29.9M incident; hard stop 25M.

## 33-36. CAPEX/OPEX, amortisation, request, next tranche
- CAPEX (PP + capsule): E1-E4, E7, P50 ~9M. OPEX (P25 + reforecast): P50 ~4.5M.
- Observed savings are counted only after P25 (old-path counterfactual: ~30M per phase planned with GSD).
  Projected: phases 6, 9-11, 13 on the capsule. Not counted until measured.
- **Request: 25M hard, drawn from the M2 remainder (~98.5M); M2 stays held for anything else.**
- Second tranche only after: P25 verified at <=8M; reforecast table; hold --stop proven on GEX44.

## 37. Owner questions
Q1 approve this tranche (25M hard)? Q2 update the GEX44 live PP install to laptop HEAD (other missions there use
it, e.g. ql-lifecycle) or arm P25 from a PP clone? Q3 run the bootstrap in this pane (recommended: arming a Ralph
mission for it would repeat the planning topology being fixed) or as /cpp-gsd-long?
