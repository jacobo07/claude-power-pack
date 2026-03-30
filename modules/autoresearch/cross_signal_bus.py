#!/usr/bin/env python3
"""
Cross-signal bus for autoresearch.

Reads pending signal files emitted by rss_sniffer and youtube_firehose,
runs them through signal_scorer.filter_signals for scoring + dedup,
detects cross-project relevance using config cross_project_keywords,
emits cross-signal files, and generates a batch digest.

Output:
  - Cross-signal files in ~/.claude/autoresearch-triggers/signals/cross/
  - Batch digest at ~/.claude/autoresearch-triggers/latest_digest.md
  - Moves processed signals to signals/processed/
"""

from __future__ import annotations

import json
import logging
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [cross_signal_bus] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Add module dir to path for local imports
MODULE_DIR = Path(__file__).resolve().parent

import sys
sys.path.insert(0, str(MODULE_DIR))

from signal_scorer import load_dedup_cache, save_dedup_cache, filter_signals

BASE_DIR = Path.home() / ".claude" / "autoresearch-triggers"
PENDING_DIR = BASE_DIR / "signals" / "pending"
PROCESSED_DIR = BASE_DIR / "signals" / "processed"
CROSS_DIR = BASE_DIR / "signals" / "cross"
DEDUP_CACHE_PATH = BASE_DIR / "dedup_cache.json"
DIGEST_PATH = BASE_DIR / "latest_digest.md"
CONFIG_PATH = MODULE_DIR / "config.json"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def load_pending_signals() -> list[dict[str, Any]]:
    """Load all pending signal JSON files."""
    if not PENDING_DIR.exists():
        return []

    signals: list[dict[str, Any]] = []
    for fp in sorted(PENDING_DIR.glob("*.json")):
        try:
            sig = json.loads(fp.read_text(encoding="utf-8"))
            sig["_source_file"] = str(fp)
            signals.append(sig)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Skipping corrupt signal file %s: %s", fp.name, exc)
    logger.info("Loaded %d pending signals", len(signals))
    return signals


def find_cross_project_matches(
    signal: dict[str, Any],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Check if a signal is relevant to other projects via cross_project_keywords.
    Returns list of cross-signal dicts.
    """
    source_project = signal.get("project", "")
    projects = config.get("projects", {})
    source_cfg = projects.get(source_project, {})
    cross_kw_map = source_cfg.get("cross_project_keywords", {})

    text = f"{signal.get('title', '')} {signal.get('summary', '')}".lower()
    cross_signals: list[dict[str, Any]] = []

    for target_project, keywords in cross_kw_map.items():
        matched_kws = [kw for kw in keywords if kw.lower() in text]
        if matched_kws:
            cross_signal = {
                "type": "cross_signal",
                "source_project": source_project,
                "target_project": target_project,
                "source_signal_type": signal.get("type", "unknown"),
                "title": signal.get("title", ""),
                "link": signal.get("link", ""),
                "matched_keywords": matched_kws,
                "original_score": signal.get("score", 0),
                "relevance_note": (
                    f"Signal from {source_project} matched {len(matched_kws)} "
                    f"cross-project keywords for {target_project}"
                ),
                "emitted_at": datetime.now(timezone.utc).isoformat(),
            }
            cross_signals.append(cross_signal)
            logger.info(
                "Cross-signal: %s -> %s (%d keywords: %s)",
                source_project,
                target_project,
                len(matched_kws),
                ", ".join(matched_kws[:3]),
            )

    return cross_signals


def emit_cross_signal(cross_sig: dict[str, Any]) -> Path:
    """Write a cross-signal JSON file."""
    CROSS_DIR.mkdir(parents=True, exist_ok=True)
    src = cross_sig.get("source_project", "unknown")
    tgt = cross_sig.get("target_project", "unknown")
    filename = f"cross_{src}_to_{tgt}_{int(time.time()*1000)}.json"
    filepath = CROSS_DIR / filename
    filepath.write_text(json.dumps(cross_sig, indent=2), encoding="utf-8")
    return filepath


def move_to_processed(signal: dict[str, Any]) -> None:
    """Move a processed signal file from pending to processed."""
    source_file = signal.get("_source_file")
    if not source_file:
        return
    src_path = Path(source_file)
    if not src_path.exists():
        return
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    dest = PROCESSED_DIR / src_path.name
    shutil.move(str(src_path), str(dest))
    logger.debug("Moved to processed: %s", src_path.name)


def generate_digest(
    accepted_signals: list[dict[str, Any]],
    cross_signals: list[dict[str, Any]],
    total_pending: int,
) -> str:
    """Generate a Markdown digest of this run's findings."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# Autoresearch Digest - {now}",
        "",
        f"**Pending signals processed:** {total_pending}",
        f"**Signals accepted (above threshold):** {len(accepted_signals)}",
        f"**Cross-project signals found:** {len(cross_signals)}",
        "",
    ]

    if accepted_signals:
        lines.append("## Accepted Signals")
        lines.append("")
        # Group by project
        by_project: dict[str, list[dict]] = {}
        for sig in accepted_signals:
            proj = sig.get("project", "unknown")
            by_project.setdefault(proj, []).append(sig)

        for proj in sorted(by_project.keys()):
            sigs = by_project[proj]
            lines.append(f"### {proj} ({len(sigs)} signals)")
            lines.append("")
            for sig in sigs:
                score = sig.get("score", 0)
                title = sig.get("title", "Untitled")[:80]
                src = sig.get("source", "unknown")
                link = sig.get("link", "")
                sig_type = sig.get("type", "unknown")
                lines.append(f"- **[{score:.2f}]** [{title}]({link}) ({sig_type} via {src})")
            lines.append("")

    if cross_signals:
        lines.append("## Cross-Project Signals")
        lines.append("")
        for cs in cross_signals:
            src_proj = cs.get("source_project", "?")
            tgt_proj = cs.get("target_project", "?")
            title = cs.get("title", "Untitled")[:60]
            kws = ", ".join(cs.get("matched_keywords", [])[:5])
            lines.append(f"- **{src_proj} -> {tgt_proj}**: {title} (keywords: {kws})")
        lines.append("")

    if not accepted_signals and not cross_signals:
        lines.append("*No notable signals this run.*")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    logger.info("=== Cross-Signal Bus starting ===")
    config = load_config()

    # Load pending signals
    all_signals = load_pending_signals()
    if not all_signals:
        logger.info("No pending signals to process")
        # Write empty digest
        DIGEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        DIGEST_PATH.write_text(
            generate_digest([], [], 0),
            encoding="utf-8",
        )
        logger.info("=== Cross-Signal Bus complete: 0 signals ===")
        return

    total_pending = len(all_signals)

    # Score and filter through signal_scorer
    dedup_cache = load_dedup_cache(DEDUP_CACHE_PATH)
    accepted = filter_signals(all_signals, config, dedup_cache)
    save_dedup_cache(DEDUP_CACHE_PATH, dedup_cache)

    # Find cross-project relevance for accepted signals
    all_cross_signals: list[dict[str, Any]] = []
    for sig in accepted:
        cross_matches = find_cross_project_matches(sig, config)
        for cs in cross_matches:
            emit_cross_signal(cs)
            all_cross_signals.append(cs)

    # Generate digest
    digest_text = generate_digest(accepted, all_cross_signals, total_pending)
    DIGEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    DIGEST_PATH.write_text(digest_text, encoding="utf-8")
    logger.info("Digest written to %s", DIGEST_PATH)

    # Move all pending signals to processed (not just accepted ones)
    for sig in all_signals:
        move_to_processed(sig)

    logger.info(
        "=== Cross-Signal Bus complete: %d accepted, %d cross-signals from %d pending ===",
        len(accepted),
        len(all_cross_signals),
        total_pending,
    )


if __name__ == "__main__":
    main()
