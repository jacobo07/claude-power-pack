"""
Sleepless QA — Heartbeat Self-Test

Proves the Claude Vision API is alive by rendering a QR code with a unique
run_id and asking the vision model to decode it. If the decoded payload
matches the original, the pipeline's "eyes" are working.

This is the anti-gaslighting layer. If heartbeat fails, all verdicts that
session are voided. The whole sleepless-qa pipeline refuses to trust any
vision-based PASS until heartbeat passes first.

Usage:
    python -m sleepless_qa.heartbeat
    python -m sleepless_qa heartbeat  (via cli.py)
"""

from __future__ import annotations

import base64
import json
import logging
import os
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from . import STATE_DIR_DEFAULT

logger = logging.getLogger(__name__)

VISION_MODEL = "claude-haiku-4-5-20251001"
HEARTBEAT_PROMPT = (
    "This image contains a QR code. Decode the QR code and return ONLY the "
    "raw text payload it encodes. Do not add any commentary, markdown, or "
    "explanation. If you cannot decode the QR code, return exactly: "
    "QR_DECODE_FAILED"
)


@dataclass
class HeartbeatVerdict:
    run_id: str
    status: str  # "alive" | "dead"
    qr_match: bool
    vision_response_raw: str
    duration_ms: int
    api_cost_estimate_usd: float
    input_tokens: int
    output_tokens: int
    timestamp: str
    error: str | None = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


def _state_dir() -> Path:
    override = os.environ.get("QA_STATE_DIR")
    base = Path(override).expanduser() if override else STATE_DIR_DEFAULT
    hb_dir = base / "heartbeat"
    hb_dir.mkdir(parents=True, exist_ok=True)
    return hb_dir


def _render_qr(payload: str, out_path: Path) -> None:
    try:
        import qrcode  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "qrcode library not installed. Run: pip install qrcode[pil]"
        ) from exc

    img = qrcode.make(payload)
    img.save(str(out_path))


def _call_vision(image_path: Path, api_key: str) -> tuple[str, int, int]:
    try:
        import anthropic  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "anthropic SDK not installed. Run: pip install anthropic"
        ) from exc

    client = anthropic.Anthropic(api_key=api_key)
    image_data = base64.standard_b64encode(image_path.read_bytes()).decode("utf-8")
    media_type = "image/png"

    response = client.messages.create(
        model=VISION_MODEL,
        max_tokens=200,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {"type": "text", "text": HEARTBEAT_PROMPT},
                ],
            }
        ],
    )

    text = response.content[0].text.strip()
    input_tokens = getattr(response.usage, "input_tokens", 0)
    output_tokens = getattr(response.usage, "output_tokens", 0)
    return text, int(input_tokens), int(output_tokens)


def _cost_estimate_usd(input_tokens: int, output_tokens: int) -> float:
    # Haiku 4.5 pricing (per 1M tokens, approximate): $1 input / $5 output
    return (input_tokens * 1.0 + output_tokens * 5.0) / 1_000_000


def run_heartbeat(api_key: str | None = None) -> HeartbeatVerdict:
    """Execute one heartbeat self-test cycle. Returns a HeartbeatVerdict.

    Raises nothing; errors are captured in the verdict's `error` field and
    status is set to "dead". Caller decides whether to raise based on status.
    """
    run_id = str(uuid.uuid4())
    payload = json.dumps({"run_id": run_id, "ts": int(time.time())}, separators=(",", ":"))
    ts_iso = datetime.now(timezone.utc).isoformat()
    hb_dir = _state_dir()
    png_path = hb_dir / f"{run_id}.png"
    json_path = hb_dir / f"{run_id}.json"

    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        verdict = HeartbeatVerdict(
            run_id=run_id,
            status="dead",
            qr_match=False,
            vision_response_raw="",
            duration_ms=0,
            api_cost_estimate_usd=0.0,
            input_tokens=0,
            output_tokens=0,
            timestamp=ts_iso,
            error="ANTHROPIC_API_KEY not set in environment",
        )
        json_path.write_text(verdict.to_json(), encoding="utf-8")
        return verdict

    start = time.monotonic()
    try:
        _render_qr(payload, png_path)
    except Exception as exc:
        logger.exception("Failed to render QR code")
        verdict = HeartbeatVerdict(
            run_id=run_id,
            status="dead",
            qr_match=False,
            vision_response_raw="",
            duration_ms=int((time.monotonic() - start) * 1000),
            api_cost_estimate_usd=0.0,
            input_tokens=0,
            output_tokens=0,
            timestamp=ts_iso,
            error=f"QR render failed: {exc}",
        )
        json_path.write_text(verdict.to_json(), encoding="utf-8")
        return verdict

    try:
        raw, in_tok, out_tok = _call_vision(png_path, api_key)
    except Exception as exc:
        logger.exception("Vision API call failed")
        verdict = HeartbeatVerdict(
            run_id=run_id,
            status="dead",
            qr_match=False,
            vision_response_raw="",
            duration_ms=int((time.monotonic() - start) * 1000),
            api_cost_estimate_usd=0.0,
            input_tokens=0,
            output_tokens=0,
            timestamp=ts_iso,
            error=f"Vision API error: {exc}",
        )
        json_path.write_text(verdict.to_json(), encoding="utf-8")
        return verdict

    duration_ms = int((time.monotonic() - start) * 1000)
    # QR decode comparison: the model may wrap in quotes or add whitespace
    cleaned = raw.strip().strip('"').strip("'").strip()
    qr_match = cleaned == payload or payload in cleaned
    status = "alive" if qr_match else "dead"

    verdict = HeartbeatVerdict(
        run_id=run_id,
        status=status,
        qr_match=qr_match,
        vision_response_raw=raw,
        duration_ms=duration_ms,
        api_cost_estimate_usd=_cost_estimate_usd(in_tok, out_tok),
        input_tokens=in_tok,
        output_tokens=out_tok,
        timestamp=ts_iso,
        error=None if qr_match else f"QR payload mismatch. expected={payload!r} got={cleaned!r}",
    )
    json_path.write_text(verdict.to_json(), encoding="utf-8")
    return verdict


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [heartbeat] %(levelname)s: %(message)s",
    )
    verdict = run_heartbeat()
    print(verdict.to_json())
    return 0 if verdict.status == "alive" else 1


if __name__ == "__main__":
    sys.exit(main())
