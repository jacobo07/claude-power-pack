#!/usr/bin/env python3
"""root_progress.py -- progress v1 per root (plan s12 commit 7, RCA s17).

What did a root's spend move? v1 reads only facts the transcripts and git hold:

  writes   files the root wrote (Write / Edit / MultiEdit / NotebookEdit file paths)
  commits  commits in the repo the root WORKED in (each line's cwd, resolved to its
           git top-level), on any branch, that changed a written file: in span
           (by the root's last call + ACTIVE_GAP_S) or later (within LATER_S)
  tests    the root's test runs (Bash commands that look like a test runner) and
           their verdict from the tool_result: GREEN / RED / UNKNOWN

state: ADVANCED (a commit in span, or a green test), ADVANCED_LATER (only a later
commit), UNSETTLED (none of these). UNSETTLED is not WASTE: exploration, review and
planning leave no commit, and v1 cannot see their value either way.

Why not "commits issued by this root": RCA s17 measured that instrument at 0
commits where full-text matching found 7 (commits go through shells, wrappers and
other panes). Attribution here is FILE OVERLAP, not authorship: another writer
committing the same file in span is counted too. That and every other blind spot
is named in the output, never folded into a number.

Data: the root's transcripts come from the usage index (main files by the calls'
prompt_id, subagent files by spawn ancestry, nested included); they are read
on demand, so no history re-index is needed. No model call.

CLI:
  prompt PROMPT_ID
  top --from ISO --to ISO [--n 20]   costliest roots first, with surface coverage
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import fanout_ledger as fl  # noqa: E402
import usage_index as ux  # noqa: E402

GIT = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"
WRITE_TOOLS = {"Write": "file_path", "Edit": "file_path", "MultiEdit": "file_path",
               "NotebookEdit": "notebook_path"}
LATER_S = 24 * 3600
# Every tool that runs a shell command. On Windows hosts tests run through PowerShell;
# a Bash-only reader measured 0 test runs on roots that ran dozens.
SHELL_TOOLS = ("Bash", "PowerShell")
TEST_CMD = re.compile(r"(?i)\b(pytest|unittest|vitest|jest|npm\s+(run\s+)?test|pnpm\s+(run\s+)?test|"
                      r"mix\s+test|go\s+test|cargo\s+test)\b|test_[\w-]+\.(py|js|ts)\b")
PASS_LINE = re.compile(r"_PASS=(\d+)/(\d+)")
PASSED = re.compile(r"\b(\d+) passed\b")
FAILED_N = re.compile(r"\b(\d+) (failed|errors?)\b")


def _text(body) -> str:
    if isinstance(body, list):
        return " ".join(x.get("text", "") for x in body if isinstance(x, dict))
    return str(body or "")


def test_verdict(text: str, is_error: bool) -> str:
    """GREEN / RED / UNKNOWN from a test run's output. A quiet or truncated output
    with no count is UNKNOWN, never GREEN."""
    passes = PASS_LINE.findall(text)
    failed = sum(int(n) for n, _ in FAILED_N.findall(text))
    if is_error or failed or any(int(a) < int(b) for a, b in passes):
        return "RED"
    if PASSED.search(text) or any(int(a) == int(b) > 0 for a, b in passes):
        return "GREEN"
    return "UNKNOWN"


def repo_top(cwd) -> Path | None:
    try:
        r = subprocess.run([GIT, "-C", str(cwd), "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    return Path(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None


def _norm(p) -> str:
    return os.path.normcase(os.path.normpath(str(p)))


def root_files(con, prompt_id: str) -> dict:
    """{transcript: is_main} for one root: main transcripts holding its calls, then
    every subagent transcript reachable through spawns, nested included."""
    mains = [r[0] for r in con.execute(
        "SELECT DISTINCT file FROM calls WHERE prompt_id=? AND is_sub=0", (prompt_id,))]
    files = {f: True for f in mains}
    frontier = list(mains)
    while frontier:
        f = frontier.pop()
        q = ("SELECT a.file FROM spawns s JOIN subagents a ON a.tool_use_id = s.tool_use_id "
             "WHERE s.file=?" + (" AND s.prompt_id=?" if files[f] else ""))
        for (sub,) in con.execute(q, (f, prompt_id) if files[f] else (f,)):
            if sub not in files:
                files[sub] = False
                frontier.append(sub)
    return files


def _scan(path: str, prompt_id: str | None) -> dict:
    """Writes, cwds and test runs in one transcript. For a main transcript only the
    lines under `prompt_id` count (a session holds many prompts)."""
    out = {"writes": set(), "cwds": set(), "tests": [], "lines": 0}
    pending: dict = {}
    cur = None
    try:
        fh = open(path, encoding="utf-8", errors="replace")
    except OSError:
        out["unreadable"] = True
        return out
    with fh:
        for raw in fh:
            try:
                o = json.loads(raw)
            except ValueError:
                continue
            if not isinstance(o, dict):
                continue
            if o.get("type") == "user" and o.get("promptId"):
                cur = o["promptId"]
            if prompt_id is not None and cur != prompt_id:
                continue
            out["lines"] += 1
            if o.get("cwd"):
                out["cwds"].add(o["cwd"])
            msg = o.get("message") if isinstance(o.get("message"), dict) else {}
            content = msg.get("content") if isinstance(msg.get("content"), list) else []
            for c in content:
                if not isinstance(c, dict):
                    continue
                if c.get("type") == "tool_use":
                    inp = c.get("input") if isinstance(c.get("input"), dict) else {}
                    key = WRITE_TOOLS.get(c.get("name"))
                    if key and inp.get(key):
                        p = Path(inp[key])
                        if not p.is_absolute() and o.get("cwd"):
                            p = Path(o["cwd"]) / p
                        out["writes"].add(_norm(p))
                    elif (c.get("name") in SHELL_TOOLS
                          and TEST_CMD.search(str(inp.get("command", "")))):
                        pending[c.get("id")] = True
                elif c.get("type") == "tool_result" and c.get("tool_use_id") in pending:
                    pending.pop(c["tool_use_id"])
                    out["tests"].append(test_verdict(_text(c.get("content")), bool(c.get("is_error"))))
    out["tests"].extend("UNKNOWN" for _ in pending)          # ran, no result recorded
    return out


def _commits(top: Path, since: float, until: float) -> list[tuple[str, float, set]]:
    def iso(t):
        return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    r = subprocess.run([GIT, "-C", str(top), "log", "--all", f"--since={iso(since)}",
                        f"--until={iso(until)}", "--name-only", "--format=%x00%H %ct"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    out = []
    for block in r.stdout.split("\x00")[1:]:
        lines = [x for x in block.splitlines() if x.strip()]
        if not lines:
            continue
        sha, ct = lines[0].split()
        out.append((sha, float(ct), {_norm(top / f) for f in lines[1:]}))
    return out


def root_progress(con, prompt_id: str) -> dict:
    span = con.execute("SELECT min(ts), max(ts) FROM calls WHERE prompt_id=? AND is_sub=0",
                       (prompt_id,)).fetchone()
    if not span or span[0] is None:
        return {"prompt": prompt_id, "state": "UNKNOWN_PROMPT"}
    files = root_files(con, prompt_id)
    subs = [f for f, main in files.items() if not main]
    if subs:
        q = f"SELECT max(ts) FROM calls WHERE file IN ({','.join('?' * len(subs))})"
        end = max(span[1], con.execute(q, subs).fetchone()[0] or span[1])
    else:
        end = span[1]
    start = span[0]
    writes, cwds, tests, unreadable = set(), set(), [], 0
    for f, main in files.items():
        s = _scan(f, prompt_id if main else None)
        writes |= s["writes"]
        cwds |= s["cwds"]
        tests += s["tests"]
        unreadable += bool(s.get("unreadable"))
    # The workspace is where the root WROTE, not only where it stood: a session whose
    # cwd is one repo can edit another (RCA s17: a PP cwd editing an InfinityOps
    # worktree). So repos come from each written file's directory as well as the cwds.
    tops, no_repo = {}, []
    for c in sorted(cwds):
        t = repo_top(c)
        if t is None:
            no_repo.append(c)
        else:
            tops[_norm(t)] = t
    outside = 0
    dir_top: dict = {}
    for w in writes:
        d = os.path.dirname(w)
        if d not in dir_top:
            dir_top[d] = repo_top(d) if os.path.isdir(d) else None
        if dir_top[d] is None:
            outside += 1
        else:
            tops.setdefault(_norm(dir_top[d]), dir_top[d])
    in_span = later = 0
    touched = set()
    grace = fl.ACTIVE_GAP_S
    for t in tops.values():
        for sha, ct, changed in _commits(t, start - grace, end + LATER_S):
            hit = changed & writes
            if not hit:
                continue
            touched |= hit
            if ct <= end + grace:
                in_span += 1
            else:
                later += 1
    tc = Counter(tests)
    state = ("ADVANCED" if in_span or tc.get("GREEN") else
             "ADVANCED_LATER" if later else "UNSETTLED")
    blind = {"goal_log": "goal events carry no session or prompt id: not attributable",
             "attribution": "file overlap, not authorship: another writer's commit counts too",
             "tests_unknown": tc.get("UNKNOWN", 0)}
    if no_repo:
        blind["no_repo"] = no_repo
    if outside:
        blind["writes_outside_repo"] = outside
    if unreadable:
        blind["unreadable_transcripts"] = unreadable
    return {"prompt": prompt_id, "span": [ux._iso(start), ux._iso(end)],
            "transcripts": len(files), "repos": sorted(str(t) for t in tops.values()),
            "writes": len(writes), "written_committed": len(touched),
            "commits_in_span": in_span, "commits_later": later,
            "tests": dict(tc), "state": state, "blind_spots": blind}


def top(con, start: float, end: float, n: int = 20) -> dict:
    """Progress of the costliest roots in (start, end]. Coverage is their share of
    the window's surface: the tail is judged first, the rest stays unmeasured."""
    sh = fl.shape(con, start, end)
    roots = sh["roots"][:n]
    rows = []
    for r in roots:
        p = root_progress(con, r["prompt"])
        rows.append({"prompt": r["prompt"], "root": r["root"], "project": r["project"],
                     "area": r["area"], "surface": r["surface"], **{k: p.get(k) for k in (
                         "state", "writes", "written_committed", "commits_in_span",
                         "commits_later", "tests", "repos")},
                     "blind": {k: v for k, v in p.get("blind_spots", {}).items()
                               if k not in ("goal_log", "attribution")}})
    covered = sum(r["surface"] for r in roots)
    states = Counter(r["state"] for r in rows)
    return {"window": sh["window"], "roots_judged": len(rows), "roots_total": len(sh["roots"]),
            "surface_coverage": round(covered / sh["check"]["window_surface"], 4)
            if sh["check"]["window_surface"] else None,
            "states": dict(states),
            "surface_by_state": {s: sum(r["surface"] for r in rows if r["state"] == s) for s in states},
            "roots": rows}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("cmd", choices=["prompt", "top"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--db", default=str(ux.DEFAULT_DB))
    ap.add_argument("--from", dest="start", default=None)
    ap.add_argument("--to", dest="end", default=None)
    ap.add_argument("--n", type=int, default=20)
    a = ap.parse_args(argv)
    con = ux.connect(Path(a.db))
    if a.cmd == "prompt":
        if not a.args:
            ap.error("prompt needs a PROMPT_ID")
        res = root_progress(con, a.args[0])
    else:
        now = time.time()
        res = top(con, ux._epoch(a.start) if a.start else now - 86400,
                  ux._epoch(a.end) if a.end else now, a.n)
    print(json.dumps(res, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
