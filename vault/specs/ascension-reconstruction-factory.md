---
covers: [ascension, factory, m2c, objdiff, mkw, wsr, ksr, fifa, wiiparty, tennis, materialize]
status: F1 measured, F2-F4 open
owner_go: "go ahead with everything" (Owner, 2026-11-19, pane 81dcf473)
---
# Ascension reconstruction factory (deterministic, no model call)

## Why
Measured 2026-11-19: Ascension LLM generations certify ~2 functions per 1M processed tokens. KSR's 8,687 certificates
came from a deterministic pipeline instead (decomp_work/b8d1db7edd42: Ghidra bounds -> m2c lift of every function ->
mwcceppc under wibo, per-object flag arm -> byte identity), 25% of all functions in 710 s. It had run on ONE binary.

## F1: generalised runner (DONE, measured)
`/home/kobii/agora/factory/factory.py` (laptop copy: pane 81dcf473 scratchpad). Reuses read-only: the pinned m2c
producer + venv (/opt/ksr-decomp), t1-campaign `repair.transform_v5` + `toolchain_sd.retype`, `cv1.objdiff_pct`, KSR
wibo/objdiff. Per dtk-template repo: corpus from symbols.txt -> m2c over dtk asm -> 2 flag arms -> objdiff vs the
function's own dtk target object -> one arm per object (KSR rule; FLAGS_SPLIT certifies nothing).
Output: <out>/{corpus.jsonl, m2c/, sweep.jsonl, matched.tsv, summary.json}. A row in matched.tsv is PROVISIONAL_MATCH.

Measured (GEX44, nice 10):
| run | functions | L1 | compile | 100% object-consistent | >=90% near | new vs lane reports | wall |
|---|---|---|---|---|---|---|---|
| mkw-main-pilot400 | 400 | 366 | 103 | 49 | 17 | - | 29 s |
| mkw-main-full | 9,086 | 8,222 | 2,719 | 1,213 | 451 | 1,111 new (592 >8 B, 36,692 B) | 10 min |
| mkw-staticr-full | 17,232 | 16,003 | 7,228 | 4,078 | 1,299 | 2,989 new (1,278 >8 B, 96,152 B) | 10.5 min |
| wsr-main-full (Wii/1.0) | 34,148 | 30,375 | 19,023 | 8,647 | 2,463 | 8,586 new (3,851 >8 B, 232,104 B) | 39 min |

Totals 2026-11-19: 12,686 new PROVISIONAL_MATCH (MKW 4,100 vs its report's 3,922; WSR 8,586 vs its report's 136),
0 model tokens, ~1 h CPU at nice 10. Not yet counted by any report (F2). TARGET_AMBIGUOUS (WSR 5,249, StaticR 1,550)
= a name in more than one target object; recoverable by keying the target on address instead of name.

Largest loss: L1 -> compile (8,222 -> 2,719 on MKW). Next yield lever = compile repair (types/headers, C++ this-calls),
not more search.

## F2: materialize into the product tree (MKW, MKWLIB, WSR DONE 2026-11-19)
Route used: `factory/carve.py` = one unit per function for matches in dtk `auto_*` objects (the MKW lane's own
`auto_tu` shape), `Object(NonMatching, "factory/<sym>.c", cflags=[chosen arm])`, split = the function's exact .text
range. `factory/materialize.py` (greedy multi-function unit with per-step byte check) stays for named units (not run).
MKW result (lane/mkw 8234f1c, fast-forwarded while the lane was PARKED, rebuilt in the lane): report.json matched
3,922 -> 7,723 (+3,801; 1,044 main + 2,739 StaticR carved), matched code 7.36% -> 9.43%, 0 functions lost by
unit::name, main.dol OK, StaticR.rel OK, no split unit removed or changed (255 -> 1,319 and 2,034 -> 4,773 units).
total_functions 26,639 -> 27,057: carving auto objects changes objdiff's enumeration; use matched code % for trend.
Autopilot MATCH snapshot match/MKW.json advanced 3,904 -> 7,723 under cron.lock (ledger kind `factory_match`, 0
tokens), so no generation is credited for factory work; side effect: S204M's 18 pending functions are in it too.
MKWLIB (mkw-lib cb3faf0, same binary as MKW): report 2,043 -> 7,408 (5.96% -> 8.96%), 0 lost, main.dol OK, StaticR.rel
OK; snapshot match/MKWLIB.json 2,019 -> 7,408. WSR (wsr-decomp 1f4f821): report 136 -> 8,722 (code 3.64%), 0 lost,
main.dol OK; snapshot match/WSR.json -> 8,722.

### Lane merge KSR -> WSR (DONE 2026-11-19, `factory/port_ksr.py`)
KSR (t1-campaign) and WSR target the same main.dol (sha1 7752caae). port_ksr.py takes each KSR certificate WSR lacks,
recompiles it against WSR's own target object and admits it only at objdiff 100%: 645 candidates -> 535 MATCH, 96
NO_COMPILE, 14 NO_MATCH (those 110 stay counted in KSR only). Scratch first (8,722 -> 9,257, code 3.88%, 0 lost,
main.dol OK), then lane commit 483a94f, lane rebuild main.dol OK, report 9,257, snapshot match/WSR.json 8,722 -> 9,257
(backup `WSR.json.bak-81dc-port-20261119T192111Z`; checked: snapshot == lane report set, 0 lost vs backup).
Autopilot lanes 8 -> 5 (Owner "go ahead to both", 2026-11-19): KSR, MKWLIB, FIFATC set `status PARKED,
park_kind merged, merged_into WSR/MKW/FIFA` under cron.lock (state.json CAS e6bc2729, backup
`state.json.bak-8949-merge-20261119T220016Z`, ledger kind `owner_park`). No worker was alive in any of the three; their
missions were left as they were. `park_kind merged` is never auto-lifted (only `budget` is). Undo = restore the backup.

### Original F2 plan
Goal: each PROVISIONAL_MATCH counted by the lane's own `ninja build/<GAME>/report.json` (the autopilot MATCH class).
- Per target object with >=1 match: one source file holding its matched functions (prelude + transformed lift), compiled
  with that object's chosen arm; unit declared in configure.py as `Object(NonMatching, ...)` with those cflags and the
  game's mw_version; the split entry must exist in splits.txt (auto_* objects need a named split first).
- Done-gate: ninja report.json before/after; matched_functions rises by the materialized count and no previously
  matched function is lost; `main.dol: OK` still builds where the lane builds; a planted wrong source is refused.
- Ownership: a lane's product repo is written only between generations (lane PARKED or under a hold), in its own commit,
  never while its worker runs (concurrent-writers rule).

## F3: the other binaries (OPEN)
FIFA/FIFATC (b8637681, RSO, 24,482 named fns), WIIPARTY (f8f46694, monolithic DOL, no symbols), TENNIS
(SportsPackEP.dol) have no dtk-template build. Each needs a dtk split (config.yml + symbols/splits; Ghidra bounds via
ExportL1.java where no symbols exist) before F1 runs. MKWLIB = MKW binary: share MKW's run, do not run twice.

## F4: cross-lane index (OPEN)
One certified-source pool per binary (KSR+WSR, MKW+MKWLIB, FIFA+FIFATC) and a masked-byte index across binaries
(SDK/NW4R/EGG), consulted by the planner before any generation; the model works only on the residual (LF1 near misses).

## Rollback
F1 writes only under /home/kobii/agora/factory/. Delete the run dir to undo. F2 commits are per-lane and revertible.
