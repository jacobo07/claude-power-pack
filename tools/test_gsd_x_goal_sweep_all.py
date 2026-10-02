#!/usr/bin/env python3
"""V-gates for the scheduled goal sweep (SPEC-GOAL-SWEEP-SCHEDULED).

The scheduler calls `sweep-all`, which must DISCOVER autonomous goals from the
store (never a hand list), know where each one runs, say why it skipped any, and
leave a heartbeat so a missed run is not mistaken for a quiet one.

    python tools/test_gsd_x_goal_sweep_all.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.gsd_x.goal import contract as gc         # noqa: E402
from modules.gsd_x.goal import convergence as cv      # noqa: E402
from modules.gsd_x.goal import engine_identity as ei  # noqa: E402
from modules.gsd_x.goal import epoch as ep            # noqa: E402
from modules.gsd_x.goal import git_state as gs        # noqa: E402
from modules.gsd_x.goal import log as gl              # noqa: E402
from modules.gsd_x.goal import sweep as sw            # noqa: E402

GIT = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t", "PYTHONIOENCODING": "utf-8"}


def make_repo(tag: str) -> Path:
    d = Path(tempfile.mkdtemp(prefix=f"gsdx_sweepall_{tag}_"))
    subprocess.run([GIT, "init", "-q", str(d)], check=True, env=ENV)
    (d / "gate.py").write_text(f"import sys\nprint('{tag}')\nsys.exit(0)\n", encoding="utf-8")
    subprocess.run([GIT, "-C", str(d), "add", "."], check=True, env=ENV)
    subprocess.run([GIT, "-C", str(d), "commit", "-qm", f"seed {tag}"], check=True, env=ENV)
    return d


def make_goal(base: Path, gid: str, repo: Path) -> gl.GoalLog:
    lg = gl.GoalLog(gl.repo_id(repo), gid, base=base)
    gc.declare(lg, f"sweep-all {gid}", ["the gate passes"], [], {"paths": ["."]})
    for plane in cv.PLANES:
        cv.set_plane(lg, gc.project(lg), plane, plane in cv.ALWAYS,
                     "" if plane in cv.ALWAYS else "not claimed", "t")
    cv.accept_obligation(lg, gc.project(lg), "ob-outcome", cv.OUTCOME, "prove it",
                         f'"{sys.executable}" gate.py', gs.file_pin(repo, ["gate.py"]), "t")
    return lg


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []

    def check(g, cond, ev, why):
        (passes if cond else fails).append(g)
        print(f"  {'PASS' if cond else 'FAIL'} {g}: {ev if cond else why}")

    # Arrange
    goals = Path(tempfile.mkdtemp(prefix="gsdx_sweepall_goals_")) / "goals"
    goals.mkdir(parents=True)
    os.environ["GSDX_GOALS_ROOT"] = str(goals)
    repo_a, repo_b = make_repo("a"), make_repo("b")
    on = make_goal(goals, "g-on", repo_a)
    off = make_goal(goals, "g-off", repo_a)
    never = make_goal(goals, "g-never", repo_a)
    legacy = make_goal(goals, "g-legacy", repo_a)
    gone_repo = make_repo("gone")
    gone = make_goal(goals, "g-gone", gone_repo)

    sw.set_autonomous(on, gc.project(on), True, "test", "owner", root=repo_a)
    sw.set_autonomous(off, gc.project(off), True, "test", "owner", root=repo_a)
    sw.set_autonomous(off, gc.project(off), False, "stop", "owner")
    sw.set_autonomous(legacy, gc.project(legacy), True, "pre-root event", "owner")
    sw.set_autonomous(gone, gc.project(gone), True, "test", "owner", root=gone_repo)
    # git object files are read-only on Windows: clear the bit, then delete.
    shutil.rmtree(gone_repo, onerror=lambda f, p, _: (os.chmod(p, 0o700), f(p)))
    check("V-SWEEPALL-PRECONDITION-ROOT-DELETED", not gone_repo.exists(),
          "precondition: g-gone's root really is gone", f"{gone_repo} still exists")

    try:
        sw.set_autonomous(never, gc.project(never), True, "wrong repo", "owner", root=repo_b)
        wrong_refused = False
    except gl.GoalLogError:
        wrong_refused = True
    check("V-SWEEPALL-REFUSES-FOREIGN-ROOT", wrong_refused and not sw.is_autonomous(
              gc.project(never)),
          "a root holding ANOTHER repository is refused at write, nothing appended",
          "a goal was bound to a root of a different repository")

    # Act
    found, skipped = sw.autonomous_goals()
    ids = {lg.goal_id: root for lg, root in found}

    # Assert: discovery
    check("V-SWEEPALL-DISCOVERS-AUTONOMOUS",
          set(ids) == {"g-on"} and Path(ids["g-on"]).resolve() == repo_a.resolve(),
          f"only g-on is swept, at its recorded root ({sorted(ids)})",
          f"discovered {sorted(ids)}")
    joined = " | ".join(skipped)
    check("V-SWEEPALL-NAMES-LEGACY-SKIP", "g-legacy" in joined and "no root" in joined,
          "autonomous without a recorded root is skipped with that reason", joined)
    check("V-SWEEPALL-NAMES-MISSING-ROOT", "g-gone" in joined and "missing" in joined,
          "a recorded root that vanished is skipped with that reason", joined)
    check("V-SWEEPALL-OFF-AND-NEVER-SILENT",
          "g-off" not in ids and "g-never" not in ids,
          "switched-off and never-marked goals are not swept", f"{sorted(ids)}")

    # Assert: heartbeat on a refused run (no autonomy record in this state dir)
    rep = sw.sweep_all(ROOT, dry_run=True)
    hb_path = sw.heartbeat_path()
    hb = json.loads(hb_path.read_text(encoding="utf-8")) if hb_path.is_file() else {}
    check("V-SWEEPALL-HEARTBEAT-ON-REFUSAL",
          rep.refused and hb.get("refused") and hb.get("ts"),
          "a refused run still leaves a dated heartbeat naming the refusal", f"{hb}")

    # Assert: acting run, dry
    sw.record_path().write_text(json.dumps({
        "head": "0" * 40, "engine": ei.engine_identity(ROOT), "green": True,
        "suites": {s: {"ok": True} for s in sw.REQUIRED_SUITES}}), encoding="utf-8")
    rep = sw.sweep_all(ROOT, dry_run=True)
    hb = json.loads(hb_path.read_text(encoding="utf-8"))
    check("V-SWEEPALL-ACTS-WHEN-GREEN",
          not rep.refused and any("g-on" in a and "would run" in a for a in rep.acted),
          f"with a green record it plans g-on's gate ({rep.acted})", rep.render())
    check("V-SWEEPALL-HEARTBEAT-ON-ACT",
          not hb.get("refused") and hb.get("goals_seen") == 1 and hb.get("acted"),
          f"heartbeat records the run ({hb.get('goals_seen')} goal, {len(hb['acted'])} act)",
          f"{hb}")
    check("V-SWEEPALL-DRY-RUN-DISPATCHES-NOTHING", not ep.project_epochs(gc.project(on)),
          "a dry sweep-all creates no epoch", "the dry run dispatched")

    # Assert: retry key's engine term ignores repo HEAD
    term = sw.retry_engine_term(ROOT)
    check("V-SWEEPALL-RETRY-KEY-IS-ENGINE", term == ei.engine_identity(ROOT) and term,
          "the retry key names the engine, not the moving repo HEAD", f"term={term!r}")

    print(f"\nGSDX_SWEEP_ALL_PASS={len(passes)}/{len(passes) + len(fails)}  "
          f"threshold={len(passes) + len(fails)}/{len(passes) + len(fails)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
