# WU-1H3 progress (session breaker tripped at ~523K > stop 500K)

Done (uncommitted in worktree):
- tools/test_halt_continues.py: capsule path -> gm.lr.state_dir(); epoch expectation e1 -> e2 (capsule is written after the stop bumps the epoch).
- tools/gsd_mission.py `_git_ro`: resolves git via shutil.which / C:\Program Files\Git\cmd\git.exe (git is not on PATH in this shell; capsule head/commits/dirty were empty).
- test_halt_continues: HALT_CONTINUES_PASS=10 FAIL=0 (_logs/wu1h3/t3.log).

In flight: 3 mutants via tools/mutation_drill.py, specs _logs/wu1h3/spec{1,2,3}.json, logs _logs/wu1h3/mut{1,2,3}.log
(background task bjbf6s6m3). Read the last lines of each mut log; each must say KILLED.

Next exact actions: 1) read mut logs; if any is HARNESS (CRLF anchor), fix the anchor and rerun; 2) four suites in one
PowerShell call into _logs/wu1h3/; 3) commit by pathspec with -F msgfile (gsd_mission.py, test_halt_continues.py, WU-1H2 note,
this note, WU-1H3.md); 4) replace WU-1H-receipt.md (<=40 lines, deploy hashes, B = second format, mission-level);
5) goal-status ce-lifecycle-v2 and arm-chain WU-ADV if remaining-open >= 1,100,000 else WAITING_FOR_AUTHORITY.

HANDOFF NOTE: WU-1H not done -- breaker stop; test green, mutants in flight, remaining steps above
