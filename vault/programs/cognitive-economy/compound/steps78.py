#!/usr/bin/env python
"""steps78.py -- pillar L: the transactional tail of /cpp-compound (steps 7+8), compiled out of prose.

`commands/compound.md` step 7 used to ask the model to do, by hand, a mutex + merge + atomic write + marker
delete. The parts that need no judgement are done here:

  1. acquire the mkdir mutex `<state>.lock` (stale after STALE_S, give up after --timeout: nothing written);
  2. back up the state file's exact bytes to a sibling `<state>.bak`;
  3. MERGE the project's entry, never replace it: `{**old, last_run_iso, directive_count: 0}`.
     JSON keys are case-sensitive: the live file holds project ids that differ only by case
     (`C--Users-...` and `c--Users-...`); a case-folding parser (PowerShell ConvertFrom-Json) refuses or
     merges them, so this module is Python and every other key is carried through untouched;
  4. write a sibling tmp, fsync, `os.replace` over the state file (retried on a Windows sharing violation);
  5. unlink the marker `LEARNINGS_PENDING.md` (absent is fine). Any other unlink failure ROLLS BACK:
     the backup's bytes are restored over the state file, so cursor and marker stay consistent;
  6. release the mutex (always, once acquired).

The project id is derived HERE from --cwd with the sentinel's exact rule (hooks/learning-sentinel.js
resolveProject: drive letter up, then every char outside [a-zA-Z0-9-] becomes '-'). A model slugging the
path by hand is how one project came to own two cursor entries (2026-09-10).

    python steps78.py --state PATH --cwd DIR --marker PATH [--timeout S] [--now ISO]
    python steps78.py --cwd DIR --print-pid

Prints one JSON object. `action` is one of: advanced, busy, bad_state, read_failed, write_failed,
rolled_back, rollback_failed. Exit 0 only for `advanced`.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

STALE_S = 30
TIMEOUT_S = 5.0
POLL_S = 0.1
REPLACE_TRIES = 3
REPLACE_BACKOFF_S = 0.2


class Busy(Exception):
    """The mutex could not be acquired in time: nothing was written."""


def pid_for(cwd: str) -> str:
    """The sentinel's project id for `cwd` (learning-sentinel.js canonicalCwd + resolveProject)."""
    if re.match(r"^[a-z]:", cwd):
        cwd = cwd[0].upper() + cwd[1:]
    return re.sub(r"[^a-zA-Z0-9-]", "-", cwd)


def acquire(lock: Path, timeout: float = TIMEOUT_S, stale_s: float = STALE_S) -> None:
    deadline = time.monotonic() + timeout
    while True:
        try:
            os.mkdir(lock)
            return
        except FileExistsError:
            try:
                if time.time() - lock.stat().st_mtime > stale_s:
                    os.rmdir(lock)
                    continue
            except FileNotFoundError:
                continue
            except OSError:
                pass
        if time.monotonic() >= deadline:
            raise Busy(f"{lock} held for > {timeout}s")
        time.sleep(POLL_S)


def write_atomic(path: Path, data: bytes) -> None:
    """Sibling tmp + fsync + os.replace. A PermissionError on the replace (a reader holding the file on
    Windows) is retried; on final failure the tmp is removed and the error propagates."""
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    try:
        with open(tmp, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        for attempt in range(REPLACE_TRIES):
            try:
                os.replace(tmp, path)
                return
            except PermissionError:
                if attempt == REPLACE_TRIES - 1:
                    raise
                time.sleep(REPLACE_BACKOFF_S)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
        except OSError:
            pass


def finalize(state: Path, project: str, marker: Path, now_iso: str | None = None,
             timeout: float = TIMEOUT_S, stale_s: float = STALE_S) -> dict:
    """Steps 7.1-7.5 + marker delete as one transaction. Returns {"ok", "action", ...}."""
    now_iso = now_iso or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    lock = state.with_name(state.name + ".lock")
    try:
        acquire(lock, timeout, stale_s)
    except Busy as exc:
        return {"ok": False, "action": "busy", "detail": str(exc)}
    try:
        try:
            original = state.read_bytes()
        except OSError as exc:
            return {"ok": False, "action": "read_failed", "detail": repr(exc)}
        try:
            doc = json.loads(original.decode("utf-8-sig"))
        except ValueError as exc:
            return {"ok": False, "action": "bad_state", "detail": str(exc)}
        if not isinstance(doc, dict) or not isinstance(doc.get("projects", {}), dict):
            return {"ok": False, "action": "bad_state", "detail": "projects is not an object"}
        backup = state.with_name(state.name + ".bak")
        projects = doc.setdefault("projects", {})
        old = projects.get(project) if isinstance(projects.get(project), dict) else {}
        projects[project] = {**old, "last_run_iso": now_iso, "directive_count": 0}
        try:
            backup.write_bytes(original)
            write_atomic(state, (json.dumps(doc, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
        except OSError as exc:
            return {"ok": False, "action": "write_failed", "detail": repr(exc)}
        try:
            marker.unlink()
        except FileNotFoundError:
            pass
        except OSError as exc:
            try:
                write_atomic(state, original)
            except OSError as exc2:
                return {"ok": False, "action": "rollback_failed",
                        "detail": f"marker unlink failed: {exc!r}; restore failed: {exc2!r}",
                        "backup": str(backup)}
            return {"ok": False, "action": "rolled_back", "detail": f"marker unlink failed: {exc!r}"}
        return {"ok": True, "action": "advanced", "project": project, "last_run_iso": now_iso,
                "backup": str(backup)}
    finally:
        try:
            os.rmdir(lock)
        except OSError:
            pass


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--state")
    ap.add_argument("--cwd", required=True, help="the project directory; the id is derived from it")
    ap.add_argument("--marker")
    ap.add_argument("--timeout", type=float, default=TIMEOUT_S,
                    help=f"seconds to wait for the mutex; above {STALE_S} a stale lock is always reclaimed")
    ap.add_argument("--now")
    ap.add_argument("--print-pid", action="store_true", help="print the project id and exit")
    a = ap.parse_args(argv)
    pid = pid_for(a.cwd)
    if a.print_pid:
        print(json.dumps({"ok": True, "action": "pid", "project": pid}))
        return 0
    if not a.state or not a.marker:
        ap.error("--state and --marker are required unless --print-pid")
    res = finalize(Path(a.state), pid, Path(a.marker), a.now, timeout=a.timeout)
    print(json.dumps(res))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
