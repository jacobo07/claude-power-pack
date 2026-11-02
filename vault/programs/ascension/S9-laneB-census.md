# S9 Lane B0-B2 -- Exactness Bridge census (deterministic, $0)

Repo: GEX44 `/home/kobii/missions/t1-campaign`, branch `t1/campaign`, base HEAD `62e108c6`, lane commit **`8adf4843`** (no push).
No model call, no `llm_fix run`, and no mission was run in this lane. Every number below comes from a command run on GEX44 at the repo root.
Glue: `tools/ascension_s9_census.py` (`corpus | diff | twin | census`). It only reuses existing owners: shared_scope (rules, held_out, survey data),
cv1/fastmatch/toolchain_sd (compile under the sd8 lane), fingerprint (`objdiff_raw/extract/normalize/make_row`), causal_diff (`classify_row/derive`),
build_twin (`VARIANTS/variant_flags/_phase/outcome/verdict`) and llm_fix (`sha`, `harness_dir`). The only new logic is the morph-class to cause-layer map
and the class rule (`census_class`).

## B0a -- Model-spend accounting (verified)

Spend is recorded by `modules/recon_fabric/llm_fix.py spend_since()`. For each `evidence/llm-fix/<run>/results.jsonl` it adds `cost_usd` and
`prior_cost_usd`. A run is admitted at its manifest stamp. A straddler (admitted before `since`, resumed after it) is counted whole, so the total can
over-count but never under-count. The authority is set in `tools/test_recon_fabric_ascension.py:8` (`AUTH_USD, SINCE = 471.10, "2026-10-31T15:30:00+01:00"`).

Command: `timeout 60 python3 -m modules.recon_fabric.llm_fix spend --since 2026-10-31T15:30:00+01:00` -> rc=0

| measure | value |
|---|---|
| `total_usd` | **331.0298** |
| runs counted | 14 (all `how=manifest`, 0 straddlers) |
| largest runs | ascs6-prev 48.5516, ascs6-new 47.669, s8d-r1 35.4481, g4-A6 34.8385 |
| authority / headroom | 471.10 / 140.0702 |

Verdict: the ~$331 claim is **CONFIRMED** ($331.03 settled, inside the $471.10 authority).

## B0b -- Build Twin check (the 73 S8 transitions + 5 held-out)

Command: `timeout 580 python3 tools/ascension_s9_census.py twin` -> `evidence/ascension/s9/twin.json`. Each of the 78 best candidates is compiled under
the sd8 lane and then under every `build_twin.VARIANTS` recipe. Instrument check: the baseline pct matched the recorded best pct for 78 of 78 (`baseline_mismatch: []`).

| variant (dimension) | outcomes over 78 | pct up / down | exact | G3 twin verdict over 944 certified |
|---|---|---|---|---|
| inline_auto | SAME_OBJ 78 | 0 / 0 | 0 | INDISTINGUISHABLE |
| fpc_off | SAME_OBJ 78 | 0 / 0 | 0 | INDISTINGUISHABLE |
| fpc_on | SAME_OBJ 77, NO_MATCH 1 | 0 / 1 | 0 | INDISTINGUISHABLE |
| inline_deferred | SAME_OBJ 46, NO_MATCH 32 | 0 / 0 | 0 | FALSIFIED (2) |
| ogws_pair | SAME_OBJ 46, NO_MATCH 32 | 0 / 1 | 0 | FALSIFIED (2) |
| inline_off | SAME_OBJ 63, NO_MATCH 15 | 0 / 14 | 0 | FALSIFIED (36) |
| sdata_flip | SAME_OBJ 19, NO_MATCH 59 | 4 / 53 | 0 | FALSIFIED (207) |
| opt_O4s | SAME_OBJ 16, NO_MATCH 62 | 8 / 36 | 0 | FALSIFIED (214) |
| opt_O3p | NO_MATCH 78 | 7 / 67 | 0 | FALSIFIED (469) |
| opt_O0 (control) | NO_MATCH 78 | 2 / 69 | 0 | FALSIFIED (725) |

TU spread (the split target objects; all Tennis fns share the one pinned recipe): auto_03_80202950 41, auto_03_8023FE44 27, auto_03_8032BC4C 4,
auto_03_80257B08 3, auto_03_80278300 2, auto_03_8025643C 1.

**Verdict: no shared compiler/flag/TU uncertainty with fan-out.** The three unpinned dimensions (inline_auto, fpc_on, fpc_off) leave 77 or 78 of 78
objects byte-identical and raise nothing. Every variant that moves a pct makes far more rows worse than better. That variant is already falsified by
207 to 725 certified fns, and no variant makes any of the 78 exact. The one structured signal is a per-function lead, not a recipe fault.
The 4 identical void-arith fns at 0 % (fn_8020FFB0, fn_802209EC, fn_80221B7C, fn_80222BB0) all score 52.941177 under `-O3,p`. That points to a
scheduling-form difference in one source shape, filed under UNKNOWN_DIAGNOSIS below.

## B1 -- Transition Corpus (`evidence/ascension/s9/transition.jsonl`, 78 rows)

Command: `timeout 300 python3 tools/ascension_s9_census.py corpus`, then `diff --jobs 12`.

- Definition: `keep and state != CERTIFIED and not lane[0]` over `sweep-b.json`. This is the same predicate as `shared_scope.fanout` v5t `compile_gains`.
  It gives **73** (B) and **5** on `sweep-h.json` (H: fn_8021391C, fn_80213BB0, fn_80216D60, fn_802293D0, fn_8022F260). All 73 have frontier state NO_COMPILE.
- Correction to the sweep-b field semantics: `rules[k]` is `[changed, compiles, pct]`, not `[before, after, pct]`. The pre-S8 compile is `lane[0]`
  (source: `shared_scope.sweep` docstring).
- Unlocking rule (the rule alone changes the text AND compiles): void-arith, sp-locals, ptr-args, or `v5t-combined(shared_table+...)` when no single
  rule compiles alone. Per-row counts are in the file.
- Pre-S8 diagnostics: all 78 rows have `survey-lane.json` diagnostics (`pre_diag_missing: []`). First diagnostics: UNDEFINED_IDENT:<local> 24,
  ILLEGAL_OPERANDS:void*+int 22, NOT_STRUCT:<local> 15, IMPLICIT_CONVERSION:long->void* 10, ILLEGAL_OPERANDS:void*+long 5, long->long* 1, void*-int 1.
- **"69 of 73 in s8b-diagnosis, 4 missing" is FALSE.** `s8b-diagnosis.json` is the output of `shared_actuate.diagnose`, which covers only the
  shared-type-class dependents, not the transition set. Overlap with the 73 is **20**. **53** of the 73 are absent from it, and 49 of its 69 are not
  transitions (37 still fail to compile after v5t, plus H, plus lane-compiling fns). So there is no "4 absent" set to name. Each of the 53 is
  diagnosed instead from survey-lane (pre-S8) plus the objdiff residual in B2.
- Best candidate and provenance: S8d-model 26 (the IMPROVED rows; their `best.c` is in the harness dir, sha256 matches `best_sha256` for 27 of 27),
  sweep-v5t 52. S8a-search: 15 rows, all BUDGET_EVALS. Their search trees persist only as a sha, so the source is **unrecoverable**: recorded, not used.
  The S8d non-dispatched 13 and the S8d NO_GAIN 1 fall back to v5t.
- Instrument checks: recomputed v5t pct equals the sweep pct for 78 of 78. Recomputed S8d pct equals the recorded `best_pct` for 27 of 27.
- Held-out: the 73 B rows have 0 held-out members (sweep-b excluded 184). The 5 H rows carry `held_out.any=true`. They are measured, never tuned on.
- Each row also carries `model_history`: every llm-fix run row for that fn, with its cost.

## B2 -- WHY_NOT_EXACT census (`evidence/ascension/s9/why_not_exact.json`)

Command: `timeout 120 python3 tools/ascension_s9_census.py census`. Each best candidate's objdiff goes through `fingerprint.normalize` and then
`causal_diff.derive`, and each differing row through `classify_row`. The row is then mapped to a layer:

| morph classes | layer |
|---|---|
| FRAME/STACK_SLOT/MISSING_STACK/EXTRA_STACK | STACK_LAYOUT |
| REG_RENAME | REGISTER_ALLOCATION |
| BRANCH_* | BRANCH_FORM |
| WIDTH, CONSTANT on a load/store | TYPE_LAYOUT |
| RELOC_FORM | SDA_RELOCATION |
| CALL_SYMBOL, one-sided bl/b/bctrl | CALL_SHAPE |
| signed/unsigned opcode pairs | SIGNEDNESS |
| other CONSTANT/OPCODE/one-sided | EXPRESSION_SHAPE |
| UNEXPLAINED | UNKNOWN_DIAGNOSIS |

Class rule: a row at **>= 95 %** (llm_fix's own `min_pct` near line) is `NEAR:<layer signature>`. A row below 95 % is `FAR:STRUCTURAL_CFG` when it has
both a len gap and a cfg gap, `FAR:EXPRESSION_SHAPE` when it has a len gap only, and `FAR:<dominant layer>` otherwise. A row at 0 % is UNKNOWN_DIAGNOSIS.

**Collapse (73 B rows): 73 -> 10 causal classes** (78 -> 10 with H). Other cuts of the same data: dominant layer 4, layer signature 21,
causal_diff `cause` 7, causal_diff `signature` 41. Only 25 of 73 B rows are near (>= 95 %); 48 are far.

| rank | class | n (B) | held-out | median gap (hundredths %) | within 1 % | defining atoms |
|---|---|---|---|---|---|---|
| 1 | FAR:STRUCTURAL_CFG | 28 (25) | 3 | 4059 | 0 | REG_RENAME, MISSING_OTHER, MISSING_STACK, EXTRA_OTHER, CONSTANT |
| 2 | FAR:EXPRESSION_SHAPE | 15 (14) | 1 | 2928 | 0 | REG_RENAME, MISSING_OTHER, EXTRA_OTHER, MISSING_STACK |
| 3 | NEAR:REGISTER_ALLOCATION | 14 (14) | 0 | 27.5 | 11 | REG_RENAME only |
| 4 | UNKNOWN_DIAGNOSIS | 7 (7) | 0 | 10000 | 0 | EXTRA_OTHER, EXTRA_STACK, MISSING_OTHER |
| 5 | NEAR:EXPRESSION_SHAPE+REGISTER_ALLOCATION | 4 (3) | 1 | 214.5 | 0 | REG_RENAME, EXTRA_OTHER |
| 6 | NEAR:SDA_RELOCATION | 4 (4) | 0 | 11 | 4 | RELOC_FORM x1 each |
| 7 | NEAR:REGISTER_ALLOCATION+SDA_RELOCATION | 2 (2) | 0 | 78.5 | 1 | REG_RENAME, RELOC_FORM |
| 8 | FAR:REGISTER_ALLOCATION | 2 (2) | 0 | 884 | 0 | REG_RENAME |
| 9 | NEAR:EXPRESSION_SHAPE+TYPE_LAYOUT | 1 (1) | 0 | 143 | 0 | CONSTANT, EXTRA_OTHER |
| 10 | NEAR:REGISTER_ALLOCATION+TYPE_LAYOUT | 1 (1) | 0 | 229 | 0 | REG_RENAME, WIDTH |

Rank order: fan-out (n) first, then held-out members, then median gap. No row in the corpus shows a SIGNEDNESS, BRANCH_FORM-dominant, CALL_SHAPE,
INLINING or BUILD_CONTEXT class. That is measured, not assumed: BUILD_CONTEXT was falsified by B0b.

### Top 3 dominator classes

1. **FAR:STRUCTURAL_CFG** (28). Members: fn_80204070 fn_80208EF8 fn_8020B598 fn_8021391C fn_80213BB0 fn_80215A84 fn_80215AE0 fn_8021DFB4 fn_8021E254
   fn_8022F260 fn_802319BC fn_80231E18 fn_80243798 fn_80243FF0 fn_80244DAC fn_8024C3DC fn_8024C48C fn_8024CD1C fn_8024CECC fn_8024D0BC fn_8024D26C
   fn_80256984 fn_80256A9C fn_80257834 fn_8025829C fn_8025D57C fn_8032C8E8 fn_8032CA84. **Held-out: fn_8021391C, fn_80213BB0, fn_8022F260.**
   The instruction count and the control flow both differ: the source shape is wrong (m2c lift structure). This is not a residual one rule closes.
2. **FAR:EXPRESSION_SHAPE** (15). Members: fn_8020A6FC fn_80213328 fn_802168FC fn_80216D60 fn_80218B48 fn_8021AC34 fn_802272B8 fn_80228A0C fn_8022C230
   fn_8022C764 fn_80230CB0 fn_8024105C fn_802564C4 fn_8027EDC0 fn_80333A78. **Held-out: fn_80216D60.**
3. **NEAR:REGISTER_ALLOCATION** (14, the closest to exact: median gap 0.275 %, 11 within 1 %). Members: fn_80220214 fn_80222480 fn_80222ED8 fn_802262F0
   fn_80226454 fn_802265D0 fn_8024DE84 fn_80255B08 fn_80255C00 fn_80256314 fn_802563FC fn_80256BB4 fn_80256CD8 fn_8025DD74. Held-out: none.

**Bridge note (closeness, not fan-out):** NEAR:SDA_RELOCATION (fn_80212A1C, fn_80212FF4, fn_80215B6C, fn_80216590) is 4 fns at 99.89 to 99.91 %. Each has
exactly **1** differing row, a RELOC_FORM. All 4 are ptr-args unlocks with S8d best. They are the cheapest exact candidates in the corpus.
Together with NEAR:REGISTER_ALLOCATION, that is 18 single-layer near rows.

### Open UNKNOWN_DIAGNOSIS (7)

| fn | unlock | pre-S8 first diag | residual | lead |
|---|---|---|---|---|
| fn_8020FFB0, fn_802209EC, fn_80221B7C, fn_80222BB0 | void-arith | ILLEGAL_OPERANDS:void*+long | 0 %, 17/17 insns, 25 rows | the same source shape; 52.941177 % under `-O3,p` (twin): a scheduling-form lead, not a recipe fault (opt is falsified on 469 certified) |
| fn_80243234 | sp-locals | UNDEFINED_IDENT:<local> | 0 %, 95 vs 81 insns | 30.81 % under sdata_flip |
| fn_8025BF8C | sp-locals | UNDEFINED_IDENT:<local> | 0 %, 1 vs 50 insns | the target is 1 instruction: the lift is the wrong body or a stub |
| fn_8032D348 | sp-locals | UNDEFINED_IDENT:<local> | 0 %, 155 vs 279 insns | the lift is about 1.8x too long |

## Owner reuse notes

- `atoms.py` is **live**: build_twin imports `atoms as A`, and 7 modules or tools import it. `g3_atoms.py` (G3-4 ingestion over `atoms.PREDICATES_G3`) is
  reached only by `tools/test_recon_fabric_g34.py`. The two are layered, not parallel copies. This came from a grep of importers and was not traced further.
- No parallel module was added. `tools/ascension_s9_census.py` is glue only.
- Not reused (not needed): certify.py (no candidate reached 100), compiler_causality.py, search_ops.py, g4_ops.py, tools/fixed_point_objdiff.py.

## Commit

`8adf4843` on `t1/campaign` (pathspec: `evidence/ascension/s9/{transition.jsonl,why_not_exact.json,twin.json}`, `tools/ascension_s9_census.py`). Not pushed.
