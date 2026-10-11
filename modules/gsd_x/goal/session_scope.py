#!/usr/bin/env python3
"""SESSION scope for the Goal Spine: obligations of a session with no goal bound.

Same store, same event format as a goal (log.py): the pseudo goal id is
``session-<sid>``, one ``NNNNNN.json`` per event under
``<goals_root>/<repo-id>/session-<sid>/``. Written atomically by ``GoalLog``
(temp file, fsync, link). A Node hook reads it with readdir + JSON.parse; each
file is one self-contained event, ``data`` holds the obligation fields.

Events: ``obligation.accepted`` (open) and ``obligation.satisfied`` (closed).
There is no declaration event, so this module folds events itself instead of
calling ``contract.project``.
"""
from __future__ import annotations

import hashlib
import re
from types import SimpleNamespace

from .convergence import (ACTIONABILITIES, OB_ACCEPTED, OB_SATISFIED, OUTCOME, SATISFIED,
                          SEVERITIES, OWNER_CLASSES, project_convergence)
from .log import GoalLog, GoalLogError, LostRace

PREFIX = "session-"
SESSION_REVISION = "session"
_MAX_RETRY = 5


class SessionScopeError(GoalLogError):
    pass


def scope_id(sid: str) -> str:
    s = re.sub(r"[^a-z0-9._-]+", "-", str(sid or "").lower()).strip("-.")
    if not s:
        raise SessionScopeError("a session id is required")
    return (PREFIX + s)[:64].rstrip("-.")


def _log(repo: str, sid: str) -> GoalLog:
    return GoalLog(repo, scope_id(sid))


def obligation_id(text: str) -> str:
    norm = " ".join(re.sub(r"[^a-z0-9 ]+", " ", str(text).lower()).split())
    return "s-" + hashlib.sha256(norm.encode("utf-8")).hexdigest()[:10]


def _fold(log: GoalLog):
    return project_convergence(SimpleNamespace(goal_id=log.goal_id, events=log.read()))


def _append(log: GoalLog, type_: str, data: dict, actor: str) -> None:
    for _ in range(_MAX_RETRY):
        try:
            log.append(len(log.read()) + 1, type_, data, actor)
            return
        except LostRace:
            continue
    raise SessionScopeError(f"{log.goal_id}: lost the append race {_MAX_RETRY} times")


def add(repo: str, sid: str, *, text: str, source: str, severity: str, actionability: str,
        owner_class: str, next_action: str, actor: str = "ewc") -> str:
    """Record an open obligation; identical text in the same session is ONE obligation."""
    if not (text or "").strip():
        raise SessionScopeError("an obligation needs text")
    if severity not in SEVERITIES:
        raise SessionScopeError(f"severity must be one of {SEVERITIES}")
    if actionability not in ACTIONABILITIES:
        raise SessionScopeError(f"actionability must be one of {ACTIONABILITIES}")
    if owner_class not in OWNER_CLASSES:
        raise SessionScopeError(f"owner_class must be one of {OWNER_CLASSES}")
    if not (next_action or "").strip():
        raise SessionScopeError("an obligation needs a next_action")
    log = _log(repo, sid)
    oid = obligation_id(text)
    if oid in _fold(log).obligations:
        return oid
    _append(log, OB_ACCEPTED,
            {"id": oid, "plane": OUTCOME, "text": text.strip(), "done_gate": "", "gate_pin": [],
             "revision": SESSION_REVISION, "gate_class": "", "scope": "SESSION",
             "source": source, "severity": severity, "actionability": actionability,
             "owner_class": owner_class, "next_action": next_action.strip()}, actor)
    return oid


def parse_verdict(verdict: str) -> dict:
    """A verdict must be '<gate that ran>: <what it observed>'. A bare 'done' is refused."""
    gate, sep, result = str(verdict or "").partition(":")
    gate, result = gate.strip(), result.strip()
    if not sep or len(gate) < 3 or not result:
        raise SessionScopeError(
            "closing needs a verdict naming the gate that ran, as '<gate>: <result>' "
            "(e.g. 'pytest tools/test_x.py: exit 0, 12 passed')")
    if gate.lower() in {"done", "ok", "fixed", "resolved", "complete", "completed", "verdict"}:
        raise SessionScopeError(f"{gate!r} is not a gate")
    return {"gate": gate, "result": result, "raw": str(verdict).strip()}


def close(repo: str, sid: str, ob_id: str, verdict: str, actor: str = "ewc") -> None:
    v = parse_verdict(verdict)
    log = _log(repo, sid)
    obs = _fold(log).obligations
    if ob_id not in obs:
        raise SessionScopeError(f"no obligation {ob_id!r} in session {sid!r}")
    if obs[ob_id].disposition == SATISFIED:
        return
    _append(log, OB_SATISFIED, {"id": ob_id, "verdict": v, "reason": v["raw"]}, actor)


def list_obligations(repo: str, sid: str) -> list[dict]:
    log = _log(repo, sid)
    out = []
    for o in _fold(log).obligations.values():
        closed = o.disposition == SATISFIED
        out.append({"id": o.identifier, "text": o.text, "source": o.source, "severity": o.severity,
                    "actionability": o.actionability, "owner_class": o.owner_class,
                    "next_action": o.next_action, "state": "closed" if closed else "open",
                    "verdict": (o.verdict or {}).get("raw", "")})
    return out
