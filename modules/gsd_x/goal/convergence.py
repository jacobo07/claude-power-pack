#!/usr/bin/env python3
"""Convergence planes, goal obligations, failures -- and the closure that reads them.

A goal is not done because its tasks are. It is done when every PLANE that
applies to it -- outcome, runtime reality, evidence, failures, regressions,
institutional learning, transfer -- has obligations that were proven by gates
that actually ran against the tree and revision being closed.

Three rules carry the design:

  * **Unknown is never N/A.** A plane nobody has judged stays CANDIDATE and
    blocks closure. Declaring a plane not applicable needs a stated reason, so
    "we did not think about it" cannot pass as "it does not apply".
  * **A verdict is about one tree and one revision.** Evidence gathered before
    the goal's meaning changed, or against a tree that has since moved, proves
    nothing about what is being closed, and each is refused with its own words.
  * **Reality needs a reality gate.** A Reality-plane obligation cannot be
    satisfied by a unit test that exited 0, however green.

This module reuses the Mission Contract's transition rules (narrative is not
authority; a failed gate refuses with its own reason) by calling them, and adds
only the goal-specific clauses. It computes; it never decides CONVERGED alone --
that needs the independent judge.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..mission import closure as mcl
from ..mission.obligation import (ACCEPTED, CANDIDATE, DEFERRED, NOT_APPLICABLE,
                                  REJECTED, SATISFIED, STALE)
from .contract import GoalState
from .log import GoalLog, GoalLogCorrupt, GoalLogError

OUTCOME, REALITY, EVIDENCE, FAILURE, REGRESSION = (
    "OUTCOME", "REALITY", "EVIDENCE", "FAILURE", "REGRESSION")
SETUP_LEARNING, UCR_CIF_LEARNING, TRANSFER = "SETUP_LEARNING", "UCR_CIF_LEARNING", "TRANSFER"
RECOVERY, OPERATIONAL = "RECOVERY", "OPERATIONAL"
PLANES = (OUTCOME, REALITY, EVIDENCE, FAILURE, REGRESSION, SETUP_LEARNING,
          UCR_CIF_LEARNING, TRANSFER, RECOVERY, OPERATIONAL)
# Planes that apply to every goal. They may not be declared N/A.
ALWAYS = frozenset({OUTCOME, EVIDENCE, FAILURE, REGRESSION, UCR_CIF_LEARNING})
# The kinds of observation a gate can make. Canonical here rather than in the
# provider, because acceptance validates a class long before any provider runs.
GATE_CLASSES = ("unit", "integration", "in_game", "live")
# Planes whose obligations only a runtime gate can satisfy.
RUNTIME_GATE_CLASSES = frozenset({"in_game", "live"})
REALITY_PLANES = frozenset({REALITY})
# The FAILURE plane is carried by failure events, not by obligations.
EVENT_CARRIED = frozenset({FAILURE})

PLANE_SET = "plane.applicability"
OB_ACCEPTED = "obligation.accepted"
OB_SATISFIED = "obligation.satisfied"
OB_DISPOSITIONED = "obligation.dispositioned"
OB_CARRIED = "obligation.carried"
FAILURE_RECORDED = "failure.recorded"
FAILURE_DISPOSITIONED = "failure.dispositioned"

FAILURE_DISPOSITIONS = frozenset({"fixed", "regression_added", "accepted_risk",
                                  "not_reproducible", "superseded"})
# Dispositions a person may declare on an OBLIGATION. SATISFIED is absent on
# purpose -- it is reached by a verdict and by nothing else -- and so are the
# open states, which are reached by accepting or carrying.
DECLARABLE_DISPOSITIONS = frozenset({DEFERRED, REJECTED, NOT_APPLICABLE})
# An obligation in one of these states will never be proven, so it cannot stand
# in as a plane's coverage.
RETIRED_DISPOSITIONS = DECLARABLE_DISPOSITIONS


@dataclass
class GoalObligation:
    """Duck-compatible with the Mission Contract's Obligation for transitions."""
    identifier: str
    plane: str
    text: str
    done_gate: str
    gate_pin: tuple = ()
    revision: str = ""                 # revision it was accepted (or carried) under
    disposition: str = ACCEPTED
    disposition_reason: str = ""
    verdict: dict | None = None
    # The KIND of observation this obligation's gate makes, declared by whoever
    # registered it. Never inferred from the plane: deriving it from the plane is
    # what made the reality check below tautological -- the class the check reads
    # would be the class the plane implied, so its refusing branch was
    # unreachable and a unit test could prove a production claim. Measured
    # 2026-09-23 in `sweep`, which built {"class": "in_game" if plane == REALITY}.
    gate_class: str = ""


@dataclass
class Convergence:
    planes: dict = field(default_factory=dict)          # plane -> (state, reason)
    obligations: dict = field(default_factory=dict)     # id -> GoalObligation
    failures: dict = field(default_factory=dict)        # id -> {summary, disposition, reason}


def _pin(value) -> tuple:
    return tuple(tuple(p) for p in (value or ()))


def project_convergence(state: GoalState) -> Convergence:
    cv = Convergence()
    for p in PLANES:
        cv.planes[p] = (CANDIDATE, "never judged")
    for ev in state.events:
        d = ev.data
        try:
            if ev.type == PLANE_SET:
                cv.planes[d["plane"]] = (
                    ACCEPTED if d["applicable"] else NOT_APPLICABLE, d.get("reason", ""))
            elif ev.type == OB_ACCEPTED:
                cv.obligations[d["id"]] = GoalObligation(
                    d["id"], d["plane"], d["text"], d["done_gate"], _pin(d.get("gate_pin")),
                    d["revision"], gate_class=d.get("gate_class", ""))
            elif ev.type == OB_SATISFIED:
                o = cv.obligations[d["id"]]
                o.disposition, o.verdict = SATISFIED, dict(d["verdict"])
                o.disposition_reason = d.get("reason", "")
            elif ev.type == OB_DISPOSITIONED:
                o = cv.obligations[d["id"]]
                o.disposition, o.disposition_reason = d["disposition"], d["reason"]
            elif ev.type == OB_CARRIED:
                o = cv.obligations[d["id"]]
                o.revision = d["revision"]
                if o.disposition == SATISFIED:      # its proof was about the old meaning
                    o.disposition, o.verdict = ACCEPTED, None
            elif ev.type == FAILURE_RECORDED:
                cv.failures[d["id"]] = {"summary": d["summary"], "disposition": None,
                                        "reason": "", "seq": ev.seq}
            elif ev.type == FAILURE_DISPOSITIONED:
                f = cv.failures[d["id"]]
                f["disposition"], f["reason"] = d["disposition"], d["reason"]
        except (KeyError, TypeError) as exc:
            raise GoalLogCorrupt(f"{state.goal_id} seq {ev.seq}: malformed {ev.type} "
                                 f"({exc})") from exc
    return cv


# --- writes (each one refuses what the rules forbid) ------------------------------

def set_plane(log: GoalLog, state: GoalState, plane: str, applicable: bool,
              reason: str, actor: str) -> None:
    if plane not in PLANES:
        raise GoalLogError(f"unknown plane {plane!r}")
    if not applicable and plane in ALWAYS:
        raise GoalLogError(f"{plane} applies to every goal and cannot be declared N/A")
    if not applicable and not (reason or "").strip():
        raise GoalLogError(f"declaring {plane} not applicable needs a reason")
    log.append(state.last_seq + 1, PLANE_SET,
               {"plane": plane, "applicable": bool(applicable), "reason": reason.strip()},
               actor)


def accept_obligation(log: GoalLog, state: GoalState, ob_id: str, plane: str, text: str,
                      done_gate: str, gate_pin, actor: str, gate_class: str = "") -> None:
    if plane not in PLANES or plane in EVENT_CARRIED:
        raise GoalLogError(f"{plane!r} does not take obligations")
    if not (done_gate or "").strip():
        raise GoalLogError(f"{ob_id}: an obligation needs a done gate that can settle it")
    if not gate_pin:
        raise GoalLogError(f"{ob_id}: the gate's files must be pinned at acceptance")
    if gate_class and gate_class not in GATE_CLASSES:
        raise GoalLogError(f"{ob_id}: gate class {gate_class!r} must be one of {GATE_CLASSES}")
    # Fail closed, and only here. An unstated class on a REALITY obligation is
    # "nobody said what kind of observation this is", which is not evidence that
    # a runtime one was made. Refusing at ACCEPTANCE is what makes the check in
    # `goal_closure` falsifiable: the class now comes from a person, so its
    # refusing branch is reachable by a real registration.
    if plane in REALITY_PLANES and gate_class not in RUNTIME_GATE_CLASSES:
        raise GoalLogError(
            f"{ob_id}: a {plane} obligation must declare an in_game or live gate class at "
            f"acceptance (got {gate_class or 'nothing'}); only a runtime observation can "
            "prove a reality claim, and the plane may not be used to infer that it made one")
    log.append(state.last_seq + 1, OB_ACCEPTED,
               {"id": ob_id, "plane": plane, "text": text, "done_gate": done_gate,
                "gate_pin": [list(p) for p in gate_pin], "revision": state.revision,
                "gate_class": gate_class},
               actor)


def carry_obligation(log: GoalLog, state: GoalState, ob_id: str, reason: str,
                     actor: str) -> None:
    """Explicitly keep an obligation across a revision. It is never implicit:
    a new revision changed what counts as done, and someone has to say this
    obligation still means the same thing. Its old proof does not carry --
    a SATISFIED obligation carried forward must be proven again."""
    cv = project_convergence(state)
    if ob_id not in cv.obligations:
        raise GoalLogError(f"no obligation {ob_id!r}")
    if cv.obligations[ob_id].revision == state.revision:
        raise GoalLogError(f"{ob_id} already belongs to revision {state.revision}")
    if not (reason or "").strip():
        raise GoalLogError("carrying an obligation across a revision needs a reason")
    log.append(state.last_seq + 1, OB_CARRIED,
               {"id": ob_id, "revision": state.revision, "reason": reason}, actor)


def disposition_obligation(log: GoalLog, state: GoalState, ob_id: str, disposition: str,
                           reason: str, actor: str) -> None:
    """Retire an obligation that will not be proven, with a stated reason.

    `obligation.dispositioned` has been read by the projection since C2 and
    nothing ever wrote it -- a consumer with no producer, which is
    indistinguishable from a working feature until the day it is needed.

    That day was the first real goal, 2026-09-22. Committing the job file moved
    it out of `jobs/pending/` (which the repo's own .gitignore excludes) into
    `jobs/examples/`, so `ob-outcome`'s gate pin named a path that no longer
    exists. The pin is immutable on purpose -- a changed gate proves nothing
    about the pinned one -- so the obligation could never be satisfied again,
    and with no writer here it could never be retired either. The goal could
    only escalate, correctly and forever.

    It cannot be used to wave work away quietly. SATISFIED is unreachable from
    here (only a verdict reaches it) and so are the open states (those are
    reached by accepting or carrying); a reason is required; and `goal_closure`
    does not count a retired obligation as a plane's coverage, so retiring the
    last live obligation on an applicable plane reopens that plane's block
    rather than closing it.
    """
    if disposition not in DECLARABLE_DISPOSITIONS:
        raise GoalLogError(
            f"{disposition!r} may not be declared on an obligation; declarable: "
            f"{sorted(DECLARABLE_DISPOSITIONS)}. SATISFIED is reached by a verdict, "
            "never by saying so")
    if not (reason or "").strip():
        raise GoalLogError(f"retiring {ob_id} unproven needs a reason")
    if ob_id not in project_convergence(state).obligations:
        raise GoalLogError(f"no obligation {ob_id!r}")
    log.append(state.last_seq + 1, OB_DISPOSITIONED,
               {"id": ob_id, "disposition": disposition, "reason": reason}, actor)


def record_failure(log: GoalLog, state: GoalState, fid: str, summary: str,
                   actor: str) -> None:
    if not (summary or "").strip():
        raise GoalLogError("a failure needs a stated summary")
    log.append(state.last_seq + 1, FAILURE_RECORDED, {"id": fid, "summary": summary}, actor)


def disposition_failure(log: GoalLog, state: GoalState, fid: str, disposition: str,
                        reason: str, actor: str) -> None:
    if disposition not in FAILURE_DISPOSITIONS:
        raise GoalLogError(f"unknown failure disposition {disposition!r}")
    if not (reason or "").strip():
        raise GoalLogError("a failure disposition needs a reason")
    if fid not in project_convergence(state).failures:
        raise GoalLogError(f"no recorded failure {fid!r}")
    log.append(state.last_seq + 1, FAILURE_DISPOSITIONED,
               {"id": fid, "disposition": disposition, "reason": reason}, actor)


# --- transition --------------------------------------------------------------------

def evaluate(ob: GoalObligation, verdict: mcl.Verdict | None, state: GoalState,
             narrative: str | None = None) -> mcl.TransitionResult:
    """May `ob` move to SATISFIED on this verdict, for this goal, now?"""
    if ob.revision != state.revision:
        return mcl.TransitionResult(mcl.REFUSED,
            f"{ob.identifier} was accepted under revision {ob.revision}; the goal is now "
            f"{state.revision} -- carry it forward explicitly or re-derive it")
    base = mcl.evaluate_transition(ob, verdict, narrative)
    if not base.allowed:
        return base
    if ob.plane in REALITY_PLANES and verdict.gate_class not in RUNTIME_GATE_CLASSES:
        return mcl.TransitionResult(mcl.REFUSED,
            f"{ob.identifier} is a {ob.plane} obligation; {verdict.gate!r} is class "
            f"{verdict.gate_class or 'unstated'}, and only an in_game/live gate can prove it")
    if not verdict.tree_hash:
        return mcl.TransitionResult(mcl.UNJUDGEABLE,
            f"{ob.identifier}: the verdict names no tree, so it cannot be tied to what closes")
    if verdict.revision != state.revision:
        return mcl.TransitionResult(mcl.REFUSED,
            f"{ob.identifier}: verdict is about revision {verdict.revision or 'unstated'}, "
            f"the goal is {state.revision}")
    if _pin(verdict.gate_pin) != _pin(ob.gate_pin):
        return mcl.TransitionResult(mcl.REFUSED,
            f"{ob.identifier}: the gate that ran is not the gate pinned at acceptance "
            "(its files differ) -- a changed gate proves nothing about the pinned one")
    return base


def satisfy(log: GoalLog, state: GoalState, ob_id: str, verdict: mcl.Verdict | None,
            actor: str, narrative: str | None = None) -> mcl.TransitionResult:
    cv = project_convergence(state)
    if ob_id not in cv.obligations:
        raise GoalLogError(f"no obligation {ob_id!r}")
    res = evaluate(cv.obligations[ob_id], verdict, state, narrative)
    if res.allowed:
        v = verdict
        log.append(state.last_seq + 1, OB_SATISFIED,
                   {"id": ob_id, "reason": res.reason,
                    "verdict": {"gate": v.gate, "exit_status": v.exit_status,
                                "observed": v.observed, "tree_hash": v.tree_hash,
                                "revision": v.revision, "gate_class": v.gate_class,
                                "gate_pin": [list(p) for p in v.gate_pin]}}, actor)
    return res


# --- closure -----------------------------------------------------------------------

@dataclass
class GoalClosure:
    may_close: bool
    blocking: list = field(default_factory=list)
    planes: dict = field(default_factory=dict)
    residual_risk: list = field(default_factory=list)


def goal_closure(state: GoalState, tree_hash: str, open_epochs: list | None = None) -> GoalClosure:
    """Every reason this goal may not close at `tree_hash`, or none.

    A projection: it stores nothing, and it is necessary for CONVERGED, never
    sufficient -- the independent judge re-runs the pinned gates.
    """
    cv = project_convergence(state)
    blocking: list[str] = []
    for ep in open_epochs or []:
        blocking.append(f"epoch {ep} is still open")
    for plane, (pstate, reason) in cv.planes.items():
        if pstate == CANDIDATE:
            blocking.append(f"plane {plane} was never judged applicable or not")
        elif pstate == ACCEPTED and plane not in EVENT_CARRIED:
            on_plane = [o for o in cv.obligations.values() if o.plane == plane]
            # A retired obligation is not coverage: it records a decision NOT to
            # prove that plane. Counting it would turn `disposition_obligation`
            # into a way to close a plane by retiring the only thing that could
            # have proven it -- the hole that writer would otherwise open.
            if not on_plane:
                blocking.append(f"plane {plane} applies and has no obligation")
            elif all(o.disposition in RETIRED_DISPOSITIONS for o in on_plane):
                blocking.append(f"plane {plane} applies and every obligation on it was "
                                "retired unproven")
    for o in cv.obligations.values():
        if o.disposition == SATISFIED:
            v = o.verdict or {}
            if v.get("tree_hash") != tree_hash:
                blocking.append(f"{o.identifier} was proven at tree {v.get('tree_hash')}, "
                                f"not at the tree being closed ({tree_hash})")
            if v.get("revision") != state.revision:
                blocking.append(f"{o.identifier} was proven under revision "
                                f"{v.get('revision')}, the goal is {state.revision}")
        elif o.disposition in (ACCEPTED, STALE, CANDIDATE):
            blocking.append(f"{o.identifier} ({o.plane}) is {o.disposition} -- requires "
                            f"{o.done_gate!r}")
        if o.disposition not in (DEFERRED, REJECTED, NOT_APPLICABLE) and \
                o.revision != state.revision:
            blocking.append(f"{o.identifier} belongs to revision {o.revision}")
    for fid, f in cv.failures.items():
        if not f["disposition"]:
            blocking.append(f"failure {fid} is recorded and undispositioned: {f['summary'][:80]}")
    residual = [f"{o.identifier} deferred: {o.disposition_reason}"
                for o in cv.obligations.values() if o.disposition == DEFERRED]
    residual += [f"failure {fid} accepted as risk: {f['reason']}"
                 for fid, f in cv.failures.items() if f["disposition"] == "accepted_risk"]
    return GoalClosure(not blocking, blocking, dict(cv.planes), residual)
