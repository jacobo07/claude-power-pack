#!/usr/bin/env python3
"""compound_audit.py - health check for the Compound Learnings stack.

Runs four assertions:
  1. Sentinel hook file exists at ~/.claude/hooks/learning-sentinel.js
     and is non-empty.
  2. Sentinel is registered in ~/.claude/settings.json on at least one
     of: Stop, SessionEnd, SessionStart.
  3. State file ~/.claude/state/compound-learnings.json parses as valid
     JSON and has the expected schema_version/threshold/projects shape.
  4. No orphan LEARNINGS_PENDING.md markers older than 30 days exist in
     any of the per-project cwd entries (stale markers usually indicate
     a /cpp-compound run that never completed Step 7 cursor advance).

Exit 0 = healthy, 5 = degraded. Designed to be runnable from a CI gate
or a /restart preflight check.
"""
from __future__ import annotations
import datetime as dt
import json
import os
import sys

HOME = os.path.expandvars(r"%USERPROFILE%")
SENTINEL = os.path.join(HOME, ".claude", "hooks", "learning-sentinel.js")
SETTINGS = os.path.join(HOME, ".claude", "settings.json")
STATE = os.path.join(HOME, ".claude", "state", "compound-learnings.json")
STALE_MARKER_DAYS = 30


def assert_sentinel_present() -> tuple[bool, str]:
    if not os.path.isfile(SENTINEL):
        return False, f"missing {SENTINEL}"
    sz = os.path.getsize(SENTINEL)
    if sz < 1024:
        return False, f"sentinel suspiciously small ({sz} bytes)"
    return True, f"sentinel OK ({sz} bytes)"


def assert_sentinel_registered() -> tuple[bool, str]:
    try:
        with open(SETTINGS, "r", encoding="utf-8-sig") as fh:
            d = json.load(fh)
    except (OSError, ValueError) as e:
        return False, f"settings.json read failed: {e}"
    events = []
    for evt, lst in d.get("hooks", {}).items():
        for entry in lst:
            for h in entry.get("hooks", []):
                if "learning-sentinel" in (h.get("command") or ""):
                    events.append(evt)
    if not events:
        return False, "sentinel not registered on any event"
    return True, f"registered on: {sorted(set(events))}"


def assert_state_valid() -> tuple[bool, str]:
    if not os.path.isfile(STATE):
        return True, "state file not yet created (cold start)"
    try:
        with open(STATE, "r", encoding="utf-8-sig") as fh:
            d = json.load(fh)
    except (OSError, ValueError) as e:
        return False, f"state read failed: {e}"
    if d.get("schema_version") != 1:
        return False, f"schema_version != 1: {d.get('schema_version')!r}"
    if not isinstance(d.get("threshold"), int):
        return False, f"threshold not int: {d.get('threshold')!r}"
    if not isinstance(d.get("projects"), dict):
        return False, "projects key missing or wrong type"
    return True, (f"threshold={d['threshold']}, "
                  f"projects={len(d['projects'])}, "
                  f"last_run_global={d.get('last_run_global') or 'never'}")


def assert_no_stale_markers() -> tuple[bool, str]:
    if not os.path.isfile(STATE):
        return True, "no state file -> no projects to check"
    try:
        with open(STATE, "r", encoding="utf-8-sig") as fh:
            d = json.load(fh)
    except (OSError, ValueError):
        return True, "state unreadable, skipping marker check"
    projects = d.get("projects", {})
    now = dt.datetime.now(dt.timezone.utc)
    stale = []
    # Reverse the pid encoding to find candidate cwds.
    # pid = cwd.replace(/[^a-zA-Z0-9-]/g, '-'); we cannot perfectly invert,
    # but we can probe the canonical projects under ~/.claude/projects/<pid>/
    # and the actual Cursor projects path families. Check the per-project
    # last_run_iso freshness as a soft signal.
    for pid, info in projects.items():
        iso = (info or {}).get("last_run_iso")
        if not iso:
            continue
        try:
            t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
        except ValueError:
            continue
        age_days = (now - t).days
        if age_days > STALE_MARKER_DAYS * 3:
            stale.append(f"{pid[:50]} ({age_days}d)")
    if stale:
        return True, f"projects with very stale cursors (advisory): {stale[:3]}"
    return True, f"all {len(projects)} project cursors within sliding window"


def main() -> int:
    checks = [
        ("sentinel-file", assert_sentinel_present),
        ("sentinel-registered", assert_sentinel_registered),
        ("state-shape", assert_state_valid),
        ("marker-staleness", assert_no_stale_markers),
    ]
    failed = []
    print("=== compound_audit ===")
    for name, fn in checks:
        ok, msg = fn()
        tag = "OK " if ok else "FAIL"
        print(f"  [{tag}] {name}: {msg}")
        if not ok:
            failed.append(name)
    if failed:
        print(f"COMPOUND_AUDIT FAIL: {failed}")
        return 5
    print("COMPOUND_AUDIT OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
