#!/usr/bin/env python3
"""The resident's own durable state: where it lives and how it is written.

Two write shapes, both crash-honest:

  * **atomic replace** for documents that are read whole (heartbeat, mission
    records, leases): write a temp file in the same directory, fsync, then
    `os.replace`. A reader sees the old document or the new one, never half.
  * **append** for ledgers (intents, gain, census, escalations): one JSON line
    per write, fsynced. A crash can tear only the LAST line; `read_jsonl`
    reports a torn tail separately instead of either dropping it silently or
    refusing the whole ledger for it. A corrupt line anywhere else is raised:
    an unreadable ledger is never an empty one.
"""
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

from .. import log as gl

ENV_STATE = "GSDX_RESIDENT_STATE"


class StateUnreadable(Exception):
    """A resident state file exists and cannot be read. Never 'empty'."""


def resolve_state_dir() -> Path:
    env = os.environ.get(ENV_STATE, "").strip()
    if env:
        return Path(env)
    return gl.goals_root().parent / "resident"


def atomic_write_json(path: Path, obj) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / f".tmp-{path.name}-{uuid.uuid4().hex}"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True))
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def read_json(path: Path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise
    except (OSError, json.JSONDecodeError) as exc:
        raise StateUnreadable(f"{path}: {exc.__class__.__name__}: {exc}") from exc


def append_jsonl(path: Path, obj: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n"
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(line)
        fh.flush()
        os.fsync(fh.fileno())


def read_jsonl(path: Path) -> tuple[list, bool]:
    """(records, torn_tail). A missing ledger is empty; a corrupt one raises."""
    path = Path(path)
    if not path.is_file():
        return [], False
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise StateUnreadable(f"{path}: {exc}") from exc
    lines = raw.split("\n")
    records, torn = [], False
    for i, ln in enumerate(lines):
        if not ln.strip():
            continue
        try:
            records.append(json.loads(ln))
        except json.JSONDecodeError as exc:
            last = i == len(lines) - 1          # no trailing newline: the torn write
            if last:
                torn = True
                continue
            raise StateUnreadable(f"{path}: line {i + 1} is corrupt ({exc})") from exc
    return records, torn


class StateDir:
    """Every path the resident owns, derived from one root."""

    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root else resolve_state_dir()

    @property
    def lock(self) -> Path:
        return self.root / "lock"

    @property
    def heartbeat(self) -> Path:
        return self.root / "heartbeat.json"

    @property
    def missions(self) -> Path:
        return self.root / "missions"

    @property
    def intents(self) -> Path:
        return self.root / "intents.jsonl"

    @property
    def gain(self) -> Path:
        return self.root / "gain.jsonl"

    @property
    def escalations(self) -> Path:
        return self.root / "escalations.jsonl"

    @property
    def census(self) -> Path:
        return self.root / "census.jsonl"

    @property
    def leases(self) -> Path:
        return self.root / "leases"

    @property
    def stop(self) -> Path:
        return self.root / "STOP"

    @property
    def goals(self) -> Path:
        return self.root / "goals.json"

    @property
    def runs(self) -> Path:
        return self.root / "runs"

    def ensure(self) -> None:
        for d in (self.root, self.missions, self.leases, self.runs):
            d.mkdir(parents=True, exist_ok=True)
