"""G6 runtime -- Power Beacon: the graceful-vs-ungraceful startup classifier.

The Session Resilience family already RESTORES on a cold start (extension
``restore_guard.js`` + ``extension.js`` runColdStartRestore, SCS C50) and already
keeps a fresh ``session_snapshot.json`` (session_start_hub hook 8 + ram_guard).
What was missing is the *classification* the G6 dataset specifies in 6.6/6.7:
a durable beacon that lets startup tell apart

  * first-run            -- no prior beacon at all
  * reload               -- pty host reconnected terminals (live count > 0)
  * graceful-reopen      -- the last session wrote a graceful-exit beacon
  * ungraceful-shutdown  -- a session was active and NEVER closed gracefully
                            AND terminals are gone (the Owner's lid-close ->
                            freeze -> power-off -> reboot case)

Only ``ungraceful-shutdown`` requires a recovery to be RECORDED (see reentry.py
-> G5 event + G4 verdict). The reentry MECHANISM itself is the existing extension
guard; this module never relaunches anything.

Durability (G6 dataset 6.6 + HR-G6-BEACON-001): every beacon write is fsync'd and
atomically replaced, so a power loss the instant after a write cannot leave a
truncated beacon. The "two-signal rule" (ACV stale-marker lesson) gates the
ungraceful verdict: it needs BOTH an active-kind beacon AND zero live terminals,
never a single signal.

Hermetic: every function takes an explicit ``state_dir`` -- no global path, no
wall-clock dependency in the pure classifier (callers pass ``now``).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
BEACON_FILENAME = "power_beacon.json"

KIND_ACTIVE = "active"
KIND_GRACEFUL = "graceful"

# Startup classes
FIRST_RUN = "first-run"
RELOAD = "reload"
GRACEFUL_REOPEN = "graceful-reopen"
UNGRACEFUL = "ungraceful-shutdown"


def _now_iso(now: str | None) -> str:
    return now if now else datetime.now(timezone.utc).isoformat(timespec="seconds")


def _beacon_path(state_dir: Path | str) -> Path:
    return Path(state_dir) / BEACON_FILENAME


def _durable_write_json(path: Path, obj: dict) -> None:
    """Atomic + fsync'd write. The file either reflects the prior state or the
    new state in full -- never a half-written record, even on power loss right
    after the call (HR-G6-BEACON-001: no async/buffered-only writes)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    data = json.dumps(obj, ensure_ascii=False, indent=2)
    # newline="" so Windows text-mode never rewrites \n -> \r\n on rewrites
    # (feedback_windows_text_mode_compounding).
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)  # atomic on POSIX and Windows
    # Best-effort directory fsync so the rename itself is durable (no-op on hosts
    # that cannot fsync a directory handle, e.g. some Windows configs).
    try:
        dfd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    except (OSError, AttributeError, ValueError):
        pass


def _read_beacon(state_dir: Path | str) -> dict | None:
    p = _beacon_path(state_dir)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (ValueError, OSError):
        return None


def write_active_beacon(state_dir: Path | str, session_id: str | None = None,
                        cwd: str | None = None, snapshot_ref: str | None = None,
                        now: str | None = None) -> dict:
    """Mark the session ALIVE. Written on SessionStart and at the ram_guard
    pre-OOM threshold so a durable 'I was running' fact exists before any crash.
    The absence of a later graceful beacon is what proves an ungraceful death."""
    rec = {
        "schema_version": SCHEMA_VERSION,
        "kind": KIND_ACTIVE,
        "ts": _now_iso(now),
        "session_id": session_id,
        "cwd": cwd,
        "snapshot_ref": snapshot_ref,
    }
    _durable_write_json(_beacon_path(state_dir), rec)
    return rec


def write_graceful_exit(state_dir: Path | str, session_id: str | None = None,
                        cwd: str | None = None, now: str | None = None) -> dict:
    """Mark a CLEAN close (SessionEnd / window close). Overwrites the active
    beacon so the last word on disk is 'graceful' -- the next startup then reads
    graceful-reopen, not ungraceful-shutdown."""
    rec = {
        "schema_version": SCHEMA_VERSION,
        "kind": KIND_GRACEFUL,
        "ts": _now_iso(now),
        "session_id": session_id,
        "cwd": cwd,
    }
    _durable_write_json(_beacon_path(state_dir), rec)
    return rec


def classify_startup(state_dir: Path | str, live_terminal_count: int = 0,
                     now: str | None = None) -> dict[str, Any]:
    """Pure classifier (no writes). Returns
    {class, confidence, signals[], beacon}. Two-signal rule for UNGRACEFUL:
    an active-kind beacon AND zero live terminals (cold start). A single signal
    is never enough -- a live terminal means reload, a graceful beacon means a
    clean reopen."""
    beacon = _read_beacon(state_dir)
    if beacon is None:
        return {"class": FIRST_RUN, "confidence": "high",
                "signals": ["no prior beacon on disk"], "beacon": None}
    if (live_terminal_count or 0) > 0:
        return {"class": RELOAD, "confidence": "high",
                "signals": ["live terminals present (pty host reconnected)"],
                "beacon": beacon}
    if beacon.get("kind") == KIND_GRACEFUL:
        return {"class": GRACEFUL_REOPEN, "confidence": "high",
                "signals": ["last exit beacon was graceful"], "beacon": beacon}
    # kind == active (or unknown-but-not-graceful) AND no live terminals.
    return {
        "class": UNGRACEFUL,
        "confidence": "high",
        "signals": [
            "prior beacon kind=active (session never closed gracefully)",
            "zero live terminals at startup (true cold start, not a reload)",
        ],
        "beacon": beacon,
    }


def _main(argv=None) -> int:  # pragma: no cover - thin CLI for hub/manual use
    import argparse
    ap = argparse.ArgumentParser(description="G6 power beacon")
    ap.add_argument("--state-dir", default=str(Path.home() / ".claude" / "state"))
    ap.add_argument("--active", action="store_true", help="write an active beacon")
    ap.add_argument("--graceful", action="store_true", help="write a graceful-exit beacon")
    ap.add_argument("--classify", action="store_true", help="print startup classification")
    ap.add_argument("--session-id", default=os.environ.get("PP_EVT_SID"))
    ap.add_argument("--cwd", default=os.environ.get("PP_EVT_CWD") or os.getcwd())
    ap.add_argument("--live-terminals", type=int, default=int(os.environ.get("PP_LIVE_TERMS", "0")))
    a = ap.parse_args(argv)
    if a.active:
        print(json.dumps(write_active_beacon(a.state_dir, a.session_id, a.cwd)))
    elif a.graceful:
        print(json.dumps(write_graceful_exit(a.state_dir, a.session_id, a.cwd)))
    elif a.classify:
        print(json.dumps(classify_startup(a.state_dir, a.live_terminals)))
    else:
        ap.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main())
