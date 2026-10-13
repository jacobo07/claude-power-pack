# W12 prep ready (GEX44 plane, 2026-10-12)

Producer: GEX44 headless worker 8ed00572 (26 turns, 2,503,357 processed, settled into goal tennis-rf).
Receipt: `evidence/w12/W12-prep-receipt.md`. Per-function prep records: `evidence/w12/records.jsonl`.

- Patch: `patches/W12-prep-1.patch` (on top of `patches/W11-1.patch`). BOTH are already applied, uncommitted, in
  `C:\Users\User\Apps\recon_work\wt_tennis_rf` (tennis_context.h/.py, test_tennis_context.py, m2c_producer.py,
  test_m2c_producer.py). Verified on the laptop: TENNIS_CONTEXT_DRILL=9/9 (laptop factory venv).
- m2c + lint for all 24: `C:\Users\User\Apps\recon_work\wst_tennis\w12\m2c\` (lint.json, results.tsv, c\).
- INCLUDED, 22 lint-clean: the 10 W11-clean + 12 new (fn_80278FEC and fn_803315A0 closed by det type repair;
  the other 10 by context work, PoMN per row).
- EXCLUDED, UNK_FIELD: fn_8021EAA8 (->unk14), fn_8022F90C (.unk2A).
- Hazards the lint cannot see (lint-clean, still sent; the oracle judges them): fn_8021F8BC `var_r31 += 4` on a
  struct pointer; fn_8021F3E4 ptmf call drops the r12 element.
