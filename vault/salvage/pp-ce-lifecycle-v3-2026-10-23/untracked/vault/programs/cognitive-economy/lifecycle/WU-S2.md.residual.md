# WU-S2 -- certified executable resolver + PATH-loss canary (plan v3 S2, Owner "A" 2026-10-09)

Goal ce-lifecycle-v3. cwd = this worktree. Work class: REPAIR (small).

Defect (found by WU-1H3, patched locally in `_git_ro` only): mission tooling resolves git, python and node through ambient
PATH. Under the harness PowerShell, git is not on PATH, so the fault capsule recorded an empty HEAD, commits and dirty
set, and nothing failed loudly.

Read ONLY: `grep -n "_git_ro\|shutil.which\|\"git\"\|'git'" tools/gsd_mission.py` output and the lines it names
(+-10). Do not read the rest of the file.

Budget: hard cap 8 model calls. Checkpoint-commit as soon as step 2 is green.

Steps:
1. One function `resolve_exe(name)` in tools/gsd_mission.py:
   - order: an env override (CPP_EXE_<NAME>), shutil.which, then the known Windows install paths
     (C:\Program Files\Git\cmd\git.exe; the Python312 interpreter = sys.executable for python; node via where.exe);
   - returns None only when all fail;
   - the capsule then records `"git": "UNRESOLVED"` instead of empty fields.
   Make `_git_ro` and every other git/node subprocess in that file use it.
2. tools/test_halt_continues.py (extend, do not fork):
   - V-LIFE-CAPSULE-PATH-LOSS: run the capsule writer against a temp git repo with os.environ["PATH"] = "". The capsule
     must carry the real HEAD sha, a commit list and the dirty path.
   - V-LIFE-CAPSULE-UNRESOLVED: a control where every source is unavailable; it must say UNRESOLVED, never "".
   - Mutant via tools/mutation_drill.py: resolve_exe returns shutil.which(name) only. PATH-LOSS must go red.
   - Run the whole file; baseline HALT 14/0 plus your gates.
3. Commit by pathspec with -F msgfile (tools/gsd_mission.py, tools/test_halt_continues.py, this packet).
4. WU-S2-receipt.md (<= 20 lines), Status: DONE, gates, mutant, calls. Commit.

NEVER write "needs a fresh pane" or "/kclear". End your final message with: HANDOFF NOTE: WU-S2 done


## Residual
Proposed by the steward for stopped mission m-34f33c20b40b (PROPOSAL ONLY: arming it needs the Owner/coordinator).
- Partial receipt: C:\Users\User\Apps\pp-ce-lifecycle-v3\vault\programs\cognitive-economy\lifecycle\WU-S2.md.partial.json
- RESUMPTION_FILE: C:\Users\User\Apps\pp-ce-lifecycle-v3\RESUMPTION_FILE.md
- Salvage: C:\Users\User\Apps\pp-ce-lifecycle-v3\vault\specs\salvage\m-34f33c20b40b
