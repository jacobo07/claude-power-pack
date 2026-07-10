#!/usr/bin/env python3
"""session_active.py -- D5: the shared "is a Claude session live right now?" guard.

Several scheduled tasks fire every 2-8 minutes 24/7 whether or not any Claude Code
session is running. For tasks whose work is meaningless without a live session
(hibernation governor, pane-map rebuild), that is pure idle burn. This guard is the
single gate they call to skip cleanly when nothing is live.

LIVENESS BY INTERNAL TIMESTAMP, NOT FILE MTIME. A transcript's file mtime is forged
by batch sweeps (heartbeats, backups, git, antivirus) -- the pane_map-mtime-forges-
liveness lesson. The authoritative signal is the newest INTERNAL "timestamp" field
inside the transcript JSONL (written by Claude Code per turn). mtime is used ONLY as
a cheap prefilter to pick which transcripts to read the internal timestamp from.

Fail-open toward RUNNING: if the guard cannot determine activity (no corpus, parse
error), it reports UNKNOWN and the CLI exits 0 (active), so a broken guard never
silently stops a task forever. A task skips ONLY on an explicit IDLE verdict.
"""
from __future__ import annotations

import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# A session is "active" if its newest internal entry is within this many minutes.
DEFAULT_IDLE_MIN = float(os.environ.get("PP_SESSION_ACTIVE_IDLE_MIN", "15"))
# How many most-recently-modified transcripts to read internal timestamps from.
_MTIME_PREFILTER = 30
# Tail bytes to scan for the last internal timestamp (a turn entry is well under this).
_TAIL_BYTES = 65536

_SID_RE = re.compile(r"^[0-9a-fA-F-]{8,}$")
_TS_RE = re.compile(rb'"timestamp"\s*:\s*"([0-9T:\.\-\+Z]+)"')


def _proj_base(proj_base=None) -> Path:
    return Path(proj_base) if proj_base else (Path.home() / ".claude" / "projects")


def _tail(path: Path, n: int = _TAIL_BYTES) -> bytes:
    try:
        with path.open("rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(0, size - n))
            return fh.read()
    except OSError:
        return b""


def _parse_iso(raw: str):
    try:
        t = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return t if t.tzinfo else t.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def newest_internal_activity_min(proj_base=None, *, now=None,
                                 prefilter: int = _MTIME_PREFILTER):
    """Minutes since the newest INTERNAL transcript timestamp across live-ish
    sessions. None if no timestamp could be read (unknown). Fail-open -> None."""
    try:
        base = _proj_base(proj_base)
        if not base.is_dir():
            return None
        now = now or datetime.now(timezone.utc)
        cands = []
        for sub in base.iterdir():
            if not sub.is_dir():
                continue
            for jf in sub.glob("*.jsonl"):
                if "subagent" in jf.name.lower() or not _SID_RE.match(jf.stem):
                    continue
                try:
                    cands.append((jf.stat().st_mtime, jf))
                except OSError:
                    continue
        cands.sort(key=lambda c: c[0], reverse=True)
        newest = None
        for _, jf in cands[:prefilter]:
            for m in _TS_RE.finditer(_tail(jf)):
                t = _parse_iso(m.group(1).decode("ascii", "replace"))
                if t and (newest is None or t > newest):
                    newest = t
        if newest is None:
            return None
        return (now - newest).total_seconds() / 60.0
    except Exception:  # noqa: BLE001 -- fail-open
        return None


def is_session_active(max_idle_min: float = DEFAULT_IDLE_MIN, *, proj_base=None,
                      now=None) -> bool:
    """True if a session's newest internal entry is within max_idle_min. UNKNOWN
    (no timestamp) fails OPEN -> True (never silently stop a task on a broken probe)."""
    age = newest_internal_activity_min(proj_base, now=now)
    if age is None:
        return True  # fail-open toward running
    return age <= max_idle_min


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="D5 session-active guard")
    ap.add_argument("--quiet", action="store_true",
                    help="exit 0 if active/unknown, 1 if IDLE (for task gates)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--max-idle-min", type=float, default=DEFAULT_IDLE_MIN)
    args = ap.parse_args(argv)
    age = newest_internal_activity_min()
    active = age is None or age <= args.max_idle_min
    if args.json:
        import json
        print(json.dumps({"active": active, "idle_min": age,
                          "max_idle_min": args.max_idle_min,
                          "verdict": "ACTIVE" if active else "IDLE"}))
    elif not args.quiet:
        if age is None:
            print("ACTIVE (unknown activity -> fail-open)")
        else:
            print(f"{'ACTIVE' if active else 'IDLE'} (last internal entry {age:.1f} min ago)")
    # quiet mode: exit code IS the answer. 0 = active/unknown, 1 = idle.
    return 0 if active else 1


if __name__ == "__main__":
    raise SystemExit(main())
