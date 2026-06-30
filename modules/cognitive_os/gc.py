#!/usr/bin/env python3
"""gc.py -- CO-06: Cognitive Garbage Collector (the hygiene policy).

CO-04 provides the MECHANISM to move content between memory tiers; CO-06 provides
the POLICY -- what to evict from HOT, when, and what to prune from the registry --
so context stays minimal and the asset store stays clean. It is the proactive,
surgical counterpart to /compact (continuous selective eviction, not an occasional
blunt stop-the-world reset), and it is what lets CO-00 defend the 60% ceiling
proactively (evict before the band, so the band is reached far less often).

Eviction scores HOT items by THREE signals (none sufficient alone): recency (LRU),
relevance (in the current working set?), aging (how long HOT, at what depth). The
working set + hard-rule-class + active task state are PINNED -- never evicted (the
safety rail that makes aggressive eviction safe). Eviction is graduated by the
CO-00 band (AMBER trims stale residue; RED demotes more aggressively).

Registry/exhaust hygiene prunes conservatively (cost asymmetry: dropping a useful
asset costs a re-derivation; keeping a dead one costs a little index space), and
NEVER drops a protected class. The Session-Safety guarantee is categorical: **no
`.jsonl` transcript is ever a prune candidate** -- CO-06 collects derived/resolved
exhaust only; primary session history is sacred. Honest limit: CO-06 cannot revoke
a running turn's context (rung-2, CO-00); it keeps HOT lean so resets are rare.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

PROTECTED_KINDS = ("hard-rule", "active-task", "active-todo", "todo")
_DEPTH_WEIGHT = {"full": 2.0, "summary": 1.0, "discovery": 0.0}
# Graduated eviction thresholds by CO-00 band (higher score = staler/lower value).
_BAND_THRESHOLD = {"AMBER": 12.0, "RED": 6.0, "BREACH": 4.0}


@dataclass
class GCItem:
    id: str
    kind: str = ""
    last_ref_turn: int = 0
    hot_since_turn: int = 0
    depth: str = "discovery"
    in_working_set: bool = False
    protected: bool = False


def is_transcript(path) -> bool:
    """A primary session transcript -- categorically excluded from pruning
    (Session Safety Contract S1). Never matched by the prune allow-list."""
    return bool(path) and str(path).lower().endswith(".jsonl")


def is_protected(item: GCItem, *, working_set_ids=()) -> bool:
    """The pin set: the working set, hard-rule-class, and active task state are
    never eviction candidates."""
    return (item.in_working_set or item.id in set(working_set_ids or ())
            or item.kind in PROTECTED_KINDS or item.protected)


def eviction_score(item: GCItem, *, current_turn: int) -> float:
    """Composite recency + relevance + aging. Higher = staler/lower-value =
    stronger eviction candidate."""
    recency = max(0, current_turn - item.last_ref_turn)        # turns since used
    relevance = 0.0 if item.in_working_set else 10.0           # off-working-set
    aging = max(0, current_turn - item.hot_since_turn) * 0.5   # time HOT
    return recency + relevance + aging + _DEPTH_WEIGHT.get(item.depth, 0.0)


def eviction_candidates(items, *, current_turn: int, band: str = "AMBER",
                        working_set_ids=()) -> list:
    """HOT items to demote now, ranked staleest-first, PINNED items excluded,
    graduated by the CO-00 band. Lossless (CO-04 demote keeps a WARM pointer)."""
    thresh = _BAND_THRESHOLD.get(band, 999.0)
    scored = []
    for i in items:
        if is_protected(i, working_set_ids=working_set_ids):
            continue
        s = eviction_score(i, current_turn=current_turn)
        if s >= thresh:
            scored.append((s, i))
    scored.sort(key=lambda t: t[0], reverse=True)
    return [i for _, i in scored]


def _parse_ts(s):
    try:
        d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def prune_candidates(assets, *, now: datetime | None = None,
                     retention_days: int = 30) -> list:
    """Registry/exhaust prune candidates (CO-06 II). Conservative: only a
    zero-retrieval, aged, NON-protected, NON-transcript asset is a candidate.
    A `.jsonl` transcript is categorically excluded -- never a candidate."""
    now = now or datetime.now(timezone.utc)
    out = []
    for a in assets:
        if is_transcript(a.get("path")):
            continue                                   # sacred -- never pruned
        if a.get("protected") or a.get("kind") == "hard-rule":
            continue                                   # protected class
        if int(a.get("retrievals", 0) or 0) > 0:
            continue                                   # used -> keep
        ts = _parse_ts(a.get("stored_ts"))
        if ts is not None and (now - ts).days >= retention_days:
            out.append(a)
    return out


def main(argv=None) -> int:
    import argparse
    import json
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--band", default="AMBER")
    args = ap.parse_args(argv)
    print(json.dumps({"band": args.band,
                      "threshold": _BAND_THRESHOLD.get(args.band)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
