# WU-S1 receipt
Status: DONE
Stage: C:\Users\User\Apps\pp-live-stage (detached 41ed853b, install set staged; not removed)
Merge: 4 files via git merge-file on LF blobs (CRLF checkout caused false whole-file conflicts); 1 real conflict, tools/gsd_mission.py slim_finished vs LIVE settle branch: kept both (v3 halt_continue block + LIVE settle).
Checks: node --check x2, py_compile x3 rc=0
Suites: LIFE 6/0 (baseline 5/1), MC 226/227 (baseline 224/225; fail: FAIL V-MC-SUP-HOST-UNANSWERED-NOT-BLOCKED RUNNING ledger=0 rows=[{'mission_id': 'm-hunk', 'state': 'RUNNING', 'epoch': 1, 'action': 'none', 'reason': 'owner UNKNOWN: host session list unavailable'}]), ADM 43/43, HALT 14/0
Logs: _logs/wus1/
sha256[:12] patch: f8c3ce6f6b6a
sha256[:12] hooks/lib/goal_binding.js : ed580ddc5ec7
sha256[:12] hooks/session_budget_guard.js : aa0ed82143c4
sha256[:12] modules/provider_routing/ledger.py : be882040cb42
sha256[:12] tools/gsd_mission.py : 49570bf6b79f
sha256[:12] tools/mission_spend.py : 44b3ffa28502
sha256[:12] tools/test_process_lifecycle.py : 3a549b9682cd
sha256[:12] tools/test_halt_continues.py : 4c9be3ddecdb
Next: coordinator applies L1-install.patch by index onto LIVE (foreign uncommitted gsd_mission.py change exists), then removes the stage.
