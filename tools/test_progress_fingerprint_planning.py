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
        (repo / "app.py").write_text("a\n", encoding="utf-8")
        git(repo, "add", "app.py")
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

        (repo / "app.py").write_text("a\nb\n", encoding="utf-8")
        git(repo, "commit", "-q", "-am", "work")
        fp5 = gm.progress_fingerprint(str(repo))
        check("V-PFP-COMMIT-MOVES", fp5 != fp4, "a commit still counts")

        # Bookkeeping commits (measured 2026-10-23, GEX44 m-95e10a5bb636 -> m-01e5d5509ee6): ~54 epochs each
        # committed only a TRACKED STATE.md + RESUMPTION.md ("no Owner input, no unit") and every one read as
        # progress, because HEAD's tree moved. Tracked .planning here, as on that branch.
        trk = tmp / "tracked"
        trk.mkdir()
        git(trk, "init", "-q")
        ws = trk / ".planning" / "workstreams" / "ws"
        ws.mkdir(parents=True)
        (trk / "app.py").write_text("a\n", encoding="utf-8")
        (ws / "STATE.md").write_text("s0\n", encoding="utf-8")
        (ws / "RESUMPTION.md").write_text("r0\n", encoding="utf-8")
        git(trk, "add", "-A")
        git(trk, "commit", "-q", "-m", "init")
        t0 = gm.progress_fingerprint(str(trk))
        (ws / "STATE.md").write_text("s1 epoch 24 - no Owner input, no unit\n", encoding="utf-8")
        t1 = gm.progress_fingerprint(str(trk))
        check("V-PFP-TRACKED-STATE-DIRT-STILL", t1 == t0, "an uncommitted tracked STATE.md edit is not progress")
        (ws / "RESUMPTION.md").write_text("r1 longer resumption text\n", encoding="utf-8")
        git(trk, "commit", "-q", "-am", "STATE + RESUMPTION epoch 24 - no Owner input, no unit")
        t2 = gm.progress_fingerprint(str(trk))
        check("V-PFP-BOOKKEEPING-COMMIT-STILL", t2 == t0, "a commit of only STATE.md + RESUMPTION.md is not progress")
        (ws / "PLAN-01.md").write_text("a real plan\n", encoding="utf-8")
        git(trk, "add", "-A")
        git(trk, "commit", "-q", "-m", "plan")
        t3 = gm.progress_fingerprint(str(trk))
        check("V-PFP-TRACKED-PLAN-MOVES", t3 != t2, "a committed plan under .planning still counts")
        (trk / "app.py").write_text("a\nwork\n", encoding="utf-8")
        t4 = gm.progress_fingerprint(str(trk))
        check("V-PFP-PRODUCT-DIRT-MOVES", t4 != t3, "an uncommitted product edit still counts")
        os.environ["CPP_PROGRESS_BOOKKEEPING"] = "count"
        try:
            k0 = gm.progress_fingerprint(str(trk))
            (ws / "STATE.md").write_text("s2 kill switch\n", encoding="utf-8")
            k1 = gm.progress_fingerprint(str(trk))
            check("V-PFP-KILL-SWITCH-COUNTS", k1 != k0, "CPP_PROGRESS_BOOKKEEPING=count restores the old reading")
        finally:
            os.environ.pop("CPP_PROGRESS_BOOKKEEPING", None)

        # Claim 8 (phase 9): the fingerprint reads an allow-listed content set. Each noise case must leave it
        # unmoved; each work case must move it (a blind fingerprint already caused a false no_progress halt).
        def commit(repo_, msg):
            git(repo_, "add", "-A")
            git(repo_, "commit", "-q", "-m", msg)

        def moved(repo_, act):
            before = gm.progress_fingerprint(str(repo_))
            act()
            after = gm.progress_fingerprint(str(repo_))
            return before is not None and after is not None and before != after

        al = tmp / "allow"
        (al / ".planning" / "workstreams" / "x").mkdir(parents=True)
        git(al, "init", "-q")
        (al / "tools").mkdir()
        (al / "tools" / "t.py").write_text("v1\n", encoding="utf-8")
        (al / ".planning" / "workstreams" / "x" / "STATE.md").write_text("s0\n", encoding="utf-8")
        commit(al, "base")

        def w(path, text):
            return lambda: (al / path).write_text(text, encoding="utf-8")

        def w_commit(path, text, msg):
            return lambda: (w(path, text)(), commit(al, msg))

        noise = {
            "root RESUMPTION_FILE.md commit": w_commit("RESUMPTION_FILE.md", "next\n", "rf"),
            "tracked junk.txt commit": w_commit("junk.txt", os.urandom(8).hex(), "junk"),
            "untracked pytest.log": w("pytest.log", "3 passed\n"),
            "nested RESUMPTION_FILE.md dirty": w("tools/RESUMPTION_FILE.md", "x\n"),
            "untracked .log in .planning": w(".planning/workstreams/x/run.log", "x\n"),
        }
        for name, act in noise.items():
            check("V-PFP-ALLOWLIST-NOISE-QUIET", not moved(al, act), name)
        work = {
            "code under tools/ edited": w("tools/t.py", "v2\n"),
            "new untracked source file": w("tools/new_mod.py", "x = 1\n"),
            "committed source file": w_commit("tools/c.py", "y = 2\n", "code"),
            "PLAN artifact": w(".planning/workstreams/x/01-01-PLAN.md", "# plan\n"),
            "SUMMARY artifact": w(".planning/workstreams/x/01-01-SUMMARY.md", "# sum\n"),
            "VERIFICATION artifact": w(".planning/workstreams/x/01-VERIFICATION.md", "# ver\n"),
        }
        for name, act in work.items():
            check("V-PFP-ALLOWLIST-WORK-MOVES", moved(al, act), name)
        os.environ["CPP_PROGRESS_BOOKKEEPING"] = "count"
        try:
            check("V-PFP-ALLOWLIST-KILL-SWITCH", moved(al, w("scratch.log", "x\n")),
                  "count mode still sees a log the allow-list ignores (the control fires)")
        finally:
            os.environ.pop("CPP_PROGRESS_BOOKKEEPING", None)

        bare = tmp / "noplanning"
        bare.mkdir()
        git(bare, "init", "-q")
        (bare / "app.py").write_text("a\n", encoding="utf-8")
        git(bare, "add", "app.py")
        git(bare, "commit", "-q", "-m", "init")
        check("V-PFP-NO-PLANNING-EMPTY", gm._planning_artifacts(str(bare)) == "",
              "no .planning/ adds nothing to the hash")
        check("V-PFP-NOT-GIT-UNMEASURED", gm.progress_fingerprint(str(tmp)) is None,
              "outside git stays unmeasured")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"PFP_PASS={passes}/{passes + fails}  threshold=25/25")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
