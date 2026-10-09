# WU-S5 -- adopt the gsdx S1 mission steward: settle-on-terminal + mission-scoped capsule (plan v3 S5 + B1, Owner "A")

Goal ce-lifecycle-v3. cwd = this worktree. Work class: INTEGRATION (adopt existing code, no new design).

Why (measured by the coordinator, journal goal-budget/ce-lifecycle-v3):
- Terminal workers keep their last lease open. S1 has 159,220 open, S3 237,665, and S3b 750,000; the ledger says
  remaining 1.43M while real remaining is about 2.7M.
- S3b's real 236K was settled as measured=0.
- The halt_continue fault capsule lists the whole branch history as DONE (it should list commits since mission start).

The fix exists, uncommitted, in the gsdx-factory program (unit WU-S1, halted, 18/18 reported). A byte snapshot is in
salvage/gsdx-S1-steward/:
- steward-core.patch: ledger.py, gsd_mission.py, mission_spend.py; base = BASE.txt.
- mission_steward.py.
- test_mission_steward.py.
Ownership (plan b5f441b6): the steward owns STOPPED-worker settle, fallback receipt, salvage, residual and successor
arm; halt_continue (WU-1H) owns HALTED renew. Keep exactly one owner per transition.

Read ONLY:
- the snapshot files;
- in tools/gsd_mission.py, the halt_continue block (grep -n "def halt_continue\|def write_fault_capsule\|def supervise")
  +-30 lines.

Budget: <= 7 steps (about 17 physical calls). Commit as soon as step 3 is green.

Steps:
1. Copy mission_steward.py and its test into tools/. Apply steward-core.patch with `git apply --3way`; resolve only the
   conflict hunks. Run test_mission_steward.py (expect 18/18 or say which differ).
2. One owner per transition:
   - If the steward also renews a HALTED mission, disable that path in favour of halt_continue, or the reverse.
     Choose the path with the stronger tests and state why in one line.
   - write_fault_capsule's DONE list must use the steward's commits-since-mission-start (_git_log(tree, since=created_at)).
3. Wire steward_pass into the sweep path that supervise() runs (kill switch the steward's own _off()). Gates:
   - extend test_halt_continues.py: V-LIFE-CAPSULE-MISSION-SCOPED (the capsule lists only post-start commits);
   - V-LIFE-SETTLE-ON-TERMINAL (a COMPLETED mission's open lease is closed with the transcript-measured tokens;
     a missing transcript stays held as UNKNOWN).
   Mutants: drop the since filter; drop the lease close. Run test_halt_continues, test_mission_steward,
   test_gsd_mission (226/227 baseline), test_gsd_mission_admission (43/43).
4. Dry run against LIVE state: `python tools/mission_steward.py --dry-run` (or the steward's equivalent). It must
   propose closing the leases of sids 12fc875e, d3d5b84a and 84955c89 on goal ce-lifecycle-v3. Paste the 3 lines.
5. Install patch: `git diff --binary af86e3dc -- <changed files>` -> install/L3-steward.patch + sha256.
   Write WU-S5-receipt.md (<= 25 lines). Commit. No deploy: the coordinator installs it.
6. Write one line to C:\Users\User\Apps\pp-gsdx-factory-2\vault\STEWARD-ADOPTED.md saying the steward was adopted
   by ce-lifecycle-v3 at <commit> and that WU-S1 there must not be re-run. This is the only write outside this worktree.

NEVER write "needs a fresh pane" or "/kclear". End your final message with: HANDOFF NOTE: WU-S5 done
