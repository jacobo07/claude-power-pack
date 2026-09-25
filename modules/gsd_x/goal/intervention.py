#!/usr/bin/env python3
"""Operator intervention as durable goal events (UWCP S1-7).

A control surface -- this terminal today, Orca X later -- must be able to pause,
resume, cancel or annotate a Workstream without holding the session that is
running it. So intervention is an EVENT in the goal log, written with the same
compare-and-swap as everything else, and the reconciler (a pure function of the
log) honours it on its next decision. No side channel, no process signal, no
flag file that a restart forgets.

Semantics, each chosen so a race has exactly one outcome:

  * **cancel is terminal and dominates.** After it, pause/resume/cancel are
    refused. Two operators racing pause against cancel resolve by the log's CAS:
    whichever lands second re-reads, and a cancel already there wins.
  * **pause and resume must change something.** A second pause is refused, not
    silently accepted: a log full of no-op interventions hides the one that
    mattered.
  * **Pause/cancel stop NEW work only.** Recovery of a crashed dispatch and
    harvest of an ended epoch still run, so nothing in flight goes unaccounted.
    Actively stopping an epoch that is RUNNING is the provider's cancel, wired
    by the queue provider (S5); until then a running epoch finishes within its
    own wall bound and is harvested.
  * **Notes are data.** An operator note is rendered to the next epoch as a
    labelled claim by a named actor, never as authority.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .contract import GoalState, project
from .log import GoalLog, GoalLogCorrupt, GoalLogError

PAUSE, RESUME, CANCEL, NOTE = ("operator.pause", "operator.resume", "operator.cancel",
                               "operator.note")
KINDS = (PAUSE, RESUME, CANCEL, NOTE)
MAX_NOTE_CHARS = 2000


class OperatorRefused(GoalLogError):
    """The intervention would be a no-op or contradicts a terminal cancel."""


@dataclass
class OperatorState:
    paused: bool = False
    cancelled: bool = False
    last_actor: str = ""
    last_seq: int = 0
    last_reason: str = ""
    notes: list = field(default_factory=list)      # [(seq, actor, text)]


def project_operator(state: GoalState) -> OperatorState:
    op = OperatorState()
    for ev in state.events:
        if ev.type not in KINDS:
            continue
        try:
            reason = str(ev.data.get("reason", ""))
            if ev.type == NOTE:
                op.notes.append((ev.seq, ev.actor, str(ev.data["text"])))
                continue
            if op.cancelled:
                continue          # nothing after a cancel changes the state
            if ev.type == PAUSE:
                op.paused = True
            elif ev.type == RESUME:
                op.paused = False
            elif ev.type == CANCEL:
                op.cancelled, op.paused = True, False
            op.last_actor, op.last_seq, op.last_reason = ev.actor, ev.seq, reason
        except (KeyError, TypeError, AttributeError) as exc:
            raise GoalLogCorrupt(f"{state.goal_id} seq {ev.seq}: malformed {ev.type} "
                                 f"({exc})") from exc
    return op


def intervene(log: GoalLog, state: GoalState, kind: str, actor: str,
              reason: str = "", text: str = "") -> OperatorState:
    """Append one operator event on `state`, or refuse. A stale `state` loses the
    log's CAS (LostRace): re-read and decide again, never retry blindly."""
    if kind not in KINDS:
        raise OperatorRefused(f"unknown intervention {kind!r}")
    if not (actor or "").strip():
        raise OperatorRefused("an intervention needs a named actor")
    op = project_operator(state)
    if kind != NOTE and op.cancelled:
        raise OperatorRefused(f"{state.goal_id} was cancelled by {op.last_actor} at seq "
                              f"{op.last_seq}; cancellation is terminal")
    if kind == PAUSE and op.paused:
        raise OperatorRefused(f"{state.goal_id} is already paused (seq {op.last_seq})")
    if kind == RESUME and not op.paused:
        raise OperatorRefused(f"{state.goal_id} is not paused; nothing to resume")
    data: dict = {"reason": reason}
    if kind == NOTE:
        body = " ".join((text or "").split())
        if not body:
            raise OperatorRefused("an operator note needs text")
        if len(body) > MAX_NOTE_CHARS:
            raise OperatorRefused(f"note is {len(body)} chars, bound {MAX_NOTE_CHARS}")
        data["text"] = body
    log.append(state.last_seq + 1, kind, data, actor)
    return project_operator(project(log))


def blocking_reason(state: GoalState) -> str:
    """Why the reconciler must not start new work, or ''."""
    op = project_operator(state)
    if op.cancelled:
        return (f"cancelled by operator {op.last_actor} at seq {op.last_seq}"
                + (f": {op.last_reason}" if op.last_reason else ""))
    if op.paused:
        return (f"paused by operator {op.last_actor} at seq {op.last_seq}"
                + (f": {op.last_reason}" if op.last_reason else ""))
    return ""
