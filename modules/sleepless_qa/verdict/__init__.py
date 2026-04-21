"""Verdict package — schema + strategies + aggregator."""

from __future__ import annotations

from .engine import judge
from .schema import Verdict, VerdictStatus

__all__ = ["judge", "Verdict", "VerdictStatus"]
