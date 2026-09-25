#!/usr/bin/env python3
"""UWCP S1 foundation gates (V-UWCP-F-*).

Covers the goal-log durability additions made for a remote authority home.
Evidence class of this file: LOCAL_REALITY on the host that runs it. The POSIX
branch of the directory fsync can only be exercised on Linux; it is re-run on
the VPS authority home in S5 and is NOT claimed by a Windows run.

    python tools/test_uwcp_foundation.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.gsd_x.goal import log as gl          # noqa: E402

REPO = "e" * 40


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []

    def check(g, cond, ev, why):
        (passes if cond else fails).append(g)
        print(f"  {'PASS' if cond else 'FAIL'} {g}: {ev if cond else why}")

    base = Path(tempfile.mkdtemp(prefix="uwcp_f_"))
    lg = gl.GoalLog(REPO, "g-f", base=base)

    # --- S1-4 directory fsync happens after the name is published -------------
    calls: list[tuple[Path, bool]] = []
    real = gl._fsync_dir

    def spy(path):
        calls.append((Path(path), (Path(path) / f"{len(lg.read()):06d}.json").is_file()))

    gl._fsync_dir = spy
    try:
        lg.append(1, "goal.declared", {"x": 1}, "t")
        check("V-UWCP-F-DIRSYNC-CALLED",
              len(calls) == 1 and calls[0][0] == lg.dir and calls[0][1],
              "publish syncs the goal directory once, after the event name exists",
              f"calls={calls}")
        try:
            lg.append(1, "goal.declared", {"x": 2}, "t")
            raced = False
        except gl.LostRace:
            raced = True
        check("V-UWCP-F-DIRSYNC-NOT-ON-LOSS", raced and len(calls) == 1,
              "a lost race publishes nothing and syncs nothing", f"raced={raced} calls={calls}")
    finally:
        gl._fsync_dir = real

    if os.name == "nt":
        try:
            real(lg.dir)
            noop = True
        except OSError:
            noop = False
        check("V-UWCP-F-DIRSYNC-NT-NOOP", noop,
              "on Windows the directory sync is an explicit no-op, not a crash "
              "(POSIX branch: REMOTE_REALITY owed in S5)", "raised on Windows")
    else:
        real(lg.dir)
        check("V-UWCP-F-DIRSYNC-POSIX", True, "POSIX directory fsync ran without error", "")

    total = len(passes) + len(fails)
    print(f"UWCP_FOUNDATION_PASS={len(passes)}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
