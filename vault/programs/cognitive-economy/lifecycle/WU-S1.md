# WU-S1 -- staged 3-way merge of the lifecycle install set onto LIVE HEAD (plan v3 S1, Owner "A" 2026-10-09)

Goal ce-lifecycle-v3. cwd = this worktree (C:\Users\User\Apps\pp-ce-lifecycle-v3, branch ce/lifecycle-v3).
Work class: CONTROL_PLANE/merge. You do NOT write to the live checkout; the coordinator applies your patch by index.

Inputs (measured by the coordinator):
- LIVE = C:\Users\User\.claude\skills\claude-power-pack, HEAD 41ed853b (branch feature/knowledge-acquisition).
- merge-base(LIVE HEAD, ce/lifecycle-v3) = 86ad6f16.
- Install set (5 files): hooks/lib/goal_binding.js (new), hooks/session_budget_guard.js, modules/provider_routing/ledger.py,
  tools/gsd_mission.py, tools/mission_spend.py. Tests that pin them: tools/test_process_lifecycle.py,
  tools/test_halt_continues.py (bring both too).
- LIVE has a foreign UNCOMMITTED change in tools/gsd_mission.py and tools/route_admission.py (cost-collapse E4a).
  Merge against LIVE HEAD (committed blobs), never against the LIVE working files.

Budget: hard cap 8 model calls (measured: ~18K floor + ~15K growth per call). One command per call. Never read whole
source files; let `git merge-file` find conflicts and read only conflict hunks.

Steps:
1. One PowerShell call: `git -C <LIVE> worktree add --detach C:\Users\User\Apps\pp-live-stage 41ed853b`; then for each
   install-set file run `git merge-file -p <stage file> <base blob 86ad6f16> <v3 blob>` into the stage (new file: copy);
   print per-file conflict counts. Copy the two test files from v3.
2. Resolve only conflict hunks, if any (read the hunk, not the file).
3. One call: node --check on the two .js, python -m py_compile on the three .py, then in the stage (Start-Process
   -WorkingDirectory, never cd) run test_process_lifecycle, test_halt_continues, test_gsd_mission,
   test_gsd_mission_admission; logs to _logs/wus1/ in THIS worktree; print summary lines only.
   Baselines: LIFE 5/1 (V-LIFE-PREMODEL-TRANSPORT pre-existing), MC 224/225, ADM 43/43, HALT 14/0.
4. `git -C <stage> diff 41ed853b --binary -- <install set + 2 tests>` > vault/programs/cognitive-economy/lifecycle/
   install/L1-install.patch; record sha256 of the patch and of each staged file in WU-S1-receipt.md (<= 30 lines,
   Status: DONE or Status: PARTIAL with the exact next step). Commit both by pathspec with -F msgfile in THIS worktree.
5. Stop. Do not remove the stage worktree; the coordinator applies and removes it.

If a suite regresses against its baseline: commit the receipt with Status: PARTIAL and the failing gate name; stop.
NEVER write "needs a fresh pane" or "/kclear". End your final message with: HANDOFF NOTE: WU-S1 done
