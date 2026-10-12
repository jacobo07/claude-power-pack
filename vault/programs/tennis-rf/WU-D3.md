# WU-D3 -- Ph3 global residual census + Semantic Residual Compiler v0 (GEX44 cpu)

Common brief: `D28-BRIEF.md`. Plan Ph3 and section 4 "Residual", MDG 9, 17, 18. Inputs: P1P2 facts/factor/
blockers, D1d status files, D2 outputs.

Steps:
1. `M/out/d28/tools/residual.py`: per function, residual = facts(fn) - certified(header facts, VALID idioms, motif
   cover, proof) -> {unresolved_vars (unknown field offsets per base, `?` types, unknown helpers), conflicts,
   obligations, expected_unlock}. Writes `residuals.jsonl` (1,797 rows; UNKNOWN never counted as zero).
2. Census: distribution of residual size, functions with empty residual not yet lint-clean (a contradiction:
   name each), counts by role.
3. Distance-to-autonomy 0-5 per function (0 = lint-clean + compile-verified, 1 = lint-clean, 2 = residual only
   certified-fact gaps, 3 = needs a hypothesis from D4/D5 kinds, 4 = needs model reasoning, 5 = UNKNOWN). Rule
   written in the code, histogram in `autonomy.json`.
4. Effective remaining work = sum over functions of a cost per distance class priced from MEASURED rates only
   (W12 deterministic rate 12/22, W12/P1P2 tokens); classes without a measured rate are reported as UNKNOWN ranges.
5. `test_d3.py` (V-D3-*): 1,797 rows, every lint-clean fn has distance <= 1, the 22 W12 fns agree with their
   verdicts, the census contradictions list is empty or each item is explained.
Done-check: test_d3 exit 0; evidence to PP `evidence/d28/d3/`.
Receipt: `WU-D3-receipt.md`.
