import sys, copy
sys.path.insert(0, "/home/kobii/missions/skill-capability/.claude/worktrees/sc-run/tools")
import test_contribution_verdict as T
inp = T.default_inputs()
fro = T.frozen(); cap = fro["denominators"]["D-SESSIONS"]["new_benchmark_cap"]
rows = copy.deepcopy(inp["rows"])
# Scenario: the frozen D-CARD.arm_c "2/2 PASS (123c96cc)" rows get committed as arm C (fixed card).
for r in rows:
    if r["arm"] == "C":
        r["grade"] = "PASS"
res, ctx = T.evaluate_core(rows, None, inp["regrade"], cap, inp["st"])
for n, s, t in res: print(s, n, t[:150])
print("verdict", T.verdict_of(res))
print("needed_k(1)", T.needed_k(1))
