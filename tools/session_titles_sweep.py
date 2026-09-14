#!/usr/bin/env python3
"""session_titles_sweep.py -- keep every /resume entry descriptively titled, forever.

WHY THIS EXISTS
  Two paths can title a session, and each alone leaves a permanent gap:

    * FORWARD (hooks/mark-live-session.js -> session-title-lib.deriveReadableTitle)
      runs on every Stop, but derives from the ai-title ONLY. A session that never
      gets an ai-title keeps the 8-hex hash forever. Measured 2026-09-14: of 187
      untitled sessions, 77 (41%) were nameable only from first-user / SUB / branch
      -- rungs the forward path does not implement.

    * RETROACTIVE (tools/rename_sessions.py) implements the full 4-rung ladder but
      is a manual CLI. Nothing invoked it, so the gap reopened after every session.

  Porting the ladder into the Node hook was rejected: it would duplicate ~150 lines
  of derivation logic in a second language (two sources of truth for one rule) and
  add work to the Stop chain, which this estate has measured saturating
  (12,237 ETIMEDOUT). Instead this sweep calls the sealed retroactive tool on a
  schedule. One implementation, zero cost on the hot path.

LIVENESS (why it is safe to run while panes are open)
  rename_sessions.py appends and then verifies prefix-byte-identity, reverting by
  truncation on mismatch. If claude.exe wrote to the same transcript inside that
  window, the revert would truncate away ITS line. So live sessions are excluded.

  The liveness signal is the launcher's own contract, not a re-derivation:
  bin/kclaude.ps1 writes %TEMP%\\kclaude-pane-<wrapperpid>.sid at start and removes
  it on exit (kclaude.ps1:336). An existing beacon therefore means an open pane.
  A beacon older than STALE_BEACON_DAYS is treated as debris from a crashed
  wrapper and ignored, so one crash cannot freeze the sweep permanently.

  Under-skipping risks truncation; over-skipping only defers a rename to tomorrow.
  The asymmetry is the whole reason this errs toward skipping.

  Beacons alone are NOT sufficient, and assuming they were is the bug this guard
  exists to close. Measured 2026-09-14: panes started outside bin/kclaude.ps1 run
  with wrapper_kind "none" and write no beacon at all -- the sweep's own session
  was one of them. So a second, wrapper-independent signal is required: any
  transcript whose .jsonl was written inside RECENT_WRITE_MINUTES is treated as
  live, because a session in use writes on every turn. The two signals fail in
  different ways, which is the point of having both.

EXIT CODES
  0 swept (or nothing to do)   1 the rename tool failed   2 the sweep itself failed
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
PP_ROOT = Path(__file__).resolve().parent.parent
RENAMER = PP_ROOT / "tools" / "rename_sessions.py"
LOG_DIR = PP_ROOT / "_logs"
LOG_FILE = LOG_DIR / "session_titles_sweep.log"

STALE_BEACON_DAYS = 7
BEACON_GLOB = "kclaude-pane-*.sid"
PROJECTS_ROOT = HOME / ".claude" / "projects"
RECENT_WRITE_MINUTES = 30


def temp_dir() -> Path:
    return Path(os.environ.get("TEMP") or os.environ.get("TMP") or "/tmp")


def live_session_ids() -> tuple[set[str], int, int]:
    """Session ids of panes that are currently open, per the launcher's beacons.

    Returns (sids, beacons_read, beacons_stale).
    """
    sids: set[str] = set()
    read = 0
    stale = 0
    cutoff = time.time() - STALE_BEACON_DAYS * 86400
    for path in sorted(temp_dir().glob(BEACON_GLOB)):
        try:
            if path.stat().st_mtime < cutoff:
                stale += 1
                continue
            obj = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            # An unreadable beacon is an unknown pane. Unknown means skip-worthy
            # only if we can name it, and we cannot -- so it is simply not counted.
            continue
        read += 1
        sid = obj.get("sid")
        if isinstance(sid, str) and sid.strip():
            sids.add(sid.strip())
    return sids, read, stale


def recently_written_session_ids() -> tuple[set[str], int]:
    """Sessions whose transcript was written very recently -- i.e. in use.

    Wrapper-independent, so it covers panes that write no beacon. The transcript
    filename is the session id, so this costs one stat() per file and no parsing.

    Returns (sids, transcripts_seen).
    """
    sids: set[str] = set()
    seen = 0
    cutoff = time.time() - RECENT_WRITE_MINUTES * 60
    try:
        project_dirs = [d for d in PROJECTS_ROOT.iterdir() if d.is_dir()]
    except OSError:
        return sids, 0
    for proj in project_dirs:
        try:
            entries = list(proj.glob("*.jsonl"))
        except OSError:
            continue
        for path in entries:
            seen += 1
            try:
                if path.stat().st_mtime >= cutoff:
                    sids.add(path.stem)
            except OSError:
                # Cannot stat it -> cannot prove it is idle -> treat as live.
                sids.add(path.stem)
    return sids, seen


def build_argv(skip: set[str], dry_run: bool) -> list[str]:
    argv = [sys.executable, str(RENAMER), "--all",
            "--dry-run" if dry_run else "--apply", "--sample", "0"]
    for sid in sorted(skip):
        argv += ["--skip-sid", sid]
    return argv


def log(line: str) -> None:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y-%m-%dT%H:%M:%S")
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(f"{stamp}  {line}\n")
    except OSError:
        pass


def main() -> int:
    dry_run = "--dry-run" in sys.argv

    if not RENAMER.is_file():
        log(f"FAIL renamer missing at {RENAMER}")
        print(f"session_titles_sweep: renamer not found: {RENAMER}", file=sys.stderr)
        return 2

    # Two independent liveness signals. A pane missed by one is caught by the
    # other: beacons miss wrapper-less panes, mtime misses a pane idle >30 min.
    by_beacon, beacons, stale = live_session_ids()
    by_write, transcripts = recently_written_session_ids()
    skip = by_beacon | by_write

    # The sweep's own session, when a human runs it from inside a pane.
    own = os.environ.get("PP_EVT_SID", "").strip()
    if own:
        skip.add(own)

    if not transcripts:
        # An empty projects tree is indistinguishable from an unreadable one, and
        # only one of them is safe to sweep under. Refuse rather than guess.
        log("FAIL no transcripts visible under "
            f"{PROJECTS_ROOT} -- refusing to sweep")
        print(f"session_titles_sweep: no transcripts under {PROJECTS_ROOT}",
              file=sys.stderr)
        return 2

    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    try:
        proc = subprocess.run(build_argv(skip, dry_run), cwd=str(PP_ROOT), env=env,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=900)
    except (OSError, subprocess.SubprocessError) as exc:
        log(f"FAIL renamer did not run: {exc.__class__.__name__}: {exc}")
        print(f"session_titles_sweep: {exc}", file=sys.stderr)
        return 2

    tail = [ln for ln in (proc.stdout or "").splitlines() if ln.strip()]
    # The last line is the tool's footer ("Re-run with --apply"), not its result.
    # Prefer the lines that actually carry numbers, so the log says what happened.
    marks = ("APPLIED:", "would be renamed", "Sessions scanned:")
    scored = [ln.strip() for ln in tail if any(m in ln for m in marks)]
    verdict = " | ".join(scored[-2:]) if scored else (tail[-1] if tail else "(no output)")

    mode = "dry-run" if dry_run else "apply"
    log(f"{mode} rc={proc.returncode} beacons={beacons} stale_beacons={stale} "
        f"transcripts={transcripts} skip_beacon={len(by_beacon)} "
        f"skip_recent={len(by_write)} skip_total={len(skip)} :: {verdict}")

    # stdout is what a human sees when running this by hand; keep it one screen.
    print(f"session_titles_sweep [{mode}] transcripts={transcripts} "
          f"beacons={beacons} stale={stale} "
          f"skipped_live={len(skip)} (beacon={len(by_beacon)}, recent={len(by_write)})")
    print(verdict)
    if proc.returncode != 0:
        err = (proc.stderr or "").strip()
        if err:
            print(err[-2000:], file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
