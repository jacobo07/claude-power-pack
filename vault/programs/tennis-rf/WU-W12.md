# WU-W12 -- Tennis measurement: ~24 functions, ONE GEX44 job (job 3 of 4)

Common brief: `PROGRAMME.md`. Needs W11 DONE. Read `WU-W11-receipt.md`, `MEASURE.md`, `JOBS.md`.
Purpose (W9 HANDOFF section 2): Scope-B admission needs >= 20 verified functions with measured tokens. This unit
produces the measured rates W8b needs.

Steps:
1. Draw: the 12 W5a functions plus 12 new ones, drawn BEFORE any candidate exists with seed 20261012 by the
   W5a method (pool = W3 sample60 m2c L1 rows not already drawn, strata by insns). Record the draw in MEASURE.md
   and `evidence/w12/draw.json` first.
2. Cascade per function (PROGRAMME.md economic rules): NO_WORK -> prior result -> Resort donor -> det type repair with
   W11 context -> model. Each model step carries its one-line Proof of Model Necessity.
3. One certified job: `stage.py build` -> `stage.py certify` -> JOBS.md row 3 BEFORE send -> send by the W10b custody
   route -> wait -> judge. Exactly ONE send. Job 4 stays in reserve; use it only if job 3 fails for an
   infrastructure cause that has since got a local regression gate.
4. Records: append to `measure/records.jsonl` per function: closing layer, verdict (MATCH / PARTIAL % / FAIL class),
   compiles, model calls, processed tokens deduplicated by message.id (missing = UNKNOWN). Update MEASURE.md with the
   compile-verified rate per layer and its n.
5. Restore and read back the custody state as W10b specified, even if the job failed.
Done-check: JOBS.md row 3 judged, records for every drawn function, MEASURE.md rate table with n, custody read back.
Receipt: `vault/programs/tennis-rf/WU-W12-receipt.md`. K7 row as in W11.
