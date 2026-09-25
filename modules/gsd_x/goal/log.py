#!/usr/bin/env python3
"""The goal event log: the ONE durable record a goal owns.

A goal outlives every session, worktree and worker that touches it, so its
truth cannot live in any of them. It lives here, as an append-only sequence of
events under ``~/.claude/state/gsd-x/goals/<repo-id>/<goal-id>/`` -- the same
host-state convention the long-run ledger already uses, visible to every pane
and every worktree of the repository, and therefore not split by branch.

Three properties, each one a failure this estate has already paid for:

  * **Content-complete compare-and-swap.** An event is written to a temp file,
    flushed and fsynced, and only then LINKED onto its sequence name. Exclusive
    create on the final name would reserve the number before its content
    existed, and a crash in between leaves a truncated event that either wedges
    the goal or is silently dropped. Linking publishes all of it or none of it.
  * **Three outcomes, never two.** ``FileExistsError`` means another writer won
    that sequence number: the loser must RE-READ and RE-DERIVE, never append its
    stale decision at the next number. A sharing violation (``PermissionError``,
    an antivirus or indexer handle on Windows) proves nothing either way and is
    reported as inconclusive -- reading it as "lost" or as "won" would both lie.
  * **A hash chain.** Each event carries the digest of its predecessor. A gap,
    a truncation, an edited event or a restore from a diverged export is
    detected at read time and raised. An unreadable log is never an empty log:
    "no events" from a corrupt store would let a goal restart from nothing.

The repository is identified by its ROOT COMMIT, not its path: repositories
here get moved, and a path-derived id would orphan every goal on a rename.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

EVENT_RE = re.compile(r"^(\d{6})\.json$")
GOAL_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
ENV_ROOT = "GSDX_GOALS_ROOT"          # tests and alternate hosts only


class GoalLogError(Exception):
    """Base for every goal-log failure."""


class GoalLogCorrupt(GoalLogError):
    """The log cannot be read as a complete, unbroken chain. Never 'empty'."""


class LostRace(GoalLogError):
    """Another writer published this sequence number first. Re-read, re-derive."""


class Inconclusive(GoalLogError):
    """The write could not be judged (sharing violation, transient I/O)."""


class RepoIdUnknown(GoalLogError):
    """The repository identity could not be established."""


def repo_id(root: Path) -> str:
    """The repository's root commit hash.

    Stable across moves, renames and clones. A repository with more than one
    root commit has no single identity and is refused rather than guessed.

    ONE implementation: `modules.repo_identity.identity.portable_repo_id` (UWCP
    S1-3). This wrapper keeps the goal spine's own error type for its callers.
    """
    from modules.repo_identity.identity import PortableIdUnknown, portable_repo_id
    try:
        return portable_repo_id(Path(root))
    except PortableIdUnknown as exc:
        raise RepoIdUnknown(str(exc)) from exc


def goals_root() -> Path:
    env = os.environ.get(ENV_ROOT, "").strip()
    return Path(env) if env else Path.home() / ".claude" / "state" / "gsd-x" / "goals"


def _canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def event_digest(event: dict) -> str:
    body = {k: v for k, v in event.items() if k != "digest"}
    return hashlib.sha256(_canonical(body)).hexdigest()


@dataclass(frozen=True)
class Event:
    seq: int
    type: str
    ts: str
    actor: str
    data: dict
    prev_digest: str
    digest: str

    @classmethod
    def from_dict(cls, d: dict) -> "Event":
        return cls(int(d["seq"]), str(d["type"]), str(d["ts"]), str(d["actor"]),
                   dict(d.get("data") or {}), str(d["prev_digest"]), str(d["digest"]))

    def to_dict(self) -> dict:
        return {"seq": self.seq, "type": self.type, "ts": self.ts, "actor": self.actor,
                "data": self.data, "prev_digest": self.prev_digest, "digest": self.digest}


GENESIS = "0" * 64


class GoalLog:
    """One goal's events. Stateless: every call reads the disk."""

    def __init__(self, repo: str, goal_id: str, base: Path | None = None):
        if not GOAL_ID_RE.match(goal_id or ""):
            raise GoalLogError(f"invalid goal id {goal_id!r} (lowercase, digits, . _ -)")
        if not re.fullmatch(r"[0-9a-f]{7,64}", repo or ""):
            raise GoalLogError(f"invalid repo id {repo!r}")
        self.repo, self.goal_id = repo, goal_id
        self.dir = (base or goals_root()) / repo / goal_id

    def exists(self) -> bool:
        return (self.dir / f"{1:06d}.json").is_file()

    def read(self) -> list[Event]:
        """Every event, verified as one unbroken chain from genesis."""
        if not self.dir.is_dir():
            return []
        numbered = []
        for p in self.dir.iterdir():
            m = EVENT_RE.match(p.name)
            if m:
                numbered.append((int(m.group(1)), p))
        numbered.sort()
        events: list[Event] = []
        prev = GENESIS
        for expected, (seq, path) in enumerate(numbered, start=1):
            if seq != expected:
                raise GoalLogCorrupt(f"{self.dir}: sequence gap, expected {expected} found {seq}")
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise GoalLogCorrupt(f"{path}: unreadable event: {exc}") from exc
            if raw.get("digest") != event_digest(raw):
                raise GoalLogCorrupt(f"{path}: content does not match its digest")
            if raw.get("prev_digest") != prev or int(raw.get("seq", -1)) != seq:
                raise GoalLogCorrupt(f"{path}: chain broken at seq {seq}")
            ev = Event.from_dict(raw)
            events.append(ev)
            prev = ev.digest
        return events

    def append(self, expected_seq: int, type_: str, data: dict, actor: str) -> Event:
        """Publish event number ``expected_seq`` or raise.

        ``expected_seq`` is the caller's claim about the state it decided on:
        it must be exactly one past the last event it read. A caller that read
        stale state loses here instead of writing a decision computed on it.
        """
        events = self.read()
        if expected_seq != len(events) + 1:
            raise LostRace(f"{self.goal_id}: expected to write seq {expected_seq}, "
                           f"log is at {len(events)}")
        body = {
            "seq": expected_seq,
            "type": type_,
            "ts": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "data": data,
            "prev_digest": events[-1].digest if events else GENESIS,
        }
        body["digest"] = event_digest(body)
        return self.publish(body)

    def publish(self, body: dict) -> Event:
        """Publish a PREPARED event onto its sequence name, or raise.

        Split out from `append` so the compare-and-swap can be driven directly.
        `append`'s pre-read is a cheap early-out, NOT the guarantee: two writers
        that both pass it must still be separated here. A test that only races
        `append` catches a broken publish when the two happen to overlap and
        misses it when they serialise -- measured 2026-09-22, where exactly that
        made a mutation drill report a mutant as caught by luck.
        """
        expected_seq = int(body["seq"])
        self.dir.mkdir(parents=True, exist_ok=True)
        target = self.dir / f"{expected_seq:06d}.json"
        tmp = self.dir / f".tmp-{uuid.uuid4().hex}"
        try:
            with open(tmp, "xb") as fh:
                fh.write(json.dumps(body, indent=2, ensure_ascii=False).encode("utf-8"))
                fh.flush()
                os.fsync(fh.fileno())
            try:
                os.link(tmp, target)            # atomic, refuses an existing name
            except FileExistsError:
                raise LostRace(f"{self.goal_id}: seq {expected_seq} already published")
            except PermissionError as exc:
                raise Inconclusive(f"{target}: sharing violation: {exc}") from exc
            except OSError:
                # Filesystems without hard links: rename also refuses an existing
                # target on Windows. On POSIX it would overwrite, so re-check.
                if target.exists():
                    raise LostRace(f"{self.goal_id}: seq {expected_seq} already published")
                os.rename(tmp, target)
        finally:
            # A leftover temp file is harmless (read() ignores it) and must not
            # replace the outcome already decided above, whichever it was.
            try:
                tmp.unlink(missing_ok=True)
            except OSError as exc:
                print(f"goal-log: temp not removed ({exc})", file=__import__("sys").stderr)
        return Event.from_dict(body)
