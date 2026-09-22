#!/usr/bin/env python3
"""V-gates for the independent judge (C13).

The drill that matters is the RIGGED BUILDER: a builder that weakened its own
done gate after it was accepted must not be certified by an honest re-run of the
weakened gate.

    python tools/test_gsd_x_goal_judge.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.gsd_x.goal import contract as gc       # noqa: E402
from modules.gsd_x.goal import convergence as cv    # noqa: E402
from modules.gsd_x.goal import git_state as gs      # noqa: E402
from modules.gsd_x.goal import judge as jd          # noqa: E402
from modules.gsd_x.goal import log as gl            # noqa: E402
from modules.gsd_x.mission import closure as mcl    # noqa: E402

GIT = r"C:\Program Files\Git\cmd\git.exe"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
REPO_ID = "a1" * 20

REAL_GATE = "import sys\nprint('3 passed')\nsys.exit(0)\n"
FAILING_GATE = "import sys\nprint('1 failed')\nsys.exit(1)\n"


def make_repo(gate_body: str) -> Path:
    d = Path(tempfile.mkdtemp(prefix="gsdx_judge_"))
    subprocess.run([GIT, "init", "-q", str(d)], check=True, env=ENV)
    (d / "gate.py").write_text(gate_body, encoding="utf-8")
    subprocess.run([GIT, "-C", str(d), "add", "."], check=True, env=ENV)
    subprocess.run([GIT, "-C", str(d), "commit", "-qm", "gate"], check=True, env=ENV)
    return d


def goal_with_satisfied(base: Path, gid: str, repo: Path, tree: str):
    lg = gl.GoalLog(REPO_ID, gid, base=base)
    gc.declare(lg, "judge me", ["the gate passes"], [], {"paths": ["."]})
    for plane in cv.PLANES:
        s = gc.project(lg)
        cv.set_plane(lg, s, plane, plane in cv.ALWAYS, "" if plane in cv.ALWAYS
                     else "not claimed", "t")
    pin = gs.file_pin(repo, ["gate.py"])
    gate_cmd = f'"{sys.executable}" gate.py'
    for plane in (cv.OUTCOME, cv.EVIDENCE, cv.REGRESSION, cv.UCR_CIF_LEARNING):
        cv.accept_obligation(lg, gc.project(lg), f"ob-{plane.lower()}", plane, "do it",
                             gate_cmd, pin, "t")
    for oid in list(cv.project_convergence(gc.project(lg)).obligations):
        s = gc.project(lg)
        cv.satisfy(lg, s, oid, mcl.Verdict("gate.py", 0, "3 passed", tree, s.revision,
                                           "unit", pin), "t")
    return lg


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []

    def ok(g, ev):
        passes.append(g)
        print(f"  PASS {g}: {ev}")

    def bad(g, why):
        fails.append(g)
        print(f"  FAIL {g}: {why}")

    def check(g, cond, ev, why):
        (ok if cond else bad)(g, ev if cond else why)

    base = Path(tempfile.mkdtemp(prefix="gsdx_judge_goals_"))
    clean_env = {k: v for k, v in os.environ.items() if k != jd.EPOCH_ENV}

    # --- the control: an honest goal is certified ---------------------------------
    repo = make_repo(REAL_GATE)
    tree = gs.tree_id(repo, ["."])
    lg = goal_with_satisfied(base, "g-honest", repo, tree)
    r = jd.judge(gc.project(lg), tree, repo, ["."], env=clean_env)
    check("V-JUDGE-PASSES-HONEST", r.verdict == jd.PASS and len(r.gates) == 4,
          f"an honest goal is certified after re-running its 4 pinned gates ({r.reason})",
          f"{r.verdict}: {r.reason}")

    # --- the rigged builder -----------------------------------------------------------
    (repo / "gate.py").write_text("import sys\nprint('always fine')\nsys.exit(0)\n",
                                  encoding="utf-8")
    subprocess.run([GIT, "-C", str(repo), "commit", "-qam", "weaken the gate"], check=True,
                   env=ENV)
    weak_tree = gs.tree_id(repo, ["."])
    r2 = jd.judge(gc.project(lg), weak_tree, repo, ["."], env=clean_env)
    check("V-JUDGE-REFUSES-RIGGED-GATE",
          r2.verdict == jd.REFUSED and "pinned gate files differ" in r2.reason,
          "a gate weakened after acceptance is refused, even though it exits 0",
          f"{r2.verdict}: {r2.reason}")

    # --- a gate that genuinely fails ------------------------------------------------------
    repo2 = make_repo(REAL_GATE)
    tree2 = gs.tree_id(repo2, ["."])
    lg2 = goal_with_satisfied(base, "g-fails", repo2, tree2)
    (repo2 / "gate.py").write_text(FAILING_GATE, encoding="utf-8")
    # re-pin so the FAILURE is what is judged, not the pin
    s2 = gc.project(lg2)
    subprocess.run([GIT, "-C", str(repo2), "commit", "-qam", "gate now fails"], check=True,
                   env=ENV)
    tree2b = gs.tree_id(repo2, ["."])
    lg2b = goal_with_satisfied(base, "g-fails-2", repo2, tree2b)
    r3 = jd.judge(gc.project(lg2b), tree2b, repo2, ["."], env=clean_env)
    check("V-JUDGE-REFUSES-FAILING-GATE",
          r3.verdict == jd.REFUSED and "exit 1" in r3.reason,
          "a pinned gate that re-runs and fails refuses certification",
          f"{r3.verdict}: {r3.reason}")

    # --- independence ---------------------------------------------------------------------
    r4 = jd.judge(gc.project(lg), tree, repo, ["."], env={**clean_env, jd.EPOCH_ENV: "ep-99"})
    check("V-JUDGE-REFUSES-INSIDE-EPOCH",
          r4.verdict == jd.UNJUDGEABLE and "cannot judge itself" in r4.reason,
          "a judge invoked from inside an epoch refuses: that is the builder",
          f"{r4.verdict}: {r4.reason}")
    r5 = jd.judge(gc.project(lg), "git:0000000000000000000000000000000000000000", repo, ["."],
                  env=clean_env)
    check("V-JUDGE-WRONG-TREE",
          r5.verdict == jd.UNJUDGEABLE and "not the tree being judged" in r5.reason,
          "judging tree A while standing in tree B is refused", f"{r5.verdict}: {r5.reason}")

    # --- nothing to judge is not a pass --------------------------------------------------------
    lg3 = gl.GoalLog(REPO_ID, "g-empty", base=base)
    gc.declare(lg3, "nothing proven yet")
    r6 = jd.judge(gc.project(lg3), gs.tree_id(repo, ["."]), repo, ["."], env=clean_env)
    check("V-JUDGE-NOTHING-IS-NOT-PASS",
          r6.verdict == jd.UNJUDGEABLE and "nothing was judged" in r6.reason,
          "a goal with no proven obligation is UNJUDGEABLE, never PASS",
          f"{r6.verdict}: {r6.reason}")

    # --- a gate that cannot run outranks a subject failure -------------------------------------
    lg4 = goal_with_satisfied(base, "g-unrunnable", repo2, tree2b)
    s4 = gc.project(lg4)
    # point one obligation at a command that cannot start
    cv.accept_obligation(lg4, s4, "ob-broken", cv.RECOVERY, "x", "definitely-not-a-program",
                         gs.file_pin(repo2, ["gate.py"]), "t")
    s4 = gc.project(lg4)
    cv.satisfy(lg4, s4, "ob-broken",
               mcl.Verdict("x", 0, "ok", tree2b, s4.revision, "unit",
                           gs.file_pin(repo2, ["gate.py"])), "t")
    r7 = jd.judge(gc.project(lg4), tree2b, repo2, ["."], env=clean_env)
    check("V-JUDGE-UNRUNNABLE-OUTRANKS",
          r7.verdict == jd.UNJUDGEABLE and "could not be run" in r7.reason,
          "a gate the judge could not run outranks subject failures in the same run",
          f"{r7.verdict}: {r7.reason}")

    total = len(passes) + len(fails)
    print(f"\nGSDX_JUDGE_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
