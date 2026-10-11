# W8 receipt
Status: DONE

Commits: PP only (plans/d21-tennis-token-budget-2026-10-11.md, this receipt). Zero model work on functions, zero jobs, zero compiles. Calls ~8.
Oracle: WU-W10a ended PARTIAL, no W10a/b/c receipts exist, JOBS.md empty: compile-verified rate UNKNOWN for all layers (n=0); not FAIL, nothing was run to fail.

Scope A (M tokens; N=50/50/100/160 fns, 48 families; semantic lower bound 2.0):
| forecast | LOWER | P50 | P80 | P95 |
|---|---:|---:|---:|---:|
| CURRENT-TOPOLOGY | 31 | 103 | 351 | 883 |
| COMPILED-LEARNING | 44 | 122 | 376 | 918 |
Hard authority ~380M in 25-function tranches, confidence LOW. Compiled >= current: curve not measured, 96 % singletons, CAPEX only added.

Scope B (1,797 fns, 1,630 model-needed; semantic lower bound 66.5):
| forecast | LOWER | P50 | P80 | P95 |
|---|---:|---:|---:|---:|
| CURRENT-TOPOLOGY | 394 | 1,949 | 4,633 | 8,053 |
| COMPILED-LEARNING (family discount UNPROVEN) | 339 | 1,739 | 4,383 | 8,088 |
Hard authority: none. Confidence VERY LOW.

Admission: Scope B = NOT YET (curve UNKNOWN, 90.7 % model-needed, 0 verdicts, no oracle, dup factor 14.06); scope stays. Old hypothesis 47/215/755 and 434/1,927/4,640 compared in plan section 7.
Next unit must know: all per-function costs are H x M; the Tennis oracle (W10a-c) never completed, so rerun W8 after it. Plan file: vault/plans/d21-tennis-token-budget-2026-10-11.md.
