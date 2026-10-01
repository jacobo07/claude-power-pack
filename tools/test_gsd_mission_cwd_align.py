#!/usr/bin/env python
"""V-MCA-* gates for gsd_mission.align_cwd and its call in supervise().

Origin (measured 2026-09-30, Brand #001 m-cdd8fc64ed65): a handback advanced only the mission
worktree; the cwd stayed on the seed, the renewed worker launched there, read a stale roadmap and
redid Phase 1 on a branch without 73 commits of finished work.

Real git repositories in a temp dir, no fixtures standing in for git.
Run: python tools/test_gsd_mission_cwd_align.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import gsd_mission as gm  # noqa: E402

GIT = os.environ.get("CPP_GIT_EXE") or r"C:\Program Files\Git\cmd\git.exe"
if not Path(GIT).exists():
    GIT = "git"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
       "GIT_COMMITTER_EMAIL": "t@t"}

passes = 0
fails = 0


def _ok(gate, msg):
    global passes
    passes += 1
    print(f"[PASS] {gate}: {msg}")


def _fail(gate, msg):
    global fails
    fails += 1
    print(f"[FAIL] {gate}: {msg}")


def git(path, *args):
    r = subprocess.run([GIT, "-C", str(path), *args], capture_output=True, text=True, env=ENV, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(f"git {args}: {r.stderr}")
    return r.stdout.strip()


def commit(path, name, text):
    (Path(path) / name).write_text(text, encoding="utf-8")
    git(path, "add", name)
    git(path, "commit", "-q", "-m", name)
    return git(path, "rev-parse", "HEAD")


def repo(root: Path):
    """cwd checkout on `program` + a worktree `wt` on branch `work`, both at the seed."""
    cwd = root / "repo"
    cwd.mkdir(parents=True)
    git(cwd, "init", "-q", "-b", "program")
    commit(cwd, "seed.txt", "seed")
    wt = root / "wt"
    git(cwd, "worktree", "add", "-q", "-b", "work", str(wt))
    return cwd, wt


def head(path):
    return git(path, "rev-parse", "HEAD")


def check(gate, cond, msg):
    (_ok if cond else _fail)(gate, msg)


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)

        # 1 same path / no work_dir
        cwd, wt = repo(t / "c1")
        r1, r2 = gm.align_cwd(str(cwd), str(cwd)), gm.align_cwd(str(cwd), None)
        check("V-MCA-SAME", r1["status"] == "same" and r2["status"] == "same", f"{r1['status']}, {r2['status']}")

        # 2 aligned
        check("V-MCA-ALIGNED", gm.align_cwd(str(cwd), str(wt))["status"] == "aligned", "both at seed")

        # 3 behind + clean -> fast-forward, cwd now carries the work
        cwd, wt = repo(t / "c3")
        w = commit(wt, "phase1.txt", "done")
        r = gm.align_cwd(str(cwd), str(wt))
        check("V-MCA-FF", r["status"] == "fast_forwarded" and head(cwd) == w,
              f"status={r['status']} cwd={head(cwd)[:8]} work={w[:8]}")

        # 4 behind + dirty tracked file -> blocking, cwd untouched
        cwd, wt = repo(t / "c4")
        commit(wt, "phase1.txt", "done")
        before = head(cwd)
        (cwd / "seed.txt").write_text("local edit", encoding="utf-8")
        r = gm.align_cwd(str(cwd), str(wt))
        check("V-MCA-DIRTY", r["status"] == "behind_dirty" and head(cwd) == before
              and (cwd / "seed.txt").read_text(encoding="utf-8") == "local edit",
              f"status={r['status']}, head unchanged={head(cwd) == before}")

        # 5 diverged -> blocking (the Brand #001 shape)
        cwd, wt = repo(t / "c5")
        commit(wt, "handback.txt", "73 commits")
        commit(cwd, "redo.txt", "phase 1 again")
        before = head(cwd)
        r = gm.align_cwd(str(cwd), str(wt))
        check("V-MCA-DIVERGED", r["status"] == "diverged" and head(cwd) == before,
              f"status={r['status']}")

        # 6 cwd ahead (already contains the work) -> no action
        cwd, wt = repo(t / "c6")
        commit(cwd, "more.txt", "x")
        r = gm.align_cwd(str(cwd), str(wt))
        check("V-MCA-AHEAD", r["status"] == "ahead", f"status={r['status']}")

        # 7 unrelated repository -> not ours to judge
        cwd, _ = repo(t / "c7a")
        other, _ = repo(t / "c7b")
        r = gm.align_cwd(str(cwd), str(other))
        check("V-MCA-UNRELATED", r["status"] == "unrelated", f"status={r['status']}")

        # 8 blocking set is exactly the three refusals
        check("V-MCA-BLOCKING-SET", set(gm.CWD_ALIGN_BLOCKING) == {"behind_dirty", "diverged", "unreadable"}
              and "fast_forwarded" not in gm.CWD_ALIGN_BLOCKING, str(gm.CWD_ALIGN_BLOCKING))

    # 9 structural: supervise aligns the cwd BEFORE it launches a worker
    src = Path(gm.__file__).read_text(encoding="utf-8")
    sup = src[src.index("def supervise("):]
    a, l = sup.find('align_cwd(rec["cwd"]'), sup.find('row["launch"] = launch_worker(')
    check("V-MCA-SUPERVISE-ORDER", 0 <= a < l, f"align at {a}, launch at {l}")

    print(f"MCA_PASS={passes}/{passes + fails}  threshold=9/9")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
