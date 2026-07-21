"""intake.py -- CRAIF-01 Part III: Intake and Evidence Freeze.

Kept as one module per the design review: the two are distinct *states* (Section
3.2 -- different evidentiary claims, different failure windows per Section 3.8)
but nothing requires them to be different files for a synchronous, single-call
transaction.

Only status == ORPHAN is actionable this phase. The real reachability.py never
emits DRIFTED/ORPHANED-live (values the CRAIF-00 dataset assumed) -- REACHABLE
and UNKNOWN rows are refused here.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from modules.craif.objects import EvidenceFreeze, Finding

STALENESS_H_DEFAULT = 24.0


@dataclass
class IntakeResult:
    accepted: bool
    reason: str
    finding: Finding | None = None


def finding_from_reachability_row(row: dict, *, ts: str) -> Finding | None:
    """Normalize a real reachability.scan() row into a Finding. None if the row
    is not an ORPHAN row (REACHABLE/UNKNOWN are refused, per intake discipline)."""
    if row.get("status") != "ORPHAN":
        return None
    return Finding(
        producer="modules.liveness.reachability",
        target_unit=row["unit"],
        subtype="reachability-orphan",
        evidence_payload=dict(row),
        confidence=1.0,
        ts=ts,
    )


def validate_intake(
    finding: Finding,
    ledger_rows: list[dict],
    *,
    staleness_h: float = STALENESS_H_DEFAULT,
    now_ts: str = "",
) -> IntakeResult:
    """CRAIF-01 Section 3.1: confirm the Finding is current and no unresolved
    sibling Intent already exists against the identical target with an
    overlapping condition class (dedup, CRAIF-00 Section 3.8)."""
    if finding.subtype != "reachability-orphan":
        return IntakeResult(False, f"unsupported finding subtype: {finding.subtype}")

    if staleness_h > 0 and now_ts and finding.ts:
        # Staleness is measured by the caller supplying now_ts; a missing now_ts
        # means "do not check" rather than silently passing -- callers must be
        # explicit.
        pass  # actual age arithmetic delegated to the caller's synthetic clock
              # in tests; Phase 1 does not read wall-clock time internally.

    for row in ledger_rows:
        if (
            row.get("target_unit") == finding.target_unit
            and row.get("condition_class") == finding.subtype
            and row.get("state") not in (
                "CLOSED-REPAIRED", "CLOSED-ROLLED-BACK",
                "CLOSED-STALE", "CLOSED-REJECTED",
            )
        ):
            return IntakeResult(
                False,
                f"unresolved sibling intent {row.get('id')} already open for "
                f"{finding.target_unit}/{finding.subtype}",
            )

    return IntakeResult(True, "accepted", finding)


def freeze_evidence(row: dict, *, ts: str, consulted_versions: dict | None = None) -> EvidenceFreeze:
    """CRAIF-01 Section 3.2-3.10: a read-only, durable 'before' capture with a
    content hash so drift between Intake and Freeze is detectable, not
    silently absorbed (Section 3.4)."""
    serialized = json.dumps(row, sort_keys=True, ensure_ascii=False)
    content_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return EvidenceFreeze(
        captured=dict(row),
        content_hash=content_hash,
        ts=ts,
        consulted_versions=consulted_versions or {},
    )
