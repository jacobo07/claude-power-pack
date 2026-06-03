"""Error Prevention -- PP BL-PREMISE-001.

Public API: verify_premises, assert_premises, verify_file_exists,
verify_function_exists, verify_attr_exists, PremiseResult.
"""
from .premise_verifier import (
    PremiseResult,
    assert_premises,
    verify_attr_exists,
    verify_file_exists,
    verify_function_exists,
    verify_premises,
)

__all__ = [
    "PremiseResult",
    "assert_premises",
    "verify_attr_exists",
    "verify_file_exists",
    "verify_function_exists",
    "verify_premises",
]
