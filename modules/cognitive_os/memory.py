#!/usr/bin/env python3
"""memory.py -- CO-04: Context Virtual Memory (Hot / Warm / Cold / External).

The kernel's memory hierarchy. Context is the scarcest resource (CO-00), so the
live window is treated like a CPU's registers: only the working set is HOT;
everything else lives one tier down, paged in on PROVEN need. This is the
*proactive* defense of the 60% ceiling -- load less, rather than compact later.

  HOT      -- in the live window now. Highest context cost (counts vs 60%), zero
              latency. A WORKING SET, not an archive.
  WARM     -- indexed + instantly recoverable (CO-05 registry, FTS5, audit_cache,
              snapshots). ~Zero context cost (a pointer), low latency, full trust.
  COLD     -- datasets, transcripts, archives: zero context cost until summoned,
              higher latency, full trust (own data).
  EXTERNAL -- out of process (web, other repos, MCP): zero context cost, highest
              latency, UNTRUSTED until validated (CO-10 / prompt-defense baseline).

CO-04 provides the MECHANISM (the tiers + the lossless page-out path); CO-06
provides the POLICY (what to evict). EXTEND of jit_skill_loader's proto Hot/Warm
(discovery->summary->full depth ladder, 40KB circuit breaker), generalized to all
context + the Cold/External tiers it lacks. Honest limit: CO-04 minimizes what is
LOADED (the part the kernel controls); it cannot revoke context a running turn
holds mid-generation (rung-2 limit, CO-00).
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

HOT, WARM, COLD, EXTERNAL = "HOT", "WARM", "COLD", "EXTERNAL"

# Context cost rank (HOT highest). Lower-cost tier preferred when it satisfies.
TIER_RANK = {HOT: 0, WARM: 1, COLD: 2, EXTERNAL: 3}
TIER_CONTEXT_COST = {HOT: "high", WARM: "pointer", COLD: "zero", EXTERNAL: "zero"}
TIER_TRUST = {HOT: "full", WARM: "full", COLD: "full", EXTERNAL: "untrusted"}

DEPTHS = ("discovery", "summary", "full")     # the page-in ladder (cheap->full)

# kind -> home tier.
_KIND_TIER = {
    "skill-full": HOT, "task-file": HOT, "working": HOT, "active-todo": HOT,
    "skill-summary": WARM, "vault-asset": WARM, "audit-summary": WARM,
    "snapshot": WARM, "skill-card": WARM, "index": WARM,
    "transcript": COLD, "archive": COLD, "research": COLD, "handoff": COLD,
    "old-session": COLD, "log": COLD,
    "web": EXTERNAL, "mcp": EXTERNAL, "other-repo": EXTERNAL,
    "unindexed-file": EXTERNAL, "fetched": EXTERNAL,
}


@dataclass
class MemoryItem:
    id: str
    kind: str
    tier: str = ""
    depth: str = "discovery"
    size_tokens: int = 0
    last_ref_turn: int = 0
    in_working_set: bool = False
    anchor: dict | None = None

    def __post_init__(self):
        if not self.tier:
            self.tier = tier_of(self.kind)


def tier_of(kind: str) -> str:
    """Home tier for a context item kind. Unknown -> EXTERNAL (lowest trust)."""
    return _KIND_TIER.get(kind, EXTERNAL)


def is_external_untrusted(item: MemoryItem) -> bool:
    """EXTERNAL data must be validated before it can influence reasoning."""
    return item.tier == EXTERNAL


def page_in_depth(need: str | None) -> str:
    """Minimum depth that satisfies the need (CO-04 II.1): never load full when a
    summary suffices. Default 'discovery' (the cheapest, an 80-token pointer)."""
    return need if need in DEPTHS else "discovery"


def cheaper_tier_preferred(a: str, b: str) -> str:
    """The lower-context-cost tier of two (used by CO-03's cheapest-first)."""
    return a if TIER_RANK.get(a, 9) >= TIER_RANK.get(b, 9) else b  # higher rank = cheaper


def demote(item: MemoryItem) -> MemoryItem:
    """Lossless page-out HOT->WARM: the content becomes a pointer (summary depth),
    recoverable from WARM/COLD on the next proven need. Never destroys content."""
    return replace(item, tier=WARM, depth="summary")


def working_set(items) -> list:
    """The items that must stay HOT (the current task's working set)."""
    return [i for i in items if i.in_working_set]


def hot_token_load(items) -> int:
    return sum(i.size_tokens for i in items if i.tier == HOT)


def hot_budget_ok(items, *, cap_tokens: int) -> bool:
    """The generalized 40KB circuit breaker: HOT promotions are capped so a burst
    of page-ins cannot itself breach the ceiling."""
    return hot_token_load(items) <= cap_tokens


@dataclass
class MemoryView:
    hot: list = field(default_factory=list)
    warm: list = field(default_factory=list)
    cold: list = field(default_factory=list)
    external: list = field(default_factory=list)


def classify(items) -> MemoryView:
    """Group items by tier -- the kernel's single memory-hierarchy read."""
    v = MemoryView()
    bucket = {HOT: v.hot, WARM: v.warm, COLD: v.cold, EXTERNAL: v.external}
    for i in items:
        bucket.get(i.tier, v.external).append(i)
    return v


def main(argv=None) -> int:
    import argparse
    import json
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--kind", default="skill-full")
    args = ap.parse_args(argv)
    t = tier_of(args.kind)
    print(json.dumps({"kind": args.kind, "tier": t,
                      "context_cost": TIER_CONTEXT_COST[t],
                      "trust": TIER_TRUST[t]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
