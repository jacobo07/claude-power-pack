#!/usr/bin/env python3
"""Execution epochs -- one bounded unit of work serving one Goal revision.

An epoch is not the Goal. It is born PREPARED, bound to (goal_id, revision) and to
a structured fingerprint, and it ends COMPLETED, ABANDONED or STALE. The Goal
outlives every one of them.

TWO KINDS OF PROVIDER, TWO START CONTRACTS
------------------------------------------
* AUTONOMOUS (verify, codex): the spine launches and owns the process, so it
  marks STARTED itself at launch. Nothing else can.
* WORKER (gsd_long): the spine CANNOT start the run. Arming a marker starts
  nothing, and the resume daemon types into whichever window has focus (audit
  gap 6). So the spine prepares an instruction and waits. A worker pane CLAIMS
  the epoch by id -- an act specific to this epoch that unrelated work cannot
  perform -- and the epoch becomes STARTED only when THAT claimed session's own
  transcript shows the prepared command submitted after the claim.

  The command check reuses `/cpp-gsd-long`'s detector
  (`tools/gsd_long_run.user_issued_command_since`) rather than a second transcript
  parser. That detector matches the command NAME only; the claim is what binds it
  to this epoch (audit gap 7: "first transcript activity" is satisfied by a pane's
  own unrelated work, and `resume_confirmed` fires only at the first compaction).

FINGERPRINT (audit gap 12): structured fields only -- provider, scope, the
obligations digest. A reworded hypothesis cannot mint a fresh fingerprint and so
cannot reset the retry refusal the reconciler enforces.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import goal as gl
from . import store as gs

PREPARED = "PREPARED"
CLAIMED = "CLAIMED"          # a worker session took this epoch by id
STARTED = "STARTED"
COMPLETED = "COMPLETED"
ABANDONED = "ABANDONED"      # lease expired, or the worker vanished
STALE = "STALE"              # the Goal revised under it

AUTONOMOUS_PROVIDERS = frozenset({"verify", "codex"})
WORKER_PROVIDERS = frozenset({"gsd_long"})
PROVIDERS = AUTONOMOUS_PROVIDERS | WORKER_PROVIDERS
OPEN_STATES = frozenset({PREPARED, CLAIMED, STARTED})

_EPOCH_ID_RE = re.compile(r"^e-[0-9a-f]{12}$")
_PP_ROOT = Path(__file__).resolve().parents[2]

# How long an epoch may sit before the reconciler gives up on it. A worker epoch
# waits for a human to open a pane, so it is generous; an autonomous epoch should
# be executed by its runner within the same tick, so it is short.
UNCLAIMED_LEASE_HOURS = 48.0
AUTONOMOUS_LEASE_HOURS = 2.0


def fingerprint(provider: str, scope: list[str], obligations_digest: str) -> str:
    canon = json.dumps({"provider": provider, "scope": sorted(scope),
                        "state": obligations_digest}, sort_keys=True)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:16]


@dataclass
class Epoch:
    epoch_id: str
    goal_id: str
    goal_revision: int
    provider: str
    scope: list[str]                     # obligation ids this epoch works on
    fingerprint: str
    state: str = PREPARED
    command: str = ""                    # worker: the exact instruction to run
    cwd: str = ""
    prepared_at: str = ""
    claimed_by: str = ""                 # worker session id
    claimed_at: str = ""
    started_at: str = ""
    ended_at: str = ""
    lease_expires_at: str = ""
    outcome: str = ""                    # why it ended
    receipts: list[str] = field(default_factory=list)
    version: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


def _parse(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _epochs_dir() -> Path:
    return gs.state_dir() / "epochs"


def _path(epoch_id: str) -> Path:
    if not _EPOCH_ID_RE.match(epoch_id or ""):
        raise ValueError(f"invalid epoch id {epoch_id!r}")
    return _epochs_dir() / f"{epoch_id}.json"


def prepare(goal: gl.Goal, provider: str, scope: list[str], obligations_digest: str,
            *, command: str = "", cwd: str = "") -> Epoch:
    if provider not in PROVIDERS:
        raise ValueError(f"unknown provider {provider!r}")
    if not scope:
        raise ValueError("an epoch must name the obligations it works on")
    unknown = set(scope) - set(goal.required_obligation_ids)
    if unknown:
        raise ValueError(f"scope names obligations the Goal does not declare: {sorted(unknown)}")
    if provider in WORKER_PROVIDERS and not command.startswith("/"):
        raise ValueError("a worker epoch needs the exact slash command the pane will run")
    now = gl.now_iso()
    fp = fingerprint(provider, scope, obligations_digest)
    # A NONCE, not just the clock. `now` has one-second resolution, so a replan in
    # the same second -- same Goal, same revision, same fingerprint, which is
    # exactly what abandoning an unclaimed epoch and re-preparing produces --
    # minted the SAME id and the save collided at version 0, escaping the tick
    # after its side effects. It passed alone and failed in a full run, because
    # the difference was whether the two calls straddled a second boundary.
    # Identity is per PREPARATION; refusing a duplicate attempt is the
    # fingerprint's job and serialising coordinators is the lock's.
    eid = "e-" + hashlib.sha256(
        f"{goal.goal_id}|{goal.revision}|{fp}|{now}|{uuid.uuid4().hex}".encode()).hexdigest()[:12]
    # EVERY epoch carries a lease from birth. Only `claim()` used to set one, so a
    # worker epoch no pane ever claimed -- or an autonomous epoch no runner ever
    # executed -- stayed in an open state forever: each tick answered WAIT, no
    # budget advanced and no Owner was ever told. A Goal cannot be allowed to go
    # quiet because nobody picked up its work (adversarial audit, 2026-09-22).
    hours = (UNCLAIMED_LEASE_HOURS if provider in WORKER_PROVIDERS
             else AUTONOMOUS_LEASE_HOURS)
    expires = (datetime.now(timezone.utc) + timedelta(hours=hours)).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    return Epoch(epoch_id=eid, goal_id=goal.goal_id, goal_revision=goal.revision,
                 provider=provider, scope=sorted(scope), fingerprint=fp,
                 command=command, cwd=cwd, prepared_at=now, lease_expires_at=expires)


def save(ep: Epoch, *, expected_version: int) -> Epoch:
    p = _path(ep.epoch_id)
    current = load(ep.epoch_id).version if p.is_file() else 0
    if current != expected_version:
        raise gs.ConflictError(f"{ep.epoch_id} is at version {current}, caller read {expected_version}")
    ep.version = expected_version + 1
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(f".{os.getpid()}.{uuid.uuid4().hex[:8]}.tmp")   # per-writer, never shared
    tmp.write_text(json.dumps(ep.to_dict(), indent=2) + "\n", encoding="utf-8")
    tmp.replace(p)
    return ep


def load(epoch_id: str) -> Epoch:
    p = _path(epoch_id)
    try:
        raw = json.loads(p.read_text(encoding="utf-8-sig"))
        return Epoch(**raw)
    except FileNotFoundError:
        raise
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        raise RuntimeError(f"epoch record {p} is unreadable: {exc}") from exc


def for_goal(goal_id: str) -> list[Epoch]:
    d = _epochs_dir()
    if not d.is_dir():
        return []
    out = [load(p.stem) for p in sorted(d.glob("e-*.json")) if _EPOCH_ID_RE.match(p.stem)]
    # prepared_at has one-second resolution, so it alone is not a total order: two
    # epochs prepared in the same second tied and "the last one" was whichever the
    # glob happened to return first. The id is the tiebreak.
    return sorted((e for e in out if e.goal_id == goal_id),
                  key=lambda e: (e.prepared_at, e.epoch_id))


def is_stale(ep: Epoch, goal: gl.Goal) -> bool:
    return ep.goal_revision != goal.revision


def mark_started_autonomous(ep: Epoch) -> None:
    if ep.provider not in AUTONOMOUS_PROVIDERS:
        raise PermissionError(f"{ep.provider} is a worker provider; the spine cannot start it")
    if ep.state != PREPARED:
        raise PermissionError(f"{ep.epoch_id} is {ep.state}, not PREPARED")
    ep.state, ep.started_at = STARTED, gl.now_iso()


def claim(ep: Epoch, session_id: str, *, lease_hours: float = 24.0) -> None:
    """A worker pane takes this epoch. One claim per epoch; the lease bounds it."""
    if ep.provider not in WORKER_PROVIDERS:
        raise PermissionError("only worker epochs are claimed")
    if ep.state != PREPARED:
        raise PermissionError(f"{ep.epoch_id} is {ep.state}; it was already claimed or ended")
    if not re.match(r"^[0-9a-f-]{8,64}$", session_id or ""):
        raise ValueError(f"invalid session id {session_id!r}")
    now = datetime.now(timezone.utc)
    ep.state, ep.claimed_by = CLAIMED, session_id
    ep.claimed_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    ep.lease_expires_at = (now + timedelta(hours=lease_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _detector():
    """`/cpp-gsd-long`'s own command detector, loaded from the sibling tool."""
    spec = importlib.util.spec_from_file_location(
        "_gsd_long_run_for_goal_spine", _PP_ROOT / "tools" / "gsd_long_run.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load tools/gsd_long_run.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def observe_worker_start(ep: Epoch, transcript: Path | None = None) -> bool:
    """CLAIMED -> STARTED iff the claimed session submitted the command after the claim.

    `transcript` defaults to the claimed session's own transcript, found by
    `/cpp-gsd-long`'s resolver. Any other session's transcript is irrelevant by
    construction: this function never looks at one.
    """
    if ep.state != CLAIMED:
        return False
    mod = _detector()
    path = transcript if transcript is not None else mod.find_transcript(ep.claimed_by)
    if path is None:
        return False
    since = _parse(ep.claimed_at).timestamp()
    if mod.user_issued_command_since(Path(path), ep.command, since):
        ep.state, ep.started_at = STARTED, gl.now_iso()
        return True
    return False


def lease_expired(ep: Epoch, now: datetime | None = None) -> bool:
    """True for any OPEN epoch past its lease -- PREPARED included.

    PREPARED was excluded before, which is how an epoch nobody claimed became
    immortal instead of being abandoned and replanned.
    """
    if not ep.lease_expires_at or ep.state not in OPEN_STATES:
        return False
    return (now or datetime.now(timezone.utc)) >= _parse(ep.lease_expires_at)


def end(ep: Epoch, state: str, outcome: str) -> None:
    if state not in (COMPLETED, ABANDONED, STALE):
        raise ValueError(f"{state} is not an end state")
    if ep.state not in OPEN_STATES:
        raise PermissionError(f"{ep.epoch_id} already ended as {ep.state}")
    if not outcome.strip():
        raise ValueError("an epoch ends with a stated outcome")
    ep.state, ep.outcome, ep.ended_at = state, outcome.strip(), gl.now_iso()
