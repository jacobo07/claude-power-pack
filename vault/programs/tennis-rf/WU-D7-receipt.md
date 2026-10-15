# WU-D7 receipt -- Ph7 incremental recompile

Status: DONE. `test_d7.py` EXIT=0 (8/8 PASS: V-D7-REPRO, REPRO-SHA, SOUND, CTRL-UNUSED, CTRL-WIDE, CTRL-D6, DET, SMALLER).
Evidence: `evidence/d28/d7/` (replay.json, controls.json, full_runs.json, run.log, dirty.py, d7.py, test_d7.py).
Run on GEX44 `/home/kobii/missions/tennis-w11/out/d28/{tools,d7}`.

## Result
- Reproduction: incremental (m2c + lint on dirty closure only) reproduces D6's whole-corpus lint-clean set for all 5 variants, diff empty, output sha equal to whole-corpus run (D5_void_void sha c963b7c4...ca37).
- Closure size 44 of 1,797 (2.4%) for each D6 delta (seed 44, one level).
- Wall time: incremental 1.37-1.75 s vs whole-corpus 8.05-9.20 s (~5-6x faster).
- Direct vs transitive unlock (D6 facts): D5_void_void direct 3 (fn_80242AC8, fn_80242CAC, fn_80242E24), transitive 0 (wave2 dependents empty). The 4 fixed/variadic variants: 0 unlocks direct and transitive.
- Closure deterministic across runs.

## Controls
- Unused fact (`zz_d7_unused_fact`): closure empty (0).
- Wide struct (`Ptmf8021F3E4`, f_00 s32->u32): closure 7 = full set of changed functions; clean set equal, sha equal, nothing changed outside closure.
- D6 control: closure contains every function D6 saw change; missing = [].

## Defect found and fixed
First pass: fixed/variadic variants gave closure 1489 because `arg0..arg4` parameter names were counted as facts. `dirty.py` now ignores `argN`/`aN`/`var_*` ids; test_d7 asserts closure <= 100. Note: the earlier fix had not actually reached GEX44 (md5 mismatch); re-uploaded and rerun.

## Plan delta
MDG 13: incremental recompile is viable. Dirty closure by fact id is ~2% of corpus and sound on the tested deltas. Caveat: closure is an over-approximation and was validated on 5 D6 deltas + 2 synthetic controls only; the id filter is name-pattern based, so non-conventional param names would inflate the closure (safe direction).
