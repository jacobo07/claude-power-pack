"""Output Contract Registry -- BL-OUTPUT-001.

OQS (Output Quality Score) scorer + per-output-type contracts.
Threshold: OQS >= 70 -> done. Public API: is_done, score,
OQS_DONE_THRESHOLD, list_contracts, get_contract.
"""
from .validator import (
    OQS_DONE_THRESHOLD,
    get_contract,
    is_done,
    list_contracts,
    score,
)

__all__ = [
    "OQS_DONE_THRESHOLD",
    "get_contract",
    "is_done",
    "list_contracts",
    "score",
]
