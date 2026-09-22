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

import json
import os
import re
from pathlib import Path

from .goal import Goal, now_iso

_GOAL_ID_RE = re.compile(r"^g-[0-9a-f]{12}$")


class ConflictError(RuntimeError):
    """The record changed after the caller read it."""


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
    tmp = p.with_suffix(".json.tmp")
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
