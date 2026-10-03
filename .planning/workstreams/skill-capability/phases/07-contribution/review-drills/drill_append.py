import sys, copy
sys.path.insert(0, "/home/kobii/missions/skill-capability/.claude/worktrees/sc-run/tools")
import test_contribution_verdict as T
inp = T.default_inputs(); fro = T.frozen(); cap = fro["denominators"]["D-SESSIONS"]["new_benchmark_cap"]
# Scenario: the owning workstream appends one new run (outside the pinned set) and its reflog-aware regrade row,
# exactly as 713b02a7 did for N0/R/P.
new = copy.deepcopy(inp["all_rows"][0]); new.update(run_id="D-cwst-C-r3", arm="C", rep=3, grade="PASS")
all_rows = inp["all_rows"] + [new]
reg = inp["regrade"] + [{"run_id": "D-cwst-C-r3", "regraded_by": "reflog-aware grader", "grade": "PASS"}]
inside, outside = T.pinned_split(all_rows, inp["st"]["info"])
print("outside:", [r["run_id"] for r in outside])
res, ctx = T.evaluate_core(inside, None, reg, cap, inp["st"])
print([(n, s) for n, s, _ in res][:1], res[0][2])
print("verdict", T.verdict_of(res))
print("ROWS-PINNED", T.clause_rows_pinned(all_rows, reg, inp["st"]["info"]))
print("ROWS-PINNED rows-only append", T.clause_rows_pinned(all_rows, inp["regrade"], inp["st"]["info"]))
