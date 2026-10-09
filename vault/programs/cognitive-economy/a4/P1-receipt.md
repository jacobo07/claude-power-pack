# A4-P1 receipt
Status: DONE
Staged at C:\Users\User\Apps\pp-live-stage-a4p1 (detached ddae1fb1); LIVE untouched.
sha256[:12] P1-install.patch=916a52116585 mission_spend.py=e98ab7db001d mission_capsule.py=1d3509b8c637 test_goal_autopsy.py=a39254e96728
Conflicts: git merge-file against CRLF worktree files conflicted whole-file (EOL); redone on LF blobs: mission_capsule 0, mission_spend 2. Both resolved by hand: kept LIVE side (goal-prebind/settle/correct), added only R5 parts (goal-autopsy parser + dispatch). Source-only goal-fault/grant/revoke/reconcile left out (not R5; not in LIVE).
Baseline -> after: admission 43/43 -> 43/43; process_lifecycle 6/0 -> 6/0; gsd_mission 226/227 -> 226/227 (same pre-existing FAIL V-MC-SUP-HOST-UNANSWERED-NOT-BLOCKED); test_goal_autopsy 10/10.
py_compile OK. goal-autopsy --help OK. Autopsy ce-unify (_logs/a4p1/autopsy-ce-unify.json): ok=true cap=1200000 used=750000 bound_processed=663402 sessions=1 (worker, 11 calls, 1 open hold).
Hook hunk (P1-hook-hunk.patch, GOAL_STATE regex): NOT required by the 10 tests; apply separately after Owner review (HR-001).
Patch applies on ddae1fb1 (apply --check -R passed on stage). Mind CRLF warnings: blobs are LF.
Calls used: 9 (budget 7; extra from PS5.1 encoding/EOL retries).
