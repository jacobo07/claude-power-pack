# Roadmap: Expected Verified Completion engine repair (evc workstream)

Plan of record: `vault/plans/economic-engine-repair-MASTER-PLAN-2026-10-10.md` (PP 88af526e). Owner approval: "y"
2026-10-10 ~11:00 UTC to "APPROVE EVC" (boundary 1). This approval is also the D12 D-C cap decision: the cost-collapse
goal cap (8.0M left) is superseded by this programme's envelope.
Adopts, never duplicates: backlog D12 (`vault/plans/deferred-backlog.md` §D12; specs `expected-completion-admission.md`
and `cost-collapse.md` in `C:\Users\User\Apps\pp-cost-collapse`, branch `cost-collapse/main`, T2 = 2b5b0ea5), the `dgl`
lease-epoch work on branch `dgl/durable-goal-lease` (worktree `C:\Users\User\Apps\pp-dgl`; NOT on live HEAD: W1b V-gates
c5f22af9, W2 closed-lease fence 31f9b5f4 in `hooks/lib/goal_binding.js`), `tools/gsdx_reforecast.py` (610808c5, branch
`gsdx-factory/v2` only; cherry-pick that commit, never merge the branch),
`hooks/session_budget_guard.js`, `tools/mission_spend.py`, `tools/usage_index.py`, `tools/cost_to_completion.py`,
`tools/mission_steward.py`, `tools/gsd_mission.py`.

## Reality at start (measured 2026-10-10 10:41 UTC; transcripts deduped by message id, subagents included)
- intent/order m-cd548e5d2ada worker ec66dcff: 371.0M processed, 2,294 calls (91 % in subagents), cache read 94.6 %,
  output 0.9 %, mean ctx/call 160k, stopped by HTTP 429 weekly limit at 06:25 UTC (resets 2026-10-13 02:00 UTC), NOT by the hold.
- Clock A m-5709490db84c worker e0cd1dbb: 58.4M, BLOCKED on founder items, Phase 10 done (TUA-X bac6b195e).
- Clock A old m-f24648f187c5 (HALTED) worker be97307b: 245.8M.
- Defects proven: estimator clamp [1M,15M]/2; hold message froze 18.2M (stale); hold blocks relay only; session guard is
  opt-in and counts the MAIN transcript only (32.0M seen vs 371M real, 11.6x undercount); 24 h judged from mission created_at;
  per-call fresh floor ~115k. (Corrected 2026-10-10 self-deflation: a price table DOES exist in `tools/usage_index.py`,
  which prices every usage category per model; Phase 1 reuses it.)
- U0 containment DONE in the arming pane: deny budgets declared for ec66dcff and e0cd1dbb
  (`~/.claude/state/session-budget-<sid>.json`, stop=1); drill via `decide()` = deny for both, control allow.
  Do NOT lift these budgets. Product continuation of Clock A / intent-order is OUT of scope until boundary 2.

## Operating constraints (every phase)
- Work tree: `C:\Users\User\Apps\pp-evc`, branch `evc/main` (from 88af526e). All development and tests here.
- Landing to live (`C:\Users\User\.claude\skills\claude-power-pack`, `feature/knowledge-acquisition`, shared with peer panes and
  Ralph missions, ~900 dirty paths that are NOT ours): only in Phase 9, by cherry-pick of evc commits, after a rollback tag
  `evc-pre-<phase>`; commit by explicit pathspec; verify `git log -1 --format=%s`. Never reset/clean/restore/stash/amend/force.
  Never push. Before editing a live file, diff live vs 88af526e for that path; if a peer changed it, merge, never overwrite.
- Do not edit TUA-X, the Clock A or intent-order worktrees, or their mission records (read only).
- Owner is not asked mid-run. Anything needing the Owner goes to `vault/plans/evc-owner-bundle.md` and the run continues.
- Unit of account everywhere = processed tokens split into input / cache_write / cache_read / output, deduped by message id,
  synthetic rows excluded, subagent transcripts INCLUDED. Three economies reported separately: processed, API-equivalent
  (sourced price table, else UNKNOWN), cognitive composition.
- UNKNOWN is never zero; a partial monitor is never current; missing profile is never calibrated.
- Every phase commits an EVIDENCE.md with: Product Delta, Intelligence Delta, gates run (command + exit), processed tokens
  spent by the phase (measured, not estimated), and the forecast-vs-actual for that phase once Phase 4 exists.
- Agents only for independent semantic novelty; never for waiting, polling, arithmetic or relay.

## Budget (processed tokens, whole programme) — SELF-DEFLATED 2026-10-10 (Owner "y" to PP 836c1121)
Sunk before this budget: 2.64M (epoch-1 worker 65aa58ea, frontier ~0; it produced only phases/01-usage-truth-plane/01-CONTEXT.md).
lower 28M · P50 41M · P80 52M · P95 62M · **hard stop 65M, ENFORCED** by `mission_spend.judge` (token_estimate 32.5M x
token_trip_ratio 2.0). There is no other limit: the earlier "hard stop 160M" was prose, and the enforced value was 170M; both
are retired. Coordinator share <= 20 %. Confidence EXPLORATORY until Phase 8.

### Deflation dispositions (override the phase criteria below wherever they conflict)
| Phase | Disposition | Price |
|---|---|---|
| 1 Usage truth | SHRINK: reuse the `usage_index.py` price table; build only the freshness watermark + stale-snapshot guard in hold/status text + 429 detection | 3M |
| 2 Autopsy/forecast | LAND cost-collapse T1+T2 (f3b503e6, 2b5b0ea5) by cherry-pick; run the autopsy on the 2 named missions | 2M |
| 3 Profiles/confidence | SHRINK: `tools/cost_to_completion.py` becomes the primary estimator; clamp retired; confidence states + miss taxonomy only | 4M |
| 4 Distributions/reforecast | LAND 610808c5 alone, then add the P50/P80/P95 output + DRAINING edge | 4M |
| 5 Spend capability | SHRINK: hold/suspend writes the guard budget (the U0 mechanism, measured to work on 65aa58ea at 13:31) + subagent accounting + canary | 4M |
| 6 Durable goal | LAND dgl W1b+W2 only (backlog D15 keeps W3-W8 parked) + the age-boundary gate | 4M |
| 7 Fresh-floor cut | KEEP (largest lever). The global `~/.claude/CLAUDE.md` (39,812 chars, 292 lines vs its own <100-line rule) goes to the owner bundle as a PROPOSAL, never edited by the run | 8M |
| 8 Backtest | SHRINK to 2 traces (Clock A old m-f24648f187c5, intent/order m-cd548e5d2ada) + 1 holdout | 4M |
| 9 Landing/canary | KEEP the landing; the self-forecast merges into Phase 11 | 2M |
| 10 Ratchet | SHRINK to KV/UKDL entries; global no-opt-in defaults DEFERRED to backlog | 2M |
| 11 Recompile + STOP | KEEP | 4M |

Execution rule learned in epoch 1: the worker must NOT call EnterWorktree. Its cwd already IS this worktree, and the
host's "Entering worktree" permission prompt blocked the worker even with `--allowedTools EnterWorktree`.
From Phase 4 on, the programme's own remaining budget is reforecast by the new engine at each phase boundary and written
to `vault/plans/evc-forecast.json` (self-hosting). If quota (Phase 1 measurement) cannot cover the remaining P80, stop at
the next phase boundary and write the residual to the owner bundle.

## Phases

- [ ] **Phase 1: Usage truth plane** - fresh, complete, categorised spend with a freshness watermark; no stale figure shown as current
- [ ] **Phase 2: Autopsy and obligation forecast** - land cost-collapse T2 here and extend it to subagent-inclusive accounting
- [ ] **Phase 3: Work-class profiles and confidence** - profiles with evidence maturity, miss taxonomy, invalidation; the clamp retired as primary
- [ ] **Phase 4: Distribution forecast and live reforecast** - lower/P50/P80/P95/ceiling, reforecast on triggers, predictive lease edge
- [ ] **Phase 5: Spend capability and precise lease states** - hold/suspend reaches the live worker; breaker becomes containment
- [ ] **Phase 6: Durable goal across execution leases** - the 24 h process cap no longer forces a new semantic mission
- [ ] **Phase 7: Fresh-floor cut** - cost-collapse T4: measure and cut the ~115k per-call floor for packet workers
- [ ] **Phase 8: Historical backtest** - calibration evidence on real traces with a holdout
- [ ] **Phase 9: Live landing, canary and self-hosting** - land on live with rollback tags; canary; the engine forecasts its own residual
- [ ] **Phase 10: Ratchet** - Knowledge Vault, UKDL, CBR promotions and retirements; global defaults, no opt-in
- [ ] **Phase 11: Recompile Clock A and intent/order, final plan, STOP** - boundary 2

## Phase Details

### Phase 1: Usage truth plane
**Goal**: Every spend figure the runtime shows carries its freshness, its categories and whether a live worker can still add to it.
**Success Criteria**:
1. One reader (extend `mission_spend.py` / `usage_index.py`, no new owner) returns per session AND per mission tree (main + subagents)
   input/cache_write/cache_read/output, call count, last-call timestamp, data age. Reproduces 371.0M / 58.4M / 245.8M within 1 %.
2. Hold, breaker and status text never print a frozen figure as current: they print `measured X as of T (age A); worker LIVE ->
   total current UNKNOWN, >= X` when an attributed worker is alive. Gate drives the stale branch red/green.
3. A sourced price table (official Anthropic pricing page, retrieval date recorded) yields API-equivalent cost per category;
   absent model -> UNKNOWN, never 0.
4. Quota state: the reader detects provider 429 / weekly-limit events per worker and reports reset time; current quota feasibility
   is UNKNOWN unless measured.
5. Gate `tools/test_evc_usage_truth.py` exit 0.

### Phase 2: Autopsy and obligation forecast
**Goal**: The autopsy explains where a mission's tokens went, and the forecast prices obligations, not phases.
**Success Criteria**:
1. Cost-collapse T2 (2b5b0ea5, `mission_spend autopsy` + `forecast`) ported onto evc/main with its V-AUTOPSY gates green.
2. Autopsy runs on m-cd548e5d2ada and m-f24648f187c5: per-subagent calls, processed, cache r/w, first/max/mean ctx, tool mix,
   stall windows; cognitive composition (novelty / implementation / reads / context rent / control plane / proof / repair /
   rediscovery / closeout / UNKNOWN) where evidence permits, else UNKNOWN.
3. Phase count x average survives only as `old_execution_reference`.

### Phase 3: Work-class profiles and confidence
**Goal**: Forecasts come from Work-Class profiles that know how mature their evidence is and lose authority when they miss.
**Success Criteria**:
1. Work classes reuse existing vocabularies (route floors, `work_class` in baseline_resolved); profiles carry fresh floor, ctx
   trajectory, calls distribution, processed distribution, repair/proof/closeout tails, sample count.
2. Confidence state machine UNKNOWN/EXPLORATORY/PROVISIONAL/CALIBRATED/DEGRADED/INVALIDATED; an order-of-magnitude miss
   invalidates unless an isolated anomaly is proven; three comparable material misses invalidate; an INVALIDATED profile cannot
   admit large work (fallback conservative or bounded measurement tranche).
3. Miss taxonomy (CALL_COUNT, CONTEXT_GROWTH, WORK_CLASS_MISCLASSIFICATION, PROOF_TAIL, CLOSEOUT_TAIL, REPAIR, CONTROL_PLANE_LEAK,
   SEMANTIC_SCOPE, STALE_USAGE_TRUTH, RESOURCE_ANOMALY, PROVIDER_BEHAVIOR_CHANGE, PROFILE_TRANSFER, UNKNOWN), mapped to FIOS.
4. The [1M,15M]/2 auto envelope is no longer the primary estimator (kept only as a labelled emergency fallback).
5. Hierarchical resolution: global class prior -> project family -> mission -> live worker, confidence-weighted.

### Phase 4: Distribution forecast and live reforecast
**Goal**: Every material forecast is a calibrated distribution that recompiles while the work runs.
**Success Criteria**:
1. Lower/P50/P80/P95/ceiling with confidence; sample too small -> WIDE/UNKNOWN stated.
2. Context-growth aware: per-call cost = floor + context image along the trajectory; E3C2 EAC usage wiring (the call site that
   passes no usage) fixed.
3. Reforecast triggers: semantic milestone, ctx growth, miss, repair, proof failure, model change, rotation, new obligation,
   usage refresh. Output in the mission record + ledger.
4. Predictive lease edge: when spent + P95 remaining + protected tail exceeds authority, the mission enters DRAINING before
   the hard breaker. Gate drives it.

### Phase 5: Spend capability and precise lease states
**Goal**: A revoked or suspended lease stops the live worker's next substantive boundary; PAUSED never hides spend.
**Success Criteria**:
1. States ACTIVE / RELAY_HELD / DRAINING / SUSPENDED / WAITING / HALTED (or stronger existing names), with Owner-facing text
   that states whether spend can continue. RELAY_HELD is never displayed as paused.
2. Setting SUSPENDED (or a cost-breaker trip) writes the worker's session budget (or goal lease close) so the guard denies the next
   gated tool call, Agent launch included; in-flight provider call marked as exposure and allowed to finish.
3. The guard accounts subagent transcripts (fixes the 11.6x undercount).
4. Breaker = containment fallback; the simple 2x steering is retained only as labelled emergency fallback.
5. Canary drill on a throwaway mission: revoke -> next boundary refused (observed in a real worker transcript), control allowed.

### Phase 6: Durable goal across execution leases
**Goal**: Process TTL is an execution-lease property; the semantic goal continues through epochs.
**Success Criteria**:
1. Audit of DEFAULT_MAX_HOURS=24 (origin, what it protects: RAM, staleness, context); preserve the protection.
2. A relay past the TTL continues the same goal in a new lease epoch (dgl GoalLedger lease epochs), no `--supersedes` re-arm.
3. Predictive time lease: before expiry, if expected remaining > safe remaining time, checkpoint and rotate.
4. Gate: a goal crossing the age boundary continues without a new mission id.

### Phase 7: Fresh-floor cut
**Goal**: The per-call floor (~115k) is measured by component and the CPP-controllable part is cut for packet workers.
**Success Criteria**: cost-collapse T4 criteria: measured first-call ctx before/after on a real packet worker; hooks suites green.

### Phase 8: Historical backtest
**Goal**: Calibration evidence before claiming repair.
**Success Criteria**: For Clock A old/new, intent/order, DWS, recon-factory, gsdx-pcc and KSR/KME where traces exist: forecast
from past-only data vs actual; bias, P80/P95 coverage, miss class; at least one holdout class; leakage stated.
Results in `vault/plans/evc-backtest.md` + machine JSON.

### Phase 9: Live landing, canary and self-hosting
**Goal**: The engine runs on the live install and governs its own remaining work.
**Success Criteria**: rollback tag; cherry-pick evc commits onto live by pathspec; live gate suites green (test_gsd_mission,
envelope, owner_hold, session_budget_guard, verdict contract, evc gates); live canary of Phase 5 drill; `vault/plans/evc-forecast.json`
produced by the new engine; legacy flat estimate no longer the primary controller (gate).

### Phase 10: Ratchet
**Goal**: Proven behaviour becomes the default for every compatible future project.
**Success Criteria**: Knowledge Vault entries for each proven failure motif; UKDL hard/process/trap candidates; CBR promotions
and retirements (phase-average estimator, flat-call assumption, ambiguous PAUSED, manual multiplier, 2x steering,
process-lifetime = mission-lifetime, stale-spend reporting) with evidence; fresh-project inheritance check; `tools/evc_done.py` exit 0.

### Phase 11: Recompile Clock A and intent/order, final plan, STOP
**Goal**: Price the remaining verified semantic outcome of Clock A and intent/order with the new engine; then stop.
**Success Criteria**:
1. Read-only refresh of both programmes (TUA-X worktrees `.claude/worktrees/brand001-clock-a` and `brand001-intent-order`,
   their ROADMAPs, commits, founder packet); residual compiled into obligations classified DONE / NO_WORK / DETERMINISTIC /
   KNOWN_TRANSFORM / BOUNDED / NOVEL / PROOF_ONLY / OWNER_ONLY / WAITING.
2. `vault/plans/evc-final-remaining-plan.md`: per work unit objective, work class, strategy, dependencies, proof, model tier,
   interrupts, calls, ctx profile, lower/P50/P80/P95/ceiling, confidence, provenance; token budget split (Clock A, intent/order,
   shared, proof/closeout, recovery reserve, Owner actions, external waits); three cost views; old-vs-new comparison
   (8.18M, 40M, 368M/371M, 81M/phase, 500-600M) explaining scope differences; handoff fields; meta-analysis.
3. The plan ends with exactly: DECISION REQUIRED / APPROVE REMAINING EXECUTION / or / OPTIMIZE FURTHER.
4. STOP. Do not lift the U0 deny budgets, do not arm or release any Clock A / intent-order mission.
