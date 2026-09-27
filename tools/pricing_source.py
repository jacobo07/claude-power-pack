#!/usr/bin/env python3
"""Resolve the current pricing provenance file.

Pricing lives in dated files, vault/pricing/anthropic_YYYY-MM.json, and a
superseded file is kept as the record of what was believed then. Three tools
hardcoded `anthropic_2026-05.json`, so a newer file could land and nothing
would read it -- which is how a $15/$75 Opus 4 rate survived four months
under the claude-opus-4-7 id. Every consumer asks here instead.
"""
from __future__ import annotations

import re
from pathlib import Path

PRICING_DIR = Path(__file__).resolve().parent.parent / "vault" / "pricing"
_DATED = re.compile(r"^anthropic_(\d{4})-(\d{2})\.json$")


def current_pricing_path(pricing_dir: Path = PRICING_DIR) -> Path:
    """Newest anthropic_YYYY-MM.json by the date in its name.

    Raises FileNotFoundError when none exists: a missing pricing source is a
    configuration fault for the caller to surface, never an empty price list.
    """
    dated = []
    for p in pricing_dir.glob("anthropic_*.json"):
        m = _DATED.match(p.name)
        if m:
            dated.append(((int(m.group(1)), int(m.group(2))), p))
    if not dated:
        raise FileNotFoundError(f"no anthropic_YYYY-MM.json under {pricing_dir}")
    return max(dated)[1]


def pricing_path_or_missing(pricing_dir: Path = PRICING_DIR) -> Path:
    """For consumers that already report an absent file through their own
    `is_file()` branch: the current file, or a path that cannot exist, so
    that branch fires with its own words instead of an import-time crash."""
    try:
        return current_pricing_path(pricing_dir)
    except FileNotFoundError:
        return pricing_dir / "anthropic_NONE-FOUND.json"


if __name__ == "__main__":
    print(current_pricing_path())
