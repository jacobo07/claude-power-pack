# WU-W12 -- Tennis measurement: ~24 functions, ONE GEX44 job (job 3 of 4)

Common brief: `PROGRAMME.md`. Needs W11 DONE. Read `WU-W11-receipt.md`, `MEASURE.md`, `JOBS.md`.
Purpose (W9 HANDOFF section 2): Scope-B admission needs >= 20 verified functions with measured tokens. This unit
produces the measured rates W8b needs.

Steps:
1. Draw: DONE by the coordinator (MEASURE.md "W12 draw", `evidence/w12/draw.json`, seed 20261012). Do not redraw.
2. Cascade: DONE on GEX44 (Owner option a, 2026-10-12; laptop below the RAM floor). Read `W12-PREP-READY.md`: it
   names the patch to apply in wt_tennis_rf (`patches/W12-prep-1.patch`, `git apply --ignore-whitespace`, never
   commit .ksr_vault or CRLF churn), the m2c+lint outputs for all 24 functions (`wst_tennis\w12\m2c\`), the
   per-function prep records and which functions are EXCLUDED. Re-run `test_tennis_context.py` with the laptop
   factory venv (`C:\Users\User\Apps\decomp_tools\venv\Scripts\python.exe`) after applying. Do not redo the cascade.
3. Units: compose the job units from the included m2c outputs with the context header and the presets the W10c
   build used (the build path W10c used for job 2, now with the prelude and context). Then one certified job: `stage.py build` -> `stage.py certify` -> JOBS.md row 3 BEFORE send -> send by the W10b custody
   route -> wait -> judge. Exactly ONE send. Job 4 stays in reserve; use it only if job 3 fails for an
   infrastructure cause that has since got a local regression gate.
4. Records: append to `measure/records.jsonl` per function: closing layer, verdict (MATCH / PARTIAL % / FAIL class),
   compiles, model calls, processed tokens deduplicated by message.id (missing = UNKNOWN). Update MEASURE.md with the
   compile-verified rate per layer and its n.
5. Restore and read back the custody state as W10b specified, even if the job failed.
Done-check: JOBS.md row 3 judged, records for every drawn function, MEASURE.md rate table with n, custody read back.
Receipt: `vault/programs/tennis-rf/WU-W12-receipt.md`. K7 row as in W11.
