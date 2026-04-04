#!/usr/bin/env python3
"""
Whisper Bridge — Audio transcription with graceful degradation.

Attempts transcription in order:
  1. faster-whisper (local, fast, free)
  2. openai-whisper (local, slower)
  3. None (caller falls back to youtube-transcript-api)

Part of Claude Power Pack — Video-Enhanced Reverse Engineering.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

MODULE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = MODULE_DIR / "config.json"


@dataclass
class Segment:
    start: float
    end: float
    text: str
    confidence: float = 0.0


@dataclass
class TranscriptResult:
    text: str
    segments: list[Segment] = field(default_factory=list)
    language: str = "en"
    duration: float = 0.0
    engine: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_timestamped_text(self) -> str:
        lines = []
        for seg in self.segments:
            mins, secs = divmod(int(seg.start), 60)
            lines.append(f"[{mins}:{secs:02d}] {seg.text.strip()}")
        return "\n".join(lines)


def _load_whisper_model() -> str:
    try:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return config.get("video_analysis", {}).get("whisper_model", "base")
    except Exception:
        return "base"


def transcribe_faster_whisper(audio_path: str | Path) -> TranscriptResult | None:
    """Transcribe using faster-whisper (CTranslate2 backend)."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None

    model_size = _load_whisper_model()
    logger.info(f"Transcribing with faster-whisper ({model_size}): {audio_path}")

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments_iter, info = model.transcribe(str(audio_path), beam_size=5)

    segments = []
    full_text_parts = []
    for seg in segments_iter:
        segments.append(Segment(
            start=seg.start,
            end=seg.end,
            text=seg.text,
            confidence=seg.avg_logprob,
        ))
        full_text_parts.append(seg.text.strip())

    return TranscriptResult(
        text=" ".join(full_text_parts),
        segments=segments,
        language=info.language,
        duration=info.duration,
        engine="faster-whisper",
    )


def transcribe_openai_whisper(audio_path: str | Path) -> TranscriptResult | None:
    """Transcribe using OpenAI's whisper (PyTorch backend)."""
    try:
        import whisper
    except ImportError:
        return None

    model_size = _load_whisper_model()
    logger.info(f"Transcribing with openai-whisper ({model_size}): {audio_path}")

    model = whisper.load_model(model_size)
    result = model.transcribe(str(audio_path))

    segments = []
    for seg in result.get("segments", []):
        segments.append(Segment(
            start=seg["start"],
            end=seg["end"],
            text=seg["text"],
            confidence=seg.get("avg_logprob", 0.0),
        ))

    return TranscriptResult(
        text=result.get("text", ""),
        segments=segments,
        language=result.get("language", "en"),
        duration=segments[-1].end if segments else 0.0,
        engine="openai-whisper",
    )


def transcribe(audio_path: str | Path) -> TranscriptResult | None:
    """Transcribe audio with graceful degradation across engines."""
    audio_path = Path(audio_path)
    if not audio_path.exists():
        logger.error(f"Audio file not found: {audio_path}")
        return None

    # Try faster-whisper first (faster, lower memory)
    result = transcribe_faster_whisper(audio_path)
    if result:
        return result

    # Fallback to openai-whisper
    result = transcribe_openai_whisper(audio_path)
    if result:
        return result

    logger.warning("No whisper engine available. Install: pip install faster-whisper")
    return None


# ── CLI ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Whisper Bridge — Audio Transcription")
    parser.add_argument("--audio", required=True, help="Path to audio file")
    parser.add_argument("--output", help="Output JSON path (default: stdout)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    result = transcribe(args.audio)
    if result is None:
        print("No transcription engine available.", file=sys.stderr)
        print("Install: pip install faster-whisper", file=sys.stderr)
        sys.exit(1)

    output = json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Transcript saved to {args.output}")
    else:
        print(output)
