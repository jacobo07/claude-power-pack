"""Mirror pair discovery -- the producer that replaced a hand-written list.

Consumed by `tools/verify_global_mirrors.py` (Mirror Parity Law done-gate).
"""
from .discovery import (  # noqa: F401
    ALIASES,
    DOMAINS,
    ENV_LIVE_ROOT,
    FOREIGN_PREFIXES,
    LIVE_ONLY,
    LIVE_ROOT_DEFAULT,
    PAIRED,
    REPO_ONLY,
    Discovery,
    Pair,
    discover,
    resolve_live_root,
)

__all__ = [
    "ALIASES", "DOMAINS", "ENV_LIVE_ROOT", "FOREIGN_PREFIXES", "LIVE_ONLY",
    "LIVE_ROOT_DEFAULT", "PAIRED", "REPO_ONLY", "Discovery", "Pair",
    "discover", "resolve_live_root",
]
