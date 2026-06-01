"""Cascade Prevention -- BL-CASCADE-001.

Public API: detect, SURFACES, CascadeHit, CascadeSeverity, CascadeType,
filter_blockers, filter_warnings, is_blocked.
"""
from .blocker import filter_blockers, filter_warnings, is_blocked
from .engine import SURFACE_DETECTORS, detect
from .surfaces import SURFACES
from .types import CascadeHit, CascadeSeverity, CascadeType

__all__ = [
    "CascadeHit",
    "CascadeSeverity",
    "CascadeType",
    "SURFACES",
    "SURFACE_DETECTORS",
    "detect",
    "filter_blockers",
    "filter_warnings",
    "is_blocked",
]
