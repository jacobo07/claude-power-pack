#!/usr/bin/env python3
"""Durable Goal storage: one file per Goal, plus an append-only event log.

The Goal is the only state the spine writes. Everything else it needs is read
from its owner at the moment it is needed (see goal.py).

Three properties, each pinned by `tools/test_goal_spine.py`:
  * ATOMIC -- tmp + replace, so a crash mid-write leaves the previous record;
  * CORRUPT RAISES -- an unreadable record is not an absent Goal. Treating it as
    absent would let a reconciler re-declare, or skip, a Goal it cannot read;
  * SINGLE WRITER -- `save` takes the version the caller read and refuses if the
    record moved since. Two coordinators ticking the same Goal cannot both win;
    the second gets `ConflictError` and must re-read. This is the lease the estate
    did not have: ownership that expires the moment someone else writes.

Location: `~/.claude/state/goal-spine/`, overridable with GOAL_SPINE_STATE_DIR
(tests use it; production does not need to).
"""
from __future__ import annotations

import contextlib
import json
import os
import re
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .goal import Goal, now_iso

_GOAL_ID_RE = re.compile(r"^g-[0-9a-f]{12}$")
TICK_LEASE_SECONDS = 900


class ConflictError(RuntimeError):
    """The record changed after the caller read it."""


class LockBusy(RuntimeError):
    """Another coordinator holds this Goal's tick lock."""


@contextlib.contextmanager
def tick_lock(goal_id: str, *, ttl_s: int = TICK_LEASE_SECONDS):
    """Exclusive, expiring lock over one Goal's whole reconciliation.

    The version CAS alone is NOT a lease: it fences only writers that read before
    it, so a second coordinator loading AFTER the first one's claim succeeded and
    both prepared epochs for the same obligation (found by adversarial audit,
    2026-09-22). A lock has to span load -> decide -> save, which a compare-and-set
    on a single write cannot.

    O_CREAT|O_EXCL is atomic on Windows and POSIX alike. The lock EXPIRES, because
    a coordinator killed mid-tick must not park a Goal forever; a holder past its
    ttl is taken over, and the takeover is recorded in the lock file it replaces.
    """
    p = _goal_path(goal_id).with_suffix(".lock")
    p.parent.mkdir(parents=True, exist_ok=True)
    mine = f"{os.getpid()}:{uuid.uuid4().hex[:8]}"
    fd = None
    try:
        try:
            fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                held = json.loads(p.read_text(encoding="utf-8"))
                until = datetime.strptime(held["until"], "%Y-%m-%dT%H:%M:%SZ").replace(
                    tzinfo=timezone.utc)
            except (OSError, ValueError, KeyError):
                until = datetime.now(timezone.utc)       # unreadable lock: treat as expired
            if datetime.now(timezone.utc) < until:
                raise LockBusy(f"{goal_id} is being ticked by {held.get('owner', '?')} "
                               f"until {held['until']}") from None
            with contextlib.suppress(OSError):
                p.unlink()
            time.sleep(0.01)
            try:
                fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                raise LockBusy(f"{goal_id}: another coordinator took the expired lock") from None
        until = (datetime.now(timezone.utc) + timedelta(seconds=ttl_s)).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        os.write(fd, json.dumps({"owner": mine, "until": until}).encode("utf-8"))
        os.close(fd)
        fd = None
        yield mine
    finally:
        if fd is not None:
            with contextlib.suppress(OSError):
                os.close(fd)
        try:
            if p.is_file() and json.loads(p.read_text(encoding="utf-8")).get("owner") == mine:
                p.unlink()
        except (OSError, ValueError):
            pass


def state_dir() -> Path:
    override = os.environ.get("GOAL_SPINE_STATE_DIR")
    return Path(override) if override else Path.home() / ".claude" / "state" / "goal-spine"


def _goal_path(goal_id: str) -> Path:
    if not _GOAL_ID_RE.match(goal_id or ""):
        raise ValueError(f"invalid goal id {goal_id!r}")
    return state_dir() / f"{goal_id}.json"


def exists(goal_id: str) -> bool:
    return _goal_path(goal_id).is_file()


def load(goal_id: str) -> Goal:
    p = _goal_path(goal_id)
    if not p.is_file():
        raise FileNotFoundError(f"no goal {goal_id} under {state_dir()}")
    try:
        raw = json.loads(p.read_text(encoding="utf-8-sig"))
        return Goal.from_dict(raw)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise RuntimeError(f"goal record {p} is unreadable: {exc}") from exc


def save(goal: Goal, *, expected_version: int) -> Goal:
    """Write `goal` iff the stored record is still at `expected_version`.

    A new Goal is saved with expected_version=0. On success the returned Goal
    carries the new version; the caller must use it for its next save.
    """
    p = _goal_path(goal.goal_id)
    current = load(goal.goal_id).version if p.is_file() else 0
    if current != expected_version:
        raise ConflictError(
            f"{goal.goal_id} is at version {current}, caller read {expected_version}")
    goal.version = expected_version + 1
    p.parent.mkdir(parents=True, exist_ok=True)
    # A PER-WRITER temp name. A single shared `<id>.json.tmp` is two processes
    # writing one file before either replaces it, so a torn or foreign payload can
    # land under the winner's name. The version check above is still check-then-act
    # and is NOT a lock -- `tick_lock` is what serialises a whole reconciliation.
    tmp = p.with_suffix(f".{os.getpid()}.{uuid.uuid4().hex[:8]}.tmp")
    tmp.write_text(json.dumps(goal.to_dict(), indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    tmp.replace(p)
    return goal


def list_goals() -> list[str]:
    d = state_dir()
    if not d.is_dir():
        return []
    return sorted(p.stem for p in d.glob("g-*.json") if _GOAL_ID_RE.match(p.stem))


def append_event(goal_id: str, kind: str, **fields) -> dict:
    """Append one event. The log is evidence of what happened, never state."""
    ev = {"ts": now_iso(), "goal_id": goal_id, "kind": kind, **fields}
    d = state_dir()
    d.mkdir(parents=True, exist_ok=True)
    with (d / "events.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(ev, ensure_ascii=False, sort_keys=True) + "\n")
    return ev


def events(goal_id: str | None = None) -> list[dict]:
    f = state_dir() / "events.jsonl"
    if not f.is_file():
        return []
    out = []
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        ev = json.loads(line)
        if goal_id is None or ev.get("goal_id") == goal_id:
            out.append(ev)
    return out
