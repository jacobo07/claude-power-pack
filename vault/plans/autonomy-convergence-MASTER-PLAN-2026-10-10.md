---
covers: [autonomy-convergence, zero-model-control-plane, programme-authority, programme-status, land-worktree, queue-chain, live-qa-recompile]
tier: T3
status: awaiting-owner-approval
date: 2026-10-10
---

# Autonomy Convergence — Master Plan (Stage A optimization + Stage B Live QA recompile), 2026-10-10

Status: AWAITING OWNER APPROVAL (boundary 1). The chat is the approval surface; this file backs it up.
Nothing was mutated to produce it except this file. No worker stopped, no branch landed, no budget changed.

## 1. Reality delta (measured 2026-10-10 ~12:00-12:30 UTC, read-only)

- **Spend truth, Sidecar Live QA programme (Master Plan 2026-10-09):** 8 slim packet workers 8.11M (0 unmeasured, 0.5-1.6M
  each, one queue item per session); bootstrap pane b3fb1dd2 15.7M after approval (92 calls, ~170k ctx/call; plan cap 3M);
  6.7M planning before approval. Control-plane amplification = 15.7 / 8.1 = **1.9** (inversion confirmed).
- **Live QA product state:** io-liveqa `feat/sidecar-live-qa` @ 080225c9 (local). Queue: A1 A2 A3 A4 A5 A6, B-P2-close done;
  B-P3 running as m-112d8ff4c477 (slim, 646k so far, ends on its own after one item); B-P4, B-park, A-experiments pending.
  Hermes ABSENT on laptop and GEX44 (`command -v hermes`, measured now).
- **Live PP:** `feature/knowledge-acquisition` @ 836c1121, 936 dirty paths, 60 worktrees, never pushed.
- **The control/economic plane already exists in pieces, mostly unlanded:**

| Capability | Existing owner | Landed in live PP? |
|---|---|---|
| Mission lifecycle, relay, slim packet, admission | `gsd_mission.py`, `route_admission.py`, sweep `PP-GsdLongRun-Sweep` (5 min, zero model) | yes |
| Lineage budget, renewal inherits remaining (A2), relay re-admit (A3) | `mission_spend.py`, `gsd_mission.readmit_for_relay` | yes (4b4490dc) |
| NO_WORK proof (A6), unit receipt (A5) | `work_proof.py` + verdict in `route_admission` | yes; not emitted by supervise |
| Tier routing (A4) | `tier_routing.py` a21ab8bf | no (feat/ucda) |
| Old-worker settle, linger kill | `mission_steward.py`, supervisor | yes |
| Goal reservation / per-session deny budget | D14 `session_budget_guard.js`, `hooks/lib/goal_binding.js` | yes (laptop only) |
| Price table, forecast | `usage_index.py`, `cost_to_completion.py` | yes |
| Autopsy + obligation forecast | cost-collapse T1 f3b503e6 / T2 2b5b0ea5 | no (`pp-cost-collapse`) |
| Live reforecast | `gsdx_reforecast.py` 610808c5 | no (gsdx-factory/v2) |
| Deterministic chain tick | `gsdx_chain.py` (task PP-GsdxChain-Tick, runs FROM a worktree), dgl `goal_chain.py` (PP-DglChain-Tick disabled) | no |
| Lease epochs | dgl W1b c5f22af9, W2 31f9b5f4 | no (`pp-dgl`) |
| Fresh worker card (≤8 KB), slim floor 13.5k | `mission_capsule.py` capsule-v2 | yes |
| Status projection | `gsd_mission status` (per mission); `mission_state_compile.py` (Live QA only, io-liveqa) | partial |
| Landing to live PP | manual rebase + ff-only + overlap check (cost ~4M per landing in a big pane) | no tool |

- **Competing plans:** EVC `economic-engine-repair` (88af526e) and `evc-self-deflation` (836c1121), both awaiting approval,
  priced P50 41M / stop 65M; they cover usage truth, estimator, distributions, spend capability, lease epochs, fresh-floor cut.

**Root cause of the inversion (evidence above):** not missing intelligence. (1) The successor of a finished packet mission is
created by a model in a pane (manual re-arm); (2) known integration (landing) is done by a model; (3) status is answered by
replaying a long conversation; (4) every re-arm mints a new mission id, so the lineage meter cannot see the programme;
(5) six programmes each built a piece of the control plane in their own worktree and none converged, so each programme
re-buys supervision by hand.

## 2. Architecture decision: converge, do not build

No new OS. One writer, one queue, the existing owners. The new code is four small deterministic pieces, plus landings:

1. `land_worktree.py`: the known-integration transaction (rebase onto live HEAD, overlap check against live dirty paths, declared tests, ff-only, receipt; conflict = cognitive interrupt).
2. A programme as the root of the lineage: `programme_id` on the mission record. `successor` inherits the remaining programme authority. Arming a packet that belongs to a live programme without it is refused. One canonical programme spend: settled / reserved / UNKNOWN / available.
3. A queue-driven zero-model chain: receipt DONE + next pending queue item + authority remains → the sweep arms, admits and launches the successor. One chain owner; the gsdx and dgl ticks merge into it.
4. `programme_status.py`: a deterministic projection of the programme with all status fields and the HANDOFF block, built from durable state in O(current state). Notification only on material events.

## 3. Obligation ledger (ROI gate)

| Prompt obligation | Disposition | Unit |
|---|---|---|
| Zero-model successor chaining, receipt consumption | EXTEND gsd_mission + MERGE gsdx/dgl ticks | S3 |
| Programme authority survives rotation, one spend, unattributed = failure, Owner-chat isolation | EXTEND mission_spend lineage + goal_binding session roles | S2 |
| Status O(current state), HANDOFF rendered | IMPLEMENT_NOW (small) | S4 |
| Automatic known integration | IMPLEMENT_NOW `land_worktree.py`, then land T1/T2, 610808c5, dgl W1b/W2, A4, chain tick | S1 |
| Estimator, distributions P50/P80/P95, fresh-floor cut, backtest, spend capability | MERGE = EVC U1-U8 as priced there | S5 |
| Proof reuse / NO_WORK / tier / unit receipt in supervise | CONNECT (A4 A5 A6 exist) | S6 |
| Waiting zero-hot, event wake | ALREADY_SATISFIED by deterministic sweep + WAITING_ZERO_HOT; a new event bus is NEGATIVE_ROI now | S7 test only |
| Reflexes, immunity coverage | EXTEND steward/linger/reapers + coverage counter | S7 |
| 8 universal invariants as benchmarks | IMPLEMENT_NOW as deterministic V-gates | S7 |
| Fresh worker gets working set, not history | ALREADY (capsule-v2 card, slim) + EVC U7 floor cut | S5 |
| Cross-domain canary | IMPLEMENT_NOW: fresh non-Live-QA 2-unit programme | S8 |
| CBR / UKDL / retirements | EXTEND: UKDL entries dedup'd, chain default-on, retire manual re-arm text + duplicate ticks | S9 |
| Global obligation fabric, semantic CSE, distributed singleflight, theorem plane | EXPERIMENT_FIRST: no measured duplicate demand exists to price | deferred |
| Economic double-entry, ROIC, multi-resource vector, experiment compiler, Semantic Error integral | DEFER: receipts (A5) are the first step; the rest needs data | deferred |
| GEX44 control-plane port, UWCP transport | DEFER (DEPLOY class; GEX44 has no route admission, D12) | Owner later |
| Hermes | Owner-only, not authorized | — |

## 4. Units (one writer, slim packet workers, Ralph, worktree pp-ucda-wt)

S0 containment (0.3M): the Live QA queue gets `hold: stage-A`. B-P3 m-112d8ff4c477 drains on its own (one item, then it ends) and is not re-armed. No kill. If EVC is approved separately, S5 becomes NO_WORK and this programme consumes EVC's output, so there are never two writers.
S1 land-converge (8M). S2 programme authority (6M). S3 zero-model chain (5M). S4 programme status (3M).
S5 EVC economics (16M). S6 proof/tier wiring (4M). S7 reflex + invariant bench (4M). S8 cross-domain canary (4M).
S9 CBR/UKDL/retire (2M). S10 Stage B Live QA recompile, READ-ONLY, then STOP at boundary 2 (3M).
Self-hosting: once S3 lands, this programme's own successors chain with zero model. Once S4 lands, status comes only from S4. This pane exits after approval.

## 5. Token budget (processed tokens, incremental from approval)

- Sunk, relevant to design: Live QA programme 23.8M (8.1M workers / 15.7M control); this scan ≈1.5M (inside pane b3fb1dd2).
- UNKNOWN / in flight: B-P3 worker m-112d8ff4c477 (646k so far, Live QA budget, not this programme's).
- Semantic lower bound ≈ 28M: 5 landings, 4 small tools, wiring, canary, and about 15 semantic boundaries.
- **P50 55M · P80 68M · P95 82M · hard stop 90M** (enforced: token_estimate 45M × breaker 2.0). These include EVC's 41M P50: approving this plan replaces the EVC plans, it does not add to them.
- Reserves inside the units: proof 8 %, integration (S1) 8M, live canary (S8) 4M, cross-domain (S8), recovery 5M. Meta-optimization: 0 resident panes; control-plane target ≤1M for the whole run.
- Expected immediate Live QA saving: **18-30M**. The control plane drops from ~15-30M to ~1-2M, plus 10-25 % on workers from NO_WORK, proof reuse and tier routing. This is a forecast, not measured.
- Estate-wide: the laptop programmes measured 371M (intent/order), 304M (Clock A, old and new), with 91 % inside GSD subagents. Fresh-floor cut + slim packets + zero-model chain should give multi-hundred-M lifetime avoidance. Confidence LOW (EXPLORATORY until the S5 backtest).
- Payback confidence: control plane HIGH (measured inversion 1.9×), estimator MEDIUM, estate LOW.

## 6. Done-gate (Stage A)

The Master Done-Gate is met when:
- A non-Live-QA 2-unit programme runs end to end with zero manual re-arm and zero model on chaining and landing.
- `programme_status` answers from durable state, and repeated calls cost 0 model tokens.
- A successor and a new mission id keep the parent spend.
- A waiting programme has 0 resident processes.
- A known landing runs as a transaction.
- The 8 invariant V-gates are green, with a mutation drill per gate.
- The UKDL entries and the default are applied, and the retired paths are removed.

Then S10, then STOP.
