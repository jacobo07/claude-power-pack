"""Output Contract Registry -- BL-OUTPUT-001.

OQS (Output Quality Score) scorer + per-output-type contracts.
Threshold: OQS >= 70 -> done. Public API: is_done, score,
OQS_DONE_THRESHOLD, list_contracts, get_contract.
"""
from .validator import (
    OQS_DONE_THRESHOLD,
    TIER_OQS_FLOOR,
    get_contract,
    is_done,
    is_done_for_tier,
    list_contracts,
    score,
    tier_floor,
)

__all__ = [
    "OQS_DONE_THRESHOLD",
    "TIER_OQS_FLOOR",
    "get_contract",
    "is_done",
    "is_done_for_tier",
    "list_contracts",
    "score",
    "tier_floor",
]
