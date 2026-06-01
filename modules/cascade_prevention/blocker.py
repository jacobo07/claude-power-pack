"""Filter / partition cascade hits for callers (warn vs block)."""
from __future__ import annotations

from .types import CascadeHit


def filter_blockers(hits: list[CascadeHit]) -> list[CascadeHit]:
    return [h for h in hits if h.should_block]


def filter_warnings(hits: list[CascadeHit]) -> list[CascadeHit]:
    return [h for h in hits if h.should_warn and not h.should_block]


def is_blocked(hits: list[CascadeHit]) -> bool:
    return any(h.should_block for h in hits)
