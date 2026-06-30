#!/usr/bin/env python3
"""enricher.py -- AutoResearch credential-free enrichment (Block C, 2026-06-30).

Agent-Reach's CLI is agent-facing (setup/doctor/transcribe/format); it is NOT a
per-channel fetch API. Its headless-usable credential-free primitives are:
  - Jina Reader: GET https://r.jina.ai/<url> -> clean article text (verified live
    from the KobiiClaw VPS, no key, no cookie).
  - yt-dlp: YouTube auto-subtitles -> transcript text (no key).

This module is an ADDITIVE post-scoring stage: discovery (rss_sniffer /
youtube_firehose) is unchanged. It enriches the TOP accepted signals with full
text so the digest carries substance, not just RSS titles.

Footprint discipline (VPS ~80% disk): bounded by enrichment.max_signals,
per-call timeouts, char caps, and a tempdir always cleaned. Every call is
fail-open -- a network/parse error leaves the signal untouched and never raises
into the pipeline.
"""
from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

JINA_PREFIX = "https://r.jina.ai/"


def _default_cfg() -> dict:
    return {
        "enabled": True,
        "max_signals": 8,
        "jina_enabled": True,
        "jina_max_chars": 1200,
        "jina_timeout_s": 25,
        "ytdlp_enabled": True,
        "ytdlp_path": "~/.agent-reach-venv/bin/yt-dlp",
        "ytdlp_max_chars": 1500,
        "ytdlp_timeout_s": 60,
        "ytdlp_sub_lang": "en",
    }


def _cfg(config: dict) -> dict:
    c = _default_cfg()
    over = config.get("enrichment", {}) if isinstance(config, dict) else {}
    if isinstance(over, dict):
        c.update(over)
    return c


def jina_fetch(url: str, timeout_s: int = 25, max_chars: int = 1200) -> str | None:
    """Fetch clean article text for a URL via Jina Reader. Fail-open -> None."""
    if not url:
        return None
    try:
        import httpx
        with httpx.Client(timeout=timeout_s, follow_redirects=True) as client:
            resp = client.get(
                JINA_PREFIX + url,
                headers={"User-Agent": "AutoResearch/2.0 (enricher)"},
            )
            resp.raise_for_status()
            text = resp.text.strip()
    except Exception as exc:  # fail-open on any network/parse error
        logger.warning("Jina fetch failed for %s: %s", url[:80], exc)
        return None
    if not text:
        return None
    return text[:max_chars]


_VTT_TAG = re.compile(r"<[^>]+>")


def _parse_vtt(vtt_text: str) -> str:
    """Strip WEBVTT headers/timestamps/cue tags -> deduped plain transcript."""
    out: list[str] = []
    seen_last = ""
    for line in vtt_text.splitlines():
        line = line.strip()
        if not line or line == "WEBVTT" or "-->" in line:
            continue
        if line.isdigit():
            continue
        if line.startswith(("Kind:", "Language:", "NOTE")):
            continue
        clean = _VTT_TAG.sub("", line).strip()
        if clean and clean != seen_last:
            out.append(clean)
            seen_last = clean
    return " ".join(out)


def ytdlp_transcript(video_url: str, ytdlp_path: str, timeout_s: int = 60,
                     max_chars: int = 1500, sub_lang: str = "en") -> str | None:
    """Fetch a YouTube auto-sub transcript via yt-dlp. Fail-open -> None."""
    if not video_url or not ytdlp_path:
        return None
    exe = os.path.expanduser(ytdlp_path)
    if not os.path.exists(exe):
        return None
    tmp = tempfile.mkdtemp(prefix="ar_yt_")
    try:
        cmd = [exe, "--skip-download", "--write-auto-sub",
               "--sub-lang", sub_lang, "--sub-format", "vtt",
               "--no-warnings", "-o", os.path.join(tmp, "%(id)s.%(ext)s"),
               video_url]
        try:
            subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout_s, check=False)
        except subprocess.TimeoutExpired:
            logger.warning("yt-dlp timed out for %s", video_url[:80])
            return None
        vtts = list(Path(tmp).glob("*.vtt"))
        if not vtts:
            return None
        raw = vtts[0].read_text(encoding="utf-8", errors="replace")
        text = _parse_vtt(raw)
        return text[:max_chars] if text else None
    except Exception as exc:  # fail-open
        logger.warning("yt-dlp transcript failed for %s: %s", video_url[:80], exc)
        return None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def enrich_signals(accepted: list[dict[str, Any]], config: dict) -> int:
    """Attach `enriched` text to the top accepted signals. Returns count enriched.

    Top-N by score (footprint cap). YouTube -> yt-dlp transcript; web/RSS ->
    Jina full text. Each call is fail-open; a failure leaves the signal
    unchanged and never raises."""
    c = _cfg(config)
    if not c.get("enabled", True) or not accepted:
        return 0
    ranked = sorted(accepted, key=lambda s: s.get("score", 0), reverse=True)
    budget = int(c.get("max_signals", 8))
    enriched = 0
    for sig in ranked:
        if enriched >= budget:
            break
        link = sig.get("link") or ""
        stype = sig.get("type", "")
        text = None
        src = ""
        if stype == "youtube" and c.get("ytdlp_enabled", True):
            text = ytdlp_transcript(
                link, c.get("ytdlp_path", ""),
                int(c.get("ytdlp_timeout_s", 60)),
                int(c.get("ytdlp_max_chars", 1500)),
                c.get("ytdlp_sub_lang", "en"))
            src = "yt-dlp"
        elif c.get("jina_enabled", True) and link:
            text = jina_fetch(
                link, int(c.get("jina_timeout_s", 25)),
                int(c.get("jina_max_chars", 1200)))
            src = "jina"
        else:
            continue
        if text:
            sig["enriched"] = text
            sig["enriched_via"] = src
            enriched += 1
    logger.info("Enriched %d/%d signals (budget %d)",
                enriched, len(accepted), budget)
    return enriched
