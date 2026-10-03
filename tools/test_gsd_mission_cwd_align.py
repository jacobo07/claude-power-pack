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

# Hermetic for the supervise gates (14-16): mission state and markers in a temp dir BEFORE import.
STATE = tempfile.mkdtemp(prefix="gsd-mca-state-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = STATE
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(STATE) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = STATE

import gsd_mission as gm  # noqa: E402
import gsd_long_run as lr  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None

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

        # 10-13: a shared checkout (measured 2026-10-03: m-fdefb0fca0c0 and m-876f8b5a904a HELD for
        # good because peers committed to the main checkout while the worker worked in its own
        # worktree). The supervisor PROVED the worktree (effective_workdir: the predecessor worked
        # there, on this workstream); then a diverged cwd is a peer's history, not a stale roadmap.
        def shared(root):
            c, w = repo(root)
            (w / ".planning" / "workstreams" / "ws").mkdir(parents=True)
            commit(w, ".planning/workstreams/ws/ROADMAP.md", "phase 1 done")
            commit(c, "peer.txt", "another pane's commit")
            return c, w

        cwd, wt = shared(t / "c10")
        bc, bw = head(cwd), head(wt)
        r = gm.align_cwd(str(cwd), str(wt), proven_workstream="ws")
        check("V-MCA-DIVERGED-FOLLOWED", r["status"] == "diverged_followed"
              and "diverged_followed" not in gm.CWD_ALIGN_BLOCKING
              and head(cwd) == bc and head(wt) == bw,
              f"status={r['status']} heads unchanged={head(cwd) == bc and head(wt) == bw}")

        cwd, wt = shared(t / "c11")
        r = gm.align_cwd(str(cwd), str(wt))
        check("V-MCA-DIVERGED-UNPROVEN", r["status"] == "diverged",
              f"no proof of the worktree -> still blocking: {r['status']}")

        cwd, wt = shared(t / "c12")
        (cwd / ".planning" / "workstreams" / "ws").mkdir(parents=True)
        commit(cwd, ".planning/workstreams/ws/ROADMAP.md", "newer roadmap the worktree lacks")
        r = gm.align_cwd(str(cwd), str(wt), proven_workstream="ws")
        check("V-MCA-DIVERGED-STALE-ROADMAP", r["status"] == "diverged",
              f"worktree lacks the cwd's latest workstream commit -> blocking: {r['status']}")

        # 13 three relays while main keeps advancing: every relay follows, nothing is lost or moved
        cwd, wt = shared(t / "c13")
        statuses, kept = [], True
        for n in range(3):
            w = commit(wt, f".planning/workstreams/ws/phase{n + 2}.md", f"phase {n + 2}")
            commit(cwd, f"peer{n}.txt", f"peer commit {n}")
            statuses.append(gm.align_cwd(str(cwd), str(wt), proven_workstream="ws")["status"])
            kept = kept and head(wt) == w and not (cwd / f".planning/workstreams/ws/phase{n + 2}.md").exists()
        check("V-MCA-THREE-RELAYS", statuses == ["diverged_followed"] * 3 and kept,
              f"statuses={statuses} worktree kept every phase, cwd untouched={kept}")

    # 9 structural: supervise aligns the cwd BEFORE it launches a worker
    src = Path(gm.__file__).read_text(encoding="utf-8")
    sup = src[src.index("def supervise("):]
    a, l = sup.find('align_cwd(rec["cwd"]'), sup.find('row["launch"] = launch_worker(')
    check("V-MCA-SUPERVISE-ORDER", 0 <= a < l, f"align at {a}, launch at {l}")

    # 14-16 supervise passes the proof ONLY for a worktree effective_workdir followed. A recorded
    # work_dir, or the mission cwd itself, proves nothing (the Brand #001 shape stays blocked).
    class R:
        def __init__(self, out):
            self.stdout, self.stderr, self.returncode = out, "", 0

    seen, launches = [], []
    real_ew, real_align = gm.effective_workdir, gm.align_cwd

    def fake_align(cwd, work_dir, proven_workstream=None):
        seen.append(proven_workstream)
        return {"status": "diverged_followed" if proven_workstream else "aligned", "detail": "fake"}

    def launch(argv, cwd):
        launches.append(argv)
        return R(f"backgrounded · 9e9e9e9e · {argv[argv.index('-n') + 1]}")

    def one_pass(mid, ew_answer):
        for p in Path(STATE).glob("gsd-mission-*.json"):
            p.unlink()
        gm.create(STATE, "/gsd-autonomous", mission_id=mid, workstream="ws", now=1_800_000_000.0)
        gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t", now=1_800_000_000.0,
                      state=gm.RUNNING, epoch=1,
                      owner={"session_id": f"s-{mid}", "pid": 5151, "kind": "background"})
        gm.effective_workdir = lambda sid, base, ws=None: ew_answer(base)
        seen.clear()
        rows = gm.supervise(now=1_800_000_000.0, sessions=[{
            "sessionId": f"s-{mid}", "status": "idle", "state": "working", "kind": "background",
            "id": f"s-{mid}"[:8], "pid": 999}],
            gsd_status=lambda c, workstream=None: {"outcome": "OK", "reason": "ok"},
            runner=launch, stop_runner=lambda argv: R("stopped"), pid_alive=lambda pid: False)
        return next((r for r in rows if r.get("mission_id") == mid or r.get("id") == mid), rows[0] if rows else {})

    gm.align_cwd = fake_align
    try:
        n = len(launches)
        row = one_pass("m-proven", lambda base: str(Path(base) / "wt-proven"))
        followed = [e for e in lr.ledger_events("m-proven") if e.get("event") == "cwd_diverged_followed"]
        check("V-MCA-SUP-PROVEN-PASSED", seen == ["ws"] and row.get("cwd_align") == "diverged_followed"
              and not row.get("held") and len(launches) == n + 1 and len(followed) == 1,
              f"proof={seen} align={row.get('cwd_align')} held={row.get('held')} "
              f"launched={len(launches) - n} ledgered={len(followed)}")
        row = one_pass("m-recorded", lambda base: None)
        check("V-MCA-SUP-RECORDED-NOT-PROOF", seen == [None], f"proof={seen} (no effective_workdir)")
        row = one_pass("m-base", lambda base: base)
        check("V-MCA-SUP-BASE-NOT-PROOF", seen == [None], f"proof={seen} (effective_workdir == cwd)")
    finally:
        gm.effective_workdir, gm.align_cwd = real_ew, real_align

    print(f"MCA_PASS={passes}/{passes + fails}  threshold=16/16")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
