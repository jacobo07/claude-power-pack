# Tennis RF programme -- final Owner handoff (W9, 2026-10-12)

Sources: `vault/plans/tennis-rf-optimization-MASTER-PLAN-2026-10-11.md` s9; the programme brief's FINAL HANDOFF CONTRACT text was not available to W9 (the capsule only names it), so the fields below follow plan s9 and the W9 packet. UNKNOWN = not measured.

## 1. Answer to the programme question
Tennis Scope A and Scope B cost, measured on Tennis evidence: see `vault/plans/d21-tennis-token-budget-2026-10-11.md` (W8 receipt).
- Scope A (160 fns, 48 families): P50 103-122M processed tokens, P80 351-376M, P95 883-918M. Hard authority ~380M in 25-function tranches. Confidence LOW. (WU-W8-receipt.md)
- Scope B (1,797 fns, 1,630 model-needed): P50 1,739-1,949M, P95 ~8,050M. No hard authority. Confidence VERY LOW. (WU-W8-receipt.md)
- Every per-function cost is a hypothesis x model (H x M): tokens per VERIFIED Tennis function = UNKNOWN (0 verified; W6, W8).

## 2. Scope-B admission: NOT YET
Admit when: a Tennis A/A passes; >=20 verified functions carry measured tokens; a >=3-member family curve falls; a >=20-insn discriminator confirms the compiler. Scope definition (D21) is unchanged.

## 3. Spend (`mission_spend.py goal-status --goal tennis-rf`, 2026-10-12)
cap 55,000,000; used 35,071,200 (settled 33,802,885 + open 1,268,315); remaining 19,928,800; exhausted false. W1-W5b worker sessions: 13,086,143 processed tokens over 321 calls (W6). Sunk/CAPEX; no per-function cost implied.
GEX44 jobs: 1 of 4 used (JOBS.md row 1, ksrmb-20261011-223128, W10c A/A, judged 3/3 MATCH). Zero local compiles. Phase-7 / cp50-c2 jobs: none used by this programme.

## 4. What was built (all wired + tested unless stated)
W1 send guard CAPSULE_NOT_CURRENT, source lint, custody miss classes (29/29); W2 readiness certificate (SEND_CERT_DRILL 10/10); W10a Tennis capsule profile (11/11); W10b Tennis judge + own F root cap 4 (18/18). NOT baseline: W6 ledger, W7 clustering, cascade record schema (unwired). Detail: `vault/knowledge_base/tennis_rf/UKDL_CANDIDATES_TENNIS_RF.md` section C.

## 5. Findings
- C2b root cause (ROOT-CAUSE-C2B.md): one missing CURRENT_CAPSULE read as 50 environment misses, plus 50/50 uncompilable sources.
- 0 % of programme spend was semantic work; 49.9 % exploration, 27.0 % tax, 22.5 % work; duplication factor 14.06 (W6).
- Tennis is ~70 % novel; 167 of 1,797 functions (9.3 %) deterministic-eligible (W7).
- REA: REJECT (REA-DISPOSITION.md).
- Knowledge: `vault/knowledge_base/tennis_rf/TRF_KNOWLEDGE_PROMOTION.md` (8 classes confirmed; FUNCTION_COST_INTRINSICNESS_FALLACY, FLAT_MARGINAL_COGNITION, REPEATED_RAW_BINARY_PAGE_FAULT NOT promoted, no evidence).

## 6. NOT proven / open
- A real compiled Tennis object matching (W10b NOT_PROVEN; only the W10c A/A row in JOBS.md says 3/3 MATCH, and no W10c receipt exists: the unit ended PARTIAL).
- Compiled-learning family discount, sequence curve, Haiku routing holdouts: not run.
- W8 should be rerun after a completed Tennis oracle run with verdicts.

## 7. Decisions for the Owner
None blocking. Capital: 19.9M of the 55M remains; no cap change requested. Recommended next: finish W10c (receipt), run ~24-function measurement, rerun W8, then decide Scope B admission.
