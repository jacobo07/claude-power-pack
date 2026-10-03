#!/usr/bin/env python
"""steps78.py -- pillar L: the transactional tail of /cpp-compound (steps 7+8), compiled out of prose.

`commands/compound.md` step 7 asks the model to do, by hand, a mutex + merge + atomic write + marker
delete. The pipeline stalls there about once a day; the parts that need no judgement are done here:

  1. acquire the mkdir mutex `<state>.lock` (stale after STALE_S, give up after TIMEOUT_S: nothing written);
  2. back up the state file's exact bytes to a sibling `<state>.bak`;
  3. MERGE the project's entry, never replace it: `{**old, last_run_iso, directive_count: 0}`.
     JSON keys are case-sensitive: the live file holds project ids that differ only by case
     (`C--Users-...` and `c--Users-...`); a case-folding parser (PowerShell ConvertFrom-Json) refuses or
     merges them, so this module is Python and every other key is carried through untouched;
  4. write a sibling tmp, fsync, `os.replace` over the state file;
  5. unlink the marker `LEARNINGS_PENDING.md` (absent is fine). Any other unlink failure ROLLS BACK:
     the backup's bytes are restored over the state file, so cursor and marker stay consistent;
  6. release the mutex (always, once acquired).

The caller passes every path, so the gate drives this against a TEMP copy and never the live state.

    python steps78.py --state PATH --project PID --marker PATH [--now ISO]

Exit 0 = cursor advanced and marker gone; 1 = nothing changed (lock busy, bad state, or rolled back).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

STALE_S = 30
TIMEOUT_S = 5.0
POLL_S = 0.1


class Busy(Exception):
    """The mutex could not be acquired in time: nothing was written."""


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
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    with open(tmp, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


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
        original = state.read_bytes()
        try:
            doc = json.loads(original.decode("utf-8-sig"))
        except ValueError as exc:
            return {"ok": False, "action": "bad_state", "detail": str(exc)}
        if not isinstance(doc, dict) or not isinstance(doc.get("projects", {}), dict):
            return {"ok": False, "action": "bad_state", "detail": "projects is not an object"}
        backup = state.with_name(state.name + ".bak")
        backup.write_bytes(original)
        projects = doc.setdefault("projects", {})
        old = projects.get(project) if isinstance(projects.get(project), dict) else {}
        projects[project] = {**old, "last_run_iso": now_iso, "directive_count": 0}
        write_atomic(state, (json.dumps(doc, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
        try:
            marker.unlink()
        except FileNotFoundError:
            pass
        except OSError as exc:
            write_atomic(state, backup.read_bytes())
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
    ap.add_argument("--state", required=True)
    ap.add_argument("--project", required=True)
    ap.add_argument("--marker", required=True)
    ap.add_argument("--now")
    a = ap.parse_args(argv)
    res = finalize(Path(a.state), a.project, Path(a.marker), a.now)
    print(json.dumps(res))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
