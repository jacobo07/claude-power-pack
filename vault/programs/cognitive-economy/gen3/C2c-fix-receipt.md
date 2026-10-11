# C2c-fix receipt
Mission: goal cp50-c2 (worktree wt_cp50_c2); id from rehydration card not visible to this worker. Calls used: 6 of 7. Nothing sent.
Edits: runner_lib.py:1472 candidate mode now calls trim_objdiff_report(fn.diff.json -> units/<uid>.diff.json, unit["symbol"]); test_candidate.py gains V-CAND-DIFF-TRIMMED.
PASS V-CAND-DIFF-TRIMMED schema=ksr.objdiff_trim/1 full_bytes=71
test_candidate.py: 2 FAIL, both unrelated to the edit and environmental: V-CAND-OPERANDS-NORMALISED and V-SDA-PRECHECK-REAL, then FileNotFoundError opening a file under wt_cp50_c2\.planning\work... (this worktree has no .planning dir; the real one is in wt_keosdtk_home). Not confirmed pre-existing by a baseline run (call budget).
BATCH_LOCAL_PASS=74/74
ARM_A_DRILL=10/10
ARM_A_PREPARED: NOT RUN (packet gates prepare on test_candidate passing)
Job dir / CURRENT / TRIM_CALLS: not produced (no prepare).
Open points: (1) make the two failing gates find .planning (copy/junction it into wt_cp50_c2, or point the test at wt_keosdtk_home), then re-run test_candidate; (2) then run arm_a.py prepare --first 1 --last 5 and check CURRENT_CAPSULE and TRIM_CALLS=3.
HANDOFF NOTE: C2c-fix PARTIAL -- test_candidate 2 gates need wt_cp50_c2\.planning (env); fix verified by V-CAND-DIFF-TRIMMED, prepare not run