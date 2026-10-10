---
covers: [durable-goal-liveness, effect-authority, scoped-holds, typed-waits, safe-closeout, stop-reason, owner-decision-queue, gex44-runtime-port, dws-recovery]
status: APPROVED (Owner "y" in chat, 2026-10-10 ~18:40 CEST, pane 16a354ea) -- the 6 bundled decisions in section 6 included
extends: vault/plans/autonomy-convergence-MASTER-PLAN-2026-10-10.md (S0-S4 DONE, S5-S10 in flight) ; vault/plans/durable-goal-lease-2026-10-09.md (dgl W1b/W2) ; vault/plans/event-driven-wake-caa-2026-10-08.md
source: Orca X DWS pane 16a354ea, read-only Reality Delta 2026-10-10 17:40-18:25 CEST
---

# Lifecycle Autonomy (Stage C of Autonomy Convergence) + DWS recovery

## 1. Reality delta (measured, read-only)

### DWS / goal dws-exec
GEX44 runs an isolated runtime, /home/kobii/ce5-env, which is CPP snapshot cd389b50 + 6d8ca5c4 + local patches.
- **Budget:** dws-exec has cap 10,000,000, settled 6,677,167, open 0, remaining 3,322,833. ce-a5 has used 8.32M of 20M.
- **The only non-terminal mission is m-d9395ab760bc** (X01r, PREPARED). Its owner_hold reads "route DEFER: needs
  276,222 but only 206,524 remains", set at arm time while 3 running sessions held reservations. Those reservations
  have since settled.
- **Why one hold freezes the whole goal:** gsd_mission.goal_refusal says "A Goal hold covers every unit". So X03r,
  X04r, X11 and X18–X20 fail with "goal held", and X12–X14 wait on X11.
- **Hosts:** no worker processes and no orca serve on GEX44. codex reports "Logged in using ChatGPT"; claude is
  logged in.
- **Records:** X01–X10 have one. X15, X16 and X17 do not.
- **Dirty, uncommitted work on disk:**
  - row-71: 3 paths
  - row-72: 5 paths (orchestration db/types + 3 new files)
  - row-73: 5 paths (3 harness scripts + 2 new tests)
- **Owner authority** ("autorizo el redespliegue"; 6 live turns per unit) exists only as prose in packets
  X01r/X03r/X04r and commit 9343202. It is not machine-checkable, and nothing debits turns.
- **Economics (23 sessions):**
  - 6,677,167 tokens over 282 calls = 23.7K per call. The first call is 5.4K.
  - Tranche-2 sessions ran 16–20 calls, with context climbing to 40–70K.
  - Route call estimates of 10–13 came from admission maxima, not from the class posterior. So the 1.5× breaker cut
    four siblings in a row.
- **Residual:**
  - Untouched: 23 claims (13 bounded_coding / 5 known_transform / 5 novel, 84 obligations).
  - Touched, not closed: 19 claims.
  - owner_reality: 2 claims (14 obligations).
  - Sleeping: 46.
  - Matrix: PASS 11, PARTIAL 35, ABSENT 29, UNKNOWN 1.

### CPP
Live PP is feature/knowledge-acquisition, with many dirty paths and other writers. The autonomy writer is pp-ucda-wt
(feat/ucda).
- **Autonomy Convergence** (Owner "y" 2026-10-10):
  - S0–S4 are DONE and landed: land_worktree, the programme spend/authority view, the registry chain tick for N
    programmes with continuation insert, and programme_status.
  - EVC U1/U3/U4/U5 have landed. S5–S10 are in flight.
  - The plan DEFERS the GEX44 control-plane port to "Owner later".
- **dgl** (lease epochs + lineage) is in pp-dgl. **wake_check + GoalLog** event wake exists (caa-wake).
- **What the GEX44 runtime lacks:** chain_registry, land_worktree, gsdx_chain, programme_status, goal_chain,
  work_proof and tier_routing.
- **Renewal limits:** "already renewed" stops a lineage after one renewal (HALT_CONTINUE_MAX_RENEWAL=2).
- **Classifier:** the Claude Code auto-mode classifier that denied the chain pass is a HARNESS control. CPP cannot
  override it.

### Correction after approval (CLASE 2, measured 18:45)
- **The premise that S0–S4 landed was false.** The live PP HEAD d9d0e8e8 has S1 only (land_worktree b97ced4a),
  plus gsdx_chain and work_proof. S2–S4 (chain_registry, programme_status, goal_chain) and EVC U1–U5 exist only on
  feat/ucda (944ed790), which has diverged from live HEAD.
- **Consequence:** Stage C bases on feat/ucda 944ed790. It lands only after autonomy-convergence lands its own work
  (land_worktree rebases onto live, with an overlap check).
- **C0 moves LAST:** a deterministic switch of ce5-env/pp to the landed commit, with rollback. It stays out of the
  runtime-under-use path while workers run on it.

### Phase-4 audit injections (auditor report scratchpad/autonomy/audit.md: 1 BLOCKER, 9 MAJOR, 2 MINOR -- all accepted)
1. **BLOCKER, C1.** Every hold writer records `hold.kind` (owner | admission_defer | cost_breaker | readmit_fail).
   - A legacy hold with no kind is treated as an Owner hold: goal-wide and never auto-released. X01r is one.
   - D2 releases X01r through the Owner CLI under bundled decision D2, never by parsing reason text.
2. **C1, release must lead to a launch.** A release of an admission_defer hold re-runs admit_route on the recorded
   route, with the packet/route hash checks.
   - D2 prechecks both admission terms, the mission envelope and goal headroom, and records which one bound.
3. **C1 safety.** cost_breaker holds stay goal-wide (or class-wide) and never auto-release. Only admission_defer
   auto-releases, and only after a fresh ADMISSIBLE verdict.
4. **C4 safety.** The closeout reserve is BOUNDED in both calls and tokens and charged to the goal lease.
   - Only an exact pathspec `git commit -F` command shape is eligible.
   - Drill: reserve exhausted means deny.
5. **C4 salvage.** Use a private GIT_INDEX_FILE + commit-tree to refs/salvage/<mid>. HEAD and the index are never
   touched, only paths the worker itself wrote are included, and there is a concurrent-writer drill.
6. **C0 runs LAST** as one deterministic switch:
   - only when no record is RUNNING or LAUNCHING;
   - take a state-dir preimage first;
   - then a dry tick and the ce-a5 canary;
   - roll back to the previous commit if needed.
7. **File-ownership table versus autonomy S5–S10** (gsd_mission, mission_steward, session_budget_guard). Stage C
   rebases onto the landed S7 commit. land_worktree refuses when files overlap.
8. **C2: the runtime never mints authority.**
   - A receipt is minted only through an Owner path: a real-console --owner, or the Owner approving the sha256 of the
     exact receipt bytes. The runtime may only debit or narrow a receipt.
   - D3 moves after C2. The D3 receipt bytes are the decision-3 specs of this approved plan, and its provenance is
     this plan file's sha256 at approval.
9. **C5.** No unbounded succession: each lineage has a spend ceiling tied to its authority. Progress means a
   receipt, test or commit delta, not a tree fingerprint.
10. **C6** depends on finding 1. Steward R2 exempts only Owner-kind holds.
11. **Every unit ships its V-gate plus a mutant**, not only C8. Examples:
    - goal-wide goal_refusal turns C1 red;
    - an Owner-kind hold never auto-releases;
    - an exhausted reserve denies.
12. **Self-hosting.** The runtime that executes Stage C is pinned (CODE_ID stable). It switches only after landing.

Revised order: D1 (deterministic, now) → C1 → C4 → C2 → D3 → C3 → C5 → C6 → C7 → C8 → C0 → D2/D4/D5.

## 2. Root-cause matrix
| incident | verdict | evidence |
|---|---|---|
| AUTHORITY_PROPAGATION_FAILURE / BRITTLE_TEXTUAL_AUTHORIZATION | CONFIRMED | Authority is packet prose; a new session re-judged it |
| AUTHORIZED_EFFECT_REESCALATION | CONFIRMED (harness) | Classifier denial after an explicit Owner go |
| OVERCOARSE_PRODUCTION_DEPLOY_CLASSIFICATION | PARTIAL | Harness-side; CPP has no effect classifier |
| "X01r hold came from the deploy denial" | REJECTED | The hold is an admission DEFER under in-flight reservations |
| OVERBROAD_OWNER_HOLD + HEAD_OF_LINE_BLOCKING | CONFIRMED | goal_refusal: a goal hold covers every unit |
| UNTYPED_WAIT_STATE | CONFIRMED | READY_FOR_LIVE, DEFER and breaker cut all collapse into HALTED/PARTIAL |
| LIVE_INFRA_COUPLING / BUILD_LIVE_PROOF_CONFLATION | CONFIRMED | One unit = build + leg-writing + live proof |
| FORECAST_LATE_LEARNING / CALL_CAP_CLIFF | CONFIRMED | Four sibling cuts at estimate × 1.5 |
| PROTECTED_CLOSEOUT_STARVATION / DIRTY_UNRECORDED_WORK / SEMANTIC_RECEIPT_TOO_LATE | CONFIRMED | X15–X17 |
| LEASE_EXHAUSTION_STOP | CONFIRMED (GEX44) | "already renewed"; the chain never re-arms STOPPED. Laptop S3 has continuation insert |
| NO_EVENT_WAKEUP | PARTIAL | A deterministic 5-min sweep exists; no typed live-lane wake |
| OWNER_INTERRUPTED_FOR_MECHANICS / OWNER_CAPITAL_MECHANICS | CONFIRMED | Re-authorize + interactive cap typing |
| PROCESS_EXIT_STOP / CONTEXT_ROTATION_STOP | PARTIAL | One renewal, then stop |

## 3. Architecture: converge, do not build
Stage C closes only the gaps that Autonomy Convergence does not own. It adds to its obligation ledger, uses its
registry/chain tick/programme_status/land_worktree, and builds no new registry, event bus or OS.

| unit | gap | owner extended | work |
|---|---|---|---|
| C0 | GEX44 runtime port | ce5-env/pp | Pin the isolated runtime to a landed CPP commit that has S0–S4 + EVC. Keep the local patches as commits. Canary ce-a5 + dws-exec dry tick. The shared GEX44 CPP tree is not touched. |
| C1 | Scoped holds + stale-DEFER release | gsd_mission.goal_refusal / admission | A hold blocks its unit + after-closure only. A DEFER hold auto-re-admits when settled headroom returns (known recovery, zero model). |
| C2 | Effect Authority receipts | mission_spend lineage / programme authority (S2) | A durable capability object: effect class, target, environment, preconditions, rollback, counters (live turns debit), expiry/invalidators, revocation, provenance. Inherit downward only, subset-checked. |
| C3 | Typed unit states + live lane | receipts / chain / programme_status | READY_FOR_LIVE, COMMIT_PENDING, WAITING_INFRA, WAITING_AUTHORITY, WAITING_CAPITAL. A deploy receipt is a wake predicate for READY_FOR_LIVE units (wake_check). |
| C4 | Safe closeout + dirty-work salvage | session_budget_guard + mission_steward | A protected closeout reserve (record/commit calls are never denied). On a cut, the steward commits the dirty set to a salvage ref with a typed residual. Route calls come from the class posterior (EVC), not admission maxima. |
| C5 | Unbounded succession within parent authority | gsd_mission renewal + S3 continuation | A successor while the goal has headroom AND the last session made progress (no-progress breaker kept). |
| C6 | Stop-reason + semantic stall | programme_status + chain tick | Every terminal carries a machine stop reason from the allowed set. OPEN + nothing live + no successor + no wait + no Owner boundary = SEMANTIC_STALL, which re-ticks or raises. |
| C7 | Owner decision queue | vault/OWNER_QUEUE.md + BLOCKED_HUMAN receipts | Non-blocking decisions queue; scoped holds keep independent units running. |
| C8 | Autonomy CI canary matrix | S7 invariant V-gates | Inject lease exhaustion, worker crash, context clear, provider failure, hold, live-infra down, dirty work, proof/commit failure, duplicate wake, authority expiry/revocation, parent exhaustion. Each resolves to continue / typed wait / Owner boundary. |

Order: C0 → C1 + C4 (they unblock DWS) → C2 → C3 → C5 → C6 → C7 → C8.
- **Execution:** slim GEX44 workers, the ce-a5 recipe at about 0.6M per unit. CPP lands only through land_worktree,
  after autonomy S6/S7 land, with an overlap check. No push.
- **Self-hosting:** from C1, Stage C runs on its own repaired chain.

### Owner-map refinements (read-only subagent scan, live PP d9d0e8e8; full map in pane scratchpad autonomy/owner-map.md)
- **C1:** set_owner_hold is called by the breaker, arm_chain and re-admission failures (gm:1274). goal_refusal
  (gm:3536) refuses every unit. Fix: a machine hold carries a typed release condition and a unit scope; only an
  Owner hold stays goal-wide.
- **C2 = MERGE, not new:** today authority is free text spread across 5 stores (arm authority gm:3562, approvals
  gm:3687/3746, ledger declare_cap(approval_id)/correct(authority), lease AUTHORITY_REQUIRED, owner_queue). One typed
  receipt with these as readers. It also needs a producer: today only the tests write approval files.
- **C3/C6 = CONNECT** the gsd_x goal vocabulary (`modules/gsd_x/goal/reconcile.py`: "empty queue is not success",
  BLOCKED must name an external condition) instead of a third state enum. gsd_mission halt reasons are free text, and
  renewal string-matches "budget:".
- **C5:** unify the two renewal regimes: budget renewal MAX_RENEWALS=3 (gm:2163), halt-continue "already renewed"
  (gm:2512), HALT_CONTINUE_MAX_RENEWAL=2.
- **C6:** steward R2 (mission_steward.py:226) treats any owner_hold as covered and only writes incidents, so a
  machine-held goal sleeps forever. That is the semantic-stall bug, and C6 fixes it there.
- **C7 = CONNECT** modules/owner_queue/owner_queue.py:165 to holds and AUTHORITY_REQUIRED.
- **C3/C1:** `after_settled` has 0 hits in CPP (it exists only in my GEX44 chain patch). Upstream it into
  gsdx_chain/tranche_driver as fan-in.
- **Event wake:** polling only (5-min sweep). The autonomy plan rated a new bus NEGATIVE_ROI. C3 adds typed wake
  predicates through wake_check, not a bus.

## 4. DWS recovery (after C0 + C1 + C4 at minimum)
- **D1 preserve:** salvage-commit row-71/72/73 dirty work. Write records X15–X17 from their transcripts, typed
  IMPLEMENTED_UNVERIFIED / RECORD_PENDING.
- **D2:** release the stale X01r DEFER hold through C1 (3.32M headroom exists). Independent units re-arm.
- **D3:** compile the Owner's prior chat approvals into C2 receipts:
  - the GEX44 orca serve redeploy (isolated HOME, preimage of ~/.codex + ~/.claude, verified restore, zero leftover
    processes);
  - 6 live turns per unit for X03r/X04r.
- **D4 live lane:** batch the READY_FOR_LIVE two-host legs into one laptop e2e build plus one GEX44 disposable root.
  The p16 regression is included.
- **D5 reprice:** reprice the residual from the 23-session posterior, then continue within 3.32M. If the posterior
  needs more, stop once at one capital decision.

## 5. Token budget (processed tokens; GEX44 slim ≈ 23.7K per call measured; ce-a5 units ≈ 0.6M)
| workstream | low | P50 | high |
|---|---|---|---|
| Reality + root cause (sunk, this pane; main-pane calls are 100K+ each) | 2M | 3M | 4M |
| C0 GEX44 runtime port + canary | 0.4M | 0.7M | 1.0M |
| C1 scoped holds + DEFER release | 0.5M | 0.7M | 1.0M |
| C2 Effect Authority receipts | 1.0M | 1.4M | 2.0M |
| C3 typed states + live lane | 0.8M | 1.1M | 1.5M |
| C4 safe closeout + salvage + posterior routes | 1.0M | 1.4M | 2.0M |
| C5 succession within parent authority | 0.6M | 0.9M | 1.2M |
| C6 stop reason + semantic stall | 0.6M | 0.9M | 1.2M |
| C7 Owner decision queue | 0.4M | 0.6M | 0.8M |
| C8 Autonomy CI canary matrix | 1.0M | 1.4M | 2.0M |
| landing via land_worktree (laptop) | 1.0M | 1.6M | 2.5M |
| cross-domain canary (non-DWS) | 0.5M | 0.7M | 1.0M |
| KV / FIOS / UKDL / CBR | 0.4M | 0.6M | 0.8M |
| control plane (meta-optimization tax) | 1.5M | 2.5M | 4.0M |
| DWS D1 preserve + D3 receipts + D5 reprice | 0.5M | 0.8M | 1.2M |
| recovery reserve (15 %) | — | 2.2M | 3.3M |

- **Stage C + DWS control:**
  - Semantic lower bound ≈ 6M.
  - LOWER 10M · P50 15M · P80 19M · P95 25M.
  - Hard authority asked: goal `lca`, cap 19M (P80), breaker on. Anything above P80 stops at one capital decision.
- **DWS live lane (D4) + productive work:** inside the existing dws-exec authority (3.32M left). No new money now.
- **DWS full residual** (indicative only; recompiled in D5 under the repaired topology):
  - Semantic lower bound ≈ 12M.
  - LOWER 22M · P50 34M · P80 42M · P95 52M.
  - For comparison: the old forecast was 31.6M (underfit, n=1 per class), and my current-topology guess was ≈ 40M+.
  - The repaired topology saves mainly on: cut-and-re-pay sessions, closeout denials, holds idling capacity, and
    builds conflated with live proof. Estimated saving 15–25 %. LOW confidence.

## 6. Owner decisions bundled in the one approval
1. Goal `lca` cap 19M for Stage C + DWS control (new capital; no self-raise; P80 overrun = one capital stop).
2. GEX44 isolated-runtime port (ce5-env only; the shared GEX44 CPP tree is untouched). This is the DEPLOY-class item
   the autonomy plan deferred.
3. Compile the chat approvals into durable receipts, valid 7 days or until an invalidator fires:
   - X01r GEX44 orca serve redeploy (isolated HOME, ~/.codex + ~/.claude preimage, verified restore, zero leftover
     processes);
   - 6 live turns per unit for X03r/X04r.
4. Execution plane: receipt-covered effects run in the GEX44 deterministic runtime and its worker sessions, never
   from this pane. If a worker session's own classifier denies one, the unit goes WAITING_AUTHORITY in the queue. No
   route-around.
5. No push. Land into live PP only via land_worktree after autonomy S6/S7 land. Never write in pp-ucda-wt.
6. dws-exec cap unchanged. The DWS capital decision is deferred to D5 with LOWER/P50/P80/P95.

## 7. Modes, rollback, canaries
- **Modes:**
  - ULTRA: C2 (authority), C5 (succession policy).
  - PLAN: C3, C6.
  - EXECUTION: C0, C1, C4, C7, C8, D1–D5.
- **Rollback:**
  - Each unit is a revertible land_worktree landing with a kill switch env.
  - The runtime port keeps the previous ce5-env/pp commit to roll back to.
- **Canaries:** C8 matrix + the S8 cross-domain canary + one non-DWS lifecycle canary on GEX44 (ce-a5 small unit).
