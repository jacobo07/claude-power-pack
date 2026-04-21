"""
Visual verdict — Claude Vision API against captured screenshots.

Uses the same client pattern as modules/autoresearch/vision_scorer.py.
Issued a strict-JSON QA-inspector prompt; returns PASS/FAIL/UNCERTAIN based
on the model's verdict and confidence.

Guard: confidence < uncertain_threshold => UNCERTAIN (not FAIL).
"""

from __future__ import annotations

import base64
import json
import logging
import os
from pathlib import Path
from typing import Any

from ..dumpers.base import EvidenceBundle
from .schema import Verdict, VerdictStatus

logger = logging.getLogger(__name__)

VISION_MODEL_DEFAULT = "claude-haiku-4-5-20251001"

VERDICT_PROMPT = """You are a QA inspector reviewing a screenshot captured during automated testing.

Your job: determine if this screenshot shows a **working** application state or a **broken** one.

Broken signals include:
- Visible error dialogs, stack traces, crash screens
- Blank white/black pages (unless that's the expected state)
- Untranslated placeholder text (lorem ipsum, TODO, [object Object], undefined, NaN)
- Missing images (broken-image icons)
- Layout completely misaligned / overflowing
- Text overlapping other text
- Loading spinners frozen for a long time (stuck state)

Working signals:
- Content rendered as expected
- Interactive elements visible and well-formed
- No error overlays

Respond in STRICT JSON with this exact shape (no markdown, no commentary):
{"status": "PASS" | "FAIL", "confidence": 0.0-1.0, "reason": "<one sentence>"}

If you cannot tell, pick the closest status and lower the confidence below 0.7."""


def _api_key() -> str | None:
    return os.environ.get("ANTHROPIC_API_KEY")


def _encode(path: Path) -> tuple[str, str]:
    data = base64.standard_b64encode(path.read_bytes()).decode("utf-8")
    suffix = path.suffix.lower()
    media = "image/png" if suffix == ".png" else "image/jpeg"
    return data, media


def _cost_estimate_usd(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens * 1.0 + output_tokens * 5.0) / 1_000_000


def evaluate(
    bundle: EvidenceBundle,
    uncertain_threshold: float = 0.7,
    model: str = VISION_MODEL_DEFAULT,
    max_frames: int = 3,
) -> Verdict | None:
    """
    Score up to `max_frames` screenshots. Returns aggregated verdict.

    Returns None if no screenshots are present (skip this strategy).
    """
    if not bundle.screenshots:
        return None

    api_key = _api_key()
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set — visual strategy skipped")
        return Verdict(
            status=VerdictStatus.UNCERTAIN,
            confidence=0.0,
            reason="Visual strategy skipped: ANTHROPIC_API_KEY not set",
            strategy="visual",
            evidence_refs=[str(p) for p in bundle.screenshots[:max_frames]],
            priority_level=2,
        )

    try:
        import anthropic  # type: ignore
    except ImportError:
        logger.warning("anthropic SDK not installed — visual strategy skipped")
        return Verdict(
            status=VerdictStatus.UNCERTAIN,
            confidence=0.0,
            reason="Visual strategy skipped: anthropic SDK not installed",
            strategy="visual",
            evidence_refs=[],
            priority_level=2,
        )

    # Evenly sample frames
    frames = list(bundle.screenshots)
    if len(frames) > max_frames:
        step = len(frames) / max_frames
        frames = [frames[int(i * step)] for i in range(max_frames)]

    client = anthropic.Anthropic(api_key=api_key)
    verdicts: list[tuple[str, float, str]] = []
    total_cost = 0.0

    for frame in frames:
        try:
            data, media = _encode(frame)
        except OSError as exc:
            logger.error("Failed to read frame %s: %s", frame, exc)
            continue

        try:
            response = client.messages.create(
                model=model,
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": media, "data": data}},
                        {"type": "text", "text": VERDICT_PROMPT},
                    ],
                }],
            )
        except Exception as exc:
            logger.error("Vision API error on %s: %s", frame, exc)
            continue

        in_tok = int(getattr(response.usage, "input_tokens", 0))
        out_tok = int(getattr(response.usage, "output_tokens", 0))
        total_cost += _cost_estimate_usd(in_tok, out_tok)

        raw = response.content[0].text.strip()
        parsed = _parse_strict_json(raw)
        if parsed is None:
            logger.warning("Could not parse vision response as JSON: %r", raw[:200])
            continue

        status = str(parsed.get("status", "")).upper()
        conf = float(parsed.get("confidence", 0.0))
        reason = str(parsed.get("reason", ""))
        if status not in ("PASS", "FAIL"):
            logger.warning("Unexpected status from vision model: %r", status)
            continue
        verdicts.append((status, conf, reason))

    if not verdicts:
        return Verdict(
            status=VerdictStatus.UNCERTAIN,
            confidence=0.0,
            reason="All vision calls failed or returned unparseable data",
            strategy="visual",
            evidence_refs=[str(f) for f in frames],
            priority_level=2,
            api_cost_estimate_usd=total_cost,
        )

    # Aggregate: any FAIL with confidence above threshold → FAIL
    confident_fails = [(s, c, r) for s, c, r in verdicts if s == "FAIL" and c >= uncertain_threshold]
    if confident_fails:
        worst = min(confident_fails, key=lambda t: t[1])
        return Verdict(
            status=VerdictStatus.FAIL,
            confidence=worst[1],
            reason=f"Visual FAIL: {worst[2]}",
            strategy="visual",
            evidence_refs=[str(f) for f in frames],
            priority_level=2,
            api_cost_estimate_usd=total_cost,
        )

    confident_passes = [(s, c, r) for s, c, r in verdicts if s == "PASS" and c >= uncertain_threshold]
    if confident_passes and len(confident_passes) == len(verdicts):
        avg_conf = sum(c for _, c, _ in confident_passes) / len(confident_passes)
        return Verdict(
            status=VerdictStatus.PASS,
            confidence=avg_conf,
            reason=f"Visual PASS across {len(confident_passes)} frames",
            strategy="visual",
            evidence_refs=[str(f) for f in frames],
            priority_level=2,
            api_cost_estimate_usd=total_cost,
        )

    # Mixed or low confidence
    avg_conf = sum(c for _, c, _ in verdicts) / len(verdicts)
    return Verdict(
        status=VerdictStatus.UNCERTAIN,
        confidence=avg_conf,
        reason=f"Visual results mixed or low confidence across {len(verdicts)} frames",
        strategy="visual",
        evidence_refs=[str(f) for f in frames],
        priority_level=2,
        api_cost_estimate_usd=total_cost,
    )


def _parse_strict_json(text: str) -> dict[str, Any] | None:
    """Extract JSON from a possibly-wrapped response."""
    if "```" in text:
        parts = text.split("```")
        if len(parts) >= 2:
            candidate = parts[1]
            if candidate.startswith("json"):
                candidate = candidate[4:]
            text = candidate
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return None
