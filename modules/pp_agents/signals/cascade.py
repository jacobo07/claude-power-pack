"""pp-cascade-guard signal -- Woz gate on known cascade patterns.

Reads CEPS events.jsonl and builds a co-occurrence map: error A at
time T is correlated with error B if B appears within 5 minutes of
A and the (A, B) pair has been observed at least 2 times. When the
current error matches a known A, the agent surfaces the likely B/C
followers so the Owner fixes the root and not the leaf.

Sealed BL-HARDRULE-001 (2026-05-29).
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[3]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.pp_agents.proactive_core import ProactiveSignal

EVENTS_PATH = PP_ROOT / "vault" / "ceps" / "events.jsonl"
CASCADE_WINDOW_SECONDS = 300
MIN_COOCCURRENCE = 2


def _load_events() -> list[dict]:
    if not EVENTS_PATH.is_file():
        return []
    out: list[dict] = []
    for line in EVENTS_PATH.read_text(encoding="utf-8-sig").splitlines():
        s = line.strip()
        if not s:
            continue
        try:
            out.append(json.loads(s))
        except ValueError:
            continue
    return out


def _parse_ts(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _error_key(event: dict) -> str:
    cat = str(event.get("category", "") or "").strip()
    sub = str(event.get("subsystem", "") or "").strip()
    if cat and sub:
        return f"{cat}:{sub}"
    return cat or sub


def _build_cascade_map() -> dict[str, list[str]]:
    """Return {error_key: [likely_follower_keys]}.

    Reads CEPS events.jsonl, sorts by ts, then for each event looks
    at the next 10 events within CASCADE_WINDOW_SECONDS and counts
    each distinct (key_a, key_b) co-occurrence. Followers with count
    >= MIN_COOCCURRENCE are returned per source key.
    """
    events = _load_events()
    if not events:
        return {}
    indexed: list[tuple[datetime, str]] = []
    for e in events:
        key = _error_key(e)
        ts = _parse_ts(str(e.get("ts", "")))
        if key and ts is not None:
            indexed.append((ts, key))
    indexed.sort(key=lambda t: t[0])

    co: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for i, (t_a, key_a) in enumerate(indexed):
        for t_b, key_b in indexed[i + 1:i + 11]:
            if (t_b - t_a).total_seconds() > CASCADE_WINDOW_SECONDS:
                break
            if key_b and key_b != key_a:
                co[key_a][key_b] += 1

    cascade_map: dict[str, list[str]] = {}
    for src, followers in co.items():
        strong = sorted([k for k, n in followers.items()
                         if n >= MIN_COOCCURRENCE])
        if strong:
            cascade_map[src] = strong
    return cascade_map


def evaluate(current_error: str = "",
             project: str = "global",
             category: str = "",
             subsystem: str = "") -> ProactiveSignal | None:
    """Fire when the current error matches a known cascade source.

    Two match paths, because the producer and the consumer spoke different
    languages. `_build_cascade_map` keys on `f"{category}:{subsystem}"` -- a composite
    the CEPS recorder assembles from two STRUCTURED fields -- while the live dispatcher
    passes raw error TEXT. A composite like "regression:bash:cat" never appears verbatim
    inside an error message, so the substring path could only ever match a caller that
    already knew the key. Measured 2026-08-25: the store's own newest error text returned
    None while the synthetic key fired.

    Structured input is therefore matched on the key itself. The text path is kept
    unchanged so no existing caller regresses.
    """
    # Cheapest possible exit FIRST. The original returned on an empty current_error
    # before touching the store; moving the map build above that early return made every
    # dispatch parse events.jsonl even with nothing to match, and the benchmark caught it
    # at proactive_dispatch_ms 123 vs a 30 ms target. Building an index you cannot query
    # is pure cost -- widening an input contract must not widen the no-input path.
    if not (category or current_error):
        return None
    cascade_map = _build_cascade_map()
    if not cascade_map:
        return None

    src_key = ""
    if category:
        want = _error_key({"category": category, "subsystem": subsystem})
        if want in cascade_map:
            src_key = want
        else:
            # The live subsystem can be finer-grained than what was recorded. Fall back
            # to the category, but ONLY when it identifies a single source: co-occurrence
            # was learned at subsystem granularity, and picking one of several keys that
            # merely share a category would invent a specificity the data never had.
            same_cat = [k for k in cascade_map
                        if k.split(":", 1)[0] == category]
            if len(same_cat) == 1:
                src_key = same_cat[0]
    if not src_key and current_error:
        haystack = current_error.lower()
        for k in cascade_map:
            if k.lower() in haystack:
                src_key = k
                break
    if not src_key:
        return None

    followers = cascade_map[src_key]
    followers_str = ", ".join(followers[:3])
    return ProactiveSignal(
        agent_name="pp-cascade-guard",
        trigger="cascade_pattern_detected",
        value=0.85,
        advisory=(
            f"'{src_key}' has historically preceded: "
            f"{followers_str}.\n"
            f"Woz: did you fix the root or only the leaf?"
        ),
        gate="woz",
        actionable=(
            "Verify these components before continuing: "
            + ", ".join(followers[:3])
        ),
    )


__all__ = [
    "EVENTS_PATH",
    "CASCADE_WINDOW_SECONDS",
    "MIN_COOCCURRENCE",
    "_build_cascade_map",
    "evaluate",
]
