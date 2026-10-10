---
covers: [cognitive-deflation, model-call-firewall, cognitive-effects, cognitive-ledger, semantic-breaker, cognitive-ci, proof-locality, derivation-cache, pgo, cbr-inheritance, ql-organic-recompile]
tier: T3
status: approved
date: 2026-10-10
---

# Cognitive Deflation Closure (CDC) -- Master Plan, 2026-10-10

Status: APPROVED (Owner "y" 2026-10-10; executing since C0 16e52c89 in Apps/pp-cdc, goal cdc 80M; reconfirmed by
the Owner 2026-10-10 evening). The chat is the approval surface; this file backs it up.
Nothing was mutated to produce it except this file. No worker stopped, no branch landed, no budget changed.
Source brief: the Owner's /cpp-gsd-long prompt (universal cognitive deflation + read-only QuickLease recompile).

## 1. Reality delta (measured read-only, 2026-10-10 ~15:00-15:40 local)

- Dataset `Downloads/Dataset QuickLease SEO + GEO Token Optimization 1.md` (82 KB, 5,160 lines). All historical
  facts sit in lines 1-1160 (354M / 424.8M / 548.3M, 807 calls, 155K/call, 159 planning calls, 7 subagents,
  42.3 USD, 5.7 h, ~50 vs 6 calls/task). Lines 1163-5160 are the design conversation that produced the brief;
  their numbers are illustrative only (grep-verified). Treated as evidence, not instructions.
- **Four overlapping programmes were approved TODAY and are in flight:**
  | Programme | Plan | State now |
  |---|---|---|
  | Autonomy Convergence (S0-S10, cap 90M) | `autonomy-convergence-MASTER-PLAN-2026-10-10.md` | S0, S1 DONE (land_worktree.py live b97ced4a; gsdx_chain, gsdx_reforecast, dgl lease epochs landed; cost-collapse T1/T2 BLOCKED_CONFLICT); chain ticks S2 next |
  | EVC self-deflation (P50 41M, stop 65M) | `evc-self-deflation-...` + `economic-engine-repair-...` | mission m-79dbb97c5017 RUNNING in `.claude/worktrees/evc` (phase 1) |
  | Context Rent same-pane (stop 16M) | `context-rent-same-pane-2026-10-10.md` | APPROVED; mission m-4d1b851262ff BLOCKED (prompt) |
  | UKAI knowledge (5M) | `ukai-2026-10-10.md` | workstream planned (aa4b160f) |
- Live PP: `feature/knowledge-acquisition` @ fe86ea91, 936 dirty paths, 60 worktrees, a live writer
  (m-9bee7894f20f RUNNING in the live checkout). 29 claude.exe processes.
- **QuickLease safety:** QL organic mission m-23568bbcd2f9 HALTED, owner DEAD, last commit 0d88a1ae (10-08 23:10).
  No live mission has a QL cwd. Nothing is burning QL tokens. No containment needed.

### Existing owners (reuse map)
| Brief concept | Owner today | Landed? |
|---|---|---|
| Claim-graph estimator, classes satisfied/deterministic/known_transform/bounded_coding/novel/owner_reality | `tools/cost_to_completion.py` | yes |
| Envelope / floor admission, verdict contract | `tools/route_admission.py`, `gsd_mission.py` | yes |
| NO_WORK proof, unit receipt | `tools/work_proof.py` (A6/A5) | yes, not emitted by supervise |
| Work-class tier routing, escalate on failed verify | `tools/tier_routing.py` (A4) | yes (b97ced4a) |
| Lineage / goal lease / spend reservation, deny budget at tool boundary | `mission_spend.py`, `hooks/lib/goal_binding.js`, `hooks/session_budget_guard.js`, dgl lease epochs | yes |
| Usage truth + price table, per-session autopsy | `tools/usage_index.py`, `tools/session_autopsy.py` | yes |
| Distributions P50/P80/P95, reforecast, backtest, spend capability, fresh-floor cut | EVC U1-U8 (+ `gsdx_reforecast.py`) | in flight |
| Programme status zero-model, zero-model chain, known integration | Autonomy S2-S4, S1 | S1 live, rest in flight |
| Epoch rotation (ASER), ContextImage = capsule, rent attribution, status fast path, floor census | `rollover.py` + ctx-same-pane S0-S7 | approved |
| Knowledge / prompt recall | UKAI F0-F7 | approved |
| Change impact (proof locality seed) | `tools/change_impact.py` (09-28) | yes, not wired |
| Cognitive Economy ledger verifier, opt-in CI clauses | `tools/cep_gen2.py` (meta_work, token_incident, hot_token_delta) | yes, opt-in only |
| Constitutive baseline / tower | `Apps/pp-cbr-wt` (parked 09-25), UKDL, hookreg + `test_matcher_liveness` | partial |
| Agent spawn interception | 4 PreToolUse hooks on `Task|Agent`, SubagentStart/Stop | yes |

### Where cognition bypasses optimization today (evidence)
1. Main-thread model turns: the host exposes no pre-call hook for the model itself. Only tool calls, Agent spawns,
   prompt submit, worker launch and epoch rotation are interceptable. -> EXTERNAL_LIMITATION; enforce at those edges.
2. Agent/subagent spawn: guards check shape (solo, bound, durable output), not cognitive necessity. 91 % of measured
   programme spend sat inside GSD subagents, each re-paying a ~115-125K floor.
3. Status questions: answered by a model turn at full resident (ctx plan, measured).
4. Calls without semantic progress: only a 3-epoch no-progress halt; no within-epoch breaker.
5. Proof: landings run declared lists or full suites; change_impact is not wired.
6. Research: WebSearch/WebFetch have no evidence-reuse gate.
7. Cognitive CI: measures (cep_gen2) but blocks nothing on a cost regression.

### Largest known cognitive taxes (measured)
calls x fresh floor (115-146K p50/p90) dominate every programme; control-plane amplification 1.9x (Live QA);
global `~/.claude/CLAUDE.md` 39.8K chars on every call; QL Phase 1 = 807 calls at 155K mean, 42.3 USD.

## 2. Architecture decision: close the gaps, do not build a fifth programme

The brief's compiler pipeline already exists as owners spread over four approved programmes. CDC is a thin
closure programme: it adds only what none of them owns, wires everything into ONE admission path at the edges the
host exposes, makes Cognitive CI release-blocking, and proves the 24 Master Done-Gates on top. No new OS, no new
ledger, no second estimator, no second chain.

**Single admission path ("cognitive compiler", implemented as passes in existing owners):**
work_proof (NO_WORK) -> derivation store (reuse/in-flight) -> effect class + tier (tier_routing) -> route_admission
(context floor, envelope) -> spend lease (goal_binding / EVC U5) -> execution -> receipt (A5 + role ledger) -> CI.

**Enforcement edges:** PreToolUse `Agent|Task` (agent necessity + capability token), worker launch (`gsd_mission arm`,
`claude -p`), PreToolUse `WebSearch|WebFetch` (research reuse), PostToolUse `*` (semantic breaker), UserPromptSubmit
(status fast path, ctx S4), epoch rotation (ctx S2). Every guard has a kill switch, fails open on its own error, and
ships with a red-branch drill.

## 3. Obligation ledger (every brief concept classified)

| Concept | Disposition | Unit |
|---|---|---|
| Universal Cognitive Compiler | CONNECT owners into one admission path | C3 |
| Proof of Work Necessity / NO_WORK | ALREADY_DONE (work_proof); CONNECT to Agent edge + supervise | C3 |
| Proof of Read Necessity / read-once | IMPLEMENT minimal: re-read detector (same path+sha in epoch) in role ledger + breaker | C1, C4 |
| Proof of Cognition / Agent Necessity, model-call firewall, privileged syscall | IMPLEMENT at Agent + launch edges (capability token from admission); main turn = EXTERNAL_LIMITATION | C3 |
| Cognitive effect system / IR / deopt | EXTEND cost_to_completion classes + tier_routing into one enum on route/packet; deopt = explicit field | C2 |
| Cognitive ABI / information hiding | EXTEND route.json + unit packet schema (effects, class, invalidators, deopt) | C2 |
| Model boundary budget, semantic progress, semantic breaker, token incident, stop-the-line, autopsy | IMPLEMENT on PostToolUse + EVC U5 spend capability | C4 |
| Universal token ledger (roles), receipts, waste ledger, P&L, flamegraph | EXTEND session_autopsy/usage_index with deterministic role classifier | C1 |
| Context compiler, CWS, CRA, rent controller, epoch rotation, pane continuity | ALREADY owned by ctx-same-pane (S1/S2/S4/S5); CONNECT metrics into CI | C7 |
| In-epoch paging / semantic GC / projection pushdown | EXTERNAL_LIMITATION (host owns transcript); fallback = rotation + capsule pointers | -- |
| Tool linker / skill linker / constitutional rent / residual / prompt half-life | MEASURE via ctx S1 census; IMPLEMENT one retirement of a mechanically enforced hot rule (with backup) | C9 |
| Planning deflation / cache, research compiler, research reuse, negative knowledge | IMPLEMENT minimal derivation store (provenance, deps hash, freshness, invalidators) + WebSearch/WebFetch reuse gate; negative knowledge = UKDL traps + FIOS queried at the gate | C6 |
| Semantic CSE, estate-wide singleflight, semantic cache, incremental build | IMPLEMENT minimal: content-addressed derivation key + in-flight lock (same store); EXPERIMENT_FIRST beyond one host | C6 |
| Proof compiler, green-path proof, review deflation | CONNECT change_impact into land_worktree (affected closure) + tier_routing policy "green deterministic = no reviewer" | C5 |
| Debugging deflation, failure entropy, recovery deflation | ALREADY partial (steward, linger, reapers; Autonomy S7); CONNECT FIOS signatures -> recovery table | C8 |
| Integration deflation | ALREADY_DONE (land_worktree S1) | -- |
| Status / handoff / wait / monitoring deflation | ALREADY owned (Autonomy S4, ctx S4, sweep, WAITING_ZERO_HOT); CI fitness gates only | C7 |
| Decision SSA, call fusion/fission, peephole optimizer | EXPERIMENT_FIRST: the motif miner (C8) must show measured recurrence before any build | C8 |
| Global sequence mining, PGO, capital allocator, debt register + interest, ROIC, half-lives, irreducibility / frontier registry | IMPLEMENT as ONE deterministic report over the role ledger (no new store) | C8 |
| Automatic primitive / decision / proof / recovery / context synthesis | SEMI-AUTOMATIC: miner proposes; one candidate compiled and certified (Done-Gate 18); full auto = NEGATIVE_ROI now | C8 |
| Role / prompt / decision extinction | IMPLEMENT one real retirement (Done-Gate 19) | C9 |
| Cognitive CI, regression budget, statistical confidence, metamorphic + mutation tests, benchmark suite | IMPLEMENT: benchmark bank + certified baseline JSON + release-blocking check inside land_worktree | C7 |
| Counterfactual engine, holdout missions | CONNECT EVC U8 backtest + rollover_replay; add holdouts | C10 |
| CBR promote / retire, baseline compaction, fresh-project inheritance | CONNECT hookreg + matcher liveness + UKDL; global hooks = inherited by every repo without opt-in | C9, C11 |
| ADR cognitive governance, Exit-to-Determinism, cost compatibility metadata | FOLD into the C8 report fields; separate system = NEGATIVE_ROI | C8 |
| Agent Teams mode | NEGATIVE_ROI for this programme (slim single-writer packets) | -- |
| UWCP / cross-host | DEFER_EXTERNAL (GEX44 control-plane port is Owner/deploy class) | -- |
| Self-hosting | MANDATORY ordering, section 5 | all |
| QuickLease Phase-1 autopsy + recompile | IMPLEMENT read-only, last | C12 |

## 4. Units (vertical slices; slim packet workers; one writer)

Execution shape: CDC units are APPENDED to the existing Autonomy chain (`vault/programs/autonomy/chain.json`) after
S9, in a new worktree `Apps/pp-cdc` (branch `feat/cdc`), landed only through `land_worktree.py`. One queue, one
writer per worktree, zero-model chaining (Autonomy S3), no coordinator pane. Autonomy S10 (Live QA recompile)
stays where it is. CDC units that consume EVC or ctx-same-pane outputs declare `requires: <receipt path>`;
C0 adds that field to gsdx_chain if absent. A unit whose requirement is missing waits with zero residents.

| Unit | Content | Mode | Proof |
|---|---|---|---|
| C0 | worktree, chain append, `requires` support, goal `cdc` declared with cap | EXECUTION | chain test + drill |
| C1 | role ledger: deterministic per-call classifier (NOVELTY/IMPLEMENT/PLAN/RESEARCH/READ/REREAD/PROOF/REPAIR/CONTROL/STATUS/RECOVERY/CONTEXT_FAULT) on session_autopsy, receipts per boundary, unattributed share | EXECUTION | golden transcripts + mutants |
| C2 | effect enum + ABI fields on route/packet; ZERO/DETERMINISTIC route that opens a model boundary without `deopt` = refused | PLAN (one decision note) then EXECUTION | drill: deterministic packet spawning Agent is refused |
| C3 | admission path at Agent/launch edges: NO_WORK, derivation hit, tier, envelope, spend lease -> capability token; refusal reasons; kill switch | EXECUTION | real blocked call observed in a live session |
| C4 | semantic breaker: N calls with 0 progress (commit, tree change, receipt claim, new file) or repeated reread -> incident file + deny budget (EVC U5) + autopsy | EXECUTION | drill on a synthetic no-progress loop + live canary |
| C5 | proof locality: change_impact -> affected tests in land_worktree; green deterministic path needs no reviewer | EXECUTION | affected vs full-suite agreement on 3 landings |
| C6 | derivation store + in-flight lock + research gate on WebSearch/WebFetch + negative-knowledge lookup | EXECUTION | repeat query served from store; in-flight subscriber waits instead of duplicating |
| C7 | Cognitive CI: benchmark bank (known transform, bounded coding, status, green proof, recovery, wait, dormant goals, large history, unrelated tools/skills, test-count), certified baseline, regression budget file, release-blocking in land_worktree; metamorphic V-gates | PLAN (thresholds from measured noise) then EXECUTION | planted regression goes RED and blocks a landing |
| C8 | PGO report: dominant tax, motif miner (tool n-grams x cost), debt register with interest, ROIC ranking, irreducibility/frontier list; compile ONE top motif into a certified primitive | EXECUTION | primitive replaces the motif on a replayed trace |
| C9 | extinction + CBR: retire >= 1 hot rule/role now mechanically enforced (backup + revert path + test that behaviour still holds); fresh-repo inheritance test (no opt-in) | EXECUTION | fresh repo session shows guards active; floor census delta |
| C10 | holdouts: replay Live QA, Clock A, intent/order, DWS traces (not used for design); one live cross-domain canary in a non-PP repo | EXECUTION | scope-normalized before/after table |
| C11 | done-gate evaluator `tools/cdc_gate.py` (24 gates, UNKNOWN never PASS), KV/UKDL/FIOS entries (dedup), handoff rendered from state | EXECUTION | gate run stored |
| C12 | QuickLease READ-ONLY: Phase-1 call autopsy via C1, residual compile (DONE/NO_WORK/.../UNKNOWN), semantic families, CWS, new LOWER/P50/P80/P95/HARD, old-vs-new, savings attribution; then STOP | EXECUTION | numbers reproducible from the tool output |

Iteration: each worker applies `Downloads/Promptsss/Prompts pa iterar/Universal/iteracion-avanzada-universal.txt`
at the checkpoints the brief lists, inside its own unit.

## 5. Dependency graph and self-hosting order

Autonomy S2-S4 (programme authority, zero-model chain, status) -> C0 -> C1 -> C2 -> C3 (firewall live: every later
unit is admitted through it) -> C4 (breaker guards C5+) -> C5 (later landings use affected proof) -> C6 -> C7 (CI
judges C8+ landings) -> C8 -> C9 -> C10 -> C11 -> C12 -> STOP.
External requires: C4 needs EVC U5 (spend capability) or uses goal_binding deny budget directly; C7 needs ctx S1
attribution (falls back to session_autopsy if absent); C10 needs EVC U8 replay harness (falls back to rollover_replay).
Self-hosting proof (Done-Gate 22): C1 ledger measures C0-C12; C5-C12 tokens/semantic transition vs C0-C4.

## 6. Done-gates

The brief's 24 Master Done-Gates, evaluated by `cdc_gate.py`. Declared up front as EXTERNAL_LIMITATION (detected,
tested fallback, never PASS-by-assumption): gate 2 covers interceptable edges, not the main model turn; gates 4/5 are
met at epoch boundary and through MCP/skill exposure settings, not by in-epoch selection.

## 7. Migration and rollback

Every change lands ff-only through land_worktree with a receipt; rollback = revert that commit. Every new guard has an
env kill switch (`CPP_COG_ADMISSION=off`, `CPP_SEM_BREAKER=off`, `CPP_COG_CI=off`, `CPP_RESEARCH_GATE=off`) and fails
open on its own error. Hot-rule retirement edits `~/.claude/CLAUDE.md` only after a backup under
`~/.claude/backups/` and with a revert line in the same receipt. No push, no GEX44 deploy, no QL product change.

## 8. Token budget (processed tokens, this programme only)

Measured comparable: Autonomy S1 (tool + 10 tests + 4 landings) ~30 calls at ~150K = ~4.5M per substantial unit.
| Item | Tokens |
|---|---|
| Sunk relevant | 4 approved programmes (not re-spent here); this scan ~3-4M (estimate, this pane) |
| Semantic lower bound | ~20M |
| C0 0.5 · C1 4 · C2 3 · C3 5 · C4 4 · C5 3 · C6 5 · C7 6 · C8 5 · C9 3 · C10 4 · C11 3 · C12 3 | 48.5M |
| Inside the units: proof 3M, integration 3M, holdouts 4M (C10), mutation 2M, CBR/UKDL 2M, recovery 4M | |
| **LOWER 30M · P50 48M · P80 60M · P95 75M · HARD STOP 80M** (enforced: token_estimate 40M x breaker 2.0) | |
| Meta-optimization tax target | control plane <= 5 % (<= 2.5M), 0 resident coordinator |

Not included (already authorized separately): Autonomy remainder (cap 90M), EVC (stop 65M), ctx-same-pane (stop 16M),
UKAI (5M). Confidence: MEDIUM on C0-C6 (owners known), LOW on C7-C8 (noise and motif recurrence unmeasured).
QuickLease payback (hypothesis, LOW): old central 354M is contaminated by Phase-1 topology; if the C12 recompile lands
P50 in the 40-120M band, avoided spend is ~230-310M, i.e. 5-6x the CDC P50. Estate-wide (hypothesis, LOW): laptop
programmes measured 371M (intent/order), 304M (Clock A), 23.8M (Live QA), 91 % in subagents; a 30-60 % cut on
known-work classes is hundreds of M per month. Both become measured numbers only through C10/C12.

## 9. Approval scope (one word)

"y" approves: worktree `Apps/pp-cdc`, appending C0-C12 to the Autonomy chain, global hook installs with kill
switches, goal `cdc` with hard stop 80M, one backed-up retirement edit of mechanically enforced text in
`~/.claude/CLAUDE.md`. It does NOT approve: QuickLease execution, push, deploy, a second writer in any existing
worktree, or changes to the EVC / ctx-same-pane / UKAI plans.
