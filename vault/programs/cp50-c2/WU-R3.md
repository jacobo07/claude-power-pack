# WU-R3 -- C2c residual + readiness certificate (goal cp50-c2, root wt_cp50_c2)
Plan: vault/plans/cpx-control-plane-extinction-cp50-2026-10-11.md section 5 (R3). 3cf66819 already settled (799,548). Mission m-ae80353974b4 is HALTED: never re-arm.
1. Baseline-compare the 2 FAIL gates (fail only if worse than baseline).
2. Port W1 fa8aaf0; port trim (runner_lib.py:1472 shutil.copyfile -> trim_objdiff_report, PP patch 147115b0).
3. Output-budget admission: sum(.o + trimmed diff) + log ceiling <= 20,971,520 else NOT_READY:OUT_BUDGET.
4. Job-key exactly-once; rm_a prepare --first 1 --last 5; verify CURRENT_CAPSULE + TRIM_CALLS.
5. Replay the job-2 directory: it MUST refuse. Write readiness certificate vault/programs/cp50-c2/R3-certificate.md (W1 port, trim, budget, job-key, CURRENT_CAPSULE).
Done-check: certificate present and valid; replay refusal output in receipt.
Route: route-L.json.
Common: no Monitor, no waiting call, no Agent spawns, no GSD commands. Pathspec commits on feature/knowledge-acquisition (no push), message ends with the Co-Authored-By line from the commit attribution. Never tick a chain by hand. Receipt K7 row: estimate vs actual processed tokens. Receipt line 1 '# <ID> receipt', line 2 'Status: DONE'.
Receipt path: C:\Users\User\.claude\skills\claude-power-pack\vault\programs\cp50-c2\WU-R3-receipt.md
