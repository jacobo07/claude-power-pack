"""Model Adapter Layer (CCF component #4).

generate(prompt, params) -> ImageArtifact, per vault/plans/CCF_ARCHITECTURE.md
§4. Ships one real adapter (GPTImage2Adapter, the reference repo's provider)
behind a provider-agnostic interface so a second adapter can be added without
touching any caller. CCF-F03 (no fallback provider) is an explicitly open gap
in v1 -- ProviderError propagates as a FAILED ImageArtifact, it is never
swallowed.
"""
from __future__ import annotations

import abc
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional


@dataclass
class ImageArtifact:
    status: str  # "OK" | "FAILED"
    provider: str
    model_id: str
    bytes_: Optional[bytes] = None
    format: Optional[str] = None
    resolution: Optional[str] = None
    cost: Optional[float] = None
    latency_ms: Optional[float] = None
    request_id: Optional[str] = None
    error_detail: Optional[str] = None


class ModelAdapter(abc.ABC):
    """Base interface every provider adapter implements."""

    @abc.abstractmethod
    def generate(self, prompt: str, params: dict) -> ImageArtifact:
        ...


class GPTImage2Adapter(ModelAdapter):
    """Adapter for OpenAI gpt-image-2, matching the reference repo's real params
    (1536x1024, quality=high) as defaults.
    """

    ENDPOINT = "https://api.openai.com/v1/images/generations"
    MODEL_ID = "gpt-image-2"
    # Reference repo's observed cost profile (REVERSE_ENGINEERING_REPORT.md §I):
    # ~90s/call at high quality -- used here only as a default timeout floor.
    DEFAULT_TIMEOUT_S = 120

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY")

    def generate(self, prompt: str, params: dict = None) -> ImageArtifact:
        params = params or {}
        if not self.api_key:
            # Fail-visible, never fail-silent: a missing key is reported as a
            # FAILED artifact with an explicit reason, not a raised exception
            # a caller might not catch, and not a silently-empty result.
            return ImageArtifact(
                status="FAILED",
                provider="openai",
                model_id=self.MODEL_ID,
                error_detail="OPENAI_API_KEY not configured",
            )

        resolution = params.get("resolution", "1536x1024")
        quality = params.get("quality", "high")
        timeout_s = params.get("timeout", self.DEFAULT_TIMEOUT_S)

        body = json.dumps({
            "model": self.MODEL_ID,
            "prompt": prompt,
            "size": resolution,
            "quality": quality,
        }).encode("utf-8")
        request = urllib.request.Request(
            self.ENDPOINT,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

        start = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=timeout_s) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as exc:
            return ImageArtifact(
                status="FAILED",
                provider="openai",
                model_id=self.MODEL_ID,
                latency_ms=(time.monotonic() - start) * 1000,
                error_detail=f"{type(exc).__name__}: {exc}",
            )
        latency_ms = (time.monotonic() - start) * 1000

        try:
            image_b64 = payload["data"][0]["b64_json"]
            image_bytes = image_b64.encode("ascii")  # left base64-encoded; caller decodes
            request_id = payload.get("id")
        except (KeyError, IndexError) as exc:
            return ImageArtifact(
                status="FAILED",
                provider="openai",
                model_id=self.MODEL_ID,
                latency_ms=latency_ms,
                error_detail=f"unexpected response shape: missing {exc}",
            )

        return ImageArtifact(
            status="OK",
            provider="openai",
            model_id=self.MODEL_ID,
            bytes_=image_bytes,
            format="png",
            resolution=resolution,
            latency_ms=latency_ms,
            request_id=request_id,
        )
