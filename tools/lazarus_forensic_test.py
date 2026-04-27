#!/usr/bin/env python3
"""
lazarus_forensic_test.py — MC-LAZ-05: forensic recovery validation.

Builds a synthetic Lazarus state in an isolated temp HOME, runs the
lister against it, and asserts the contract holds:

  1. A stale-heartbeat session is classified as CRASHED.
  2. A clean-exit session is classified as CLEAN.
  3. A pending_resume.txt entry is classified as CRASHED.
  4. The freshest-heartbeat session in the cwd's project is detected
     as CURRENT and DROPPED from the listing under default
     --exclude-current.
  5. With --include-current, that same session is visible and tagged
     CURRENT (status column).
  6. The Restoration paths block emits one `claude --resume <sid>` line
     per LIVE/CRASHED row, never for CURRENT rows.
  7. terminal-keys binding (work→sid) is surfaced under the project
     header.

The test never touches the real ~/.claude/lazarus/ — it constructs a
sandbox HOME under a tempdir, runs the lister with HOME overridden,
and tears down on exit. Exit code 0 = green, 1 = any assertion failed.

Usage:
  python tools/lazarus_forensic_test.py
  python tools/lazarus_forensic_test.py --verbose
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Windows default stdout is cp1252 — the lister output we display in
# verbose mode contains box-drawing / bullet glyphs that crash on
# encode. Reconfigure to UTF-8 so the test runner can faithfully echo
# any output (lister output, assertion bullets, etc.).
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass


THIS_DIR = Path(__file__).resolve().parent
LISTER = THIS_DIR / "lazarus_revive_all.py"


def now_iso(offset_seconds: float = 0.0) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)) \
        .isoformat().replace("+00:00", "Z")


def sanitize_project_id(cwd: str) -> str:
    return re.sub(r"[^a-zA-Z0-9-]", "-", cwd)


def write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def touch_mtime(p: Path, age_seconds: float) -> None:
    """Set the mtime of a path to N seconds in the past."""
    target = time.time() - age_seconds
    os.utime(p, (target, target))


def build_fixture(home: Path, cwd_project: str) -> dict:
    """Write a synthetic Lazarus state and return the assertion plan.

    Layout:
      home/.claude/lazarus/<cwd_project>/
        sessions/{current,live,crashed,clean}.json
        heartbeats/{current,live,crashed}.lock
        index.json   — clean exit for 'clean'
        pending_resume.txt  — entry for 'pending'
        bindings.json  — work→current, plan→live
      home/.claude/lazarus/global_index.json
    """
    lazarus = home / ".claude" / "lazarus"
    proj_dir = lazarus / cwd_project
    sessions = proj_dir / "sessions"
    heartbeats = proj_dir / "heartbeats"
    sessions.mkdir(parents=True, exist_ok=True)
    heartbeats.mkdir(parents=True, exist_ok=True)

    proj_path = "/synthetic/forensic/project"

    # 1) CURRENT — fresh heartbeat (5s old)
    cur_sid = "sid-current-A"
    write_json(sessions / f"{cur_sid}.json", {
        "project_id": cwd_project,
        "project_path": proj_path,
        "session_id": cur_sid,
        "timestamp": now_iso(-5),
        "branch": "main",
        "uncommitted_files": ["a.py", "b.py"],
        "active_plan": None,
        "last_intent": ["typing on this terminal"],
        "tool_summary": {"Edit": 3},
    })
    cur_lock = heartbeats / f"{cur_sid}.lock"
    write_json(cur_lock, {
        "session_id": cur_sid,
        "pid": 12345,
        "timestamp": now_iso(-5),
        "cwd": proj_path,
        "last_tool": "Edit",
        "terminal_hint": "PPID=12345",
    })
    touch_mtime(cur_lock, 5)

    # 2) LIVE (other terminal) — heartbeat 90s old (within live-window=300s,
    #    outside current-window=90s default)
    live_sid = "sid-live-B"
    write_json(sessions / f"{live_sid}.json", {
        "project_id": cwd_project,
        "project_path": proj_path,
        "session_id": live_sid,
        "timestamp": now_iso(-95),
        "branch": "feature/x",
        "uncommitted_files": ["c.py"],
        "last_intent": ["another window"],
    })
    live_lock = heartbeats / f"{live_sid}.lock"
    write_json(live_lock, {
        "session_id": live_sid,
        "pid": 22222,
        "timestamp": now_iso(-95),
        "cwd": proj_path,
        "last_tool": "Read",
        "terminal_hint": "PPID=22222",
    })
    touch_mtime(live_lock, 95)

    # 3) CRASHED — stale heartbeat (10 min old)
    crash_sid = "sid-crashed-C"
    write_json(sessions / f"{crash_sid}.json", {
        "project_id": cwd_project,
        "project_path": proj_path,
        "session_id": crash_sid,
        "timestamp": now_iso(-600),
        "branch": "main",
        "uncommitted_files": [],
        "last_intent": ["lost mid-edit"],
    })
    crash_lock = heartbeats / f"{crash_sid}.lock"
    write_json(crash_lock, {
        "session_id": crash_sid,
        "pid": 33333,
        "timestamp": now_iso(-600),
        "cwd": proj_path,
        "last_tool": "Bash",
    })
    touch_mtime(crash_lock, 600)

    # 4) CLEAN — exited cleanly via Stop hook; no heartbeat
    clean_sid = "sid-clean-D"
    write_json(sessions / f"{clean_sid}.json", {
        "project_id": cwd_project,
        "project_path": proj_path,
        "session_id": clean_sid,
        "timestamp": now_iso(-3600),
        "branch": "main",
    })

    # index.json — record clean exit for D, live for B/C
    write_json(proj_dir / "index.json", {
        "project_id": cwd_project,
        "project_path": proj_path,
        "sessions": [
            {"session_id": cur_sid, "started": now_iso(-100),
             "last_seen": now_iso(-5), "status": "live", "terminal_hint": "PPID=12345"},
            {"session_id": live_sid, "started": now_iso(-200),
             "last_seen": now_iso(-95), "status": "live", "terminal_hint": "PPID=22222"},
            {"session_id": crash_sid, "started": now_iso(-1200),
             "last_seen": now_iso(-600), "status": "live"},
            {"session_id": clean_sid, "started": now_iso(-7200),
             "last_seen": now_iso(-3600), "ended": now_iso(-3600),
             "status": "clean_exit"},
        ],
        "updated": now_iso(),
    })

    # pending_resume.txt — older crashed session reference
    pending_sid = "sid-pending-E"
    (proj_dir / "pending_resume.txt").write_text(pending_sid + "\n", encoding="utf-8")
    write_json(sessions / f"{pending_sid}.json", {
        "project_id": cwd_project,
        "project_path": proj_path,
        "session_id": pending_sid,
        "timestamp": now_iso(-7200),
        "branch": "main",
    })

    # bindings.json — terminal-key map (MC-LAZ-04)
    write_json(proj_dir / "bindings.json", {
        "terminal_keys": {"work": cur_sid, "plan": live_sid},
        "updated": now_iso(),
    })

    # global_index.json — register the project
    write_json(lazarus / "global_index.json", {
        cwd_project: {"project_path": proj_path, "timestamp": now_iso()},
    })

    return {
        "lazarus_dir": lazarus,
        "proj_dir": proj_dir,
        "proj_path": proj_path,
        "sessions": {
            "current": cur_sid,
            "live": live_sid,
            "crashed": crash_sid,
            "clean": clean_sid,
            "pending": pending_sid,
        },
    }


def run_lister(home: Path, proj_path: str, *extra_args: str) -> tuple[int, str, str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)  # Windows expanduser fallback
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [sys.executable, str(LISTER), "--cwd", proj_path, *extra_args]
    p = subprocess.run(cmd, capture_output=True, text=True, env=env, encoding="utf-8")
    return p.returncode, p.stdout, p.stderr


# ─────────────────────────── assertions ───────────────────────────


class Failure(Exception):
    pass


def expect(label: str, cond: bool, evidence: str = "") -> None:
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {label}")
    if not cond:
        if evidence:
            print(f"        evidence: {evidence}")
        raise Failure(label)


def assert_default_run(stdout: str, sids: dict) -> None:
    print("Phase 1 — default run (--exclude-current ON)")
    expect("CURRENT row excluded from listing",
           sids["current"] not in stdout,
           f"unexpected sid={sids['current']} in stdout")
    expect("LIVE row present", sids["live"] in stdout)
    expect("CRASHED row present", sids["crashed"] in stdout)
    expect("PENDING (CRASHED via pending_resume) row present",
           sids["pending"] in stdout)
    expect("CLEAN row present (informational)", sids["clean"] in stdout)
    expect("Restoration path emits LIVE resume command",
           f"claude --resume {sids['live']}" in stdout)
    expect("Restoration path emits CRASHED resume command",
           f"claude --resume {sids['crashed']}" in stdout)
    expect("Restoration path does NOT suggest reviving CURRENT",
           f"claude --resume {sids['current']}" not in stdout)
    expect("Restoration path does NOT suggest reviving CLEAN",
           f"claude --resume {sids['clean']}" not in stdout)
    expect("terminal-keys map surfaced under project header",
           "terminal-keys:" in stdout and "work" in stdout)


def assert_include_run(stdout: str, sids: dict) -> None:
    print("Phase 2 — --include-current run")
    expect("CURRENT row visible when included",
           sids["current"] in stdout)
    expect("CURRENT status tag emitted",
           "CURRENT" in stdout)
    expect("[CURRENT] inline tag emitted",
           "[CURRENT]" in stdout)
    expect("Even with --include-current, no resume command for it",
           f"claude --resume {sids['current']}" not in stdout)


def assert_json_run(stdout: str, sids: dict) -> None:
    print("Phase 3 — --json shape (default --exclude-current)")
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as e:
        raise Failure(f"JSON parse failed: {e}")
    expect("JSON has 'header' object", isinstance(payload.get("header"), dict))
    expect("JSON has 'rows' list", isinstance(payload.get("rows"), list))
    sids_in = {r["session_id"] for r in payload["rows"]}
    expect("CURRENT sid absent in --exclude-current JSON",
           sids["current"] not in sids_in)
    expect("LIVE sid present in JSON", sids["live"] in sids_in)
    expect("CRASHED sid present in JSON", sids["crashed"] in sids_in)
    expect("Header reflects exclude_current=True",
           payload["header"].get("exclude_current") is True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Lazarus forensic recovery test")
    parser.add_argument("--verbose", action="store_true",
                        help="dump full lister stdout for each phase")
    parser.add_argument("--keep", action="store_true",
                        help="don't delete the sandbox HOME on exit (debug aid)")
    args = parser.parse_args()

    if not LISTER.exists():
        print(f"FATAL: lister not found at {LISTER}", file=sys.stderr)
        return 2

    sandbox = Path(tempfile.mkdtemp(prefix="lazarus-forensic-"))
    print(f"Sandbox HOME: {sandbox}")

    try:
        proj_path = "/synthetic/forensic/project"
        cwd_project = sanitize_project_id(proj_path)
        plan = build_fixture(sandbox, cwd_project)
        sids = plan["sessions"]

        # Phase 1: default
        rc, out, err = run_lister(sandbox, proj_path, "--mode", "all", "--include-stale")
        if args.verbose:
            print("--- stdout (phase 1) ---\n" + out)
            if err:
                print("--- stderr ---\n" + err)
        if rc != 0:
            print(f"FATAL: lister exit {rc} (stderr: {err})", file=sys.stderr)
            return 2
        assert_default_run(out, sids)

        # Phase 2: --include-current
        rc, out, err = run_lister(
            sandbox, proj_path,
            "--mode", "all", "--include-stale", "--include-current",
        )
        if args.verbose:
            print("--- stdout (phase 2) ---\n" + out)
        if rc != 0:
            print(f"FATAL: include-current exit {rc} (stderr: {err})", file=sys.stderr)
            return 2
        assert_include_run(out, sids)

        # Phase 3: --json
        rc, out, err = run_lister(
            sandbox, proj_path,
            "--mode", "all", "--include-stale", "--json",
        )
        if rc != 0:
            print(f"FATAL: json exit {rc} (stderr: {err})", file=sys.stderr)
            return 2
        assert_json_run(out, sids)

        print("\nALL FORENSIC ASSERTIONS PASS — Lazarus restore contract verified.")
        return 0

    except Failure as f:
        print(f"\nFORENSIC TEST FAILED — {f}", file=sys.stderr)
        return 1
    finally:
        if not args.keep:
            shutil.rmtree(sandbox, ignore_errors=True)
        else:
            print(f"(sandbox kept at {sandbox} — clean up manually)")


if __name__ == "__main__":
    sys.exit(main())
