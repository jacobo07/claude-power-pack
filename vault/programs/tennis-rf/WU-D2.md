# WU-D2 -- Ph2 W12A+ autopsy (GEX44 cpu)

Common brief: `D28-BRIEF.md`. Plan Ph2, MDG 6, 7, 8. Inputs: W12 evidence (PP `evidence/w12/`: records.py,
measure/records.jsonl, draw.json; the job 3 return under `M/out/w12*`), P1P2 facts.jsonl / knowledge_shock.json,
D1d `idioms_status.json` + `cluster_status.json` (use only VALID ones).

Steps:
1. Causality: for each of the 22 judged W12 functions, which header facts (struct tags, fields, prelude items) its
   m2c-with-ctx output actually used (grep the generated source for each fact). `causality.json`.
2. Near-match decomposition: for the 9 PARTIAL functions, the minimal mismatch signature from the objdiff output
   (first diverging insn, class: REGALLOC, SCHEDULING, POINTER_STRIDE, PTMF_R12, SIZE_+-N, FLAG/CODEGEN, OTHER).
   Prior flags: 8021F8BC pointer stride, 8021F3E4 ptmf r12, 6 SIZE +-1-2 words. Classes -> `near_match.json`;
   root-cause compression ratio = distinct classes / PARTIAL functions.
3. 80252F34: lint-clean yet COMPILE_FAILED(context). Find the missing context item from the compile log; write
   the admission story (why lint admitted it) and the lint rule that would have refused it. `admission_gap.md`.
4. Knowledge-shock attribution 175 -> 276: leave-one-fact-out over the header's 35 struct tags (m2c + lint only, 20
   cores; NO compile). Per fact: functions it alone makes clean, functions needing it with others. Rank.
   `shock_attribution.json`. Red control: drop a random non-header struct name -> ~0 change.
5. `test_d2.py` (V-D2-*): 22 causality rows, 9 near-match rows, attribution sums reconcile with 276-175 (or the
   residual is named), red control passes.
Done-check: test_d2 exit 0; evidence copied to PP `evidence/d28/d2/`; the near-match classes listed in the receipt.
Receipt: `WU-D2-receipt.md`.
