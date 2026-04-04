#!/usr/bin/env python3
"""
Vision Scorer — Score video frames for architectural/RE value.

Analyzes extracted video frames to detect:
  - Architecture diagrams (flowcharts, DAGs, microservice layouts)
  - UI/UX patterns (design systems, component hierarchies)
  - Code walkthroughs (editor screenshots, terminal output)
  - Metrics/benchmarks (charts, dashboards, performance numbers)
  - System demos (live product functionality)

Uses Claude vision API when ANTHROPIC_API_KEY is set.
Falls back to heuristic scoring (file size, dimensions) without API.

Part of Claude Power Pack — Video-Enhanced Reverse Engineering.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

MODULE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = MODULE_DIR / "config.json"

MAX_FRAMES_DEFAULT = 8
VISION_PROMPT = """Analyze this video frame for reverse engineering value. Classify what you see:

1. architecture_diagram: Is there a system architecture diagram, flowchart, DAG, or microservice layout? (true/false)
2. ui_pattern: Is there a UI/UX design, component hierarchy, or design system visible? (true/false)
3. code_walkthrough: Is there code, an editor, terminal output, or IDE visible? (true/false)
4. metrics_visible: Are there charts, dashboards, performance numbers, or benchmarks visible? (true/false)
5. system_demo: Is this a live product demo showing real functionality? (true/false)
6. description: One-sentence description of what's in this frame.
7. confidence: Your confidence in this classification (0.0-1.0).

Respond in JSON only: {"architecture_diagram": bool, "ui_pattern": bool, "code_walkthrough": bool, "metrics_visible": bool, "system_demo": bool, "description": "...", "confidence": 0.0}"""


@dataclass
class FrameScore:
    frame_path: str
    architecture_diagram: bool = False
    ui_pattern: bool = False
    code_walkthrough: bool = False
    metrics_visible: bool = False
    system_demo: bool = False
    description: str = ""
    confidence: float = 0.0


@dataclass
class VisionScore:
    architecture_detected: bool = False
    ui_patterns: bool = False
    metrics_visible: bool = False
    code_walkthrough: bool = False
    system_demo: bool = False
    confidence: float = 0.0
    frame_scores: list[FrameScore] = field(default_factory=list)
    composite_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _load_config() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _get_api_key() -> str | None:
    config = _load_config()
    env_var = config.get("video_analysis", {}).get("vision_api_key_env", "ANTHROPIC_API_KEY")
    return os.environ.get(env_var)


def _encode_image(path: Path) -> str:
    """Base64-encode an image file."""
    return base64.standard_b64encode(path.read_bytes()).decode("utf-8")


def _score_frame_vision(frame_path: Path, api_key: str) -> FrameScore:
    """Score a single frame using Claude vision API."""
    try:
        import anthropic
    except ImportError:
        logger.warning("anthropic SDK not installed. Using heuristic scoring.")
        return _score_frame_heuristic(frame_path)

    client = anthropic.Anthropic(api_key=api_key)
    image_data = _encode_image(frame_path)

    suffix = frame_path.suffix.lower()
    media_type = "image/png" if suffix == ".png" else "image/jpeg"

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
                    {"type": "text", "text": VISION_PROMPT},
                ],
            }],
        )

        text = response.content[0].text.strip()
        # Extract JSON from response (handle markdown code blocks)
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text)

        return FrameScore(
            frame_path=str(frame_path),
            architecture_diagram=data.get("architecture_diagram", False),
            ui_pattern=data.get("ui_pattern", False),
            code_walkthrough=data.get("code_walkthrough", False),
            metrics_visible=data.get("metrics_visible", False),
            system_demo=data.get("system_demo", False),
            description=data.get("description", ""),
            confidence=float(data.get("confidence", 0.5)),
        )
    except Exception as e:
        logger.warning(f"Vision API error for {frame_path}: {e}")
        return _score_frame_heuristic(frame_path)


def _score_frame_heuristic(frame_path: Path) -> FrameScore:
    """Heuristic scoring when vision API is unavailable."""
    size_kb = frame_path.stat().st_size / 1024
    # Larger frames tend to have more visual content
    confidence = min(0.3, size_kb / 500)
    return FrameScore(
        frame_path=str(frame_path),
        description="Heuristic score (no vision API)",
        confidence=confidence,
    )


def score_frames(frames_dir: str | Path, max_frames: int | None = None) -> VisionScore:
    """Score all frames in a directory for RE value."""
    frames_dir = Path(frames_dir)
    if not frames_dir.exists():
        logger.error(f"Frames directory not found: {frames_dir}")
        return VisionScore()

    config = _load_config()
    max_frames = max_frames or config.get("video_analysis", {}).get("max_frames_per_video", MAX_FRAMES_DEFAULT)

    # Collect image files
    image_files = sorted([
        f for f in frames_dir.iterdir()
        if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
    ])

    if not image_files:
        logger.warning(f"No image files found in {frames_dir}")
        return VisionScore()

    # Limit to max_frames (evenly spaced)
    if len(image_files) > max_frames:
        step = len(image_files) / max_frames
        image_files = [image_files[int(i * step)] for i in range(max_frames)]

    # Score each frame
    api_key = _get_api_key()
    frame_scores = []

    for frame_path in image_files:
        if api_key:
            score = _score_frame_vision(frame_path, api_key)
        else:
            score = _score_frame_heuristic(frame_path)
        frame_scores.append(score)

    # Aggregate scores
    result = VisionScore(
        architecture_detected=any(fs.architecture_diagram for fs in frame_scores),
        ui_patterns=any(fs.ui_pattern for fs in frame_scores),
        metrics_visible=any(fs.metrics_visible for fs in frame_scores),
        code_walkthrough=any(fs.code_walkthrough for fs in frame_scores),
        system_demo=any(fs.system_demo for fs in frame_scores),
        confidence=sum(fs.confidence for fs in frame_scores) / len(frame_scores) if frame_scores else 0.0,
        frame_scores=frame_scores,
    )

    # Compute composite score (0.0-1.0)
    multipliers = {
        "architecture_detected": 2.0,
        "system_demo": 1.8,
        "ui_patterns": 1.5,
        "metrics_visible": 1.3,
        "code_walkthrough": 1.2,
    }
    base = len(frame_scores) / max_frames  # frame coverage
    bonus = sum(
        mult for attr, mult in multipliers.items()
        if getattr(result, attr)
    )
    result.composite_score = min(1.0, base * (1 + bonus / 10))

    return result


# ── CLI ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Vision Scorer — Frame Analysis for RE")
    parser.add_argument("--frames-dir", required=True, help="Directory with extracted frames")
    parser.add_argument("--max-frames", type=int, help="Max frames to analyze")
    parser.add_argument("--output", help="Output JSON path (default: stdout)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    result = score_frames(args.frames_dir, args.max_frames)
    output = json.dumps(result.to_dict(), indent=2, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Vision scores saved to {args.output}")
    else:
        print(output)
