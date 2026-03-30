#!/usr/bin/env python3
"""
RSS feed poller for autoresearch.

Reads feed configuration from config.json (not hardcoded).
For each project, polls its RSS feeds, applies keyword filtering,
maintains a hash-based seen cache, and emits signal files.

Output: one JSON signal file per matched entry in
  ~/.claude/autoresearch-triggers/signals/pending/
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [rss_sniffer] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

MODULE_DIR = Path(__file__).resolve().parent
BASE_DIR = Path.home() / ".claude" / "autoresearch-triggers"
SIGNALS_DIR = BASE_DIR / "signals" / "pending"
SEEN_CACHE_PATH = BASE_DIR / "rss_seen.json"
CONFIG_PATH = MODULE_DIR / "config.json"


def load_config() -> dict:
    """Load config.json."""
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def load_seen_cache() -> dict[str, float]:
    """Load hash-based seen cache. Maps entry_hash -> epoch."""
    if not SEEN_CACHE_PATH.exists():
        return {}
    try:
        data = json.loads(SEEN_CACHE_PATH.read_text(encoding="utf-8"))
        return {k: float(v) for k, v in data.items()} if isinstance(data, dict) else {}
    except (json.JSONDecodeError, ValueError):
        logger.warning("Corrupt RSS seen cache, resetting")
        return {}


def save_seen_cache(cache: dict[str, float]) -> None:
    """Save seen cache, pruning entries older than 7 days."""
    SEEN_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    cutoff = time.time() - 7 * 86400
    pruned = {k: v for k, v in cache.items() if v > cutoff}
    SEEN_CACHE_PATH.write_text(json.dumps(pruned), encoding="utf-8")
    logger.debug("Saved seen cache: %d entries (pruned %d)", len(pruned), len(cache) - len(pruned))


def entry_hash(feed_url: str, entry_id: str) -> str:
    """Deterministic hash for a feed entry."""
    raw = f"{feed_url}:{entry_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def parse_published(entry: Any) -> float | None:
    """Extract publication epoch from a feedparser entry."""
    import calendar

    struct = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if struct:
        try:
            return float(calendar.timegm(struct))
        except (ValueError, OverflowError):
            pass
    return None


def matches_keywords(text: str, keywords: list[str] | None) -> bool:
    """
    Check if text matches any keyword. If no keywords configured, always match.
    """
    if not keywords:
        return True  # no filter = accept all
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def emit_signal(
    project: str,
    feed_name: str,
    entry: Any,
    authority: float,
    keywords: list[str] | None,
    published_epoch: float | None,
) -> None:
    """Write a signal JSON file to the pending signals directory."""
    SIGNALS_DIR.mkdir(parents=True, exist_ok=True)

    title = getattr(entry, "title", "Untitled")
    link = getattr(entry, "link", "")
    summary = getattr(entry, "summary", "")[:500]

    signal = {
        "type": "rss",
        "project": project,
        "source": feed_name,
        "title": title,
        "link": link,
        "summary": summary,
        "published_epoch": published_epoch,
        "authority": authority,
        "keywords": keywords or [],
        "entry_count": 1,
        "emitted_at": datetime.now(timezone.utc).isoformat(),
    }

    filename = f"rss_{project}_{int(time.time()*1000)}.json"
    filepath = SIGNALS_DIR / filename
    filepath.write_text(json.dumps(signal, indent=2), encoding="utf-8")
    logger.info("Signal emitted: [%s] %s -> %s", project, title[:60], filepath.name)


def poll_feed(
    project: str,
    feed_cfg: dict,
    seen_cache: dict[str, float],
    universal_keywords: list[str],
) -> int:
    """
    Poll a single RSS feed. Returns count of new signals emitted.
    """
    import feedparser
    import httpx

    url = feed_cfg["url"]
    name = feed_cfg.get("name", url)
    authority = feed_cfg.get("authority", 0.5)
    keywords = feed_cfg.get("keywords")

    logger.info("Polling [%s] %s", project, name)

    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            resp = client.get(url, headers={"User-Agent": "AutoResearch/2.0 (nightcrawler)"})
            resp.raise_for_status()
            raw_feed = resp.text
    except httpx.HTTPError as exc:
        logger.warning("HTTP error polling %s: %s", name, exc)
        return 0
    except Exception as exc:
        logger.warning("Error polling %s: %s", name, exc)
        return 0

    feed = feedparser.parse(raw_feed)
    if feed.bozo and not feed.entries:
        logger.warning("Feed parse error for %s: %s", name, feed.bozo_exception)
        return 0

    new_count = 0
    for entry in feed.entries[:20]:  # cap at 20 entries per feed
        eid = getattr(entry, "id", None) or getattr(entry, "link", "") or getattr(entry, "title", "")
        h = entry_hash(url, eid)

        if h in seen_cache:
            continue

        title = getattr(entry, "title", "")
        summary = getattr(entry, "summary", "")
        combined_text = f"{title} {summary}"

        # Keyword check (feed-specific keywords OR universal)
        if keywords:
            if not matches_keywords(combined_text, keywords):
                seen_cache[h] = time.time()
                continue
        # If no feed-specific keywords, accept all from this feed

        published_epoch = parse_published(entry)
        seen_cache[h] = time.time()
        emit_signal(project, name, entry, authority, keywords, published_epoch)
        new_count += 1

    logger.info("  %s: %d new signals from %d entries", name, new_count, len(feed.entries))
    return new_count


def main() -> None:
    logger.info("=== RSS Sniffer starting ===")
    config = load_config()
    projects = config.get("projects", {})
    universal_keywords = config.get("universal_keywords", [])
    seen_cache = load_seen_cache()

    total_signals = 0

    for project_name, project_cfg in projects.items():
        feeds = project_cfg.get("rss_feeds", [])
        if not feeds:
            continue

        for feed_cfg in feeds:
            count = poll_feed(project_name, feed_cfg, seen_cache, universal_keywords)
            total_signals += count

    save_seen_cache(seen_cache)
    logger.info("=== RSS Sniffer complete: %d new signals ===", total_signals)


if __name__ == "__main__":
    main()
