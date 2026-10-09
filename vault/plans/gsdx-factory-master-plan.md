---
covers: [gsdx-factory, recon-factory, steward, call-units, estimator, gex44-port]
status: PROPOSED (awaiting Owner single approval)
date: 2026-10-09
goal: gsdx-factory-2 (ledger cap 100,000,000 MEASURED)
---

# GSD X Reconstruction Factory: Master Plan v1

Labels: M = MEASURED, D = DERIVED, E = ESTIMATED, H = HYPOTHESIZED, U = UNKNOWN.

## 0. Reality Delta: six facts that change the plan

1. **The canonical factory is the `recon-factory` workstream.** It lives in `Apps\recon_work\wt_keosdtk_home` on branch
   `keosdtk-home`, and its done-gate is Phase 9 VERIFICATION with the CP50 report. gsdx Part B is a recompiled overlay of it.
   - **Done:** phases 1, 01.1, 4, 5 (0bb9786) and 6 (9697c9e), plus 3a (the seam, dcd9178) and the Phase 7 G0 freeze
     (e3b0b82). Phase 2 is nearly done: its A/A gate passed on GEX44 today (cfedba3).
   - **Remaining:** close Phase 2, Phase 3 bulk promotion, the Phase 7 CP50 run, Phase 8 (only if CP50 meets its
     criterion) and Phase 9.
   - **Already paid:** the gen3 tranche has spent at least 10.4M on these phases (M).
2. **S2 and S3 are already built, by `ce-lifecycle-v3`.** That programme writes the same files we would.
   - WU-S3 (ea5cf9c8): the growth estimator and the three-miss DEGRADED mode.
   - WU-S4 (753a2a4a): the predictive lease edge and admission priced in physical calls.
   - WU-S5 and WU-S5b (m-b205bb55bdac, RUNNING): adopting our S1 steward from a byte snapshot.
   - WU-S5c: two fixes we need, F3 (the calls wall goes through closeout) and F1 (no COMPLETED without a receipt).
   - WU-INST2: installs all of the above on the laptop live tree.
3. **GEX44's live install (@1872e9a1) has none of the control plane:** no route_admission, gsd_dossier, steward or
   session_budget_guard (M). Cost-collapse E4a2 is BLOCKED_PREMISE for the same reason. Host health (M): 53 GB RAM
   available, load 0.4, 1.1 TB disk free, agora-mission-sweep timer running.
4. **The KSR/recon runner on GEX44 is READY (M).** Job ksrmb-20261009-090602 passed its A/A gate, and recon_tools has
   dtk and objdiff_cli. "KSR UNKNOWN gates B2" is stale: B2 (population factoring) corresponds to Phase 5, which is done.
   That mapping is H until L1 confirms it.
5. **Authority:** goal gsdx-factory-2 already has a ledger cap of 100,000,000 (M). No Owner terminal action is needed.
6. **Recon rearm task:** PP-ReconFactory-Rearm-20261011 is Disabled (M), so nothing else will arm the recon work.

Iteration-prompt REALITY CHECK. These premises from earlier reports were false:
- "S2/S3 unbuilt" (CLASE 2);
- "Part B costs 38.9M" (CLASE 2);
- "GEX44 is ready to run it" (CLASE 2);
- "the 100M needs an Owner terminal action" (CLASE 2).

## 1. Answers

**1. True state of S1.**
- Mission m-ffb75e73f813 is HALTED.
- Its code is green, re-run by the coordinator: STEWARD 18/18, GOAL 45/45, ADM 44/44 (M).
- Six paths in pp-gsdx-factory-2 are uncommitted.
- Still missing: the 2 mutation drills, the commits, the receipt and settlement. The worker's lease of 491,545 is still
  open.

**2. Can S1 close without a new worker?** Yes. Everything left is deterministic:
- the drills, run through mutation_drill.py;
- 3 pathspec commits;
- the receipt, written from measured data;
- settlement through the worktree's own goal-settle. It writes a `settle` op that the live fold already reads.

**3. Why S1 cost 2.71M against a 763K estimate.**
- **Admission assumed a flat cost per call:** 18,742 x 34 x 1.2 = about 764K.
- **The context grew instead:** from 18,742 to 96,922 tokens over 40 model calls, about +2,005 per call (M).
- **A linear-growth model fits most of it:** at 40 calls it predicts 2.31M; actual was 2.71M.
- **The flat model covered only 28% of the actual spend.** The cause is the estimator, not wasted execution.

**4. Was 61 vs 34 a unit bug, a forecast bug, or both?** Both, and they are separate.
- **Unit bug:**
  - The worker made 40 model calls, exactly the envelope's 40, and 64 tool calls (M).
  - The breaker tripped at 61 tool calls > 1.5 x 40. It compared tool calls against a model-call estimate.
  - The token stop was never reached: 2.61M at the trip, against a 4M stop.
- **Forecast bug:** the token estimate (answer 3).
- **Model-call count:** 40 against the worker's 34 is only 1.18x.

**5. S3 cost model.** C(n) = n·F + g·n(n−1)/2 + n·ō + T_close, with n counted in MODEL calls.
- **Physical calls = r·n,** with r measured per work class: S1 1.6, lc3-S2 1.3, S4 1.0.
- **Measured per-profile terms:**
  - slim-t2 floor F is 18.7–19.0K.
  - Growth g is 2.0K for implementation (S1) and 1.3–1.5K for integration (lc3 S2/S3; their fit is 1,725 at n=4).
  - Top-level F is about 121K (A-G1).
- **Expected verified cost** = C(n) + p_repair·C(n_residual), with p_repair taken from receipts.
- **Epoch length:** average cost per call is F + gL/2 + R/L, which is lowest at L* = √(2R/g). R, the rehydration cost,
  is measured in W3.
- **Delivered as MERGE:** onto lc3's estimator, adding per-class g, r and the closeout tail.

**6. Where the predictive lease edge should have fired.**
- **Admission:** with growth modelled, 34 calls predicts about 2.1M against the 763K that was used. Either price it
  there, or split the unit into 2 epochs.
- **In flight:** about tool call 50, when the closeout still needed (~8 calls) exceeded the headroom left (60 − 50).
  The token edge never needed to fire.

**7. Reserves.**
- **Closeout:** zero-model, as a Certified Closeout Transaction run by the steward.
- **Inside the worker,** protect only the step that makes green work durable: max(4 tool calls, 10% of the calls wall),
  plus 2 calls for the proof run.
- **Recovery:** held at programme level, about 25% of the largest unit, not reserved per unit.
- **Why it matters:** done in-worker at 95K context, S1's closeout tail would have cost about 0.6M. Done outside, it
  costs about 0.

**8. Part A after S2/S3.** Expected 2.5M (range 1.2–4.5M) (E):

| Unit | Expected |
|---|---|
| A-G2 | 0.6M |
| A-G3 (likely MERGE) | 0.4M |
| A-G4 | 0.8M |
| A-G5 | 0.7M |

**9. Part B, bottom-up.** Expected 13.9M (range 3.9–27.3M); see section 3.

**10. Authority needed.**
- A programme envelope of **40M**, with a hard ceiling of 55M, inside the existing 100M ledger cap.
- If goal-declare allows lowering a cap without the Owner, the ledger cap itself is lowered to 55M (U). Otherwise
  arm-chain admission enforces the envelope.

**11. Staying alive on GEX44 without a coordinator.**
- The agora sweep runs every 5 minutes, on top of the ported control plane and the steward.
- Each unit's receipt names its successor, and arm-chain arms it.
- The steward's R3 (unarmed successor) gains the right to arm within the envelope.
- This pane exits after W0 and the first arm.

**12. Automatic lease reconciliation.**
- **Mission workers:** the steward's R1 calls settle_stopped at transcript-measured spend.
- **Every other dead session (new R4):** probes, panes and phantoms. An open hold is settled at measured spend when its
  session has no live process and its transcript is final. With no transcript it stays held as UNKNOWN.
- **Phantom root cause:** renew() always reserves, and on refusal it reserves a final hold. Separately, the guard
  reserves a 750K lease per goal-bound session. Nothing ever closes either one for a dead session.

**13. Economic immunity.** A unit FAILS immunity, and gets an autopsy row, if any of these happens:
- the forecast error exceeds 35% on 3 comparable units in a row (lc3's three-miss → DEGRADED);
- a unit halts on its calls wall while holding green, dirty work;
- any settle is written by hand;
- a fresh worker is spawned only to close out.

**14. Full WSR boundary.**
- **Out of scope:** recorded in gsdx §5 as DEFERRED_EXTERNAL, and in TRANCHE-CP50 as "FULL_WSR is never a budget".
- **In scope:**
  - the 34,159-function Phase 5 matrix, as inventory only;
  - reconstruction attempts only on the preregistered draw (300 + 60 holdout) through CP50/150/300;
  - Phase 3 promotion of the 289 donors and the model matches.

**15. CBR candidates.** Each is promoted only after a second work class shows the effect:
- unit-typed budgets;
- the growth-aware estimator;
- calls-wall closeout;
- the Certified Closeout Transaction;
- R1 + R4 reconciliation;
- receipt-gated completion;
- successor arming within the envelope;
- work-class profiles with maturity levels.

## 2. Execution graph (after approval)

- **W0 — S1 closeout.** ZERO_MODEL, this pane, 3–5 calls.
  - The 2 drills, 3 commits and RECEIPT-S1 with its autopsy.
  - settle_stopped for e422223f, 7013ffb1 and 55c8c721.
  - On the old goal, settle the 6305f97c phantom and the 530d9700 final hold.
- **W1 — wait for convergence.** Zero-hot: the event is lc3's INST2 receipt. W2 runs meanwhile.
- **W2 — L1.**
  - **Deterministic extraction** from both gsdx plans, the recon ROADMAP, the gen3 receipts and the 756-line dataset.
  - **Disposition:** slim-t2 batches.
  - **Gate:** `gsd_dossier dispose --check` exits 0.
  - **Output:** the authoritative remaining graph, plus the Part B ↔ recon-phase mapping.
- **W3 — S2/S3 residual** (MERGE, slim-t2, after INST2):
  - a `calls_unit` field on every budget, and a model-call counter (by message.id) beside the tool counter;
  - per-class g, r and closeout tail;
  - R4 reconciliation, and successor arming within the envelope.
  - **Canary:** the counters must match the transcript, and the breaker must deny on the intended unit. The S1 replay
    must be priced at 2.1M or more, or split.
- **W4 — reforecast.** Deterministic. A change over 25% triggers the iteration prompt. The Owner is woken only if the
  total goes over 40M.
- **W5 — port the control plane to GEX44.**
  - A git bundle of the converged laptop live tree goes to GEX44 live, with a backup tag.
  - The DEPLOY hard-rule class is read first.
  - The guard is wired through the dispatcher, and its DENY branch is driven to prove it.
  - This also resolves cost-collapse E4a2, option (a).
  - UWCP is evaluated here (U).
- **W6 — Part A:** A-G2..A-G5, as L1 dispositions them.
- **W7 — Part B on GEX44.**
  - **Setup:** keosdtk-home is bundled to a GEX44 clone. The laptop's 569 dirty paths are inventoried first and never
    touched.
  - **Order:** P2 close → P3 → CP50 (a 10-row priced canary first) → P8 if the criterion is met → P9 with one targeted
    Opus red team.
- **W8 — programme closeout.** Deterministic, plus one slim writer for the knowledge files.
- **CP50 dependency** on ce-lifecycle-v3 S6 (~5.5M, unfunded there): L1 rules it WAIT or SUPERSEDED. It is carried as
  a contingent line.

## 3. Token budget (processed tokens, deduplicated by message.id)

**Sunk spend**
- **Old goal gsdx-factory: 14,020,691 (M):**
  - A-G1: 3,276,310;
  - coordinator 530d9700: 10,362,060, misattributed through Set-Location;
  - open holds: 382,321.
- **gen3 recon tranche:**
  - 9,881,933 (M) for P5 through P2a;
  - R1: 553,590 (M);
  - P2b: 1.0M or less, exact figure U.

**Current programme, gsdx-factory-2**
- **Workers:** 2,839,056 (M).
- **Ledger:** used 3,862,583, of which open holds 1,330,160 (M).
- **Real spend still unsettled inside those holds:** 306,633 (D).
- **Releasable after settlement:** 1,023,527 (D).
- **This coordinator pane:** U. It is not bound to the goal; W0 measures it.

**Remaining work** (all E unless marked)

| Line | Expected | Lower | Safety |
|---|---|---|---|
| S1 closeout | 0.5 | 0.3 | 0.8 |
| S2 residual | 0.3 | 0.0 | 0.6 |
| S3 residual | 0.4 | 0.2 | 0.8 |
| L1 | 2.0 | 1.2 | 3.5 |
| GEX44 port | 1.0 | 0.5 | 2.0 |
| Part A residual | 2.5 | 1.2 | 4.5 |
| B: P2 close | 0.4 | 0.2 | 0.8 |
| B: P3 promotion | 1.0 | 0.5 | 2.5 |
| B: P7 CP50 (LOW confidence) | 3.5 | 1.5 | 6.0 |
| B: P8 CP150/300 (p = 0.5, H) | 5.0 | 0.0 | 12.0 |
| B: P9 seal | 2.0 | 1.2 | 3.0 |
| B: rows not mapped to a phase | 2.0 | 0.5 | 3.0 |
| Contingent lifecycle stage (H) | 0.0 | 0.0 | 5.5 |
| Proof reserve | 1.5 | 0.5 | 2.5 |
| Closeout reserve | 0.5 | 0.2 | 1.0 |
| Recovery reserve | 2.5 | 1.0 | 4.0 |
| Control plane (≤7% of spend) | 1.5 | 0.8 | 3.0 |
| **Total (M tokens)** | **26.6** | **9.8** | **55.5** (every tail at once) |

**Envelope**
- **Lower bound:** 9.8M.
- **Expected verified completion:** 26.6M.
- **Safety envelope:** 40M, i.e. P8 and CP50 at full size plus 30% on everything else.
- **Hard ceiling:** 55M.
- **Model calls:** 550–900 expected. Tool operations: about 1.3–1.6x that. Semantic boundaries: about 30.
- **Confidence:** MEDIUM for the S/L/A blocks (5 or more slim samples). LOW for P7 and P8, where CP50 is itself the
  measurement.

**Against the old plan's 60–65M remaining:** the gap is not savings.
- About 10.4M of Part B was already paid in gen3's ledger.
- About 3M of S2/S3 was paid in lc3's.
- Several Part B rows correspond to phases that are already finished.

**Tranches.** These are steward-side gates and advance automatically on a receipt plus a reforecast:

| Tranche | Covers | Size |
|---|---|---|
| T-A | W0–W6 | 8M |
| T-B1 | P2, P3, CP50, P9, unmapped rows | 16M |
| T-B2 | P8, only if the CP50 criterion is met | 12M |
| Reserves | | 4M |

## 4. Risks and falsifiers

- **lc3 stalls** in S5b/S5c/INST2: W3 and W5 wait, while W2 and P2 close proceed. If the stall passes 24 h, gsdx lands
  its own original S1 code itself.
- **CP50 per-escalation cost is U:** the 10-row canary prices it before the rest is spent.
- **Concurrent writers:**
  - lc3: gsd_mission.py, the guard, ledger.py, mission_spend.py;
  - cost-collapse: route_admission.py and gsd_mission.py, with uncommitted E4a edits on the live tree;
  - gen3: the recon worktree.
  - gsdx edits none of these while their units run.
- **The GEX44 port is a live deploy:** the DEPLOY hard rule applies, with a backup tag and a rollback path.

## 5. What one approval covers

- **Scope:** Part A, plus recon-factory through Phase 9. Full WSR stays excluded.
- **Authority:**
  - the 40M envelope, with a 55M hard ceiling, inside the existing ledger cap;
  - recon-factory funding moves from the per-plan gen3 tranches to goal gsdx-factory-2.
- **Ownership:**
  - S2/S3 are MERGEd into ce-lifecycle-v3;
  - the GEX44 control-plane port also settles cost-collapse E4a2 as option (a).
- **Execution:** autonomous.
