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
import os
import re
import sys
from pathlib import Path

# Opt-in redirect for suites that must not write synthetic markers into the Owner's real
# state dir. Deliberately NOT GSD_LONG_RUN_STATE_DIR: ~20 existing suites and tools set that
# variable while writing markers to the real dir, and reusing it split them from the
# watchdog they drive (measured: V-OVLY-ARMED-LEGACY-REACHED went red). A new name has no
# existing consumer to break.
STATE_DIR = Path(os.environ.get("GSD_AUTORUN_MARKER_DIR") or (Path.home() / ".claude" / "state"))
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


def resolve_cwd(cwd: str) -> str:
    """Absolutise the project at ARMING time, where the answer is knowable.

    `/cpp-gsd-long` documents `--cwd .`, and a marker that stores `"."` is read
    later by a sweep running in its OWN directory -- so the relative path
    resolves against the reader instead of the run. Measured 2026-09-19: 8 of 9
    armed markers held `"."`, and `Path(".").is_dir()` is true everywhere, which
    is what makes the finish path able to unlink another project's marker.

    Empty stays empty: it means *unknown*, and turning it into the arming
    process's directory would be the same guess one layer earlier.
    """
    if not cwd:
        return ""
    try:
        return str(Path(cwd).resolve())
    except OSError:
        return cwd


def write_marker(session_id: str, command: str, cwd: str = "",
                 phase: int | None = None, max_cycles: int | None = None,
                 max_hours: float | None = None) -> Path:
    path = marker_path(session_id)
    cmd = validate_command(command)
    now = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    payload = {
        "session_id": session_id,
        "resume_command": cmd,
        "cwd": resolve_cwd(cwd),
        "phase": phase,
        "ts": now,
        "armed_at": now,
        "cycles": 0,
        # Budget (spec gsd-long-run-v2.md, gap 11). None -> the resume gate's defaults.
        "max_cycles": max_cycles,
        "max_hours": max_hours,
        "schema_version": 2,
    }
    _save(path, payload)
    return path


def _save(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)


def bump_cycles(session_id: str) -> int | None:
    """Count one resume against the budget. Returns the new count, None if no marker."""
    data = read_marker(session_id)
    if data is None:
        return None
    data["cycles"] = int(data.get("cycles") or 0) + 1
    _save(marker_path(session_id), data)
    return data["cycles"]


def record_intent(session_id: str, intent: str) -> bool:
    """Persist what must happen FIRST after the compaction. True when stored.

    This is the durable home for the obligations the model writes into its
    `/compact ...` line, and it exists because the host destroys them two
    different ways (measured 2026-09-19, both in this estate's transcripts):

      * 37cfb187 -- the args arrived and were wrapped in
        `<local-command-caveat> ... DO NOT respond to these messages or
        otherwise consider them ...`, i.e. the host hands the model the
        instruction inside an envelope telling it to ignore the instruction;
      * de7f3c91 -- `<command-args></command-args>`, empty, because the line
        was ultimately submitted by hand as a bare `/compact`.

    `compactMetadata` has no field for the text at all, so nothing downstream
    can recover it. Stored here it reaches the model through the Stop hook's
    `reason`, which the host does not caveat.

    Never raises and never CREATES a marker: an intent for a run that is not
    armed is not a run, and inventing a marker here would arm one by accident.
    """
    try:
        text = (intent or "").strip()
        if not text:
            return False
        data = read_marker(session_id)
        if data is None:
            return False
        data["post_compact_intent"] = text
        _save(marker_path(session_id), data)
        return True
    except Exception:
        return False


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
    ap.add_argument("--max-cycles", type=int, default=None,
                    help="resumes allowed before the run halts (default 12)")
    ap.add_argument("--max-hours", type=float, default=None,
                    help="wall-clock hours before the run halts (default 24)")
    ap.add_argument("--workstream", default=None,
                    help="arm against GSD workstream .planning/workstreams/<name> instead of the "
                         "root milestone, for a repo whose root milestone belongs to another track. "
                         "Freshness, the phase preflight, every resume re-check and the sweep's "
                         "finish test then read that workstream. Set it active for THIS session "
                         "first (gsd-tools query workstream.set <name>), so the resumed command "
                         "routes there too.")
    args = ap.parse_args(argv)

    if args.write:
        # Arming point of /cpp-gsd-long. A mechanically sound runner pointed at a stale roadmap
        # executes the wrong mission (tools/gsd_mission_freshness.py), so the CLI refuses to
        # arm unless the active milestone matches a declared mission. The library call
        # write_marker() stays unconditional: it is the primitive, this is the boundary.
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import gsd_mission_freshness as _mf
        import gsd_long_run as _lr
        try:
            verdict = _mf.check(args.cwd or ".", args.mission, args.workstream)
        except ValueError as exc:
            sys.stderr.write(f"REFUSED: {exc}\n")
            return 2
        if not verdict.armable:
            sys.stderr.write(f"REFUSED: mission freshness {verdict.outcome}: {verdict.reason}\n")
            return 2
        # Gaps 6 + 8 (spec gsd-long-run-v2.md): the run executes in the SESSION's directory,
        # and /gsd-autonomous does nothing on a roadmap GSD cannot parse.
        try:
            validate_command(args.command)
        except MarkerError as exc:
            sys.stderr.write(f"REFUSED: {exc}\n")
            return 2
        ok, why = _lr.arm_preflight(args.session, args.cwd or ".", args.command,
                                    workstream=args.workstream)
        if not ok:
            sys.stderr.write(f"REFUSED: {why}\n")
            return 2
        try:
            path = write_marker(args.session, args.command, args.cwd, args.phase,
                                args.max_cycles, args.max_hours)
            data = json.loads(path.read_text(encoding="utf-8"))
            data["mission"] = {"terms": verdict.mission_terms, "matched": verdict.matched,
                               "active_milestone": verdict.active_milestone}
            if args.workstream:
                # Every later reader (resume_gate, sweep) re-derives its answer from this key;
                # absent, they read the root milestone -- another track's, in the case it exists for.
                data["workstream"] = args.workstream
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except MarkerError as exc:
            sys.stderr.write(f"REFUSED: {exc}\n")
            return 2
        # cwd is DERIVED from the marker just written, never recomputed from args.cwd.
        # write_marker stored resolve_cwd(cwd) (:98); passing the raw argument here let one
        # arming produce two disagreeing records -- an absolute path in the marker and a
        # bare "." in the ledger row, which no later reader can resolve, and which is the
        # same defect marker_project already REFUSES rather than resolves
        # (gsd_long_run.py:739). A second resolve_cwd call could drift; a value read back
        # from the marker cannot disagree with it. Empty stays empty, per resolve_cwd.
        _lr.ledger_append(args.session, "armed", command=args.command, cwd=data.get("cwd"),
                          max_cycles=data.get("max_cycles"), max_hours=data.get("max_hours"))
        # Path stays the FIRST line: it is this command's machine-readable result and
        # callers parse it. Everything after is for the human/agent reading the terminal.
        sys.stdout.write(str(path) + "\n")
        # ARMING IS NOT STARTING. Measured 2026-09-19 across this estate's own ledger:
        # 4 of 9 markers had been armed with no evidence a run ever began, three of them
        # from different sessions. The failure is not carelessness -- it is that a marker
        # and lowered thresholds make a run SURVIVE a compaction while launching nothing,
        # and `gsd_long_run.py status` reports an armed-and-idle run exactly the way it
        # reports a healthy one. Worse, every event that would distinguish them
        # (crossing / resume_requested / resume_confirmed) only fires at the FIRST
        # compaction, which can be hours away -- so in between, a started run and an
        # abandoned one are indistinguishable by construction.
        #
        # A sentence in the command doc did not travel to this moment; three sessions
        # proved that. This does, because it is printed at the instant of the mistake.
        sys.stdout.write(
            "\n"
            "  ARMED -- BUT NOTHING IS RUNNING YET.\n"
            "  The marker only makes a run survive a compaction. It starts nothing.\n"
            "\n"
            f"  NEXT STEP (required, not optional):   {args.command}\n"
            "\n"
            "  Invoke that now. If you stop here you have configured compaction-survival\n"
            "  for a run that never began, and `gsd_long_run.py status` will show it as a\n"
            "  healthy armed run for as long as it sits there.\n"
        )
        return 0

    if args.read:
        data = read_marker(args.session)
        if data is None:
            sys.stdout.write("ABSENT\n")
            return 1
        sys.stdout.write(json.dumps(data) + "\n")
        return 0

    removed = clear_marker(args.session)
    if removed:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import gsd_long_run as _lr
        _lr.ledger_append(args.session, "cleared", by="cli")
    sys.stdout.write("CLEARED\n" if removed else "ABSENT\n")
    return 0 if removed else 1


if __name__ == "__main__":
    sys.exit(main())
