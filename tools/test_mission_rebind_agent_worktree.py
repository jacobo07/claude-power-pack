#!/usr/bin/env python
"""V-RB-* gates for T1 F4: detect_rebind never selects a harness `agent-*` isolation worktree, and prefers the
worktree that holds the worker's own cwd.

Measured 2026-10-23 (m-260aa89142c8, 07:59Z): the auto-rebind chose subagent worktree agent-a33215aa, because it
was added after bound_at and named in tool text, the two conditions detect_rebind checks. Driven from both poles
on a real git repository with real worktrees: an agent worktree alone is excluded, while an ordinary worktree under
the same conditions is still a candidate; and of two candidates the worker's cwd decides, while without a cwd
both stay (no invented choice).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TMP = Path(tempfile.mkdtemp(prefix="mission-rebind-f4-"))
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
import mission_binding as mb  # noqa: E402
from gsd_mission import resolve_exe  # noqa: E402

GIT = resolve_exe("git") or "git"
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def git(*args, cwd):
    subprocess.run([GIT, "-C", str(cwd), *args], check=True, capture_output=True, text=True)


def transcript(name: str, paths: list[Path], cwd: Path | None) -> Path:
    ts = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(time.time() + 5))
    rows = [{"type": "assistant", "timestamp": ts, "message": {"content": [
        {"type": "tool_use", "id": f"t{i}", "name": "Bash", "input": {"command": f"ls {p.as_posix()}"}}]}}
        for i, p in enumerate(paths)]
    if cwd is not None:
        rows.append({"type": "user", "timestamp": ts, "cwd": str(cwd), "message": {"content": "x"}})
    p = TMP / f"{name}.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return p


def main() -> int:
    repo = TMP / "repo"
    repo.mkdir()
    git("init", "-q", cwd=repo)
    git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "root", cwd=repo)
    since = time.time() - 60
    wt = {n: repo / ".claude" / "worktrees" / n for n in ("agent-a33215aa", "exec2", "exec3")}
    for n, p in wt.items():
        git("worktree", "add", "-q", "-b", f"b-{n}", str(p), cwd=repo)
    rec = {"mission_id": "m-rb", "cwd": str(repo), "created_at": since}

    # 1. the T1 shape: only the agent worktree is new and named -> no candidate, and it is reported as excluded.
    d = mb.detect_rebind(rec, transcript("t1", [wt["agent-a33215aa"]], None))
    check("V-RB-AGENT-WORKTREE-EXCLUDED", d is not None and d["candidates"] == []
          and len(d["excluded_agent_worktrees"]) == 1, str(d)[:200])
    d = mb.detect_rebind(rec, transcript("ctl", [wt["exec2"]], None))
    check("V-RB-CONTROL-ORDINARY-WORKTREE-STILL-CANDIDATE", d and len(d["candidates"]) == 1
          and mb._norm(d["candidates"][0]) == mb._norm(wt["exec2"]), str(d)[:200])
    check("V-RB-PREDICATE", mb.is_agent_worktree(str(wt["agent-a33215aa"])) and not mb.is_agent_worktree(str(wt["exec2"]))
          and not mb.is_agent_worktree(str(repo / "agent-x")), "only <repo>/.claude/worktrees/agent-*")

    # 2. two ordinary candidates: the worker's own cwd picks one; without a cwd both stay.
    both = [wt["exec2"], wt["exec3"], wt["agent-a33215aa"]]
    d = mb.detect_rebind(rec, transcript("cwd", both, wt["exec3"] / "src"))
    check("V-RB-WORKER-CWD-PREFERRED", d and len(d["candidates"]) == 1
          and mb._norm(d["candidates"][0]) == mb._norm(wt["exec3"]), str(d)[:200])
    d = mb.detect_rebind(rec, transcript("nocwd", both, None))
    check("V-RB-CONTROL-NO-CWD-NO-INVENTED-CHOICE", d and len(d["candidates"]) == 2, str(d)[:200])
    d = mb.detect_rebind(rec, transcript("agentcwd", both, wt["agent-a33215aa"]))
    check("V-RB-AGENT-CWD-NEVER-CHOSEN", d and len(d["candidates"]) == 2
          and all(not mb.is_agent_worktree(c) for c in d["candidates"]), str(d)[:200])
    check("V-RB-UNREADABLE-TRANSCRIPT-UNJUDGED", mb.detect_rebind(rec, TMP / "absent.jsonl") is None)

    print(f"REBIND_F4_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    shutil.rmtree(TMP, ignore_errors=True)
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
