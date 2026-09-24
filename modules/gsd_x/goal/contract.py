#!/usr/bin/env python3
"""Goal Contract and revision -- the Mission Contract's missing identity.

The Mission Contract (``modules.gsd_x.mission.contract``) keys a mission by its
milestone name or, failing that, the repository name: one mission per worktree
root. That was correct for one session doing one thing. A goal spans sessions,
worktrees and executors, and one GSD milestone in this estate carries four
tracks owned by four sessions -- so a goal needs an identity of its own.

A goal's contract is REPLAYED from its event log, never stored as a document
that can drift from it. The REVISION is a hash of the fields that define what
counts as done -- intent, acceptance criteria, constraints, scope -- and of
nothing else. Budget and authority are separate event types on purpose: topping
up quota must not invalidate every piece of evidence the goal has gathered, and
a revision that moved on a budget change would do exactly that.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from .log import Event, GoalLog, GoalLogCorrupt, GoalLogError, LostRace

DECLARED = "goal.declared"
REVISED = "goal.revised"
BUDGET_SET = "goal.budget_set"
AUTHORITY_SET = "goal.authority_set"

SEMANTIC_FIELDS = ("intent", "acceptance", "constraints", "scope")


class GoalExists(GoalLogError):
    """A goal with this id is already declared in this repository."""


class GoalNotDeclared(GoalLogError):
    """The log has no declaration event."""


def _norm_list(items) -> list[str]:
    return [" ".join(str(i).split()) for i in (items or []) if str(i).strip()]


def normalise(intent: str, acceptance, constraints, scope) -> dict:
    """The semantic content, in the one form the revision hash is taken over.

    The intent is kept VERBATIM apart from whitespace: the human's own words are
    the thing a later reader must be able to see, and paraphrasing them here
    would already be deciding what the goal is about.
    """
    text = (intent or "").strip()
    if not text:
        raise GoalLogError("a goal needs its intent in the Founder's own words")
    sc = dict(scope or {})
    sc["paths"] = sorted(_norm_list(sc.get("paths")))
    return {"intent": text, "acceptance": _norm_list(acceptance),
            "constraints": _norm_list(constraints), "scope": sc}


def revision_of(semantic: dict) -> str:
    body = {k: semantic[k] for k in SEMANTIC_FIELDS}
    raw = json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


@dataclass
class GoalState:
    goal_id: str
    repo: str
    intent: str = ""
    acceptance: list = field(default_factory=list)
    constraints: list = field(default_factory=list)
    scope: dict = field(default_factory=dict)
    revision: str = ""
    revisions: list = field(default_factory=list)      # [(seq, revision)]
    budget: dict = field(default_factory=dict)
    authority: dict = field(default_factory=dict)
    last_seq: int = 0
    events: list = field(default_factory=list)

    def semantic(self) -> dict:
        return {"intent": self.intent, "acceptance": self.acceptance,
                "constraints": self.constraints, "scope": self.scope}


def project(log: GoalLog) -> GoalState:
    """Replay the log into the goal's current state. Writes nothing."""
    events = log.read()
    if not events or events[0].type != DECLARED:
        raise GoalNotDeclared(f"{log.goal_id}: no declaration event")
    st = GoalState(goal_id=log.goal_id, repo=log.repo, events=events)
    for ev in events:
        if ev.type in (DECLARED, REVISED):
            try:
                sem = ev.data["semantic"]
                st.intent, st.acceptance = sem["intent"], sem["acceptance"]
                st.constraints, st.scope = sem["constraints"], sem["scope"]
                st.revision = ev.data["revision"]
            except (KeyError, TypeError) as exc:
                # The chain proves who wrote it, not that it is well formed.
                raise GoalLogCorrupt(f"{log.goal_id} seq {ev.seq}: malformed "
                                     f"{ev.type} payload ({exc})") from exc
            st.revisions.append((ev.seq, st.revision))
        elif ev.type == BUDGET_SET:
            st.budget = dict(ev.data)
        elif ev.type == AUTHORITY_SET:
            st.authority = dict(ev.data)
        st.last_seq = ev.seq
    return st


def declare(log: GoalLog, intent: str, acceptance=None, constraints=None,
            scope=None, actor: str = "founder") -> GoalState:
    semantic = normalise(intent, acceptance, constraints, scope)
    try:
        log.append(1, DECLARED, {"semantic": semantic, "revision": revision_of(semantic)},
                   actor)
    except LostRace as exc:
        raise GoalExists(f"{log.goal_id} is already declared") from exc
    return project(log)


def revise(log: GoalLog, expected_seq: int, intent: str, acceptance=None,
           constraints=None, scope=None, actor: str = "founder") -> GoalState:
    """A meaningful change to what counts as done. Refuses a no-op revision:
    minting a new revision for identical content would stale every piece of
    evidence for nothing."""
    current = project(log)
    semantic = normalise(intent, acceptance, constraints, scope)
    rev = revision_of(semantic)
    if rev == current.revision:
        raise GoalLogError(f"{log.goal_id}: revision unchanged ({rev}); nothing to revise")
    log.append(expected_seq, REVISED, {"semantic": semantic, "revision": rev,
                                       "supersedes": current.revision}, actor)
    return project(log)


def set_budget(log: GoalLog, expected_seq: int, budget: dict, actor: str) -> GoalState:
    log.append(expected_seq, BUDGET_SET, dict(budget), actor)
    return project(log)


def set_authority(log: GoalLog, expected_seq: int, authority: dict, actor: str) -> GoalState:
    log.append(expected_seq, AUTHORITY_SET, dict(authority), actor)
    return project(log)


def last_event(state: GoalState) -> Event | None:
    return state.events[-1] if state.events else None
