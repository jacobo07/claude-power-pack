#!/usr/bin/env python3
"""pm_05_prefetch.py -- PM-05: Speculative Prefetch Engine (minimal, honest).

The mesh's one forward-looking dataset. Pre-warms the CHEAP, reusable assets a
pane will predictably need (an index, a dep map, a grep over a declared scope) so
the expensive moment is served from a warm asset. The weakest guarantee in the
family BY DESIGN -- a wrong guess is bounded cheap waste, never a burn and never a
wrong result (the lazy path is always the correct fallback).

Three hard constraints make a wrong guess harmless, and each is empirically
verifiable (which is why PM-05 is built rather than deferred):
  * cheap-only    -- only CO-03's deterministic/haiku rungs may prefetch. An Opus
                     prefetch is a routing violation, refused (not warned).
  * idle-only     -- runs ONLY in PM-04 GREEN mode AND when no pane is hot
                     (scheduler.gather_hot_sessions empty). A hot pane -> fail-stop.
  * net-positive  -- a per-class ledger auto-disables any prefetch class that
                     costs more than it saves. Optimism is not a strategy.

Parents: CO-04 (memory WARM -- prefetched assets are speculative WARM occupants),
CO-05 (registry -- a validated prefetch promotes to an asset), CO-03 (cheap rungs).

Honest (CO-10): "idle" is the coarse proxy "no hot session in the window" -- a
pane could still activate the next second; that is exactly why prefetch is
cheap-only and net-positive-gated, so the cost of a wrong idle read is bounded.
Fail-open ABSOLUTE: any error -> do not prefetch (the lazy path is always correct).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.parallel_mesh import pm_04_auction as _pm4  # noqa: E402

# Only these CO-03 rungs may prefetch. Opus/Sonnet reasoning is never speculated.
CHEAP_TIERS = ("deterministic", "haiku")
# Below this sample count a class gets the benefit of the doubt (not yet judged).
MIN_SAMPLES = 3


@dataclass
class PrefetchResult:
    ran: bool
    reason: str
    cls: str = ""
    asset: object = None


class NetPositiveLedger:
    """Per prefetch-class accounting: prefetches, hits, spent, saved (WU/MTok-ish).
    A class is disabled once it has enough samples AND saves less than it spends."""

    def __init__(self):
        self._c: dict = {}

    def _row(self, cls: str) -> dict:
        return self._c.setdefault(
            cls, {"prefetches": 0, "hits": 0, "spent": 0, "saved": 0})

    def record_prefetch(self, cls: str, *, spent: int = 1) -> None:
        r = self._row(cls)
        r["prefetches"] += 1
        r["spent"] += max(0, spent)

    def record_use(self, cls: str, *, saved: int = 0) -> None:
        r = self._row(cls)
        r["hits"] += 1
        r["saved"] += max(0, saved)

    def stats(self, cls: str) -> dict:
        return dict(self._row(cls))

    def is_enabled(self, cls: str) -> bool:
        """Enabled until proven net-negative (spent > saved over >= MIN_SAMPLES)."""
        r = self._row(cls)
        if r["prefetches"] < MIN_SAMPLES:
            return True
        return r["saved"] >= r["spent"]


class SpeculativePrefetch:
    """Runs a cheap prefetch ONLY under all three constraints. `cheap_fn` is the
    deterministic/Haiku producer (injected); it is called at most once, and only
    when every gate passes."""

    def __init__(self, ledger: NetPositiveLedger | None = None):
        self.ledger = ledger or NetPositiveLedger()

    def prefetch(self, repo: str, cls: str, cheap_fn, *, mode: str,
                 hot_count: int, tier: str = "deterministic",
                 est_cost: int = 1) -> PrefetchResult:
        """Attempt a speculative prefetch. Returns PrefetchResult(ran=...). Never
        raises (fail-open -> do not prefetch)."""
        try:
            if tier not in CHEAP_TIERS:
                return PrefetchResult(
                    False, f"cheap-only: tier '{tier}' is not {CHEAP_TIERS}", cls)
            if mode != _pm4.GREEN:
                return PrefetchResult(
                    False, f"idle-only: concurrency mode {mode} != GREEN", cls)
            if hot_count and hot_count > 0:
                return PrefetchResult(
                    False, f"idle-only: {hot_count} pane(s) hot -- fail-stop", cls)
            if not self.ledger.is_enabled(cls):
                return PrefetchResult(
                    False, f"net-negative: class '{cls}' auto-disabled", cls)
            asset = cheap_fn()
            self.ledger.record_prefetch(cls, spent=est_cost)
            return PrefetchResult(
                True, "prefetched (green + idle + cheap + net-positive)", cls, asset)
        except Exception:  # noqa: BLE001 -- fail-open: never prefetch on error
            return PrefetchResult(False, "error -- fail-open (no prefetch)", cls)

    def mark_used(self, cls: str, *, saved: int) -> None:
        """A prefetched asset was actually consumed -> record the saving so the
        net-positive ledger can keep the class enabled."""
        self.ledger.record_use(cls, saved=saved)


def main(argv=None) -> int:
    import argparse
    import os
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--repo", default=None)
    ap.add_argument("--cls", default="index")
    ap.add_argument("--tier", default="deterministic")
    ap.add_argument("--proj-base", default=None)
    args = ap.parse_args(argv)
    repo = args.repo or os.getcwd()
    mv = _pm4.current_mode(proj_base=args.proj_base)
    eng = SpeculativePrefetch()
    r = eng.prefetch(repo, args.cls, lambda: f"<{args.cls} index for {repo}>",
                     mode=mv.mode, hot_count=0, tier=args.tier)
    print(f"# mode={mv.mode} ran={r.ran} reason={r.reason}")
    if r.ran:
        print(r.asset)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
