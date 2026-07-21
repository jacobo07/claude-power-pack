"""objects.py -- CRAIF-00's ontology, the Phase-1 subset.

Full RepairIntentState defined per CRAIF-01 Part II Section 2.2 for completeness;
Phase 1 only ever reaches PRECONDITIONS_CHECKED (paused=True), per CRAIF-01
Section 2.6's explicit provision for a transaction paused, not closed, prior to
SNAPSHOT-TAKEN. No CLOSED_PROPOSED state exists -- it is not in the sealed
dataset text and is not invented here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RepairIntentState(str, Enum):
    OPENED = "OPENED"
    INTAKE_VALIDATED = "INTAKE-VALIDATED"
    EVIDENCE_FROZEN = "EVIDENCE-FROZEN"
    PRECONDITIONS_CHECKED = "PRECONDITIONS-CHECKED"
    CANDIDATE_SELECTED = "CANDIDATE-SELECTED"
    AUTHORITY_ACQUIRED = "AUTHORITY-ACQUIRED"          # unreachable this phase
    SNAPSHOT_TAKEN = "SNAPSHOT-TAKEN"                  # unreachable this phase
    SANDBOXED = "SANDBOXED"                            # unreachable this phase
    STATICALLY_VALIDATED = "STATICALLY-VALIDATED"      # unreachable this phase
    TARGETED_VERIFIED = "TARGETED-VERIFIED"            # unreachable this phase
    REGRESSION_VERIFIED = "REGRESSION-VERIFIED"        # unreachable this phase
    ACTIVATION_VERIFIED = "ACTIVATION-VERIFIED"        # unreachable this phase
    CANARY_DEPLOYED = "CANARY-DEPLOYED"                # unreachable this phase
    CLOSED_REPAIRED = "CLOSED-REPAIRED"                # unreachable this phase
    CLOSED_ROLLED_BACK = "CLOSED-ROLLED-BACK"          # unreachable this phase
    CLOSED_STALE = "CLOSED-STALE"
    CLOSED_REJECTED = "CLOSED-REJECTED"


@dataclass
class Finding:
    """A Reachability Finding, normalized from a real reachability.scan() row.

    Only status == ORPHAN is actionable this phase (CRAIF-01 Part III Intake).
    """

    producer: str
    target_unit: str
    subtype: str            # "reachability-orphan" this phase
    evidence_payload: dict  # the raw scan row, retained verbatim
    confidence: float
    ts: str


@dataclass
class EvidenceFreeze:
    """CRAIF-01 Part III Section 3.10: a durable, timestamped 'before' capture,
    carrying a content hash so drift between Intake and Freeze is detectable."""

    captured: dict
    content_hash: str
    ts: str
    consulted_versions: dict = field(default_factory=dict)


@dataclass
class RepairIntent:
    id: str
    findings: list[Finding]
    target_unit: str
    state: RepairIntentState = RepairIntentState.OPENED
    paused: bool = False
    pause_reason: str = ""
    evidence_freeze: EvidenceFreeze | None = None


@dataclass
class Candidate:
    """A falsifiable candidate: names both the target-state assertion AND the
    verification instrument that would prove it (CRAIF-00 Section 4.4/4.7)."""

    target_unit: str
    target_state_assertion: str
    verification_instrument: str
    proposed_surface: str
    is_build_decision: bool = False


@dataclass
class UnfalsifiableCandidateRejection:
    """CRAIF-00 Section 4.4/5.5: no proposed_target_state supplied -- refuse
    rather than guess a surface to wire the orphan into."""

    target_unit: str
    reason: str
    missing: list[str] = field(default_factory=list)


@dataclass
class PreconditionsRecord:
    ownership_unambiguous: bool
    ownership_note: str
    rollback_mechanism_available: bool
    rollback_gap_reason: str
    drk_classification_current: bool
