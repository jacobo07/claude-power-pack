#!/usr/bin/env python3
"""lifecycle.py -- authoritative lifecycle state for a capability (UCR-CIF W3).

WHY THIS IS NOT `maturity`, AND NOT `retirement.py`
---------------------------------------------------
`contract.Maturity` is a FITNESS scale -- EXPERIMENTAL < DEVELOPING < PROVEN <
MATURE -- and `applicability` consumes it as ONE weighted factor among five
(`maturity_fit`, weight 0.15). Measured consequence: degrading a capability
from MATURE to EXPERIMENTAL moves its score by at most 0.15 * 3/4 = 0.1125,
so a relevant, high-stakes capability stays MANDATORY however far its maturity
falls. Revocation through maturity is arithmetically impossible, and it would
be the wrong claim anyway: "less proven" is not "no longer authoritative".

`retirement.py` computes whether a contract's `retirement_condition` has come
true. It is PROPOSE-ONLY by explicit design -- "a capability that retires
itself is a gate that grades itself; the Owner retires, the evaluator only
shows the evidence." That design is right and it is why the estate had a
retirement EVALUATOR with no effect and a SELECTOR that never consulted
lifecycle. This module is the missing authority between them: the state an
Owner writes and the selector honours.

So the three axes stay separate, and each answers a different question:

    maturity   how proven is this?          (ranking)
    retirement has its condition come true? (evidence, propose-only)
    lifecycle  may it be inherited NOW?     (authority, this module)

A MATURE capability can be REVOKED. An EXPERIMENTAL one can be ACTIVE.

THE STATES
----------
ACTIVE       current valid authority; the only inheritable state.
SUPERSEDED   a stronger state occupies its place. Carries `successor`, so
             lineage survives the replacement.
DEPRECATED   not active; consumable only under a declared compatibility
             condition. That condition is FREE TEXT and therefore not
             auto-evaluable -- `retirement.py` already paid for that lesson --
             so it is recorded for a human and never machine-honoured. A
             DEPRECATED capability is withheld until an Owner transitions it.
SUSPENDED    temporarily withheld pending evidence or an incident. Reversible
             by construction; SUSPENDED is not REVOKED.
REVOKED      no longer eligible for inheritance within its scope. Terminal for
             inheritance; NOT terminal for history.
UNKNOWN      evidence insufficient to classify. Absence resolves here, never
             to ACTIVE.

WITHDRAWN = {SUPERSEDED, DEPRECATED, SUSPENDED, REVOKED} -- the states that
refuse inheritance unconditionally.

WHY UNKNOWN IS REPORTED RATHER THAN WITHHELD
--------------------------------------------
UNKNOWN is not ACTIVE and is never written as verified authority. It is also
not WITHDRAWN, and that is a deliberate, reversible decision rather than a
softening.

Ten contracts predate this field. Resolving absence to "withheld" would have
silently stopped four capabilities this estate currently activates as MANDATORY
on every prompt (`secret_containment`, `output_quality_gate`,
`liveness_reachability`, `premise_verification`) -- a live regression wearing
the costume of a safety improvement, and precisely the "silently reduce
correctness" the mission forbids. So UNKNOWN still activates, carries
`lifecycle_verified=False`, and is reported in its own bucket where it can be
counted and driven down.

The ratchet, not the default, is what closes this: `tools/test_capability_lifecycle.py`
pins the UNKNOWN population as shrink-only. When it reaches zero, tightening
UNKNOWN into WITHDRAWN is a one-line change with no population left to break.

CONCURRENCY
-----------
Every transition states the state it believes it is replacing (`expected`). A
transition whose subject has moved is REFUSED, never applied -- the authority
the caller reviewed is the authority it may replace. `expected=None` means the
caller did not look, and is refused for anything but a first classification.
This is the institutional half of "lost update rate -> 0"; the file half is the
atomic replace `contract.save_contract` already performs.

HISTORY
-------
The contract file carries the CURRENT state and is a projection. The append-only
`lifecycle_log.jsonl` is the authority for history: every transition, with
actor, reason, evidence and successor. Revocation never deletes; `history()`
and `reconstruct_at()` replay it.

Stdlib-only. Fail-open on read, fail-closed on write.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.capability_runtime.contract import (  # noqa: E402
    CapabilityContract, ContractError, load_contracts, save_contract,
)

LIFECYCLE_LOG = _PP_ROOT / "vault" / "capability_runtime" / "lifecycle_log.jsonl"
SCHEMA_VERSION = 1


class Lifecycle(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    DEPRECATED = "deprecated"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    UNKNOWN = "unknown"


# The states that refuse inheritance. UNKNOWN is deliberately absent -- see the
# module docstring; it is reported, counted and ratcheted, not withheld.
WITHDRAWN = frozenset({
    Lifecycle.SUPERSEDED, Lifecycle.DEPRECATED, Lifecycle.SUSPENDED,
    Lifecycle.REVOKED,
})

# Reversible withdrawals may return to ACTIVE. SUPERSEDED and REVOKED may not be
# resurrected in place: the successor carries the authority, or a new capability
# does. Recorded as a table rather than prose so it is executable.
_LEGAL: dict = {
    Lifecycle.UNKNOWN: {Lifecycle.ACTIVE, Lifecycle.SUPERSEDED,
                        Lifecycle.DEPRECATED, Lifecycle.SUSPENDED,
                        Lifecycle.REVOKED},
    Lifecycle.ACTIVE: {Lifecycle.SUPERSEDED, Lifecycle.DEPRECATED,
                       Lifecycle.SUSPENDED, Lifecycle.REVOKED},
    Lifecycle.SUSPENDED: {Lifecycle.ACTIVE, Lifecycle.REVOKED,
                          Lifecycle.SUPERSEDED, Lifecycle.DEPRECATED},
    Lifecycle.DEPRECATED: {Lifecycle.ACTIVE, Lifecycle.SUPERSEDED,
                           Lifecycle.REVOKED},
    # Terminal for inheritance. History stays readable; the row does not move.
    Lifecycle.SUPERSEDED: set(),
    Lifecycle.REVOKED: set(),
}


class LifecycleError(ValueError):
    """A refused transition. The message names what was refused and why."""


@dataclass
class LifecycleEvent:
    capability_id: str
    from_state: str
    to_state: str
    iso_ts: str
    actor: str
    reason: str
    evidence: list = field(default_factory=list)
    successor: str = ""
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict:
        return asdict(self)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def coerce(value) -> Lifecycle:
    """Any stored spelling to a state. Absence and nonsense both resolve to
    UNKNOWN -- never to ACTIVE, and never by raising, because a store this
    cannot read must not take a capability down."""
    if isinstance(value, Lifecycle):
        return value
    text = str(value or "").strip().lower()
    if not text:
        return Lifecycle.UNKNOWN
    try:
        return Lifecycle(text)
    except ValueError:
        return Lifecycle.UNKNOWN


def state_of(contract) -> Lifecycle:
    """The lifecycle of a contract. A contract predating the field is UNKNOWN."""
    return coerce(getattr(contract, "lifecycle", ""))


def inheritable(contract) -> bool:
    """May this capability be inherited by a mission right now?"""
    return state_of(contract) not in WITHDRAWN


def verified(contract) -> bool:
    """Is the lifecycle a positive, evidenced classification (not an absence)?"""
    return state_of(contract) is not Lifecycle.UNKNOWN


# --------------------------------------------------------------------------- #
# History. Append-only; the authority for "what was true, when, and why".
# --------------------------------------------------------------------------- #
def append_event(event: LifecycleEvent, log_path=None) -> Path:
    """Append one transition. O_APPEND so concurrent writers interleave rows
    rather than overwrite each other -- a shared-line file with a count-derived
    id is exactly the race `baseline_ledger_append` carries, and this store does
    not repeat it: identity is (capability_id, iso_ts), never a line number."""
    p = Path(log_path) if log_path is not None else LIFECYCLE_LOG
    p.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(event.to_dict(), ensure_ascii=False) + "\n"
    fd = os.open(str(p), os.O_WRONLY | os.O_CREAT | os.O_APPEND)
    try:
        os.write(fd, line.encode("utf-8"))
    finally:
        os.close(fd)
    return p


def load_log(log_path=None) -> list:
    """Every readable transition, oldest first. Fail-open: an unreadable log
    yields [], a malformed row is skipped rather than taking the sweep down."""
    p = Path(log_path) if log_path is not None else LIFECYCLE_LOG
    out: list = []
    try:
        text = p.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return out
    known = set(LifecycleEvent.__dataclass_fields__)
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if not isinstance(d, dict) or "capability_id" not in d:
            continue
        out.append(LifecycleEvent(**{k: v for k, v in d.items() if k in known}))
    return out


def history(capability_id: str, log_path=None, events=None) -> list:
    """Every transition for one capability, oldest first."""
    evs = events if events is not None else load_log(log_path)
    return [e for e in evs if e.capability_id == capability_id]


def reconstruct_at(capability_id: str, iso_ts: str, log_path=None,
                   events=None) -> Lifecycle:
    """The state this capability held at `iso_ts`.

    Ordered by the transition's own timestamp, not by insertion: two rows
    written out of order otherwise render as a reversal that never happened.
    Before the first transition a capability is UNKNOWN, which is also what an
    empty log returns -- the two are the same claim.
    """
    rows = sorted(history(capability_id, log_path, events),
                  key=lambda e: (e.iso_ts, e.to_state))
    state = Lifecycle.UNKNOWN
    for e in rows:
        if e.iso_ts <= iso_ts:
            state = coerce(e.to_state)
        else:
            break
    return state


def current_from_log(capability_id: str, log_path=None, events=None) -> Lifecycle:
    """The state the LOG says this capability holds -- the reconstructable
    answer, independent of the contract file's projection. Disagreement between
    the two is a real finding, so they are computed separately on purpose."""
    rows = sorted(history(capability_id, log_path, events),
                  key=lambda e: (e.iso_ts, e.to_state))
    return coerce(rows[-1].to_state) if rows else Lifecycle.UNKNOWN


# --------------------------------------------------------------------------- #
# Transition. Optimistic concurrency; the projection is written last.
# --------------------------------------------------------------------------- #
def transition(capability_id: str, to_state, *, expected=None, actor: str,
               reason: str, evidence=None, successor: str = "",
               contracts_dir=None, log_path=None,
               contracts=None) -> LifecycleEvent:
    """Move a capability to `to_state`, or refuse and change nothing.

    `expected` is the state the caller BELIEVES it is replacing. It is required
    whenever the subject is already classified: authorising a transition against
    a state nobody looked at is how one writer silently discards another's. A
    first classification (the subject is UNKNOWN) may pass `expected=None`.
    """
    # Reads coerce an unrecognised state to UNKNOWN so a bad store cannot take a
    # capability down. A WRITE must not: an unrecognised target is a caller
    # error, and silently recording UNKNOWN would look like a classification.
    raw = (to_state.value if isinstance(to_state, Lifecycle)
           else str(to_state or "")).strip().lower()
    try:
        target = Lifecycle(raw)
    except ValueError:
        raise LifecycleError(
            f"{capability_id}: {to_state!r} is not a lifecycle state "
            f"(known: {sorted(s.value for s in Lifecycle)})") from None
    if not str(actor or "").strip():
        raise LifecycleError(
            f"{capability_id}: a transition requires an actor -- authority "
            "without provenance is not authority")
    if not str(reason or "").strip():
        raise LifecycleError(f"{capability_id}: a transition requires a reason")

    cs = contracts if contracts is not None else load_contracts(contracts_dir)
    by_id = {c.id: c for c in cs}
    if capability_id not in by_id:
        raise LifecycleError(
            f"{capability_id}: no such capability contract "
            f"(looked in {contracts_dir or 'vault/capability_runtime/contracts'})")
    contract = by_id[capability_id]
    current = state_of(contract)

    if target is Lifecycle.SUPERSEDED and not str(successor or "").strip():
        raise LifecycleError(
            f"{capability_id}: SUPERSEDED requires a successor -- "
            "'a stronger state occupies its place' names which one")
    if successor and successor not in by_id and successor != capability_id:
        raise LifecycleError(
            f"{capability_id}: successor {successor!r} is not a known capability")

    if expected is None:
        if current is not Lifecycle.UNKNOWN:
            raise LifecycleError(
                f"{capability_id}: is {current.value!r}, not an unclassified "
                "subject -- state the expected state you reviewed")
    else:
        exp = coerce(expected)
        if exp is not current:
            raise LifecycleError(
                f"{capability_id}: expected {exp.value!r} but it is "
                f"{current.value!r} -- refused; re-read it and decide again")

    if target is current:
        raise LifecycleError(
            f"{capability_id}: already {current.value!r} -- a transition that "
            "changes nothing is not a transition")
    legal = _LEGAL.get(current, set())
    if target not in legal:
        allowed = sorted(s.value for s in legal) or ["(terminal)"]
        raise LifecycleError(
            f"{capability_id}: {current.value} -> {target.value} is not a legal "
            f"transition; from {current.value} the legal moves are {allowed}")

    event = LifecycleEvent(
        capability_id=capability_id, from_state=current.value,
        to_state=target.value, iso_ts=_now(), actor=str(actor).strip(),
        reason=str(reason).strip(), evidence=[str(e) for e in (evidence or [])],
        successor=str(successor or ""),
    )
    # History first. If the projection write fails, the transition is still
    # reconstructable; the reverse order would lose the record of a change the
    # store already shows.
    append_event(event, log_path)
    contract.lifecycle = target.value
    save_contract(contract, contracts_dir)
    return event


def classify_population(contracts=None, contracts_dir=None) -> dict:
    """Counts per state over the whole contract store. The UNKNOWN entry is the
    one the ratchet holds shrink-only."""
    cs = contracts if contracts is not None else load_contracts(contracts_dir)
    counts: dict = {s.value: 0 for s in Lifecycle}
    unknown: list = []
    withheld: list = []
    for c in cs:
        s = state_of(c)
        counts[s.value] += 1
        if s is Lifecycle.UNKNOWN:
            unknown.append(c.id)
        elif s in WITHDRAWN:
            withheld.append(c.id)
    return {"total": len(cs), "counts": counts,
            "unknown": sorted(unknown), "withheld": sorted(withheld)}


__all__ = [
    "Lifecycle", "LifecycleError", "LifecycleEvent", "LIFECYCLE_LOG",
    "WITHDRAWN", "SCHEMA_VERSION", "append_event", "classify_population",
    "coerce", "current_from_log", "history", "inheritable", "load_log",
    "reconstruct_at", "state_of", "transition", "verified",
]
