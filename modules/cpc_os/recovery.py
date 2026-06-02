"""CPC-OS recovery -- two concerns:

1. recover_corrupt_registry(): registry-file corruption recovery (backs
   up the broken JSON, returns an empty registry).
2. detect_crash_state(): section 208.4 crash detection -- pure read that
   builds an honest restore plan for stale/crashed panes. Never guesses
   a session identity; a pane with no known session id gets a "new
   session only" low-confidence entry. Idempotent (no mutation), so it
   can run on every SessionStart without side effects.
"""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

from .registry import DEFAULT_REGISTRY_PATH, PaneRegistry, STALE_THRESHOLD_S


def recover_corrupt_registry(
    path: Path | None = None,
) -> tuple[PaneRegistry, bool]:
    """Returns (registry, recovered_flag). When the file parses
    cleanly: returns the live registry and False. When it doesn't:
    backs up the broken file to <path>.corrupt-<ts>.bak (best effort)
    and returns an empty registry + True."""
    p = path or DEFAULT_REGISTRY_PATH
    if not p.is_file():
        return PaneRegistry(_path=p), False
    try:
        json.loads(p.read_text(encoding="utf-8"))
        return PaneRegistry.load(p), False
    except (OSError, json.JSONDecodeError):
        ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        backup = p.with_suffix(f".corrupt-{ts}.bak")
        try:
            shutil.copy2(p, backup)
        except OSError:
            pass
        return PaneRegistry(_path=p), True


def detect_crash_state(
    registry: PaneRegistry | None = None,
    now: float | None = None,
) -> dict:
    """section 208.4: detect crashed/stale panes and emit a restore plan.

    A pane is a crash candidate when its status is already ``stale`` OR
    it is ``active`` but its last heartbeat is older than
    STALE_THRESHOLD_S. ``dead`` and ``paused`` panes are intentional
    states, not crashes. Pure read -> idempotent. Never spawns a
    terminal; only describes safe ``claude --resume`` / ``cd && claude``
    commands for the Owner to confirm.
    """
    reg = registry if registry is not None else PaneRegistry.load()
    t = time.time() if now is None else now

    crashed: list[tuple] = []
    for rec in reg.panes.values():
        if rec.status in ("dead", "paused"):
            continue
        idle = t - rec.last_heartbeat_at
        if rec.status == "stale" or (rec.status == "active" and idle > STALE_THRESHOLD_S):
            crashed.append((rec, idle))

    if not crashed:
        return {
            "crash_detected": False,
            "active_count": len(reg.get_active_panes()),
            "stale_count": 0,
            "restore_plan": [],
            "message": "No crash detected -- all panes healthy",
        }

    plan: list[dict] = []
    for rec, idle in crashed:
        if rec.session_id:
            plan.append({
                "pane_id": rec.pane_id,
                "cwd": rec.cwd,
                "action": f"claude --resume {rec.session_id}",
                "session_id": rec.session_id,
                "confidence": "high",
                "idle_s": round(idle, 1),
            })
        else:
            plan.append({
                "pane_id": rec.pane_id,
                "cwd": rec.cwd,
                "action": f"cd {rec.cwd} && claude",
                "session_id": None,
                "confidence": "low",
                "note": "session id unknown -- new session only (no guessing)",
                "idle_s": round(idle, 1),
            })

    return {
        "crash_detected": True,
        "stale_count": len(crashed),
        "active_count": len(reg.get_active_panes()),
        "restore_plan": plan,
        "message": (
            f"Crash recovery: {len(crashed)} stale/crashed pane(s). "
            "Restore plan generated. Manual confirmation required."
        ),
    }
