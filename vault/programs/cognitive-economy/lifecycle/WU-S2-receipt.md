# WU-S2 receipt
Status: DONE
- tools/gsd_mission.py: resolve_exe(name) (CPP_EXE_<NAME> > shutil.which > known Windows paths / sys.executable / where.exe node; None only if all fail). `_git_ro` and the 5 other git call sites use it. Capsule records "git": "UNRESOLVED" (head/commits/dirty = "UNRESOLVED") instead of empty fields.
- tools/test_halt_continues.py extended: HALT_CONTINUES_PASS=16 FAIL=0 (baseline 14/0 + 2).
- V-LIFE-CAPSULE-PATH-LOSS PASS (PATH="": real 40-char HEAD, commit list, dirty path).
- V-LIFE-CAPSULE-UNRESOLVED PASS (all sources unavailable -> UNRESOLVED, never "").
- Mutant (resolve_exe = shutil.which only) via tools/mutation_drill.py: KILLED on V-LIFE-CAPSULE-PATH-LOSS.
- Model calls: ~8.
