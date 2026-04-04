#!/usr/bin/env python3
"""
Video Analyzer — Bridge between YouTube URLs and frame/transcript extraction.

Wraps yt-research tool when available, degrades gracefully without it.
Connects: YouTube URL → download → frames → transcript → vision scoring → cache.

Part of Claude Power Pack — Video-Enhanced Reverse Engineering.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

MODULE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = MODULE_DIR / "config.json"
DEFAULT_CACHE_DIR = Path.home() / ".claude" / "autoresearch-triggers" / "signals" / "video_cache"


@dataclass
class AnalysisResult:
    video_id: str
    title: str = ""
    duration: float = 0.0
    transcript: str = ""
    transcript_engine: str = ""
    frames: list[dict[str, Any]] = field(default_factory=list)
    vision_score: dict[str, Any] = field(default_factory=dict)
    cache_dir: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _load_config() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _get_cache_dir() -> Path:
    config = _load_config()
    cache_str = config.get("video_analysis", {}).get("cache_dir", "")
    if cache_str:
        return Path(os.path.expanduser(cache_str))
    return DEFAULT_CACHE_DIR


def extract_video_id(url: str) -> str | None:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r"(?:v=|\/v\/|youtu\.be\/|embed\/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def _has_yt_research() -> bool:
    """Check if yt-research CLI is available."""
    return shutil.which("yt-research") is not None


def _has_yt_dlp() -> bool:
    """Check if yt-dlp is available."""
    return shutil.which("yt-dlp") is not None


def _has_ffmpeg() -> bool:
    """Check if ffmpeg is available."""
    return shutil.which("ffmpeg") is not None


# ── Transcript Extraction ───────────────────────────────────────────

def _get_youtube_transcript(video_id: str) -> tuple[str, str]:
    """Extract transcript from YouTube captions (no download needed)."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Prefer manual transcripts
        for transcript in transcript_list:
            if not transcript.is_generated:
                entries = transcript.fetch()
                text = "\n".join(
                    f"[{int(e['start']//60)}:{int(e['start']%60):02d}] {e['text']}"
                    for e in entries
                )
                return text, "youtube-captions-manual"

        # Fallback to auto-generated
        for transcript in transcript_list:
            entries = transcript.fetch()
            text = "\n".join(
                f"[{int(e['start']//60)}:{int(e['start']%60):02d}] {e['text']}"
                for e in entries
            )
            return text, "youtube-captions-auto"

    except Exception as e:
        logger.debug(f"YouTube captions unavailable: {e}")

    return "", ""


def _get_whisper_transcript(video_path: Path) -> tuple[str, str]:
    """Transcribe audio using whisper_bridge."""
    try:
        from whisper_bridge import transcribe
        # Extract audio from video
        audio_path = video_path.with_suffix(".mp3")
        if not audio_path.exists():
            subprocess.run(
                ["ffmpeg", "-i", str(video_path), "-vn", "-acodec", "libmp3lame",
                 "-q:a", "4", str(audio_path), "-y"],
                capture_output=True, timeout=120,
            )

        if audio_path.exists():
            result = transcribe(audio_path)
            if result:
                return result.to_timestamped_text(), result.engine

    except Exception as e:
        logger.debug(f"Whisper transcription failed: {e}")

    return "", ""


# ── Frame Extraction ────────────────────────────────────────────────

def _extract_frames_ffmpeg(video_path: Path, output_dir: Path, max_frames: int = 8) -> list[dict]:
    """Extract frames using ffmpeg at regular intervals."""
    if not _has_ffmpeg():
        logger.warning("ffmpeg not available — skipping frame extraction")
        return []

    output_dir.mkdir(parents=True, exist_ok=True)

    # Get duration
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(video_path)],
            capture_output=True, text=True, timeout=30,
        )
        duration = float(result.stdout.strip())
    except Exception:
        duration = 300  # assume 5 min

    # Calculate interval
    interval = max(1, int(duration / max_frames))

    # Extract frames
    subprocess.run(
        ["ffmpeg", "-i", str(video_path), "-vf", f"fps=1/{interval},scale=1280:-1",
         "-q:v", "2", str(output_dir / "frame_%04d.png"), "-y"],
        capture_output=True, timeout=180,
    )

    frames = []
    for f in sorted(output_dir.glob("frame_*.png")):
        idx = int(f.stem.split("_")[1]) - 1
        frames.append({
            "path": str(f),
            "timestamp": idx * interval,
            "scene_type": "interval",
        })

    return frames


# ── Main Analysis Pipeline ──────────────────────────────────────────

def analyze_video(url: str, project_key: str = "default") -> AnalysisResult:
    """Full video analysis pipeline."""
    video_id = extract_video_id(url)
    if not video_id:
        return AnalysisResult(video_id="unknown", error=f"Could not extract video ID from: {url}")

    config = _load_config()
    va_config = config.get("video_analysis", {})
    max_frames = va_config.get("max_frames_per_video", 8)
    max_duration = va_config.get("max_video_duration_minutes", 30)
    download_timeout = va_config.get("download_timeout_seconds", 120)

    cache_dir = _get_cache_dir() / video_id
    cache_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = cache_dir / "frames"

    result = AnalysisResult(video_id=video_id, cache_dir=str(cache_dir))

    # Check cache
    manifest_path = cache_dir / "result.json"
    if manifest_path.exists():
        try:
            cached = json.loads(manifest_path.read_text(encoding="utf-8"))
            if cached.get("video_id") == video_id and not cached.get("error"):
                logger.info(f"Using cached analysis for {video_id}")
                return AnalysisResult(**cached)
        except Exception:
            pass

    # Step 1: Try yt-research CLI (best quality — histogram scene detection + NotebookLM)
    if _has_yt_research():
        logger.info(f"Using yt-research for {video_id}")
        try:
            subprocess.run(
                ["yt-research", "analyze", url],
                capture_output=True, timeout=300,
            )
            # Read yt-research cache
            yr_cache = Path.home() / ".yt-research" / "cache" / video_id
            if yr_cache.exists():
                meta_path = yr_cache / "metadata.json"
                if meta_path.exists():
                    meta = json.loads(meta_path.read_text(encoding="utf-8"))
                    result.title = meta.get("title", "")
                    result.duration = meta.get("duration", 0.0)

                transcript_path = yr_cache / "transcript.txt"
                if transcript_path.exists():
                    result.transcript = transcript_path.read_text(encoding="utf-8")
                    result.transcript_engine = "yt-research"

                yr_frames = yr_cache / "frames"
                if yr_frames.exists():
                    for f in sorted(yr_frames.glob("*.png")):
                        result.frames.append({"path": str(f), "timestamp": 0, "scene_type": "histogram"})
                    # Symlink for vision scorer
                    if not frames_dir.exists():
                        frames_dir.symlink_to(yr_frames)

        except Exception as e:
            logger.warning(f"yt-research failed: {e}")

    # Step 2: Fallback — manual download + extraction
    if not result.frames:
        video_path = cache_dir / f"{video_id}.mp4"

        # Download if needed
        if not video_path.exists() and _has_yt_dlp():
            logger.info(f"Downloading {video_id} via yt-dlp")
            try:
                subprocess.run(
                    ["yt-dlp", "-f", "worst[ext=mp4]", "--max-filesize", "200M",
                     "-o", str(video_path), url],
                    capture_output=True, timeout=download_timeout,
                )
            except Exception as e:
                logger.warning(f"Download failed: {e}")

        # Extract frames
        if video_path.exists():
            result.frames = _extract_frames_ffmpeg(video_path, frames_dir, max_frames)

    # Step 3: Transcript (if not already from yt-research)
    if not result.transcript:
        text, engine = _get_youtube_transcript(video_id)
        if text:
            result.transcript = text
            result.transcript_engine = engine
        elif any(f.get("path") for f in result.frames):
            # Try whisper on downloaded video
            video_path = cache_dir / f"{video_id}.mp4"
            if video_path.exists():
                text, engine = _get_whisper_transcript(video_path)
                if text:
                    result.transcript = text
                    result.transcript_engine = engine

    # Step 4: Vision scoring (if frames exist)
    if result.frames and frames_dir.exists():
        try:
            from vision_scorer import score_frames
            vs = score_frames(frames_dir, max_frames)
            result.vision_score = vs.to_dict()
        except Exception as e:
            logger.debug(f"Vision scoring skipped: {e}")

    # Save transcript to file
    if result.transcript:
        (cache_dir / "transcript.txt").write_text(result.transcript, encoding="utf-8")

    # Save result manifest
    manifest_path.write_text(
        json.dumps(result.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    logger.info(f"Analysis complete: {video_id} | frames={len(result.frames)} | transcript={len(result.transcript)} chars | engine={result.transcript_engine}")
    return result


def analyze_video_async(url: str, project_key: str = "default") -> None:
    """Fire-and-forget video analysis (called from youtube_firehose)."""
    try:
        # Run in subprocess to avoid blocking the firehose
        subprocess.Popen(
            [sys.executable, __file__, "--url", url, "--project", project_key],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )
    except Exception as e:
        logger.debug(f"Async analysis launch failed: {e}")


# ── CLI ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Video Analyzer — YouTube RE Bridge")
    parser.add_argument("--url", required=True, help="YouTube URL or video ID")
    parser.add_argument("--project", default="default", help="Project key for signal routing")
    parser.add_argument("--output", help="Output JSON path (default: stdout)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    result = analyze_video(args.url, args.project)
    output = json.dumps(result.to_dict(), indent=2, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Analysis saved to {args.output}")
    else:
        print(output)
