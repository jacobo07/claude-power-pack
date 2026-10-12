# P1P2 receipt
Status: PARTIAL

Worker: GEX44 headless `claude -p`, ended `error_max_turns` at 37 turns (19:22), wrote no receipt; its last act was
writing `tools/factor.py` (never run). TRF-C (coordinator) ran the remaining deterministic steps, zero model calls in
them. Tokens (worker.jsonl final `result.usage`): input 72 + cache_create 148,493 + cache_read 4,172,661 + output
66,868 = 4,388,094 processed; total_cost_usd 3.36. Outputs `M=/home/kobii/missions/tennis-w11/out/p1p2/`.

## Coordinator repair to factor.py (one root cause, two symptoms)
`gid()` only labels functions inside a partition, so `dag[fn]` / `ig[fn]` raised KeyError for functions outside it
(first: OSReport, anchored data set below DATA_MIN; then zero idiom hits). Fix: every fn defaults to no group id
(None = not in a group of >= 2), and per fn `data_basis` / `data_anchored_basis` records `below_DATA_MIN` vs
`partitioned`, so a below-minimum function is never read as a singleton (A1). Original kept as `tools/factor.py.orig`.
Facts restored from `facts.pass1.jsonl` (sha b3d93d67) before the run; factor.py merges m2c_with_ctx into facts.jsonl.

## Claims
- PROVEN Pass 1: facts.jsonl 1,797 rows (gate). Roles: UNKNOWN 1,615, TAILCALL_THUNK 111, LEAF_ACCESSOR 65,
  UNREACHABLE 6; each labelled role has its rule in extract_summary.json. CTOR/DTOR_SHAPE NOT emitted: 0 __ct__/__dt__
  symbols to validate a rule against (A1). Program functions scanned for callers/refs: 18,820.
- PROVEN Knowledge shock (A3): lint-clean 175 without header -> 276 with header; newly clean 101, newly dirty 0;
  80 of the 101 are OUTSIDE the 24 W5a/W12 draws. Reproduced: both arms run twice, clean sets and c sha256 equal.
  m2c status split 1,613 L1 / 92 M2C_ERROR / 92 M2C_FAILED in all four runs = W7's split. Many newly clean fns carry no
  struct tag (they gained from header prototypes/prelude); see `knowledge_shock.json` rows.
- PROVEN data_family (red 35 vs real 490 members in groups>=2), data_family_anchored (18 vs 112), motifs
  (2,023 motifs, 39.0 % of insns covered; red 0.53 %).
- INCONCLUSIVE structural_family: red A 588 / red B 524 vs real 926 members; pre-declared collapse needs <= 463.
- INCONCLUSIVE idiom_family: red 1,023 vs real 1,039 (multisets dominated by stack_guard_prolog, 8,949 program fns).
- PROVEN W12 no-regression: the 22 W12 lint-clean ids are clean with ctx (gate; predicate cross-checked: facts
  clean=True count 276 == clean_after 276).
- NOT_PROVEN idiom detectors: `idioms_test.txt` (>=1 positive + >=1 negative asm example per idiom) was never written.
  Hits are reported but the detectors are unvalidated. Program-wide fns: vtable_call 1,236, bool_from_compare 414,
  struct_copy 363, float_to_int 327, switch_jump_table 172, ptmf_call 66.
- W7 singletons 1,114: 772 belong to a >=2 group at a red-control-PROVEN resolution (1,046 at any resolution).
- residual_structural deciles p10 .153, p30 .409, p50 .709, p70-p100 1.0 (structural coverage, not semantic novelty).
- Blockers (blockers.json; rank, item, fns blocked, of which hard-fail): 1 HELPER:fn_800B4508 89; 2 M2C:unknown
  instruction cror 67 (51); 3 HELPER:fn_801CD7D0 64; 4 HELPER:fn_801CD868 56; 5 M2C_FAILED:Cannot find branch target
  52 (52); 6 HELPER:fn_800B32F8 45; 7 HELPER:fn_801D022C 43; 8 HELPER:fn_801CCE78 40; 9 HELPER:fn_801BFF60 39;
  10 HELPER:fn_801CDA9C 39; 11 M2C_FAILED:jump table for bctr 37 (37); 12-20 HELPER fn_801CFCE8 31, fn_8003ED00 29,
  fn_801CCE10 29, fn_801CD8AC 29, fn_801CFC9C 29, fn_801CFB90 23, fn_80200A78 23, fn_801EDA74 22, fn_801CD4C0 21.
  31 not-clean fns have no explained blocker. hypotheses.json: top-10 blockers, data only, nothing resolved.
- proof_family: UNKNOWN for all (no verdicts joined yet; W12 ledger has 22).

## Gates
`/opt/ksr-decomp/venv/bin/python -I tools/test_p1p2.py $M` -> P1P2_GATES=7/9, rc=1 (FAIL IDIOM-EXAMPLES,
FAIL RED-STRUCTURAL_FAMILY). Full lines: `gates.txt`.

## Hashes (sha256, on GEX44; large files not repatriated)
facts.jsonl cb69983e..; factor.json 1e115a59..; blockers.json b5b4e467..; hypotheses.json 4e585cd8..;
knowledge_shock.json 62dd94a9..; tools/factor.py 9c53fbb9.. (patched); test_p1p2.py d0767ded..

## Still UNKNOWN / next
Idiom examples; a structural key that collapses under its red control (size bucket + arity alone is too coarse);
proof_family join with W12 verdicts; the 31 unexplained not-clean fns. Knowledge Leverage Ratio token side: TRF-C.
