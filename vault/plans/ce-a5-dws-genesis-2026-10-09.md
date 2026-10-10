---
covers: [ce-a5, dws-genesis, semantic-demand, lower-bound, non-compute, reality-set-cover, visual-residual, resource-admission, interrupt-budget, state-projection, dws-recompile]
status: PROPOSED (awaiting Owner boundary 1)
date: 2026-10-09
---
# CE Amendment A5 — DWS as genesis benchmark for global cognitive deflation

Status: PROPOSED. No mutation was made by the scan except this file and scratch analysis.
Approval phrase: **"go a5"**. Boundary 2 (after the Master Done-Gate): APPROVE DWS EXECUTION or OPTIMIZE FURTHER.

## 1. Reality delta (measured 2026-10-09 ~21:30 Madrid)

CPP already owns this programme. It is not new:
- Cognitive Economy gen2 is the owner. Amendment A4 ("estate rearm") was approved on 10-08. Goal `ce-a4` has a cap of 16.6M,
  2,435,335 used and 14,164,665 remaining. Of its W0..W3 units, only P1 has landed (goal-autopsy, on LIVE at 81301310
  today). W0 has not been armed, and the duplicate W0 mission m-4bf75e9e8ecc is held.
- `ce-unify` (today) holds a ledger of 50 obligations from the previous dataset: 2 already done, 19 EXTEND, 16 OWNED, 7 REJECT and
  6 UNKNOWN. Its 7 REJECTs are Context VM (D-39), superoptimizer (D-36), capital allocator (D-48), balance sheet (D-30),
  compiled research (D-42), "APIs make wrong impossible" (D-33) and "ask why" (D-14).
- Other active CE goals: ce-lifecycle-v3 (14M cap, 8.49M used); cost-collapse (BLOCKED); ce-a3b-r (over cap).
- About 25 CE worktrees, and 15 non-terminal missions across the estate. The main CPP checkout is dirty with other sessions' files,
  so it is a concurrent-writer surface.
- Quota: `usage_index burn` reports MONITOR_FAILURE, so the weekly % is UNKNOWN. One of 4 weekly windows (Sun 18:00Z) is REJECTED
  until 2026-10-11 18:00Z. This session runs, so at least one account has capacity.
- DWS: HEAD 466b62d82 (2026-10-02), no commits since then. All 4 Ralph missions are HALTED. The claim graph is the same as the 91-claim compile.

DWS trace evidence (deterministic, read-only, 312 transcripts, 10,985 calls, 3.10B context tokens):
- p50 context per call is 265K and p90 is 430K.
- Subagents account for 86 % of calls and 87 % of tokens.
- 64 of 311 sessions ran more than 60 calls and carry 84 % of tokens. 14 ran more than 150 calls and carry 46 %. The largest is a single
  Sonnet subagent with 609 calls whose context grew from 150K to 492K.
- The fixed first-call floor is p50 102K, and subagents start at about 150K. That floor alone is about 1.1B (36 %): baseline rent, not semantics.
- There is about 1 tool per call. Of 3,946 reads over 1,060 paths, STATE.md was read 123 times, the matrix 85 and ROADMAP 35. There are 157 `sleep 1`
  and 37 poll loops.
- Conclusion: the 424 calls per step are mostly **long-lived conversational subagents paying floor plus accumulated history
  on every serial tool step**. Model choice is a minor lever (6 %). Missing machinery is the major one.

## 2. Thesis

This is CE gen2 **Amendment A5** (HR-NOVELTY-001: no new programme, no new OS). A5 = finish the A4 substrate, plus a
DWS-genesis delta that A4 and ce-unify do not own. A4's approved 14.16M stays A4's money, and A5 adds its own goal and cap.
Execution uses A4's own grammar: one compiled packet per slim Sonnet worker, `gsd_mission arm --no-launch` + envelope + admit,
chained by `tranche_driver`, two-strike stop, and caps that are never raised. The mission is armed via Ralph (`gsd_mission`), but **not**
with raw `/gsd-autonomous`. The raw GSD grammar is the old architecture (measured at 162.2M on gsdx-pcc).

## 3. Obligation ledger (summary; full ledger is unit U0's deliverable, merged into ce-unify's)

The dataset holds about 264 numbered ideas plus the budget report. They collapse into the families below.

| Family | Dataset ideas | Disposition | Owner |
|---|---|---|---|
| Work/No-Work/No-Compute, extinction-first order | P1 1-3, 35, 50-56; P3 3, 12, 91-98 | EXTEND | A4 W2b (dossier before launch) plus A5-U3 (NO_COMPUTE class) |
| Semantic demand, obligation vs computation, lower bound, overhead multiplier | P2 1-4; P3 1-2 | IMPLEMENT_NOW (narrow) | A5-U3 extends `cost_to_completion.py`, no new graph store |
| Family factoring (bounded_coding), known_transform zero-model | P1 3-5, 38-42 | EXTEND | A4 W2b COMPILED_UNIT plus A5-U3 family classes |
| Semantic CSE / singleflight / reason-once | P2 9-10; P3 6-7, 18-20 | DEFER_INSUFFICIENT_EVIDENCE beyond what exists. Only goal singleflight is LIVE (`gsd_mission.py:3483`). Gen1 pillar G (CSE) was **falsified**, so negative-investment memory applies; U2 reopens the QUESTION by measuring duplicate derivations in DWS. The producer-kill canary runs on the existing goal singleflight (U7) | ce-unify D-37 / A4 W1a |
| Read-once / state projection / Markdown as view / SSA | P1 13-15; P3 13-17, 19 | EXTEND | A4 W2c ContextImage plus capsule-v2 (Context Compiler is SPEC-ONLY/UNDECIDED; SSM/UCVM absent as code); A5-U8 GSD STATE projection |
| Proof-once / affected proof closure / subsumption / assurance | P1 21-23; P2 18-20; P3 22-23 | EXTEND, narrowly. Gen1 pillar P (proof reuse) measured 0.50 % and was **falsified** at that envelope; `verified_reuse.py` is BUILT-NOT-WIRED. DWS's envelope differs (repeated full re-verification), so U2 measures it before anything is wired | A4 W2b proof transaction |
| Reality-once / set-cover / Owner interaction compiler | P1 24-26; P3 24-26 | IMPLEMENT_NOW | A5-U4 (DWS has 2 owner-reality claims plus a multi-PC session) |
| Visual residual compiler (region diff, failure mask, freeze) | P1 27-29 | EXTEND the existing numeric gate in the `image-calco` skill (`gate_boxes.py`, `detect_scale.py`). CPP's own `sleepless_qa/verdict/visual.py` asks a model, which is the thing to replace | A5-U5 |
| Resource admission (RAM headroom) | P1 30-31 | IMPLEMENT_NOW. Verified absent: `host-memory-floor.js` only warns, and `wait-ram` is a soft wait; nothing refuses a launch | A5-U6 in `gsd_mission` launch path |
| Interrupt provenance, purity, semantic interrupt budget, stall trip | P1 33-36, 48; P2 6-8; P3 57-61 | EXTEND | the cost breaker exists (token x estimate); A5-U7 adds the progress-stall trip and labels from autopsy |
| Trace mining, sequence-to-primitive, flamegraphs, counterfactual lab | P1 7-12, 46-49; P2 31-34; P3 31-32, 75-76 | EXTEND | goal-autopsy (LIVE) plus A4 W3 PGO; A5-U1/U2 run them on the DWS corpus |
| Context VM, page-fault economics, weighted cache, thrash detector | P1 16-18; P2 22-25; P3 28-36 | DEFER_INSUFFICIENT_EVIDENCE: ce-unify REJECT D-39 stands; U2 reopens the QUESTION by measurement only | — |
| Tool/capability virtualization, progressive disclosure, tool output ABI | P1 19-20; P2 30, 53-55; P3 40-41, 50 | NEGATIVE_ROI for tool schemas: Gen1 pillar C measured them at 0.002 %, and the harness already loads schemas lazily. Skills are already progressive (jit_skill_loader LIVE). Tool-output projection is MERGED into A4 W3 "receipt by reference". U2 still attributes the 102K floor by source, to find the real rent | A4 W1c / W3 |
| Constitutional compiler, prompt extinction, zero-prose ratio | P2 29; P3 45-52 | EXTEND | A4 W1c (prompt extinction #1) plus D-32 rent ledger |
| Role extinction (planner/reviewer/coordinator/researcher) | P2 60-67; P3 53-54 | EXTEND | A4 W2b/W2c |
| Superoptimizer / e-graph / cognitive exchange / futures / shadow price / VOI scheduler | P2 11-15, 31; P3 4-5, 8-12, 27 | NEGATIVE_ROI (ce-unify D-36 holds): one consumer, no measured basis. The "smallest useful e-graph" = alternative satisfiers listed per obligation in U3 | — |
| Capital allocator, balance sheet, debt register, NPV | P1 59-60; P2 39-40, 92-95; P3 80-82 | MERGE: a ranking field in the ledger plus one NPV field in autopsy (D-29). The standalone allocator stays REJECT (D-48) | A4 W3 |
| Economic theorem registry, negative investment memory, holdouts, mutation testing, CI, SLOs | P2 72-84; P3 77-89 | EXTEND | A4 W3 (UKDL via CEPS, Cognitive CI, Canary 1 non-PP repo); A5-U9 holdout replays |
| Architecture PGO, maintainability NFR, radius budgets, token-aware API | P2 41-49; P3 — | DEFER_INSUFFICIENT_EVIDENCE: no measured cost-of-change per module yet (D-31 UNKNOWN). U1 emits per-file attribution, and the decision is taken from that | — |
| Half-life metrics, deflation SLO, call amplification, velocity | P2 84-91; P3 61-64 | EXTEND | A4 sec. 9 deflation definition; A5-U10 reports them for DWS |
| Fresh-project auto-inheritance, CBR ratchet | P1 61-62; P3 85-86 | OWNED | A4 W1c/W3 (CBR artifact, Canary 1) |

OMITTED = 0. Any idea U0 cannot place goes to UNKNOWN, with the missing number named.

## 4. Units (each = one packet, one slim worker, deterministic done-gate, receipt)

| Unit | Depends on | Deliverable | Done-gate | Budget (target / stop) |
|---|---|---|---|---|
| A5-U0 | — | Full ledger (264 ideas, one disposition each) merged into ce-unify's ledger | every idea id has a row; count check is deterministic | 0.8M / 1.0M |
| A5-U1 | — | DWS trace corpus: typed call ledger (session, role, tool, read target, poll, phase, matrix delta) with provenance labels (NOVELTY/STATE_MISS/CONTROL_LOOP/REDISCOVERY/RECOVERY/…), tool-sequence n-grams and context flamegraph by object | byte-identical regen; a planted mislabel fixture goes red; numbers reproduce §1 | 1.5M / 1.8M |
| A5-U2 | U1 | Counterfactual replay of DWS under: slim floor, session rotation at N calls, read-once projection, poll→event, affected-proof closure, no planner/reviewer. Includes the tool-schema-rent and Context-VM questions | each policy has delta tokens/calls with stated assumptions; a negative result is recorded in negative-investment memory | 1.2M / 1.5M |
| A5-U3 | U1 | `cost_to_completion` semantic stage: claims → obligations → computations with NO_WORK / NO_COMPUTE / FAMILY / SHARED_OBS / SHARED_PROOF; irreducible-transition lower bound; overhead multiplier; per-class interrupt budget | V-SEM suite; old PHASE_MULTIPLIER refusal still red; mutants (stale dependency, missing invalidator, family without proof) refused | 2.5M / 3.0M |
| A5-U4 | U3 | Reality set-cover plus Owner session packet (claims → observations → minimum session plan; post-processing distributes evidence) | greedy cover on DWS fixtures; a duplicate observation is never planned twice; missing evidence leaves the claim open | 1.2M / 1.5M |
| A5-U5 | — | Visual residual compiler, built as an extension of `image-calco`'s numeric gate: region grid diff, failure mask, frozen passing regions, deterministic final gate (project-agnostic) | identical PNG → PASS; one shifted region → mask names only it; tiny canary on one synthetic card, not the DWS product | 1.5M / 1.8M |
| A5-U6 | — | Resource admission in `launch_worker`: free RAM below the class floor → REFUSE / reroute / wait (never warn-only) | planted low-memory reading refuses; an UNKNOWN reading never admits | 0.8M / 1.0M |
| A5-U7 | U1 | Semantic-progress stall trip in the supervisor (N calls with no commit, receipt or matrix delta → stop + recompile), plus the singleflight producer-kill canary | planted stall trips; killed producer: no hang, no duplicate effect, demand id kept | 1.2M / 1.5M |
| A5-U8 | A4 W2c | GSD STATE projection: worker card gets frontier, changed deps, open unknowns and proof state, not STATE.md | DWS card ≤ 8 KB vs 53K-token STATE; replayed worker has no fault on the 3 sampled tasks | 1.5M / 1.8M |
| A5-U9 | U2, U3 | Holdout replay on 2 non-DWS traces (one CPP mission, one other project) for the policies U2 promotes | a promoted policy shows benefit on ≥ 1 holdout, or stays DWS-local | 1.0M / 1.2M |
| A5-U10 | all + A4 W1-W3 | READ-ONLY DWS recompilation and the new budget (format of the mission's §FINAL) | budget derived from obligations, not from 6.5B × %; old vs new table | 1.0M / 1.2M |
| Coordinator | — | arm, read receipts, update RESUMPTION; no reasoning in the loop | ≤ 0.6M per pane, two-strike | 0.6M / 0.6M |

Order: U0, U1, U5, U6 start at once (independent files). U2, U3, U7 follow U1. U4 follows U3. U8 waits for A4 W2c. U9 then U10 come last.
A4 W0 → W3 runs on A4's own goal and is a prerequisite for U8 and U10. A5 does not do A4's work and does not spend A4's cap.

## 5. Token budget (processed tokens = input + cache write + cache read, the estate's measured currency)

| Item | Value |
|---|---|
| Historical sunk evidence base (DWS, reused, not re-bought) | 3.10B tokens / 10,985 calls ($744 productive + $233 anomaly) |
| This scan (pre-approval) | UNKNOWN exact (session not yet in usage index); outside the goal |
| UNKNOWN historical | prior CE gen2 spend per goal is known per goal; estate-wide weekly % UNKNOWN (MONITOR_FAILURE) |
| Lower bound (U0-U3, U6, U10 only) | 7.8M |
| **Expected A5 CAPEX** | **14.8M** (sum of unit targets) |
| Safety envelope (P90) | 17.9M (sum of stops) |
| **Hard catastrophic stop (goal cap)** | **20.0M** |
| Model-call budget | ≈ 145 worker calls, run as ≈ 13 fresh slim sessions of ≤ 12 calls each. Estate formula: 18K floor + 15K growth per call, so a 12-call session costs ≈ 1.2M. Plus coordinator ≤ 40 calls |
| Semantic-interrupt budget | 18 irreducible decisions expected (IR shape, class taxonomy, label set, set-cover cost model, visual metric, RAM floors, stall N, projection schema, 2 holdout picks, policy promotions ×4, final assumptions ×4). Trip at 36 |
| Proof reserve | inside each unit (done-gate + mutants), ≈ 25 % of unit budget |
| Counterfactual/replay | 1.2M (U2) + 1.0M (U9) |
| Live canary | ≤ 0.4M (U5 synthetic card, U6/U7 planted canaries); no DWS product execution |
| Cross-domain holdout | 1.0M (U9) |
| Checkpoint / closeout reserve | 0.6M coordinator + receipts inside units |
| Recovery reserve | 3.1M (stop minus target) + 2.1M (cap minus stops) |
| USD at estate effective rate ($0.36/M processed) | expected ≈ $5.4, cap ≈ $7.3 |
| A4 substrate (already approved, not new money) | 14.16M remaining on goal ce-a4 |

Expected return (a RANGE, low confidence until U2 lands):
- DWS runnable today is priced at 6.50B (old architecture).
- The measured composition suggests the floor (≈ 36 %) and accumulated history in long sessions (≈ 84 % of tokens in sessions over 60 calls) are both removable by machinery that A4/A5 build.
- Plausible DWS runnable after recompile: **0.8B – 2.6B (2.5× – 8× cheaper)**. Confidence: LOW-MEDIUM. Nothing here is realized savings. Payback on 20M is reached if the recompiled DWS runnable budget is cheaper by more than 0.3 %.
- Estate-level: the same session shape exists in every GSD mission. The recurring saving per estate week (≈ $9.5k API-equivalent measured 09-25 → 10-03) is UNKNOWN until U9.

## 6. Key questions (short answers)
- Smallest IR: Goal, Obligation, Computation (with satisfier kind), Observation, Proof receipt, Invalidator, Decision. All are typed rows in the existing claim JSON and receipts. No new store.
- Demand graph without a new system: it is a stage inside `cost_to_completion` over the claim graph, plus the goal ledger. Cross-goal sharing is via the singleflight key (ce-unify D-37).
- Obligation vs computation: an obligation is "what must hold". A computation is created only when no satisfier (state, proof, transform, other goal, observation) resolves it.
- Irreducible transition estimate: count decisions/observations/assurance judgments that remain after the satisfier pass. It is labelled an estimate, with ±.
- Non-Compute cheap: deterministic lookups only (claim state, receipt hash, dependency hash). There is no model in the check, and it is O(closure).
- CSE identity: hash of (normalized question id, dependency fingerprint, scope, evidence epoch, assurance level). Prompt wording is excluded.
- Singleflight failure: the lease has a TTL. A killed producer releases on expiry, a waiter re-elects, and the demand id is preserved (U7 canary).
- Proof/reality invalidation: each receipt carries its invalidators (file hashes, host epoch). A missing invalidator = not reusable.
- Context VM bloat vs thrash: not built. U2 measures fault cost versus the projection first.
- Dynamic linking of tool surface: measured in U2 (schema share of the 102K floor). A4 W1c owns the change.
- Sequence → transactions: U1 n-grams × cost → candidates → A4 W3 pipeline (replay, shadow, canary, CBR).
- JIT/deopt safety: a compiled unit names its assumptions in the packet. A violated assumption = deopt with that assumption only.
- Model calls as interrupts: provenance label per call from U1. Purity is reported, not enforced, until U7 has a measured stall rate.
- Runaway detection: the stall trip in U7, plus the existing cost breaker (> 2 × estimate).
- Theorem invalidation: each economic finding goes to UKDL via CEPS (A4 W3) with its pricing/model/workload invalidators.
- Preventing bureaucracy: every unit has a cap and a two-strike stop; there are no permanent agents; NEGATIVE_ROI rows stay rejected.
- DWS traces without running DWS: U1/U2/U10 are read-only. The only canaries are synthetic (U5–U7).
- Why the final budget differs causally: it prices obligations after satisfier elimination, with measured per-class worker profiles under the new grammar (slim floor, rotation, projection). It never takes 424 calls/step × claims.

## 7. Boundaries and rules
- Owner boundary 1 = this plan. Boundary 2 = the final DWS budget. Nothing in between except HR-001 residuals that only the Owner can perform (each stays a named OWNER_QUEUE line, not a question).
- Never: execute DWS product scope, raise a cap, Set-Location into another Apps\pp-* root, write in another live worktree, or push.
- Worktree `Apps\pp-ce-a5` off CPP main HEAD; goal `ce-a5` cap 20,000,000 bound to that root.
