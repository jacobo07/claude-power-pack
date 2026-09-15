#!/usr/bin/env python3
"""A record on every judgement, not only on the ones that fire.

A guard that writes only when it acts cannot answer the one question that
matters after it fails to act: did it run? A predicate that never received the
case and a predicate that received it and passed produce the same observable --
nothing happened -- and they need opposite fixes. The estate has paid for this
twice: closer-guard sat correct and structurally unreachable in exactly its
highest-value case, and 38 of 45 of its timeouts shared a second with another
hook, failing open and silently each time.

So this advances on EVERY evaluation, including the ones that abstain and the
ones that bottom out on the floor. A counter that did not move across the window
of an escaped case is proof of non-delivery, and it has to exist before the
incident, not after.

Write surface is ~/.claude/state/, matching closer-guard and d2a_gate rather
than inventing a third convention, and deliberately NOT the repository: this
fires on every user prompt, and a repo write per prompt is continuous status
noise in a tree where another writer may be committing.

Fail-open is absolute. A heartbeat must never cost a turn.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

_STATE = Path(os.environ.get("CLAUDE_STATE_DIR") or (Path.home() / ".claude" / "state"))
HEARTBEAT = _STATE / "gsd-x-heartbeat.json"

# Bounded: the tail is a debugging aid, not an archive. The counters are the
# durable half and they never reset.
_TAIL = 20


def _empty() -> dict:
    return {
        "judgements": 0,
        "by_tier": {},
        "by_floor": 0,
        "abstained": 0,
        "informative": 0,
        "first_seen": None,
        "last_seen": None,
        "recent": [],
    }


def read() -> dict:
    """Current state, or an empty record. Never raises."""
    try:
        return json.loads(HEARTBEAT.read_text(encoding="utf-8-sig"))
    except Exception:                                  # noqa: BLE001
        return _empty()


def record(tier: str, *, by_floor: bool, abstained: bool,
           informative: bool, reason: str = "") -> bool:
    """Advance the counters. Returns whether the write landed.

    The return value is reported, never enforced: a caller that treats a failed
    heartbeat as a failure would convert an observability aid into an outage.
    """
    try:
        state = read()
        now = time.time()
        state["judgements"] = int(state.get("judgements", 0)) + 1
        tiers = state.setdefault("by_tier", {})
        tiers[tier] = int(tiers.get(tier, 0)) + 1
        if by_floor:
            state["by_floor"] = int(state.get("by_floor", 0)) + 1
        if abstained:
            state["abstained"] = int(state.get("abstained", 0)) + 1
        if informative:
            state["informative"] = int(state.get("informative", 0)) + 1
        state["first_seen"] = state.get("first_seen") or now
        state["last_seen"] = now
        recent = list(state.get("recent") or [])
        recent.append({"t": now, "tier": tier, "floor": by_floor,
                       "reason": reason[:160]})
        state["recent"] = recent[-_TAIL:]

        HEARTBEAT.parent.mkdir(parents=True, exist_ok=True)
        tmp = HEARTBEAT.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(state), encoding="utf-8")
        os.replace(tmp, HEARTBEAT)                     # atomic; no torn reads
        return True
    except Exception:                                  # noqa: BLE001
        return False


def informative_rate() -> float | None:
    """Share of judgements that said more than the constant string already does.

    None when nothing has been judged -- an empty denominator is not a zero
    rate, and reporting 0.0 for "never ran" is the exact confusion this module
    exists to prevent.
    """
    state = read()
    total = int(state.get("judgements", 0))
    if total == 0:
        return None
    return int(state.get("informative", 0)) / total


if __name__ == "__main__":
    s = read()
    rate = informative_rate()
    print(f"judgements : {s.get('judgements', 0)}")
    print(f"by tier    : {s.get('by_tier', {})}")
    print(f"by floor   : {s.get('by_floor', 0)}")
    print(f"abstained  : {s.get('abstained', 0)}")
    print(f"informative: {s.get('informative', 0)}"
          f"  ({'n/a -- nothing judged' if rate is None else f'{rate:.0%}'})")
    print(f"path       : {HEARTBEAT}")
