# W11 receipt
Status: DONE

Slice done across 4 sessions: laptop m-4420dde76545 (breaker at 30 calls), laptop m-132da7bbecd1 and a third laptop
re-arm (both stopped on host RAM starvation, ~2 GB free, 38 claude processes), then a GEX44 headless worker
d7e8ca97 (Owner 2026-10-12 "continua Tennis en la GEX44"; max-turns 28; it hit the limit before committing, so the
coordinator committed and re-verified).

- Step 1 PROVEN: fn_801BD194 compile_error = missing type prelude (`s32` redeclared). All 26 job-2 units failed to
  compile for that reason, so job 2's 0/26 measured no reconstruction at all. KNOWLEDGE entry written (session 2).
- Steps 2-3 PROVEN: `gex44/tennis_context.h` = M2C_TYPES prelude (ported from CP50 arm_a.py) + 13 structs, every
  member at its cited asm offset; `tennis_context.py` + `test_tennis_context.py`. m2c regenerated for the 12 W5a ids
  with `--context`: 10 lint-clean (fn_801BD194, 80203FEC, 8020711C, 8020CC14, 8022621C, 80241018, 80252F34,
  80254440, 80257978, 8025C600). EXCLUDED by source_lint UNK_FIELD: fn_8021EAA8 (->unk14), fn_8022F90C.
- Tests on the laptop, factory venv `Apps\decomp_tools\venv`: `test_tennis_context.py` TENNIS_CONTEXT_DRILL=9/9;
  `test_m2c_producer.py` M2C_DRILL=13/13. Also 9/9 on GEX44 (/opt/ksr-decomp; m2c source sha 67583db0... on both).
- Commits: wt_tennis_rf cannot commit (.ksr_vault gate); edits applied there uncommitted. Durable copy
  `patches/W11-1.patch` (GEX44 clone commit on top of tag w11-gex-base). m2c outputs + lint.json in
  `wst_tennis\w11\m2c_w11\`. GEX44 workspace: /home/kobii/missions/tennis-w11.
- Step 4 (stage.py build + certify, no send) NOT RUN: it reads laptop-only recon_factory state. It moves into W12
  step 3, which builds and certifies its own job anyway.
- K7: GEX44 worker 3,018,609 processed (stream-json usage, dedup by message.id; goal-settle). Laptop sessions:
  1,344,935 + sessions 2-3 (in the goal ledger). Goal after settle: used 40,546,283 of 55,000,000.
Next unit: the Tennis context lives in gex44/tennis_context.h; the 12 new W12 functions need their own structs there
(same citation rule) before lint. Do that part on GEX44 while the laptop is below 4 GB free.
