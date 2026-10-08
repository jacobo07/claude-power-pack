# WU-INST -- certified install of approved hashes into the live checkout (Amendment D L5, ex a3b-r R3)

Plan: ce-a3 Amendment D (pp-ce-a3 3aa002af, Owner "y" ~18:05) L5 + section 5. Goal ce-lifecycle-v2. cwd = this worktree.
Precondition: WU-1D-receipt.md (or WU-1-receipt.md) says done.
LIVE = C:\Users\User\.claude\skills\claude-power-pack (the dispatcher loads hooks from here; supervise runs its tools).
LIVE is shared by many panes: never checkout/reset/stash/rebase there; pathspec commits only; re-read before write.

Approved install set (section 5; nothing else): GOAL_STATE R1b (ce/a3b-r d0d0eb2b), WU-1B binding (b62f9019),
L1 WU-1H and L2 WU-ADV gsd_mission/route_admission changes, L6 when its receipt exists. A file that also carries an
unnamed change (e.g. WU-1C roots or WU-1D arm --goal) is installed only if `<state>/approvals/` holds a consumed-or-
open approval record naming that file's blob hash; otherwise leave that file out and write ONE line to
vault/OWNER_QUEUE.md: "YES to install <file> blob <hash> (WU-1C/1D)". Never a command for the Owner to type.

Budget: 20 calls per epoch, max 2 epochs (0.8M). CHECKPOINT FIRST: commit a stub receipt. Logs under _logs/wuinst/.

Steps:
1. Integrate R1b here first: `git cherry-pick -x d0d0eb2b`. On conflict in session_budget_guard.js / mission_spend.py
   resolve by keeping BOTH behaviours (R1b authorization + WU-1B prospective binding), then run test_goal_budget_admission,
   test_process_lifecycle, test_hook_boundary, test_gsd_mission. Red -> abort the cherry-pick, record, stop (BLOCKED).
2. For each install file F: base = `git merge-base <LIVE HEAD> HEAD` version; ours = LIVE HEAD version; theirs = this
   HEAD. Refuse if LIVE has F dirty. `git merge-file -p ours base theirs` into _logs/wuinst/staged/F. Any conflict
   marker -> BLOCKED with the hunk; never hand-resolve guard code in LIVE. Expected: LIVE carries 6 guard commits
   (31f1e714..ffd8f9e9) absent here; they must survive.
3. Staging proof: `git -C LIVE worktree add <tmp> HEAD --detach`, copy staged files in, run the four suites there.
   Record PASS lines. Then `git -C LIVE worktree remove <tmp>`.
4. Install: immediately before each write re-hash LIVE's F; if it moved since step 2, redo step 2 for F. Copy staged F
   into LIVE, `node --check` the js files, commit in LIVE by pathspec (-F msgfile, verify git log -1), run the four
   suites in LIVE. Any red -> `git -C LIVE revert --no-edit <commit>` and BLOCKED.
5. If a write into LIVE is denied by permissions (HR-001 / auto-mode self-modification), do NOT retry another way:
   status WAITING_FOR_OWNER_ACTIVATION, staged files + hashes in the receipt, one line in vault/OWNER_QUEUE.md asking
   for a YES bound to those hashes. Continue to step 7.
6. Drift check: every installed F's blob in LIVE equals the staged blob; live guard reads a spec file while a protected
   write is still denied (Amendment D done-gate). Append a `reclassify`-equivalent ledger correction ONLY if WU-1B's
   prebind op exists in LIVE: goal-prebind for sid fc54a743 on ce-lifecycle-v (6,855,731), consume-once by source.
7. WU-INST-receipt.md (<= 50 lines): files, base/ours/theirs/installed hashes, suites, LIVE commit, rollback
   (`git -C LIVE revert <commit>` or CPP_PROSPECTIVE_BIND=0 / CPP_SWEEP_ADVANCE=off). Commit here by pathspec.
8. Arm WU-TRIP unless a live/PREPARED mission holds it, if remaining - open >= 1,000,000 (atomic arm, lc-WU-TRIP,
   --token-estimate 700000). Never hand the arm to a pane.

End your final message with: HANDOFF NOTE: WU-INST done
