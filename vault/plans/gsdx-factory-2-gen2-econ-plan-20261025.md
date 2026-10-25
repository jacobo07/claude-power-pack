---
status: AWAITING_OWNER (one approval, section 14)
date: 2026-10-25
program: gsdx-factory
goal: gsdx-factory-2 (existing identity; no new programme)
covers: [pre-boundary-ceiling, exact-subject-push, unit-econ-telemetry, providerless-next-unit, factory-2-gen2, class-interrupt-work-class, economic-immunity, economic-compounding, fresh-process-inheritance]
depends-on: [t1-incident-compiled-certification-20261023 (A7/A8 evidence), gsdx-fabric-master-plan-2026-10-14, gsdx-econ-recon-program-plan]
---

# GSDX Factory Generation 2 -- economic safety micro-slice + generation-2 residual

Owner prompt 2026-10-25 (`/cpp-gsd-long`, "GSDX-Factory Generation 2"). Reality Delta by session fc4dce34.
Nothing is armed until section 14 is answered.

## 1. Current factory reality (measured 2026-10-25)

| Fact | Value | Source |
|---|---|---|
| Factory-2 identity | goal `gsdx-factory-2` EXISTS: programme 654,817,916, settled 334,923,153, executable 318,790,068, lease L21, bound root `Apps\pp-gsdx-factory-2` only | `mission_spend programme-status/goal-status --goal gsdx-factory-2` |
| Gen-1 goal `gsdx-factory` | cap 8,000,000, settled 13,870,691 (remaining -5,870,691): a second post-hoc overrun | `goal-status --goal gsdx-factory` |
| Product frontier | 519/1797 certified (12 ledger + 490 cert1 + 17 search), FRONTIER_CHECK OK | t1 plan lines 19-21; GEX44 t1/campaign |
| GEX44 t1/campaign | HEAD 0c353ecb = bare remote (ls-remote verified) | this session |
| Laptop PP | feature/knowledge-acquisition 0b4aa4ce = origin (ls-remote verified) | this session |
| Uncertified views (pre-A7 snapshot, 557) | COUNT_DIFFERS 435 (95-100 band 45) · OPCODE_DIFFERS 68 (95-100 band 18) · REG_MAP_CONFLICT 31 (20 searched: 8 solved, 12 exhausted) · REG_MAP_CONSISTENT 10 · IMMEDIATE_ONLY 5 (done) · ARG_MIXED 5 (done) · ORDER_ONLY 2 · RELOC 1 (negative) | GEX44 `evidence/fingerprint/views.jsonl` |
| NO_COMPILE | 738, never scanned for operators | t1 plan line 42 |
| T1 campaign sessions | interactive, Owner-woken per class ("rec", "hazlo", "sí"), **no session envelope, not bound to any goal** | no `session-budget-<sid>*` for 4f881648, e8654fa7, bd86f1e3, fc4dce34 |

## 2. Generation-1 economic baseline (work class CLASS_INTERRUPT = label medoid -> operator -> judge -> search -> certify)

| Unit | Spend | Calls | Avg/call | Value deposit | Source |
|---|---|---|---|---|---|
| A7 REG_MAP_CONFLICT (incl. first-receipt gate repairs) | ~12.6M vs 9M hard | 95 (session total) | ~200K | 1 operator, 1 cert | t1 plan line 12 |
| A7 expansion (widen REG_MAP) | 4.38M vs +5M | -- | -- | 7 certs | line 12 |
| (b) budget re-run + (a) IMMEDIATE_ONLY | 8.33M | -- | ~200K | 1 operator, 13 certs, 1 negative (b) | line 12-14 |
| ARG_MIXED | **6.46M vs 3M** | 37 | ~175K | 1 operator, 3 certs | line 17 |
| ARG_MIXED widening (session 4f881648) | **4.31M vs 3M** | 29 | ~148K | 3 certs | line 19 |
| RELOC_OR_BRANCH_ONLY | ~2.3M vs 4M | -- | -- | 1 negative | line 20 |
| Jumptable cohort + A8 (session fc4dce34) | 9.15M + 3.1M (still open) | 56 + 21 | 163K / 148K | 1 negative, 1 replay receipt | transcript segmentation |

Gen-1 medians: new-operator class unit ≈ 6.5M / ~35 calls; widen unit ≈ 4.3M / ~29 calls. Per-call cost 148-200K.

## 3. A8 evidence (exact; not reinterpreted)

F1 PROVEN: avoidable 144,711,979 of 196,160,185 (lenient 143,920,386). F2 PROVEN as exposure refusal (80M vs 151,588,755 refused; under F1 accepted at 50,436,045; F2 alone attributes 0 tokens). F3/F4 UNMEASURED. Planner 53,187,533 ESTIMATE (9,134,923 additional). Red drills: stub gate exit 1, disabled F2 exit 1. Receipt: GEX44 t1/campaign 0c353ecb `evidence/incidents/t1/replay-receipt.json`.

## 4. Hard-ceiling root cause (4.31M vs 3M, session 4f881648)

1. **No enforcement existed for that session.** `hooks/session_budget_guard.js:484` -- `if (!fs.existsSync(bPath)) return null; // the opt-in: no envelope, no guard`. The Owner's "3M" lived only in the prompt: MODEL_POLICY_ONLY.
2. **Even with an envelope the session check is post-hoc.** `judge()` line 120 denies on `st.tokens > budget.stop` -- after the crossing call already ran. The predictive "LEASE EDGE" (line 141) only *advises*. Prior evidence: 2026-10-07 canary refused at 3,005,579 vs 3M then admitted ~1.17M more (comment lines 161-163).
3. **Goal mode is already pre-boundary** (`decideGoal` line 416: renew when `measured - base + next > amount`), but T1 sessions were never bound to a goal (cwd = PP root, not a goal root).
4. Gen-1 `gsdx-factory` overran 8M by 5.87M -- same class (unbound spend booked after the fact).

Class: **HARD_CEILING_ENFORCED_AFTER_EFFECT** (+ ENFORCEMENT_OPT_IN_DEFAULT_OFF).

## 5. Provider-boundary coverage (guarantee strength)

| Path | Pre-admission today | Strength |
|---|---|---|
| Interactive main session, envelope declared | PreToolUse deny on tools; post-hoc `tokens > stop` | RUNTIME_GUARDED, post-hoc |
| Interactive main session, no envelope (T1 campaign) | none | MODEL_POLICY_ONLY |
| Goal-bound session | `measured + next > lease` -> renew/refuse before the call | RUNTIME_GUARDED, pre-boundary |
| Ralph bg worker | goal guard + 5-min sweep breaker (kills worker) | RUNTIME_GUARDED + post-hoc kill |
| Subagent tool calls | guard runs per PreToolUse; transcript attribution of subagent spend to parent envelope **UNKNOWN** | UNKNOWN -> verify in H0 |
| Text-only model turn / the call that reads a deny | no hook can stop it | UNAVAILABLE (bounded by one `next`) |

Honest ceiling: hooks cannot stop the model call that follows a denial, so "hard" = admitted spend + one `next` call, which the reserve must cover.

## 6. Push TOCTOU root cause

Session fc4dce34: secret scan over `origin/feature/knowledge-acquisition..feature/knowledge-acquisition` (11,613 added lines, tip f4db3d41); then `git push origin feature/knowledge-acquisition:feature/knowledge-acquisition` re-resolved the **moving ref** and published 0b4aa4ce (written by another pane in between) unscanned. `ovo-push-gate.js` binds a verdict to a 10-minute TTL, not to a subject (lines 103-113). Class: **CHECK_RESULT_NOT_BOUND_TO_MUTATED_SUBJECT**.

## 7. Context floor (current, measured)

| Session | First call after (re)start | cache_read | cache_write | Steady avg |
|---|---|---|---|---|
| fc4dce34 (kresume) | 113,976 | 33,794 | 80,016 | 163,432 |
| fc4dce34 (post-compaction) | 117,741 | 33,794 | 83,690 | 148,448 |
| 4f881648 (kresume) | 111,047 | 33,794 | 77,081 | 163,321 |
| 4f881648 (post-compaction) | 124,525 | 31,840 | 91,527 | 128,240 |

Fresh CWS ≈ 111-125K: ~32-34K shared cached prefix, ~77-92K session-written resident prefix. Attribution of the ~80K among CLAUDE.md / rules / memory / skills list / tools / SessionStart injections: **UNKNOWN** (recorded as context debt, section 11). The 148K figure is representative of steady state, not fresh start.

## 8. Four blocking gates -- status and smallest repair

| Gate | Status | Repair (micro-slice) | Mode |
|---|---|---|---|
| G0 pre-boundary ceiling | PARTIAL (goal mode yes; session mode post-hoc; unbound = none) | **H0**: `judge()` denies when `tokens + next + seal_reserve > stop` (next = max(last ctx, live floor)); closeout calls paid inside `stop`; factory units always run with an envelope or goal binding (launcher declares before call 1); unbound campaign = refused by the factory launcher | EXECUTION |
| G1 push atomicity | MISSING | **H1**: `tools/exact_push.py` -- resolve sha once, scan `remote_ref..sha` (added lines + paths, secret-firewall patterns), receipt {repo, remote url, ref, base sha, sha, policy hash, result}, push `<sha>:refs/heads/<ref>`, refuse on any receipt/subject mismatch, verify `ls-remote == sha` | EXECUTION |
| G2 telemetry | PARTIAL (`session-tree` gives tokens/turns/peak/avg) | **H2**: `tools/unit_econ.py` -- per-unit receipt: goal, work class, unit, calls, tokens, first-call CWS, cache r/w, avg/peak, value deposit (frontier delta), forecast vs actual, amplification; deterministic, run by the sweep -> 0 model tokens | EXECUTION |
| G3 providerless continuation | PARTIAL (Ralph sweep relays; T1 next-unit chosen by Owner turns) | **H3**: GEX44 `campaign next` -- deterministic: views x labels x bands minus certified / negatives / exhausted ledger -> next unit packet (class, cohort, operator set, budget); arm via mission runtime | EXECUTION |

No ULTRA-PLAN: every repair extends an existing owner (guard, mission_spend, campaign runner).

## 9. Factory-2 residual (compiled from current truth)

| Unit | Work class | Disposition | Tier |
|---|---|---|---|
| U1 operator census: 4 landed operators (arg-passthru, ptr-bytestride, sum-reorder, decl/stmt-swap) at depth <= 3 over ALL uncertified CNM (not only the 27-pool) | WIDEN | DETERMINISTIC (CPU on GEX44); certify --solved | no model / slim |
| U2 next label class: OPCODE_DIFFERS 95-100 (18) | CLASS_INTERRUPT | MODEL (new operator) | fresh GEX44 worker, card only |
| U3 second class: REG_MAP_CONSISTENT (10) or ORDER_ONLY (2) or COUNT_DIFFERS 95-100 (45), chosen by `campaign next` after U1/U2 | CLASS_INTERRUPT | MODEL | fresh worker (immunity test) |
| RELOC / jumptable verifier-plane | -- | NO_WORK (negative stands, 1 unlock < 5) | -- |
| REG_MAP_CONFLICT remaining 12 exhausted | -- | NO_WORK unless U1 census solves them | -- |
| F3/F4 measurement | -- | DEFERRED (no fixture attribution; VOI low) | -- |
| NO_COMPILE 738 | -- | DEFERRED (separate work class, needs compile-repair operators) | -- |

Fusion: U1 fuses all widening (one census instead of per-label widen units). Fission: none justified.

## 10. Canaries and metrics

- **C-A** H0 fixture: replay 4f881648 transcript with stop=3M -> admitted spend <= 3M (+ one next); post-hoc judge gives > 3M (red).
- **C-B** H1 drill: local bare repo; scan A, commit B, push with A receipt for tip B -> refuse; push exact A -> remote == A; rescan B, push B -> remote == B.
- **C-C** H2 on one real unit (U1) -> receipt with all fields; measurement tax recorded.
- **C-D** H3: a landed receipt -> `campaign next` emits the next packet with no model turn.
- **G1 Self-healing** (U2): forecast 4M; at 1.25x forecast (5M) the guard checkpoints, seals, recompiles residual.
- **G2 Immunity** (U3): no repeat of gen-1 waste (no unbound session, no overrun, no infra repair inside a class unit).
- **G3 Compounding**: WIDEN 4.3M -> <= 1M (U1); CLASS_INTERRUPT 6.5M -> <= 4M (U2, U3). Otherwise ECONOMIC_REGRESSION with a cause.
- **G4 Fresh-process**: U2 and U3 start as fresh GEX44 workers with the card only (no transcript).
- Metrics: Verified Novelty Yield = (certs + operators + proven negatives) / M tokens; Known-Work Tax = tokens in units whose class is WIDEN or already-operatored; Deflation = gen-2 / gen-1 median per comparable class; Capital Turnover = time and tokens from operator discovery to first reuse in another unit; Reasoning Half-Life = units a decision stays model-driven before `campaign next` owns it.
- Zero-yield breaker per class: CLASS_INTERRUPT stops at 60% of budget with no operator draft passing a depth-1 judge; WIDEN stops at exhausted evals (existing).
- Interruption ROI gate: infra may interrupt product only with measured amplification, P80 payback < 3 units, bounded scope, proof strategy.

## 11. Context debt (recorded, not fixed now)

~80K session-written prefix per fresh session x ~30 calls per unit. Attribution UNKNOWN. A bounded attribution probe is admitted only if U2/U3 show the floor dominating (> 60% of unit cost) -- then ROI gate.

## 12. Token budget (processed tokens; per-call 150K live floor)

| Stage | Lower | P50 | P80 | P95 | Hard | Calls | Deterministic |
|---|---|---|---|---|---|---|---|
| H0 guard + fixture + mutation drill | 1.2M | 2.0M | 2.6M | 3.2M | 3.2M | ~13 | -- |
| H1 exact_push + drill | 1.0M | 1.6M | 2.2M | 2.7M | 2.7M | ~11 | -- |
| H2 unit_econ | 0.6M | 1.0M | 1.4M | 1.7M | 1.7M | ~7 | sweep-run |
| H3 campaign next (GEX44) | 1.0M | 1.6M | 2.2M | 2.7M | 2.7M | ~11 | yes |
| CAPEX subtotal | 3.8M | 6.2M | 8.4M | 10.3M | **10.5M** | | |
| U1 census (WIDEN) | 0.2M | 0.6M | 1.0M | 1.3M | 1.5M | <=6 | CPU |
| U2 class interrupt | 2.5M | 4.0M | 5.0M | 6.0M | 6.0M | ~26 | |
| U3 class interrupt | 2.5M | 4.0M | 5.0M | 6.0M | 6.0M | ~26 | |
| OPEX subtotal | 5.2M | 8.6M | 11.0M | 13.3M | **13.5M** | | |
| E0 comparison + K0 KV/UKDL + CBR | 1.0M | 1.5M | 2.0M | 2.5M | **2.5M** | | |
| **Total** | 10M | **16.3M** | **21.4M** | 26.1M | **26.5M** | | |

Seal reserve: each unit keeps 2 x next (~300K) inside its hard figure.

## 13. Micro-commits, order, rollback

H0a fixture (red) -> H0b pre-boundary judge -> H0c launcher envelope -> H1a drill (red) -> H1b exact_push -> H2 unit_econ -> H3 campaign next (GEX44) -> C-A..C-D -> U1 -> U2 -> U3 -> E0 -> KV/UKDL -> CBR. Each commit pathspec-scoped, `-F` msgfile, verified subject. Rollback: `CPP_PREBOUNDARY=off` restores the old `judge`; exact_push is additive (old push path untouched); campaign next is additive. GEX44 pushes go through exact_push once H1 lands (self-hosting).

## 14. Owner approval (one surface)

1. Approve this plan and **26.5M hard** under goal `gsdx-factory-2` (executable 318.8M; capital exists, this is the ceiling).
2. Security boundary: the PP repo is **PUBLIC** and carries mission briefs, host names and token figures. Keep publishing them there (exact_push enforces secrets only), or make the repo private?
</content>
</invoke>
