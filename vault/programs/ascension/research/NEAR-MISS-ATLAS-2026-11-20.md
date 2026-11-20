# Ascension research: per-function failure atlas (measured, GEX44, 2026-11-20, pane 5a77ca0e)

Owner: "research even deeper, way deeper, atomically deeper". Backlog D43. Every number here was observed today by the
command named; nothing is projected unless labelled. Code + raw rows on GEX44 under `/home/kobii/agora/factory/research/`
(`research_atlas.py`, `nearmiss.jsonl`, `census.json`, `an_5a77.py`).

## Instrument
For a stratified random sample (seed 20261120, up to 60 per run x band; 1,200 rows), recompile the function exactly as
the sweep did (same producer module, prelude, flag arm, compiler binary), run `objdiff-cli diff --format json`, and
classify every instruction pair objdiff marks: register-only arg (REG/FREG/CR), immediate arg (IMM), relocation arg
(RELOC), branch target, opcode change (OPC), insert/delete (INSDEL); pure reordering (same multiset, other order) = SCHED.
- **Reproduction check:** recompiled match % == the sweep's stored % in 777 / 784 classified rows. The atlas sees what the
  sweep saw.
- **Defect found (matters for D43):** 416 rows (MKW 226 / 300, WSR 190 / 300) do not pair: the sweep rows point at target
  objects under mutable build dirs (`mkw-repo`, `wsr-repo`) that were rebuilt after the sweep; the target now names that
  address differently (e.g. `DirectPrint_*` where the sweep row says `fn_80024DF0`). Their stored % describes objects that
  no longer exist. **The ledger must pin each target by content hash, never by path.** WIIPARTY/TENNIS rows (600) are
  unaffected; MKW/WSR keep 184 paired rows.

## Where the bytes are (whole runs, `census.json`)
| run | NO_COMPILE | TARGET_AMBIGUOUS | 70-90% | 90-100% (not 100) | 100% |
|---|---|---|---|---|---|
| WIIPARTY vs2 | 44.9% B (1,196 fns) | - | 20.4% | 12.5% | 4.7% |
| TENNIS vs2 | 31.4% (1,624) | - | 24.1% | 20.4% | 6.2% |
| MKW base | 85.6% (5,503) | - | 4.1% | 3.5% | 2.1% |
| WSR base | 38.1% (6,102) | 24.0% (5,249) | 14.2% | 7.1% | 5.1% |
Bytes-first reading: **compile failure is the largest byte bucket in every game** (31-86%); then TARGET_AMBIGUOUS on WSR
(24%, never attempted); then the 70-90% band (14-24%). Near misses >=90% are 3.5-20% of bytes. MKW and WSR were swept
only with the base producer; vs2 (m2c --valid-syntax) cut WIIPARTY's NO_COMPILE 2,875 -> 1,196 functions.

## What a near miss actually is (pooled, 784 classified rows)
| band | n | REGALLOC_ONLY | IMM_ONLY | ARGS_MIXED | INSDEL | OPC | OPC+INSDEL |
|---|---|---|---|---|---|---|---|
| 99-100 | 152 | **74%** | 15% | 6% | 1% | 0% | 0% |
| 95-99 | 157 | 39% | 1% | 6% | 33% | 8% | 12% |
| 90-95 | 163 | 0% | 0% | 0% | 44% | 7% | 47% |
| 70-90 | 155 | 0% | 0% | 0% | 22% | 2% | 75% |
| 50-70 | 157 | 0% | 0% | 0% | 16% | 0% | 83% |
- Above 99%: almost all register allocation (the classic decomp-permuter target) or one immediate. Below 95%: never
  register-only; structure differs (instructions added/removed, opcodes changed).
- INSDEL length deltas (>=90): mostly 0 / +-1 / -2 instructions: a missing or extra temporary, cast, or copy.
- Median size: REGALLOC_ONLY 76 B, IMM_ONLY 60 B, INSDEL 112 B, OPC+INSDEL 220 B: the bigger the function, the more
  structural the miss.
- Diff kinds at >=90 (counts of instruction args/lines): REG 3,272, INSDEL 726, IMM 594, OPC 280, FREG 87, BRANCH 39,
  RELOC 7. Relocations are essentially never the problem.

## Named, operator-sized patterns (opcode substitutions at >=90, target -> ours)
| pattern | count | probable source cause | deterministic operator |
|---|---|---|---|
| stack-offset immediates (`x(r1)`) | 188 | different locals / frame size (temporaries, local types) | local-variable count/type search |
| `addi->stmw`, `addi->lmw` | 18 + 13 | save/restore form: `-use_lmw_stmw` arm mismatch per function | add a third flag arm (lmw off) |
| `addi<->li`, `addi->mr` | 34 + 16 + 14 | constant/copy materialisation: expression shape, `x = 0` vs `x = y - y`, pointer arith | expression rewrite set |
| `stb->stw`, `stw->sth`, `lhz<->lha`, `lwz<->lhz` | 16 + 3 + 5 + 3 + 3 | wrong field width/signedness from m2c type guesses | type-width search on loads/stores |
| `bne<->beq`, `b<->cmpwi` | 11 + 5 + 9 + 8 | if/else polarity, loop form (while vs do/for) | branch-polarity / loop-shape rewrites |
| `subic->neg`, `subfe->or` | 6 + 6 | boolean idioms (`!x`, `x != 0`, `(x|y) != 0`) | boolean-idiom rewrites |
| `clrlwi<->clrrwi` | 3 + 3 | mask/shift expression form | mask rewrites |

## Consequences for D43 (ranked by bytes, measured basis named)
1. **Run vs2 full on MKW, MKWLIB, WSR** (compile repair already measured: WIIPARTY NO_COMPILE -58%; MKW pilot compiles
   99 -> 241 of 400). Largest bucket, 0 tokens, existing code.
2. **Address-keyed targets on WSR** (24% of its bytes, never attempted).
3. **Third flag arm** for the lmw/stmw save-restore mismatch (31 occurrences in the sample at >=90).
4. **Permuter on the >=99 band** (74% register-only). Pilot: `research_perm_pilot.py` (section below).
5. **Deterministic rewrite operators** for the named patterns (types, boolean idioms, branch polarity, locals): they
   address the 90-99 band where INSDEL/OPC dominate and the permuter's random search is weakest.
6. **The 70-90 band and NO_COMPILE remainder are structural** (OPC+INSDEL 75-83%): types/headers from donors and model
   work belong there, with the function's ledger history.
7. **Ledger rule from the defect above:** pin targets by content hash.
