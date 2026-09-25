#!/usr/bin/env python3
"""The founder-decision relay: sign on one host, append and witness on another.

In production no single process can both SIGN a founder event and WITNESS it:
the founder's private key lives only on the Founder's workstation, the goal
store belongs to the resident, and the witness is writable only by the judge
user. `GoalLog.append` does both in one call, so it cannot run anywhere. The
relay splits it (spec: vault/specs/gdd-founder-authority.md section 10):

  * `head`            -- the log's last seq and digest, read-only;
  * `make_envelope`   -- on the workstation, sign exactly one founder-class
                         event against that head;
  * `apply_envelope`  -- on the store's host, verify it and publish it through
                         `GoalLog.append_presigned`, which uses the same
                         compare-and-swap and witness write as `append`.

An envelope is signed against ONE head. Anything that moved the log since then
makes it STALE_ENVELOPE, which is also why replaying an applied envelope is
refused: the Founder re-reads the head and re-signs. Every refusal writes
nothing.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from . import authority as au
from .log import GENESIS, Event, GoalLog, GoalLogError, LostRace

ENVELOPE_KIND = "gsdx-founder-envelope/1"
HEAD_KIND = "gsdx-goal-head/1"
ENVELOPE_FIELDS = ("kind", "repo", "goal", "seq", "prev_digest", "type", "data", "ts", "actor",
                   "key_id", "sig")

# Refusal reasons of the relay itself (signature reasons are authority's).
ENVELOPE_MALFORMED = "ENVELOPE_MALFORMED"
ENVELOPE_TYPE_NOT_FOUNDER = "ENVELOPE_TYPE_NOT_FOUNDER"
STALE_ENVELOPE = "STALE_ENVELOPE"
AUTHORITY_REQUIRED = "AUTHORITY_REQUIRED"

DECLARED, REVISED = "goal.declared", "goal.revised"


class EnvelopeRefused(au.AuthorityError):
    """The envelope was refused; nothing was written. ``reason`` names why."""

    def __init__(self, reason: str, detail: str):
        super().__init__(f"{reason}: {detail}")
        self.reason = reason


def head(log: GoalLog) -> dict:
    """The log's last event, after the whole chain has verified. Writes nothing.

    Deliberately not a projection: a goal the resident refuses (a rollback, a
    bad signature) still has a head, and refusing THAT is the apply's job, where
    the refusal is named.
    """
    events = log.read()
    last = events[-1] if events else None
    return {"kind": HEAD_KIND, "repo": log.repo, "goal": log.goal_id,
            "seq": last.seq if last else 0, "digest": last.digest if last else GENESIS}


def _require_checking_anchor(action: str) -> au.Anchor:
    anchor = au.load_anchor()
    if anchor.mode == au.ABSENT:
        raise EnvelopeRefused(AUTHORITY_REQUIRED, f"{action} needs founder authority; set "
                              f"{au.ENV_ANCHOR} to the trust anchor first")
    if anchor.mode == au.UNVERIFIABLE:
        raise EnvelopeRefused(AUTHORITY_REQUIRED, au.describe(anchor))
    return anchor


def _check_payload(seq: int, type_: str, data) -> None:
    """Refuse at SIGN time what could never be removed once signed and published."""
    if type_ not in au.FOUNDER_CLASS:
        raise EnvelopeRefused(ENVELOPE_TYPE_NOT_FOUNDER,
                              f"{type_!r} is not founder-class; only a founder decision is relayed")
    if not isinstance(data, dict):
        raise EnvelopeRefused(ENVELOPE_MALFORMED, "data must be a JSON object")
    if au.SIG_FIELD in data:
        raise EnvelopeRefused(ENVELOPE_MALFORMED, f"data must not carry {au.SIG_FIELD}; the "
                              "signature is made here")
    if (seq == 1) != (type_ == DECLARED):
        raise EnvelopeRefused(ENVELOPE_MALFORMED, f"{type_} at seq {seq}: a goal's first event is "
                              "its declaration, and a declaration is only ever its first event")
    if type_ in (DECLARED, REVISED):
        from .contract import SEMANTIC_FIELDS, revision_of   # contract imports authority, not us
        sem = data.get("semantic")
        if (not isinstance(sem, dict) or any(k not in sem for k in SEMANTIC_FIELDS)
                or data.get("revision") != revision_of(sem)):
            raise EnvelopeRefused(ENVELOPE_MALFORMED, f"{type_} needs semantic "
                                  f"{SEMANTIC_FIELDS} and revision = revision_of(semantic)")


def make_envelope(repo: str, goal: str, head_seq: int, head_digest: str, type_: str,
                  data: dict, actor: str, ts: str | None = None) -> dict:
    """Sign one founder-class event against a head, with the key named by
    ``GSDX_FOUNDER_SIGNING_KEY``. The signature is `sign_event_data`'s, i.e.
    exactly what `GoalLog.append` would have stored."""
    anchor = _require_checking_anchor("founder-sign")
    seq = int(head_seq) + 1
    _check_payload(seq, type_, data)
    GoalLog(repo, goal)                      # validates the ids; touches nothing
    ts = ts or datetime.now(timezone.utc).isoformat()
    signed = au.sign_event_data(anchor, repo, goal, seq, type_, data, head_digest, ts, actor)
    block = signed.pop(au.SIG_FIELD)
    return {"kind": ENVELOPE_KIND, "repo": repo, "goal": goal, "seq": seq,
            "prev_digest": head_digest, "type": type_, "data": signed, "ts": ts,
            "actor": actor, "key_id": block["key_id"], "sig": block["sig"]}


def write_envelope(path: Path, envelope: dict) -> None:
    """Exclusive create: an envelope is never overwritten by another decision."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0),
                 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(json.dumps(envelope, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8"))


def read_envelope(path: Path) -> dict:
    try:
        env = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EnvelopeRefused(ENVELOPE_MALFORMED, f"{path} is unreadable "
                              f"({exc.__class__.__name__})") from None
    return env


def _parse(env) -> dict:
    if not isinstance(env, dict) or env.get("kind") != ENVELOPE_KIND:
        raise EnvelopeRefused(ENVELOPE_MALFORMED, f"not a {ENVELOPE_KIND}")
    missing = [f for f in ENVELOPE_FIELDS if f not in env]
    if missing:
        raise EnvelopeRefused(ENVELOPE_MALFORMED, f"missing {missing}")
    if not isinstance(env["seq"], int) or env["seq"] < 1 or not isinstance(env["data"], dict):
        raise EnvelopeRefused(ENVELOPE_MALFORMED, "seq must be a positive integer and data an object")
    if au.SIG_FIELD in env["data"]:
        raise EnvelopeRefused(ENVELOPE_MALFORMED, f"data must not carry {au.SIG_FIELD}")
    return env


def apply_envelope(env, base: Path | None = None) -> Event:
    """Verify an envelope and publish its event, or raise EnvelopeRefused.

    Order is the spec's: anchor, signature, head, witness, publish, mark. The
    signature is checked before the head so a forged envelope is named as
    forged, not merely as stale.
    """
    anchor = _require_checking_anchor("founder-apply")
    env = _parse(env)
    if env["type"] not in au.FOUNDER_CLASS:
        raise EnvelopeRefused(ENVELOPE_TYPE_NOT_FOUNDER, f"{env['type']!r} is not founder-class")
    try:
        log = GoalLog(str(env["repo"]), str(env["goal"]), base=base)
    except GoalLogError as exc:
        raise EnvelopeRefused(ENVELOPE_MALFORMED, str(exc)) from None
    seq, prev = env["seq"], str(env["prev_digest"])
    data = {**env["data"], au.SIG_FIELD: {"key_id": env["key_id"], "sig": env["sig"]}}
    candidate = Event(seq, env["type"], str(env["ts"]), str(env["actor"]), data, prev, "")
    ok, why = au.verify_event(anchor, log.repo, log.goal_id, candidate)
    if not ok:
        raise EnvelopeRefused(au.FOUNDER_SIGNATURE_INVALID, f"{env['type']} seq {seq}: {why}")
    events = log.read()
    current_seq, current = (events[-1].seq, events[-1].digest) if events else (0, GENESIS)
    if seq != current_seq + 1 or prev != current:
        moved = "with another digest" if seq == current_seq + 1 else f"at seq {current_seq}"
        raise EnvelopeRefused(STALE_ENVELOPE, f"signed against seq {seq - 1}, the log is {moved}; "
                              "re-run head and re-sign")
    # Refuse to ratify a rollback, as `append` does; also re-checked inside
    # append_presigned against the read it publishes on.
    au.check_witness(anchor, log.repo, log.goal_id, events, governed=False)
    try:
        return log.append_presigned(seq, env["type"], data, candidate.actor, candidate.ts, prev)
    except LostRace as exc:
        # The resident (or another relay) published this seq between our read
        # and our link: nothing of ours is visible.
        raise EnvelopeRefused(STALE_ENVELOPE, f"{exc}; re-run head and re-sign") from None
