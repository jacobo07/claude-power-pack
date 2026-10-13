#!/usr/bin/env python3
"""land_worktree.py -- known-integration transaction (autonomy S1).

Lands a worktree branch onto the LIVE checkout in one command:
  1. worktree tracked-clean, live HEAD recorded
  2. overlap check: files the branch changes vs live dirty/untracked paths -> refuse
  3. rebase branch onto live HEAD (conflict -> abort, branch restored, refuse)
  4. declared tests in the worktree (red -> branch restored, refuse)
  5. live HEAD unchanged + `merge --ff-only` in live (nothing else touches live)
  6. declared tests again in live (red is RECORDED as LANDED_POST_RED, never hidden)
  7. JSON receipt

Refusals land nothing. Exit 0 = LANDED, 1 = REFUSED, 2 = LANDED_POST_RED.
Never pushes. Usage:
  land_worktree.py --worktree W --live L [--branch B] --test "python -m pytest x -q" [--test ...] [--receipt f.json]
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import shlex
import subprocess
import sys
import time

GIT = r"C:\Program Files\Git\cmd\git.exe"
if not os.path.exists(GIT):
    GIT = "git"


def git(repo, *args, check=False):
    p = subprocess.run([GIT, "-C", repo, *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if check and p.returncode != 0:
        raise RuntimeError("git %s failed: %s" % (" ".join(args), p.stderr.strip()))
    return p


def rev(repo, ref="HEAD"):
    p = git(repo, "rev-parse", ref)
    return p.stdout.strip() if p.returncode == 0 else ""


def live_dirty_paths(live):
    """Every path dirty or untracked in live (renames contribute both sides)."""
    p = git(live, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    if p.returncode != 0:
        raise RuntimeError("live status failed: " + p.stderr.strip())
    parts = p.stdout.split("\0")
    out, i = set(), 0
    while i < len(parts):
        e = parts[i]
        i += 1
        if len(e) < 4:
            continue
        out.add(e[3:])
        if e[0] in "RC" or e[1] in "RC":
            if i < len(parts) and parts[i]:
                out.add(parts[i])
            i += 1
    return out


def branch_paths(repo, base, tip):
    p = git(repo, "diff", "--name-only", "--no-renames", base + "..." + tip)
    return {x for x in p.stdout.splitlines() if x}


def overlap(branch_files, dirty):
    return sorted(branch_files & dirty)


def run_tests(cwd, tests):
    results = []
    for t in tests:
        argv = shlex.split(t, posix=False)
        argv = [a.strip('"') for a in argv]
        if argv and argv[0].lower() in ("python", "python.exe"):
            argv[0] = sys.executable
        try:
            p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=1800)
            rc, tail = p.returncode, (p.stdout + p.stderr).strip()[-400:]
        except Exception as e:  # missing exe / timeout = red, never green
            rc, tail = 99, repr(e)
        results.append({"cmd": t, "rc": rc, "tail": tail})
    return results, all(r["rc"] == 0 for r in results)


def _suite_of(cmd):
    parts = cmd.replace("\\", "/").split()
    return parts[-1] if parts else cmd


def load_baseline_red(path):
    """Suites known red (or timed out is NOT red) before the change: JSON {"red": [...]} or one path per line."""
    txt = open(path, encoding="utf-8-sig").read()
    try:
        d = json.loads(txt)
        return set(d["red"] if isinstance(d, dict) else d)
    except ValueError:
        return {x.strip().replace("\\", "/") for x in txt.splitlines() if x.strip()}


def split_baseline(results, baseline_red):
    """Red results whose suite is in the baseline are reported (non-blocking); the rest block."""
    base = set(baseline_red or ())
    blocking = [x for x in results if x["rc"] != 0 and _suite_of(x["cmd"]) not in base]
    known = [x for x in results if x["rc"] != 0 and _suite_of(x["cmd"]) in base]
    return blocking, known


def _closure(paths, worktree):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import change_impact
    return change_impact.affected_closure(paths, worktree)


def _hub(cl, worktree):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import change_impact
    return change_impact.hub_report(cl, worktree)


def land(worktree, live, branch=None, tests=(), now=time.time, affected=False, exempt=(), closure_fn=None,
         baseline_red=(), hub_fn=None):
    r = {"worktree": worktree, "live": live, "tests": list(tests), "ts": int(now()),
         "status": "REFUSED", "reason": "", "landed": False, "affected": bool(affected)}
    if not tests and not affected:
        r["reason"] = "NO_TESTS_DECLARED"
        return r
    branch = branch or git(worktree, "branch", "--show-current").stdout.strip()
    if not branch:
        r["reason"] = "DETACHED_WORKTREE"
        return r
    r["branch"] = branch
    orig = rev(worktree, branch)
    r["branch_before"] = orig
    if git(worktree, "status", "--porcelain", "--untracked-files=no").stdout.strip():
        r["reason"] = "WORKTREE_DIRTY"
        return r
    if git(worktree, "branch", "--show-current").stdout.strip() != branch:
        r["reason"] = "BRANCH_NOT_CHECKED_OUT_IN_WORKTREE"
        return r
    live_head = rev(live)
    r["live_head_before"] = live_head
    if not live_head:
        r["reason"] = "LIVE_HEAD_UNKNOWN"
        return r
    base = git(worktree, "merge-base", live_head, orig).stdout.strip()
    files = branch_paths(worktree, base, orig)
    r["files"] = sorted(files)
    if not files:
        r["reason"] = "NOTHING_TO_LAND"
        return r
    if affected:
        try:
            cl = (closure_fn or _closure)(sorted(files), worktree)
        except Exception as e:  # no answer is never green
            cl = {"unjudged": True, "gaps": [repr(e)]}
        if cl.get("unjudged"):
            r["reason"], r["detail"] = "AFFECTED_UNJUDGED", str(cl.get("gaps"))[-400:]
            return r
        unmapped = [p for p in cl["unmapped"] if not any(fnmatch.fnmatch(p, g) for g in exempt)]
        if unmapped:
            r["reason"], r["unmapped"] = "AFFECTED_NO_MAPPED_TEST", unmapped
            return r
        hub = (hub_fn or _hub)(cl, worktree)
        if hub["hubs"]:
            r["hub"] = hub
            if not tests:
                r["reason"] = "AFFECTED_HUB_NEEDS_EXPLICIT_TEST"
                return r
            hub_cmds = {c for p in hub["hubs"] for c in cl["per_path"][p]}
            cl = dict(cl, tests=[c for c in cl["tests"] if c not in hub_cmds])
        tests = list(dict.fromkeys([*tests, *cl["tests"]]))
        r["tests"] = tests
        r["affected_closure"] = {"per_path": cl["per_path"], "exempt": list(exempt),
                                 "exempted": [p for p in cl["unmapped"] if p not in unmapped]}
        if not tests:
            r["reason"] = "NO_TESTS_DECLARED"
            return r
    ov = overlap(files, live_dirty_paths(live))
    if ov:
        r["reason"], r["overlap"] = "OVERLAP_LIVE_DIRTY", ov
        return r
    rb =git(worktree, "rebase", live_head)
    if rb.returncode != 0:
        git(worktree, "rebase", "--abort")
        git(worktree, "reset", "--hard", orig)
        r["reason"] = "REBASE_CONFLICT"
        r["detail"] = (rb.stdout + rb.stderr).strip()[-400:]
        return r

    def restore():
        git(worktree, "reset", "--hard", orig)

    pre, ok = run_tests(worktree, tests)
    r["tests_before"] = pre
    if not ok and baseline_red:
        blocking, known = split_baseline(pre, baseline_red)
        r["baseline_red_before"] = [x["cmd"] for x in known]
        ok = not blocking
    if not ok:
        restore()
        r["reason"] = "TESTS_RED_BEFORE"
        return r
    new_tip = rev(worktree, branch)
    r["branch_rebased"] = new_tip
    if rev(live) != live_head:
        restore()
        r["reason"] = "LIVE_MOVED_DURING_LAND"
        return r
    ov = overlap(branch_paths(worktree, live_head, new_tip), live_dirty_paths(live))
    if ov:
        restore()
        r["reason"], r["overlap"] = "OVERLAP_LIVE_DIRTY", ov
        return r
    mg = git(live, "merge", "--ff-only", new_tip)
    if mg.returncode != 0:
        restore()
        r["reason"] = "FF_REFUSED"
        r["detail"] = (mg.stdout + mg.stderr).strip()[-400:]
        return r
    r["landed"], r["live_head_after"] = True, rev(live)
    post, ok = run_tests(live, tests)
    r["tests_after"] = post
    if not ok and baseline_red:
        blocking, known = split_baseline(post, baseline_red)
        r["baseline_red_after"] = [x["cmd"] for x in known]
        ok = not blocking
    r["status"] = "LANDED" if ok else "LANDED_POST_RED"
    r["reason"] = "" if ok else "TESTS_RED_AFTER_LANDING (landed; revert is an Owner/steward decision)"
    return r


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--live", required=True)
    ap.add_argument("--branch")
    ap.add_argument("--test", action="append", default=[])
    ap.add_argument("--receipt")
    ap.add_argument("--affected", action="store_true",
                    help="tests = explicit --test + change_impact closure of the changed paths; unmapped path -> refuse")
    ap.add_argument("--exempt", action="append", default=[],
                    help="glob of changed paths allowed to have no mapped test (listed in the receipt)")
    ap.add_argument("--baseline-red", help="file of suites red before the change (reported in the receipt, not blocking)")
    a = ap.parse_args(argv)
    base = load_baseline_red(a.baseline_red) if a.baseline_red else ()
    r = land(a.worktree, a.live, a.branch, a.test, affected=a.affected, exempt=a.exempt, baseline_red=base)
    txt = json.dumps(r, indent=2)
    if a.receipt:
        with open(a.receipt, "w", encoding="utf-8", newline="\n") as f:
            f.write(txt + "\n")
    print(txt)
    return {"LANDED": 0, "LANDED_POST_RED": 2}.get(r["status"], 1)


if __name__ == "__main__":
    sys.exit(main())
