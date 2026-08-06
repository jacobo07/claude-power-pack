"""Cascade severity ladder + cascade types. OD2 thresholds sealed."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum

# OD2 (Owner-sealed 2026-06-01):
#   C3+ = warn (advisory; agent continues)
#   C4+ = block (hard stop; Owner override required)
WARN_THRESHOLD_NAME = "C3"
BLOCK_THRESHOLD_NAME = "C4"


class CascadeSeverity(IntEnum):
    C1 = 1  # informational
    C2 = 2  # noteworthy
    C3 = 3  # warn (advisory)
    C4 = 4  # block (default deny)
    C5 = 5  # halt-and-escalate (Owner-only override)


class CascadeType(Enum):
    DEPLOY_WITHOUT_TEST = "deploy_without_test"
    EDIT_LOCKED_FILE = "edit_locked_file"
    COMMIT_WITHOUT_VERIFY = "commit_without_verify"
    DELETE_WITHOUT_BACKUP = "delete_without_backup"
    SECRET_IN_OUTPUT = "secret_in_output"
    MISSING_ROLLBACK = "missing_rollback"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    RACE_CONDITION = "race_condition"
    CONTEXT_OVERFLOW = "context_overflow"
    SCOPE_CREEP = "scope_creep"
    # A successor failure inferred from history rather than observed in the present.
    # Distinct from every type above: those name something already true.
    PREDICTED_SUCCESSOR = "predicted_successor"


@dataclass(frozen=True)
class CascadeHit:
    cascade_type: CascadeType
    severity: CascadeSeverity
    surface: str
    reason: str

    # --- predictive dimension (SEIP-EXT-D3) -------------------------------
    # Severity answers "how bad is this hit"; it says nothing about whether a
    # SECOND failure is likely to follow. Those are different questions, and a
    # second C1-C5 ladder would only restate the first. `prior` is the observed
    # frequency with which this class historically preceded `predicts`, and
    # `basis` names the evidence it was computed from.
    #
    # None is not "no risk" -- it is "not measured". A predicted hit must be
    # able to say what it was inferred from, or it is an assertion wearing a
    # number (`feedback_provider_score_to_hard_verdict`).
    prior: float | None = None
    predicts: str = ""
    basis: str = ""

    @property
    def should_warn(self) -> bool:
        return self.severity >= CascadeSeverity.C3

    @property
    def should_block(self) -> bool:
        return self.severity >= CascadeSeverity.C4

    @property
    def is_predictive(self) -> bool:
        """True only when a prior was actually measured from evidence."""
        return self.prior is not None and bool(self.basis)
