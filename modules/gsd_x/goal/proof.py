#!/usr/bin/env python3
"""Proof-conserving convergence: the additive event vocabulary (spec S2-S13).

Four event types, owned here and nowhere else:

  * `obligation.contract` -- the typed proof contract for an obligation (spec S7)
  * `proof.produced`      -- a gate receipt: a proof exists for a candidate (spec S6)
  * `proof.inherited`     -- the reconciler re-derived the premises and inherits it
  * `proof.invalidated`   -- a certificate stopped holding, with the reason

Forward-compat contract (the words of evidence.py): old readers skip these types
(contract.project and every legacy projection ignore an unknown type), and no
pre-PCC code ever consulted them, so an old reader loses nothing it ever had. In
Phase 2 no legacy caller consumes this module either: zero behaviour change.

A payload carries `v`. A `v` greater than SUPPORTED_V is UNKNOWN to this engine: it
is listed in `ProofLedger.unsupported` and never raised, because a newer engine's
event must not stop an older one from reading or sweeping the goal. A malformed
payload of an own type raises GoalLogCorrupt, but only from `project_proofs`.

The event is a CLAIM. State is computed from observed premises, never from what an
event says about itself; `actor` is self-asserted, so the chain proves integrity,
not authorship.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from .contract import GoalState, project
from .log import GoalLog, GoalLogCorrupt, GoalLogError

CONTRACT = "obligation.contract"
PRODUCED = "proof.produced"
INHERITED_EV = "proof.inherited"
INVALIDATED = "proof.invalidated"
NEW_TYPES = (CONTRACT, PRODUCED, INHERITED_EV, INVALIDATED)

SUPPORTED_V = 1

# Rollback switches (spec S10). Env only, read at CALL time, never cached. ON iff the
# variable is unset/empty or one of on|1|true|yes (after strip + lower); every other
# value -- off, 0, false, a typo -- is OFF, so a typo falls back to the legacy path.
FRONTIER_SWITCH = "GSDX_FRONTIER"
INHERITANCE_SWITCH = "GSDX_PROOF_INHERITANCE"
_ON_VALUES = frozenset({"", "on", "1", "true", "yes"})


def switch_on(name: str) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return True
    return raw.strip().lower() in _ON_VALUES


def inheritance_enabled() -> bool:
    return switch_on(INHERITANCE_SWITCH)

REQUIRED_FIELDS = {
    CONTRACT: ("v", "claim_id", "obligation", "elements", "combine"),
    PRODUCED: ("v", "claim_id", "candidate", "binding", "revision", "strength", "source"),
    INHERITED_EV: ("v", "claim_id", "certificate", "candidate", "premises"),
    INVALIDATED: ("v", "claim_id", "certificate", "reason"),
}


class ProofRefused(GoalLogError):
    """The PCC event would be unreadable or unwritable by this engine."""


def check_payload(type_: str, data) -> bool:
    """True for a readable v1 payload, False for a newer `v`, ValueError when malformed."""
    if type_ not in REQUIRED_FIELDS:
        raise ValueError(f"{type_!r} is not a PCC event type")
    if not isinstance(data, dict):
        raise ValueError("payload is not an object")
    v = data.get("v")
    if isinstance(v, bool) or not isinstance(v, int):
        raise ValueError("v is missing or not an int")
    if v > SUPPORTED_V:
        return False
    missing = [k for k in REQUIRED_FIELDS[type_] if k not in data]
    if missing:
        raise ValueError(f"missing {', '.join(missing)}")
    if type_ == CONTRACT:
        el = data["elements"]
        if not isinstance(el, list) or not el or not all(isinstance(x, dict) for x in el):
            raise ValueError("elements must be a non-empty list of objects")
    return True


@dataclass
class ProofLedger:
    contracts: list = field(default_factory=list)
    produced: list = field(default_factory=list)
    inherited: list = field(default_factory=list)
    invalidated: list = field(default_factory=list)
    unsupported: list = field(default_factory=list)       # seqs of events with a newer v


def project_proofs(state: GoalState) -> ProofLedger:
    ledger = ProofLedger()
    slots = {CONTRACT: ledger.contracts, PRODUCED: ledger.produced,
             INHERITED_EV: ledger.inherited, INVALIDATED: ledger.invalidated}
    for ev in state.events:
        if ev.type not in NEW_TYPES:
            continue
        try:
            readable = check_payload(ev.type, ev.data)
        except (ValueError, KeyError, TypeError) as exc:
            raise GoalLogCorrupt(f"{state.goal_id} seq {ev.seq}: malformed {ev.type} "
                                 f"({exc})") from exc
        if not readable:
            ledger.unsupported.append(ev.seq)
            continue
        slots[ev.type].append({"seq": ev.seq, "actor": ev.actor, "ts": ev.ts,
                               "data": dict(ev.data)})
    return ledger


def append_pcc(log: GoalLog, state: GoalState, type_: str, data: dict, actor: str) -> ProofLedger:
    """Append one PCC event through the CAS writer, or refuse it with the reason."""
    if type_ not in NEW_TYPES:
        raise ProofRefused(f"{type_!r} is not a PCC event type")
    try:
        readable = check_payload(type_, data)
    except ValueError as exc:
        raise ProofRefused(f"{type_}: {exc}") from exc
    if not readable:
        raise ProofRefused(f"{type_}: v {data.get('v')} is newer than SUPPORTED_V={SUPPORTED_V}; "
                           "a writer never writes a version it cannot read")
    log.append(state.last_seq + 1, type_, data, actor)
    return project_proofs(project(log))
