#!/usr/bin/env python3
"""Process identity, liveness, process-group census, and the single-instance lock.

A pid is not an identity: the kernel reuses it. The resident therefore records
a process's START TIME beside its pid (POSIX: /proc/<pid>/stat field 22, in
clock ticks since boot) and calls a process alive only when both still match.

Three answers, never two:

  ALIVE    the pid exists and its start time equals the recorded one
  DEAD     positive evidence: the pid is absent, OR it exists with a different
           start time (a reused pid is a different process)
  UNKNOWN  anything else -- no /proc (Windows), no recorded start time, an
           unreadable stat file. UNKNOWN is never treated as DEAD: a stale lock
           or lease is reclaimed only on positive evidence.
"""
from __future__ import annotations

import json
import os
import socket
import time
import uuid
from pathlib import Path

from . import store

ALIVE, DEAD, UNKNOWN = "ALIVE", "DEAD", "UNKNOWN"

# Named lock refusals.
LOCK_HELD_ALIVE = "LOCK_HELD_ALIVE"
LOCK_HELD_UNKNOWN = "LOCK_HELD_UNKNOWN"
LOCK_UNREADABLE = "LOCK_UNREADABLE"
LOCK_RACE = "LOCK_RACE"


class ProcInfo:
    """Reads the POSIX /proc filesystem. On a host without it every answer is
    None ('cannot say'), which callers map to UNKNOWN."""

    def __init__(self, proc_root: str = "/proc"):
        self.proc_root = Path(proc_root)

    def available(self) -> bool:
        return os.name == "posix" and (self.proc_root / "self" / "stat").is_file()

    def _stat_fields(self, pid) -> list | None:
        """Fields after the parenthesised comm, so rest[k] is stat field k+3.
        Returns None when the pid is absent; raises StateUnreadable otherwise."""
        try:
            raw = (self.proc_root / str(int(pid)) / "stat").read_text(encoding="utf-8",
                                                                      errors="replace")
        except FileNotFoundError:
            return None
        except ProcessLookupError:
            return None
        except (OSError, ValueError) as exc:
            raise store.StateUnreadable(f"/proc/{pid}/stat: {exc}") from exc
        close = raw.rfind(")")
        if close < 0:
            raise store.StateUnreadable(f"/proc/{pid}/stat: no comm terminator")
        return raw[close + 1:].split()

    def exists(self, pid) -> bool | None:
        if not self.available():
            return None
        try:
            return self._stat_fields(pid) is not None
        except store.StateUnreadable:
            return None

    def start_time(self, pid) -> int | None:
        if not self.available():
            return None
        try:
            f = self._stat_fields(pid)
        except store.StateUnreadable:
            return None
        if f is None or len(f) < 20:
            return None
        return int(f[19])                      # stat field 22

    def pgid_members(self, pgid) -> list | None:
        """Live (non-zombie) pids whose process group is `pgid`; None = cannot say."""
        if not self.available() or pgid is None:
            return None
        members = []
        for entry in self.proc_root.iterdir():
            if not entry.name.isdigit():
                continue
            try:
                f = self._stat_fields(entry.name)
            except store.StateUnreadable:
                return None                  # a partial census is not a clean one
            if f is None or len(f) < 3:
                continue                     # exited during the scan
            state, pgrp = f[0], f[2]         # stat fields 3 and 5
            if state == "Z":
                continue                     # reaped-pending: not running anything
            if int(pgrp) == int(pgid):
                members.append(int(entry.name))
        return sorted(members)


def liveness(pid, recorded_start, info: ProcInfo) -> tuple[str, str]:
    if pid is None:
        return UNKNOWN, "no pid recorded"
    exists = info.exists(pid)
    if exists is None:
        return UNKNOWN, "process table not observable on this host"
    if exists is False:
        return DEAD, f"pid {pid} is absent"
    now_start = info.start_time(pid)
    if recorded_start is None or now_start is None:
        return UNKNOWN, f"pid {pid} exists but its start time cannot be compared"
    if int(now_start) != int(recorded_start):
        return DEAD, (f"pid {pid} was reused: start time {now_start} is not the recorded "
                      f"{recorded_start}")
    return ALIVE, f"pid {pid} with start time {now_start}"


def self_identity(info: ProcInfo) -> dict:
    pid = os.getpid()
    return {"pid": pid, "start_time": info.start_time(pid), "host": socket.gethostname()}


class LockRefused(Exception):
    def __init__(self, reason: str, detail: str):
        super().__init__(f"{reason}: {detail}")
        self.reason, self.detail = reason, detail


class InstanceLock:
    """Single-instance lock: an O_EXCL file holding pid + start time + token."""

    def __init__(self, path: Path, info: ProcInfo):
        self.path = Path(path)
        self.info = info
        self.token = ""
        self.reclaimed_from: dict | None = None

    def _create(self) -> bool:
        body = {**self_identity(self.info), "token": uuid.uuid4().hex, "ts": time.time()}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(str(self.path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError:
            return False
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(body))
            fh.flush()
            os.fsync(fh.fileno())
        self.token = body["token"]
        return True

    def acquire(self) -> dict:
        if self._create():
            return {"acquired": True, "reclaimed": None}
        try:
            holder = store.read_json(self.path)
        except FileNotFoundError:
            if self._create():
                return {"acquired": True, "reclaimed": None}
            raise LockRefused(LOCK_RACE, "the lock appeared and vanished; retry later")
        except store.StateUnreadable as exc:
            raise LockRefused(LOCK_UNREADABLE, f"{exc}; no evidence its holder is dead")
        if not isinstance(holder, dict):
            raise LockRefused(LOCK_UNREADABLE, f"{self.path} is not an object")
        verdict, why = liveness(holder.get("pid"), holder.get("start_time"), self.info)
        if verdict == ALIVE:
            raise LockRefused(LOCK_HELD_ALIVE, why)
        if verdict == UNKNOWN:
            raise LockRefused(LOCK_HELD_UNKNOWN, f"{why}; not reclaimed without evidence")
        # DEAD, positively. Move the stale lock aside atomically: only one
        # reclaimer can win the rename, so two cannot both believe they hold it.
        aside = self.path.parent / f"lock.stale-{uuid.uuid4().hex}"
        try:
            os.rename(self.path, aside)
        except FileNotFoundError:
            raise LockRefused(LOCK_RACE, "another process reclaimed the stale lock first")
        if not self._create():
            raise LockRefused(LOCK_RACE, "another process took the lock after the reclaim")
        self.reclaimed_from = {**holder, "evidence": why, "moved_to": aside.name}
        return {"acquired": True, "reclaimed": self.reclaimed_from}

    def held(self) -> bool:
        try:
            cur = store.read_json(self.path)
        except (FileNotFoundError, store.StateUnreadable):
            return False
        return bool(self.token) and isinstance(cur, dict) and cur.get("token") == self.token

    def release(self) -> bool:
        """Remove the lock only if it is still ours."""
        if not self.held():
            return False
        os.unlink(self.path)
        self.token = ""
        return True
