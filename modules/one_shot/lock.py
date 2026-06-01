"""Fidelity lock -- scope-deviation detector."""
from __future__ import annotations

from .compiler import OneShotContract

# A contract is "deviated" when fewer than this fraction of touched
# files are in-scope. 40% is the Owner-sealed default; below this we
# should pause and re-prompt.
SCOPE_DEVIATION_THRESHOLD = 0.4

# Tokens shorter than this are too generic to anchor scope ("is",
# "on", "the"). 3 chars filters them while keeping useful nouns.
MIN_SCOPE_TOKEN_LEN = 3


def fidelity_score(
    contract: OneShotContract, actual_files_touched: list[str],
) -> float:
    """Return the fraction of touched files that are in-scope.

    v1 heuristic: a file is in-scope if any token from the contract's
    `scope` strings appears as a substring of the file path (case
    insensitive). This is intentionally generous -- the goal is to
    flag obvious deviation, not to police every cross-cut.
    """
    if not actual_files_touched:
        return 1.0
    scope_tokens: set[str] = set()
    for s in contract.scope:
        scope_tokens.update(
            t for t in s.lower().split() if len(t) >= MIN_SCOPE_TOKEN_LEN
        )
    if not scope_tokens:
        return 1.0
    in_scope = 0
    for f in actual_files_touched:
        path = f.lower()
        if any(t in path for t in scope_tokens):
            in_scope += 1
    return in_scope / len(actual_files_touched)


def is_deviated(
    contract: OneShotContract, actual_files_touched: list[str],
) -> bool:
    return fidelity_score(contract, actual_files_touched) < SCOPE_DEVIATION_THRESHOLD
