---
covers: [self-governing-mission-runtime, autonomous-liveness, continuation-intent, progress-verified-wake, mission-economic-profiler, economic-field-types, continuous-reforecast, derived-runway, context-economic-rotation, resource-retry, proof-budget, marginal-evidence-value, strategy-exhaustion, decision-plane-cleanup, tb-full-canary]
status: PROPOSED 2026-10-18 (Reality Delta Scan only; nothing implemented; waits for ONE Owner approval)
tier: SDD T3
---

# Self-governing mission runtime: plan from the TB-FULL stress test

Scan time 2026-10-18 12:39 UTC. Every number below names its source. UNKNOWN stays UNKNOWN.
Sources: S1 = mission records `~/.claude/state/gsd-mission-*.json` on GEX44; S2 = `mission_spend.processed_tokens` and
per-call usage read from 57 transcripts under the four tb-m2 project dirs on GEX44 (de-duplicated by message id);
S3 = `git log` of worktree p17-growth; S4 = worktree `.planning/STATE.md`; S5 = PP source read this session.

## 1-3. Reality, mission/worker/epoch, authority and runway

- Mission `m-e6f3dd0fb70e`: RUNNING, epoch 3, iterations 16, continuations 13 (S1). Owner session f541e3eb (started 09:51 UTC).
  Epoch 1 = 80970e0b, epoch 2 = ab3cd91c (S2). Latest commit 04976e9 "d3b" 14:37 local = 12:37 UTC (S3).
- Authority: C-210 receipt f8587a019af950ff, cumulative 210M. Applied by D6 as `token_estimate` 80,129,978, trip at 2.0 x = 160.26M
  on this mission's own meter (S1). `authority_tokens` is NOT set, `lineage_id` is NOT set (S1).
- Meters (S2): this mission 125,025,968 processed (`processed_tokens`); predecessors 49.74M (46.78M + 2.96M). Cumulative 174.77M.
  Headroom to 210M = 35.2M. `cost_mark.tokens` read 123.2M at the same minute: it lags the true meter by one supervisor pass.
- Runway at the measured epoch-3 rate (26M/h): about 1.35 h to the existing breaker. The breaker already exists and is the safe
  transition (`mission_spend.judge`: "explain the variance and recompute the remaining work before release"). This plan does not
  add a stop; it only observes that the stop is near.

## 4. Phase 24 proof frontier (S4, S3)

- PASS/A: levels a-e seen in sequence on the family-entry ship disc c6144d43 (D2c).
- PARTIAL: hub door route (D2, D2b: door reached, no family load; hypotheses P2 absent, A press, DOL handler untested; marked last slot);
  co-op single-player control (D1: roty 0 vs 90 not distinguishable from pixels); names partial; hair not judged; journal hint icon but
  no text (D3, D3b prereg open). Decision recorded: ship both profiles, hub default.
- Remaining DELIVER items: the worker states 7 (about 3 units each). I did NOT read GAPS.json; the count is the worker's, unverified.

## 5. D2 / D2b / D2c strategy history

| Attempt | Changed dimension vs previous | Result | Causally distinct? |
|---|---|---|---|
| D2 | hub walk to Episode I door | B: room entered, no family level | baseline |
| D2b | area doors inside the Episode I room | B: vault door reached, no load | same entry path (hub), different target: weak |
| D2c | entry path (family-entry profile, new disc) | A: levels a-e | yes (entry path) |
D2b spent a slot on the same causal dimension as D2 after D2 was B; D2c is the change that worked. Cost per attempt is not yet attributed (A1).

## 6. Cost and burn evidence (S2)

Per hour, UTC, de-duplicated: calls, processed M, avg context per call, cache-read share.
- 02h 80 / 15.6M / 194K, 03h 73 / 14.0M / 192K, 04h 53 / 14.4M / 270K (epochs 1-2, orchestrator only).
- Gap 05h-08h: no calls. This is the 4.6 h idle (blocked 04:51 to my wake 09:29 UTC).
- 09h 58 / 12.8M, 10h 220 / 24.0M / 109K, 11h 216 / 27.0M / 125K, 12h (39 min) 128 / 17.2M / 134K (epoch 3).
- Cache reads are 95-98% of every hour; output is 0.1-0.2%. The unit `processed` is therefore carry rent, not price.
- Epoch 3 (09:51-12:36): 71.8M in 2.75 h = 26M/h. 72.5% (52.1M) is 24 subagent sessions of about 2.2M each (about 19 calls at about 110K);
  27.5% (19.8M) is the orchestrating session. All-in about 3.0M per subagent session if one session is one unit (unverified).
- Correction of my own earlier figures: "8M/h" was wrong (it came from a 3M delta over an unmeasured interval). The measured pre-fan-out
  rate was 14-15M/h. What changed at epoch 3 is fan-out: calls/h rose 3-4x while context per call fell to about half. Cost = calls x context.
- Worker-side meter: STATE.md says "47.6M processed over 23 measured units (canary_spend); predecessors about 54M; central total stays under 210M".
  The mission meter says 125.0M and 49.7M. The worker's number covers a subset (it equals about the main sessions only); its under-210M
  projection is therefore unsupported. At the worker's own 2.1M/unit, 21 units add 44M against 35.2M headroom; at 3.0M all-in, 63M.
  Either way the cumulative ceiling is projected to be exceeded. Confidence LOW (n=24 sessions, no quantiles, item count unverified).

## 7. token_estimate semantics (S5: mission_spend.py)

`token_estimate` is an OPERATOR FORECAST of this mission's own processed tokens; the breaker trips at `token_trip_ratio` (default 2.0) x it.
It is not authority, not an actual, not cumulative. `authority_tokens` is the Owner ceiling (trip at authority minus closeout reserve, level
MISSION_AUTHORITY). `lineage_id` / `lineage_token_budget` / `lineage_remaining` exist to enforce a cumulative budget across successor missions.
Consequence: D6 reimplemented predecessor arithmetic and wrote the OWNER ceiling into the operator-forecast field. Cumulative 210M therefore has
no closeout reserve and `authority_kind` reads OPERATOR_ESTIMATE. Fix = A1: D6 writes `authority_tokens` + lineage (existing owner), not a second formula.
Also: owner `heartbeat_at` is 2.07 h old while the mission is productive (S1); heartbeat is not a liveness signal here, the progress fingerprint is.

## 8. Root-cause matrix

| Symptom | Root cause (evidence) | Owner today | Gap |
|---|---|---|---|
| 4.6 h idle | worker ended its turn BLOCKED with "host needs: run /gsd-autonomous --from 20"; `surface_blocked` records the text and nothing consumes it (gsd_mission.py:4882-4889); `unblock` fires only when the host lists the owner LIVE | gsd_mission.supervise | no consumer for a continuation request |
| Status woke it | the only actor that read the host text and answered was me | none | status and scheduling share one person |
| Wake ACK taken as success | `_wake` returns the `continue_worker` ack | decision_plane._wake | no progress deadline |
| Burn 14 to 26M/h | fan-out (24 subagents, 72.5%), cache-read carry | none measures it by class | profiler by class, per-session |
| Ceiling mismatch | D6 wrote token_estimate, not authority/lineage | mission_spend lineage | duplicate formula |
| Worker under-reports | its meter is a subset | worker STATE.md | one meter |
| BLOCKED loop | ask repeated 3x (units) | - | continuation intent |

## 9. Existing owner map (extend, never rebuild)

- Liveness/supervision: `gsd_mission.supervise`, `_note_liveness_incident`, `classify_launch` (gsd_epoch), `progress_fingerprint`, `test_mission_liveness_incident.py`.
- Economics: `mission_spend` (judge, lineage_*, closeout_reserve, stale_usage_guard, session_tree_*), `work_class_profile.py` (settle/forecast/calibrate), `ccr_pgo.py`.
- Hypotheses: `modules/gsd_x/goal/evidence.py` (Hypothesis, HypothesisRefused). Proof strength: `modules/done_gate/strength_ladder.py`.
- Experiment admission (retry novelty, instrument breakers): `vault/specs/experiment-admission.md`, TB `prereg_lint`.
- Decisions: `decision_plane.py` D0-D6. Sleep/wake: `mission_sleep`.
- No existing owner found for: continuation intent, progress-verified wake, per-class cost attribution, economic rotation criterion, proof budget, strategy exhaustion compiler. I did not run the D2A family sweep or the 13-question novelty proof;
  both are scheduled as the first act of A2 and A7 and any FOLD result there overrides this plan.

## 10. Seven loops: one runtime, no new daemon

Liveness, Economic, Context, Resource, Proof, Strategy, Learning are pure functions over events that the supervisor pass already receives.
They are modules called from `supervise`, not processes. The periodic pass stays as anti-entropy.

## 11-16. Liveness, typed progress, continuation intent, verified wake, coverage, sweep

- States: ACKNOWLEDGED, ACTIVATED, PRODUCTIVE, DURABLE_WAIT, STALLED, DEAD, PREEMPTED, UNKNOWN. RUNNING stops meaning productive.
- Typed progress = delta classes (code, proof, obligation, artifact, measurement, resource, decision, transition, commit). Source: transcript usage growth + progress fingerprint + ledger rows; commit is one class.
- Continuation intent: the worker writes a small typed record (mission, phase, completed obligations, desired transition, resources, proof frontier,
  authority needed, invalidators) instead of "host needs: run X". The compiler maps intent to the next Work Unit or a valid wait. A host command text is parsed once into an intent for legacy workers (compat shim, deleted when no worker emits it).
- Wake = SENT, ACK, ACTIVATED, PROGRESS, FAILED. Success only on PROGRESS or DURABLE_WAIT inside a Work-Class activation window. No progress: diagnose binding, executor, continuation, resource, authority, context, host; never repeat the identical wake.
- Coverage invariant: actionable mission has a PRODUCTIVE executor, a PREPARED successor, or a ROTATING state; else raise `liveness_incident` (existing row type).
- Metrics: autonomous liveness ratio, idle actionable time, human wake count, status-to-progress coupling. Fixture: the 04:51-09:29 gap (4 h 38 min, from S1/S2).

## 17-21. Profiler, field types, reforecast, runway, deoptimization

- Profiler = extend `session_tree_report` to attribute by session (main vs subagent), call class, and tool class; unknown stays UNKNOWN. First flamegraph is the table in section 6.
- Field types (renamed, never silently interchanged): forecast, authority, settled_actual, reserved, in_flight, epoch_actual, mission_cumulative, programme_cumulative, external_measured, last_reconciled (with as_of), cost_mark. `token_estimate` is kept as FORECAST and admission code may not read it as authority.
- Reforecast controller: on each settled unit call `work_class_profile.settle` then `forecast` (p50/p80/p95 once n>=3/10), compute residual from the open obligation list, runway = authority - settled - reserve - closeout.
- Runway replaces any fixed "stop near 190M": capital decision only when required residual authority after deflation exceeds remaining authority.
- Deoptimization levers in order: no work, proof reuse, shrink subagent host floor (first-call context is the dominant carry), fewer fan-out units, smaller model per boundary, strategy reduction.
- Economic incident: raised when burn per hour exceeds the Work-Class P80 by evidence-backed margin; epoch 3's 26M/h vs 14-15M/h is the first fixture.

## 22-24. Context loop

Physical rotation (300K) and economic rotation (carry rent over remaining boundaries exceeds rehydration cost) are separate reasons. Measured: epoch 1 avg 194K, epoch 2 192-270K (rose), epoch 3 109-134K per call but 3-4x calls.
So rotation lowered context per call; the cost moved to call count. Regrowth detection: avg context of a fresh epoch re-reaches 80% of predecessor within N calls, then name ingress classes; no blind re-rotation.

## 25-27. Resource loop and GEX44 transport

Observed once: first ssh timed out (kex_exchange_identification), the retry with `-o ConnectTimeout=20` succeeded. One sample is not a policy; A5 records outcomes per attempt and sets
bounded retry (max 3, backoff, then WAIT_RESOURCE) only for the transport error classes seen at least twice. No model in the loop for known classes.

## 28-33. Proof loop, marginal evidence, strategy, partial

- Phase 24 contract: must-have = disc boots (PASS), family chain a-e on ship disc (PASS), PLAY_GUIDE + STATUS_FOR_OWNER generated (PASS, tests 17/17). Open and not yet classified: names, kitten, hair, co-op control, hub door route, journal text. Classification into must-have vs nice-to-have is a product choice that the worker's manifest already partially records; A6 reads it, does not invent it.
- Proof budget per open claim: minimum evidence, candidate strategies, max processed tokens, valid PARTIAL. Budget exhaustion yields PARTIAL / DONE_WITH_LIMITS, never open-ended search.
- Marginal evidence value = expected coverage gain / expected cost; shadow-only first (proxy: claims moved per processed M over the last k units).
- Strategy graph on top of `evidence.Hypothesis`: attempt, changed causal dimension, result. Two zero-progress attempts force a checkpoint; an equivalent third is denied unless a causal delta is declared. D2b would have triggered the checkpoint.

## 34-38. Decision Plane cleanup (verified debts from earlier in this session)

rec alias declared on the surface (only when exactly one recommendation exists); `resolve-transcript` run by the router, not the model; one delivery path (`gsd_mission.deliver_decision` and `consume_bundle` share logic today);
packet versioning with supersession (this plan's own R-200/R-320 table in `decision-plane-master-plan-2026-10-17.md` stays live and must be invalidated); resolutions bind to the active packet fingerprint.

## 39-40. Hygiene and foreign gates

Corrected: `git ls-files` shows 0 tracked pyc in worktree p17-growth (S3). The earlier incident was UNTRACKED `__pycache__` colliding with a fast-forward in tb-m2 main. Fix is a `.gitignore` entry plus a relay preflight that classifies untracked generated files as disposable. `.gitignore` was read only to line 5 (no pyc entry visible); not verified further.
Foreign gates: 8 red `test_gsd_epoch.py` gates (94/102) attributed to commit e6b649e0, never bisected. A5/A10 adds owner, scope, blocking relation per gate; FOREIGN_NONBLOCKING excludes it from this mission's denominator.

## 41-42. TB-FULL self-hosting canary and Phase 24 deopt checkpoint

First stage after approval is NOT a stop. It is the checkpoint: attribute (done above), shrink subagent floor and fan-out, recompile residual, then continue Phase 24. The existing breaker at 160.26M stays as the hard safety.
Each primitive is switched on for this run as soon as it passes its fault-injection test.

## 43. Mode by workstream

Reality Delta EXECUTION (done). Field types, profiler, hygiene, foreign gates, SSH policy, wake verification, alias/delivery cleanup: EXECUTION. Liveness loop, coverage, economic rotation, proof budget, marginal value, strategy compiler: PLAN then EXECUTION.
ULTRA-PLAN: none (no unresolved foundational ownership conflict found).

## 44. Micro-commits

One commit per: field types; D6 -> authority+lineage; profiler; typed progress; continuation intent; verified wake; coverage + sweep; reforecast + runway; economic rotation; transport policy; proof budget; strategy compiler; decision alias; canonical delivery; packet versioning; hygiene; foreign gate scoping; fault tests; knowledge. Pathspec-scoped, never touching foreign staged (`d12b-progress-2026-10-14.md`), GEX44 `gsd_mission.py` dirty, `terminal_slots.json`.

## 45. Staged budget (processed tokens, M; planning estimates, UNMEASURED, confidence LOW; "boundaries x CWS" = my pane at about 150K)

| Stage | Lower | P50 | P80 | P95 | Hard | Boundaries | Avg CWS |
|---|---|---|---|---|---|---|---|
| A0 reality delta (this scan) | spent | spent | - | - | - | about 45 | 120K |
| A1 field types + D6 fix + profiler | 0.8 | 1.5 | 2.2 | 3.0 | 3.0 | 12 | 130K |
| A2 liveness, typed progress, intent | 1.5 | 3.0 | 4.5 | 6.0 | 6.0 | 25 | 150K |
| A3 coverage + verified wake | 1.0 | 2.0 | 3.0 | 4.0 | 4.0 | 15 | 150K |
| A4 context loop | 1.0 | 2.0 | 3.0 | 4.5 | 4.5 | 15 | 150K |
| A5 resource + transport | 0.4 | 0.8 | 1.2 | 1.8 | 1.8 | 6 | 130K |
| A6 proof budget | 0.8 | 1.5 | 2.2 | 3.0 | 3.0 | 10 | 150K |
| A7 strategy | 1.0 | 2.0 | 3.0 | 4.0 | 4.0 | 14 | 150K |
| A8 reforecast, runway, deopt | 1.2 | 2.5 | 3.5 | 5.0 | 5.0 | 16 | 150K |
| A9 decision cleanup | 0.8 | 1.5 | 2.2 | 3.0 | 3.0 | 10 | 150K |
| A10 hygiene + foreign gates | 0.3 | 0.6 | 1.0 | 1.5 | 1.5 | 4 | 120K |
| A11 canary | TB-FULL OPEX, not here | | | | | | |
| A12 reprofile | 0.5 | 1.0 | 1.5 | 2.0 | 2.0 | 7 | 150K |
| A13 vault, FIOS, UKDL, CBR | 0.8 | 1.5 | 2.2 | 3.0 | 3.0 | 10 | 130K |

## 46. Infrastructure CAPEX (separate from TB-FULL)

- Tranche 1 (stops the bleeding): A1, A2, A3, A5, A8, A10. P50 10.4M, hard 21.3M.
- Tranche 2: A4, A6, A7, A9, A12, A13. P50 9.5M, hard 19.5M.
- Both: P50 19.9M, hard 40.8M. Runs in THIS pane under a declared session envelope (`mission_spend.declare`), so no new mission is armed and no capital packet needs a consumer mission.
  The Decision Plane requires a consumer mission for every capital decision; CAPEX in a pane has none, so a packet cannot be compiled honestly now. That is a limitation of D0-D6 and goes on the A9 list.

## 47-48. TB-FULL residual OPEX and capital packet

Remaining authority 35.2M. Residual 44M (worker rate) to 63M (all-in rate), confidence LOW. Probable shortfall 9-28M plus the closeout reserve (1M default). NO PACKET IS COMPILED NOW:
the order is measure, attribute, deoptimize, recompile residual, and only then a packet with an exact number. A8 produces it; if the deflated residual fits 35.2M, no capital is requested.

## 49-50. Approval and return conditions

Approval surface (one reply): `T1` = Tranche 1 (hard 21.3M), `T12` = both tranches (hard 40.8M), `STOP` = nothing.
After approval I act without further turns, except for: a new TB-FULL capital number that A8 shows is genuinely required, a security boundary, an irreversible action, a product/scope choice (for example which Phase 24 claims are must-have), or a human-only external action.

## Fault-injection matrix

One deterministic test per row of the brief's TEST list; the first six (idle actionable mission, worker host-command request, wake ACK only, status query, progress without commit, context high but live set small) land with A2/A3/A4. Each is driven red by a mutant before it counts.

## Final done-gate honesty

DONE needs live TB-FULL evidence: a continuation transition with zero manual wake, a status read that does not move scheduler state, a wake judged by progress, one flamegraph, and one attributed high-burn interval. None exists yet.
