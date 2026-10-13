---
covers: [autonomous-mission-recovery, amr, mission-recovery, cost-hold-recovery, strategy-identity, ksp-fusion-recovery]
status: APPROVED 2026-10-13 ("Aprobar y ejecutar", one click: T3 runtime change + tokens A 25M / B 60M + KSP 36 h renewal)
tier: T3 (global mission runtime, every CPP mission inherits it)
---

# AMR — Autonomous Mission Recovery, then KSP-FUSION continuation

Source directive: Owner `/cpp-gsd-long` 2026-10-13 ("Obligation A then Obligation B").
Inline plan in session 43d7834b is the approval surface; this file is its durable copy.

## 1. Incident, reconstructed from machine evidence

| Time (UTC) | Evidence | Fact |
|---|---|---|
| 10-12 23:08 | `gsd-mission-m-342bc71ba415.json` created_at | Mission armed, ralph, `--ws ksp-fusion`, 30 cycles / 36 h, model sonnet (policy@1). |
| 23:12 | ledger `worker_adopted` | Epoch 2 worker `7182c66c` adopted (epoch 1 died on the MCP dialog). |
| 23:19 | `01-CONTEXT.md` mtime | Worker wrote Phase 1 CONTEXT (3,365 B). Never committed. |
| 23:20 | worker transcript L183 | Worker dispatched `gsd-planner` **async** (prompt 2,751 chars). This is GSD's default per-phase topology: no admission decision was made. |
| 23:21 | ledger `cost_mark` 1,840,536 | Last fingerprint move (the untracked CONTEXT file). |
| 23:20-00:01 | `agent-aecc1698aebf3061f.jsonl` | Planner: 68 tool calls, 0 writes inside the worktree, 6 scratch scripts `gsd_scan*.py` in `%TEMP%` (off-tree, invisible to the fingerprint), no `PLAN.md`. |
| 00:01:12 | ledger `cost_breaker_tripped` | spent 6,312,195 vs estimate 7,500,000 (auto envelope); 4,471,659 since the tree last changed > stall budget 3,750,000. |
| 00:01:13 | `owner_hold_set`, `session-budget-7182c66c.json` | Hold kind=cost; `hold_guard_budget` wrote target=warn=stop=1 for the worker sid. |
| ~00:02 | worker transcript L207 | Planner hand-back "PLANNING INCONCLUSIVE" with a complete 3-plan design (capitalized below). |
| 00:02:52 | `mission-costhold-*.flag` n=3 | Guard refused the worker 3 times; worker wrote `memory/handoffs/ksp-fusion-phase1-handoff.md` and ended blocked. |
| 00:03 → 08:16 | sweep task `PP-GsdLongRun-Sweep` every 5 min | `plan_next` returned `none: owner hold` on every pass (~100 passes). Goal idle **8 h 15 min**. |

Worktree now: HEAD `be9de84c`; untracked `01-CONTEXT.md`, the handoff; modified `vault/handoffs/ESCALATED.md` + `escalations.json` (a hook's mirror-drift counter, not mission work).
Host: worker `7182c66c` listed `blocked` (alive, refused by the guard). No successor exists. No newer session touched Phase 1.

### The exact missing transition
`gsd_mission._cost_breaker` → `set_owner_hold(kind="cost")` → `plan_next` returns `{"action":"none"}` for **every** hold
(`gsd_mission.py:529-557`). The only exits are `release` (manual, re-enables the SAME strategy) and settle-on-DEAD.
There is no `recover` action, no classifier, no residual, no successor path. The guard's refusal text and the job's
`needs` both instruct the Owner to run `session-declare` or delete the file: process mechanics.

## 2. Root-cause matrix

| Cause | Verdict | Evidence |
|---|---|---|
| COST_BREAKER_WORKING | CONFIRMED | trip at 4.47M stall, guard refused 3 calls, no bypass |
| AUTONOMOUS_RECOVERY_MISSING | CONFIRMED | no `recover` action anywhere in `plan_next`/`supervise` |
| HOLD_WITHOUT_RECOVERY_TRANSITION | CONFIRMED | `gsd_mission.py:557` |
| PROGRESS_CLASSIFICATION_INSUFFICIENT | CONFIRMED | fingerprint = HEAD+porcelain+diff of the tree only; off-tree planner work and the hand-back are invisible; hook-written files in the tree count as progress (false positive pole) |
| PLANNER_TOPOLOGY_FAILURE | CONFIRMED | 68 calls, re-measured facts already in CONTEXT/STEP2_PLAN |
| MODE_INFLATION | CONFIRMED | Phase 1 had success criteria + approved plan + audit; GSD spawns the planner unconditionally |
| SUBAGENT_NEGATIVE_EVC | CONFIRMED | ~4.5M for a design that fits in 8 KB |
| REQUIRED_PLAN_ARTIFACT_MISSING | CONFIRMED | 0 of 3 `PLAN.md` |
| RESIDUAL_COMPILER_NOT_AUTOMATIC | CONFIRMED | residual exists only as prose in the hand-back and handoff |
| TOPOLOGY_RECOMPILER_NOT_AUTOMATIC | CONFIRMED | — |
| SUCCESSOR_LEASE_NOT_AUTOMATIC | CONFIRMED | `renew_mission` refuses a held record |
| SUCCESSOR_EXECUTOR_NOT_AUTOMATIC | PARTIAL | `launch_worker` exists and works (epoch 2 proves it); nothing calls it from a hold |
| OWNER_PROCESS_MECHANICS_LEAK | CONFIRMED | guard text + job `needs` + my own 10:16 question to the Owner |
| GOAL_LIVENESS_GAP | CONFIRMED | nothing distinguishes "held, recoverable" from "held, Owner boundary" |
| FAILED_ATTEMPT_CAPITALIZATION_PARTIAL | CONFIRMED | design survived only by luck (async hand-back landed after the trip) |

## 3. Owner map (EXTEND / CONNECT before CREATE)

| Capability | Today | Action |
|---|---|---|
| Cost breaker `_cost_breaker`, `mission_spend.judge` | ACTIVE | NO_WORK on the predicate; EXTEND to emit a typed `breaker_event` |
| Hold `set_owner_hold`, `hold_guard_budget` | ACTIVE | EXTEND: hold carries `recovery` sub-state; per-sid guard file stays as the executor fence |
| Supervisor `plan_next`/`supervise` + sweep task (5 min) | ACTIVE | EXTEND: new action `recover` (this IS the watchdog/scheduler; no model polling) |
| Mission Recompiler / Goal Liveness / Strategy Identity / Residual / Topology Recompiler | ABSENT (0 hits) | IMPLEMENT in one module `tools/mission_recovery.py` (pure functions) |
| Programme Authority | ABSENT as code | CONNECT: = mission caps (cycles/hours) + token envelope; new field `authority_tokens` |
| Lease runtime | PARTIAL (`renew_mission`, epochs, `token_estimate`) | EXTEND: successor lease = new epoch + new envelope + new strategy id |
| Successor executor | PARTIAL (`launch_worker`, `_launch_slim`, card) | CONNECT: recovery calls `launch_worker` with a ContextImage card |
| Agent admission | ACTIVE (`cdc C3` cognitive admission firewall at Agent/Task spawn, `admit_route` W1) | EXTEND: deny a fenced strategy (`gsd-planner` for a fenced unit) |
| Handoff / RESUMPTION | ACTIVE | CONNECT as ContextImage inputs (page-fault references, not preload) |
| ContextImage / CCR | PARTIAL (`ccr_pgo.py`) | IMPLEMENT minimal card section; CCR cost admission reused |
| UWCP | ACTIVE (goal providers) | NO_WORK: single-host missions; no positive ROI for distributed machinery |
| Non-convergence | PARTIAL (`gsd_x/goal/convergence.py`, stall fingerprint) | CONNECT stall/same-signature evidence into the failure classifier |
| FIOS / Knowledge Vault / UKDL / CBR | ACTIVE | EXTEND at close |

## 4. Recovery contract

States (stored in `owner_hold.recovery.state`, monotonic, CAS through `transition`):
`HELD_FOR_DIAGNOSIS → EVIDENCE_SEALED → CLASSIFIED → RESIDUAL_COMPILED → TOPOLOGY_COMPILED → SUCCESSOR_LEASED → SUCCESSOR_LAUNCHED → RUNNING_SUCCESSOR`
Exits: `OWNER_BOUNDARY` (with a Decision Packet), `DURABLE_WAIT`, `EXTERNAL_WAIT`, `TERMINAL`.

- **Trigger:** a hold with `kind=cost` (later: stall-halt, failed launch, executor crash) seen by `supervise`.
- **Freeze:** old worker stays refused by its per-sid guard (stop=1); supervisor stops it (existing `stop_owner`) before any successor. The guard file is NOT deleted: it is the fence and is kept for the old sid forever.
- **Seal:** `vault/recovery/<mission>/<n>/evidence.json`: breaker numbers, fingerprint, tree delta, off-tree artifacts, Agent calls in window, hand-back texts (sha256 + path), handoff.
- **Progress classifier (deterministic):** path classes over the tree delta (tests→PROOF, `.planning`→PLAN, vault/memory docs→KNOWLEDGE, code→PRODUCT, hook-owned paths ignored), plus off-tree evidence (subagent hand-backs naming the missing required artifacts → PLAN_PROGRESS); efficiency = class / processed tokens. Classes: PRODUCT, PROOF, KNOWLEDGE, PLAN, INFRASTRUCTURE, MIXED, ZERO, REGRESSION, EXTERNAL_WAIT, UNKNOWN (never folded into ZERO).
- **Failure classifier (rule table, first match):** PLANNER_TOPOLOGY_FAILURE (planner Agent active + required artifact missing), EXECUTOR_STALL (no Agent, zero delta), REPEATED_STRATEGY (same strategy id tripped before), EXTERNAL_DEPENDENCY, AUTHORITY_EXHAUSTED, UNCLASSIFIED (→ Owner packet).
- **Strategy identity:** `sha256(goal, unit, topology_kind, agent_types, decomposition_key)`, topology_kind ∈ {main_thread, planner_agent, executor_agent, multi_agent}. Session id and model are NOT inputs: a new session running the same planner hashes equal.
- **Material change:** successor strategy id ∉ the unit's fenced set. Fenced ids are stored on the record and enforced at Agent spawn.
- **Residual compiler:** GSD phase state (success criteria, plans present/summarised) minus capitalized delta → ordered obligations, each with its proof command.
- **Topology recompiler (table):** PLANNER_TOPOLOGY_FAILURE + captured design → main_thread EXECUTION, planner Agent denied for the unit; EXECUTOR_STALL → smaller unit (first residual obligation only); REPEATED_STRATEGY with no new evidence → OWNER_BOUNDARY.
- **Successor lease:** settle old spend (ledger row); price = residual estimate; envelope = min(price × 1.5, authority_left − reserve(recovery 10 % + closeout 5 %)); new epoch; same mission id and goal. Never all remaining authority.
- **ContextImage:** a card section ≤ 2.5 KB: goal, residual, capitalized delta path, fenced strategy + reason, allowed next operations, budget, page-fault references. No transcript replay.
- **Launch:** existing `launch_worker` (proven path). Launch failure → one retry with the same strategy only if the failure is infrastructural, else OWNER_BOUNDARY.
- **Owner boundary (narrow):** authority exhausted; recursion cap (2 recoveries per unit, each a different strategy); UNCLASSIFIED failure; HR-04 / irreversible / security / product decision in the residual. Output = one Decision Packet in `vault/OWNER_QUEUE.md`, never "delete the file".
- **Goal liveness:** every non-terminal mission must map to one of {active, successor_ready, durable_wait, external_wait, owner_boundary}; a held mission with all recovery preconditions true and no `recovery` state after 2 sweep passes → `liveness_incident` ledger row + escalation.
- **Kill switch:** `CPP_MISSION_RECOVERY=off` (and a file switch) reverts to today's park-forever behaviour.
- **PGO:** `vault/recovery/pgo.jsonl` one row per recovery (classes, old/new topology, spend, time to next verified progress).

## 5. Current incident: recovery path (not executed yet)

- **Capitalized delta:** `01-CONTEXT.md` + the planner hand-back (full text saved; settled design for plans 01/02/03, measured facts: 147 rows S92/N24/O31, 0 record/ledger disagreements, retired rule dry run 0 changes, carrier table, 4 empty `answered_by` rows, naming `sp1_*.py`, no ledger write in Phase 1, SP1B hazard). Duplicated/useless: the 6 `%TEMP%` scan scripts.
- **Residual:** write `01-01/02/03-PLAN.md` from the design (no re-derivation), then execute 01 → 02 → 03 sequentially; re-measure the 4 empty-`answered_by` rows; final gates.
- **Successor:** main-thread EXECUTION worker, no planner Agent (fenced), one plan per commit, ≤2 `.py` per commit.
- **Commit strategy:** first commit = CONTEXT + 3 plans (PLAN_PROGRESS made durable); then one commit per plan with its proof.

## 6. Obligation B

Phase 1 lean as above, then Phases 2-9 of `.planning/workstreams/ksp-fusion/ROADMAP.md` under the same mission, each phase
planned in main thread unless the phase's own uncertainty passes Agent admission. Further breaker events recover through AMR.

## 7. Budget (processed tokens, the unit `mission_spend` measures)

Obligation A — semantic lower bound 3M · lower 6M · P50 11M · P80 16M · P95 24M · requested hard authority 25M (confidence MEDIUM).
Breakdown P50: reality delta 0.8 (spent) · reconstruction 0.3 · progress cls 0.8 · failure cls 0.5 · strategy id 0.6 · hold transitions 0.8 · semantic delta 0.6 · residual 0.8 · topology 0.7 · lease 0.6 · ContextImage 0.5 · launcher+fence 1.2 · liveness 0.7 · watchdog 0.3 · mode regression 0.4 · fault injection 1.5 · self-host/real recovery 1.0 · KV/UKDL/CBR 0.8 · reserve 1.5 · meta tax 0.5 (sum ~15.9 = P80 envelope).

Obligation B — the canonical Step 2 plan gives NO token figure (UNMEASURED; 8-10 epochs, shares only). Derived: Phase 1 ~5.5M at P50 (15 % share) → programme ~37M.
semantic lower bound 12M · lower 25M · P50 40M · P80 55M · P95 75M · requested hard authority 60M (confidence LOW, rises after Phase 1 measures a real rate).
Breakdown P50: recovery 0.5 · Phase 1 exec 4.5 · Phase 1 verify 1.0 · Phases 2-9 28 · recovery reserve 3 · epoch/context reserve 3 · closeout 1.

Current authority: the KSP mission's only token bound is the AUTO envelope 7.5M (6.31M spent). No token-denominated Programme Authority exists; the Step 2 approval covered cycles (30) and hours (36, expiring 2026-10-14 ~11:08 UTC).

## 8. Resources

One writer per tree. PP work in a dedicated PP worktree (`gsd_mission.py` was committed by another pane at 02:03 today; the main PP checkout carries 1,128 dirty paths). KSP successor = background worker launched by the runtime itself (not this pane). Agents: one read-only `oneshot-architect-auditor` on the state machine (independent adversarial review; bounded). No planner Agents.

## 8b. Progress (2026-10-13, session 43d7834b)

- DONE: AMR built in worktree `C:\Users\User\Apps\pp-amr-wt`, branch `amr/mission-recovery`, commit `92b49b35`
  (mission_recovery.py, gsd_mission.py wiring, hooks/amr_fence.js, 61-gate suite). Independent audit WARNING ->
  all 9 findings fixed. Real-incident dry run reproduces the fixture (PLANNER_TOPOLOGY_FAILURE -> main-thread
  EXECUTION, gsd-planner fenced, 6M lease, residual = commit capital / write plans / execute / prove).
- NOT YET LIVE: merge into the live PP checkout + add `../skills/claude-power-pack/hooks/amr_fence.js` to
  `~/.claude/hooks/hook-dispatcher.js` 'PreToolUse-Agent-default'. Then `gsd_mission.py authority --mission
  m-342bc71ba415 --tokens 66M --extend-hours 36` and the 5-minute sweep recovers KSP-FUSION by itself.
- BLOCKED ON: host memory 1.3 GB free of 31 (32 claude + 38 Cursor + 116 node processes). The recovery launches a
  background worker; the reaper already killed the mutation drill (renewal-blind mutant never ran).

## 8c. Owner redirect 2026-10-13: run the KSP successor on GEX44 (spec vault/specs/gex44-mission-plane.md)

Owner: "why don't you do it on GEX44?" Laptop memory (1.3-3.3 GB free) is not a boundary: the plane spec already
decides "missions that do not need Windows move to GEX44"; KSP-FUSION needs nothing Windows-only. Measured GEX44:
1 TB free on /, 56 GB RAM available, 20 cores, Java 21, Maven, Python 3.12, GitHub reachable (key kobiicraft_github,
ls-remote OK). Pattern: per-mission env `~/<name>-env` with its own HOME (template `~/a7-env`: env.sh, node/, npm/
with claude 2.1.282, home/.claude with PP clone + hooks + settings), cron `*/5 flock ... mission_sweep.sh`.

Steps (one writer at every moment):
1. DONE 10:5x: laptop worker 7182c66c stopped (host `stopped`); its stop=1 guard file kept (fence).
2. Laptop KSP worktree: commit `01-CONTEXT.md` + `memory/handoffs/ksp-fusion-phase1-handoff.md` (+ RESUMPTION note:
   executor moved to GEX44) with `scripts/safe_commit.py`; do NOT commit the hook-noise `vault/handoffs/ESCALATED.md`
   / `escalations.json`. Push `kseip/ksp-fusion-step2` to origin.
3. Laptop mission m-342bc71ba415: settle HALTED, reason "moved to GEX44 lineage" (hold kept -> never renewed locally).
4. GEX44 `~/ksp-env`: copy a7-env node/, npm/, home/ minus home/.claude/{state,projects,jobs,sessions,history.jsonl};
   fresh `.credentials.json` from ~/.claude (perm 600); PP in home/.claude/skills/claude-power-pack moved to AMR commit
   92b49b35 (incremental git bundle from a7's PP head 01199995 if it is an ancestor); add
   '../skills/claude-power-pack/hooks/amr_fence.js' to 'PreToolUse-Agent-default' in home/.claude/hooks/hook-dispatcher.js;
   env.sh (HOME, PATH, CPP_GIT_EXE, CPP_CLAUDE_EXE, PYTHONIOENCODING); mission_sweep.sh (twin of a7's).
5. GEX44 clone: `~/missions/ksp-fusion` = `git clone --reference ~/kobii-a7 -b kseip/ksp-fusion-step2`; trust the cwd
   in home/.claude.json; decline the repo MCP (`.claude/settings.local.json` disabledMcpjsonServers ["codex"]);
   post-commit hook pushes the branch to origin (plane spec B: push after every committed step).
6. Evidence carry: copy laptop transcript 7182c66c-....jsonl + its subagents/ dir into ksp-env home projects dir for
   the GEX44 cwd encoding. Arm the mission (no launch), `authority --tokens 60M --extend-hours 36`, set
   previous_owner session_id 7182c66c-6f6d-410d-8b0d-fe1a8129ae9c, set a cost hold with the laptop breaker reason.
   Then install the cron line. Proof = the sweep alone answers `recover`, launches the deflated successor, and its
   first commit reaches origin.

## 9. What returns to the Owner

Only this approval: (1) T3 change to the global mission runtime, (2) token authority A 25M + B 60M, (3) KSP mission wall time renewed to 36 h of further runtime. After that: Decision Packets only at a real Owner boundary (Q-002/Q-007/Q-012 at W4, the Phase 6 batched product question, HR-04).
