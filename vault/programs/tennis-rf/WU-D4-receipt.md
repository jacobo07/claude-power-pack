# WU-D4 receipt
Status: PARTIAL (done-check NOT met: `test_d4.py` exits 1 on V-D4-RED-FALLS; 6 of 7 gates PASS. Not weakened to pass.)
Done-check: `python -I tools/test_d4.py d3 d4` on GEX44 (M/out/d28) -> TEST_D4 FAIL V-D4-RED-FALLS, exit 1. Output `evidence/d28/d4/test_d4.txt`.
Evidence: PP `evidence/d28/d4/` (frontier.json 3,429 vars, dominators.json, causal.json 18 classes, redcontrol.json, tools/). GEX44 M/out/d28/d4/.

## Results
1. Frontier: 3,429 unresolved vars over 1,521 non-clean fns (field_offset_untyped excluded: per-function offsets, no cross-function identity). Rules, cost table
   and the transitive rule are stated at the top of `tools/frontier.py` and copied into frontier.json. Transitive rule: only HELPER:F / SELF_SIG:F are
   signature-bearing; a caller is blocked only if its own signature uses the type (undecidable from asm) -> transitive range [0, all non-clean ancestors of F]. Other kinds [0,0].
2. Top 30 dominators (rank, var, blocked [low,high] fns, score [low,high]): in dominators.json. 29 are HELPER prototypes (script-fillable, cost 1-2), #17 is
   `M2C:unknown instruction cror` (sole 51, total 67, tool-side). Top: HELPER:fn_800B4508 89, fn_801CD7D0 64, fn_801CD868 56, fn_80210018 50, fn_800B32F8 45,
   fn_801D022C 43, fn_801CCE78 40, fn_801BFF60 39, fn_801CDA9C 39, fn_802544AC 34. Low is 0 for every HELPER (each function also has per-function blockers),
   so unlock is NOT proven for any prototype alone; only `cror` has a proven sole-unlock (51 fns).
3. Causal: 18 classes (lint, blocker, W12 verdict, D2 near-match primary). 5 compress to one root (the 5 D2 near-match codegen rules, 9 PARTIAL fns).
   The lint/blocker classes have NO_SHARED_ROOT (each spans many causes); W12 MATCH/PARTIAL carry no unresolved var.
4. Red control: FAILS. Direct counts are degree counts, invariant under any degree-preserving shuffle (score-level control falls: low/high/mid all false, reported).
   Transitive-only control (permute call subjects, 20 perms): real 6.67 vs shuffled mean 6.19, max 8.63 -> does not fall. Ranking is therefore degree-driven and
   INCONCLUSIVE as a structural claim (dominators.json `red_control_verdict`). Transitive high added ~0 to the top 30.
5. Reruns reproduce (sha256 of outputs equal, V-D4-REPRO PASS).

## Plan delta
MDG 10/11/14/15: frontier = 3,429 vars; dominator ranking exists but red control did not discriminate -> treat energy ranges as degree counts, not structure. Real lever
signal: prototype table (29 of top 30) and `cror` (51 proven sole-unlock fns). Failure root causes: only the 5 codegen rules compress.

## Commands
GEX44 M/out/d28: `python -I tools/frontier.py d3 d1d near_match.json d4` (+ `d4_rerun`), then `python -I tools/test_d4.py d3 d4`. Inputs: d3/residuals.jsonl, d1d/facts.jsonl, D2 near_match.json. No model calls.
Open: a red control that can discriminate needs unlock semantics (per-function keys resolved together); not done here.
