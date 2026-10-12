#!/usr/bin/env python
"""V-LAND-* gates for land_worktree --affected (CDC C5). Hermetic temp repos, injected closure."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import land_worktree as lw  # noqa: E402
import change_impact as ci  # noqa: E402
import tier_routing as tr  # noqa: E402

passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def g(repo, *a):
    return subprocess.run([lw.GIT, "-C", str(repo), *a], capture_output=True, text=True)


def mk(tmp):
    live, wt = Path(tmp) / "live", Path(tmp) / "wt"
    live.mkdir()
    g(live, "init", "-q", "-b", "main")
    g(live, "config", "user.email", "t@t")
    g(live, "config", "user.name", "t")
    (live / "a.txt").write_text("a")
    g(live, "add", "."); g(live, "commit", "-qm", "i")
    g(live, "worktree", "add", "-q", "-b", "feat", str(wt))
    (wt / "x.py").write_text("x = 1\n")
    g(wt, "add", "x.py"); g(wt, "commit", "-qm", "x")
    return live, wt


def cl(unmapped=(), unjudged=False, tests=()):
    return lambda paths, wt: {"unjudged": unjudged, "gaps": ["g"], "unmapped": list(unmapped),
                              "tests": list(tests), "per_path": {p: list(tests) for p in paths}}


with tempfile.TemporaryDirectory() as t:
    live, wt = mk(t)
    r = lw.land(str(wt), str(live), affected=True, closure_fn=cl(unmapped=["x.py"]))
    check("V-LAND-01 unmapped path refuses, nothing landed", r["reason"] == "AFFECTED_NO_MAPPED_TEST"
          and r["unmapped"] == ["x.py"] and not r["landed"], r["reason"])
    r = lw.land(str(wt), str(live), affected=True, closure_fn=cl(unjudged=True))
    check("V-LAND-02 unjudged closure refuses", r["reason"] == "AFFECTED_UNJUDGED")
    r = lw.land(str(wt), str(live), affected=True, closure_fn=cl(tests=["python -c \"import sys; sys.exit(1)\""]))
    check("V-LAND-03 red affected test refuses", r["reason"] == "TESTS_RED_BEFORE" and not r["landed"])
    r = lw.land(str(wt), str(live), tests=[], affected=False)
    check("V-LAND-04 no tests, no --affected -> NO_TESTS_DECLARED", r["reason"] == "NO_TESTS_DECLARED")
    r = lw.land(str(wt), str(live), tests=['python -c "pass"'], affected=True,
                closure_fn=cl(tests=['python -c "print(1)"']))
    check("V-LAND-05 union of explicit + affected, closure in receipt, landed",
          r["status"] == "LANDED" and len(r["tests"]) == 2 and "x.py" in r["affected_closure"]["per_path"], r["status"])

with tempfile.TemporaryDirectory() as t:
    live, wt = mk(t)
    r = lw.land(str(wt), str(live), affected=True, exempt=["x.*"], closure_fn=cl(unmapped=["x.py"]),
                tests=['python -c "pass"'])
    check("V-LAND-06 exempt glob is explicit in the receipt", r["status"] == "LANDED"
          and r["affected_closure"]["exempted"] == ["x.py"], r.get("reason"))

# change_impact.affected_closure with a fake analyzer
def fake(root, changed):
    p = changed[0]
    if p == "tools/a.py":
        return {"affected": {"test": ["tools/test_a.py"]}, "gaps": []}
    if p == "x.md":
        return {"affected": {"test": []}, "gaps": [{"type": "unmatched-change", "path": p}]}
    if p == "tools/test_self.py":
        return {"affected": {"test": []}, "gaps": []}
    return {"unjudged": True, "gaps": [{"type": "bridge"}]}


c = ci.affected_closure(["tools/a.py", "x.md", "tools/test_self.py"], analyzer=fake)
check("V-LAND-07 closure maps, flags unmapped, test file reaches itself",
      c["tests"] == ["python tools/test_a.py", "python tools/test_self.py"] and c["unmapped"] == ["x.md"], c)
check("V-LAND-08 unjudged analyzer -> unjudged, no tests",
      ci.affected_closure(["zzz"], analyzer=fake)["unjudged"])

check("V-LAND-09 reviewer skipped only for deterministic + green",
      not tr.review_policy("deterministic", True)["reviewer"])
for wc, gr in (("deterministic", False), ("deterministic", None), ("novel", True), ("bounded_coding", True)):
    check(f"V-LAND-10 reviewer kept for {wc}/{gr}", tr.review_policy(wc, gr)["reviewer"])
check("V-LAND-11 unit red keeps reviewer", tr.review_policy("deterministic", True, unit_green=False)["reviewer"])

print(f"{passes} passed, {fails} failed")
sys.exit(1 if fails else 0)
