#!/usr/bin/env python3
"""V-DIET gates: floor_diet plan/apply/revert on a scratch HOME (never a live one)."""
import hashlib, os, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import floor_diet as fd

P = F = 0
def ok(n, c, ev=""):
    global P, F
    if c: P += 1; print(f"PASS {n} {ev}")
    else: F += 1; print(f"FAIL {n} {ev}")

def snap(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob("*")) if p.is_file() and "backups" not in p.parts}

def build(home):
    c = home / ".claude"
    for n in ["old-agent", "hook-agent", "used-agent", "keeper"]:
        (c / "agents").mkdir(parents=True, exist_ok=True); (c / "agents" / f"{n}.md").write_text(f"# {n}\n")
    (c / "hooks").mkdir(); (c / "hooks" / "h.js").write_text('dispatch({subagent_type: "hook-agent"})')
    (c / "rules").mkdir()
    for r in fd.RULES_TO_SKILLS: (c / "rules" / f"{r}.md").write_text(f"# {r}\n\nBody of {r}.\n")
    (c / "rules" / "other.md").write_text("# other\n")
    (c / "rules" / "skill-rule-index.md").write_text("# idx\n- a\n")
    m = c / "projects" / "p1" / "memory"; m.mkdir(parents=True)
    (m / "MEMORY.md").write_text("\n".join(f"- line {i}" for i in range(260)) + "\n")
    (c / "projects" / "p2" / "memory").mkdir(parents=True)
    (c / "projects" / "p2" / "memory" / "MEMORY.md").write_text("- short\n")

with tempfile.TemporaryDirectory() as td:
    home = Path(td); build(home); before = snap(home)
    plan = fd.plan(home, {"keeper"}, {"used-agent"})
    ok("V-DIET-PLAN-PARKS-UNUSED", plan["agents_park"] == ["old-agent.md"], str(plan["agents_park"]))
    ok("V-DIET-PLAN-KEEPS-HOOK-DISPATCHED", "hook-agent" in plan["agents_kept"] and "keeper" in plan["agents_kept"] and "used-agent" in plan["agents_kept"])
    ok("V-DIET-PLAN-MEMORY-ONLY-OVER-LIMIT", len(plan["memory_trim"]) == 1 and plan["memory_trim"][0]["cold"] == 60)
    ok("V-DIET-PLAN-IS-READONLY", snap(home) == before)
    b = fd.apply(home, plan, "t1")
    c = home / ".claude"
    ok("V-DIET-APPLY-AGENT-PARKED", not (c / "agents/old-agent.md").exists() and (c / "agents-parked/old-agent.md").exists() and (c / "agents/hook-agent.md").exists())
    ok("V-DIET-APPLY-RULES-TO-SKILLS", all((c / "skills" / r / "SKILL.md").is_file() and not (c / "rules" / f"{r}.md").exists() for r in fd.RULES_TO_SKILLS) and (c / "rules/other.md").exists())
    ok("V-DIET-APPLY-BODY-PRESERVED", "Body of durable-exit-transaction." in (c / "skills/durable-exit-transaction/SKILL.md").read_text())
    ok("V-DIET-APPLY-INDEX-LISTS-MOVED", all(r in (c / "rules/skill-rule-index.md").read_text() for r in fd.RULES_TO_SKILLS))
    mem = c / "projects/p1/memory"
    ok("V-DIET-APPLY-MEMORY-200", len((mem / "MEMORY.md").read_text().splitlines()) == 200 and len((mem / "MEMORY_COLD.md").read_text().splitlines()) == 60)
    mm = (mem / "MEMORY.md").read_text().splitlines()
    ok("V-DIET-APPLY-LOSSLESS-MEMORY", sorted(mm + (mem / "MEMORY_COLD.md").read_text().splitlines()) == sorted(f"- line {i}" for i in range(260)))
    ok("V-DIET-MEMORY-KEEPS-NEWEST-TAIL", mm[-1] == "- line 259" and "- line 0" not in mm and "- line 0" in (mem / "MEMORY_COLD.md").read_text())
    ok("V-DIET-APPLY-CHANGED-SOMETHING", snap(home) != before)
    fd.revert(home, b)
    ok("V-DIET-REVERT-BYTE-IDENTICAL", snap(home) == before)
    # negative control: an apply with a pre-existing skill must refuse and leave rules in place
    (c / "skills/durable-exit-transaction").mkdir(parents=True); (c / "skills/durable-exit-transaction/SKILL.md").write_text("x")
    try:
        fd.apply(home, fd.plan(home, set(), set()), "t2"); refused = False
    except SystemExit: refused = True
    ok("V-DIET-REFUSES-SKILL-COLLISION", refused)

long = "Alpha beta. " * 40 + "tail"
d = fd._description("# T\n\n" + long, "x")
import json as _j
ok("V-DIET-DESC-NOT-MIDWORD", _j.loads(d).endswith(".") and len(_j.loads(d)) <= 300, d[-20:])
q = fd._description("# T\n\n\"Quoted\" start: with colon", "x")
ok("V-DIET-DESC-YAML-SAFE", q.startswith('"') and _j.loads(q) == '"Quoted" start: with colon')
print(f"DIET_PASS={P}/{P+F}  threshold={P+F}/{P+F}")
sys.exit(0 if F == 0 else 1)
