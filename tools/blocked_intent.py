#!/usr/bin/env python
"""A2: what a BLOCKED worker is asking the host for, as a typed intent instead of free text nobody reads.

Measured on TB-FULL (2026-10-18): `surface_blocked` stored the host's "host needs: ..." sentence and nothing
consumed it. One block asked for a command nobody would type (4.6 h idle), three asked for a decision or for
files the Owner had already supplied. Each needs a different handler, and only one of them may be answered
without the Owner: a standing answer to a command request. A decision is the Owner's. Pure, no I/O.
"""
from __future__ import annotations

import re

COMMAND = "COMMAND_REQUEST"      # the worker wants a slash command typed: nobody will, answer once and continue
DECISION = "DECISION_REQUEST"    # a choice or scope acceptance: always the Owner's
RESOURCE = "RESOURCE_REQUEST"    # files, images, targets: answerable only if they were already supplied
HOST_GATE = "HOST_GATE"          # login, permission, trust: a host-side gate no directive can open
UNKNOWN = "UNKNOWN"              # unreadable: escalate, never guess

STANDING_ANSWER = ("STANDING ANSWER from the host: no one will run a command for you and the host will not type "
                   "one. Never end a turn asking the host to run a command. Take the next runnable unit from "
                   "your ROADMAP and STATE, run it through admission, commit the result and continue.")

_DECISION = re.compile(r"\b(choose|decision|decide|accept(?:ing)?|approve|which one|scope)\b|\b1\b.*\b2\b", re.I)
_HOST_GATE = re.compile(r"\b(log ?in|logged in|sign ?in|authenticat\w*|credential\w*|permission|trust(?:ed)? (?:this )?folder)\b", re.I)
_COMMAND = re.compile(r"(?:^|\s)/[a-z][\w-]+|\bslash command\b|\b(?:run|type|execute) (?:the )?command\b", re.I)
_RESOURCE = re.compile(r"\b(supply|provide|give|attach|upload)\b.*\b(image|images|file|files|target|targets|path|sheet)\b", re.I)
_SUPPLIED = re.compile(r"owner-refs|\.png\b|\.jpg\b|\bimage[s]? (?:is|are) (?:now )?(?:supplied|at)\b", re.I)


def classify(needs: str | None) -> str:
    """The kind of ask. A decision outranks a command: 'Choose 1 ... or run /x' is still the Owner's choice."""
    text = (needs or "").strip()
    if not text:
        return UNKNOWN
    if _DECISION.search(text):
        return DECISION
    # 2026-09-28 m-66ebaaa0324e: "login required -- run /login" is a host gate, not a command a standing answer
    # can skip; waking the worker over it would only repeat the block.
    if _HOST_GATE.search(text):
        return HOST_GATE
    if _COMMAND.search(text):
        return COMMAND
    if _RESOURCE.search(text):
        return RESOURCE
    return UNKNOWN


def already_supplied(directives: list[str] | None) -> bool:
    """True when an earlier Owner/host directive already points at the files the worker is asking for."""
    return any(_SUPPLIED.search(d or "") for d in (directives or []))


def intent(needs: str | None, directives: list[str] | None = None) -> dict:
    """{kind, action, answer, needs}: action is ANSWER_STANDING (deliver `answer`), REPOINT (the files already exist,
    say where) or ESCALATE_OWNER (a decision, an unsupplied resource, or something unreadable)."""
    kind = classify(needs)
    if kind == COMMAND:
        return {"kind": kind, "action": "ANSWER_STANDING", "answer": STANDING_ANSWER, "needs": needs}
    if kind == RESOURCE and already_supplied(directives):
        return {"kind": kind, "action": "REPOINT", "answer": None, "needs": needs}
    return {"kind": kind, "action": "ESCALATE_OWNER", "answer": None, "needs": needs}
