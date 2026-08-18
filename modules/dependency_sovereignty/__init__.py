"""Dependency Sovereignty -- what a dependency costs the institution.

R1 of the UPAC ownership audit. The public surface is deliberately small: a scan,
the ladder verdict, and the coverage report that keeps the scan honest about the
manifests it could not parse.
"""
from .sovereignty import (
    Dependency,
    decide,
    scan,
    manifest_coverage,
    render,
    main,
    MEASURED,
    UNKNOWN,
    UNREACHABLE_HERE,
    EXACT,
    RANGE,
    UNPINNED,
    USE,
    WRAP,
    DO_NOT_USE,
    REVIEW,
    UNREACHABLE_RUNGS,
    WRAP_THRESHOLD,
    count_call_sites,
)

__all__ = [
    "Dependency", "decide", "scan", "manifest_coverage", "render", "main",
    "count_call_sites",
    "MEASURED", "UNKNOWN", "UNREACHABLE_HERE",
    "EXACT", "RANGE", "UNPINNED",
    "USE", "WRAP", "DO_NOT_USE", "REVIEW",
    "UNREACHABLE_RUNGS", "WRAP_THRESHOLD",
]
