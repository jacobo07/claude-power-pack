# WU-1H3 -- finish WU-1H (third epoch of L1; closeout only, the code is already written)

Plan: as WU-1H.md / WU-1H2.md (Amendment D L1). Goal ce-lifecycle-v2. cwd = this worktree.
State at arm (coordinator 3339c6c2, 2026-10-08 ~20:55): WU-1H2 (m-6ffa7ac2513b) halted on its breaker at 755K with
the code UNCOMMITTED in tools/gsd_mission.py and the new tools/test_halt_continues.py. Its exact remaining steps are in
vault/plans/ce-lifecycle-WU-1H2-progress-2026-10-08.md. Read ONLY that note. Do NOT read or re-survey
tools/gsd_mission.py beyond the single line a failing test points at.

Budget (measured: WU-1H 926K/0 code, WU-1H2 755K/18 calls ~42K per call): hard cap 10 model calls. One command per
call; every suite run logs to _logs/wu1h3/ and you read only its summary line.

Steps (from the note, in order):
1. Fix the test path: `Path(TMP) / "fault-capsules"` and `Path(TMP, "fault-capsules", ...` ->
   `gm.lr.state_dir() / "fault-capsules"` in tools/test_halt_continues.py (one Edit, replace_all if needed). Run it.
2. The three mutants from the note via tools/mutation_drill.py; each named gate must go red.
3. Four suites in ONE PowerShell call (test_halt_continues, test_gsd_mission, test_process_lifecycle,
   test_goal_spend or the suite WU-1B used).
4. Commit by pathspec with -F msgfile: tools/gsd_mission.py, tools/test_halt_continues.py, the WU-1H2 progress note,
   this packet. Verify `git log -1 --format=%s`.
5. Replace WU-1H-receipt.md (<= 40 lines): gates, mutants, commits, calls per epoch (1H, 1H2, 1H3), deploy recipe as
   sha256 hashes for WU-INST (no deploy, HR-001). Addendum B: "second format, mission-level". Commit.
6. `mission_spend.py goal-status --goal ce-lifecycle-v2`; if remaining - open >= 1,100,000 arm WU-ADV with the new
   `gsd_mission.py arm-chain` (--parallel-unit lc-WU-ADV, --wu-packet <abs WU-ADV.md>, --token-estimate 800000,
   --route <abs route-WU-ADV.json>); else write WAITING_FOR_AUTHORITY in the receipt.

If any step cannot finish inside the cap: commit what is green, update the receipt with the exact next step, end with
HANDOFF NOTE. NEVER write "needs a fresh pane" or "/kclear".

End your final message with: HANDOFF NOTE: WU-1H done
