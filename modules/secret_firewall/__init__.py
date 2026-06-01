"""Secret Firewall -- BL-SECRET-001.

Public API: scan_text, scan_file, is_critical, summary, redact,
redact_for_log, report, is_allowed.
"""
from .detector import (
    Hit,
    PATTERNS,
    Severity,
    is_critical,
    scan_file,
    scan_text,
    summary,
)
from .redactor import redact, redact_for_log
from .reporter import report
from .allowlist import is_allowed

__all__ = [
    "Hit",
    "PATTERNS",
    "Severity",
    "is_critical",
    "is_allowed",
    "redact",
    "redact_for_log",
    "report",
    "scan_file",
    "scan_text",
    "summary",
]
