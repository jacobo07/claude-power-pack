"""candidate.py -- CRAIF-01 Part V: Candidate Generation and Selection.

CRAIF-00 Section 4.4/4.7: a candidate's target-state assertion must name both
the property to check AND the specific verification instrument. This runtime
has no diagnosis capability of its own (CRAIF-00 Part IX Section 9.3 -- diagnosis
is explicitly not CRAIF's role); a bare ORPHAN row with no diagnosed surface is
an Unfalsifiable Candidate Rejection, not a guessed candidate.
"""
from __future__ import annotations

from modules.craif.objects import (
    Candidate,
    RepairIntent,
    UnfalsifiableCandidateRejection,
)


def generate_candidate(
    intent: RepairIntent,
    proposed_target_state: dict | None = None,
) -> Candidate | UnfalsifiableCandidateRejection:
    """proposed_target_state, when supplied, must carry a 'surface' key naming
    where the orphan should be wired in. Absent it (or absent that key), this
    returns a rejection rather than synthesizing a vague candidate."""
    if not proposed_target_state or not proposed_target_state.get("surface"):
        return UnfalsifiableCandidateRejection(
            target_unit=intent.target_unit,
            reason="no proposed_target_state.surface supplied; refusing to guess",
            missing=["proposed_target_state.surface"],
        )

    surface = proposed_target_state["surface"]
    return Candidate(
        target_unit=intent.target_unit,
        target_state_assertion=(
            f"{intent.target_unit} is wired into a live surface via {surface}"
        ),
        verification_instrument=(
            "modules.liveness.reachability.scan() reports status == REACHABLE "
            f"for unit {intent.target_unit} on a subsequent scan"
        ),
        proposed_surface=surface,
        is_build_decision=False,
    )
