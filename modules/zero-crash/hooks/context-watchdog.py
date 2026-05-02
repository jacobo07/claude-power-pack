#!/usr/bin/env python
"""Stop-hook: context-watchdog (BL-0015 / MC-SYS-26).

Fires at end of every turn. If the session's used context % crosses 75%
for the first time, appends a snapshot row to the context-snapshot ledger
(separate from baseline_ledger.jsonl which is for laws, not telemetry).

Complementary to gsd-context-monitor.js (PostToolUse pre-compact dump):
  - PostToolUse (existing): warns mid-turn at <=35% remaining; fires async vault dump
  - Stop (this hook):       end-of-turn ledger row at >=75% used; survives crash mid-turn

Reads metrics from /tmp/claude-ctx-<session_id>.json written by gsd-statusline.js.
Uses lib/atomic_write.py for safe ledger append (BL-0014).

Hook contract (Stop event):
  stdin JSON: {"session_id": "...", "transcript_path": "...", "stop_hook_active": bool, "cwd": "..."}
  stdout: {} (advisory — never blocks)
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import sys
from pathlib import Path

THRESHOLD_USED_PCT = 75
LEDGER_PATH = Path.home() / ".claude" / "skills" / "claude-power-pack" / "vault" / "sleepy" / "context_snapshots.jsonl"
DEBOUNCE_MARKER_TMPL = "claude-ctxwd-{session_id}.flag"
ATOMIC_WRITE_DIR = Path.home() / ".claude" / "skills" / "claude-power-pack" / "lib"


def _import_atomic_write():
    sys.path.insert(0, str(ATOMIC_WRITE_DIR))
    try:
        import atomic_write  # type: ignore
        return atomic_write
    finally:
        try:
            sys.path.remove(str(ATOMIC_WRITE_DIR))
        except ValueError:
            pass


def _read_metrics(session_id: str) -> dict | None:
    import tempfile
    metrics_path = Path(tempfile.gettempdir()) / f"claude-ctx-{session_id}.json"
    if not metrics_path.exists():
        return None
    try:
        return json.loads(metrics_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _already_snapshotted(session_id: str) -> bool:
    import tempfile
    flag = Path(tempfile.gettempdir()) / DEBOUNCE_MARKER_TMPL.format(session_id=session_id)
    return flag.exists()


def _mark_snapshotted(session_id: str) -> None:
    import tempfile
    flag = Path(tempfile.gettempdir()) / DEBOUNCE_MARKER_TMPL.format(session_id=session_id)
    try:
        flag.write_text("1", encoding="utf-8")
    except Exception:
        pass


def run(event: dict) -> dict:
    session_id = event.get("session_id")
    if not session_id:
        return {}

    metrics = _read_metrics(session_id)
    if not metrics:
        return {}

    used_pct = metrics.get("used_pct")
    if not isinstance(used_pct, (int, float)) or used_pct < THRESHOLD_USED_PCT:
        return {}

    if _already_snapshotted(session_id):
        return {}

    try:
        atomic_write = _import_atomic_write()
    except Exception:
        return {}

    transcript_path = event.get("transcript_path") or ""
    cwd = event.get("cwd") or os.getcwd()

    row = {
        "iso_ts": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "kind": "context_snapshot",
        "session_id": session_id,
        "used_pct": used_pct,
        "remaining_pct": metrics.get("remaining_percentage"),
        "tokens_used": metrics.get("tokens_used"),
        "tokens_total": metrics.get("tokens_total"),
        "transcript_path": transcript_path,
        "cwd": cwd,
        "trigger": "stop-watchdog",
        "ledger_law_ref": "BL-0015",
        "schema_version": 1,
    }

    try:
        atomic_write.atomic_append_jsonl(LEDGER_PATH, row)
        _mark_snapshotted(session_id)
    except Exception:
        return {}

    return {}


def main() -> int:
    try:
        raw = sys.stdin.read()
        event = json.loads(raw) if raw.strip() else {}
    except Exception:
        event = {}
    try:
        out = run(event) or {}
    except Exception:
        out = {}
    try:
        sys.stdout.write(json.dumps(out))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
