# WU-INST2 -- staged 3-way merge of S2+S3+S4+S5 onto LIVE HEAD (same recipe as WU-S1, which worked first time)

Goal ce-lifecycle-v3. cwd = this worktree. Work class: CONTROL_PLANE/merge. You do NOT write to the live checkout.

Inputs:
- LIVE = C:\Users\User\.claude\skills\claude-power-pack. Read its HEAD with `git -C <LIVE> rev-parse HEAD`.
  L1 is installed there as 3f9b57cc.
- BASE = this branch at 8e2ef3a8: the state that L1 merged into live.
- THEIRS = this branch HEAD.
- Install set = `git diff --name-only 8e2ef3a8 HEAD -- hooks tools modules vault/config`. Exclude tools/lifecycle_install_apply.ps1
  (coordinator-only) and any _logs path.
- LIVE has foreign UNCOMMITTED edits (cost-collapse E4a) in tools/gsd_mission.py and tools/route_admission.py.
  Merge against LIVE HEAD blobs, never the LIVE working files.

Budget: about 14 physical calls. Read only conflict hunks.

Steps (WU-S1 receipt shows the shape; LF blobs, not CRLF checkouts):
1. `git -C <LIVE> worktree add --detach C:\Users\User\Apps\pp-live-stage2 <LIVE HEAD>`.
   - Files existing in all three: `git merge-file -p <stage> <BASE blob> <THEIRS blob>` (write the LF blobs to temp files).
   - Files new in THEIRS: copy them.
   - Print per-file conflict counts.
2. Resolve conflict hunks only.
3. node --check on the .js files and py_compile on the .py files. Then run, in the stage via Start-Process
   -WorkingDirectory (never cd), with logs in _logs/inst2/:
   - test_process_lifecycle, test_halt_continues, test_gsd_mission, test_gsd_mission_admission;
   - test_session_budget_guard, test_route_estimator, test_mission_steward.
   Baselines: the latest receipts (MC 226/227 pre-existing FAIL).
4. Diff the stage against the LIVE HEAD for the install set: `git -C <stage> diff <LIVE HEAD> --binary -- <set>`
   -> vault/programs/cognitive-economy/lifecycle/install/L3-econ.patch. Write WU-INST2-receipt.md (<= 25 lines):
   LIVE HEAD used, sha256 of the patch, suites. Commit both by pathspec with -F.
5. Stop. Leave the stage in place; the coordinator applies the patch with tools/lifecycle_install_apply.ps1 and removes it.

NEVER write "needs a fresh pane" or "/kclear". End your final message with: HANDOFF NOTE: WU-INST2 done
