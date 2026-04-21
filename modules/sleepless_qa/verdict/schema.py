"""
Verdict schema — the output of the verdict engine.

PASS  = feature empirically works per the action script
FAIL  = feature is broken; healing circuit should fire
UNCERTAIN = confidence below threshold; DO NOT auto-heal. Notify Owner.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class VerdictStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNCERTAIN = "UNCERTAIN"


class Verdict(BaseModel):
    status: VerdictStatus
    confidence: float  # 0.0 - 1.0
    reason: str
    strategy: str  # "visual" | "log_pattern" | "contract" | "aggregate"
    evidence_refs: list[str] = Field(default_factory=list)
    priority_level: int = 2  # 1=stability, 2=functionality, 3=aesthetics, 4=polish
    api_cost_estimate_usd: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)

    def is_actionable(self) -> bool:
        """PASS or FAIL are actionable. UNCERTAIN is not."""
        return self.status in (VerdictStatus.PASS, VerdictStatus.FAIL)
