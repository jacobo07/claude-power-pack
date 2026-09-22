#!/usr/bin/env python3
"""V-gates for the unattended sweep (C12).

The load-bearing case is the REFUSAL: the sweep must not act until the judge
and chaos suites are recorded green at the commit that would run, because it is
the one component that spends resources with nobody reading the output.

    python tools/test_gsd_x_goal_sweep.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.gsd_x.goal import contract as gc       # noqa: E402
from modules.gsd_x.goal import convergence as cv    # noqa: E402
from modules.gsd_x.goal import epoch as ep          # noqa: E402
from modules.gsd_x.goal import git_state as gs      # noqa: E402
from modules.gsd_x.goal import log as gl            # noqa: E402
from modules.gsd_x.goal import sweep as sw          # noqa: E402

GIT = r"C:\Program Files\Git\cmd\git.exe"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
       "PYTHONIOENCODING": "utf-8"}
REPO_ID = "5e" * 20


def make_repo() -> Path:
    d = Path(tempfile.mkdtemp(prefix="gsdx_sweep_repo_"))
    subprocess.run([GIT, "init", "-q", str(d)], check=True, env=ENV)
    (d / "gate.py").write_text("import sys\nprint('1 passed')\nsys.exit(0)\n", encoding="utf-8")
    subprocess.run([GIT, "-C", str(d), "add", "."], check=True, env=ENV)
    subprocess.run([GIT, "-C", str(d), "commit", "-qm", "seed"], check=True, env=ENV)
    return d


def make_goal(base: Path, gid: str, repo: Path, autonomous: bool):
    lg = gl.GoalLog(REPO_ID, gid, base=base)
    gc.declare(lg, f"sweep {gid}", ["the gate passes"], [], {"paths": ["."]})
    for plane in cv.PLANES:
        s = gc.project(lg)
        cv.set_plane(lg, s, plane, plane in cv.ALWAYS, "" if plane in cv.ALWAYS
                     else "not claimed", "t")
    cv.accept_obligation(lg, gc.project(lg), "ob-outcome", cv.OUTCOME, "prove it",
                         f'"{sys.executable}" gate.py', gs.file_pin(repo, ["gate.py"]), "t")
    if autonomous:
        sw.set_autonomous(lg, gc.project(lg), True, "test", "owner")
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

    goals_root = Path(tempfile.mkdtemp(prefix="gsdx_sweep_goals_")) / "goals"
    goals_root.mkdir(parents=True)
    os.environ["GSDX_GOALS_ROOT"] = str(goals_root)
    repo = make_repo()
    lg = make_goal(goals_root, "g-auto", repo, autonomous=True)
    lg_off = make_goal(goals_root, "g-manual", repo, autonomous=False)

    # --- the precondition ---------------------------------------------------------
    rep = sw.sweep(ROOT, [(lg, repo)])
    check("V-SWEEP-REFUSES-WITHOUT-RECORD",
          rep.refused and "no autonomy record" in rep.refused,
          "with no recorded green the sweep refuses to act at all", rep.render())

    rec = sw.record_path()
    rec.parent.mkdir(parents=True, exist_ok=True)
    rec.write_text(json.dumps({"head": gs.head(ROOT), "green": False,
                               "suites": {"test_gsd_x_goal_judge.py": {"ok": False}}}),
                   encoding="utf-8")
    rep = sw.sweep(ROOT, [(lg, repo)])
    check("V-SWEEP-REFUSES-RED-RECORD", rep.refused and "not green" in rep.refused,
          "a record that is not green is not permission", rep.render())

    rec.write_text(json.dumps({"head": "0" * 40, "green": True, "suites": {}}),
                   encoding="utf-8")
    rep = sw.sweep(ROOT, [(lg, repo)])
    check("V-SWEEP-REFUSES-STALE-RECORD", rep.refused and "re-run `record-gates`" in rep.refused,
          "a green recorded for ANOTHER commit is stale, not a licence", rep.render())

    rec.write_text("{not json", encoding="utf-8")
    rep = sw.sweep(ROOT, [(lg, repo)])
    check("V-SWEEP-REFUSES-UNREADABLE",
          rep.refused and "not permission" in rep.refused,
          "an unreadable record is refused, never read as permission", rep.render())

    # --- acting, once the preconditions hold -------------------------------------------
    rec.write_text(json.dumps({"head": gs.head(ROOT), "green": True,
                               "suites": {s: {"ok": True} for s in sw.REQUIRED_SUITES}}),
                   encoding="utf-8")
    rep = sw.sweep(ROOT, [(lg, repo), (lg_off, repo)], dry_run=True)
    check("V-SWEEP-ACTS-WHEN-GREEN",
          not rep.refused and any("would run" in a for a in rep.acted),
          f"with the record green it plans work ({rep.acted})", rep.render())
    check("V-SWEEP-SKIPS-MANUAL-GOALS",
          any("g-manual" in s and "not marked autonomous" in s for s in rep.skipped),
          "a goal nobody marked autonomous is skipped", f"{rep.skipped}")
    check("V-SWEEP-DRY-RUN-CHANGES-NOTHING", not ep.project_epochs(gc.project(lg)),
          "a dry run dispatches nothing", "the dry run created an epoch")

    rep = sw.sweep(ROOT, [(lg, repo)])
    eps = ep.project_epochs(gc.project(lg))
    check("V-SWEEP-DISPATCHES-GATE",
          len(eps) == 1 and list(eps.values())[0].state == "running",
          f"the gate epoch is dispatched and recorded running ({rep.acted})", rep.render())
    running = list(ep.project_epochs(gc.project(lg)).values())[0]
    check("V-SWEEP-NON-BLOCKING",
          running.state == "running" and running.outcome == "",
          "the sweep recorded a RUNNING epoch and returned: it did not wait for the gate "
          "to finish, which a five-minute schedule cannot afford",
          f"state={running.state} outcome={running.outcome}")

    # --- it never spends an account -------------------------------------------------------
    s = gc.project(lg)
    e = list(ep.project_epochs(s).values())[0]
    ep.end(lg, s, e.epoch_id, ep.FAILED, "gate failed", "t")
    acted = sw.sweep_goal(lg, repo, providers=("gate", "codex"), dry_run=True)
    check("V-SWEEP-REPORTS-WORK-NEVER-SPENDS",
          any(a.startswith("g-auto: NEXT_EPOCH") and "needs provider codex" in a
              for a in acted),
          f"work that spends an account is REPORTED, naming the provider it needs, and is "
          f"not dispatched ({acted})", f"{acted}")
    check("V-SWEEP-NO-CODEX-EPOCH",
          not any(x.provider == "codex" for x in ep.project_epochs(gc.project(lg)).values()),
          "no codex epoch was created by the sweep", "the sweep spent the account")

    # --- silence --------------------------------------------------------------------------
    quiet = sw.SweepReport()
    check("V-SWEEP-SILENT-WHEN-IDLE", quiet.render() == "",
          "a sweep that did nothing prints nothing", f"{quiet.render()!r}")

    total = len(passes) + len(fails)
    print(f"\nGSDX_GOAL_SWEEP_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
