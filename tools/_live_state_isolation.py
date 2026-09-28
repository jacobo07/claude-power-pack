"""One call that points every known live-state path of the long-run / watchdog / rollover
substrate at a private temp dir. Import and call it at the TOP of a test, before importing the
modules under test (several read these variables once, at import).

    import _live_state_isolation as iso; TMP = iso.isolate("mytest")

Why a helper: tools/test_state_isolation.py measured SIX further suites writing the real
~/.claude (markers, the rollover capsule store, the heartbeat log, the LIVE checkout's snapshot
ledger) after three had been fixed one by one on 2026-09-28. Per-suite env lines are how the
next suite forgets one; the ratchet proves the result either way.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path


def isolate(prefix: str) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix=f"{prefix}-iso-"))
    for d in ("state", "sessions", "rollover", "hooks", "projects"):
        (tmp / d).mkdir()
    os.environ.update({
        "GSD_LONG_RUN_STATE_DIR": str(tmp / "state"),
        "GSD_LONG_RUN_SESSIONS_DIR": str(tmp / "sessions"),
        "GSD_AUTORUN_MARKER_DIR": str(tmp / "state"),
        "CPP_ROLLOVER_STATE_DIR": str(tmp / "rollover"),
        "CTXWD_HEARTBEAT_LOG": str(tmp / "context-watchdog.log"),
        "CTXWD_SNAPSHOT_LEDGER": str(tmp / "context_snapshots.jsonl"),
        "CPP_WORK_STATE_DIR": str(tmp / "state"),
    })
    return tmp
