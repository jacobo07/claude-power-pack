"""Universal Quality Framework (UQF) -- ECC absorption v1.

Public surface of the framework. UQFAuditor + Principle + AuditReport
are the importable interfaces; everything else lives in submodules.

Portions adapted from Everything Claude Code (github.com/affaan-m/ecc)
under MIT License (c) 2026 Affaan Mustafa. Original principles cited
in submodule docstrings.
"""
from modules.uqf.principles import (
    Principle,
    PrincipleResult,
    register,
    get_all,
)

__all__ = [
    "Principle",
    "PrincipleResult",
    "register",
    "get_all",
]

__version__ = "1.0.0"
