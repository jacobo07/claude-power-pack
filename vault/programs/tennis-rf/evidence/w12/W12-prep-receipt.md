# W12-prep receipt
Status: DONE
- First pass, W11 header, all 12 new: 2 clean (fn_80278FEC, fn_803315A0 -> det type repair), 10 dirty (UNK_FIELD, 4 also `?`).
- Context work, 10 -> CLEAN: fn_80203E40 8032CF78 80230ABC 8027A154 802128D4 8021F8BC 80230BF8 80279E44 8021F3E4 80253348
  (22 new cited structs; 54 members match m2c layout; PoMN per row in records.jsonl).
- All 24 regenerated (out/w12/m2c, lint.json): 22 CLEAN. EXCLUDED UNK_FIELD as in W11: fn_8021EAA8 (->unk14), fn_8022F90C (.unk2A).
  The 10 W11-clean outputs are byte-identical (c_sha256 unchanged): no regression.
- Lint cannot see these semantic hazards (lint-clean, flagged in records): fn_8021F8BC `var_r31 += 4` on a struct pointer (asm stride 4);
  fn_8021F3E4 ptmf call drops the r12 element (m2c does not model r12).
- Test: `cd wt/tools/wros/binary/decomp && KSR_DECOMP_TOOLS=/opt/ksr-decomp /opt/ksr-decomp/venv/bin/python gex44/test_tennis_context.py`
  -> TENNIS_CONTEXT_DRILL=9/9 (V-TCTX-W12-DECLARED 24/24; red check: dropping a prototype makes it missing). test_m2c_producer.py not run (needs laptop corpus path).
- Commit 2ab62e70ec6b24856016762a8c990291e142035b in M/wt (pathspec: tennis_context.h, test_tennis_context.py); patch out/w12/patches/0001-*.patch.
