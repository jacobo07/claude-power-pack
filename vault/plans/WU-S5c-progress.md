# WU-S5c progress -- Status: PARTIAL

The session budget breaker tripped at 798,699 against stop 760,000. All edits are in the tree, NOT run and NOT committed.

Edits made (uncommitted):
- tools/gsd_mission.py
  - F5: halt_continue now sets row["renewal"] on every early exit (off / no packet / receipt present). The body moved to `_halt_continue_body`, wrapped in try/except that records "not renewed: halt-continue raised ...".
  - F1: in slim_finished, a clean finish with no receipt sets stopped="no receipt" -> HALTED -> halt_continue. The RECOVERY_PENDING branch is removed.
  - F4: write_fault_capsule takes its commit list from mission_steward._git_log(wd, rec["created_at"]). Without created_at it falls back to the last 20 commits.
- hooks/session_budget_guard.js (F3): CLOSEOUT_PATH now admits `*-receipt.md`. judge() already runs through closeout() at line 435; the real fault was that the receipt path was not eligible.
- tools/test_halt_continues.py
  - Renamed V-LIFE-SUCCESS-NO-RECEIPT to V-LIFE-SUCCESS-NO-RECEIPT-NOT-COMPLETED (expects HALTED).
  - Added V-LIFE-NONRENEW-HAS-REASON, V-LIFE-NONRENEW-RECEIPT-REASON and V-LIFE-CAPSULE-MISSION-SCOPED.
  - Relaxed the test-1 DONE assertion, because NOW is in the future and the scoped log is empty there.
- tools/test_session_budget_guard.py: added V-SBG-CALLS-WALL-RECEIPT.

Next exact actions:
1. Run tools/test_halt_continues.py (expect 16+/0) and tools/test_session_budget_guard.py (expect 20+/0).
2. Run the MC 226/227, ADM 43/43 and steward 18/18 suites.
3. Run one tools/mutation_drill.py mutant per fix, each must go red.
4. Commit by pathspec with -F, write WU-S5c-receipt.md (<= 20 lines), and commit again.
5. Arm WU-INST2 only if remaining - open >= 600,000.
