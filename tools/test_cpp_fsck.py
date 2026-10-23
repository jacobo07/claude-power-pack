#!/usr/bin/env python
"""V-FSCK-* gates for tools/cpp_fsck.py. Every check is driven on a fixture of its 2026-10-23 incident and a
paired admitting control; a missing source must give exit 2 and a run must leave the fixture tree untouched."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cpp_fsck  # noqa: E402

NOW = 1_790_000_000.0
passes = fails = 0


def _ok(gate: str, ev: str = "") -> None:
    global passes
    passes += 1
    print(f"PASS {gate} {ev}".rstrip())


def _fail(gate: str, why: str) -> None:
    global fails
    fails += 1
    print(f"FAIL {gate} {why}")


def gate(name: str, cond: bool, ev: str) -> None:
    (_ok if cond else _fail)(name, ev)


def git(cwd: Path, *args: str) -> str:
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@t"}
    return subprocess.run([cpp_fsck.GIT, "-C", str(cwd), *args], capture_output=True, text=True, check=True, env=env).stdout.strip()


def jl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def transcript(projects: Path, sid: str, mtime: float) -> None:
    p = projects / "proj" / f"{sid}.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("{}\n")
    os.utime(p, (mtime, mtime))


def args(**kw) -> argparse.Namespace:
    d = dict(state=Path("/nonexistent/state"), projects=Path("/nonexistent/projects"),
             repo=Path("/nonexistent/repo"), lifecycle=Path("/nonexistent/lc.json"),
             programmes=Path("/nonexistent/prog"), chain=None, tick_log=None, now=NOW)
    d.update(kw)
    return argparse.Namespace(**d)


def only(r: cpp_fsck.Result, check: str) -> list[dict]:
    return [f for f in r.findings if f["check"] == check]


def reserve(i: str, sid: str, amount: int, ts: float) -> dict:
    return {"op": "reserve", "id": i, "sid": sid, "amount": amount, "ts": ts}


def tree_hash(root: Path) -> dict:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file() and ".git/" not in p.as_posix()}


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        state, projects = tmp / "state", tmp / "projects"
        old = NOW - 3 * DAY
        # F1 fixture: three LEAKED reserves on dead sessions, plus a fresh reserve on a live session
        jl(state / "goal-budget/g1/spend.journal.jsonl", [
            reserve("r1", "dead1", 952_270, old), {"op": "leak", "id": "r1"},
            reserve("r2", "dead2", 1_060_540, old), {"op": "leak", "id": "r2"},
            reserve("r3", "dead3", 750_000, old), {"op": "leak", "id": "r3"},
            reserve("r4", "live1", 500_000, NOW - 60),
            reserve("r5", "dead1", 10, old), {"op": "settle", "sid": "dead1", "measured": 10, "closes": ["r5"]}])
        for s in ("dead1", "dead2", "dead3"):
            transcript(projects, s, old)
        transcript(projects, "live1", NOW)

        # --- F1
        r = cpp_fsck.Result()
        cpp_fsck.check_stranded_lease(r, state, projects, NOW)
        f = only(r, "stranded_lease")
        gate("V-FSCK-F1", sorted(x["amount"] for x in f) == [750_000, 952_270, 1_060_540]
             and all(x["state"] == "LEAKED" and "goal-settle" in x["repair"] for x in f), f"{len(f)} stranded")
        gate("V-FSCK-F1-CONTROL", not any(x["session"] in ("live1",) for x in f) and not r.unknown
             and all(x["reserve"] != "r5" for x in f), "fresh reserve on live session + settled reserve pass")
        # a missing transcript is UNKNOWN for that sid
        r2 = cpp_fsck.Result()
        cpp_fsck.check_stranded_lease(r2, state, tmp / "empty-projects", NOW)
        gate("V-FSCK-F1-UNKNOWN", not r2.findings and len(r2.unknown) == 3, "no transcript root -> UNKNOWN per sid")

        # --- F2
        chain = tmp / "chain.json"
        chain.write_text(json.dumps({"parked": True}))
        os.utime(chain, (NOW - 1000, NOW - 1000))
        t0 = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(NOW - 500))
        t_old = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(NOW - 5000))
        bad_log, good_log = tmp / "bad.log", tmp / "good.log"
        bad_log.write_text(f"{t_old} ram_hold free_gb=2\n{t0} ram_hold free_gb=2\n"
                           f'{t0} rc=0 free_gb=9 {{"action": "arm_refused"}}\n{t0} rc=0 free_gb=9 {{"action": "parked"}}\n')
        good_log.write_text(f"{t_old} ram_hold free_gb=2\n{t0} rc=0 free_gb=9 {{\"action\": \"parked\"}}\n{t0} rc=0 {{\"action\": \"held\"}}\n")
        r = cpp_fsck.Result()
        cpp_fsck.check_parked_chain(r, chain, bad_log)
        f = only(r, "parked_chain_polled")
        gate("V-FSCK-F2", len(f) == 1 and f[0]["count"] == 2
             and {p["action"] for p in f[0]["polls"]} == {"ram_hold", "arm_refused"}, "ram_hold + arm_refused after park")
        r = cpp_fsck.Result()
        cpp_fsck.check_parked_chain(r, chain, good_log)
        gate("V-FSCK-F2-CONTROL", not r.findings and not r.unknown, "parked/held lines only (and pre-park history) pass")

        # --- F3 and F4 share a real repo with a linked worktree
        repo = tmp / "repo"
        repo.mkdir()
        git(repo, "init", "-q", "-b", "main")
        (repo / "a.txt").write_text("1")
        git(repo, "add", "a.txt")
        git(repo, "commit", "-q", "-m", "c1")
        first = git(repo, "rev-parse", "--short", "HEAD")
        git(repo, "checkout", "-q", "-b", "side")
        (repo / "b.txt").write_text("2")
        git(repo, "add", "b.txt")
        git(repo, "commit", "-q", "-m", "side")
        side = git(repo, "rev-parse", "--short", "HEAD")
        git(repo, "checkout", "-q", "main")
        (repo / "c.txt").write_text("3")
        git(repo, "add", "c.txt")
        git(repo, "commit", "-q", "-m", "c2")
        head = git(repo, "rev-parse", "--short", "HEAD")
        wt_dirty, wt_clean, wt_known = tmp / "wt-dirty", tmp / "wt-clean", tmp / "wt-known"
        for p, b in ((wt_dirty, "w1"), (wt_clean, "w2"), (wt_known, "w3")):
            git(repo, "worktree", "add", "-q", "-b", b, str(p))
        (wt_dirty / "x.txt").write_text("dirty")
        (wt_known / "y.txt").write_text("dirty but classified")
        lc = tmp / "lifecycle.json"
        lc.write_text(json.dumps({"rows": {str(wt_known).replace("/", "\\"): {"state": "DURABLE_WAIT"}}}))
        r = cpp_fsck.Result()
        cpp_fsck.check_worktrees(r, repo, lc)
        f = only(r, "worktree_without_lifecycle")
        # git reports C:/x/y on Windows; compare in one normal form so the gate holds on both planes.
        n = lambda p: cpp_fsck._norm(str(p))  # noqa: E731
        paths = {n(x["worktree"]) for x in f}
        clean = {n(x) for x in r.info.get("unclassified_clean", [])}
        gate("V-FSCK-F3", n(wt_dirty) in paths and n(repo) not in paths, f"dirty by path: {sorted(paths)}")
        gate("V-FSCK-F3-CONTROL", n(wt_known) not in paths and n(wt_clean) not in paths
             and n(wt_clean) in clean, "classified-dirty passes; clean listed as info")

        prog = tmp / "prog"
        for name, line in (("stale", f"**Coherence anchor:** HEAD contains {side} the side branch"),
                           ("fresh", f"**Coherence anchor:** HEAD contains {head} tip"),
                           ("old", f"**Coherence anchor:** HEAD contains {first} root"),
                           ("none", "no anchor here")):
            (prog / name).mkdir(parents=True)
            (prog / name / "RESUMPTION_FILE.md").write_text(f"# {name}\n{line}\n")
        r = cpp_fsck.Result()
        cpp_fsck.check_resumption(r, repo, prog)
        stale = {Path(x["file"]).parent.name for x in only(r, "stale_resumption")}
        unk = {Path(x["file"]).parent.name: x["verdict"] for x in r.unknown}
        gate("V-FSCK-F4", stale == {"stale"} and unk == {"none": "UNKNOWN_FRESHNESS"}, f"stale={stale} unknown={unk}")
        gate("V-FSCK-F4-CONTROL", "fresh" not in stale and "old" not in stale and "fresh" not in unk,
             "anchor == HEAD and ancestor anchor pass")

        # --- F5
        def row(ts, ev, sid, **kw):
            return {"ts": ts, "event": ev, "session_id": sid, **kw}
        iso = lambda t: time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(t))  # noqa: E731
        jl(state / "rollover-ledger.jsonl", [
            row(iso(NOW - 3 * DAY), "capsule_sealed", "pend"),
            row(iso(NOW - 3 * DAY), "capsule_sealed", "claim"),
            row(iso(NOW - 3 * DAY + 60), "successor_claimed", "claim", claimant="x"),
            row(iso(NOW - 3 * DAY), "capsule_sealed", "cert"),
            row(iso(NOW - 3 * DAY + 60), "successor_claimed", "cert", claimant="y"),
            row(iso(NOW - 3 * DAY + 120), "resume_certified", "cert", claimant="y"),
            row(iso(NOW - 60), "capsule_sealed", "fresh")])
        r = cpp_fsck.Result()
        cpp_fsck.check_capsules(r, state, NOW)
        f = only(r, "capsule_without_disposition")
        gate("V-FSCK-F5", {(x["session"], x["disposition"]) for x in f} == {("pend", "PENDING"), ("claim", "CLAIMED_NO_VERDICT")},
             f"{[x['session'] for x in f]}")
        gate("V-FSCK-F5-CONTROL", all(x["session"] not in ("cert", "fresh") for x in f),
             "certified and <24h-old capsules pass")

        # --- F6
        r = cpp_fsck.Result()
        cpp_fsck.check_denominators(r)
        gate("V-FSCK-F6-CONTROL", not r.findings and not r.unknown, "live _summary carries scope/lease/programme_executable")
        saved = cpp_fsck.STATUS_KEYS
        cpp_fsck.STATUS_KEYS = saved + ("no_such_label",)
        r = cpp_fsck.Result()
        cpp_fsck.check_denominators(r)
        cpp_fsck.STATUS_KEYS = saved
        gate("V-FSCK-F6", [f["missing"] for f in only(r, "denominators_unlabelled")] == [["no_such_label"]],
             "an absent label is a finding")

        # --- whole-run semantics, through the real CLI
        full = ["--state", str(state), "--projects", str(projects), "--repo", str(repo), "--lifecycle", str(lc),
                "--programmes", str(prog), "--chain", str(chain), "--tick-log", str(bad_log), "--now", str(NOW)]
        before = tree_hash(tmp)
        cp = subprocess.run([sys.executable, str(HERE / "cpp_fsck.py"), *full], capture_output=True, text=True)
        after = tree_hash(tmp)
        out = json.loads(cp.stdout)
        gate("V-FSCK-READ-ONLY", before == after and cp.returncode == 1 and set(out["checks"]) == {
            "stranded_lease", "parked_chain_polled", "worktree_without_lifecycle", "stale_resumption",
            "capsule_without_disposition", "denominators_unlabelled"}, f"{len(before)} files unchanged, exit {cp.returncode}")
        gate("V-FSCK-EXIT-1", out["checks"]["stranded_lease"] == "FINDING" and cp.returncode == 1, "findings -> exit 1")

        nowhere = tmp / "nowhere"
        cp = subprocess.run([sys.executable, str(HERE / "cpp_fsck.py"), "--state", str(nowhere), "--projects", str(nowhere),
                             "--repo", str(nowhere), "--lifecycle", str(nowhere / "l.json"), "--programmes", str(nowhere),
                             "--now", str(NOW)], capture_output=True, text=True)
        out = json.loads(cp.stdout)
        gate("V-FSCK-UNKNOWN-NOT-PASS", cp.returncode == 2 and "PASS" not in
             [out["checks"][k] for k in out["checks"] if k != "denominators_unlabelled"], f"exit {cp.returncode} {out['checks']}")

    print(f"FSCK_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


DAY = 24 * 3600

if __name__ == "__main__":
    sys.exit(main())
