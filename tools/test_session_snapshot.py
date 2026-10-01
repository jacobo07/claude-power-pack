#!/usr/bin/env python3
"""V-SNAPSHOT-* gates for tools/session-snapshot.py (lock + orphan-tmp sweep).

Origin 2026-10-01: a per-turn Stop trigger plus a check-then-write lock let
several writers run at once, and runs killed mid-write left 132
`.zip.tmp.<pid>` files (198 GB) that rotation never collected because it only
globs `*.zip`. Every gate runs against a temp BACKUP_ROOT; the real
~/.claude/backups is never touched.
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PP = Path(__file__).resolve().parent.parent
TOOL = PP / "tools" / "session-snapshot.py"
_passes = 0
_fails = 0


def _ok(gate: str, msg: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS {gate}: {msg}")


def _fail(gate: str, msg: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {gate}: {msg}")


def _load(root: Path):
    spec = importlib.util.spec_from_file_location("session_snapshot", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.BACKUP_ROOT = root
    mod.LOCK_PATH = root / ".session-snapshot.lock"
    return mod


def _dead_pid() -> int:
    p = subprocess.Popen([sys.executable, "-c", "pass"])
    p.wait()
    return p.pid


def gate_sweep(root: Path) -> None:
    # Arrange
    mod = _load(root)
    sleeper = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        dead = _dead_pid()
        orphan = root / f"projects-snapshot-2026-09-30_000000.zip.tmp.{dead}"
        live = root / f"projects-snapshot-2026-09-30_000001.zip.tmp.{sleeper.pid}"
        final = root / "projects-snapshot-2026-09-30_000002.zip"
        for f in (orphan, live, final):
            f.write_bytes(b"x")
        # Act
        dry = mod._sweep_orphan_tmps(dry_run=True)
        dry_kept = orphan.exists()
        victims = mod._sweep_orphan_tmps(dry_run=False)
        # Assert
        if dry == [orphan] and dry_kept:
            _ok("V-SNAPSHOT-SWEEP-DRYRUN", "dry-run names the orphan and deletes nothing")
        else:
            _fail("V-SNAPSHOT-SWEEP-DRYRUN", f"dry={dry} kept={dry_kept}")
        if victims == [orphan] and not orphan.exists():
            _ok("V-SNAPSHOT-SWEEP-ORPHAN", f"dead-pid tmp swept (pid {dead})")
        else:
            _fail("V-SNAPSHOT-SWEEP-ORPHAN", f"victims={victims} exists={orphan.exists()}")
        if live.exists() and final.exists():
            _ok("V-SNAPSHOT-SWEEP-KEEPS", "live-writer tmp and finished zip kept")
        else:
            _fail("V-SNAPSHOT-SWEEP-KEEPS", f"live={live.exists()} final={final.exists()}")
    finally:
        sleeper.kill()
        sleeper.wait()


def gate_lock_states(root: Path) -> None:
    mod = _load(root)
    sleeper = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        # live foreign owner -> held, and our release must not remove it
        mod.LOCK_PATH.write_text(f"pid={sleeper.pid}\nts=0\n", encoding="utf-8")
        verdict = mod._acquire_lock()
        mod._release_lock()
        if verdict == "held" and mod.LOCK_PATH.exists():
            _ok("V-SNAPSHOT-LOCK-LIVE-OWNER", "old-but-live owner holds; foreign lock survives release")
        else:
            _fail("V-SNAPSHOT-LOCK-LIVE-OWNER", f"verdict={verdict} exists={mod.LOCK_PATH.exists()}")
        # dead owner -> reclaimed, then released by us
        mod.LOCK_PATH.write_text(f"pid={_dead_pid()}\nts=0\n", encoding="utf-8")
        verdict = mod._acquire_lock()
        owner = mod._lock_owner_pid()
        mod._release_lock()
        if verdict == "stale-reclaimed" and owner == os.getpid() and not mod.LOCK_PATH.exists():
            _ok("V-SNAPSHOT-LOCK-DEAD-OWNER", "dead owner reclaimed, own lock released")
        else:
            _fail("V-SNAPSHOT-LOCK-DEAD-OWNER", f"verdict={verdict} owner={owner}")
        # positive control: a free lock is acquired
        verdict = mod._acquire_lock()
        mod._release_lock()
        if verdict == "acquired":
            _ok("V-SNAPSHOT-LOCK-FREE", "free lock acquired")
        else:
            _fail("V-SNAPSHOT-LOCK-FREE", f"verdict={verdict}")
    finally:
        sleeper.kill()
        sleeper.wait()


RACER = r"""
import importlib.util, sys, time
from pathlib import Path
spec = importlib.util.spec_from_file_location("s", sys.argv[1])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
root = Path(sys.argv[2]); m.BACKUP_ROOT = root; m.LOCK_PATH = root / ".session-snapshot.lock"
go = float(sys.argv[3])
while time.time() < go:
    pass
print(m._acquire_lock(), flush=True)
time.sleep(3)
"""


def gate_concurrent(root: Path) -> None:
    # Arrange: 6 racers released at the same instant
    go = time.time() + 2.0
    procs = [subprocess.Popen([sys.executable, "-c", RACER, str(TOOL), str(root), str(go)],
                              stdout=subprocess.PIPE, text=True) for _ in range(6)]
    # Act
    verdicts = [p.communicate(timeout=60)[0].strip() for p in procs]
    # Assert
    winners = sum(v in ("acquired", "stale-reclaimed") for v in verdicts)
    if winners == 1 and verdicts.count("held") == 5:
        _ok("V-SNAPSHOT-LOCK-RACE", f"6 simultaneous starts -> 1 writer ({verdicts})")
    else:
        _fail("V-SNAPSHOT-LOCK-RACE", f"verdicts={verdicts}")


def main() -> int:
    print("session-snapshot gates")
    for gate in (gate_sweep, gate_lock_states, gate_concurrent):
        with tempfile.TemporaryDirectory() as td:
            gate(Path(td))
    total = _passes + _fails
    print(f"\nSNAPSHOT_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
