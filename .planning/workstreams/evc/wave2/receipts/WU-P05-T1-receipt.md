Status: BLOCKED: tools/test_gsd_mission.py exits 1 on two gates that also fail at HEAD 0c108c17 without this change
Unit: WU-P05-T1
HEAD: 0c108c17

HEAD: 0c108c17
RED-FIRST: before the code V-EVC-05-01 (stop stayed 900000), V-EVC-05-02 (stop unchanged) and V-EVC-05-04b (no deny_write_skipped) failed. V-05-03 and 04a passed vacuously on the old code. V-05-05 has no target: no SUSPENDED state exists anywhere in tools/*.py, so it is recorded as NA.
VERIFY:
- test_evc_spend_capability.py: exit 0, 6 pass 0 fail
- test_gsd_mission_owner_hold.py: exit 0, OWNER_HOLD_PASS=32/32
- test_mission_spend.py: exit 0, MSPEND_PASS=30/30
- test_gsd_mission.py: exit 1. Failing: V-MC-PLAN-FACTS-REFUSES-OVERLAP and V-MC-SUP-HOST-UNANSWERED-NOT-BLOCKED. The same two fail on a clean `git archive HEAD` copy, so they predate this task. Two WORKDIR gates also failed once from a 60 s git-add timeout, then passed on the rerun.
CODE: implemented but NOT committed, left in the worktree: tools/mission_spend.py (deny_budget, restore_budget), tools/gsd_mission.py (_worker_budget_io, hooks in set_owner_hold and release_owner_hold), tools/test_evc_spend_capability.py (new).
REMAINING STEP: fix or waive the two pre-existing test_gsd_mission failures, then commit the three files above with `feat(evc-05): task 1 -- Hold and breaker trip write the worker deny file; release restores it`.
