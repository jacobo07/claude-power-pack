#!/usr/bin/env python
"""CDC C5 proof: affected closure vs full tools/test_*.py suite on past landings.
Full suite runs once at the worktree HEAD (every subprocess awaited, 600 s cap each); a landing's closure verdict is
compared with the full verdict restricted to the suites each side ran. Output: JSON to argv[1]."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import change_impact as ci  # noqa: E402
import land_worktree as lw  # noqa: E402

LANDINGS = sys.argv[2:] or ["d1fbc0e0", "909ad75b", "512af829"]


def run(t):
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, t], cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=90)
        rc, out = p.returncode, p.stdout + p.stderr
    except Exception as e:
        rc, out = 99, repr(e)
    n = len(re.findall(r"\bPASS\b", out)) + len(re.findall(r"\bFAIL\b", out))
    return t, {"rc": rc, "secs": round(time.time() - t0, 2), "checks": n}


suites = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "tools").glob("test_*.py"))
t0 = time.time()
with ThreadPoolExecutor(10) as ex:
    full = dict(ex.map(run, suites))
full_wall = round(time.time() - t0, 1)
out = {"full": {"suites": len(full), "wall_s": full_wall, "sum_s": round(sum(v["secs"] for v in full.values()), 1),
                "checks": sum(v["checks"] for v in full.values()),
                "red": sorted(k for k, v in full.items() if v["rc"] != 0)}, "landings": []}
for sha in LANDINGS:
    files = [x for x in lw.git(str(ROOT), "diff-tree", "--no-commit-id", "--name-only", "-r", sha).stdout.splitlines() if x]
    cl = ci.affected_closure(files, ROOT)
    ts = [c.split(" ", 1)[1] for c in cl["tests"]]
    ts = [t for t in ts if t in full]
    red_in = sorted(t for t in ts if full[t]["rc"] != 0)
    out["landings"].append({
        "sha": sha, "files": files, "unmapped": cl["unmapped"], "unjudged": cl["unjudged"],
        "closure_suites": len(ts), "closure_secs": round(sum(full[t]["secs"] for t in ts), 1),
        "closure_checks": sum(full[t]["checks"] for t in ts), "closure_red": red_in,
        "closure_verdict": "GREEN" if not red_in and not cl["unmapped"] and not cl["unjudged"] else "RED/REFUSE",
        "full_verdict": "GREEN" if not out["full"]["red"] else "RED",
        "full_red_outside_closure": sorted(set(out["full"]["red"]) - set(ts))})
Path(sys.argv[1]).write_text(json.dumps(out, indent=1), encoding="utf-8")
print(json.dumps({"full": {k: v for k, v in out["full"].items() if k != "red"}, "red": out["full"]["red"],
                  "landings": [{k: v for k, v in l.items() if k != "files"} for l in out["landings"]]}, indent=1))
