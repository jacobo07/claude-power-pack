#!/usr/bin/env python3
"""The Goal record -- the one truth the Goal Spine owns.

A Goal is durable institutional state, not a session, not a GSD milestone, not a
plan file and not a `/cpp-gsd-long` run. Agents and epochs are bounded and
replaceable; the Goal persists until it converges, is superseded, is aborted by
authority, or meets a genuinely external block.

WHAT THIS MODULE OWNS, AND WHAT IT REFUSES TO OWN
-------------------------------------------------
Owned here (no other owner exists -- measured 2026-09-22, see
`vault/specs/goal-spine-v1.md`): intent, identity, revision, the outcome
contract, the declared required obligations, authority, budget and lifecycle
state.

NOT owned here: GSD phase state (GSD), obligation dispositions and closure
(GSD X `mission/`), Production Reality (the project's own verifier), Owner
decisions (`owner_queue`). This module never computes convergence. CONVERGED is
reachable only by handing it a verdict produced by `convergence.py`, which in
turn defers to GSD X's `project_closure` -- so the component being built is
never the component that grades it.

Three rules live in code rather than in a caller's memory:
  * a Goal without required obligation ids is refused at declaration, because an
    empty obligation set would let closure pass with nothing blocking it;
  * CONVERGED is not a transition anyone may request;
  * BLOCKED names an external condition from a closed set. Failing tests, an
    exhausted context and a finished epoch are not external, and cannot be
    spelled as a block.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

# --- lifecycle ----------------------------------------------------------------
DECLARED = "DECLARED"
ACTIVE = "ACTIVE"
AWAITING_WORKER = "AWAITING_WORKER"      # an epoch is prepared; no pane has started it
AWAITING_OWNER = "AWAITING_OWNER"        # a decision packet is open
BLOCKED = "BLOCKED"                      # a named external condition
HARVESTING = "HARVESTING"                # work closed; learning obligations open
CONVERGED = "CONVERGED"
SUPERSEDED = "SUPERSEDED"
ABORTED = "ABORTED"

STATES = frozenset({DECLARED, ACTIVE, AWAITING_WORKER, AWAITING_OWNER, BLOCKED,
                    HARVESTING, CONVERGED, SUPERSEDED, ABORTED})
TERMINAL = frozenset({CONVERGED, SUPERSEDED, ABORTED})

# A block is legitimate only when its cause sits outside the Factory's reach.
EXTERNAL_BLOCK_CATEGORIES = frozenset({
    "OWNER_DECISION",       # product intent or constitutional authority
    "CREDENTIAL",           # a secret or account nobody here may mint
    "HOST_RESOURCE",        # a host condition this mission does not control
    "EXTERNAL_SERVICE",     # a third party is down or refusing
    "UPSTREAM_MERGE",       # another writer's branch must land first
    "WORKER_UNAVAILABLE",   # no pane exists to run a prepared epoch
})

_ALLOWED = {
    DECLARED: {ACTIVE, ABORTED, SUPERSEDED},
    ACTIVE: {AWAITING_WORKER, AWAITING_OWNER, BLOCKED, HARVESTING, ABORTED, SUPERSEDED},
    AWAITING_WORKER: {ACTIVE, AWAITING_OWNER, BLOCKED, ABORTED, SUPERSEDED},
    AWAITING_OWNER: {ACTIVE, BLOCKED, ABORTED, SUPERSEDED},
    BLOCKED: {ACTIVE, ABORTED, SUPERSEDED},
    HARVESTING: {ACTIVE, AWAITING_OWNER, ABORTED, SUPERSEDED},
}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_intent(text: str) -> str:
    """The semantic form of an intent: whitespace is not meaning.

    Deliberately conservative. Case and punctuation are kept, because "do NOT
    migrate" and "do not migrate" should never be declared the same instruction
    by a regex. Only runs of whitespace collapse.
    """
    return " ".join((text or "").split())


def intent_digest(text: str) -> str:
    return hashlib.sha256(normalize_intent(text).encode("utf-8")).hexdigest()


_OUTCOME_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


@dataclass
class Goal:
    goal_id: str
    root: str                               # the project root the Goal is about
    intent: str                             # the human's words, verbatim
    required_obligation_ids: list[str]
    outcome_contract: list[dict]            # [{"id","text","done"}] -- the explicit backlog
    revision: int = 1
    intent_sha: str = ""
    authority: dict = field(default_factory=lambda: {"production_mutation": False})
    budget: dict = field(default_factory=lambda: {"max_epochs": 12,
                                                  "max_epochs_per_obligation": 3})
    state: str = DECLARED
    blocked_category: str = ""
    blocked_reason: str = ""
    superseded_by: str = ""
    created_at: str = ""
    updated_at: str = ""
    version: int = 0                        # optimistic-concurrency counter (store-owned)
    converged_receipt: dict = field(default_factory=dict)

    # -- derived -----------------------------------------------------------------
    @property
    def explicit_backlog_empty(self) -> bool:
        """Every explicit outcome item is done.

        Taken from the Goal's OWN outcome contract, never from whatever milestone
        GSD happens to hold in the same repository (audit gap 4: KC's STATE.md
        tracks an unrelated milestone, and a Goal must not converge because that
        one did). An empty contract is not "done" -- it is refused at declaration.
        """
        return bool(self.outcome_contract) and all(
            bool(i.get("done")) for i in self.outcome_contract)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Goal":
        known = {f for f in cls.__dataclass_fields__}
        unknown = set(d) - known
        if unknown:
            # A record from a newer writer carries fields this reader would drop
            # on the next save. Refusing is cheaper than silently losing them.
            raise ValueError(f"goal record has unknown fields {sorted(unknown)}")
        return cls(**d)


def declare(root: str, intent: str, required_obligation_ids: list[str],
            outcome_contract: list[dict], **extra) -> Goal:
    """Create a Goal. Identity is a function of the intent at declaration."""
    if not normalize_intent(intent):
        raise ValueError("a Goal needs an intent in the human's own words")
    ids = [str(i) for i in (required_obligation_ids or [])]
    if not ids:
        raise ValueError(
            "a Goal must declare the obligation ids that prove it; with none, "
            "closure has nothing to block on and would converge on an empty set")
    if len(set(ids)) != len(ids):
        raise ValueError(f"duplicate required obligation ids: {ids}")
    items = [dict(i) for i in (outcome_contract or [])]
    if not items:
        raise ValueError("a Goal needs at least one explicit outcome item")
    for i in items:
        if not _OUTCOME_ID_RE.match(str(i.get("id", ""))) or not str(i.get("text", "")).strip():
            raise ValueError(f"outcome item needs an id and text: {i!r}")
        i["done"] = bool(i.get("done", False))
    sha = intent_digest(intent)
    ts = now_iso()
    return Goal(goal_id=f"g-{sha[:12]}", root=str(root), intent=intent.strip(),
                required_obligation_ids=ids, outcome_contract=items,
                intent_sha=sha, created_at=ts, updated_at=ts, **extra)


def revise(goal: Goal, new_intent: str) -> bool:
    """Apply a Founder change. Returns True iff the semantic target moved."""
    sha = intent_digest(new_intent)
    if sha == goal.intent_sha:
        return False
    goal.intent = new_intent.strip()
    goal.intent_sha = sha
    goal.revision += 1
    goal.updated_at = now_iso()
    return True


def transition(goal: Goal, to: str, *, category: str = "", reason: str = "") -> None:
    """Move a Goal between non-terminal states. CONVERGED is not reachable here."""
    if to == CONVERGED:
        raise PermissionError(
            "CONVERGED is set only from a convergence verdict (convergence.py), "
            "never by request")
    if to not in STATES:
        raise ValueError(f"unknown state {to!r}")
    if goal.state in TERMINAL:
        raise PermissionError(f"{goal.goal_id} is {goal.state}; terminal states do not move")
    if to not in _ALLOWED.get(goal.state, set()):
        raise PermissionError(f"{goal.state} -> {to} is not an allowed transition")
    if to == BLOCKED:
        if category not in EXTERNAL_BLOCK_CATEGORIES:
            raise ValueError(
                f"BLOCKED needs an external category from "
                f"{sorted(EXTERNAL_BLOCK_CATEGORIES)}; {category!r} is work to do, "
                "not a block")
        if not reason.strip():
            raise ValueError("BLOCKED needs the missing external condition named")
        goal.blocked_category, goal.blocked_reason = category, reason.strip()
    elif goal.state == BLOCKED:
        goal.blocked_category = goal.blocked_reason = ""
    goal.state = to
    goal.updated_at = now_iso()
