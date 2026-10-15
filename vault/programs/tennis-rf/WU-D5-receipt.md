# WU-D5 receipt (v2 residual)
Status: DONE (done-check met: `test_d5.py` exit 0, 10/10 gates; GEX44 `M/out/d28/d5/test_d5.txt`, copy `evidence/d28/d5/test_d5.txt`).
Evidence: PP `evidence/d28/d5/` (cror_unlock.json, causal_unlock.json, draw.json, cands_raw.json, tools/d5.py, tools/test_d5.py). No model calls, no GEX44 job slot used (m2c+lint only, 20 cores).

## 1. cror (own experiment)
- Intervention (tool-side asm preprocessing, stated): `cror eq,[crN]{gt|lt},[crN]eq ; bne|beq T` -> `b{lt|gt|ge|le} [crN,] T`, cror -> nop. Exact for every total-order compare (V-D5-CROR-EXACT-TOTAL-ORDER, 12 cases). Caveat: float UNORDERED (NaN) sets only the UN bit, so the original `bne` is taken and the rewrite is not; m2c has no UN model. Not applied when cr0.eq is read again on the fall-through path or the branch is not the next instruction.
- 186 cror in the 67 dependents; 171 rewritten; 15 bailed (7 EQ_LIVE_ON_FALLTHROUGH, 8 NEXT_NOT_BNE_BEQ).
- **Measured unlock: wave 1 = 0 of 67 (0 of the 51 "sole" fns). New errors 0. Wave 2 = 0** (no fn has a blocker set made only of now-clean callees; nothing became clean in wave 1).
- Why: D4's "sole blocker" was sole only among *visible* keys. A fn that m2c cannot translate emits no C, so none of its other blockers (HELPER, FIELD, QTYPE_LOCAL, SELF_SIG) were observable. After the rewrite, 56 of 67 are L1 and each shows its hidden blockers (cror_unlock.json `not_unlocked`); 11 still fail (6 cror, 5 cror+`mfcr`, from the bails) and 2 of those 56-complement fail on `psq_l`/`ps_muls0`. D4's "51 proven sole-unlock fns" is therefore CONTRADICTED as an unlock claim; cror is a real prerequisite (fns went from no C to C) but unlocks nothing alone.

## 2. Draw (draw.json, seed 20261013)
Population = HELPER vars of frontier.json (the only kind whose delta a script can state from the asm); stratified by degree = blocked_direct[1], contiguous quartiles; 6 from the 29 top-30 HELPERs (1 per quartile + 2 seeded extra), 5 from the HELPERs below rank 30 (1 per quartile + 1 extra). Top-30 set recomputed = dominators.json top30. FIELD/QTYPE/SELF_SIG kinds were not drawn (no stateable asm delta): a scope limit, not coverage.

## 3-4. Causal unlock (causal_unlock.json)
| var | D4 rank | D4 degree (direct fns) | hyps | verdict | unlock |
|---|---|---|---|---|---|
| M2C cror | 17 | 67 (51 sole) | rewrite | CONTRADICTION | 0 |
| HELPER:fn_801D022C | 6 | 43 | 4 | SUPPORT | 3 (fn_80242AC8, fn_80242CAC, fn_80242E24), 0 new errors |
| HELPER:fn_801CCE10 | 13 | 29 | 3 | CONTRADICTION | 0 |
| HELPER:fn_801CD8AC | 14 | 29 | 8 | CONTRADICTION | 0 |
| HELPER:fn_80200A78 | 19 | 23 | 2 | CONTRADICTION | 0 |
| HELPER:fn_801CD4DC | 27 | 18 | 1 | CONTRADICTION | 0 |
| HELPER:fn_801E11E0 | 89 | 9 | 2 | CONTRADICTION | 0 |
| HELPER:fn_802100EC | 23 | 4 | 2 | CONTRADICTION | 0 |
| HELPER:fn_801BF164 / 802087F4 / 80234970 / 801F4980 | 908 / 1096 / 1175 / 1067 | 1 each | 1-2 | CONTRADICTION | 0 |

Every CONTRADICTION is "unlock 0" for every admitted hypothesis: each dependent still carries other blockers, so a single prototype cannot flip it (D4's low bound 0 was the real value). Resolved-key counts confirm the delta did what it said (each prototype removed `HELPER:F` from all its dependents): the unlock is capped by other keys, not by a failed delta.
Only SUPPORT: fn_801D022C, and only the hypothesis `void fn_801D022C(void)` (callee body reads no args, never writes r3); the 5/6/7-arg variants unlock 0. Weak: callers set 5+ arg registers, so this prototype is asm-consistent on the callee side and doubtful on the caller side. Kept, not resolved; single surviving hypothesis, so no CONFLICT.

Spearman(D4 degree, measured unlock): n=12 (with cror) rho=0.40; n=11 (without) rho=0.51; but 11/12 (10/11) unlocks are 0, so the value comes from ties plus one positive point. **No claim past this: n supports neither that degree has causal value nor that it lacks it.** Measured facts: of the 6 top-30 HELPERs drawn, 1 unlocked anything; of the 5 below, none; and the one strong D4 claim tested (cror, 51 sole) failed.

## 5. Gates (test_d5.txt)
V-D5-DRAW, -DRAW-STRATA, -SUPPORT-REPRO (SUPPORT hypothesis rerun, sha equal), -CROR-REPRO (67 deps sha equal), -CONTRADICTION, -CONTROL-WRONG-DELTA (arity 0 for a callee reading r3,r4, and void-with-r3-read, rejected by the asm check; the consistent delta admitted. Adapted from "width vs load op": a HELPER delta has arity/return, not field width), -CONTROL-NOOP (unlock 0, output byte-identical to baseline), -CROR-EXACT-TOTAL-ORDER, -CROR-REWRITE-FIRES, -CROR-BAILS: all PASS.

## Commands
GEX44 `M/out/d28/d5`: `KSR_DECOMP_TOOLS=/opt/ksr-decomp /opt/ksr-decomp/venv/bin/python -I tools/d5.py all .` then `... -I tools/test_d5.py .`. Inputs: d1d facts/blockers/ctx_run1, d4 frontier/dominators.

## Open (not done)
- FIELD / QTYPE_LOCAL / SELF_SIG / M2C_FAILED candidates not drawn (need struct or semantic judgement: MODEL_NEEDED).
- The 15 bailed cror shapes (mfcr consumer, non-adjacent branch) and the psq_l/ps_muls0 fns are untouched.
- Joint deltas (several prototypes at once) are the natural next measurement since single deltas are capped by co-blockers; not part of this unit.

## Plan delta
MDG 11: single-delta causal unlock measured on n=12: 1 SUPPORT (3 fns), 11 CONTRADICTION (0 fns); cror unlock 0 (D4's 51-fn sole-unlock refuted: hidden co-blockers). Degree rank has no demonstrated causal value at this n.
