import sys, copy, traceback
sys.path.insert(0, "/home/kobii/missions/skill-capability/.claude/worktrees/sc-run/tools")
import test_contribution_verdict as T
inp = T.default_inputs(); fro = T.frozen(); cap = fro["denominators"]["D-SESSIONS"]["new_benchmark_cap"]
rows = copy.deepcopy(inp["rows"])
# Scenario: N0 runs crashed before grading (stored grade null) and the reflog-aware regrade later graded them.
for r in rows:
    if r["arm"] == "N0": r["grade"] = None
res, ctx = T.evaluate_core(rows, None, inp["regrade"], cap, inp["st"])
for n, s, t in res: print(s, n, t[:120])
print("verdict", T.verdict_of(res))
try:
    T._render_or_none(dict(inp, rows=rows), fro); print("render ok")
except Exception as e:
    print("render raised", type(e).__name__, e)
try:
    T.derived_json(dict(inp, rows=rows), fro, cap); print("json ok")
except Exception as e:
    print("derived_json raised", type(e).__name__, e)
