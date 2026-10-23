---
covers: [t1-incident, hold-enforcement, authority-provenance, econ-reconciliation, mission-rebind, compiled-certification-campaign, tennis-all-match]
status: EXECUTING (Owner "y" + subelo 129M applied 3x = +387M, kept by Owner "mantén"; plan hard ceiling stays 60M). A4/F5 DONE (T1 settled to 196,160,185). A1/F1 DONE 8409d0f2: hold gate registered and drilled in a real session on both hosts; the sweep-side fixes are live on the laptop only, because GEX44's shared install 30fdbf0f is not updated (Owner decision). A2/F2+F3 DONE 34d3f4a7 (AUTHORITY_RECEIPT 28/28): enforced on laptop missions; GEX44 missions need that install update plus a cross-host owner-turn receipt, which is not designed yet. A3/F4 DONE 98256535 (REBIND_F4 7/7). Next: A0+A5 in the Fabric clone.
date: 2026-10-23
supersedes_execution_of: [tennis-all-match 03-02, 03-03, 03-04, 03-05 as GSD plans]
---
# T1 incident → compiled certification (master plan)

Reality scan 2026-10-23 ~14:00 CEST. Every number below has its source in brackets. Units: **processed** =
input + cache_write + cache_read + output tokens, summed over the worker AND all of its subagents. This is the unit
used by both the mission breaker and the goal ledger.

## 1-13 Current reality

| # | Item | Measured state |
|---|---|---|
| 1 | T1 | Mission m-260aa89142c8 is **HALTED** (MISSION_AUTHORITY hold since 09:41:38Z), worker b541504e is dead. Phases 1-2 are complete and verified; phase 3 is at plan 03-01 of 5. [mission record; exec1 log] |
| 2 | Certified | **502/1797** (CERTIFIED 502 / CNM 557 / NO_COMPILE 738 / UNKNOWN 0); `projection check` = FRONTIER_CHECK OK on 7122d4ae. |
| 3 | Dataset | `evidence/fingerprint/views.jsonl` holds 557 rows under fp-norm1. Bands: 50to90 264, lt50 122, 95to100 114, 90to95 57. Labels: COUNT_DIFFERS 435, OPCODE_DIFFERS 68, REG_MAP_CONFLICT 31, REG_MAP_CONSISTENT 10, IMMEDIATE_ONLY 5, ARG_MIXED 5, ORDER_ONLY 2, RELOC_OR_BRANCH_ONLY 1. The rows carry no pct field and no dataset id. |
| 4 | 33 set | ≥99 % = 33 (v5 sweep distribution). The view rows lack pct, so the set has to be joined from `fm1-repair5/sweep.jsonl`. It is not yet a pinned artifact. |
| 5 | fn_8022F950 | Root 98.125 %, label REG_MAP_CONSISTENT, n_diff 3. Search ran 2 evals: 1 valid, 1 pruned as equivalent, depth 1. decl-swap@1 tried 1, improved 0; stmt-swap@1 tried 0. State **EXHAUSTED**, solved 0, with negative-space sha 546eb660…. Meaning: SEARCH_FRONTIER_EXHAUSTED under a 2-operator language. [evidence/search/tracer.json] |
| 6 | Rule registry | 29 rules (19 v5 core split + others). RULES_JSONL OK. 26-rule ablation committed; registry5 re-sweep byte-identical 022768b5 with 1797/1797 cache hits. Maturity: LOCALLY_SUCCESSFUL. No rule carries a family, counterexample or promotion state. |
| 7 | Search engine | `search.py`, `search_c.py` and `search_ops.py` (~1060 LOC) on 7122d4ae. Persistent tree, negative space, equivalence pruning, determinism and live kill/resume gates (SR1). Has no cohort driver and no certify promotion path. |
| 8 | Durability | Code and evidence are sealed on bare `mission/gsdx-fabric` 7122d4ae. Two leftovers on GEX44 exec1: untracked `03-PLAN-CHECK-2.md` and dirty `vault/audits/verdicts.jsonl`. **chain.json not reproduced as uncommitted**: the clone's chain.json files are tracked and clean. |
| 9 | Authority lineage | `authority_set` 56M at 05:15:55Z (Owner "y"). `authority_set` **80M at 09:39:17Z**, written by laptop session 15f5057c (Sonnet coordinator pane of m-41fafdada77b) after the **Owner typed "a" at 09:36:51Z** in that pane. My earlier statement that "neither coordinator raised it" was **wrong**. The provenance exists only as a free-text reason plus that transcript; there is no receipt binding the session or turn. |
| 10 | Reconciliation | gsdx-factory-2: programme 267,817,916 · settled 289,914,817 · open 3,044,605. Settled − programme = **22,096,901**. "Executable" = programme − settled − open = **−25,141,506**. I reported the second number as "over programme", and that label was wrong. T1's true total is 196,160,185; I settled 152,641,947, so **43,518,238 is unsettled**. After the correction: settled 333,433,055, executable −68,659,744. |
| 11 | Cost tree | Total 196.16M, of which cache_read 188.88M (96.3 %), cache_write 7.15M, output 0.119M, input 2.6k, over 1,287 model calls (~152k processed per call). By kind: gsd-executor ×7 100.15M (51.1 %), gsd-planner ×3 53.19M (27.1 %), MAIN 26.55M (13.5 %), plan-checker ×4 9.06M (4.6 %), verifier ×2 7.22M (3.7 %). Planning+review = 69.5M (35.4 %). Search, verification and other tool CPU cost no tokens. A split of executor tokens into search vs edit is UNKNOWN. |
| 12 | Workspace | The 07:59 auto-rebind chose subagent worktree `agent-a33215aa…`. Root cause: `mission_binding.detect_rebind` accepts any worktree created after `bound_at` and named in tool text, and harness `agent-*` isolation worktrees satisfy both. Ten agent worktrees remain. |
| 13 | Context rent | T1 was driven by resident context, not MEMORY.md: ~152k processed per call × 1,287 calls, under a builtin `autocompact 250k` with model sonnet. MEMORY.md (20.7 KB ≈ 6k tokens/turn) is laptop-only and does not reach GEX44 workers. |

## 14 Root-cause matrix

| Failure | Class | Mechanism (evidence) |
|---|---|---|
| Hard ceiling crossed 3.5× | ENFORCEMENT | Accounting was exact: my recount equals the breaker at both 06:41Z (50.31M) and 09:41Z (152.64M), so descendants were **not** invisible. But **145.85M was processed after the 06:41Z STALL hold** and **43.52M after the 09:41Z authority hold**. GEX44 registers no PreToolUse gate, only PostToolUse `mission_wall_hook` and SessionStart, so a hold blocks relaunch and never stops a busy worker or its subagents. |
| Authority breach at 56M never recorded | ENFORCEMENT | Spend passed 56M at ~07:00Z while the mission was already STALL-held. No MISSION_AUTHORITY incident existed until the 80M set made the breaker re-judge. The existing hold masks the authority judgement. |
| 80M raise infeasible on arrival | INSTRUMENTATION / authority UX | The option text the Owner answered quoted "spent 50.3M of 56M", a 06:41Z incident snapshot. At 09:36Z the live figure was ~141M, so the new ceiling was below spend and tripped 2m21s later. |
| Forecast miss | STRATEGY | `token_estimate` 27.5M is a breaker envelope artifact ((40.0M + 15.0M)/2), not the T1 forecast. The real miss is 196.2M actual vs the T1 central 44M = **4.46×**, bought for 2.2 of 10 phases. |
| 0 productive yield | STRATEGY | All spend went to infra CAPEX and planning. The search engine ran 2 evals on 1 subject. |
| Coordinator duplication | CONTROL | Two coordinator panes (this one and 15f5057c) worked the same mission and both fetched/merged. |
| Reporting errors (mine) | INSTRUMENTATION | I mislabeled "executable" as "over programme" and denied a raise without searching the transcripts. |

## 15-19 Atomic model, invariants, ledgers (map onto owners that already exist; no new kernel)

No ULTRA-PLAN. A Universal State Transition Kernel is **rejected now** by the anti-abstraction gate: no failure above needs it. Each one has a narrower owner.

| Plane | Current owner, current atom | Target atom (this plan) |
|---|---|---|
| Execution | gsd_mission epochs / GSD plans | Campaign step = (subject, state_before hash, move, verifier result, state_after hash), already the search tree record |
| Search | `search.py` tree records + negative space | + search-language version + subscription on expansion |
| Evidence / proof | `evidence/*` + CERT1 receipts (certify.py) | unchanged; certify stays the single gateway |
| Economics | goal ledger (mission_spend) + breaker incidents | + reconciliation receipt with typed fields |
| Authority | ledger row `authority_set` (free-text reason) | + `owner_turn`, `prev`, `expected_seq`, actor session, refusal when ceiling ≤ live spend |
| Resource | GEX44 job pattern (nice/timeout) | unchanged |
| Context | capsule-v2 cards | campaign workers get no transcript, only the campaign IR |
| Knowledge | rules.jsonl, UKDL | + negative-space store keyed by (subject, SL version) |
| Dataset | untracked view file | dataset pin (sha of views + sweep + rules + engine commit) |

**Invariants that become tests:**
- I1: no tool call by a held mission's worker or its subagents.
- I2: no authority mutation without an owner-turn receipt that resolves to a user message in a transcript.
- I3: a ceiling ≤ live spend is refused unless `--recognize-overrun`.
- I4: the authority judgement runs even when another hold exists.
- I5: a rebind never selects `.claude/worktrees/agent-*`.
- I6: certification only through `certify run`.
- I7: no search revisit of a (state hash, SL version) pair.
- I8: the campaign makes no model call on its normal path.

**Ledgers:**
- State = git + search tree.
- Evidence = `evidence/` + receipts.
- Authority = mission ledger jsonl.
- Economic = goal ledger.
- Resource = job logs.

## 20-41 Certification runtime, search, rules (the campaign)

- **Normal path (no model):** dataset pin → for each subject, query negative space for (state, SL) → known rules (registry) → bounded deterministic search (`search.py`) → exact objdiff → `certify run` → receipt. The pieces exist; what is missing is the **cohort driver** (the old 03-03 scope as a deterministic runner, ~150 LOC) and the **solved → certify promotion hook** (the old 03-04/05 scope, folded into `certify run` input).
- **Mismatch atoms / families:** the fp-norm1 labels are **8 TENTATIVE candidate families**. **0 are causally validated.** A family becomes causal only after an operator solves ≥2 members and an ablation shows it leaves non-members unchanged.
- **Search state / CSE / dominance:** the existing tree hash already covers state identity and equivalence pruning. Add the SL version to the key. Dominance pruning is deferred because no evidence of revisits exists yet.
- **Search language:** SL-v1 = {decl-swap, stmt-swap}. An operator added through an interrupt yields SL-v2, which emits `SEARCH_LANGUAGE_EXPANDED` and re-queues only subjects whose exhausted record lists that label class.
- **Negative knowledge / counterexamples:** the exhausted tree, with its negative-space sha, is the record. It is reused by key and invalidated by an SL version change.
- **Opportunity graph:** deferred. It is built only if A6 shows ≥2 label classes exhausted under SL-v1. Until then it is a sorted label population table.
- **Rule promotion:** CANDIDATE → LOCALLY_SUCCESSFUL → FAMILY_VALIDATED (≥2 solves) → NEGATIVE_COHORT_SAFE (ablation). Higher rungs wait for evidence.

## 42-55 Interrupts, model necessity, agents, planning

- **Semantic interrupt:** one class, `MISSING_OPERATOR(label)`. Raised only when every micro-cohort medoid of that label is EXHAUSTED under the current SL. The capsule holds the label's views, 3 medoid diff handles, the operator interface, and the SR1 gate. Typed output: operator code + test. Budget ≤3M per class, ≤3 classes.
- **Model necessity receipt:** `DETERMINISTIC_FRONTIER_EXHAUSTED` (the tree records), carried in the interrupt capsule.
- **Tiers:** none for the normal path. Interrupts run on Opus (operator synthesis is novel). Summary reads run on Sonnet.
- **Agents:** no GSD planner, checker or verifier loops. At most 1 interrupt worker at a time, with a deposit contract of operator + test, or a recorded negative result.
- **Plans:** 03-02..05 leave the actionable frontier. 03-04 and 03-05 are **SUPERSEDED** (certify already is the gateway). 03-03 is **recompiled** into the deterministic runner. 03-02 is **re-scoped** into the per-label interrupts. Executed as written: 0. Garbage-collected: 4. History stays in git.

## 56-63 Dataset, cohort, breaker, forecast

- **Dataset pin `tam-ds-1`:** sha256 of views.jsonl + fm1-repair5/sweep.jsonl + rules.jsonl + engine commit, committed as `evidence/campaign/tam-ds-1.json`.
- **Micro-cohort:** subjects at ≥99 % (joined from sweep) with n_diff ≤ 4. Take 1 medoid (smallest n_diff, tie broken by address) per label class present, so ≤8 subjects. fn_8022F950 is excluded until SL changes (it is already exhausted).
- **Zero-yield breaker (semantic):** stop and report when the cohort yields 0 SOLVED and every medoid is EXHAUSTED and no interrupt produced an operator that moves any medoid's score. The cost ceiling is a backstop, not the trigger.
- **Forecast (structural):** cost = deterministic CPU (0 tokens) + Σ over label classes needing an operator (≤3M each) + summary reads. The remaining 557 are forecast **per label class**, never per function, after A7 measures the solves per operator.

## 64-70 Economics and authority fixes (must land before any campaign run)

- **F1 hold enforcement:**
  - A PreToolUse gate, `mission_hold_gate.js`, denies every tool call whose session_id (subagents carry the parent's) belongs to a mission with a `cost` or `authority` hold.
  - The sweep stops a busy worker on MISSION_AUTHORITY.
  - The authority judgement is no longer masked by an existing hold.
  - Overshoot after a hold is bounded by one model call (~150k), not hours.
  - Registered on GEX44 and the laptop. **HR-001: this writes `~/.claude/settings.json` on both hosts; this approval covers it.**
- **F2 authority provenance:**
  - `gsd_mission.py authority` gains `--owner-turn <session>:<timestamp>`, verified to be a user message in that transcript, plus the `prev`/`expected_seq`/actor fields.
  - A ceiling ≤ live spend is refused unless `--recognize-overrun`.
  - `topology` prints the lineage.
  - Drills: no receipt → reject, replay → idempotent, stale seq → conflict, subagent session → reject.
- **F3 live spend in option surfaces:** `status`/`topology` print live processed spend plus its timestamp. An incident snapshot is labelled with its age.
- **F4 rebind:** `detect_rebind` excludes `.claude/worktrees/agent-*` and prefers the worker transcript's own `cwd`. Test from both poles.
- **F5 economic receipt:** settle the remaining 43,518,238 for b541504e, then commit `vault/programs/gsdx-fabric/tennis-all-match/receipts/econ-reconciliation-t1.json` with the typed equation from §10.

## 71-76 Context, replay, universality

- **Pages:** the campaign IR plus per-subject tree records are the function and family pages. No new page store.
- **MEMORY.md:** compact below 17 KB, moving closed-programme lines to MEMORY_COLD. Expected saving is small: ≈2k tokens per turn, laptop only.
- **T1 fixture:** commit the cost tree, authority rows, incident files (copied), and tracer, as `evidence/incidents/t1/`.
- **Counterfactual replay (deterministic):** against F1-F4, evaluate the T1 ledger and transcripts. Directly provable avoidable spend: 145.85M after the STALL hold (F1), and the 80M infeasible raise (F2/F3, refused). Estimated: the 53.2M of planner tokens that a compiled campaign would not spend. The estimate is labelled as such.
- **Universal vs Tennis-specific:**
  - Universal (PP): F1-F5, interrupt-only-on-exhaustion, the dataset pin pattern.
  - Tennis-specific (Fabric): operators, labels, certify.

## 77-81 Mode, commits, budget

All stages run in **EXECUTION mode**, except A7, which plans each interrupt capsule inline. Execution topology: a **fresh lean session** (this pane carries a large resident context), deterministic jobs on GEX44, no `/gsd-autonomous`.

**Micro-commits, about 14:**
- PP: hold-gate+test, breaker precedence+test, sweep stop+test, authority receipt+drills, live-spend status, rebind fix+test, econ receipt, UKDL/vault.
- Fabric: T1 fixture, dataset pin, cohort runner+gate, certify promotion hook+gate, cohort result, per-operator commits, replay receipt.

| Stage | LB | P50 | P80 | P95 | Hard | Model calls | Deterministic | Conf. |
|---|---|---|---|---|---|---|---|---|
| A0 incident freeze + receipts | 1M | 2M | 3M | 4M | 4M | ~15 | scripts | med |
| A1 F1 fence + tests + 2-host register | 2M | 7M | 10M | 14M | 14M | ~45 | — | med |
| A2 F2+F3 provenance + drills | 1.5M | 4M | 6M | 8M | 8M | ~25 | — | med |
| A3 F4 rebind | 0.5M | 2M | 3M | 4M | 4M | ~12 | — | high |
| A4 F5 settle + seal leftovers | 0.2M | 0.5M | 1M | 1.5M | 1.5M | ~4 | — | high |
| A5 dataset pin + cohort runner + promotion hook | 2M | 5M | 7M | 10M | 10M | ~30 | — | med |
| A6 micro-cohort run + certify (CPU) | 0.2M | 0.5M | 1M | 1.5M | 1.5M | ~3 | ~100 % | high |
| A7 ≤3 operator interrupts (only if A6 exhausted) | 2M | 6M | 9M | 9M | 9M | ~40 | rerun deterministic | low |
| A8 counterfactual replay | 1M | 2M | 3M | 4M | 4M | ~10 | scripts | med |
| A9 KV/UKDL + MEMORY + handoff | 1M | 2M | 3M | 4M | 4M | ~12 | — | med |
| **Total** | **11.4M** | **31M** | **46M** | **60M** | **60M** | ~196 | | |

- Infra CAPEX (A0-A5, A8, A9): P50 24.5M, hard 49.5M.
- Tennis OPEX (A6, A7): P50 6.5M, hard 10.5M.
- Basis: ~100k processed per call in a fresh lean session, against T1's measured 152k under autocompact 250k.

## 82-85 Owner surface

- **Capital is required.** gsdx-factory-2 is overdrawn: executable −25.1M now, −68.7M after F5 recognises the 43.5M already spent.
- **Raise:**
  - The raise is `subelo 129M gsdx-factory-2`.
  - 68.7M of it recognises past spend and adds no new exposure.
  - 60M is the hard ceiling for this plan's new exposure. The P50 is 31M.
  - Stage ceilings are enforced by F1 once it lands; until then, per stage by me.
- **ASM default:** strict reading. Replace the aggregate opcode motif lists with counts only, in summary.json and receipt phase-2, as a new dataset version; history is kept.
- **Approval:** `y` approves this plan, its stage ceilings and the ASM default. Typing the `subelo` line is the capital receipt, handled by the econ hook before the model.
- **Return to the Owner only for:**
  - a stage hard ceiling hit;
  - A6+A7 zero yield (report and stop);
  - an F1 deploy failing its red-branch test on GEX44;
  - any action outside these paths.
