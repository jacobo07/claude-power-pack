#!/usr/bin/env python
"""V-MC-* gates for tools/manifest_commit.py, in a throwaway git repo: a failing test command must prevent the commit."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE / "manifest_commit.py"
GIT = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
       "GIT_COMMITTER_EMAIL": "t@t", "GIT_PAGER": "cat", "GIT_TERMINAL_PROMPT": "0"}
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def git(repo, *args):
    p = subprocess.run([GIT, "-C", str(repo), "-c", "commit.gpgsign=false", *args], capture_output=True, text=True,
                       encoding="utf-8", env=ENV)
    return p.stdout.strip()


def drive(manifest, log):
    m = log.parent / "manifest.json"
    m.write_text(json.dumps(manifest), encoding="utf-8")
    return subprocess.run([sys.executable, str(TOOL), "--manifest", str(m), "--log", str(log)], capture_output=True,
                          text=True, encoding="utf-8", env=ENV).returncode


def main() -> int:
    d = Path(tempfile.mkdtemp(prefix="mc-test-"))
    repo = d / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    (repo / "base.txt").write_text("base", encoding="utf-8")
    git(repo, "add", "base.txt")
    git(repo, "commit", "-q", "-m", "base")
    head0 = git(repo, "rev-parse", "HEAD")
    (d / "ok.py").write_text("raise SystemExit(0)", encoding="utf-8")
    (d / "bad.py").write_text("raise SystemExit(1)", encoding="utf-8")
    ok, bad = f"{sys.executable} {d / 'ok.py'}", f"{sys.executable} {d / 'bad.py'}"
    (repo / "a.txt").write_text("a", encoding="utf-8")
    (repo / "b.txt").write_text("b", encoding="utf-8")
    (repo / "unlisted.txt").write_text("u", encoding="utf-8")
    log = d / "log.jsonl"

    rc = drive([{"repo": str(repo), "paths": ["a.txt"], "test_cmds": [ok, bad], "message": "add a\n\nCo-Authored-By: x"},
                {"repo": str(repo), "paths": ["b.txt"], "test_cmds": [ok], "message": "add b"}], log)
    steps = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()]
    check("V-MC-FAILING-TEST-PREVENTS-COMMIT", rc == 3 and git(repo, "rev-parse", "HEAD") == head0
          and "a.txt" not in git(repo, "ls-files"), f"rc={rc}")
    check("V-MC-FAILURE-LOGGED-AND-RUN-STOPPED", any(s["step"] == "test" and s["rc"] == 1 for s in steps)
          and any(s["step"] == "stopped" for s in steps) and not any(s["step"] == "committed" for s in steps)
          and "b.txt" not in git(repo, "ls-files"))

    log2 = d / "sub" / "log.jsonl"
    log2.parent.mkdir()
    rc = drive([{"repo": str(repo), "paths": ["a.txt"], "test_cmds": [ok], "message": "add a\n\nCo-Authored-By: x"},
                {"repo": str(repo), "paths": ["b.txt"], "test_cmds": [ok], "message": "add b"}], log2)
    files = git(repo, "ls-files").split()
    check("V-MC-PASSING-COMMITS-ONLY-LISTED-PATHS", rc == 0 and "a.txt" in files and "b.txt" in files
          and "unlisted.txt" not in files, str(files))
    check("V-MC-ONE-COMMIT-PER-ENTRY-SUBJECT-AND-TRAILER",
          git(repo, "rev-list", "--count", f"{head0}..HEAD") == "2" and git(repo, "log", "-1", "--format=%s") == "add b"
          and "Co-Authored-By: x" in git(repo, "log", "-2", "--format=%B"))
    check("V-MC-LOG-HAS-COMMITTED-STEPS", sum(json.loads(x)["step"] == "committed"
          for x in log2.read_text(encoding="utf-8").splitlines()) == 2)

    log3 = d / "sub3" / "log.jsonl"
    log3.parent.mkdir()
    rc = drive([{"repo": str(repo), "paths": ["a.txt"], "test_cmds": [ok], "message": "again"}], log3)
    check("V-MC-NOTHING-TO-COMMIT-IS-NOOP", rc == 0 and git(repo, "rev-list", "--count", f"{head0}..HEAD") == "2")

    print(f"MC_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
