---
id: mission-authority-econ-programme
tier: T3
covers: [mission-authority, authority_tokens, goal-budget-admission, reservation, economic-incident, physical-forecast, reforecast, value-critical-dependency, capital-allocator]
novelty: EXTEND_EXISTING_OWNER -- goal-budget admission (GoalLedger, leases, headroom), econ-contain (tombstone, econ_admission), capital-authority packets, gsd_mission breaker
status: PROPOSED (awaiting Owner approval; inline plan in session 51030f62 is the approval surface, this file is backup)
---

# Mission authority + economic governance programme (2026-10-15)

## 0. Bottom line
The overrun is not a missing subsystem. The estate already has a reserve-before-spend ledger (goal-budget
admission: leases, final-reply headroom, subagent-aware settlement, live canary 2,912,243 of a 3M cap).
GSD missions were never bound to it. `authority_tokens` is read only at launch admission and for AMR
leases; the running breaker trips at `2.0 x token_estimate`, and I set token_estimate = authority, so the
45M mission would have tripped at 90M. The fix: one binding (mission -> goal ledger, cap = authority),
not a new economic system.

## 1. Global economic reality (measured 2026-10-15 14:59-15:06 local)
| | Dataset m-ce2bacd4cbb0 | SurvivalSMP m-28ab89fff085 |
|---|---|---|
| state | RUNNING + owner hold (no relay), worker idle since 14:49:59 | RUNNING, executing 02-05 |
| authority_tokens | 45,000,000 | 155,000,000 |
| spend (topology, processed) | 83,778,584 final | 136,080,690 and rising |
| at hold | 82,289,960; post-hold overshoot 1,488,624 | -- |
| breaker trip before today | 2 x 45M = 90M | 2 x 155M = 310M |
| breaker trip now | unchanged (held) | 2 x 77.5M = 155M (envelope set 15:05, existing mechanism) |
| reserved / in-flight | none (no reservation exists for missions) | none |
| model calls (transcripts, incl. subagents) | 551 | 890 |
| context floor | main 115,870 / subagent ~75,000 first call | main 116,891 / subagent ~77,000 |
| mean / peak context | ~150k / 216,789 | ~150k / 217,020 |
| cache-read share | 0.95 | 0.95 |

## 2. Dataset reality
- Phase 1 COMPLETE and verified (01-VERIFICATION.md 14:26; STATE completed_phases 1, plans 3/3). Residual 0.
- Commits on `mfx/k3-01` (clean tree, pushed to origin): afc43a7 forensics tool (1,015 lines),
  cf1ebb9 field classification + rights knowledge (5,031 lines incl. 2,838 evidence), dd8d262 draft contract.
- Core Files `gsd/mfx-k3-01` 9f383311 = 3 STATE mirrors; worktree still has uncommitted planning artifacts
  (phases/, state.json, RESUMPTION_FILE.md, escalations.json) -- the worker's, not committed by its config.
- Spend by role: gsd-planner (OPUS, 165 calls) 23.3M; gsd-executor x3 (266 calls) 42.2M; researcher x2 6.6M
  (one = Phase 2 research launched 12:27Z, after Phase 1 closed, 3.4M); general 1.8M; verifier 1.2M; main 9.0M.
- Rights, per `evidence/k3-01/forensics.json` for BOTH exports: `state: UNKNOWN`, `authority: UNKNOWN`,
  `assertions: []`, searched = the export + its run record; explicitly not inferred from package.json MIT,
  participant kind, or who ran the bot. Contract `rights-unknown-fails-closed` -> training eligibility: NOT
  ELIGIBLE (fail-closed), state UNKNOWN / REQUIRES_EVIDENCE. No legal conclusion is drawn here.
- Second value-critical dependency (not in the original plan): POPULATION. 2 samples, 1 policy, 1 world
  definition, 1 lineage group. Any split is INSUFFICIENT_POPULATION; even with rights resolved, 2 scripted
  episodes carry no training value.
- Phase dependency: 3 (eligibility), 4 (split), 7 (consumer boundary) are downstream of rights AND population;
  2, 5, 6 (identity/store/seal/validator) are infrastructure whose value exists only if more episodes follow.

## 3. SurvivalSMP reality
- Branch `gsd/survivalsmp-spawn`: 02-04 complete (2f7e36fa 13:38), 02-05 started (b360250a 13:53), executor
  active since 11:43Z (13.5M so far). 02-05 = macro walk (bot reaches every anchor + ravine control) + macro
  renders + COMPLETION rows C/D at BOT_RUNTIME -> it SEALS Phase 2 (P2-SC2). Plan file says
  `estimate.tokens: 75000`; actual plans cost 9.6M-47M (P50 ~25M): planner estimates are ~300x low.
- Remaining authority 18.9M. P(02-05 seals inside it) ~55%. Phase 3 (P50 ~4 plans x 25M = ~100M) is
  infeasible on remaining authority: must not be admitted.
- Defect: the mission is bound to the shared ROOT tree (gen 0), so other panes' commits (netbase
  893157ba..25a3ccd2) move its progress fingerprint. Progress is credited for work it did not do.
- KCOO = kcoo-g1 2026-10-14 CONTESTED on SurvivalSMP CORE vs BACKUP_ONLY; HR-04 = Owner literal phrase for any
  live write. Both gate only the Phase 13 live swap, not anything in this programme. New Owner ruling
  (root 7cb4dddc): "SurvivalSMP spawn is not finished, its adventure region is drawn later".

## 4. 82.3M vs 45M root-cause matrix
| # | cause | evidence | share |
|---|---|---|---|
| R1 | authority_tokens never a runtime trip | gsd_mission.py 3479 (admission), 1983 (AMR lease) only | enabling |
| R2 | breaker trips at 2.0 x token_estimate | mission_spend.py 27,252; estimate = authority | +45M allowed |
| R3 | breaker is async (5-min sweep), hold not reserved | supervise loop; no reservation | detection only |
| R4 | per-call guard opt-in, declared only AT hold | session-budget file declared 12:33:10 | no pre-call stop |
| R5 | guard (non-goal mode) counts main transcript only | state.json tokens 8.8M vs 84M; subagents = 89% | blind |
| R6 | missions never bound to GoalLedger (reservation exists) | goal-budget-admission.md, status done | the fix |
| R7 | no incident path: discovery by my manual status check | no notification row; Owner told by me | observability |
| R8 | forecast from roadmap length, not physics | 25-45M for 8 phases vs 551 calls x 150k for 1 | 10x |
| R9 | value-critical deps (rights, population) not gated | 8 phases planned over 2 samples | premature work |
| R10 | hold does not stop an in-flight subagent turn | 1.49M after hold | bounded residual |
Forecast miss decomposition: calls 15x (assumed ~35/phase, actual 551); per-call ~150k matched; planner on
Opus 165 calls for 3 plans of 35-50 KB (plan bloat); executor 266 calls for ~6k lines incl. tests; research
48 KB; Phase 2 research after the hold = premature.

## 5. Authority owner map
| level | owner | status |
|---|---|---|
| Programme | capital-authority packets (owner-capital WU-OC1, branch oc1) | PARTIAL / BRANCH_ONLY (verify A0) |
| Goal | GoalLedger `<state>/goal-budget/<goal>` | LIVE, only for goal-bound sessions |
| Mission | `authority_tokens` | ADVISORY (launch admission only) |
| Mission (running) | cost breaker 2 x token_estimate | LIVE async; contradicts authority (DUPLICATED) |
| Phase / Plan lease | none; plan `estimate.tokens` | MISSING / ADVISORY, ~300x low |
| Work unit | route admission (`admit`) | LIVE at launch only |
| Model call | session_budget_guard (PreToolUse), cognitive_admission (Agent edge), econ_admission (UserPromptSubmit) | LIVE; mission workers unbound |
| Reservation / settlement | GoalLedger leases, headroom, watermark settle | LIVE goal mode only |
| Holds | owner_hold kind=cost (stops worker + guard stop=1) | LIVE |
| Supervisor / watchdog | 5-min sweep; progress fingerprint | LIVE (monitor); fingerprint credits foreign commits on shared root |
| Incident bus | ledger rows only | SHADOW (no consumer, no Owner path) |

## 6-8. Synchronous Mission Authority, reservation, overshoot contract (Stage A)
Earliest reliable boundary (RQ1): the model request itself is not hook-interceptable (host limit). Earliest
enforceable points, in order: (1) supervisor launch/relay (no `claude --bg` for a spent mission);
(2) UserPromptSubmit / turn-continuation (econ_admission); (3) PreToolUse on EVERY tool incl. subagent calls
(they carry the parent sid); (4) Agent spawn reservation. An admitted call is paid by the request after it,
so the guard renews before the call when `tokens - base + context > lease`.
Design: at `arm`, the mission gets goal `mission:<id>` with cap = authority_tokens (lowering allowed, raise
only via Owner `goal-declare --owner`); at every launch/relay the supervisor writes
`session-budget-<sid>.json {goal: mission:<id>}` BEFORE the worker starts, so goal mode (subagent-aware,
fail-closed, headroom, leases, LEAKED-counts-until-settled) governs it from call 1. The 2 x estimate breaker
becomes `min(authority, ratio x estimate)`; supervisor stays reconciliation/defence-in-depth. Closeout
reserve = 1 per_call per live session + an explicit `closeout_tokens` (default 1M) that productive leases
cannot consume. Max overshoot contract: <= one admitted reply per live session (measured canary residual)
+ outstanding agent holds, which are pre-reserved; target <= 0.5M per mission, measured by canary.
Usage lag: settlement is from transcripts the guard reads incrementally; a lagging reading only delays a
renew, and the lease bounds what can run before it. Supervisor offline: the guard is in-process, unaffected.

## 9. Economic Incident Bus (A2)
Extend the ledger: `economic_incident` rows (AUTHORITY_EXHAUSTED, RESERVATION_EXHAUSTED, FORECAST_INVALIDATED,
MARGINAL_PRODUCTIVITY_COLLAPSE, VALUE_GATE_BLOCKED, ACCOUNTING_UNKNOWN, RECOVERY_REQUIRED) -> hold (existing)
-> settle -> incident receipt (mission, level, authority, settled, reserved, overshoot, last admitted
boundary, cause, closeout, next safe action) -> Owner packet via the existing capital-authority packet format
+ PushNotification only when new authority is needed. No new daemon: the sweep and guard emit.

## 10-12. Physical forecast, feasibility, continuous reforecast, residual compiler (B1-B2)
Calibration store `<state>/econ-calibration/<work_class>.jsonl` filled by the transcript autopsy
(calls, floor, mean/peak context, processed, by agent role) per closed plan. Feasibility at arm/admit/plan
start: P50/P80/P95 = calls x per-call from history; INFEASIBLE when P50 of the next sealable milestone >
remaining authority; plan `estimate.tokens` is ignored as a forecast (it is output-only). Reforecast after
every plan SUMMARY commit or >1.5x variance; residual compiler picks the largest milestone whose P80 fits.

## 13-14. Marginal Cognitive ROI + governor (B3)
Semantic progress receipt per plan = success criteria / done-gate rows moved to VERIFIED (not commits, not
lines). ROI = rows moved per 10M. Governor: CONTINUE / SHRINK_SCOPE / RECOMPILE / WAIT_ON_DEPENDENCY / STOP,
recommend-only above authority, enforce hold only on collapse (2 consecutive windows with zero rows moved).
Also fixes the shared-root fingerprint: progress counted only from paths/commits the mission wrote.

## 15-16. Value-Critical Dependency Gate + dataset rights gate (B4)
Generic: a roadmap may declare `value_gates: [{id, unlocks: [phases], state: KNOWN|UNKNOWN|REQUIRES_EVIDENCE}]`;
admission of a phase whose unlock set includes an unresolved gate -> VALUE_GATE_BLOCKED unless the plan
directly resolves the gate or the Owner accepted the risk. Dataset instance: gates `rights` and `population`
(both UNKNOWN today) block phases 3,4,7 and make 2,5,6 premature-work-taxed.

## 17. Technical Capital Allocator (B5)
Deterministic packet (no agent): per mission remaining authority, next milestone P50/P80, P(fit), blocker,
ROI trend, recommended action. Never moves capital between goals; the Owner moves it.

## 18. Dataset first useful sealed version
PARKED NOW. Release conditions: Stage A live; rights gate resolved by an Owner assertion with authority (or
explicitly accepted as eval-only); population plan decided; next milestone P80 <= approved authority.
First useful version: v0 "provenance-only": both exports sealed with identity, hashes, provenance,
rights=UNKNOWN, eligibility=NOT_ELIGIBLE, split=INSUFFICIENT_POPULATION + unlock condition, one consumer.
Useful as a pipeline proof only. Training-useful version needs rights + N episodes (local, deterministic
generation via tools/live-episode.js, zero model tokens per episode). Forecast for v0 executed LEAN (main
thread, no Opus planner, phases 2+5+7 collapsed): P50 18M, P80 28M, P95 40M. Under GSD-autonomous as run:
P50 ~150M for v0, several hundred M for 8 phases. Recommendation: stay parked until the Owner answers the
two dependency questions (Section 25).

## 19. SurvivalSMP next sealable milestone
02-05 (seals Phase 2: walked and rendered macro terrain, rows C/D at BOT_RUNTIME). Continue it inside the
existing 155M; breaker now trips at 155M. Phase 3 NOT admitted (infeasible). After 02-05 the mission holds
with a capital packet. No new authority requested now.

## 20. Context / call autopsy (both)
Floor 75-117k per call before any work (rules, tools, memory, CLAUDE.md stack); mean ~150k; 95% cache-read.
Calls per plan: dataset ~90-170, SurvivalSMP 69-309. Biggest levers: Opus planner (23M for 3 plans), plan
bloat (35-50 KB plans re-read every executor call), executor tool choreography. Reuse CCR v4 (B5 tool-output
projection -77% carry, thinking-carry finding) rather than a new compiler.

## 21. Mode by workstream
A0 EXECUTION (mostly done) | A1 PLAN->EXECUTION (owner clear: goal-budget admission) | A2 EXECUTION |
B1 EXECUTION | B2 EXECUTION | B3 PLAN->EXECUTION (metric) | B4 PLAN->EXECUTION | B5 EXECUTION (deterministic;
no ULTRA: no capital-ownership ambiguity, capital never moves without the Owner) | C1 EXECUTION |
C2 EXECUTION | D EXECUTION. ULTRA-PLAN: none needed.
Execution vehicle: Stage A runs LEAN in this pane (main thread + <=2 Sonnet subagents), itself bound to
goal `econ-authority-a` with the approved cap (self-hosting from call 1). A Ralph mission is armed only
after A1 is live, so the first mission under the new enforcement is this programme's own Stage B.

## 22. Micro-commits (PP worktree branch `econ/mission-authority`, pathspec-scoped; shared tree untouched)
1 incident receipt + autopsy tool (A0) | 2 arm binds mission goal, cap=authority (A1) | 3 launch/relay writes
goal binding before worker start (A1) | 4 breaker min(authority, ratio x est) (A1) | 5 closeout reserve (A1)
| 6 tests V-MA-* incl. fault injections (A1) | 7 live canary receipt (A1) | 8 economic_incident rows + receipt
+ packet (A2) | 9 calibration store + feasibility (B1) | 10 reforecast + residual compiler (B2) | 11 ROI receipt
+ governor + own-path fingerprint (B3) | 12 value gates (B4) | 13 allocator packet (B5) | 14 dataset gate
receipt + packet (C1, MFX branch) | 15 SurvivalSMP reforecast (C2) | 16 KV/FIOS/UKDL/CBR (D).

## 23. Budget by envelope (processed tokens, lean execution; per call ~150k measured)
| env | SLB | low | P50 | P80 | P95 | hard | conf |
|---|---|---|---|---|---|---|---|
| A0 reality + incident | 1.0M | 1.5M | 2M | 3M | 5M | 3M | high (mostly spent in this scan) |
| A1 sync mission authority | 4M | 5M | 9M | 13M | 18M | 14M | medium |
| A2 incident bus + closeout | 2M | 3M | 5M | 7M | 10M | 7M | medium |
| B1 physical forecast (min) | 2M | 2.5M | 4M | 6M | 9M | 4M (min slice now) | medium |
| B2 reforecast + residual | 2M | 3M | 5M | 7M | 10M | later | low |
| B3 ROI + governor | 2M | 3M | 6M | 9M | 13M | later | low |
| B4 value gate | 2M | 3M | 5M | 7M | 10M | later | low |
| B5 allocator | 1M | 2M | 3M | 5M | 7M | later | medium |
| C1 dataset self-host | 0.5M | 1M | 2M | 3M | 5M | later | medium |
| C2 SurvivalSMP self-host | 0.3M | 0.5M | 1M | 2M | 3M | later | high |
| D KV/FIOS/UKDL/CBR/CI | 2M | 3M | 6M | 9M | 13M | later | medium |
Total programme P50 ~48M, P80 ~71M. Capital law: one incident was 37.3M (A1 incident 2026-10-07 was 22.3M);
the immediate slice (P50 20M) pays back on the next overrun it prevents.

## 24. Minimum immediate capital request
Programme authority 30M hard = A0 3M + A1 14M + A2 7M + B1-min 4M + closeout/recovery reserve 2M.
Enforced on this pane by goal `econ-authority-a` (cap 30M) before the first edit. B2-B5, C1, C2, D are
reforecast after A1's canary and requested as a second slice.

## 25. Owner approval surface (see inline plan)
