"""
Run log — jsonl appender + correction logging to memory-engine.

Every run (heartbeat, QA, heal attempt) appends a line to the run's jsonl.
On successful heal, also calls memory-engine/append_memory.py so the
correction becomes part of the persistent learning corpus.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .. import STATE_DIR_DEFAULT

logger = logging.getLogger(__name__)


def _runs_dir() -> Path:
    override = os.environ.get("QA_STATE_DIR")
    base = Path(override).expanduser() if override else STATE_DIR_DEFAULT
    d = base / "runs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def run_dir_for(run_id: str) -> Path:
    d = _runs_dir() / run_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def append_event(run_id: str, event: dict[str, Any]) -> None:
    """Append an event to the run's jsonl log."""
    path = run_dir_for(run_id) / "run.jsonl"
    payload = {"ts": datetime.now(timezone.utc).isoformat(), **event}
    with path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(payload) + "\n")


def write_verdict_json(run_id: str, verdict_data: dict[str, Any]) -> Path:
    """Write the final verdict.json for this run."""
    path = run_dir_for(run_id) / "verdict.json"
    path.write_text(json.dumps(verdict_data, indent=2), encoding="utf-8")
    return path


def log_correction(summary: str) -> bool:
    """
    Persist a healing correction to the memory-engine so it influences
    future sessions. Returns True on success.
    """
    mem_path = Path(
        os.path.expanduser(
            "~/.claude/skills/claude-power-pack/modules/memory-engine/append_memory.py"
        )
    )
    if not mem_path.exists():
        logger.warning("memory-engine not found at %s — correction not logged", mem_path)
        return False
    entry = f"Correction: {summary}"
    try:
        result = subprocess.run(
            [sys.executable, str(mem_path), entry],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode != 0:
            logger.warning("memory-engine exit=%d stderr=%s", result.returncode, result.stderr)
            return False
        return True
    except subprocess.TimeoutExpired:
        logger.warning("memory-engine timed out")
        return False
    except Exception:
        logger.exception("memory-engine invocation failed")
        return False
