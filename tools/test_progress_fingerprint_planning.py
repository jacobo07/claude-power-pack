#!/usr/bin/env python
"""V-PFP-* gates: progress_fingerprint sees GSD artifacts in a git-excluded `.planning/`.

Measured 2026-10-15 (m-07a78fbae3c7): phase 1 of a GSD mission wrote only to an excluded `.planning/`
and the cost breaker held the working mission at 5.36M "since the work tree last changed".
Real git in a temp repo. Every "moves" gate has a "does not move" control.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
import gsd_mission as gm  # noqa: E402

passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def git(repo: Path, *args: str) -> None:
    g = gm.resolve_exe("git") or "git"
    subprocess.run([g, "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", *args],
                   check=True, capture_output=True)


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="pfp-test-"))
    try:
        repo = tmp / "repo"
        repo.mkdir()
        git(repo, "init", "-q")
        (repo / "a.txt").write_text("a\n", encoding="utf-8")
        git(repo, "add", "a.txt")
        git(repo, "commit", "-q", "-m", "init")
        (repo / ".git" / "info" / "exclude").write_text(".planning/\n", encoding="utf-8")
        phase = repo / ".planning" / "workstreams" / "ws" / "phases" / "01-x"
        phase.mkdir(parents=True)
        (repo / ".planning" / "workstreams" / "ws" / "STATE.md").write_text("s0\n", encoding="utf-8")

        fp0 = gm.progress_fingerprint(str(repo))
        check("V-PFP-MEASURED", fp0 is not None, f"fp0={fp0}")

        (phase / "01-CONTEXT.md").write_text("context\n", encoding="utf-8")
        fp1 = gm.progress_fingerprint(str(repo))
        check("V-PFP-NEW-ARTIFACT-MOVES", fp1 != fp0, "a new phase file in an excluded .planning/")

        (phase / "01-CONTEXT.md").write_text("context, longer now\n", encoding="utf-8")
        fp2 = gm.progress_fingerprint(str(repo))
        check("V-PFP-GROWN-ARTIFACT-MOVES", fp2 != fp1, "an artifact that changed size")

        (repo / ".planning" / "workstreams" / "ws" / "STATE.md").write_text("s1 rewritten every turn\n",
                                                                               encoding="utf-8")
        fp3 = gm.progress_fingerprint(str(repo))
        check("V-PFP-STATE-CHURN-STILL", fp3 == fp2, "STATE.md rewrite alone is not progress")

        fp4 = gm.progress_fingerprint(str(repo))
        check("V-PFP-IDLE-STILL", fp4 == fp3, "nothing written")

        (repo / "a.txt").write_text("a\nb\n", encoding="utf-8")
        git(repo, "commit", "-q", "-am", "work")
        fp5 = gm.progress_fingerprint(str(repo))
        check("V-PFP-COMMIT-MOVES", fp5 != fp4, "a commit still counts")

        bare = tmp / "noplanning"
        bare.mkdir()
        git(bare, "init", "-q")
        (bare / "a.txt").write_text("a\n", encoding="utf-8")
        git(bare, "add", "a.txt")
        git(bare, "commit", "-q", "-m", "init")
        check("V-PFP-NO-PLANNING-EMPTY", gm._planning_artifacts(str(bare)) == "",
              "no .planning/ adds nothing to the hash")
        check("V-PFP-NOT-GIT-UNMEASURED", gm.progress_fingerprint(str(tmp)) is None,
              "outside git stays unmeasured")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"PFP_PASS={passes}/{passes + fails}  threshold=8/8")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
