# WU-R6 receipt
Status: DONE

Finished by the coordinator pane, with zero model calls in the tooling, after residual m-677180af82ec stopped PARTIAL (residual_exhausted). The Owner approved this on 2026-10-11 ("y").
Commit: 12bd486 on the worktree branch `cp50-c2` in C:\Users\User\Apps\recon_work\wt_cp50_c2. It is not on feature/knowledge-acquisition and was not pushed.

## Built
- `tools/wros/binary/decomp/dossier.py` builds one dossier per draw 1-5 function. Each dossier holds:
  - the instructions
  - m2c output (rc 0 for all 5)
  - callers and callees from the asm
  - SDA/data refs
  - donors with the same shape
  - the Ghidra decompile, plus its callers/callees/data refs
- Cache: `vault/cache/dossier/<sha256(main.dol)>/<ADDR>.json`, keyed by binary sha256 855e4ffe4f8d69d172c44b05ec3a4ddb89645bebfadca41c98effab69111d448 + function address. The file asserts model_calls == 0.
- `ghidra_scripts/DossierDump.java` is the headless post-script. Newline and tab escaping was fixed so its JSON parses.
- Ghidra fix. Root cause of the attempt-2 stall: a fresh headless `-import` of main.dol hangs. Each run now copies `decomp_factory/ghidra_stock`, where main.dol is already imported, and opens it with `-process main.dol -readOnly -noanalysis` and stdin set to DEVNULL. The original project is never opened, because it holds a stale lock. If Ghidra fails, the field records `absent: <reason>` and the other fields still cache.

## Measured (vault/cache/run1_build.*, run2_drill.*)
- Run 1 (build): misses 5, 67.9 s, Ghidra decompile OK on 5/5 (FUN_80426354, FUN_804263a4, FUN_8042a4d0, FUN_8044064c, FUN_8044d4a8).
- Run 2 (cache-hit drill): hits 5, misses 0, recomputed=false, 0.0 s, model_calls 0.

| function | bytes | asm callers | callees | SDA/data refs | donors |
|---|---|---|---|---|---|
| main:80426354 | 2,511 | 0 | 1 | 0 | 0 |
| main:8044D4A8 | 3,096 | 0 | 2 | 2 | 4 |
| main:804263A4 | 2,839 | 0 | 1 | 1 | 0 |
| main:8044064C | 4,304 | 2 | 2 | 0 | 0 |
| main:8042A4D0 | 5,160 | 0 | 5 | 6 | 0 |

## Limits (stated, not hidden)
- 4 of 5 functions have no direct `bl` caller. They are reached through vtables; 80426354 itself dispatches via `*param_1 + 0xc4`. Caller evidence for them is therefore empty by construction, not missing.
- Ghidra references come from a project opened with `-noanalysis`, so they are only as complete as the stock import. The asm-derived callers and xrefs are the primary evidence.

## K7
| estimate | actual processed tokens (goal ledger) |
|---|---|
| route-S 1.6M, then residual route-M 3.5M | attempt 1 m-9165195743d2: 688,185. Attempt 2 m-677180af82ec: 971,168 (goal total_used 13,843,967 -> 14,815,135). R6 total 1,659,353 across 2 sessions. |

The coordinator-pane finish is not bound to goal cp50-c2 and is not in this figure. The attempt-2 worker's own receipt claimed about 55K, a self-report the ledger refutes.
