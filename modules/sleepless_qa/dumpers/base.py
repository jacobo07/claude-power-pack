"""
Dumper base class + EvidenceBundle schema.

A Dumper is a per-runtime-class adapter that:
  1. launch()  — starts the target (browser, bot, daemon, subprocess)
  2. trigger() — runs the action script (click, send chat, hit endpoint)
  3. capture() — returns an EvidenceBundle (screenshots, logs, responses)
  4. teardown() — cleans up (close browser, kill daemon)

All adapters are subprocess-isolated from the auditor. A crash in the target
never propagates to the QA pipeline.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ActionStep(BaseModel):
    """One step in an action script."""
    kind: str  # navigate | click | type | wait | http | chat | command | custom
    target: str | None = None
    value: str | None = None
    timeout_ms: int = 5000
    extra: dict[str, Any] = Field(default_factory=dict)


class ActionScript(BaseModel):
    """A declarative test scenario. Loaded from YAML."""
    name: str
    runtime_class: str  # web | minecraft | python_daemon | cli
    description: str = ""
    setup: dict[str, Any] = Field(default_factory=dict)
    steps: list[ActionStep] = Field(default_factory=list)
    expectations: dict[str, Any] = Field(default_factory=dict)


class HTTPResponse(BaseModel):
    url: str
    method: str
    status: int
    duration_ms: int
    body_excerpt: str = ""  # first 8KB


class EvidenceBundle(BaseModel):
    """
    Everything a Dumper captured from one run. Verdict engine consumes this.

    Fields intentionally optional — not every runtime produces every type.
    """
    run_id: str
    runtime_class: str
    action_script_name: str
    screenshots: list[Path] = Field(default_factory=list)
    log_excerpts: dict[str, str] = Field(default_factory=dict)
    http_responses: list[HTTPResponse] = Field(default_factory=list)
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    captured_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    model_config = {"arbitrary_types_allowed": True}


class DumperError(Exception):
    """Raised by Dumper implementations on unrecoverable adapter failure.

    NOTE: This is intentionally raised, never swallowed silently (Mistake #21).
    """


class Dumper(ABC):
    """Abstract runtime-class adapter."""

    runtime_class: str = "base"

    def __init__(self, repo_path: Path, config: dict[str, Any], run_id: str) -> None:
        self.repo_path = Path(repo_path).resolve()
        self.config = config
        self.run_id = run_id
        self._launched = False

    @abstractmethod
    def launch(self) -> None:
        """Start the target runtime. Must be idempotent on re-call."""

    @abstractmethod
    def trigger(self, action: ActionScript) -> None:
        """Execute the action script's steps against the running target."""

    @abstractmethod
    def capture(self) -> EvidenceBundle:
        """Produce an EvidenceBundle summarizing what the target did."""

    @abstractmethod
    def teardown(self) -> None:
        """Shut down the target and release any resources."""

    def __enter__(self) -> "Dumper":
        self.launch()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            self.teardown()
        except Exception:
            logger.exception("Dumper teardown failed for %s", self.runtime_class)
            # Do not suppress the original exception context.
