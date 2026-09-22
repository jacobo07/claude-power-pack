#!/usr/bin/env python3
"""enrichment.py -- let a construction ARTIFACT collect the decisions it earns.

`invocation.invoke` makes one capability callable. It still leaves the caller
holding two questions it has no business answering: which capabilities care
about the artifact in my hands, and how do I build each one's typed input?

This module answers both GENERICALLY, from the contracts, so a construction
stage never names a capability. That is the difference between a canonical
inheritance boundary and bolting one capability onto one subsystem -- the PRD
stage that calls this does not import, mention or know about surface
architecture, and a second capability declaring the same artifact kind is picked
up with no change to the stage at all.

THE ADAPTER PROTOCOL
--------------------
A contract opts in with three fields:

    inputs     must contain the artifact kind  ("prd_baseline")
    adapter    dotted path to  fn(artifact) -> (payload | None, reason)
    entrypoint dotted path to the capability itself

The adapter returns `None` when the capability does not apply to THIS artifact,
with a reason either way. Applicability therefore stays owned by the capability,
which is the only party that knows what it needs -- and a PRD for a batch job is
never handed signup obligations, because its adapter declines it by name.

FAILURE IS ISOLATED, TWICE
--------------------------
A construction stage must not break because a capability is broken. Every
adapter runs inside its own guard, every invocation is already isolated by
`invoke`, and a capability that explodes yields a RECORD saying so while the
other capabilities and the artifact proceed untouched. `enrich` raises for no
capability-side reason whatsoever.
"""
from __future__ import annotations

from modules.capability_runtime.contract import load_contracts
from modules.capability_runtime.invocation import (
    InvocationRecord, Status, invoke, resolve_entrypoint)


def candidates(artifact_kind: str, contracts=None, contracts_dir=None) -> list:
    """Contracts that declare this artifact kind AND can actually be called.

    A contract naming the kind without an entrypoint or an adapter is
    DISCOVERABLE for this artifact and no more; it is skipped silently because
    that is a legitimate state, not a defect.
    """
    pool = contracts if contracts is not None else load_contracts(contracts_dir)
    out = []
    for c in pool:
        kinds = [str(i).strip() for i in (getattr(c, "inputs", None) or [])]
        if artifact_kind not in kinds:
            continue
        if not (getattr(c, "entrypoint", "") and getattr(c, "adapter", "")):
            continue
        out.append(c)
    return out


def enrich(artifact_kind: str, artifact, *, requested_by: str = "",
           contracts=None, contracts_dir=None,
           granted_authority: str | None = "decision") -> list:
    """Run every capability that claims this artifact kind. Never raises.

    Returns one InvocationRecord per candidate, including the ones that declined
    -- a capability that was considered and did not apply is a different fact
    from one that was never considered, and only the record can tell them apart.
    """
    records: list[InvocationRecord] = []
    for c in candidates(artifact_kind, contracts, contracts_dir):
        base = dict(
            capability_id=getattr(c, "id", "<unknown>"),
            requested_by=requested_by,
            entrypoint=getattr(c, "entrypoint", ""),
            authority=getattr(c, "authority", ""),
            input_provenance=f"artifact:{artifact_kind}",
        )
        try:
            adapt = resolve_entrypoint(c.adapter)
        except Exception as e:  # noqa: BLE001 -- a broken adapter is a result
            records.append(InvocationRecord(
                status=Status.UNRESOLVABLE,
                error=f"adapter {c.adapter!r}: {e}", **base))
            continue

        try:
            payload, reason = adapt(artifact)
        except Exception as e:  # noqa: BLE001 -- isolation, same as invoke
            records.append(InvocationRecord(
                status=Status.FAILED,
                error=f"adapter raised: {type(e).__name__}: {e}", **base))
            continue

        if payload is None:
            # NOT APPLICABLE. Deliberately not an error and deliberately not a
            # silent skip: the reason is the evidence that a non-applicable
            # project was considered and correctly left alone.
            records.append(InvocationRecord(
                status=Status.NOT_CALLABLE,
                error=f"not applicable: {reason}", **base))
            continue

        records.append(invoke(
            c, payload,
            requested_by=requested_by,
            selected_because=str(reason),
            input_provenance=f"artifact:{artifact_kind} -> {type(payload).__name__}",
            granted_authority=granted_authority))
    return records


def decisions_for_artifact(artifact_kind: str, artifact, *,
                           requested_by: str = "", contracts=None,
                           contracts_dir=None) -> dict:
    """The shape a construction artifact stores: one entry per capability.

    Keyed by capability id. Every entry carries the STATUS as well as the
    outcome, so a reader can always tell "never called" from "called and
    abstained" -- the two facts this whole seam exists to keep apart.
    """
    out: dict = {}
    for rec in enrich(artifact_kind, artifact, requested_by=requested_by,
                      contracts=contracts, contracts_dir=contracts_dir):
        # DELIBERATELY NO TIMESTAMP AND NO TIMING.
        #
        # This dict is stored in a construction artifact that its own gate
        # checks for determinism: KARIMO parses the same PRD twice and requires
        # byte-identical output. `InvocationRecord.at` is a microsecond UTC
        # stamp, so including it made every parse differ from the last and broke
        # G2 DETERMINISM -- caught by the stage's own done-gate, not by mine.
        #
        # The general rule is worth more than the fix: an artifact derived from
        # an input must be a pure function OF that input. `at` and `elapsed_ms`
        # are facts about the RUN, not about the decision; they stay on the
        # record, where a log can have them, and out of anything content-addressed.
        entry = {
            "status": rec.status.value,
            "outcome": rec.outcome,
            "exit_code": rec.exit_code,
            "selected_because": rec.selected_because,
            "entrypoint": rec.entrypoint,
            "authority": rec.authority,
        }
        if rec.error:
            entry["note"] = rec.error
        if rec.result is not None and hasattr(rec.result, "to_dict"):
            entry["decision"] = rec.result.to_dict()
        out[rec.capability_id] = entry
    return out


__all__ = ["candidates", "decisions_for_artifact", "enrich"]
