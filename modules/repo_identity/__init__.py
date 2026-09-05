"""Canonical repository identity for per-repo state.

One version-control repository must produce one identity, whatever directory a
session happens to be sitting in when it writes.
"""
from .identity import (  # noqa: F401
    canonical_repo,
    repo_key,
    legacy_keys,
    ledger_paths,
)
