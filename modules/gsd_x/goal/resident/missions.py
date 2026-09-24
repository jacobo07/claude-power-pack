#!/usr/bin/env python3
"""Mission records: the resident's operational view of one engine epoch.

A mission is 1:1 with an engine epoch (mission id == epoch id). It does NOT
carry goal truth -- the epoch's events in the goal log do. It carries what the
engine deliberately does not store and a restarted resident needs: the attempt
id, the handle, the process group and its start time, a scope unit or a
background session id, uncertainty flags and a cancel record.

Writes are compare-and-swap on a `version` field. Within the single-instance
lock that is what stops a caller holding a stale copy from overwriting a newer
record; the lock is what stops a second resident. A transition not in LEGAL
raises, so an impossible history cannot be written by accident.
"""
from __future__ import annotations

import time
from pathlib import Path

from . import store

PROPOSED, ADMITTED, ISOLATED = "PROPOSED", "ADMITTED", "ISOLATED"
DISPATCHED, RUNNING, RETURNED = "DISPATCHED", "RUNNING", "RETURNED"
HARVESTED, JUDGED, RECONCILED = "HARVESTED", "JUDGED", "RECONCILED"
CANCELLED, EXPIRED, LOST = "CANCELLED", "EXPIRED", "LOST"
STALE_REVISION, UNCERTAIN = "STALE_REVISION", "UNCERTAIN"

STATES = frozenset({PROPOSED, ADMITTED, ISOLATED, DISPATCHED, RUNNING, RETURNED, HARVESTED,
                    JUDGED, RECONCILED, CANCELLED, EXPIRED, LOST, STALE_REVISION, UNCERTAIN})
TERMINAL = frozenset({RECONCILED, CANCELLED, EXPIRED, LOST, STALE_REVISION, UNCERTAIN})
HAS_HANDLE = frozenset({DISPATCHED, RUNNING, RETURNED, HARVESTED, JUDGED})

_ENDINGS = {CANCELLED, EXPIRED, LOST, UNCERTAIN}
LEGAL = {
    PROPOSED: {ADMITTED} | _ENDINGS,
    ADMITTED: {ISOLATED, DISPATCHED} | _ENDINGS,
    ISOLATED: {DISPATCHED} | _ENDINGS,
    DISPATCHED: {RUNNING, RETURNED, STALE_REVISION} | _ENDINGS,
    RUNNING: {RETURNED, STALE_REVISION} | _ENDINGS,
    RETURNED: {HARVESTED, LOST, UNCERTAIN},
    HARVESTED: {JUDGED, RECONCILED},
    JUDGED: {RECONCILED},
}


class IllegalTransition(Exception):
    pass


class MissionConflict(Exception):
    """The record moved since the caller read it (version mismatch)."""


class MissionStore:
    def __init__(self, directory: Path):
        self.dir = Path(directory)

    def _path(self, mission_id: str) -> Path:
        if not mission_id or "/" in mission_id or "\\" in mission_id or ".." in mission_id:
            raise ValueError(f"invalid mission id {mission_id!r}")
        return self.dir / f"{mission_id}.json"

    def get(self, mission_id: str) -> dict | None:
        try:
            return store.read_json(self._path(mission_id))
        except FileNotFoundError:
            return None

    def create(self, mission_id: str, state: str, **fields) -> dict:
        if state not in (PROPOSED, ADMITTED):
            raise IllegalTransition(f"a mission is born PROPOSED or ADMITTED, not {state}")
        path = self._path(mission_id)
        if path.exists():
            raise MissionConflict(f"mission {mission_id} already exists")
        now = time.time()
        rec = {"id": mission_id, "state": state, "version": 1, "created_ts": now,
               "updated_ts": now, "uncertain": [], "history": [[state, now]], **fields}
        store.atomic_write_json(path, rec)
        return rec

    def update(self, mission_id: str, expected_version: int, state: str | None = None,
               **fields) -> dict:
        cur = self.get(mission_id)
        if cur is None:
            raise MissionConflict(f"mission {mission_id} does not exist")
        if int(cur.get("version", 0)) != int(expected_version):
            raise MissionConflict(f"mission {mission_id} is at version {cur.get('version')}, "
                                  f"caller read {expected_version}")
        now = time.time()
        if state is not None and state != cur["state"]:
            if state not in STATES:
                raise IllegalTransition(f"unknown mission state {state!r}")
            if state not in LEGAL.get(cur["state"], set()):
                raise IllegalTransition(f"{mission_id}: {cur['state']} -> {state} is not legal")
            cur["history"] = list(cur.get("history") or []) + [[state, now]]
            cur["state"] = state
        cur.update(fields)
        cur["version"] = int(cur["version"]) + 1
        cur["updated_ts"] = now
        store.atomic_write_json(self._path(mission_id), cur)
        return cur

    def advance(self, mission_id: str, state: str | None = None, **fields) -> dict:
        """Read-then-CAS in one call, for the single writer that just read it."""
        cur = self.get(mission_id)
        if cur is None:
            raise MissionConflict(f"mission {mission_id} does not exist")
        return self.update(mission_id, cur["version"], state, **fields)

    def all(self) -> list[dict]:
        if not self.dir.is_dir():
            return []
        out = []
        for p in sorted(self.dir.glob("*.json")):
            out.append(store.read_json(p))
        return out

    def non_terminal(self) -> list[dict]:
        return [m for m in self.all() if m.get("state") not in TERMINAL]
