"""Predictive cascade detection (SEIP-EXT-D3).

Every detector in `engine.py` is a PRESENT-STATE rule: is this a deploy, and did the
tests pass. None of them consults history, so none of them can fire *before* a second
failure -- yet "fires before the second error in a known chain, not after" is the
standing claim made for this surface. The claim lived in an agent description; the code
had `_detect_session` returning an empty list.

This module supplies the missing half, and -- more importantly -- makes the claim
FALSIFIABLE. The interesting output here is not a prediction. It is the measurement of
whether a prediction is possible at all.

WHAT THE SUBSTRATE ACTUALLY SUPPORTS
------------------------------------
Measured 2026-08-06 over `vault/ceps/events.jsonl`:

    9 events, 2 distinct timestamps one second apart, 9 distinct categories.

Two consequences, both fatal to naive inference:

1. A 5-minute co-occurrence window over a 1-second span pairs EVERY event with EVERY
   other. The window stops discriminating, so it ranks nothing -- the sealed
   `feedback_constant_factors_rank_nothing` shape, where a factor constant across all
   items contributes no ordering. A detector built on it would fire always, and firing
   always is indistinguishable from not detecting.
2. Each category occurs exactly once, so NO ordered pair co-occurs twice. The
   bootstrap guard ("silent until a pair has 2+ co-occurrences") is therefore
   permanently unsatisfiable on this store. The guard has been correctly silent for 72
   days, and would stay silent forever -- dead by starvation at the data layer rather
   than the code layer.

So this module returns UNMEASURABLE and says why. It does not manufacture a prior from
a degenerate store, and it does not stay quietly silent either: silence was already the
behaviour, and silence is what hid the problem. Naming the degeneracy is the change.

    python -m modules.cascade_prevention.predictive        # substrate report

Fail-open throughout: an absent or malformed store is SUBSTRATE_ABSENT, never a raise.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
EVENTS_PATH = _PP_ROOT / "vault" / "ceps" / "events.jsonl"

# Co-occurrence window. Meaningful ONLY when the store spans longer than it does.
DEFAULT_WINDOW_S = 300
# A pair seen once is an anecdote. Two is the minimum that can be called a pattern.
MIN_COOCCURRENCE = 2
# Ordering cannot be observed across fewer distinct instants than this.
MIN_DISTINCT_TIMESTAMPS = 3

SUBSTRATE_OK = "SUBSTRATE_OK"
SUBSTRATE_DEGENERATE = "SUBSTRATE_DEGENERATE"
SUBSTRATE_ABSENT = "SUBSTRATE_ABSENT"

PREDICTED = "PREDICTED"
NOT_PREDICTED = "NOT_PREDICTED"
UNMEASURABLE = "UNMEASURABLE"


def _parse_ts(raw) -> datetime | None:
    if not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def load_events(path: Path | None = None) -> list:
    """Every well-formed event, oldest first. Malformed lines are skipped, not fatal."""
    p = Path(path) if path else EVENTS_PATH
    out = []
    try:
        raw = p.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return out
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        ts = _parse_ts(row.get("ts"))
        cat = row.get("category")
        if ts is None or not cat:
            continue
        out.append({"ts": ts, "category": str(cat), "id": row.get("id", "")})
    out.sort(key=lambda r: r["ts"])
    return out


def substrate_quality(events: list | None = None,
                      window_s: int = DEFAULT_WINDOW_S) -> dict:
    """Can this store support temporal inference at all? Absolute counts only."""
    ev = load_events() if events is None else events
    if not ev:
        return {"verdict": SUBSTRATE_ABSENT, "events": 0, "distinct_timestamps": 0,
                "span_seconds": 0, "window_seconds": window_s,
                "window_discriminates": False, "pairs_at_threshold": 0,
                "reason": "no well-formed events; nothing can be inferred"}

    stamps = {e["ts"] for e in ev}
    span = (max(stamps) - min(stamps)).total_seconds()
    # A window wider than the entire recorded span includes every pair, so it imposes
    # no ordering. This is the check that would have caught the problem from the start.
    discriminates = span >= window_s
    pairs = co_occurrence(ev, window_s)
    at_threshold = [f"{a}->{b}" for (a, b), n in pairs.items() if n >= MIN_COOCCURRENCE]

    reasons = []
    if len(stamps) < MIN_DISTINCT_TIMESTAMPS:
        reasons.append(
            f"{len(stamps)} distinct timestamp(s) across {len(ev)} events -- "
            f"precedence is not observable below {MIN_DISTINCT_TIMESTAMPS}")
    if not discriminates:
        reasons.append(
            f"the {window_s}s window exceeds the {span:g}s recorded span, so it pairs "
            "every event with every other and therefore ranks nothing")
    if not at_threshold:
        reasons.append(
            f"no ordered pair reaches {MIN_COOCCURRENCE} co-occurrences, so the "
            "bootstrap guard cannot be satisfied by this store")

    if reasons:
        return {"verdict": SUBSTRATE_DEGENERATE, "events": len(ev),
                "distinct_timestamps": len(stamps), "span_seconds": span,
                "window_seconds": window_s, "window_discriminates": discriminates,
                "pairs_at_threshold": 0, "reason": "; ".join(reasons)}

    return {"verdict": SUBSTRATE_OK, "events": len(ev),
            "distinct_timestamps": len(stamps), "span_seconds": span,
            "window_seconds": window_s, "window_discriminates": True,
            "pairs_at_threshold": len(at_threshold), "pairs": sorted(at_threshold),
            "reason": f"{len(at_threshold)} ordered pair(s) meet the threshold"}


def co_occurrence(events: list, window_s: int = DEFAULT_WINDOW_S) -> Counter:
    """Ordered category pairs (A before B) observed within the window."""
    pairs: Counter = Counter()
    for i, a in enumerate(events):
        for b in events[i + 1:]:
            delta = (b["ts"] - a["ts"]).total_seconds()
            if delta > window_s:
                break                      # sorted, so nothing later is closer
            if a["category"] != b["category"]:
                pairs[(a["category"], b["category"])] += 1
    return pairs


def predict(category: str, events: list | None = None,
            window_s: int = DEFAULT_WINDOW_S) -> dict:
    """What has historically FOLLOWED this category, and how often?

    Returns UNMEASURABLE rather than a prior whenever the substrate cannot support the
    inference. A number computed from a degenerate store is worse than no number: it
    carries the authority of measurement without the content.
    """
    ev = load_events() if events is None else events
    quality = substrate_quality(ev, window_s)
    if quality["verdict"] != SUBSTRATE_OK:
        return {"verdict": UNMEASURABLE, "category": category, "prior": None,
                "predicts": "", "basis": "", "substrate": quality["verdict"],
                "reason": quality["reason"]}

    pairs = co_occurrence(ev, window_s)
    outgoing = {b: n for (a, b), n in pairs.items() if a == category}
    total = sum(outgoing.values())
    if not outgoing or total == 0:
        return {"verdict": NOT_PREDICTED, "category": category, "prior": None,
                "predicts": "", "basis": "", "substrate": SUBSTRATE_OK,
                "reason": f"{category} has never been observed to precede another "
                          "category within the window"}

    successor, count = max(outgoing.items(), key=lambda kv: kv[1])
    if count < MIN_COOCCURRENCE:
        return {"verdict": NOT_PREDICTED, "category": category, "prior": None,
                "predicts": "", "basis": "", "substrate": SUBSTRATE_OK,
                "reason": f"the strongest successor {successor!r} was seen {count}x; "
                          f"{MIN_COOCCURRENCE} is the minimum that is a pattern rather "
                          "than an anecdote"}

    return {"verdict": PREDICTED, "category": category,
            "prior": count / total, "predicts": successor,
            "basis": f"{count}/{total} observed transitions from {category} within "
                     f"{window_s}s over {quality['events']} events",
            "substrate": SUBSTRATE_OK,
            "reason": f"{category} preceded {successor} in {count} of {total} "
                      "observed transitions"}


def main(argv=None) -> int:
    q = substrate_quality()
    print(json.dumps(q, ensure_ascii=False, indent=2, default=str))
    # Exit 0 even when degenerate: a thin evidence store is a gap in what has been
    # recorded, not a broken build, and failing here would pressure someone to
    # manufacture events to make a gate go green.
    return 0


if __name__ == "__main__":
    sys.exit(main())
