# WU-D6 -- Ph6 first frontier collapse (GEX44 cpu + job 4, the last approved job)

Common brief: `D28-BRIEF.md`. Plan Ph6, MDG 12. Inputs: D5 `shock_candidates.json` (survivors), W12 job route.

Steps:
1. Certify the top 1-3 surviving facts (no CONFLICT ones): each gets a provenance line (asm evidence, falsification
   result) and invalidators (what observation would retract it). Extend the context header in wt_tennis_rf
   (`tools/wros/binary/decomp/gex44/tennis_context.h` + `.py`) and its test (`test_tennis_context.py`); commit there
   (pathspec; if the recon hook refuses, PROGRAMME.md step 2 patch route).
2. Measure direct unlock: lint-clean count and the list of newly clean functions (m2c + lint over all 1,797).
3. Compile-verify with job 4: compose units for the newly clean functions (cap the batch at what job 3's 42 units
   took) plus the 3 donor controls, exactly the W12 route: `stage.py build` -> `stage.py certify` -> JOBS.md row 4
   BEFORE send -> send -> wait -> judge -> custody read back. ONE send. If the batch is empty (nothing newly clean),
   do not send: keep job 4, record why.
4. Records into `measure/records.jsonl` with closing layer `KNOWLEDGE_SHOCK`; MEASURE.md rate row with n.
Done-check: header test green, JOBS.md row 4 judged (or justified unused), unlock numbers with commands.
Receipt: `WU-D6-receipt.md`.
