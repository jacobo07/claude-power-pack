"""authority.py -- CRAIF-01 Part IV (Preconditions) and Part VI (Authority
Acquisition), Phase 1.

Preconditions refuses unconditionally this phase: no rollback mechanism exists
anywhere in the estate for CRAIF's own target class (a reachability-registry
wiring change) -- modules.rollback only covers rsync-dir/pg_dump/docker-volume.
DRK's real classification is consulted and recorded as informational evidence
on the resulting pause/escalation, never as the branch condition -- a realistic
candidate for this Finding type lands at DRK tier L2 (blast-radius magnitude >= 1
is unavoidable for any code-touching statement), so a tier-based ceiling would
never take its "acted on" branch.
"""
from __future__ import annotations

from dataclasses import dataclass

from modules.craif.objects import Candidate, PreconditionsRecord, RepairIntent
from modules.decision_review.decision_kernel import review_decision
from modules.decision_review.decision_record import (
    DecisionObject,
    DecisionRecord,
    Evidence,
    EvidenceType,
    Registry,
)

# The real modules.rollback adapters, by target class -- none cover a CRAIF
# reachability-registry wiring change. Named explicitly so a future adapter
# addition is a one-line change here, not a silent behavior shift.
_KNOWN_ROLLBACK_TARGET_CLASSES = {"rsync-dir", "pg-dump", "docker-volume"}
_CRAIF_TARGET_CLASS = "reachability-registry-wiring"


@dataclass
class AuthorityOutcome:
    paused: bool
    pause_reason: str
    preconditions: PreconditionsRecord
    drk_tier: str | None
    drk_verdict: str | None
    drk_record_id: str | None


def check_preconditions(intent: RepairIntent, candidate: Candidate) -> PreconditionsRecord:
    """CRAIF-01 Part IV: ownership-unambiguous (thin but real -- liveness is the
    only wired producer this phase) and rollback-mechanism-available (always
    False this phase, honestly)."""
    ownership_unambiguous = intent.findings[0].producer == "modules.liveness.reachability" and len(
        {f.producer for f in intent.findings}
    ) == 1
    rollback_available = _CRAIF_TARGET_CLASS in _KNOWN_ROLLBACK_TARGET_CLASSES
    return PreconditionsRecord(
        ownership_unambiguous=ownership_unambiguous,
        ownership_note="single wired producer (liveness) this phase",
        rollback_mechanism_available=rollback_available,
        rollback_gap_reason=(
            "" if rollback_available else
            f"no modules.rollback adapter covers target class "
            f"'{_CRAIF_TARGET_CLASS}'; known classes are "
            f"{sorted(_KNOWN_ROLLBACK_TARGET_CLASSES)}"
        ),
        drk_classification_current=True,
    )


def consult_drk(
    candidate: Candidate,
    *,
    registry: Registry | None = None,
    decision_id: str = "",
    ts: str = "",
) -> DecisionRecord:
    """Real, unmocked DRK call -- no injected precedent/placement/knowledge,
    because is_build_decision=False means placement/knowledge are never
    consulted and there is no real arch-decision precedent for this Finding
    type to inject. The real ReviewTier/Verdict this produces is informational
    evidence, not a gate."""
    obj = DecisionObject(
        id=decision_id or f"CRAIF-DRK-{candidate.target_unit}",
        statement=f"Register {candidate.target_unit} on a live surface via {candidate.proposed_surface}",
        problem=(
            f"modules.liveness.reachability.scan() reports {candidate.target_unit} "
            "as ORPHAN -- present, individually correct, unreachable from any "
            "live surface."
        ),
        options=[
            f"wire {candidate.target_unit} into {candidate.proposed_surface}",
            "leave unreachable",
            "delete as dead code",
        ],
        chosen=f"wire {candidate.target_unit} into {candidate.proposed_surface}",
        rationale=candidate.target_state_assertion,
        evidence=[
            Evidence(
                type=EvidenceType.OBSERVED_EVIDENCE,
                claim=f"{candidate.target_unit} is ORPHAN per a real reachability scan",
                source="modules.liveness.reachability.scan()",
            ),
        ],
        is_build_decision=candidate.is_build_decision,
    )
    return review_decision(
        obj,
        precedent=None,
        placement=None,
        knowledge=None,
        registry=registry,
        ts=ts,
        live=False,
    )


def acquire_authority(
    intent: RepairIntent,
    candidate: Candidate,
    preconditions: PreconditionsRecord,
    drk_record: DecisionRecord,
) -> AuthorityOutcome:
    """This phase always pauses: Preconditions' rollback conjunct is false for
    every candidate this phase can generate, per CRAIF-01 Section 2.6's
    provision for a paused (not closed) transaction prior to SNAPSHOT-TAKEN."""
    tier = drk_record.tier.value if drk_record.tier else None
    verdict = drk_record.verdict.value if drk_record.verdict else None
    if not preconditions.rollback_mechanism_available:
        reason = (
            f"rollback-mechanism-available=False: {preconditions.rollback_gap_reason}"
        )
    elif not preconditions.ownership_unambiguous:
        reason = "ownership-unambiguous=False"
    else:
        # Unreachable this phase (rollback is always False), kept for honesty
        # about the conjunction rather than special-casing it away.
        reason = "preconditions satisfied but no sandbox/execution mechanism exists"
    return AuthorityOutcome(
        paused=True,
        pause_reason=reason,
        preconditions=preconditions,
        drk_tier=tier,
        drk_verdict=verdict,
        drk_record_id=drk_record.obj.id if drk_record.obj else None,
    )
