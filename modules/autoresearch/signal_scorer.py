"""
Signal scoring and deduplication module for autoresearch.

Scores signals on a 0.0-1.0 scale using weighted factors:
  - authority  (0.35): source credibility
  - keyword    (0.35): keyword density in title + summary
  - recency    (0.20): age decay (1.0 at 0h, ~0.0 at 72h)
  - entry_count(0.10): normalized volume from that source burst

Deduplication uses a sliding-window SHA-256 approach keyed on
project:source:window_start so the same signal is not re-emitted
within a configurable window (default 6 hours).
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dedup cache
# ---------------------------------------------------------------------------

DedupCache = dict[str, float]  # hash -> epoch timestamp


def load_dedup_cache(cache_path: Path) -> DedupCache:
    """Load the dedup cache from disk. Returns empty dict if missing/corrupt."""
    cache_path = Path(cache_path)
    if not cache_path.exists():
        return {}
    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            logger.warning("Dedup cache is not a dict, resetting")
            return {}
        return {k: float(v) for k, v in data.items()}
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Corrupt dedup cache at %s: %s — resetting", cache_path, exc)
        return {}


def save_dedup_cache(cache_path: Path, cache: DedupCache) -> None:
    """Persist the dedup cache, pruning entries older than 48 hours."""
    cache_path = Path(cache_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cutoff = time.time() - 48 * 3600
    pruned = {k: v for k, v in cache.items() if v > cutoff}
    cache_path.write_text(json.dumps(pruned, indent=2), encoding="utf-8")
    logger.debug("Saved dedup cache with %d entries (pruned %d)", len(pruned), len(cache) - len(pruned))


def _dedup_key(project: str, source: str, window_hours: float) -> str:
    """Build a SHA-256 hash key scoped to project + source + time window."""
    window_start = int(time.time() // (window_hours * 3600))
    raw = f"{project}:{source}:{window_start}"
    return hashlib.sha256(raw.encode()).hexdigest()


def is_duplicate(project: str, source: str, cache: DedupCache, window_hours: float = 6) -> bool:
    """Return True if this project:source pair was already seen in the current window."""
    key = _dedup_key(project, source, window_hours)
    return key in cache


def mark_seen(project: str, source: str, cache: DedupCache, window_hours: float = 6) -> None:
    """Mark a project:source pair as seen in the current dedup window."""
    key = _dedup_key(project, source, window_hours)
    cache[key] = time.time()


# ---------------------------------------------------------------------------
# Signal scoring
# ---------------------------------------------------------------------------

# Weight constants
W_AUTHORITY = 0.35
W_KEYWORD = 0.35
W_RECENCY = 0.20
W_ENTRY_COUNT = 0.10


def _keyword_density(text: str, keywords: list[str]) -> float:
    """
    Fraction of keywords found in *text* (case-insensitive).
    Returns 0.0 if no keywords configured, 1.0 if all match.
    """
    if not keywords:
        return 1.0  # no filter means everything passes
    text_lower = text.lower()
    hits = sum(1 for kw in keywords if kw.lower() in text_lower)
    return hits / len(keywords)


def _recency_score(published_epoch: float | None) -> float:
    """
    Exponential decay: 1.0 at publish time, ~0.5 at 24h, ~0.0 at 72h.
    Returns 0.5 if no timestamp provided.
    """
    if published_epoch is None:
        return 0.5
    age_hours = max(0.0, (time.time() - published_epoch) / 3600)
    # half-life of 24 hours
    return math.exp(-0.693 * age_hours / 24)


def _entry_count_score(count: int) -> float:
    """Normalize entry count: log2-based saturation at ~32 entries."""
    if count <= 0:
        return 0.0
    return min(1.0, math.log2(count + 1) / 5.0)


def score_signal(signal: dict[str, Any], config: dict[str, Any]) -> float:
    """
    Score a signal dict on 0.0-1.0.

    Expected signal keys:
        - project (str): project name
        - source (str): feed/channel name
        - title (str): entry title
        - summary (str): entry summary/description
        - published_epoch (float|None): publication timestamp
        - entry_count (int): how many entries matched in this burst
        - authority (float): source authority from config (0.0-1.0)
        - keywords (list[str]): applicable keyword filters
    """
    authority = float(signal.get("authority", 0.5))
    keywords = signal.get("keywords", [])

    # Combine title + summary for keyword matching
    text = f"{signal.get('title', '')} {signal.get('summary', '')}"

    # Also check universal keywords from config
    universal = config.get("universal_keywords", [])
    all_keywords = keywords + universal if keywords else []

    kw_score = _keyword_density(text, all_keywords) if all_keywords else 1.0
    recency = _recency_score(signal.get("published_epoch"))
    entry_ct = _entry_count_score(signal.get("entry_count", 1))

    score = (
        W_AUTHORITY * authority
        + W_KEYWORD * kw_score
        + W_RECENCY * recency
        + W_ENTRY_COUNT * entry_ct
    )
    return round(min(1.0, max(0.0, score)), 4)


def filter_signals(
    signals: list[dict[str, Any]],
    config: dict[str, Any],
    cache: DedupCache,
) -> list[dict[str, Any]]:
    """
    Score, deduplicate, and filter signals.

    Returns only signals that:
      1. Are not duplicates within the dedup window
      2. Score above config['throttle']['signal_score_threshold']
    """
    threshold = config.get("throttle", {}).get("signal_score_threshold", 0.4)
    window_hours = config.get("throttle", {}).get("dedup_window_hours", 6)
    max_per_project = config.get("throttle", {}).get("max_triggers_per_project_per_day", 4)

    # Track per-project counts for rate limiting
    project_counts: dict[str, int] = {}
    passed: list[dict[str, Any]] = []

    for sig in signals:
        project = sig.get("project", "unknown")
        source = sig.get("source", "unknown")

        # Dedup check
        if is_duplicate(project, source, cache, window_hours):
            logger.debug("Skipping duplicate: %s / %s", project, source)
            continue

        # Score
        sig["score"] = score_signal(sig, config)
        if sig["score"] < threshold:
            logger.debug("Below threshold (%.3f < %.3f): %s", sig["score"], threshold, sig.get("title", ""))
            continue

        # Rate limit per project
        count = project_counts.get(project, 0)
        if count >= max_per_project:
            logger.debug("Rate limit reached for project %s (%d/%d)", project, count, max_per_project)
            continue

        # Accept
        mark_seen(project, source, cache, window_hours)
        project_counts[project] = count + 1
        passed.append(sig)
        logger.info("Signal accepted (%.3f): [%s] %s", sig["score"], project, sig.get("title", "")[:80])

    logger.info("Filtered %d -> %d signals (threshold=%.2f)", len(signals), len(passed), threshold)
    return passed
