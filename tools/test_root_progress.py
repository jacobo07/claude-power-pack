#!/usr/bin/env python3
"""V-PROG-* gates: progress v1 per root (plan s12 commit 7, RCA s17).

"Commit issued by this root" is not usable: the golden incident's commits were
issued through shells and wrappers the first instrument did not see (0 found,
7 real). Progress v1 instead joins the files a root WROTE to commits in the repo
it worked in (its cwd), in-span or later, and reads its test runs. No signal is
UNSETTLED, never WASTE. Real git repo, real commits; hermetic; no model call."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import root_progress as rp  # noqa: E402
import usage_index as ux  # noqa: E402

PASS = FAIL = 0
T0 = datetime(2026, 10, 1, tzinfo=timezone.utc).timestamp()


def ok(gate, cond, ev):
    global PASS, FAIL
    PASS += bool(cond)
    FAIL += not cond
    print(f"  {'PASS' if cond else 'FAIL'} {gate}: {ev}")


def iso(h):
    return datetime.fromtimestamp(T0 + h * 3600, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def git(repo: Path, *args, at_h: float | None = None):
    env = dict(os.environ)
    if at_h is not None:
        d = datetime.fromtimestamp(T0 + at_h * 3600, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+0000")
        env.update(GIT_AUTHOR_DATE=d, GIT_COMMITTER_DATE=d)
    subprocess.run([rp.GIT, "-C", str(repo), *args], check=True, capture_output=True, env=env)


def line(o: dict) -> str:
    return json.dumps(o) + "\n"


def prompt(pid, h, cwd):
    return line({"type": "user", "promptId": pid, "timestamp": iso(h), "sessionId": "S1",
                 "cwd": str(cwd), "origin": {"kind": "human"}})


def tool(mid, h, cwd, uses):
    return line({"type": "assistant", "timestamp": iso(h), "sessionId": "S1", "cwd": str(cwd),
                 "requestId": "r" + mid,
                 "message": {"id": mid, "model": "claude-opus-5-5", "content": uses,
                             "usage": {"input_tokens": 1, "cache_read_input_tokens": 10,
                                       "cache_creation_input_tokens": 0, "output_tokens": 1}}})


def result(h, pid, tuid, text, err=False):
    c = {"type": "tool_result", "tool_use_id": tuid, "content": text}
    if err:
        c["is_error"] = True
    return line({"type": "user", "promptId": pid, "timestamp": iso(h), "sessionId": "S1",
                 "message": {"role": "user", "content": [c]}})


def write(tid, path):
    return {"type": "tool_use", "id": tid, "name": "Write", "input": {"file_path": str(path)}}


def bash(tid, cmd):
    return {"type": "tool_use", "id": tid, "name": "Bash", "input": {"command": cmd}}


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        git(repo, "init", "-q")
        git(repo, "config", "user.email", "t@example.invalid")
        git(repo, "config", "user.name", "t")
        (repo / "seed.txt").write_text("x", encoding="utf-8")
        git(repo, "add", "seed.txt")
        git(repo, "commit", "-qm", "seed", at_h=0.5)
        repo2 = Path(td) / "repo2"
        repo2.mkdir()
        git(repo2, "init", "-q")
        git(repo2, "config", "user.email", "t@example.invalid")
        git(repo2, "config", "user.name", "t")

        proj = Path(td) / "projects" / "C--p"
        proj.mkdir(parents=True)
        # P1 writes a.py, runs a green and a red test, its file is committed in span.
        # P2 writes b.py, never committed, runs nothing: UNSETTLED.
        # P3 writes c.py, committed only LATER (after its span).
        (proj / "S1.jsonl").write_text(
            prompt("P1", 1.0, repo)
            + tool("m1", 1.01, repo, [write("w1", repo / "a.py")])
            + tool("m2", 1.02, repo, [bash("b1", "python -m pytest tests/test_a.py -q")])
            + result(1.03, "P1", "b1", "...\n3 passed in 0.4s")
            + tool("m3", 1.04, repo, [bash("b2", "python tools/test_x.py")])
            + result(1.05, "P1", "b2", "X_PASS=4/5  threshold=5/5", err=True)
            + tool("m4", 1.06, repo, [bash("b3", "git status")])
            + result(1.07, "P1", "b3", "clean")
            + tool("m5", 1.071, repo, [{"type": "tool_use", "id": "ps1", "name": "PowerShell",
                                        "input": {"command": "& $py tools\\test_y.py"}}])
            + result(1.072, "P1", "ps1", "Y_PASS=6/6  threshold=6/6")
            + prompt("P2", 2.0, repo)
            + tool("n1", 2.01, repo, [write("w2", repo / "b.py")])
            + prompt("P3", 3.0, repo)
            + tool("o1", 3.01, repo, [write("w3", repo / "c.py")])
            # P4 stands in `repo` but writes into `repo2` (RCA s17: a PP cwd editing
            # another worktree). Its commit lives only in repo2.
            + prompt("P4", 6.0, repo)
            + tool("q1", 6.01, repo, [write("w4", repo2 / "d.py")]),
            encoding="utf-8")
        for name in ("a.py", "b.py", "c.py"):
            (repo / name).write_text(name, encoding="utf-8")
        git(repo, "add", "a.py")
        git(repo, "commit", "-qm", "a", at_h=1.08)
        git(repo, "add", "c.py")
        git(repo, "commit", "-qm", "c", at_h=5.0)
        (repo2 / "d.py").write_text("d", encoding="utf-8")
        git(repo2, "add", "d.py")
        git(repo2, "commit", "-qm", "d", at_h=6.02)

        con = ux.connect(Path(td) / "ix.sqlite")
        try:
            r = ux.refresh(con, proj.parent, deadline_s=30)
            ok("V-PROG-REFRESH", r["status"] == "OK", json.dumps(r))
            p1 = rp.root_progress(con, "P1")
            ok("V-PROG-WRITES", p1["writes"] == 1, f"P1 writes={p1['writes']}")
            ok("V-PROG-COMMIT-IN-SPAN", p1["commits_in_span"] == 1 and p1["commits_later"] == 0,
               f"in_span={p1['commits_in_span']} later={p1['commits_later']}")
            ok("V-PROG-TESTS", p1["tests"] == {"GREEN": 2, "RED": 1},
               f"tests={p1['tests']} (pytest '3 passed' green; X_PASS=4/5 red; PowerShell "
               f"Y_PASS=6/6 green; git status not a test)")
            ok("V-PROG-ADVANCED", p1["state"] == "ADVANCED", f"state={p1['state']}")
            p4 = rp.root_progress(con, "P4")
            ok("V-PROG-OTHER-REPO", p4["commits_in_span"] == 1 and p4["state"] == "ADVANCED"
               and len(p4["repos"]) == 2,
               f"P4 (cwd repo, wrote repo2): in_span={p4['commits_in_span']} repos={len(p4['repos'])}")
            p2 = rp.root_progress(con, "P2")
            ok("V-PROG-UNSETTLED", p2["state"] == "UNSETTLED" and p2["writes"] == 1
               and p2["commits_in_span"] == p2["commits_later"] == 0,
               f"P2 state={p2['state']} (wrote, nothing committed, no test: never WASTE)")
            p3 = rp.root_progress(con, "P3")
            ok("V-PROG-LATER", p3["commits_later"] == 1 and p3["commits_in_span"] == 0
               and p3["state"] == "ADVANCED_LATER", f"P3 later={p3['commits_later']} state={p3['state']}")
            ok("V-PROG-BLIND-SPOTS", "goal_log" in p1["blind_spots"],
               f"blind spots named: {sorted(p1['blind_spots'])}")
            ok("V-PROG-UNKNOWN-PROMPT", rp.root_progress(con, "nope")["state"] == "UNKNOWN_PROMPT",
               "an unknown root is UNKNOWN_PROMPT, not UNSETTLED")
            # A root whose cwd is not a repository cannot be judged on commits.
            ok("V-PROG-NO-REPO", rp.repo_top(Path(td)) is None, "a non-repo cwd resolves to None")
        finally:
            con.close()

    total = PASS + FAIL
    print(f"ROOT_PROGRESS_PASS={PASS}/{total}  threshold={total}/{total}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
