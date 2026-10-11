# D21 Tennis token budget -- reforecast from measured capability (2026-10-11, W8)

Supersedes nothing: the 2026-10-10 hypothesis file stays. Unit = processed tokens (dedupe message.id). Tags: M measured (source), D derived by arithmetic, H hypothesis, U unproven saving.

## 0. Oracle state (read this first)
- WU-W10a produced only a PARTIAL residual (m-46bfe6b6d846, 0.82M tokens, no commits) and there is NO WU-W10a/b/c receipt on disk at W8 time. W10c recorded neither PASS nor FAIL. Tennis compile-verified rate = **UNKNOWN (never measured; n=0 functions, 0 GEX44 jobs, JOBS.md empty)** for every layer. It is not FAIL (nothing failed) and not zero-by-assumption. Source: JOBS.md, WU-W5a/W5b/W3b receipts (M).
- Consequence: s (verified fraction) and calls/function are H. The cost per verified function is UNKNOWN; the forecast below prices it from per-call cost (M) x calls (H) / s (H).

## 1. Measured inputs
| Fact | Value | Source |
|---|---|---|
| Programme spend W1-W5b | 13,086,143 tokens, 321 calls, 18 sessions, 0 verified functions | M causal-ledger.json |
| Mean processed tokens per call | 40.8k | D 13,086,143/321 |
| Tax / exploration / work / semantic | 27.0 / 49.9 / 22.5 / 0 % | M W6 |
| Floor rent share | 41.6 %; duplication factor 14.06 | M W6 |
| Old per-call (Resort C1) | 122k; floor 115-150k | M old plan |
| Tennis functions / families | 1,797 / 1,255 (1,114 singletons); recurrence (fam>=3) 509 = 28.3 %; novelty 0.698 | M W7 families.json |
| Deterministic-eligible (exact shape + SRC PROVEN donor) | 167 (9.3 %); model-needed 1,630 (90.7 %) | M W7 |
| m2c L1 clean (zero ?) ceiling | 194 (10.8 %); verified 0 | M W7, W5a/b |
| Det type repair | 12 fns: 10 candidates, 4 of 6 "few" lost all ? ; 0 verified. W5b: 0 of 6 hard fns closed | M W5a/W5b |
| Scope A closure | 50 fns / 48 families; upper bound 160 fns / 145 families | M W7 |
| Curve (member -> tokens) | NOT RUN (no oracle, W5b stop-loss) | M W5b |
| Toolchain | Resort mwcc pin, confidence 60 %, flags UNKNOWN | M W3 |

## 2. Cost parameters (H unless noted)
| | LOWER | P50 | P80 | P95 | Basis |
|---|---:|---:|---:|---:|---|
| tokens/call | 40.8k (M) | 81.6k (H 2x) | 122k (M C1) | 150k (M floor top) | longer coding sessions grow context |
| calls per attempted fn | 4 | 8 | 11 | 13 | H, old plan |
| s verified fraction | 0.9 | 0.7 | 0.6 | 0.5 | H |
| c/s, M tokens per verified model fn | 0.181 | 0.933 | 2.237 | 3.90 | D |
| Fixed lines (onboarding Tennis oracle 3/8/15/25 + relink 5/10/15/20 + WMOS 5/12/18/25 + validation 3/6/9/12), M tok | 16 | 36 | 57 | 82 | H; relink/WMOS/validation unchanged from old A4-A6 (still unmeasured) |
| CAPEX (toolchain, transform, claim ledger, lint, certificate, families) M tok | 10 | 15 | 20 | 28 | D/H: 13.09M W1-W5b spent (M) + W6/W7/W10a ~2M (D); H tail for finishing the oracle and W8/W9 |
Deterministic functions cost 0.02M each (H, verify only). Overhead +25 % on subtotal (H, same as old; measured tax is 27 %).

## 3. Scope A -- motion closure + relink + WMOS
N functions: 50 / 50 / 100 / 160 (M closure 50, upper 160; P80/P95 widen for linear-tracker blind spots, H). No function is donor-eligible or m2c-clean (M W7), so all are model-needed; 48 families of 50 means no family discount applies.
| M tokens | LOWER | P50 | P80 | P95 |
|---|---:|---:|---:|---:|
| Semantic lower bound (50 fns x 1 call x 40.8k, s=1) | 2.0 (D) | | | |
| CURRENT-TOPOLOGY (N x c/s + fixed, +25 %) | 31 | 103 | 351 | 883 |
| COMPILED-LEARNING (adds CAPEX, no measured curve fall => same per-fn cost) | 44 | 122 | 376 | 918 |
Why compiled >= current: the curve did not fall (it was not measured) and Scope A is 96 % singleton families, so there is nothing to amortise; CAPEX is only added. The only saving is the 167 deterministic donors, none of which are in the closure.
- Recommended hard authority: **~380M total, released in tranches of 25 functions** (re-forecast after each, stop if per-function cost > 2x P50 twice). Confidence LOW. Dominant drivers: calls/function (H), tokens/call (H), s, N, fixed lines (relink/WMOS, unmeasured).
- Old hypothesis: 47 / 215 / 755 (LOWER/P50/HIGH~P90).

## 4. Scope B -- full Tennis matching (1,797 fns)
Model-needed 1,630, deterministic 167. Family-member marginal cost factor m (U, unproven): 0.4/0.6/0.8/1.0 for LOWER/P50/P80/P95 on the 542 non-first family members x 90.7 % model share. m=1.0 at P95 = no learning.
| M tokens | LOWER | P50 | P80 | P95 |
|---|---:|---:|---:|---:|
| Semantic lower bound (1,630 x 40.8k) | 66.5 (D) | | | |
| CURRENT-TOPOLOGY | 394 | 1,949 | 4,633 | 8,053 |
| COMPILED-LEARNING (CAPEX + family discount, U) | 339 | 1,739 | 4,383 | 8,088 |
Compiled saves 14 % at LOWER, 11 % at P50, 5 % at P80, 0 at P95, and that saving is unproven (U). Recommended hard authority: none; do not authorise. Confidence VERY LOW. Drivers: c/s (4.8x spread), 1,630 model fns, no oracle.
- Old hypothesis: 434 / 1,927 / 4,640 (HIGH ~P90). Nearly identical at P50/P80 because the same H parameters survive; what changed is that the bands are now conditioned on measured facts below, not that they shrank.

## 5. CAPEX vs OPEX and who benefits
- CAPEX (reusable: transform, certificate, lint, claim ledger, toolchain note, families clustering, causal ledger): ~15M spent (D) + ~13M to finish (H) = 10/15/20/28M by percentile.
- Beneficiaries (H): Resort CP50 (claim ledger, certificate, lint, causal ledger), other DOLs (families, toolchain/profile, transform). Tennis is today the only consumer that has used the tools.
- Share charged to Tennis: 100 % at LOWER... P50 60 % is the fair share (H), but the table above charges 100 % to Tennis to stay conservative; at 60 % P50 compiled drops by ~6M (A) / ~6M (B) (D). Not material against the OPEX.

## 6. Scope-B admission
**NOT YET.** The scope stays defined (D21 unchanged).
- Curve slope: UNKNOWN (W5b not run; 0 members executed).
- Recurrence: 28.3 % of functions in families >=3, but 1,114 of 1,255 families are singletons (M); novelty 0.698.
- Model-needed share: 90.7 % (M); deterministic 9.3 %.
- Proof automation: none for Tennis. W10a/b/c incomplete: no oracle, 0 verdicts; compiler 60 % confidence, flags unknown.
- Context duplication: factor 14.06, floor rent 41.6 % (M).
- Admit when: Tennis A/A passes (>=1 object byte-exact), >=20 verified functions with measured tokens, the curve (>=3 members of a family) falls, and a non-trivial (>=20 insn) discriminator confirms the compiler.

## 7. What changed vs the old hypothesis
- MEASURED: tokens/call is 40.8k in worker sessions, not 122k (C1); spend is 0 % semantic, 27 % tax, 50 % exploration; Tennis is 70 % novel, only 9.3 % deterministic, 28 % recurrent; Scope A closure is 50 fns / 48 families (old N_A H 50/120/250); the binary is a Dec 2009 SDK build, not 2006; REA cannot read the DOL; Tennis has no oracle.
- INFERRED: calls/function, s, fixed lines, family marginal factor, the P80/P95 per-call rise.
- UNPROVEN savings: any family discount (m), any cheaper-layer displacement beyond the 167 donors, donor-proven transfers, WMOS/relink lines.
- Net: the tokens-per-call surprise lowers LOWER bounds (A 47 -> 31M) but the unproven calls/s and no learning keep P50/P80 near the old figures; Scope A P50 falls 215 -> 103M only because N_A shrinks to the measured 50; HIGH rises because 150k/call x 13 calls / s 0.5 is now applied consistently.
