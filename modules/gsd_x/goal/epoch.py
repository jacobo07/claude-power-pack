#!/usr/bin/env python3
"""Bounded execution epochs, the provider contract, and receipts.

An epoch is one bounded attempt by one executor to move a goal: a Codex run in
a worktree, a headless Claude session, a deterministic gate, a /cpp-gsd-long
run a human armed. The goal outlives all of them. What the goal STORES about an
epoch is only what nobody else owns -- which revision it aimed at, its scope,
its provider, the handle to find it again, and what it harvested. Its lease,
liveness and process belong to the provider and are projected through
`observe`, never copied.

INTENT BEFORE EFFECT. A dispatch has two crash windows. Dispatch first and die
before recording it, and recovery dispatches AGAIN: a duplicate run, double
quota, two writers in one worktree. Record first and die before dispatching,
and an "open" epoch with nothing behind it blocks closure forever. So:

    append epoch.dispatching (with a pre-minted identity)
      -> provider.dispatch
      -> append epoch.running (with the provider's handle)

and recovery of a `dispatching` epoch PROBES the pre-minted identity: it adopts
a run that exists or ends the epoch LOST. It never re-dispatches on a guess.

NO RETRY WITHOUT NEW INFORMATION. Every epoch carries an information key over
what could make a second attempt different: the revision, the open gaps, the
provider, a STRUCTURED hypothesis and a hash of the goal's own scope. A key
that already failed is refused. The hypothesis is a closed vocabulary rather
than free text and the tree is hashed over declared scope paths only, because
rewording a sentence or an unrelated commit elsewhere is not new information.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

from .contract import GoalState
from .log import GoalLog, GoalLogCorrupt, GoalLogError

DISPATCHING = "epoch.dispatching"
RUNNING = "epoch.running"
ENDED = "epoch.ended"
RECEIPT = "epoch.receipt"

# Named endings. Never a bare ok/failed: "lost" (worker vanished), "expired"
# (bound reached), "cancelled" (someone decided) and "stale_revision" (the goal
# changed underneath it) need different reactions.
COMPLETED, FAILED, LOST, EXPIRED, CANCELLED, STALE_REVISION = (
    "completed", "failed", "lost", "expired", "cancelled", "stale_revision")
OUTCOMES = frozenset({COMPLETED, FAILED, LOST, EXPIRED, CANCELLED, STALE_REVISION})
UNSUCCESSFUL = frozenset({FAILED, LOST, EXPIRED})

# What a new attempt may claim is different about it. Closed on purpose.
HYPOTHESES = frozenset({"initial", "provider_change", "scope_change", "plan_change",
                        "new_failure_signature", "new_external_fact"})

# Observation states a provider may report.
OBS_RUNNING, OBS_ENDED, OBS_LOST, OBS_UNKNOWN = "running", "ended", "lost", "unknown"


class RetryWithoutNewInformation(GoalLogError):
    """This exact attempt already failed; nothing about it has changed."""


class EpochError(GoalLogError):
    pass


@dataclass(frozen=True)
class Observation:
    state: str                 # running | ended | lost | unknown
    outcome: str = ""          # when ended: one of OUTCOMES
    detail: str = ""


@dataclass
class Receipt:
    """What an executor returns. Provider-neutral: every provider fills the same
    fields, and nothing provider-specific can be read as goal truth."""
    epoch_id: str
    provider: str
    revision: str
    head_before: str = ""
    head_after: str = ""
    tree_before: str = ""
    tree_after: str = ""
    commits: list = field(default_factory=list)
    verdicts: list = field(default_factory=list)      # dicts shaped like mission Verdict
    failures: list = field(default_factory=list)      # [{"summary", "signature"}]
    cost: dict = field(default_factory=dict)
    narrative: str = ""        # stored as INPUT only; never consulted as authority

    def receipt_id(self) -> str:
        raw = json.dumps(asdict(self), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


@runtime_checkable
class Provider(Protocol):
    """The contract every executor implements. Deliberately small.

    `wall_bound_s` is mandatory: an epoch with no bound is the immortal session
    this design refuses. `probe` exists for intent-before-effect recovery.
    """
    name: str
    wall_bound_s: float

    def dispatch(self, spec: dict) -> dict: ...                  # returns a handle
    def observe(self, handle: dict) -> Observation: ...
    def harvest(self, handle: dict, spec: dict) -> Receipt: ...
    def cancel(self, handle: dict) -> None: ...
    def probe(self, identity: dict) -> dict | None: ...          # adopt a pre-crash run


def check_provider(p) -> None:
    """Refuse a provider that does not declare a positive wall bound."""
    if not isinstance(p, Provider):
        raise EpochError(f"{p!r} does not implement the provider contract")
    if not (isinstance(p.wall_bound_s, (int, float)) and p.wall_bound_s > 0):
        raise EpochError(f"provider {p.name!r} declares no wall bound")


# --- information key ---------------------------------------------------------

def scope_hash(root: Path, paths: list[str]) -> str:
    """Hash of the bytes under the goal's declared scope paths only.

    Goal bookkeeping and unrelated commits elsewhere do not move it, so they
    cannot make a failed attempt look new.
    """
    root = Path(root)
    h = hashlib.sha256()
    files: list[Path] = []
    for rel in sorted(paths or []):
        p = root / rel
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            files.extend(q for q in p.rglob("*") if q.is_file() and ".git" not in q.parts)
    for f in sorted(set(files)):
        h.update(f.relative_to(root).as_posix().encode("utf-8") + b"\0")
        h.update(hashlib.sha256(f.read_bytes()).digest())
    return h.hexdigest()[:24]


def info_key(revision: str, open_gaps: list[str], provider: str, hypothesis: str,
             scope: str, last_failure_signature: str = "", engine: str = "") -> str:
    """`engine` is the identity of the code doing the orchestrating.

    It belongs in the key because a previous attempt can fail for a reason that
    is neither the subject's nor the provider's. Measured 2026-09-22 on the first
    real goal: three gates RAN and their evidence was dropped by a defect in the
    sweep's own harvest. Retrying those gates against a fixed engine is not a
    blind retry -- the thing that failed has changed, which is exactly what "new
    information" means. It is narrow on purpose: it moves when the engine moves,
    not when any unrelated file does.
    """
    if hypothesis not in HYPOTHESES:
        raise EpochError(f"hypothesis {hypothesis!r} is not one of {sorted(HYPOTHESES)}")
    raw = json.dumps([revision, sorted(open_gaps), provider, hypothesis, scope,
                      last_failure_signature, engine], separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


# --- projection ----------------------------------------------------------------

@dataclass
class EpochRecord:
    epoch_id: str
    revision: str
    provider: str
    identity: dict
    info_key: str
    hypothesis: str
    spec: dict
    state: str = "dispatching"          # dispatching | running | ended
    handle: dict | None = None
    outcome: str = ""
    receipts: list = field(default_factory=list)


def project_epochs(state: GoalState) -> dict[str, EpochRecord]:
    eps: dict[str, EpochRecord] = {}
    for ev in state.events:
        d = ev.data
        try:
            if ev.type == DISPATCHING:
                eps[d["epoch_id"]] = EpochRecord(d["epoch_id"], d["revision"], d["provider"],
                                                 d["identity"], d["info_key"], d["hypothesis"],
                                                 d["spec"])
            elif ev.type == RUNNING:
                e = eps[d["epoch_id"]]
                e.state, e.handle = "running", d["handle"]
            elif ev.type == ENDED:
                e = eps[d["epoch_id"]]
                e.state, e.outcome = "ended", d["outcome"]
            elif ev.type == RECEIPT:
                eps[d["epoch_id"]].receipts.append(d["receipt_id"])
        except (KeyError, TypeError) as exc:
            raise GoalLogCorrupt(f"{state.goal_id} seq {ev.seq}: malformed {ev.type} "
                                 f"({exc})") from exc
    return eps


def open_epochs(state: GoalState) -> list[str]:
    return [e.epoch_id for e in project_epochs(state).values() if e.state != "ended"]


# --- writes --------------------------------------------------------------------

def begin(log: GoalLog, state: GoalState, provider: str, spec: dict, key: str,
          hypothesis: str, actor: str) -> EpochRecord:
    """Record the intent to dispatch, with an identity minted BEFORE the effect."""
    if hypothesis not in HYPOTHESES:
        raise EpochError(f"hypothesis {hypothesis!r} is not one of {sorted(HYPOTHESES)}")
    for e in project_epochs(state).values():
        if e.info_key == key and e.outcome in UNSUCCESSFUL:
            raise RetryWithoutNewInformation(
                f"epoch {e.epoch_id} already tried exactly this and ended {e.outcome}; "
                "change the provider, the scope, the plan, or bring a new fact")
        if e.info_key == key and e.state != "ended":
            raise EpochError(f"epoch {e.epoch_id} is already attempting exactly this")
    epoch_id = f"ep-{uuid.uuid4().hex[:12]}"
    identity = {"run_token": uuid.uuid4().hex, "epoch_id": epoch_id}
    log.append(state.last_seq + 1, DISPATCHING,
               {"epoch_id": epoch_id, "revision": state.revision, "provider": provider,
                "identity": identity, "info_key": key, "hypothesis": hypothesis,
                "spec": dict(spec)}, actor)
    return EpochRecord(epoch_id, state.revision, provider, identity, key, hypothesis, dict(spec))


def mark_running(log: GoalLog, state: GoalState, epoch_id: str, handle: dict,
                 actor: str) -> None:
    e = project_epochs(state).get(epoch_id)
    if e is None or e.state != "dispatching":
        raise EpochError(f"{epoch_id} is not awaiting its handle")
    log.append(state.last_seq + 1, RUNNING, {"epoch_id": epoch_id, "handle": handle}, actor)


def end(log: GoalLog, state: GoalState, epoch_id: str, outcome: str, detail: str,
        actor: str) -> None:
    if outcome not in OUTCOMES:
        raise EpochError(f"unknown outcome {outcome!r}")
    e = project_epochs(state).get(epoch_id)
    if e is None:
        raise EpochError(f"no epoch {epoch_id}")
    if e.state == "ended":
        raise EpochError(f"{epoch_id} already ended {e.outcome}")
    log.append(state.last_seq + 1, ENDED,
               {"epoch_id": epoch_id, "outcome": outcome, "detail": detail}, actor)


def ingest_receipt(log: GoalLog, state: GoalState, receipt: Receipt, actor: str) -> str:
    """Store a receipt once. A duplicate, a receipt for an unknown epoch, or one
    about another revision is refused -- the last is also a finding, recorded by
    the caller as a failure event, because a stale executor wrote it."""
    eps = project_epochs(state)
    e = eps.get(receipt.epoch_id)
    if e is None:
        raise EpochError(f"receipt for unknown epoch {receipt.epoch_id}")
    rid = receipt.receipt_id()
    if any(rid in x.receipts for x in eps.values()):
        raise EpochError(f"receipt {rid} was already ingested")
    if receipt.revision != e.revision:
        raise EpochError(f"receipt is about revision {receipt.revision}; epoch "
                         f"{e.epoch_id} targeted {e.revision}")
    log.append(state.last_seq + 1, RECEIPT,
               {"epoch_id": receipt.epoch_id, "receipt_id": rid, "receipt": asdict(receipt)},
               actor)
    return rid


def recover(log: GoalLog, state: GoalState, provider: Provider, epoch_id: str,
            actor: str) -> str:
    """Resolve an epoch left in `dispatching` by a crash between intent and effect."""
    e = project_epochs(state).get(epoch_id)
    if e is None or e.state != "dispatching":
        raise EpochError(f"{epoch_id} is not stuck in dispatching")
    handle = provider.probe(e.identity)
    if handle is not None:
        mark_running(log, state, epoch_id, handle, actor)
        return "adopted"
    end(log, state, epoch_id, LOST, "crashed between intent and dispatch; no run found", actor)
    return LOST
