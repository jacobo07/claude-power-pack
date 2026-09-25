#!/usr/bin/env python3
"""Negative knowledge that survives session AND model replacement (UWCP S1-5).

A successor executor -- a fresh Claude session, a local Qwen epoch, a different
host -- reads the goal log and nothing else. If "we tried A, and here is why A
is false" lives only in a transcript, the successor rediscovers it for hours, or
worse, re-establishes A. So a hypothesis is an EVENT in the goal log with its
evidence refs, and its projection is what the brief renders.

Rules, each a way this estate has lost negative knowledge before:

  * **A verdict needs evidence.** `established` needs >= 1 supporting ref;
    `rejected` needs >= 1 contradicting ref. A status with no ref is an opinion.
  * **The statement is immutable.** Re-recording an id with different words is
    refused: a changed claim is a new hypothesis with a new id.
  * **Rejected stays rejected without NEW information.** Moving a rejected
    hypothesis to `open` or `established` requires a ref that was not already
    among its refs. Re-arguing the same evidence is not new information -- the
    same law as the epoch retry key (epoch.info_key).
  * **Resurrection by rewording is caught.** Opening a new id whose normalized
    statement equals a rejected one's is refused the same way.
  * **Supersession names its successor**, and the successor must exist.

Old readers ignore this event type (contract.project skips unknown types). That
is acceptable here and only here: no pre-UWCP code consulted hypotheses, so an
old reader loses nothing it ever had.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .contract import GoalState, project
from .log import GoalLog, GoalLogCorrupt, GoalLogError

HYPOTHESIS = "evidence.hypothesis"

OPEN, ESTABLISHED, REJECTED, SUPERSEDED = "open", "established", "rejected", "superseded"
STATUSES = frozenset({OPEN, ESTABLISHED, REJECTED, SUPERSEDED})
HYP_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


class HypothesisRefused(GoalLogError):
    """The hypothesis event would lose or fake negative knowledge."""


def _norm(statement: str) -> str:
    return " ".join((statement or "").lower().split())


@dataclass
class Hypothesis:
    hyp_id: str
    statement: str
    status: str
    supporting: list = field(default_factory=list)
    contradicting: list = field(default_factory=list)
    superseded_by: str = ""
    reason: str = ""
    history: list = field(default_factory=list)       # [(seq, status, actor)]

    def refs(self) -> set:
        return set(self.supporting) | set(self.contradicting)


def project_hypotheses(state: GoalState) -> dict[str, Hypothesis]:
    hyps: dict[str, Hypothesis] = {}
    for ev in state.events:
        if ev.type != HYPOTHESIS:
            continue
        d = ev.data
        try:
            h = hyps.get(d["hyp_id"])
            if h is None:
                h = hyps[d["hyp_id"]] = Hypothesis(d["hyp_id"], d["statement"], d["status"])
            h.status = d["status"]
            h.supporting = sorted(set(h.supporting) | set(d.get("supporting") or []))
            h.contradicting = sorted(set(h.contradicting) | set(d.get("contradicting") or []))
            h.superseded_by = d.get("superseded_by", "") or h.superseded_by
            h.reason = d.get("reason", "") or h.reason
            h.history.append((ev.seq, d["status"], ev.actor))
        except (KeyError, TypeError) as exc:
            raise GoalLogCorrupt(f"{state.goal_id} seq {ev.seq}: malformed {HYPOTHESIS} "
                                 f"({exc})") from exc
    return hyps


def record(log: GoalLog, state: GoalState, hyp_id: str, statement: str, status: str,
           actor: str, supporting=None, contradicting=None, superseded_by: str = "",
           reason: str = "") -> Hypothesis:
    """Append one hypothesis transition, or refuse it with the rule it breaks."""
    if not HYP_ID_RE.match(hyp_id or ""):
        raise HypothesisRefused(f"invalid hypothesis id {hyp_id!r}")
    if status not in STATUSES:
        raise HypothesisRefused(f"status {status!r} is not one of {sorted(STATUSES)}")
    text = " ".join((statement or "").split())
    if not text:
        raise HypothesisRefused("a hypothesis needs a statement")
    sup = sorted({str(r) for r in (supporting or []) if str(r).strip()})
    con = sorted({str(r) for r in (contradicting or []) if str(r).strip()})

    hyps = project_hypotheses(state)
    prior = hyps.get(hyp_id)
    if prior is not None and _norm(prior.statement) != _norm(text):
        raise HypothesisRefused(f"{hyp_id}: the statement is immutable; a changed claim "
                                "is a new hypothesis with a new id")
    if status == ESTABLISHED and not (sup or (prior and prior.supporting)):
        raise HypothesisRefused(f"{hyp_id}: established needs at least one supporting ref")
    if status == REJECTED and not (con or (prior and prior.contradicting)):
        raise HypothesisRefused(f"{hyp_id}: rejected needs at least one contradicting ref")
    if status == SUPERSEDED:
        if not superseded_by or superseded_by not in hyps or superseded_by == hyp_id:
            raise HypothesisRefused(f"{hyp_id}: superseded must name an existing successor")

    new_refs = set(sup) | set(con)
    if prior is not None and prior.status == REJECTED and status in (OPEN, ESTABLISHED):
        if not (new_refs - prior.refs()):
            raise HypothesisRefused(
                f"{hyp_id} was rejected ({'; '.join(prior.contradicting)}); reopening it "
                "needs a ref that was not already considered -- re-arguing the same "
                "evidence is not new information")
    if prior is None and status in (OPEN, ESTABLISHED):
        for other in hyps.values():
            if other.status == REJECTED and _norm(other.statement) == _norm(text):
                if not (new_refs - other.refs()):
                    raise HypothesisRefused(
                        f"{hyp_id} restates rejected {other.hyp_id}; bring a new ref or "
                        "reopen that id")

    log.append(state.last_seq + 1, HYPOTHESIS,
               {"hyp_id": hyp_id, "statement": text, "status": status,
                "supporting": sup, "contradicting": con,
                "superseded_by": superseded_by, "reason": reason}, actor)
    return project_hypotheses(project(log))[hyp_id]


def rejected(state: GoalState) -> list[Hypothesis]:
    """What a successor must NOT retry, newest first."""
    out = [h for h in project_hypotheses(state).values() if h.status == REJECTED]
    return sorted(out, key=lambda h: h.history[-1][0], reverse=True)
