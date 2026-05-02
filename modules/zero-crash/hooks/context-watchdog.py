#!/usr/bin/env python
"""Stop-hook: context-watchdog (BL-0015 + BL-0033 dual-threshold).

Two-tier context-pressure response on Stop event:

  Tier 1 — SNAPSHOT (used_pct >= 60):
    Append session snapshot to vault/sleepy/context_snapshots.jsonl
    AND a human-readable section to vault/progress.md.
    Silent (no advisory). Per-session debounced via tmp flag.

  Tier 2 — ADVISORY (used_pct >= 70):
    Above PLUS inject hookSpecificOutput.additionalContext telling the
    model to ASK the user to type `/compact focus on <current task>`.
    Per BL-0003 hooks CANNOT auto-fire slash commands; this advises
    the model, which advises the user, who types the command.
    Per-session debounced via separate tmp flag.

Reads metrics from /tmp/claude-ctx-<session_id>.json written by
gsd-statusline.js. Writes via lib/atomic_write.py (BL-0014/0018).

Complements gsd-context-monitor.js (PostToolUse, fires mid-turn at
35% remaining for pre-compact vault dump). This hook fires turn-end
and survives mid-turn crash.

Hook contract (Stop event):
  stdin JSON: {"session_id":"...","transcript_path":"...","cwd":"...",
                "stop_hook_active":bool}
  stdout: {} OR {"hookSpecificOutput":{...}} when advisory tier hit
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import sys
import tempfile
from pathlib import Path

# Thresholds (BL-0033)
THRESHOLD_SNAPSHOT_PCT = 60
THRESHOLD_ADVISORY_PCT = 70

ROOT = Path.home() / ".claude" / "skills" / "claude-power-pack"
LEDGER_PATH = ROOT / "vault" / "sleepy" / "context_snapshots.jsonl"
PROGRESS_PATH = ROOT / "vault" / "progress.md"
ATOMIC_WRITE_DIR = ROOT / "lib"

SNAPSHOT_FLAG = "claude-ctxwd-snap-{session_id}.flag"
ADVISORY_FLAG = "claude-ctxwd-adv-{session_id}.flag"


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
    metrics_path = Path(tempfile.gettempdir()) / f"claude-ctx-{session_id}.json"
    if not metrics_path.exists():
        return None
    try:
        return json.loads(metrics_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _flag_exists(session_id: str, template: str) -> bool:
    flag = Path(tempfile.gettempdir()) / template.format(session_id=session_id)
    return flag.exists()


def _set_flag(session_id: str, template: str) -> None:
    flag = Path(tempfile.gettempdir()) / template.format(session_id=session_id)
    try:
        flag.write_text("1", encoding="utf-8")
    except Exception:
        pass


def _append_progress_md(atomic_write, session_id: str, used_pct: float, remaining_pct, cwd: str, transcript_path: str) -> None:
    """Append a markdown section for this session to vault/progress.md."""
    now = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    section = (
        f"\n## {now} — session {session_id[:8]}\n"
        f"- used: **{used_pct}%** | remaining: {remaining_pct}%\n"
        f"- cwd: `{cwd}`\n"
        f"- transcript: `{transcript_path}`\n"
    )
    existing = b""
    if PROGRESS_PATH.exists():
        try:
            existing = PROGRESS_PATH.read_bytes()
            if existing and not existing.endswith(b"\n"):
                existing += b"\n"
        except Exception:
            existing = b""
    if not existing:
        existing = b"# vault/progress.md\n\nRoll-up of context-watchdog snapshots (BL-0033).\nAppend-only; rotate manually after `/kclear` or `/compact`.\n"
    try:
        atomic_write.atomic_write_bytes(PROGRESS_PATH, existing + section.encode("utf-8"))
    except Exception:
        pass


def _ledger_row(session_id: str, metrics: dict, transcript_path: str, cwd: str, tier: str) -> dict:
    return {
        "iso_ts": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "kind": "context_snapshot",
        "tier": tier,
        "session_id": session_id,
        "used_pct": metrics.get("used_pct"),
        "remaining_pct": metrics.get("remaining_percentage"),
        "tokens_used": metrics.get("tokens_used"),
        "tokens_total": metrics.get("tokens_total"),
        "transcript_path": transcript_path,
        "cwd": cwd,
        "trigger": "stop-watchdog",
        "ledger_law_ref": "BL-0033",
        "schema_version": 2,
    }


def run(event: dict) -> dict:
    session_id = event.get("session_id")
    if not session_id:
        return {}

    metrics = _read_metrics(session_id)
    if not metrics:
        return {}

    used_pct = metrics.get("used_pct")
    if not isinstance(used_pct, (int, float)) or used_pct < THRESHOLD_SNAPSHOT_PCT:
        return {}

    try:
        atomic_write = _import_atomic_write()
    except Exception:
        return {}

    transcript_path = event.get("transcript_path") or ""
    cwd = event.get("cwd") or os.getcwd()

    # Tier 1 (>= 60%) — snapshot, once per session
    if not _flag_exists(session_id, SNAPSHOT_FLAG):
        try:
            atomic_write.atomic_append_jsonl(LEDGER_PATH, _ledger_row(session_id, metrics, transcript_path, cwd, "snapshot"))
            _append_progress_md(atomic_write, session_id, used_pct, metrics.get("remaining_percentage"), cwd, transcript_path)
            _set_flag(session_id, SNAPSHOT_FLAG)
        except Exception:
            pass

    # Tier 2 (>= 70%) — strong advisory, once per session
    if used_pct >= THRESHOLD_ADVISORY_PCT and not _flag_exists(session_id, ADVISORY_FLAG):
        try:
            atomic_write.atomic_append_jsonl(LEDGER_PATH, _ledger_row(session_id, metrics, transcript_path, cwd, "advisory"))
            _set_flag(session_id, ADVISORY_FLAG)
        except Exception:
            pass

        message = (
            f"CONTEXT THRESHOLD CROSSED — {used_pct}% used (>= 70%). "
            "Pre-compact snapshot already written to vault/progress.md and "
            "vault/sleepy/context_snapshots.jsonl. The next safe action is to "
            "ASK THE USER to type `/compact focus on <current task description>`. "
            "Do NOT continue large new work in this turn. Hooks cannot auto-fire "
            "slash commands (BL-0003); the user must type it. Once /compact runs, "
            "vault/progress.md provides the resume anchor."
        )
        return {
            "hookSpecificOutput": {
                "hookEventName": "Stop",
                "additionalContext": message,
            }
        }

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
