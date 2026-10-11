# Sidecar Live QA V1 -- recompile from current reality (WU-S10, Stage B, READ-ONLY)

Date 2026-10-11. Nothing in io-liveqa was mutated; no mission armed; Live QA not executed.
All sums below are FORECASTS built from measured slim-worker costs (0.5-1.6M per item, master plan s1) unless marked MEASURED.
Confidence LOW-MEDIUM: per-class unit costs have no measured actuals beyond W1/B-P3.

## 1. Measured inputs
- io-liveqa `feat/sidecar-live-qa` HEAD 2367c711 (state: B-P3 partial receipt); worktree has 2 modified state files, untracked LEARNINGS_PENDING.md.
- Queue (programme-queue.json): done = A2-lineage, A3-chain, A1-ledger, B-P2-close, A6+A5, A4-tier; partial = B-P3; pending = B-P4, B-park, A-experiments.
- Hermes: `command -v hermes` laptop = absent (MEASURED 2026-10-11); GEX44 = NOHERMES (MEASURED via ssh). Owner install still pending (P-HERMES BLOCKED_HUMAN).
- Old compiled cost (COST-TO-COMPLETION.md): candidate 90.2M (108.2M with margin), ceiling 233M; approved envelope 68/122/205M; breaker 184M.
- MEASURED spend, mission workers: 77.1M total (Phase 1 64.1M heavy fan-out). Pre-Stage-A programme: 8 workers 8.11M + bootstrap pane 15.7M + planning 6.7M (master plan s1). Spend of Stage-A units S0-S9 and of B-P3 final: UNKNOWN here (not metered in this unit; not zero).
- `cost/claims-classified.json` still shows all 98 claims `open`: STALE, status is not propagated from receipts (finding F-1).

## 2. Claim disposition (98 claims, from queue receipts; none omitted)
| Disposition | n | Claims |
|---|---|---|
| DONE-LOCAL (Phase 2 gate 11/11, F1 drilled) | 8 | C4-01 C5-02 C5-03 C5-04 C5-05 C5-06 C14-02 C1-06 |
| DONE-STAGING-OBSERVED (GEX44:5434 same-host cluster, not a deployed staging) | 3 | C5-01 C4-03 C4-04 |
| UNIT-PROVEN, DEVICE NOT_PROVEN (B-P3, vitest 33/33, no mutation drill) | 5 | C1-01 C1-02 C1-03 C1-04 C3-01 |
| HERMES-BLOCKED | 16 | C8-01..C8-09 (sleeping) + C7-01..C7-07 (lease; dependency on Hermes inferred from wave W4/C7-01, UNKNOWN until verified) |
| OWNER-REALITY | 20 | C2-01..03 C11-02..04 C12-01..06 C16-01..08 |
| EXECUTABLE NOW, not started | 46 | det 3 (C15-01 C15-02 C15-09); known_transform 9; bounded 8; novel 26 |
Total 8+3+5+16+20+46 = 98.

## 3. Obligation disposition (166, OBLIGATIONS.json, 0 omitted)
DONE 24 (17 ALREADY_SATISFIED + OB-0024 OB-0080 OB-0144..0148); MERGED_INTO_PLAN 24; DEFERRED_INSUFFICIENT_EVIDENCE 85 (rule-defaulted, NOT_PROVEN, heuristic); EXPERIMENT_PENDING 21; CLOSED_NEGATIVE_ROI 8; REJECTED 1; UNKNOWN 3 (OB-0050 Frontier Token Firewall, OB-0051 Frontier Cognition Purity, OB-0097 Cognitive Portfolio Frontier: marked IMPLEMENT_NOW, no receipt found). Total 166.

### Semantic families
| Family | Obligations | State |
|---|---|---|
| F-CTRL control plane (A2 A3 zero-hot, readmit, chain) | OB-0080 0144 0145 0130-0139 | DONE (landed via feat/ucda S-units; live-PP landing is the programme's, not Live QA's) |
| F-PROOF proof/non-work | OB-0020 0024 0148 0155 0033 0152 | DONE except general proof reuse = CLOSED_NEGATIVE |
| F-TIER routing/tier | OB-0146 0053 0143 | DONE |
| F-FIREWALL frontier token/cognition purity | OB-0050 0051 | UNKNOWN |
| F-EXP experiments (extinction, SSA, locality, PGO, broker, oracle, counterfactual) | 21 IMPLEMENT_EXPERIMENT | pending (A-experiments), no evidence |
| F-NEG negative ROI (read-once, schema linker, projection, CSE) | 8 | CLOSED with evidence |
| F-BASE recovery-report headings + unnamed | 24 merged + 85 deferred | passive |
| F-PRODUCT 98 product claims | section 2 | active |

## 4. Budgets (processed tokens, M)
| Bucket | Scope | Lower bound | P50 | P80 | P95 | Hard ceiling |
|---|---|---|---|---|---|---|
| EXECUTABLE NOW | 46 claims, ~15 slim sessions (det 1, known 2, bounded 4, novel ~8-9) + control ≤2 | 10 | 26 | 33 | 45 | 55 |
| HERMES-BLOCKED | 16 claims, ~5 sessions, only after Owner installs Hermes | 5 | 10 | 14 | 20 | 26 |
| OWNER-REALITY | 20 claims: checklists, evidence intake, R1/R2 prep; Owner time not counted | 2 | 4 | 6 | 9 | 12 |
| FULL V1 (remaining; straight sum, conservative) | 82 claims | 17 | 40 | 53 | 74 | 93 |
Already-spent product work is not in these figures. Ceiling ≈ 2x P50 (breaker ratio 2.0).

## 5. Old vs new
- Old: candidate 90.2M / 98 claims = 0.92M per claim; 82 remaining claims pro-rata = 75.5M (margin 90M).
- New: FULL V1 remaining P50 40M. Delta ≈ 35M (FORECAST, LOW confidence).
- Attribution (approximate): ~14M claim-scope removed is NOT counted as saving (already pro-rated out); control plane 1.9x -> ≤1.2x amplification ≈ 15M of the delta (inversion MEASURED 1.9x, new factor target); slim packets 26k vs 137k per call (MEASURED on a 38-call renewal; estimator says slim loses beyond ~20 calls, keep units ≤15 calls) ≈ 12M; NO_WORK + proof reuse on re-verification ≈ 5M; remainder ≈ 3M unexplained (rounding / prior reduction). Not measured end to end: U8 backtest NOT_PROVEN (no claim graph).

## 6. Owner actions
1. Install Hermes on laptop and GEX44 (unlocks 16 claims, P-HERMES). Skip = V1 ships without C7/C8.
2. R1 (~10 min at the microphone) after Phase 3 device capture exists; R2 later.
3. Acknowledge KV-W0-01 erratum (38 vs 40 failure cases).
4. Decide: approve EXECUTABLE NOW (P50 26M, ceiling 55M) as the next Live QA envelope; Hermes and Owner-reality buckets stay unapproved.
5. Permission for any deployed staging (current evidence is a same-host test cluster on :5434; never 5433 = CostaLuz).

## 7. Findings
- F-1 claims-classified.json status never updated from receipts (all 98 `open`): cost compiler would re-count done work. Fix before arming.
- F-2 B-P3 DEVICE claims (C1-01..04, C3-01) need an Electron adapter; unit proof only, no mutation drill.
- F-3 3 IMPLEMENT_NOW obligations have no receipt: dispose or schedule.
- F-4 C7 Hermes dependence inferred, verify in W4 spec.

## 8. Another optimization pass: NPV?
NO (negative/≈0 now). Stage A already shipped the measurable levers (zero-model chain, NO_WORK, tier, lineage). A further pass costs ≥3M and only the 21 EXPERIMENT obligations remain, with no evidence and no backtest. Expected extra saving on 26M worker spend at 5-10 % = 1.3-2.6M < pass cost. Do instead: run the first 2 executable families and MEASURE actual vs P50; reopen only if measured overhead multiplier > 1.5x.

## 9. Boundary
Chain completes here. Owner decides section 6 item 4. UNKNOWN spend of S0-S9 and B-P3 must be read from the meter before any envelope is signed.
