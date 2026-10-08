status: APPROVED (Owner "y", 2026-10-08 ~20:20Z, pane 5d6a315c) -- D-A plan as written, D-B host = this laptop, D-C stop for an Owner cap decision after E4b
covers: [watched-verdict-contract, runtime-convergence, bridge-retirement, receipt-driven-successor, coordinator-extinction, context-floor, call-compression, proof-transaction, control-plane-tax, e3g-close, e3c, e4, t2-reconciliation, t3-recompile]
supersedes-chain-of: vault/plans/expected-completion-E3R-plan.md (its Chain step 4 = the bridge; retired here)

# Cost-collapse convergence -- one verdict contract, no coordinator, smaller floor

## Reality Delta (measured 2026-10-08 ~20:10Z; host = this Windows laptop, NOT GEX44 -- no GEX44 component exists)
- E3G m-cf396e288bda: BLOCKED (worker 327d5e92 asked the host: fix V-SBG-LATENCY or exclude it, rerun drills d2-d5 and
  4 suites "before arming E3C"). RECEIPT-E3G.json PARTIAL: guard call-checkpoint + packet receipt path landed (0ea29fc7),
  SBG 20/21 (V-SBG-LATENCY red, pre-existing: guard rewrites an id list of up to 20000 ids every tool call, 110-575 ms),
  drills 1 KILLED / 4 CONTROL_INVALID, 4 suites not run. Metered 35 calls / 5,742,132 vs target 4.5M, safety 5.52M
  (receipt self-reported "~29 calls, tokens not metered": the meter wins).
- E3C NOT armed (no mission record names WU-E3C). No worker running for this program. Only this pane is hot.
- Live sweep runs C:\Users\User\.claude\skills\claude-power-pack (feature/knowledge-acquisition). None of T1/T2/E1-E3G
  is on it (33 worktree-only commits). Live gsd_mission.py:1559 and :1576 accept only "ADMISSIBLE"; worktree :1631/:1666
  accept ("ADMISSIBLE","WATCHED"). A concurrent writer landed 1dad0c27 on live gsd_mission.py at 20:00Z today.
- Mission records carry the writer's code_id (gsd_mission.py:46,322): the version stamp exists, nothing compares it.
- Goal cost-collapse: cap 69,774,423 / used 50,651,362 (settled 43,904,377 + open 6,746,985) / remaining 19,123,061.
- Floors (route-floors.json): top-level-worker 110,835 (g 2310, calls_err 0.354 n=2); slim-t2 13,507; slim-t1 8,848
  (no g, no calls_err).

## Where the money went (sessions metered from transcripts; basis = usage fields)
Workers: E1 7.09M/42 calls, E2 5.80M/38, E3 7.62M/45, E3R 2.99M/22, E3G 5.74M/35 = 29.24M vs ~20.9M forecast (+40%).
Coordinators: this pane 19.66M/106 calls, recovery pane c0338e7b 8.31M/44 = 27.97M, budgeted 0.
=> control-plane cognitive tax = 28.0 / 57.2 = 49% of program spend (MEASURED). Manual handoffs: 4 of 6
(E1->E2 arm, E3->E3R recovery, E3G launch, E3G->E3C now).
Worker split: fresh floor ~111k of a ~165k mean context = ~67% floor rent (~19.6M), ~33% growth (~9.7M).
Forecast miss is call count (+25..+35% per unit), not per-call growth (model within +-7% when n is known).
Per-category split of calls (proof / status / repair / reads) UNMEASURED -> E3C2 measures it.
Calls per verified state transition: ~12-15 (35-45 calls per 2-3 commits+receipt) ESTIMATED from git log.

## Why E3G sat admitted and unlaunched ~90 min
admit ran worktree code and wrote verdict WATCHED into the SHARED mission record; the live sweep (older code, same
state dir) read it, its admission_refusal knew only ADMISSIBLE, and it logged "not admitted" every 5 min to a log
nobody reads. Two code versions, one record, no version check, refusal indistinguishable from a normal deferral.
Class: ADMISSION_SUPERVISOR_SEMANTIC_DIVERGENCE (contract skew through shared state).

## WATCHED canonical contract
WATCHED = launch PERMITTED, with: session envelope applied exactly as ADMISSIBLE; call-trajectory checkpoint (E3G);
EAC reforecast at planned-calls exhaustion and at warn (E2, wired live by E3C1); receipt required. Back to ordinary:
never mid-unit (a verdict belongs to one admission). Escalation: EAC > target x 1.25 or flat progress -> CHECKPOINT
(owner hold). ESCALATE/RECOMPILE = not launchable. One constant LAUNCHABLE_VERDICTS in route_admission.py, imported by
every gsd_mission site. Unknown verdict or record code_id the sweep does not know -> sweep row action
"verdict_unknown" with both code_ids, surfaced in `status` like BLOCKED -- never a silent "not admitted".

## Units (fresh packet workers; this pane ends after WU-0)
WU-0 (this pane, <=5 calls): commit this plan APPROVED; packet WU-E4a + route; arm E4a --supersedes m-cf396e288bda
  --depends-on m-cf396e288bda (E3G metered 5.74M > 4.5M -> ESCALATE by design; the Owner y on this plan is the recorded
  answer, as for E3R); admit. Forecast E4a 15 calls top-level: expected 1.9M, safety 2.7M < warn 3.75M -> ADMISSIBLE ->
  the LIVE sweep launches it. No bridge used. Pane ends (SAFE_TO_FORGET); no coordinator from here.
E4a convergence slice (live tree, pathspec, rollback tag; merge around 1dad0c27): LAUNCHABLE_VERDICTS contract + the
  5 call sites + verdict_unknown/code-skew surfacing; nothing else. Champion stays the live estimator, so no other live
  mission changes behaviour. Gates: worktree+live test_gsd_mission_admission, test_gsd_mission_envelope, new V-VERDICT-*
  (both poles; drill: remove WATCHED from the live set -> red). Last act: write E3C1 packet, arm+admit E3C1 (WATCHED
  expected) and DO NOT launch it -> WATCHED PRODUCTION CANARY = the live sweep launches it unaided.
E3C1 (slim-t2 canary; fallback top-level recorded with reason): guard latency (id list -> offset/high-water, st.offset
  exists), rerun E3G drills d2-d5 + 4 suites, diagnose d4; wire EAC usage at the sweep call site; recalibrate from E3 and
  E3G pairs (n=4); promotion gate (WU-E3C s3). Receipt; arm E3C2.
E3C2: receipt-driven successor -- a chain manifest (vault/specs/packets/chain-cost-collapse.json: unit, packet, route,
  depends_on) read by the sweep: predecessor terminal + green receipt -> sweep arms/admits/launches the next unit;
  red or absent receipt -> owner hold surfaced (fail closed). Proof transaction: packet `proof:` header -> one
  deterministic runner writes a compact proof receipt (only reds return to the model). Call autopsy by category
  (test/git/read/edit/status/repair) + calls per verified transition + coordinator tax (goal ledger minus mission
  workers) in mission_spend autopsy. Canaries: receipt handoff, proof transaction, call compression (before/after on
  the same suite list).
E4b land + ratchet: cherry-pick the rest onto live (rollback tag, guard diff merged, concurrent writers respected),
  smoke from live, D3 ACTIVE; bridge retirement = no packet/plan contains `supervise --actions-only` and a Cognitive CI
  check enforces it; KV + UKDL (HR: one verdict contract across admission and supervision; worktree semantics are not
  production until live converges; a bridge carries its retirement gate) + CBR + /liveness. Canary 12 + bridge
  retirement canary: the next unit launches through the live sweep only.
T2 reconciliation: deterministic (receipts already hold actuals) -> calibration row, no model unit.
T3a/T3b..T7: recompiled from post-E4 economics (slim floor if the canary held). Work extinction first.

## Budget (expected / safety; top-level fallback in brackets)
WU-0 ~1.2M (this pane at 208k ctx). E4a 1.9 / 2.7. E3C1 1.1 / 1.6 [3.5 / 5.0]. E3C2 1.1 / 1.6 [3.5 / 5.0].
E4b 1.5 / 2.2 [4.4 / 6.3]. Total 6.8M [14.5M] of 19.12M remaining. T3a..T7 (~43M at the old economics) does NOT fit
the 85M program cap: after E4b, recompile T3-T7 with measured new economics and STOP for an Owner cap decision
(raises are Owner-TTY only by construction). No unit borrows from the goal remainder; each carries its own envelope.

## Rollback / deopt
E4a and E4b: rollback tag on live before the first cherry-pick; `git reset` to it is the revert (Owner-confirmed only if
other writers landed after it -- then revert commits instead). CPP_ROUTE_ADMISSION=off stays the kill switch.
If E4a fails its gate: the one-mission worktree launch (TEMPORARY_DEOPT, owner = this plan, expiry = E4a green) may be
used once more and is recorded in the receipt.
