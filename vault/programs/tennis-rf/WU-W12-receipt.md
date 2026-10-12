# WU-W12 receipt
Claims: match=12, sent=22, drawn=24, partial=9, fail=1, donor_match=3
Status: DONE (closed by TRF-C; the worker, mission m-0acd380966c2, was fenced by the goal cap after judging, before records)

- Job 3 ksrmb-20261012-171117 (build candidate-20261012T170916Z, capsule cap1-5bf8cc7d7aac): certified READY, JOBS.md
  row 3 written before the single send, repatriated, judged 2026-10-12 17:24Z: 42 ledger rows. Job 4 untouched.
- Result (`python evidence/w12/records.py wst_tennis\w10\F\candidate_ledger.jsonl`): 12/22 sent functions MATCH
  (12/24 drawn); 9 PARTIAL; 1 FAIL BLOCKED_CONTEXT (fn_80252F34, COMPILE_FAILED); 2 excluded pre-send (lint UNK_FIELD:
  fn_8021EAA8, fn_8022F90C). Donor controls 3/3 MATCH. Exact-match units by preset: O4p 12, O2 5.
  MATCH: 801BD194 80203E40 80203FEC 8020711C 8020CC14 80230ABC 80230BF8 80257978 8025C600 80279E44 8027A154 803315A0.
  Correction: the worker's final message said 14; the ledger says 12.
- Records: `evidence/w12/measure/records.jsonl` (24 rows, layer M2C_TENNIS_CONTEXT, model_calls 0 per function).
  MEASURE.md: "W12 compile-verified rates" table with n. Versus W10c without context: 0/12.
- Custody read back (20:0x): Tennis root `wst_tennis\w10\F\CURRENT_CAPSULE.json` = cap1-5bf8cc7d7aac (job 3's capsule,
  by design per W10b: own root, nothing to restore). RF `recon_factory\gex44` = cap1-ba8a3cfe2822 (written 13:51, before
  W12's 18:58 build); Resort `match_accel_factory\gex44` = cap1-bccaf88bf463 (written 10-01). Both unchanged by W12.
- Uncommitted in wt_tennis_rf (not committed here, owner = that worktree's next unit): `gex44/tennis_context.h` comments
  no longer contain the word "asm" (the custody guard refuses any unit source containing it); worker reported
  test_tennis_context.py 9/9 after the edit. Residual lists 10 uncommitted paths in total.
- K7: W12 worker session 49a6a00d: 3,453,372 processed, 52 model calls (partial.json); GEX44 runtime of job 3 not
  model-billed. Prep (W12-prep) 2.50M was billed earlier.
