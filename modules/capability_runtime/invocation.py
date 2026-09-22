#!/usr/bin/env python3
"""invocation.py -- the seam between SELECTING a capability and CALLING it.

`applicability.compile_stack` returns capability IDENTIFIERS. Nothing in this
estate turned an identifier into a call, so every capability was DISCOVERABLE
and none was CALLABLE -- `vault/liveness/callable_inventory.json:155` records
`compile_stack` itself as "unreached at freeze (TEST_ONLY)".

This module closes exactly that gap and nothing else. It is not a dispatcher:
it neither decides WHEN to invoke (applicability does) nor WHAT to do with the
answer (the consumer does). It converts `contract.entrypoint` into one bounded,
attributable, recorded call.

THREE CLAIMS, KEPT APART
------------------------
The estate has repeatedly collapsed these, and the collapse is the defect:

    DISCOVERABLE  the contract is in the registry
    CALLABLE      a canonical path CAN invoke it   <- this module
    CONSUMED      a downstream stage USED the answer  <- the consumer's claim

So `InvocationRecord` carries TWO independent axes, never one:

    status   did the call happen at all?   (INVOKED / NOT_CALLABLE / FAILED /
                                            REFUSED_BY_AUTHORITY)
    outcome  what did the capability decide? (meaningful ONLY when INVOKED)

A single field would make "never called" and "called, abstained" indistinguishable
-- they are opposite facts needing opposite fixes, and one of them is a bug in
this seam while the other is a legitimate answer from the capability.

WHAT "BOUNDED" HONESTLY MEANS HERE
----------------------------------
An in-process Python call cannot be preempted. This module therefore does NOT
claim a timeout it cannot enforce. It enforces what it actually can:

  * exactly one call, ever -- no retry, no loop, no re-dispatch on failure;
  * a declared `budget_ms` on the contract, MEASURED and reported as
    `over_budget` on the record, so a slow capability is visible rather than
    silently tolerated;
  * total failure isolation -- a capability that raises produces a FAILED
    record and returns; it never propagates, so one capability cannot wedge
    the construction path that called it.

Claiming an enforced timeout would be the kind of self-declared evidence
`PR-NO-SELF-CERTIFICATION-001` exists to refuse.

AUTHORITY
---------
A capability that resolves is not thereby permitted to mutate. `authority` is
declared on the contract and checked BEFORE the call, never after -- a response
cannot un-mutate anything. A caller asking for more authority than the contract
declares is refused with `REFUSED_BY_AUTHORITY` and the capability is not
entered.
"""
from __future__ import annotations

import importlib
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable


class Status(str, Enum):
    """Did the call happen? Independent of what the capability decided."""

    INVOKED = "invoked"
    NOT_CALLABLE = "not_callable"            # no entrypoint declared
    UNRESOLVABLE = "unresolvable"            # entrypoint declared, import failed
    REFUSED_BY_AUTHORITY = "refused_by_authority"
    FAILED = "failed"                        # entered, raised


class Authority(str, Enum):
    """What a capability is permitted to do. Ascending."""

    ADVISORY = "advisory"          # returns prose or a hint; touches nothing
    DECISION = "decision"          # returns a typed decision; no side effects
    VALIDATION = "validation"      # may read state to judge it
    MUTATING = "mutating"          # may change state -- never granted implicitly


_RANK = {
    Authority.ADVISORY: 0,
    Authority.DECISION: 1,
    Authority.VALIDATION: 2,
    Authority.MUTATING: 3,
}


class InvocationError(RuntimeError):
    """Raised only for caller errors, never for capability failures."""


@dataclass
class InvocationRecord:
    """Everything needed to reconstruct one decision without reading logs.

    Answers, in order: who asked, why it was selected, was it actually invoked,
    what input did it receive, what did it return, how long did it take, and
    which consumer took the result.
    """

    capability_id: str
    status: Status
    requested_by: str = ""
    selected_because: str = ""
    entrypoint: str = ""
    authority: str = ""
    input_provenance: str = ""
    outcome: str = ""                 # the capability's OWN outcome vocabulary
    exit_code: int | None = None
    result: Any = None
    error: str = ""
    elapsed_ms: float = 0.0
    budget_ms: int = 0
    over_budget: bool = False
    consumed_by: str = ""             # set by the consumer, never by this module
    at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def invoked(self) -> bool:
        """True only when the capability was actually entered and returned."""
        return self.status is Status.INVOKED

    def to_dict(self) -> dict:
        d = {
            "capability_id": self.capability_id,
            "status": self.status.value,
            "requested_by": self.requested_by,
            "selected_because": self.selected_because,
            "entrypoint": self.entrypoint,
            "authority": self.authority,
            "input_provenance": self.input_provenance,
            "outcome": self.outcome,
            "exit_code": self.exit_code,
            "error": self.error,
            "elapsed_ms": round(self.elapsed_ms, 3),
            "budget_ms": self.budget_ms,
            "over_budget": self.over_budget,
            "consumed_by": self.consumed_by,
            "at": self.at,
        }
        if self.result is not None and hasattr(self.result, "to_dict"):
            d["result"] = self.result.to_dict()
        return d


def resolve_entrypoint(dotted: str) -> Callable:
    """`pkg.mod:func` or `pkg.mod.func` -> the callable.

    Raises InvocationError with the dotted path in the message, because an
    entrypoint that cannot be imported is a CONTRACT defect and the contract is
    what the reader has to fix.
    """
    if not dotted:
        raise InvocationError("empty entrypoint")
    if ":" in dotted:
        mod_name, _, attr = dotted.partition(":")
    else:
        mod_name, _, attr = dotted.rpartition(".")
    if not mod_name or not attr:
        raise InvocationError(f"malformed entrypoint: {dotted!r}")
    try:
        mod = importlib.import_module(mod_name)
    except Exception as e:  # noqa: BLE001 -- an import failure is a result here
        raise InvocationError(f"cannot import {mod_name!r} for {dotted!r}: {e}")
    try:
        fn = getattr(mod, attr)
    except AttributeError:
        raise InvocationError(f"{mod_name!r} has no attribute {attr!r}")
    if not callable(fn):
        raise InvocationError(f"{dotted!r} is not callable")
    return fn


def _read_outcome(result: Any) -> tuple[str, int | None]:
    """Take the capability's OWN outcome vocabulary; never impose one.

    A seam that renamed RECOMMEND/ABSTAIN/REQUIRE_APPROVAL/UNDETERMINED into its
    own words would be the paraphrase failure
    (`PR-INHERIT-VERBATIM-NEVER-PARAPHRASE-001`) at the invocation boundary.
    """
    outcome = getattr(result, "outcome", "")
    if isinstance(outcome, Enum):
        outcome = outcome.value
    code = getattr(result, "exit_code", None)
    if callable(code):
        code = None
    return (str(outcome) if outcome else ""), code


def invoke(
    contract,
    payload,
    *,
    requested_by: str = "",
    selected_because: str = "",
    input_provenance: str = "",
    granted_authority: str | None = None,
) -> InvocationRecord:
    """Call one capability, once, and return a record of what happened.

    NEVER raises on a capability failure -- that is the whole point of failure
    isolation. It raises only when the CALLER is wrong (no contract).
    """
    if contract is None:
        raise InvocationError("invoke() requires a contract")

    cap_id = getattr(contract, "id", "") or "<unknown>"
    entrypoint = (getattr(contract, "entrypoint", "") or "").strip()
    declared = (getattr(contract, "authority", "") or Authority.ADVISORY.value)
    budget_ms = int(getattr(contract, "budget_ms", 0) or 0)

    base = dict(
        capability_id=cap_id,
        requested_by=requested_by,
        selected_because=selected_because,
        entrypoint=entrypoint,
        authority=declared,
        input_provenance=input_provenance,
        budget_ms=budget_ms,
    )

    # Kill switch. The contract's `kill_switch` field names this env var, so it
    # is ENFORCED here rather than merely promised there -- a documented
    # capability nobody executes is indistinguishable from a working one.
    if (os.environ.get("CPP_CAPABILITY_INVOKE", "").strip().lower()
            in ("off", "0", "false")):
        return InvocationRecord(
            status=Status.NOT_CALLABLE,
            error="CPP_CAPABILITY_INVOKE=off (kill switch)", **base)

    # DISCOVERABLE but not CALLABLE -- the honest, common case. Not an error.
    if not entrypoint:
        return InvocationRecord(status=Status.NOT_CALLABLE, **base)

    # Authority is checked BEFORE entering. A reply arrives too late to matter.
    if granted_authority is not None:
        try:
            want = Authority(granted_authority)
            have = Authority(declared)
        except ValueError as e:
            return InvocationRecord(
                status=Status.REFUSED_BY_AUTHORITY,
                error=f"unknown authority: {e}", **base)
        if _RANK[want] > _RANK[have]:
            return InvocationRecord(
                status=Status.REFUSED_BY_AUTHORITY,
                error=(f"caller asked for {want.value!r}; contract declares "
                       f"{have.value!r}"),
                **base)

    try:
        fn = resolve_entrypoint(entrypoint)
    except InvocationError as e:
        return InvocationRecord(status=Status.UNRESOLVABLE, error=str(e), **base)

    t0 = time.perf_counter()
    try:
        result = fn(payload)
    except Exception as e:  # noqa: BLE001 -- isolation is the contract
        elapsed = (time.perf_counter() - t0) * 1000.0
        return InvocationRecord(
            status=Status.FAILED,
            error=f"{type(e).__name__}: {e}",
            elapsed_ms=elapsed,
            over_budget=bool(budget_ms and elapsed > budget_ms),
            **base)

    elapsed = (time.perf_counter() - t0) * 1000.0
    outcome, code = _read_outcome(result)
    return InvocationRecord(
        status=Status.INVOKED,
        outcome=outcome,
        exit_code=code,
        result=result,
        elapsed_ms=elapsed,
        over_budget=bool(budget_ms and elapsed > budget_ms),
        **base)


__all__ = [
    "Authority", "InvocationError", "InvocationRecord", "Status",
    "invoke", "resolve_entrypoint",
]
