r"""
lazarus_topology_daemon.py - background topology snapshotter (MC-LAZ-35).

Lite daemon (not a Windows service): a detached python process that
loops every TOPOLOGY_INTERVAL_SECONDS (default 30) calling
``topology_engine.snapshot_all`` and writing only when the envelope hash
changes. PID file at ~/.claude/lazarus/.topology_daemon.pid lets ``stop``
and ``status`` find the running instance.

Why not a Windows service: registering one requires sc.exe + admin and
makes uninstallation painful. A detached python process gives us 95% of
the value (it survives terminal close, restarts on reboot if registered
in the Lazarus ONLOGON task) with 5% of the operational complexity.

Usage:
  python tools/lazarus_topology_daemon.py start [--interval 30]
  python tools/lazarus_topology_daemon.py stop
  python tools/lazarus_topology_daemon.py status
  python tools/lazarus_topology_daemon.py loop   # foreground, used by start
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from lib.lazarus.topology_engine import (  # noqa: E402
    envelope_hash,
    snapshot_all,
    write_snapshot,
)

LAZARUS_ROOT = Path(os.path.expanduser("~/.claude/lazarus"))
PID_FILE = LAZARUS_ROOT / ".topology_daemon.pid"
LOG_FILE = LAZARUS_ROOT / "topology" / "daemon.log"
LAST_HASH_FILE = LAZARUS_ROOT / "topology" / ".last_hash"
DEFAULT_INTERVAL = 30


def _log(msg: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with LOG_FILE.open("a", encoding="utf-8") as h:
        h.write(f"[{ts}] {msg}\n")


def _is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        try:
            out = subprocess.check_output(
                ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                stderr=subprocess.DEVNULL,
                text=True,
            )
            return str(pid) in out
        except subprocess.CalledProcessError:
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _read_pid() -> int | None:
    if not PID_FILE.is_file():
        return None
    try:
        return int(PID_FILE.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def cmd_start(interval: int) -> int:
    pid = _read_pid()
    if pid and _is_alive(pid):
        print(f"daemon already running pid={pid}")
        return 0
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    log_handle = open(LOG_FILE, "a", encoding="utf-8")
    log_handle.write(
        f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] spawning daemon interval={interval}s\n"
    )
    log_handle.flush()
    creationflags = 0
    if os.name == "nt":
        creationflags = (
            subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS  # type: ignore[attr-defined]
        )
    proc = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "loop", "--interval", str(interval)],
        stdout=log_handle,
        stderr=log_handle,
        stdin=subprocess.DEVNULL,
        close_fds=True,
        creationflags=creationflags,
        cwd=str(REPO_ROOT),
    )
    PID_FILE.write_text(str(proc.pid), encoding="utf-8")
    print(f"daemon started pid={proc.pid} interval={interval}s log={LOG_FILE}")
    return 0


def cmd_stop() -> int:
    pid = _read_pid()
    if not pid:
        print("no PID file; daemon not running")
        return 0
    if not _is_alive(pid):
        print(f"PID {pid} stale (process gone); removing PID file")
        try:
            PID_FILE.unlink()
        except OSError:
            pass
        return 0
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], stdout=subprocess.DEVNULL)
    else:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
    time.sleep(0.5)
    try:
        PID_FILE.unlink()
    except OSError:
        pass
    _log(f"daemon stopped pid={pid}")
    print(f"daemon stopped pid={pid}")
    return 0


def cmd_status() -> int:
    pid = _read_pid()
    last_hash = (
        LAST_HASH_FILE.read_text(encoding="utf-8").strip()
        if LAST_HASH_FILE.is_file()
        else None
    )
    state = {
        "pid_file": str(PID_FILE),
        "pid": pid,
        "alive": _is_alive(pid) if pid else False,
        "last_hash": last_hash,
        "log": str(LOG_FILE),
    }
    print(json.dumps(state, indent=2))
    return 0 if state["alive"] else 1


def cmd_loop(interval: int) -> int:
    """Foreground snapshot loop. Spawned by `start` with creation flags."""
    _log(f"loop start pid={os.getpid()} interval={interval}s")
    last_hash = None
    if LAST_HASH_FILE.is_file():
        try:
            last_hash = LAST_HASH_FILE.read_text(encoding="utf-8").strip() or None
        except OSError:
            pass
    while True:
        try:
            envelope = snapshot_all()
            h = envelope_hash(envelope)
            if h != last_hash:
                path = write_snapshot(envelope)
                last_hash = h
                LAST_HASH_FILE.parent.mkdir(parents=True, exist_ok=True)
                LAST_HASH_FILE.write_text(h, encoding="utf-8")
                _log(
                    f"snapshot WRITE {path.name} workspaces={envelope['workspace_count']} errors={len(envelope['errors'])} hash={h[:12]}"
                )
            else:
                _log(f"snapshot no-change hash={h[:12]}")
        except Exception as e:  # noqa: BLE001
            _log(f"snapshot ERROR {type(e).__name__}: {e}")
        time.sleep(interval)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lazarus_topology_daemon")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_start = sub.add_parser("start")
    p_start.add_argument("--interval", type=int, default=DEFAULT_INTERVAL)
    sub.add_parser("stop")
    sub.add_parser("status")
    p_loop = sub.add_parser("loop")
    p_loop.add_argument("--interval", type=int, default=DEFAULT_INTERVAL)
    args = parser.parse_args(argv)
    if args.cmd == "start":
        return cmd_start(args.interval)
    if args.cmd == "stop":
        return cmd_stop()
    if args.cmd == "status":
        return cmd_status()
    if args.cmd == "loop":
        return cmd_loop(args.interval)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
