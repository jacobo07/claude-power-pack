#!/usr/bin/env python3
"""resume_reindex.py - native /resume chronology health scan + repair.

Root cause of "recently-touched threads hidden from /resume" (sealed
2026-05-16): `hooks/resume-hide-live.js` renames `<uuid>.jsonl` ->
`<uuid>.jsonl.live` to hide LIVE sessions from the native picker, then
restores stale ones on the next SessionStart. If that hook crashes or a
pane dies mid-cloak, a `.jsonl.live` whose session is dead is left
orphaned -> the thread vanishes from /resume even though it is recent.

This tool is a MANUAL SUPERSET of the hook's orphan-cleanup pass. It uses
the IDENTICAL liveness contract so the two restorers can never disagree
(audit gaps #6, #7):

  - heartbeat lock = ~/.claude/lazarus/<proj>/heartbeats/<uuid>.lock
  - HEARTBEAT_STALE_MS = 60000 (12x the ~5s heartbeat cadence)
  - missing lock => treated as STALE (matches resume-hide-live.js:74)
  - no-clobber: restore only if <uuid>.jsonl does NOT already exist
    (matches resume-hide-live.js:104)
  - rename only; ZERO deletion; idempotent

Secret-safe (audit gap #8): ~/.claude/history.jsonl contains live tokens
in `display` fields. This tool NEVER reads or prints session/`display`
content - only structural counts and UUID stems. The history monotonicity
audit reads a fixed-length byte snapshot, drops the final possibly-partial
line, and parses ONLY the `timestamp` and `sessionId` keys.
"""
from __future__ import annotations

import argparse
import json
import os
import time

HOME = os.path.expanduser("~")
PROJECTS_DIR = os.path.join(HOME, ".claude", "projects")
LAZARUS_DIR = os.path.join(HOME, ".claude", "lazarus")
HISTORY = os.path.join(HOME, ".claude", "history.jsonl")
HEARTBEAT_STALE_MS = 60 * 1000
LIVE_SUFFIX = ".jsonl.live"


def _heartbeat_stale(proj_name: str, uuid: str) -> bool:
    """Identical contract to resume-hide-live.js. Missing lock => stale."""
    lock = os.path.join(LAZARUS_DIR, proj_name, "heartbeats", f"{uuid}.lock")
    try:
        st = os.stat(lock)
    except OSError:
        return True  # no heartbeat file => treat as stale (hook line 74)
    age_ms = (time.time() - st.st_mtime) * 1000.0
    return age_ms > HEARTBEAT_STALE_MS


def scan_orphans() -> dict:
    total = 0
    stale = 0
    fresh = 0
    clobber_blocked = 0
    restorable: list[tuple[str, str, str]] = []
    if not os.path.isdir(PROJECTS_DIR):
        return {"projects_dir_missing": True}
    for proj_name in os.listdir(PROJECTS_DIR):
        proj_path = os.path.join(PROJECTS_DIR, proj_name)
        if not os.path.isdir(proj_path):
            continue
        for fn in os.listdir(proj_path):
            if not fn.endswith(LIVE_SUFFIX):
                continue
            total += 1
            uuid = fn[: -len(LIVE_SUFFIX)]
            if not _heartbeat_stale(proj_name, uuid):
                fresh += 1
                continue
            stale += 1
            restored = os.path.join(proj_path, f"{uuid}.jsonl")
            if os.path.exists(restored):
                clobber_blocked += 1
                continue
            restorable.append(
                (proj_name, os.path.join(proj_path, fn), restored))
    return {
        "total_live": total,
        "fresh_keep_cloaked": fresh,
        "stale": stale,
        "clobber_blocked": clobber_blocked,
        "restorable": restorable,
    }


def repair(restorable: list[tuple[str, str, str]]) -> int:
    done = 0
    for proj_name, live_path, restored in restorable:
        if os.path.exists(restored):  # re-check: zero-clobber, TOCTOU guard
            continue
        try:
            os.rename(live_path, restored)
            done += 1
            print(f"  restored {proj_name}/{os.path.basename(restored)}")
        except OSError as e:
            print(f"  restore-failed {proj_name}/"
                  f"{os.path.basename(live_path)}: {e}")
    return done


def history_monotonicity() -> dict:
    """Fixed-snapshot, secret-safe. Reads only timestamp/sessionId keys."""
    if not os.path.isfile(HISTORY):
        return {"history_missing": True}
    snap_len = os.path.getsize(HISTORY)
    with open(HISTORY, "rb") as fh:
        raw = fh.read(snap_len)
    lines = raw.split(b"\n")
    if lines and lines[-1] != b"":
        lines = lines[:-1]  # drop final possibly-partial line (live append)
    prev_ts = None
    inversions = 0
    first_inversion_idx = -1
    parsed = 0
    distinct_sessions: set[str] = set()
    for idx, ln in enumerate(lines):
        ln = ln.strip()
        if not ln:
            continue
        try:
            obj = json.loads(ln)
        except ValueError:
            continue
        ts = obj.get("timestamp")
        sid = obj.get("sessionId")
        if isinstance(sid, str):
            distinct_sessions.add(sid)
        if not isinstance(ts, (int, float)):
            continue
        parsed += 1
        if prev_ts is not None and ts < prev_ts:
            inversions += 1
            if first_inversion_idx < 0:
                first_inversion_idx = idx
        prev_ts = ts
    return {
        "lines_scanned": len(lines),
        "entries_parsed": parsed,
        "distinct_sessions": len(distinct_sessions),
        "timestamp_inversions": inversions,
        "first_inversion_line": first_inversion_idx,
        "monotonic": inversions == 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="native /resume chronology health scan + repair")
    ap.add_argument("--repair", action="store_true",
                    help="rename stale orphan .jsonl.live -> .jsonl "
                         "(rename only, zero deletion, no-clobber)")
    a = ap.parse_args()

    s = scan_orphans()
    if s.get("projects_dir_missing"):
        print("resume_reindex: ~/.claude/projects missing")
        return 0
    print(f"orphan-scan: total_live={s['total_live']} "
          f"fresh_cloaked={s['fresh_keep_cloaked']} "
          f"stale={s['stale']} clobber_blocked={s['clobber_blocked']} "
          f"restorable={len(s['restorable'])}")

    h = history_monotonicity()
    if h.get("history_missing"):
        print("history: ~/.claude/history.jsonl missing")
    else:
        print(f"history: lines={h['lines_scanned']} "
              f"parsed={h['entries_parsed']} "
              f"sessions={h['distinct_sessions']} "
              f"inversions={h['timestamp_inversions']} "
              f"monotonic={h['monotonic']} "
              f"first_inversion_line={h['first_inversion_line']}")

    if a.repair:
        n = repair(s["restorable"])
        print(f"repair: restored={n} (rerun is idempotent: 0 on clean)")
    else:
        print("dry-run (pass --repair to resurface stale hidden threads)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
