#!/usr/bin/env python
"""gsd_autorun_marker — the "an autonomous run is in flight" record.

One marker per session at ``~/.claude/state/gsd-autorun-<session_id>.json``.
Its presence is what turns the tier-2 context watchdog from "checkpoint and
advise" into "checkpoint, compact, and come back" (spec
vault/specs/gsd-autonomous-autocompact.md).

The marker carries the command that must be re-issued after a compaction. It
is data the resume daemon types verbatim, so it is validated on write: a
command that does not start with a slash, or that carries a SendKeys
metacharacter, is refused rather than typed into the Owner's editor.

CLI:
    python tools/gsd_autorun_marker.py --write --session <sid> \
        --command "/gsd-autonomous --from 3" [--cwd <path>] [--phase 3]
    python tools/gsd_autorun_marker.py --read  --session <sid>
    python tools/gsd_autorun_marker.py --clear --session <sid>
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

STATE_DIR = Path.home() / ".claude" / "state"
MARKER_TEMPLATE = "gsd-autorun-{session_id}.json"

# SendKeys treats these as control characters. A command containing one would
# be typed as a key sequence (or swallowed), so the marker refuses it at the
# write boundary rather than at the dispatch boundary where nobody is looking.
SENDKEYS_METACHARS = set('+^%~(){}[]')

_SESSION_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


class MarkerError(ValueError):
    """Refusal to write a marker that would be unsafe to type."""


def marker_path(session_id: str) -> Path:
    if not _SESSION_RE.match(session_id or ""):
        raise MarkerError(f"invalid session id: {session_id!r}")
    return STATE_DIR / MARKER_TEMPLATE.format(session_id=session_id)


def validate_command(command: str) -> str:
    """Return the command, or raise MarkerError naming why it cannot be typed."""
    cmd = (command or "").strip()
    if not cmd:
        raise MarkerError("empty resume command")
    if not cmd.startswith("/"):
        raise MarkerError(
            f"resume command must start with '/' (got {cmd[:24]!r})")
    if "\n" in cmd or "\r" in cmd:
        raise MarkerError("resume command must be a single line")
    bad = sorted(SENDKEYS_METACHARS.intersection(cmd))
    if bad:
        raise MarkerError(
            "resume command carries SendKeys metacharacter(s): " + " ".join(bad))
    if len(cmd) > 200:
        raise MarkerError(f"resume command too long ({len(cmd)} chars, max 200)")
    return cmd


def write_marker(session_id: str, command: str, cwd: str = "",
                 phase: int | None = None) -> Path:
    path = marker_path(session_id)
    cmd = validate_command(command)
    payload = {
        "session_id": session_id,
        "resume_command": cmd,
        "cwd": cwd,
        "phase": phase,
        "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "schema_version": 1,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)
    return path


def read_marker(session_id: str) -> dict | None:
    """Return the marker dict, or None when absent/unreadable/malformed.

    Fail-closed on content: a marker whose command no longer validates is
    treated as absent, so a hand-edited file cannot become keystrokes.
    """
    try:
        path = marker_path(session_id)
    except MarkerError:
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    try:
        validate_command(data.get("resume_command", ""))
    except MarkerError:
        return None
    return data


def clear_marker(session_id: str) -> bool:
    try:
        path = marker_path(session_id)
    except MarkerError:
        return False
    try:
        path.unlink()
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="GSD autorun marker")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--read", action="store_true")
    mode.add_argument("--clear", action="store_true")
    ap.add_argument("--session", required=True)
    ap.add_argument("--command", default="")
    ap.add_argument("--cwd", default="")
    ap.add_argument("--phase", type=int, default=None)
    ap.add_argument("--mission", default="",
                    help="comma-separated vocabulary of the Owner-approved mission; the active "
                         "GSD milestone must intersect it or arming is refused")
    args = ap.parse_args(argv)

    if args.write:
        # Arming point of /cpp-gsd-long. A mechanically sound runner pointed at a stale roadmap
        # executes the wrong mission (tools/gsd_mission_freshness.py), so the CLI refuses to
        # arm unless the active milestone matches a declared mission. The library call
        # write_marker() stays unconditional: it is the primitive, this is the boundary.
        try:
            import gsd_mission_freshness as _mf
        except ImportError:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            import gsd_mission_freshness as _mf
        verdict = _mf.check(args.cwd or ".", args.mission)
        if not verdict.armable:
            sys.stderr.write(f"REFUSED: mission freshness {verdict.outcome}: {verdict.reason}\n")
            return 2
        try:
            path = write_marker(args.session, args.command, args.cwd, args.phase)
            data = json.loads(path.read_text(encoding="utf-8"))
            data["mission"] = {"terms": verdict.mission_terms, "matched": verdict.matched,
                               "active_milestone": verdict.active_milestone}
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except MarkerError as exc:
            sys.stderr.write(f"REFUSED: {exc}\n")
            return 2
        sys.stdout.write(str(path) + "\n")
        return 0

    if args.read:
        data = read_marker(args.session)
        if data is None:
            sys.stdout.write("ABSENT\n")
            return 1
        sys.stdout.write(json.dumps(data) + "\n")
        return 0

    removed = clear_marker(args.session)
    sys.stdout.write("CLEARED\n" if removed else "ABSENT\n")
    return 0 if removed else 1


if __name__ == "__main__":
    sys.exit(main())
