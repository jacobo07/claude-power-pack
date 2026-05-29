"""PP Proactive Agent Core -- Jobs/Woz Standard.

Centralizes throttle, signal evaluation, and advisory formatting for
the seven PP agents that now emit unsolicited advisories when their
signals fire. Sleepy-by-default: silence is implicit approval.

Sealed BL-PROACTIVE-001 (2026-05-29).
"""
from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[2]
_THROTTLE_DIR = PP_ROOT / "vault" / "pp_agents" / "throttle"


@dataclass
class ProactiveSignal:
    agent_name: str
    trigger: str
    value: float
    advisory: str
    gate: str = "jobs"
    actionable: str = ""


@dataclass
class AgentConfig:
    name: str
    cooldown_minutes: int = 15
    min_signal_strength: float = 0.6
    max_advisory_lines: int = 3
    domains: list[str] = field(default_factory=list)


def _throttle_key(agent: str, project: str) -> Path:
    _THROTTLE_DIR.mkdir(parents=True, exist_ok=True)
    safe_agent = agent.replace("/", "_").replace("\\", "_")
    safe_project = project.replace("/", "_").replace("\\", "_")
    return _THROTTLE_DIR / f"{safe_agent}_{safe_project}.json"


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent),
                               suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _load_state(key: Path) -> dict:
    if not key.exists():
        return {}
    try:
        return json.loads(key.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def is_throttled(agent: str, project: str = "global",
                 cooldown_min: int = 15) -> bool:
    """True iff the agent fired within the last cooldown_min minutes."""
    state = _load_state(_throttle_key(agent, project))
    last_iso = state.get("last_fire")
    if not last_iso:
        return False
    try:
        last = datetime.fromisoformat(last_iso.replace("Z", "+00:00"))
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
    except ValueError:
        return False
    elapsed_min = (datetime.now(timezone.utc) - last).total_seconds() / 60
    return elapsed_min < cooldown_min


def mark_fired(agent: str, project: str = "global",
               advisory: str = "") -> None:
    key = _throttle_key(agent, project)
    state = _load_state(key)
    payload = {
        "last_fire": datetime.now(timezone.utc).isoformat(),
        "last_advisory": advisory[:200],
        "fire_count": int(state.get("fire_count", 0)) + 1,
    }
    try:
        _atomic_write_json(key, payload)
    except OSError:
        pass


def format_advisory(signal: ProactiveSignal) -> str:
    """Jobs/Woz format: icon + agent + message (<=3 lines) + action."""
    icon = "[Jobs]" if signal.gate == "jobs" else "[Woz]"
    lines = signal.advisory.strip().split("\n")[:3]
    body = "\n".join(lines)
    action = f"\n-> {signal.actionable}" if signal.actionable else ""
    return f"{icon} [{signal.agent_name}] {body}{action}"


def evaluate_and_fire(
    agent: str,
    project: str,
    signal_fn: Callable[[], ProactiveSignal | None],
    config: AgentConfig,
) -> str | None:
    """Evaluate signal, respect throttle + threshold, return advisory.

    Returns None when:
      - the agent fired recently (throttle)
      - signal_fn() returned None (no signal worth surfacing)
      - signal strength < config.min_signal_strength (weak signal)
    """
    if is_throttled(agent, project, config.cooldown_minutes):
        return None
    try:
        signal = signal_fn()
    except Exception:
        return None
    if signal is None:
        return None
    if signal.value < config.min_signal_strength:
        return None
    advisory = format_advisory(signal)
    mark_fired(agent, project, advisory)
    return advisory


__all__ = [
    "ProactiveSignal",
    "AgentConfig",
    "is_throttled",
    "mark_fired",
    "format_advisory",
    "evaluate_and_fire",
]
