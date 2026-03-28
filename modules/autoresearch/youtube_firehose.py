#!/usr/bin/env python3
"""
YouTube channel poller for autoresearch.

Reads channel configuration from config.json.
Uses YouTube RSS feeds (no API key needed) to detect new videos.
Applies keyword filtering, maintains a hash-based seen cache,
and emits signal files identical in format to rss_sniffer.

Output: signal JSON files in
  ~/.claude/autoresearch-triggers/signals/pending/
"""

from __future__ import annotations

import calendar
import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [youtube_firehose] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

MODULE_DIR = Path(__file__).resolve().parent
BASE_DIR = Path.home() / ".claude" / "autoresearch-triggers"
SIGNALS_DIR = BASE_DIR / "signals" / "pending"
SEEN_CACHE_PATH = BASE_DIR / "youtube_seen.json"
CONFIG_PATH = MODULE_DIR / "config.json"

# YouTube RSS feed URL template (no API key required)
YT_RSS_TEMPLATE = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def load_seen_cache() -> dict[str, float]:
    if not SEEN_CACHE_PATH.exists():
        return {}
    try:
        data = json.loads(SEEN_CACHE_PATH.read_text(encoding="utf-8"))
        return {k: float(v) for k, v in data.items()} if isinstance(data, dict) else {}
    except (json.JSONDecodeError, ValueError):
        logger.warning("Corrupt YouTube seen cache, resetting")
        return {}


def save_seen_cache(cache: dict[str, float]) -> None:
    SEEN_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    cutoff = time.time() - 14 * 86400  # 14-day retention
    pruned = {k: v for k, v in cache.items() if v > cutoff}
    SEEN_CACHE_PATH.write_text(json.dumps(pruned), encoding="utf-8")
    logger.debug("Saved YouTube seen cache: %d entries", len(pruned))


def video_hash(channel_id: str, video_id: str) -> str:
    raw = f"yt:{channel_id}:{video_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def parse_published(entry: Any) -> float | None:
    struct = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if struct:
        try:
            return float(calendar.timegm(struct))
        except (ValueError, OverflowError):
            pass
    return None


def matches_keywords(text: str, keywords: list[str] | None) -> bool:
    if not keywords:
        return True
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def emit_signal(
    project: str,
    channel_name: str,
    entry: Any,
    keywords: list[str] | None,
    published_epoch: float | None,
) -> None:
    SIGNALS_DIR.mkdir(parents=True, exist_ok=True)

    title = getattr(entry, "title", "Untitled")
    link = getattr(entry, "link", "")
    summary = getattr(entry, "summary", "")[:500]

    # Extract video ID from link
    video_id = ""
    if "watch?v=" in link:
        video_id = link.split("watch?v=")[-1].split("&")[0]

    signal = {
        "type": "youtube",
        "project": project,
        "source": channel_name,
        "title": title,
        "link": link,
        "video_id": video_id,
        "summary": summary,
        "published_epoch": published_epoch,
        "authority": 0.6,  # YouTube default authority
        "keywords": keywords or [],
        "entry_count": 1,
        "emitted_at": datetime.now(timezone.utc).isoformat(),
    }

    filename = f"yt_{project}_{int(time.time()*1000)}.json"
    filepath = SIGNALS_DIR / filename
    filepath.write_text(json.dumps(signal, indent=2), encoding="utf-8")
    logger.info("Signal emitted: [%s] %s -> %s", project, title[:60], filepath.name)


def poll_channel(
    project: str,
    channel_cfg: dict,
    seen_cache: dict[str, float],
) -> int:
    """Poll a single YouTube channel via RSS. Returns new signal count."""
    import feedparser
    import httpx

    channel_id = channel_cfg["id"]
    channel_name = channel_cfg.get("name", channel_id)
    keywords = channel_cfg.get("keywords")

    feed_url = YT_RSS_TEMPLATE.format(channel_id=channel_id)
    logger.info("Polling [%s] YouTube: %s", project, channel_name)

    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            resp = client.get(feed_url, headers={"User-Agent": "AutoResearch/2.0 (nightcrawler)"})
            resp.raise_for_status()
            raw_feed = resp.text
    except httpx.HTTPError as exc:
        logger.warning("HTTP error polling YouTube %s: %s", channel_name, exc)
        return 0
    except Exception as exc:
        logger.warning("Error polling YouTube %s: %s", channel_name, exc)
        return 0

    feed = feedparser.parse(raw_feed)
    if feed.bozo and not feed.entries:
        logger.warning("Feed parse error for YouTube %s: %s", channel_name, feed.bozo_exception)
        return 0

    new_count = 0
    for entry in feed.entries[:15]:  # cap at 15 videos per channel
        eid = getattr(entry, "yt_videoid", None) or getattr(entry, "id", "") or getattr(entry, "link", "")
        h = video_hash(channel_id, eid)

        if h in seen_cache:
            continue

        title = getattr(entry, "title", "")
        summary = getattr(entry, "summary", "")
        combined = f"{title} {summary}"

        if not matches_keywords(combined, keywords):
            seen_cache[h] = time.time()
            continue

        published_epoch = parse_published(entry)
        seen_cache[h] = time.time()
        emit_signal(project, channel_name, entry, keywords, published_epoch)
        new_count += 1

    logger.info("  %s: %d new signals from %d videos", channel_name, new_count, len(feed.entries))
    return new_count


def main() -> None:
    logger.info("=== YouTube Firehose starting ===")
    config = load_config()
    projects = config.get("projects", {})
    seen_cache = load_seen_cache()

    total_signals = 0

    for project_name, project_cfg in projects.items():
        channels = project_cfg.get("youtube_channels", [])
        if not channels:
            continue

        for ch_cfg in channels:
            count = poll_channel(project_name, ch_cfg, seen_cache)
            total_signals += count

    save_seen_cache(seen_cache)
    logger.info("=== YouTube Firehose complete: %d new signals ===", total_signals)


if __name__ == "__main__":
    main()
