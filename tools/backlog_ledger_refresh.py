#!/usr/bin/env python3
"""Detached worker: rebuild the reconciliation ledger of ONE tree into host state (spec vault/specs/backlog-ledger-refresh.md).

Launched by hooks/backlog_ledger_refresh.js, never inside a hook deadline (a build measured 148 s on 2026-11-16).
Writes only under the state dir (default ~/.claude/state/backlog_ledger, override CPP_BACKLOG_STATE_DIR):
  <slug>.json           the latest ledger + verify verdict (atomic replace)
  <slug>.history.jsonl  one row per attempt, success OR failure (a failed refresh is visible and rate-limited too)
  <slug>.lock           single-flight; a lock older than LOCK_STALE_S is broken once
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

LOCK_STALE_S = 3600


def state_dir() -> Path:
    d = Path(os.environ.get("CPP_BACKLOG_STATE_DIR") or (Path.home() / ".claude" / "state" / "backlog_ledger"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def _acquire(lock: Path) -> bool:
    for _ in range(2):
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w") as fh:
                fh.write("%d %f\n" % (os.getpid(), time.time()))
            return True
        except FileExistsError:
            try:
                if time.time() - lock.stat().st_mtime <= LOCK_STALE_S:
                    return False
                lock.unlink()                      # stale: the holder died; break it once
            except FileNotFoundError:
                pass                               # released between the open and the stat: retry
    return False


def _lower_priority() -> None:
    try:
        if os.name == "nt":
            import ctypes
            ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)  # BELOW_NORMAL
        else:
            os.nice(10)
    except Exception:  # noqa: BLE001 -- priority is a courtesy, never a reason to skip the refresh
        pass


def _head(root: Path) -> str | None:
    try:
        r = subprocess.run(["git", "-C", str(root), "rev-parse", "--short=8", "HEAD"], capture_output=True,
                           text=True, timeout=15, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return r.stdout.strip() or None if r.returncode == 0 else None
    except Exception:  # noqa: BLE001
        return None


def _append(path: Path, row: dict) -> None:
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def run(root: Path, slug: str, sdir: Path | None = None) -> int:
    """0 = built (verify verdict is in the row), 2 = another worker holds the lock, 1 = the build failed (row written)."""
    sdir = sdir or state_dir()
    lock = sdir / ("%s.lock" % slug)
    if not _acquire(lock):
        return 2
    t0 = time.time()
    row = {"ts": t0, "root": str(root), "slug": slug, "head": _head(root)}
    try:
        _lower_priority()
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from modules.backlog_autopilot import inventory as inv, ledger as led_mod
        inventory = inv.build(root)
        led = led_mod.build(root, inventory)
        fails = led_mod.verify(led, inventory)
        row.update({k: led[k] for k in ("reconciliation", "operational", "by_state", "blocked_in_denominator")},
                   verify="FAIL" if fails else "PASS", verify_fails=fails[:20], ms=int((time.time() - t0) * 1000))
        snap = sdir / ("%s.json" % slug)
        tmp = snap.with_suffix(".json.%d.tmp" % os.getpid())
        tmp.write_text(json.dumps(dict(led, refresh=row), indent=1, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, snap)
        _append(sdir / ("%s.history.jsonl" % slug), row)
        return 0
    except Exception as exc:  # noqa: BLE001 -- a failed refresh is a recorded row, never silence
        row.update(error="%s: %s" % (type(exc).__name__, exc), trace=traceback.format_exc()[-1500:],
                   ms=int((time.time() - t0) * 1000))
        _append(sdir / ("%s.history.jsonl" % slug), row)
        return 1
    finally:
        try:
            lock.unlink()
        except OSError:
            pass


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", required=True)
    ap.add_argument("--slug", required=True)
    a = ap.parse_args(argv)
    return run(Path(a.root).resolve(), a.slug)


if __name__ == "__main__":
    raise SystemExit(main())
