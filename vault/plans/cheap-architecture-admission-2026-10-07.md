---
covers: [cheap-architecture-admission, ce-a3, coordinator-extinction, route-admission, cost-ladder, safe-deopt]
status: PROPOSED (awaiting one Owner approval: 'fold into A3, defer U4, go T0')
extends: goal ce-a3 (Amendment A3, 5617f901)
source: fresh read-only planner 50908090-5ffc-4787-b8ad-c9eb911df84e, 19 calls, 1,478,444 processed
---

Scan finished after 19 of my 24 allowed calls. Nothing was modified. The plan follows.

# Cheap Architecture Admission: Reality Scan and master plan

**Bottom line:** this is not a new mission. The Owner approved Amendment A3 today at 20:4x ("bind every pane to its goal, kill the coordinator, cut the floor", `5617f901`), and it already covers about 70% of this brief. Goal `ce-a3` is live (declared 18:55Z). Under HR-NOVELTY-001, this plan **extends A3 inside the `ce-a3` goal** with two additions: a tranche-5 cleanup unit and a Cheap Architecture Admission compile unit. It creates no new OS, goal or budget.

## 1. Verified reality (MEASURED unless marked)

**Canonical Goal.** The parent is Cognitive Economy gen2 (TOK-18): `vault/programs/cognitive-economy/gen2/MISSION.md`, with `ledger.json` holding the 150M authorization boundary and the "connect, never duplicate" invariant. The active child is `ce-a3`:
- Journal row seq 1 sets the cap at 9,900,000 ("12M total minus coordinator pane metered separately").
- Row seq 3 is a reserve of 1,021,490 by pane 2aa0b0fb.
- `pp-ce-a3` sits at `9a02b315` (a1/a1-2 merged), and the packet `packets/A3-U1.md` exists.
- **There is no `evidence/a3/` directory, so U1 has not produced a receipt.**

| Subsystem | State | Evidence |
|---|---|---|
| Budget enforcement (session) | LIVE | `hooks/session_budget_guard.js:113-128` denies on tokens, call ratio, context ceiling and no-progress |
| Goal admission (reserve/settle, fails closed) | PARTIAL | `session_budget_guard.js:165-201`, `mission_spend.py:541-563` (goal-declare/status). Canary FAIL: 4,173,828 against a 3M cap, 39% overshoot (`evidence/goal-admission/CANARY.md:17-19`) |
| Goal binding | PARTIAL | binds only by `CPP_GOAL`, cwd root, or the budget file (`guard.js:190-201`). Unbound panes in a shared checkout are not covered. **This planner pane is itself unbound** (cwd = main checkout) |
| Agent admission | PARTIAL | the Agent lane is live (3 holds in the canary). The bound does not count subagents as requesters (CANARY.md:32-37) |
| Coordinator admission | LIVE (tranche_driver only) | `tools/tranche_driver.py:100-121` declares the coordinator first, from `--manifest` |
| Boundary / route admission | LIVE for missions only | `tools/route_admission.py:35,61` (ADMISSIBLE/DEFER/RECOMPILE/ESCALATE) is called only from `gsd_mission.py:1369,3564`. Interactive panes never see it |
| Cost ladder / deopt | PARTIAL, dormant | `tools/cost_to_completion.py:41-48` has 7 classes and `DEFAULT_DEOPT_FACTOR=3.0`. No caller found in hooks, gsd_mission, tranche_driver or commands, and it is not in the reachability registry (ESTIMATED: dormant) |
| Model routing | PARTIAL, **two authorities that disagree** | `modules/cost_collapse/router.py:22-25` says opus-4-7 / sonnet-4-6. `vault/config/model-routing.json` says opus-5-5 / sonnet-5, and its schema is ABSENT (its own line 3) |
| Fresh Focus Floor | PARTIAL | `tools/floor_regression_gate.py` exists (3% thresholds, :88-90). Host vs CPP split is UNMEASURED (A3:28) |
| Champion/challenger replay | PARTIAL | `tools/estate_shadow.py` (`replay_v2`, `recommend`), tested by `test_spawn_policy_v2.py` with `modules/cognitive_os/scheduler.py` |
| kclear/kresume | LIVE | `commands/kclear.md`, `tools/kresume_courier.py` |
| Tranche gate truth | LIVE | E1 `c2af6b95`, E2 `f35feba1` |
| HARD RULES single authority (E3) | UNCOMMITTED | `Apps/cr5-wt`, 5 modified files. `test_hard_rules_mirror` 11/11, mutation red. Open question: `test_faitp_debts` 13/14 has not been compared against HEAD (`e3-closeout:17`) |
| UKDL staging (E4) | REVERTED | `cb0ca15e` |
| Savings probe (E5) | UNDECIDED | `e70fa74c`, 605 tokens, ESTIMATED |
| E6 / E7 | NOT STARTED | `current_goal` exists nowhere in tools, hooks or gsd_x |
| UWCP | PRESENT (tests) | `tools/test_uwcp_{foundation,tla,characterization}.py` |
| SSM, UCVM, ContextImages, ZRT, read extinction, FIOS, CBR, proof runtime | **UNVERIFIED** | no file under those names in modules, tools, hooks or commands. They may live under other names (FIOS and CBR are in memory; CBR is in `Apps/pp-cbr-wt`). Not checked for absence, so not claimed ABSENT |
| GEX44 | NOT VISIBLE | A3:25 says GEX44 has no admission, so its spend is UNKNOWN |
| Worktrees | 36 registered | `git worktree list`. Many are stale branches (cwops, ucep, pp-gen3-*) |

**Host (MEASURED 20:57):** 31 `claude.exe` processes, **2,035 MB free of 32,061 MB**. Panes 2aa0b0fb (A3 U0, which per its plan should have exited) and 0f9b771b (gen3 finishing pane, already at 10.08M) were both still writing transcripts at 20:57.

## 2. Expensive defaults, largest lifetime cost first

| # | Default | Cost | Class |
|---|---|---|---|
| 1 | Long-lived interactive coordinator panes | A1 42.3M/20M, A2 27.6M/20M (coordinator 16.9M at ~238k/call), gen3 ~37.2M/31M, context-runtime-3 24.5M/7.2M (coordinator 18.4M), context-runtime-4 6.6M/3.5M (coordinator 4.57M), e6e0eca7 30.76M frozen (MEASURED, A3:16-20, CR4 closure) | **Institutional.** The lesson has been in memory since 11:27 and recurred 3x. It lives in prose, not in a mechanism |
| 2 | Per-call floor: about 105k fresh, growing to 150–240k | about 50–70% of every call (A3:27, MEASURED per pane; host/CPP split UNMEASURED) | Mixed: harness floor (host) plus CPP injections (institutional) |
| 3 | Unbound sessions | every breaching pane ran unbound | Institutional; A3-U2 fixes it |
| 4 | Concurrent requesters outrun the lease | about 970K spent before the first deny | Institutional (bound design) |
| 5 | Route admission is mission-only, and the ladder classifier has no caller | interactive work never gets asked "is there a cheaper rung?" | Institutional |
| 6 | Host memory pressure | the tranche-5 driver was reaped; 2 GB free now | **Host-unavoidable** per process (memory note: claude.exe is native); avoidable in count |

Host-unavoidable facts the design builds on:
- A running model turn cannot be interrupted, so every deny lands one request late. MEASURED: about 100k post-deny per worker.
- Headless sessions cannot write under `~/.claude`, so workers run in `Apps/pp-ce-a3`.
- The host reaps background shells under memory pressure.

## 3. Ownership, reuse, do-not-duplicate

| Concern | Owner (extend) | Do NOT create |
|---|---|---|
| Pre-call budget authority, reserve/settle | `session_budget_guard.js` goal mode + `mission_spend.py` GoalLedger | any new budget module or ledger |
| Coordinator sub-cap | `tranche_driver.py --manifest` + `goal-spawn --role coordinator` (A3-U2) | a new orchestrator |
| Rung/ladder classification | `cost_to_completion.py` CLASSES + `route_admission.py` verdicts | a new "architecture classifier" |
| Model choice | `model-routing.json` as the single source; `cost_collapse/router.py` reads it | a third routing table |
| Champion/challenger, regret | `estate_shadow.py` replay + `cognitive_os/scheduler.py` | a new shadow framework |
| Floor | `floor_regression_gate.py` | a new floor meter |
| Per-call autopsy | `vault/.../measure/turns.py --attribute` (A3-U1) | a fork of turns.py |
| Tranche truth | `cep_gen2.py --tranche` | new gates |
| Liveness | `modules/liveness/reachability.py` | hand-curated lists |
| Knowledge capture | CEPS → UKDL drafts (after the E4 regression is fixed), `router_freshness_gate` | direct UKDL appends |

## 4. Design: Cheap Architecture Admission (CAA) at the existing owners

**Taxonomy.** Extend `cost_to_completion` claims with a `topology` field on 11 rungs:

| Rung | Topology | Cost |
|---|---|---|
| R0 | none | 0 |
| R1 | deterministic | 0 |
| R2 | semantic hit | 0 |
| R3 | certified transform | 0 |
| R4 | query | 0 |
| R5 | proof transaction | 0 |
| R6 | one-shot focused call | model cost |
| R7 | focused multi-turn | model cost |
| R8 | one specialist agent | model cost |
| R9 | parallel agents | model cost |
| R10 | long-lived parent | model cost |

The existing classes map onto rungs: `deterministic`/`satisfied` → R0–R1, `known_transform` → R3/R6, `bounded_coding` → R7, `novel` → R7–R8 with deopt.

**Admission rule** (inside `route_admission.admit`, so it is one authority for missions, tranches and goal-spawn): admit the **lowest rung whose declared proof obligations it can meet**. A higher rung needs a named reason from a closed set: `needs_shared_context`, `needs_parallel_wallclock`, `needs_integration_judgment`. Otherwise the verdict is RECOMPILE with the cheaper rung named.

**Deny rules usable immediately** (guard plus driver; no shadow needed, because each already has a measured incident):
1. An unbound session writing under a declared goal root is denied (A3-U2).
2. A coordinator without a sub-cap declaration is refused (`tranche_driver.py:121` already does this for tranches; extend it to goal-spawn).
3. An Agent spawn is denied when `remaining < (live requesters + 1) × measured per-call`. This is the canary fix.
4. R9 parallel fan-out is capped at 2. It is capped at 1 when host free RAM is below 4 GB (read once per admission; an UNKNOWN reading counts as 1).
5. R10 is denied by default. A pane over N calls (default 25, the existing `DEFAULT_NOPROGRESS`) that is not declared `role: coordinator` gets the E7 handoff: write `RESUMPTION_FILE` and end on `/kresume`, never an Owner question.

**Shadow/canary first (things that change decisions without an incident):**
- rung recommendation for interactive panes, as an advisory only (no deny);
- the floor relevance gating;
- regret scoring.

Each runs through `estate_shadow.replay_v2` on U1's real pane series before enforcement.

**Safe deopt.** Every admission records `escalate_to` (next rung) plus a trigger:
- proof failed;
- or 2 strikes (Regla 12);
- or the ceiling from `deopt_factor` was crossed.

Escalation re-enters `admit`. It is never implicit, and it never raises a goal cap.

**Hard budget.** The current mechanism is kept: reserve before the call, settle on measurement, UNKNOWN = deny. Children sub-allocate from the parent goal. `goal-spawn` subtracts from the parent; a new session, agent or machine creates no budget. Calls (physical requests) and boundaries (semantic units) are kept in distinct fields, as E2 already writes both.

**Tripwires.** These are existing guard predicates extended:
- topology: requesters × per-call versus remaining;
- context: the ceiling (exists);
- calls: the ratio (exists);
- expansion: new worktrees or spawns per goal per hour, from estate_shadow.

**Work-Class profiles.** These are the `profiles`/`actuals` already in `cost_to_completion` input, filled from U1 measurements. Priors stay labelled as priors.

**Architecture Regret.** At settle, compute (actual cost − the cheapest admissible rung's counterfactual from the profile) and write it to the receipt, labelled ESTIMATED.

**Champion/challenger.** The incumbent rung policy against the candidate, replayed on frozen pane series; promotion only on lower regret with no extra proof failures.

**Cognitive CI.** `test_goal_budget_admission.py`, the V-DRIVER suite, `floor_regression_gate` and the route-admission tests are wired into the existing `cep_gen2 --tranche` clauses (A3-U5).

**CBR/UKDL propagation.** Each tranche emits lessons as CEPS drafts. They are promoted by `router_freshness_gate` only after E4's CEPS regression is fixed.

Prompt extinction and parentless execution follow from the above: workers read the card plus their packet, never the source prompt.

## 5. How this mission stays cheap

- **No coordinating pane.** After Owner approval, this planner pane makes **zero further calls**. It is itself an unbound R10 risk.
- One fresh bound pane (`CPP_GOAL=ce-a3`, cwd `Apps/pp-ce-a3`, sub-cap 0.3M, `--calls 6`) runs `tranche_driver.py --manifest` with the packets, then exits. The parent wakes only for integration judgment, at a receipt marked UNDECIDED.
- **Serial workers only** (one at a time) while free RAM is under 4 GB. The tranche-5 driver was reaped at this pressure.
- Packets are envelope-first and built bottom-up: each envelope = calls × measured floor 95,695 × (1 + margin). A packet that is not ADMISSIBLE under `route_admission` does not launch.
- Every worker uses Sonnet and makes no Agent spawns.

## 6. Tranches (all inside goal `ce-a3`)

**T0: tranche-5 leftovers** (deterministic plus 1 small worker; 0.3M)
- Compare `test_faitp_debts` against HEAD in a detached temp worktree, then commit E3 with a pathspec and write the E3 receipt (e3-closeout steps 1–3).
- E7's `current_goal` moves to T2, E6 moves to U3, and E5 stays ESTIMATED with the probe dropped.
- E4 stays reverted until the CEPS regression has a fix with a test.
- Test: the 11/11 mirror suite plus its existing drift mutation. Rollback: `cr5-wt` is unmerged.

**T1: A3-U1 autopsy** (deterministic script, worker writes it; 1.2M)
- Run the existing packet unchanged.
- Its output is the Work-Class profiles and the counterfactual base for regret.

**T2: A3-U2 extended** (bounded coding; 2.4M)
- Binding by default.
- Coordinator sub-cap.
- `current_goal(repo)`: exactly one live goal returns its id; otherwise UNDECIDED.
- Deny rules 3–5.
- Mutations: count requesters as 1; drop the RAM cap; let a missing binding admit. Each must turn a V-GOAL test red.
- Canaries:
  - expensive-denial: a tiny-cap goal with two panes plus an Agent;
  - safe-deopt: the handoff fires at N calls and a fresh session continues via `/kresume`.
- Target: overshoot ≤ one in-flight request per requester.
- Rollback: one revert.
- Note: the live dispatcher copy under `~/.claude` needs an Owner-side Copy-Item (HR-001).

**T3: CAA compile** (bounded coding; 1.5M)
- Add the `topology` rung field plus a reason enum to `cost_to_completion`/`route_admission`.
- `cost_collapse/router.py` reads `model-routing.json`, removing the stale IDs.
- Wire `admit` into `tranche_driver` and `goal-spawn`.
- Run shadow regret over U1 data.
- Declare `cost_to_completion`, `route_admission` and `floor_regression_gate` in the reachability registry, or wire them.
- Mutations: an unreasoned R9 is admitted (must go red); a router with hard-coded IDs (must go red).
- Canary: cheap-path, i.e. a known R1 task is refused at R7 with RECOMPILE.

**T4: A3-U3 floor** (2.0M, down from 2.5M; E6 rent ranking folded in)
- Done when the `floor_regression_gate` delta is below 0 on a real fresh call.

**T5: A3-U5 knowledge + Cognitive CI** (1.4M)
- UKDL drafts, CBR promotion, CI wiring, A1 reforecast.
- Knowledge-growth canary: a lesson gets promoted and `router_freshness_gate` turns green.

**A3-U4 GEX44: DEFERRED** (it needs an Owner step on GEX44 `~/.claude` anyway).
- Mission-age canary: the goal's oldest live pane is under N calls at every receipt.

## 7. Master done-gate

| Command | Expected | Level |
|---|---|---|
| `python tools/test_goal_budget_admission.py` | exit 0, new V-GOAL gates included, 3 mutants red | MEASURED |
| `python tools/test_tranche_driver.py` | exit 0 (existence UNVERIFIED in this scan; the cr4 plan names it) | MEASURED |
| route-admission + cost_to_completion tests | exit 0; unreasoned-R9 and stale-router mutants red | MEASURED |
| `evidence/goal-admission/CANARY-2.md` | overshoot ≤ requesters × one request, from raw transcripts | MEASURED |
| `python tools/floor_regression_gate.py` | delta < 0 on a real fresh call | MEASURED |
| `python tools/cep_gen2.py --tranche ce-a3` | PASS, with every clause PASS or NOT_APPLICABLE with a reason; frozen total | MEASURED |
| `python modules/liveness/reachability.py` | exit 0 | MEASURED |
| `mission_spend.py goal-status --goal ce-a3` | settled ≤ 9.9M plus the coordinator ≤ 12M total; no UNKNOWN admitted | MEASURED |
| regret receipt | per tranche, labelled ESTIMATED | ESTIMATED |
| `node ~/.claude/hooks/tests/run-all.js` | green | MEASURED |

## 8. Envelope, ROI and Owner authority

**Envelope (worker spend inside the 9.9M ledger):** T0 0.3 + T1 1.2 + T2 2.4 + T3 1.5 + T4 2.0 + T5 1.4 = **8.8M**, leaving a 1.1M proof/repair reserve. The coordinator stays within the A3 12M total. This planner pane's own spend is UNKNOWN until metered (about 20 calls); it should be settled to `ce-a3`.

**Two-strike and ROI:**
- Any tranche that fails its gate twice stops (Regla 12 / HR-ONESHOT-003).
- T3 and T4 go ahead only if T1 shows the "calls × floor" plus "rent" classes they target are at least 30% of the measured pane cost. If not, they are retired with a receipt.

**Owner authority needed:**
1. Fold this mission into A3 instead of creating a new goal.
2. Defer A3-U4 (GEX44).
3. Panes 2aa0b0fb and 0f9b771b are still running, and 31 `claude.exe` processes are alive with 2 GB free. Stopping any of them is your call, not mine.
4. Owner-side Copy-Item of the live guard/dispatcher under `~/.claude` after T2 (HR-001).
5. Drop the E5 probe.

Also: the context7 server needs authorizing via `/mcp`, and coplay-mcp, magic-ui, notion and 21st-dev/magic failed to connect. This plan uses none of them.

**Approval phrase:** **"fold into A3, defer U4, go T0"**
