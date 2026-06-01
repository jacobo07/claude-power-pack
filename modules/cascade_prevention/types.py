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


@dataclass(frozen=True)
class CascadeHit:
    cascade_type: CascadeType
    severity: CascadeSeverity
    surface: str
    reason: str

    @property
    def should_warn(self) -> bool:
        return self.severity >= CascadeSeverity.C3

    @property
    def should_block(self) -> bool:
        return self.severity >= CascadeSeverity.C4
