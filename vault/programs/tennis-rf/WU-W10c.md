# WU-W10c -- Tennis oracle jobs: the A/A, then the verified rates (<= 2 GEX44 jobs)

Common brief: `PROGRAMME.md`. Prerequisites: `WU-W10a-receipt.md`, `WU-W10b-receipt.md` (custody route). The
programme allows 4 Tennis jobs in total; read `JOBS.md` for how many are left. This unit may use at most 2.

Steps:
1. Job 1 = the W3b A/A: the Tennis capsule from W10a, the 3 W3b donors. `stage.py build` -> `stage.py certify <tag>`
   (W2 certificate) -> JOBS.md row BEFORE sending -> send by the W10b custody route -> wait -> judge.
   PASS = at least one Tennis object reproduced byte-exact. If it fails, record the failure class, add an entry to
   KNOWLEDGE.md, and stop with DONE (no job 2): W8 then reports the verified rate as FAIL, not UNKNOWN.
2. Job 2 (only after a PASS): W5a step 3. Batch all 12 W5a candidates (all preset variants, plus the W5b
   prototype-repaired variants from `measure/claims.jsonl`) into ONE certified job, record it in JOBS.md, send,
   judge. No repair round needs a third job; record residuals instead.
3. Per-function records: append to `measure/records.jsonl` with the layer that closed each function, the verdict
   (MATCH / PARTIAL % / FAIL class), compiles, model calls and processed tokens attributed (dedupe by message.id;
   missing = UNKNOWN). Update MEASURE.md with the compile-verified rate per layer (det type repair, model), and with
   the number of functions it was measured on.
4. Restore and verify the custody state as W10b specified (read it back), even when a job failed.
Zero local compiles. Continuation rule as in PROGRAMME.md step 4, but a continuation may not add jobs beyond 2.
Receipt (write it to vault/programs/tennis-rf/WU-W10c-receipt.md, Status line per PROGRAMME.md step 3; the chain
reads only that file): job ids, per-job verdicts, the verified rate table with n, and the custody state read back.
