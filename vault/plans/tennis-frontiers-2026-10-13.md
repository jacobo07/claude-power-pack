# Tennis frontiers -- 7-day / 72-hour / theoretical, with D28 measurements (2026-10-13)

Replaces the preliminary numbers of `tennis-frontier-collapse-2026-10-12.md` section 7. Tags: **M** measured (source), **D** derived by arithmetic from M, **H** hypothesis.
Corpus: 1,797 functions (M, D3).

## Measured inputs (replacing the plan's)
| input | plan (preliminary) | measured | tag / source |
|---|---|---|---|
| lint-clean | 276/1,797 (15%) | 276 (15.4%); 175 -> 276 reproduced | M D2, D6 (no further shock: 276 -> 276) |
| verification rate (compile-verified MATCH on lint-clean) | 12/22 | 12/22 = 0.545, Wilson95 0.347-0.731; donors 3/3 | M MEASURE.md, job 3 |
| distance classes 0/1/2/3/4/5 | -- | 12 / 263 / 1,307 / 92 / 92 / 31 | M D3 |
| deterministic-fixable share | "<= ~25% model-needed" | class 0-1 = 275 (15.3%) are compile-verifiable by script today; class 2 (72.7%) is "fact-gap" but UNLOCK PER FACT MEASURED ~0 (D5: 11/12 single prototypes unlock 0; cror 0/67; the one SUPPORT retracted by D6, 276 -> 276) | M D3, D5, D6 |
| model-needed fraction | ~~<= ~25%~~ | **UNKNOWN** (D12b 2026-10-14: still UNPRICED after one shared layout). Bound: functions with no script-reachable path now = 1,522/1,797 = 84.7% (D); how many of them need a model rather than a joint fact delta is not measured | D3 / UNKNOWN |
| autonomous (0 model calls) MATCH today | >= ~200 fns/day | 12 MATCH now; W13 predicts +88..186 (D, from 0.347-0.731 on 254) -> 100-198 of 1,797 = 5.6-11.0% | M+D |
| verification throughput | >= ~400 fns/day | job 3: 42 units judged 13 min after send (n=1 job, M). Serial extrapolation ~4,600 units/day is H; real limit is job approvals (7 approved, 3 used, 4 reserved to D6/D8/D9) and capsule batch size (UNKNOWN) | M n=1 / H |
| exception queue | < 150 | class-1 non-MATCH expected 68-166 (D); +1,522 unresolved classes 2-5. PARTIAL root-cause compression 5/9 = 0.556 (n=9) | D / M D2 |
| residual volume | "first number from Ph3/Ph4" | 13,745 residual items over 1,582 functions with known size (215 UNKNOWN, never counted 0); 3,429 distinct unresolved vars over 1,521 non-clean fns (HELPER 1,206, FIELD_UNTYPED 1,134, FIELD 594, QTYPE_LOCAL 400, SELF_SIG 77, M2C 15, M2C_FAILED 3) | M D3, D4 |
| incremental recompile | -- | dirty closure 44/1,797 (2.4%), 5-6x faster, sound on 5 D6 deltas + 2 controls | M D7 |
| cost of a deterministic unit | -- | 0.3-2.9M tokens, median ~1.7M per D unit; programme used 84.3M of 100M (15.7M left) | M goal-lineage |
| instruments that did NOT discriminate | -- | D4 dominator rank (red control falls; degree-driven), structural_family / idiom_family (INCONCLUSIVE) | M D1d, D4 |

## 7-day frontier (Scope B: all 1,797 to MATCH-or-queue within 7 days)
- Condition set: model-needed <= ~25%, verification >= ~400 fns/day, autonomous >= ~200 fns/day, exception queue < 150.
- **Verdict on measured evidence: NOT REACHABLE as the plan stated it; reachable slice = class 0-1.**
  - Verification (>=400/day): not the bottleneck if batches scale (H); the binding constraint is jobs (needs approvals beyond 7) and the lint-clean supply: only 276 functions are verifiable at all today (M). 7-day throughput of 400/day is moot until supply exists.
  - Autonomous MATCH: ceiling 198 of 1,797 (D) from the only lever with measured payoff (the context header on lint-clean fns). 200 fns/day for 7 days (1,400) has no measured path.
  - Supply is the frontier: raising lint-clean needs joint fact deltas; single-fact deltas measured 0 (D5, D6). A joint-delta experiment has never been run (open since D5/D6).
- UNKNOWN: model-needed fraction of classes 2-5; compile rate of lint-clean-but-unsent (W13 measures it); class-2 compile rate once lint-clean (W13 probe measures 40); joint-delta unlock; capsule batch ceiling.

## 72-hour frontier
- Condition: >= ~60% of functions (>= 1,078) in DETERMINISTIC/SEARCH-solvable zones, batch verification >= ~600/day.
- **Verdict: NOT REACHABLE on measured inputs.** Measured deterministic zone = 275 (15.3%), predicted MATCH 100-198 (5.6-11%). Reaching 60% needs +802 lint-clean beyond 276 (D). The measured shock was +101 once (175 -> 276, from prototype/extern lines, 85 of 101: D2); the next candidates added 0 (D6). Ranked helper lists (fn_800B4508 x89 etc.) are degree counts, not unlock (D4 red control, D5 Spearman n=12 uninformative).
- What would change the verdict (falsifier): a joint prototype+field delta that makes >= 100 functions lint-clean AND compile-verify at >= 0.35. One such measurement is the whole question; D7's incremental recompile makes it ~1.5 s of compute, so this is cheap to test (H).
- UNKNOWN: whether prototype arity can be derived reliably from asm (D6: `_savegpr` / variadic made D5's SUPPORT false), size of a second shock.

## Theoretical frontier (lower bound of work)
- Residual items after all shared facts: **<= 13,745** (sum of per-function residual sizes, 215 functions UNKNOWN) and **3,429 distinct unresolved vars** after grouping by var identity (M D3/D4). The true lower bound of semantic work is somewhere between "number of distinct vars that genuinely need a decision" and 3,429; the part of those that a script can fill is not measured (29 of the top-30 HELPERs are script-fillable in form, D4, but D5/D6 showed asm-derived arity can be wrong).
- Root-cause compression: PARTIAL failures 9 -> 5 classes (0.556, n=9). Whether the 1,522 unsolved functions compress at similar ratios is UNKNOWN; if H holds at 0.556, 3,429 vars -> ~1,900 decisions (H, pure extrapolation, no control).
- Floor on tokens for a deterministic-only path: 0 model calls on functions (W12 layer) -- bounded by coordination per job (0.3-2.9M per unit, M); a model-needed path has no measured price above class 1 (D3: 1,522 unpriced).
- UNKNOWN: any price above class 1; whether D4's frontier vars are independent.

## Falsifiers to carry forward
1. W13 class-1 MATCH outside 0.347-0.731 -> the verification rate is wrong; recompute 7d/72h.
2. W13 class-2 probe compile rate: >= 0.35 raises class 2 to "script-solvable" candidate; ~0 confirms the fact-gap is not the whole story.
3. Joint-delta experiment (>= 100 newly lint-clean) -> reopens 72h.
4. D8 tournament (arms B/D/E/F) when it exists: if arm F > arm B at held-out, the motif/dominator layers have value; D4/D1d say prior probability is low (H).
5. D8 and D9 have no receipt at the time of writing (see W8B-READY).
## D12b update (2026-10-14)
- One shared struct layout (global `lbl_80513E74`, 91 dependents, half-pack/half-held-out, seed 20261014): held-out newly lint-clean 0/46, vars 1285 -> 1221 (5.0%), 23/46 fns touched (M, D12b). The ~~7-day / 72-hour~~ verdicts above stand: NOT REACHABLE on measured inputs.
- Naive upper baseline (1,522 fns x 50-200K) remains an unmeasured upper bound; D12b did not run the naive arm (capsule fixes its 14 targets). W8b Scope A 88M P50 stays a topology forecast: ~~cited as Tennis forecast~~ UNPRICED until a compounding measurement exists.
- Research Frontier: 13,811 vars after identity collapse (96% private) vs 1,522 raw fns; Effective Remaining Work UNPRICED.
- Next falsifier: a joint prototype+field bundle (D12a top bundles unlock 11-12) composed with a layout fact must give >= 100 newly lint-clean on held-out or the fact-gap premise is closed.
