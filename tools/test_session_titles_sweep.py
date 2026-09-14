#!/usr/bin/env python3
"""test_session_titles_sweep.py -- V-gates for tools/session_titles_sweep.py.

Scope: the sweep's OWN logic (liveness detection, argv construction, refusal).
The rename itself is owned and already proven by tools/rename_sessions.py, whose
safety invariant is prefix-byte-identity with auto-revert.

HERMETIC BY CONSTRUCTION: every gate runs against a throwaway tmp tree and
restores the module constants it moved. Nothing reads or writes ~/.claude.

Each gate drives a branch that can actually FAIL. The liveness gates matter most:
under-skipping a live session lets an append race claude.exe, and the renamer's
revert-by-truncation would then destroy the line claude.exe had just written.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "session_titles_sweep", HERE / "session_titles_sweep.py")
sweep = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sweep)

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS  {gate}  -- {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL  {gate}  -- {diag}")


def _beacon(dirpath: Path, wrapper_pid: int, sid: str, age_days: float = 0.0) -> Path:
    p = dirpath / f"kclaude-pane-{wrapper_pid}.sid"
    p.write_text(json.dumps({"sid": sid, "cwd": "C:\\x", "pid": wrapper_pid}),
                 encoding="utf-8")
    if age_days:
        t = time.time() - age_days * 86400
        os.utime(p, (t, t))
    return p


def _transcript(proj: Path, sid: str, age_minutes: float) -> Path:
    proj.mkdir(parents=True, exist_ok=True)
    p = proj / f"{sid}.jsonl"
    p.write_text(json.dumps({"type": "user", "sessionId": sid}) + "\n",
                 encoding="utf-8")
    t = time.time() - age_minutes * 60
    os.utime(p, (t, t))
    return p


def gate_beacons(tmp: Path) -> None:
    """A fresh beacon means an open pane; a stale one is crash debris."""
    bdir = tmp / "temp_beacons"
    bdir.mkdir()
    _beacon(bdir, 111, "aaaaaaaa-0000-0000-0000-000000000001")
    _beacon(bdir, 222, "aaaaaaaa-0000-0000-0000-000000000002")
    _beacon(bdir, 333, "dead-0000-0000-0000-000000000003",
            age_days=sweep.STALE_BEACON_DAYS + 1)

    orig = sweep.temp_dir
    sweep.temp_dir = lambda: bdir
    try:
        sids, read, stale = sweep.live_session_ids()
    finally:
        sweep.temp_dir = orig

    if len(sids) == 2 and read == 2 and stale == 1:
        _ok("V-SWEEP-BEACON-LIVE", f"2 live / 1 stale ignored (read={read})")
    else:
        _fail("V-SWEEP-BEACON-LIVE",
              f"expected 2 live + 1 stale, got sids={sorted(sids)} read={read} stale={stale}")

    if "dead-0000-0000-0000-000000000003" not in sids:
        _ok("V-SWEEP-BEACON-STALE-IGNORED", "a crashed wrapper cannot freeze the sweep")
    else:
        _fail("V-SWEEP-BEACON-STALE-IGNORED", "stale beacon was treated as live")


def gate_recent_writes(tmp: Path) -> None:
    """mtime is the wrapper-independent signal: it must catch a beacon-less pane."""
    root = tmp / "projects"
    proj = root / "C--demo"
    fresh = "bbbbbbbb-0000-0000-0000-00000000000f"
    old = "bbbbbbbb-0000-0000-0000-00000000000a"
    _transcript(proj, fresh, age_minutes=1)
    _transcript(proj, old, age_minutes=sweep.RECENT_WRITE_MINUTES + 30)

    orig = sweep.PROJECTS_ROOT
    sweep.PROJECTS_ROOT = root
    try:
        sids, seen = sweep.recently_written_session_ids()
    finally:
        sweep.PROJECTS_ROOT = orig

    if sids == {fresh} and seen == 2:
        _ok("V-SWEEP-RECENT-WRITE", f"fresh flagged, idle released (seen={seen})")
    else:
        _fail("V-SWEEP-RECENT-WRITE",
              f"expected only the fresh sid, got {sorted(sids)} seen={seen}")

    # The negative control: without this the guard could flag everything and
    # still pass the assertion above.
    if old not in sids:
        _ok("V-SWEEP-RECENT-NEGATIVE", "an idle session is NOT withheld from renaming")
    else:
        _fail("V-SWEEP-RECENT-NEGATIVE", "idle session was withheld -- guard flags everything")


def gate_argv() -> None:
    """Every skipped sid must reach the renamer, or the guard is decorative."""
    skip = {"s2", "s1"}
    argv = sweep.build_argv(skip, dry_run=False)
    pairs = [(argv[i], argv[i + 1]) for i in range(len(argv) - 1)
             if argv[i] == "--skip-sid"]
    got = sorted(v for _, v in pairs)
    if got == ["s1", "s2"] and "--apply" in argv and "--dry-run" not in argv:
        _ok("V-SWEEP-ARGV-APPLY", f"--apply with {len(pairs)} skip-sid args")
    else:
        _fail("V-SWEEP-ARGV-APPLY", f"argv={argv}")

    argv_dry = sweep.build_argv(set(), dry_run=True)
    if "--dry-run" in argv_dry and "--apply" not in argv_dry:
        _ok("V-SWEEP-ARGV-DRYRUN", "dry-run never passes --apply")
    else:
        _fail("V-SWEEP-ARGV-DRYRUN", f"argv={argv_dry}")


def gate_refuses_empty(tmp: Path) -> None:
    """An unreadable projects tree reads exactly like an empty one. Refuse both."""
    empty = tmp / "no_projects"
    empty.mkdir()
    # main() logs, and the log path is global. Redirect it, or this gate writes a
    # FAIL line into the production log every time the suite runs -- a test that
    # contaminates the artifact an operator reads to check on the real sweep.
    orig = (sweep.PROJECTS_ROOT, sweep.LOG_DIR, sweep.LOG_FILE)
    sweep.PROJECTS_ROOT = empty
    sweep.LOG_DIR = tmp / "logs"
    sweep.LOG_FILE = sweep.LOG_DIR / "sweep.log"
    try:
        rc = sweep.main()
    finally:
        sweep.PROJECTS_ROOT, sweep.LOG_DIR, sweep.LOG_FILE = orig

    if rc == 2:
        _ok("V-SWEEP-REFUSE-EMPTY", "rc=2, refuses to sweep a tree it cannot see")
    else:
        _fail("V-SWEEP-REFUSE-EMPTY", f"expected rc=2, got {rc}")


def main() -> int:
    print("test_session_titles_sweep")
    with tempfile.TemporaryDirectory(prefix="pp_sweep_test_") as td:
        tmp = Path(td)
        gate_beacons(tmp)
        gate_recent_writes(tmp)
        gate_argv()
        gate_refuses_empty(tmp)
    total = _passes + _fails
    print(f"SWEEP_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
