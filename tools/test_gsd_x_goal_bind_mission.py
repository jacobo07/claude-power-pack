#!/usr/bin/env python3
"""V-gates for observing a running Ralph mission from a goal (SPEC-GOAL-OBSERVE-RALPH).

The load-bearing property is that observing never owns: the mission record's
bytes are identical before and after binding, a cancel is refused, and the
mission ending proves nothing by itself.

    python tools/test_gsd_x_goal_bind_mission.py
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
STATE = Path(tempfile.mkdtemp(prefix="gsdx_bindm_state_"))
os.environ["GSD_LONG_RUN_STATE_DIR"] = str(STATE)        # before any tool import
GOALS = Path(tempfile.mkdtemp(prefix="gsdx_bindm_goals_")) / "goals"
GOALS.mkdir(parents=True)
os.environ["GSDX_GOALS_ROOT"] = str(GOALS)
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import gsd_mission as gm                                      # noqa: E402
from modules.gsd_x.goal import bind_mission as bm             # noqa: E402
from modules.gsd_x.goal import contract as gc                 # noqa: E402
from modules.gsd_x.goal import convergence as cv              # noqa: E402
from modules.gsd_x.goal import engine_identity as ei          # noqa: E402
from modules.gsd_x.goal import epoch as ep                    # noqa: E402
from modules.gsd_x.goal import git_state as gs                # noqa: E402
from modules.gsd_x.goal import log as gl                      # noqa: E402
from modules.gsd_x.goal import sweep as sw                    # noqa: E402
from modules.gsd_x.goal.providers.long_run import LongRunProvider  # noqa: E402

GIT = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t", "PYTHONIOENCODING": "utf-8"}


def make_repo(tag: str) -> Path:
    d = Path(tempfile.mkdtemp(prefix=f"gsdx_bindm_{tag}_"))
    subprocess.run([GIT, "init", "-q", str(d)], check=True, env=ENV)
    (d / "gate.py").write_text(f"import sys\nprint('{tag}')\nsys.exit(0)\n", encoding="utf-8")
    subprocess.run([GIT, "-C", str(d), "add", "."], check=True, env=ENV)
    subprocess.run([GIT, "-C", str(d), "commit", "-qm", f"seed {tag}"], check=True, env=ENV)
    return d


def make_goal(gid: str, repo: Path) -> gl.GoalLog:
    lg = gl.GoalLog(gl.repo_id(repo), gid, base=GOALS)
    gc.declare(lg, f"bind {gid}", ["the gate passes"], [], {"paths": ["."]})
    for plane in cv.PLANES:
        cv.set_plane(lg, gc.project(lg), plane, plane in cv.ALWAYS,
                     "" if plane in cv.ALWAYS else "not claimed", "t")
    cv.accept_obligation(lg, gc.project(lg), "ob-outcome", cv.OUTCOME, "prove it",
                         f'"{sys.executable}" gate.py', gs.file_pin(repo, ["gate.py"]), "t")
    return lg


def write_mission(mid: str, state: str, cwd: Path) -> Path:
    p = gm.mission_path(mid)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"mission_id": mid, "state": state, "cwd": str(cwd), "epoch": 3,
                             "iterations": 5, "schema_version": 1}), encoding="utf-8")
    return p


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []

    def check(g, cond, ev, why):
        (passes if cond else fails).append(g)
        print(f"  {'PASS' if cond else 'FAIL'} {g}: {ev if cond else why}")

    # Arrange
    repo, other = make_repo("a"), make_repo("b")
    run_dir = STATE / "runs"
    lg = make_goal("g-bind", repo)
    rec_path = write_mission("m-aaaaaaaaaaaa", "RUNNING", repo)
    before = rec_path.read_bytes()
    write_mission("m-bbbbbbbbbbbb", "COMPLETED", repo)
    write_mission("m-cccccccccccc", "RUNNING", other)

    def refused(mid: str) -> tuple[bool, int]:
        n = len(lg.read())
        try:
            bm.bind_running_mission(lg, repo, mid, "t", "owner", run_dir)
            return False, len(lg.read()) - n
        except (ep.EpochError, gl.GoalLogError):
            return True, len(lg.read()) - n

    # Act + Assert: refusals, each with nothing appended
    for gate, mid, why in (("V-BIND-REFUSES-MISSING", "m-dddddddddddd", "absent"),
                           ("V-BIND-REFUSES-TERMINAL", "m-bbbbbbbbbbbb", "COMPLETED"),
                           ("V-BIND-REFUSES-FOREIGN-REPO", "m-cccccccccccc", "other repo")):
        r, added = refused(mid)
        check(gate, r and added == 0, f"{why} mission refused, 0 events appended",
              f"refused={r}, {added} events appended")

    # Act: the firing control
    e = bm.bind_running_mission(lg, repo, "m-aaaaaaaaaaaa", "observe it", "owner", run_dir)
    eps = ep.project_epochs(gc.project(lg))
    rec = eps[e.epoch_id]
    check("V-BIND-OPENS-RUNNING-EPOCH",
          rec.state == "running" and rec.provider == LongRunProvider.name
          and rec.handle.get("observe_only") and rec.handle.get("mission_id") == "m-aaaaaaaaaaaa",
          f"{e.epoch_id} running, observe-only handle", f"{rec}")
    check("V-BIND-NEVER-WRITES-MISSION", rec_path.read_bytes() == before,
          "the mission record's bytes are unchanged by binding", "binding wrote the record")

    prov = LongRunProvider(run_dir)
    try:
        prov.cancel(rec.handle)
        cancel_refused = False
    except ep.EpochError:
        cancel_refused = True
    check("V-BIND-CANCEL-REFUSED",
          cancel_refused and json.loads(rec_path.read_text(encoding="utf-8"))["state"] == "RUNNING",
          "cancel on an observed mission is refused; it stays RUNNING", "cancel halted it")
    probed = prov.probe(rec.identity) or {}
    check("V-BIND-PROBE-ADOPTS", probed.get("mission_id") == "m-aaaaaaaaaaaa"
          and probed.get("observe_only"),
          "a crash between intent and handle adopts the binding", f"probe={probed}")

    # Sweep observes it (needs a green autonomy record on this engine)
    sw.record_path().parent.mkdir(parents=True, exist_ok=True)
    sw.record_path().write_text(json.dumps({
        "head": "0" * 40, "engine": ei.engine_identity(ROOT), "green": True,
        "suites": {s: {"ok": True} for s in sw.REQUIRED_SUITES}}), encoding="utf-8")
    sw.set_autonomous(lg, gc.project(lg), True, "t", "owner", root=repo)
    rep = sw.sweep(ROOT, [(lg, repo)])
    eps = ep.project_epochs(gc.project(lg))
    check("V-BIND-SWEEP-WAITS-WHILE-RUNNING",
          eps[e.epoch_id].state == "running" and len(eps) == 1,
          f"while the mission runs the sweep starts nothing ({rep.acted})", f"{eps}")

    write_mission("m-aaaaaaaaaaaa", "COMPLETED", repo)
    rep = sw.sweep(ROOT, [(lg, repo)])
    s = gc.project(lg)
    rec = ep.project_epochs(s)[e.epoch_id]
    ob = cv.project_convergence(s).obligations["ob-outcome"]
    check("V-BIND-SWEEP-HARVESTS-ENDED",
          rec.state == "ended" and rec.outcome == ep.COMPLETED,
          f"the ended mission is harvested ({rep.acted})", f"{rec.state}/{rec.outcome} {rep.acted}")
    check("V-BIND-ENDING-PROVES-NOTHING", ob.disposition != cv.SATISFIED,
          "a mission ending satisfies no obligation", "the run's end satisfied an obligation")

    print(f"\nGSDX_BIND_MISSION_PASS={len(passes)}/{len(passes) + len(fails)}  "
          f"threshold={len(passes) + len(fails)}/{len(passes) + len(fails)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
