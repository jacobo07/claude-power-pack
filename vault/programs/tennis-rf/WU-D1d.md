# WU-D1d -- Ph1d fixtures and abstention (GEX44 cpu)

Common brief: `D28-BRIEF.md`. Plan rows DETERMINISTIC_ANALYSIS_KEYERROR, IDIOM_METRIC_UNVALIDATED,
STRUCTURAL_CLUSTER_INCONCLUSIVE; MDG 5. Inputs: `M/out/p1p2/` (copy into `M/out/d28/d1d/` first) and the patched
`factor.py` there.

Steps:
1. KeyError fixture: the P1P2 KeyError was a function outside every partition (gid default). Write
   `M/out/d28/tools/test_factor_partition.py` with a 3-function synthetic corpus where one function is an outsider;
   it must fail on the unpatched code path (keep a copy of the original factor.py beside it to prove RED) and pass
   on the patched one.
2. Idiom fixtures: `idioms_test.txt` with >= 1 positive and >= 1 negative asm snippet per idiom of the P1P2 table v0,
   taken from REAL Tennis asm (cite fn + addr). Run the idiom matcher on them. An idiom without both = `ABSTAIN`:
   its hit counts are removed from every downstream score (write `idioms_status.json` {idiom: VALID|ABSTAIN, why}).
3. Cluster abstention: rerun the structural_family red control (permute cfg features, 20 permutations, seeds
   recorded). Measured P1P2: red 588/524 vs real 926 (needs <= 463 to count). Write `cluster_status.json` with each
   grouping's real vs red distribution and VALID|INCONCLUSIVE. INCONCLUSIVE groupings are flagged, never used as
   evidence by later units.
4. `test_d1d.py` (V-D1D-* lines): fixture RED-then-GREEN proven, every idiom VALID or ABSTAIN, every grouping has
   its red control, rerun reproduces the numbers.
Done-check: `test_d1d.py` exit 0 on GEX44; status files copied to PP `evidence/d28/d1d/`.
Receipt: `WU-D1d-receipt.md`.
