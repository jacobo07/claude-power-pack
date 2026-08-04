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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

JINA_PREFIX = "https://r.jina.ai/"

_PP_ROOT = Path(__file__).resolve().parents[2]
# The authored-corpus store: full external text, the one input capability
# mining needs and the estate did not keep. Read by
# `modules/capability_runtime/corpus_adapter.py::evidence_from_corpus`.
CORPUS_DIRNAME = Path("vault") / "corpus"
CORPUS_MAX_CHARS = 200_000


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
        # Authored-corpus persistence (UCEIMR G5). On by default: the text is
        # already fetched and already parsed, so the marginal cost is one write
        # of text that was previously thrown away. Bounded by max_signals per
        # run and CORPUS_MAX_CHARS per file.
        "corpus_enabled": True,
        "corpus_dir": "",          # "" -> <repo>/vault/corpus
    }


def _cfg(config: dict) -> dict:
    c = _default_cfg()
    over = config.get("enrichment", {}) if isinstance(config, dict) else {}
    if isinstance(over, dict):
        c.update(over)
    return c


def _slug(text: str, limit: int = 60) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", (text or "").lower()).strip("_")
    return s[:limit] or "source"


def persist_corpus(text: str, source: str, kind: str, corpus_dir=None,
                   max_chars: int = CORPUS_MAX_CHARS):
    """Write FULL fetched text to the authored-corpus store. Fail-open -> None.

    Both fetchers below hold the complete article/transcript and then return a
    1200-1500 char slice for the digest. The remainder was discarded, so the
    estate persisted no authored external text at all -- measured 2026-08-04,
    the capability miner (`capability_runtime/corpus_adapter.py`) yielded 0
    proposals from 138 units because AKOS keeps ~220-char leads and
    `vault/research/` holds the estate's own notes. Mining cannot bite on text
    nobody wrote down.

    This is additive and does not change what either fetcher returns.
    Footprint-disciplined per this module's contract: capped per file,
    idempotent (an existing file is never rewritten), and never raises.
    """
    if not text or not str(source).strip():
        return None
    try:
        base = Path(corpus_dir) if corpus_dir else _PP_ROOT / CORPUS_DIRNAME
        base.mkdir(parents=True, exist_ok=True)
        path = base / f"{_slug(source)}.txt"
        if path.exists():          # idempotent: never rewrite a fetched source
            return path
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        body = (f"source: {source}\nkind: {kind}\nfetched_at: {stamp}\n\n"
                f"{text[:max_chars]}\n")
        tmp = path.with_suffix(".txt.tmp")
        tmp.write_text(body, encoding="utf-8")
        tmp.replace(path)
        return path
    except Exception as exc:  # noqa: BLE001 -- fail-open ABSOLUTE
        logger.warning("corpus persist failed for %s: %s", str(source)[:80], exc)
        return None


def jina_fetch(url: str, timeout_s: int = 25, max_chars: int = 1200,
               corpus_dir=None) -> str | None:
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
    if corpus_dir is not None:
        persist_corpus(text, url, "jina", corpus_dir)
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
                     max_chars: int = 1500, sub_lang: str = "en",
                     corpus_dir=None) -> str | None:
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
        if not text:
            return None
        # Persist the FULL transcript before the digest slice discards it.
        if corpus_dir is not None:
            persist_corpus(text, video_url, "yt-dlp", corpus_dir)
        return text[:max_chars]
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
    # None disables persistence entirely; a path (or "" -> the default store)
    # keeps the full text the digest slice would otherwise discard.
    corpus = None
    if c.get("corpus_enabled", True):
        corpus = c.get("corpus_dir") or _PP_ROOT / CORPUS_DIRNAME
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
                c.get("ytdlp_sub_lang", "en"), corpus)
            src = "yt-dlp"
        elif c.get("jina_enabled", True) and link:
            text = jina_fetch(
                link, int(c.get("jina_timeout_s", 25)),
                int(c.get("jina_max_chars", 1200)), corpus)
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
