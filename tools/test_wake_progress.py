#!/usr/bin/env python
"""V-WAKE-* gates: a wake is judged by the work tree, not by the host's ack (A3).

Measured 2026-10-18 (TB-FULL m-c63384bde9d0): a woken worker acked, spent 19M processed tokens and committed
nothing for 75 minutes. Every refusal has a paired control; the mutation drill makes an ack count as progress.
Hermetic: state in a temp dir before import."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="wake-progress-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_CLAUDE_EXE"] = "__no_such_claude_in_tests__"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_mission as gm  # noqa: E402
import decision_plane as dp  # noqa: E402

passes = fails = 0
NOW = 1_800_000_000.0
G = gm.WAKE_GRACE_S


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def running(mid, **extra):
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    return gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW,
                         state=gm.RUNNING, epoch=1, work_dir=TMP, **extra)


def events(mid, name):
    return [e for e in gm.lr.ledger_events(mid) if e.get("event") == name]


def main() -> int:
    stamp = {"at": NOW, "fp": "tree-A", "kind": "decision"}
    check("V-WAKE-NO-STAMP-NONE", gm.judge_wake(None, "tree-A", NOW + 10 * G) is None)
    check("V-WAKE-MOVED-IS-PROGRESS", gm.judge_wake(stamp, "tree-B", NOW + 5) == "PROGRESS")
    check("V-WAKE-UNCHANGED-WITHIN-GRACE-PENDING", gm.judge_wake(stamp, "tree-A", NOW + G - 1) == "PENDING")
    check("V-WAKE-UNCHANGED-AFTER-GRACE-NO-PROGRESS", gm.judge_wake(stamp, "tree-A", NOW + G + 1) == "NO_PROGRESS")
    check("V-WAKE-UNMEASURED-IS-NOT-NO-PROGRESS", gm.judge_wake(stamp, None, NOW + G + 1) == "UNKNOWN"
          and gm.judge_wake({**stamp, "fp": None}, "tree-A", NOW + G + 1) == "UNKNOWN")

    # integration: the supervisor judges the stamp through _check_wake
    a = running("m-wa", wake_expect=stamp)
    a2 = gm._check_wake(a, NOW + 60, fingerprint=lambda d: "tree-A")
    check("V-WAKE-PENDING-LEAVES-STAMP", a2.get("wake_expect") and not events("m-wa", "wake_no_progress"))
    a3 = gm._check_wake(gm.load("m-wa"), NOW + G + 60, fingerprint=lambda d: "tree-A")
    check("V-WAKE-SILENT-WORKER-LEDGERED", len(events("m-wa", "wake_no_progress")) == 1 and a3.get("wake_expect") is None
          and (a3.get("wake_last") or {}).get("verdict") == "NO_PROGRESS", str(a3.get("wake_last")))
    b = running("m-wb", wake_expect=stamp)
    b2 = gm._check_wake(b, NOW + 120, fingerprint=lambda d: "tree-B")
    check("V-WAKE-COMMIT-IS-PROGRESS-CONTROL", len(events("m-wb", "wake_progress")) == 1
          and not events("m-wb", "wake_no_progress") and b2.get("wake_expect") is None)
    c = running("m-wc", wake_expect=stamp)
    gm._check_wake(c, NOW + G + 60, fingerprint=lambda d: None)
    check("V-WAKE-UNMEASURED-LEDGERS-NEITHER-VERDICT-AS-FAILURE", not events("m-wc", "wake_no_progress"))

    # the wake itself stamps what the tree looked like
    d = running("m-wd")
    real_fp = gm.progress_fingerprint
    gm.progress_fingerprint = lambda wd: "tree-Z"
    try:
        dp._stamp_wake("m-wd", NOW + 5)
    finally:
        gm.progress_fingerprint = real_fp
    sd = (gm.load("m-wd") or {}).get("wake_expect") or {}
    check("V-WAKE-STAMPS-THE-TREE", sd.get("fp") == "tree-Z" and sd.get("at") == NOW + 5, str(sd))

    # mutation drill: an ack counted as progress must turn the silent-worker gate red
    real_judge = gm.judge_wake
    gm.judge_wake = lambda *a_, **k_: "PROGRESS"
    try:
        e = running("m-we", wake_expect=stamp)
        gm._check_wake(e, NOW + G + 60, fingerprint=lambda d: "tree-A")
        mutant_ledgers_silence = len(events("m-we", "wake_no_progress")) == 1
    finally:
        gm.judge_wake = real_judge
    check("V-WAKE-MUTATION-RED", not mutant_ledgers_silence, "ack-as-progress mutant fails the silent-worker gate")
    print(f"WAKE_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
