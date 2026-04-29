#!/usr/bin/env python3
"""Lazarus Pre-Reboot Arm v2 (MC-LAZ-25b)

Inventories every live session across every project via UNION of:
  - heartbeats: <project>/heartbeats/<sid>.lock with fresh mtime
  - transcripts: ~/.claude/projects/<project>/<sid>.jsonl with fresh mtime

Heartbeats only fire on PreToolUse, so an idle-but-alive Claude session
(window left open, no recent tool calls) shows NO heartbeat. Transcripts
get appended on every user message + tool result, so their mtime is a
better proxy for "recently active". Use both, OR them.

Force-enqueues each fresh session_id at the TOP of its project's
pending_resume.txt (de-duped, newest-first sorted by freshness, capped
at PENDING_CAP). Existing entries already in the queue but not in fresh
are preserved BELOW the fresh batch.

Backups every project's pre-arm state to:
  ~/.claude/lazarus/_backup_pre_reboot/<timestamp>/<project>/

Writes manifest:
  ~/.claude/lazarus/pre_reboot_manifest.json

ASCII-only output (cp1252 safe).
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

LAZARUS_DIR = Path.home() / ".claude" / "lazarus"
PROJECTS_DIR = Path.home() / ".claude" / "projects"
HEARTBEAT_WINDOW_SEC = 3600           # 1h — heartbeats are fresh-fire signals
TRANSCRIPT_WINDOW_SEC = 4 * 3600      # 4h — transcripts are append-on-activity signals
PENDING_CAP = 25
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)


def is_uuid(s: str) -> bool:
    return bool(UUID_RE.match(s))


now_local = datetime.now()
now_utc = datetime.now(timezone.utc)
now_ts = now_local.timestamp()
backup_dir = LAZARUS_DIR / "_backup_pre_reboot" / now_local.strftime("%Y%m%d_%H%M%S")
manifest_path = LAZARUS_DIR / "pre_reboot_manifest.json"

if not LAZARUS_DIR.exists():
    print(f"ERROR: {LAZARUS_DIR} does not exist", file=sys.stderr)
    sys.exit(1)

manifest: dict = {
    "created": now_utc.isoformat(),
    "host_now_local": now_local.isoformat(),
    "windows_sec": {
        "heartbeat": HEARTBEAT_WINDOW_SEC,
        "transcript": TRANSCRIPT_WINDOW_SEC,
    },
    "projects": {},
}

total_live = 0
total_transcript_only = 0

for project_dir in sorted(LAZARUS_DIR.iterdir()):
    if not project_dir.is_dir() or project_dir.name.startswith("_"):
        continue
    proj_id = project_dir.name
    transcript_dir = PROJECTS_DIR / proj_id

    # sid -> {"age_sec": int, "source": "heartbeat"|"transcript"|"both"}
    live: dict[str, dict] = {}

    # Pass 1: heartbeats
    hb_dir = project_dir / "heartbeats"
    if hb_dir.exists():
        for hb in hb_dir.iterdir():
            if not hb.is_file() or not hb.name.endswith(".lock"):
                continue
            if ".tmp." in hb.name:
                continue
            sid = hb.stem
            if not is_uuid(sid):
                continue
            age = int(now_ts - hb.stat().st_mtime)
            if age <= HEARTBEAT_WINDOW_SEC:
                live[sid] = {"age_sec": age, "source": "heartbeat"}

    # Pass 2: transcripts
    if transcript_dir.exists():
        for tr in transcript_dir.iterdir():
            if not tr.is_file() or not tr.name.endswith(".jsonl"):
                continue
            sid = tr.stem
            if not is_uuid(sid):
                continue
            age = int(now_ts - tr.stat().st_mtime)
            if age <= TRANSCRIPT_WINDOW_SEC:
                if sid in live:
                    live[sid]["source"] = "both"
                    if age < live[sid]["age_sec"]:
                        live[sid]["age_sec"] = age
                else:
                    live[sid] = {"age_sec": age, "source": "transcript"}

    if not live:
        continue

    # Sort newest-first by age
    fresh_sorted = sorted(
        [{"session_id": sid, "age_sec": v["age_sec"], "source": v["source"]} for sid, v in live.items()],
        key=lambda x: x["age_sec"],
    )

    # Backup current state
    backup_proj = backup_dir / proj_id
    backup_proj.mkdir(parents=True, exist_ok=True)
    for fname in ("pending_resume.txt", "bindings.json", "index.json"):
        src = project_dir / fname
        if src.exists():
            shutil.copy2(src, backup_proj / fname)

    # Read existing queue
    pending_path = project_dir / "pending_resume.txt"
    existing: list[str] = []
    if pending_path.exists():
        try:
            existing = [
                l.strip()
                for l in pending_path.read_text(encoding="utf-8").splitlines()
                if l.strip() and is_uuid(l.strip())
            ]
        except Exception:
            existing = []

    # Build new queue: fresh (newest-first) on top, then non-fresh existing preserved below
    fresh_ids = {f["session_id"] for f in fresh_sorted}
    non_fresh_existing = [u for u in existing if u not in fresh_ids]
    new_lines = [f["session_id"] for f in fresh_sorted] + non_fresh_existing
    if len(new_lines) > PENDING_CAP:
        new_lines = new_lines[:PENDING_CAP]

    # Atomic CRLF write (matches what the bat's findstr expects)
    tmp = pending_path.with_name(pending_path.name + ".tmp")
    payload = ("\r\n".join(new_lines) + "\r\n").encode("utf-8") if new_lines else b""
    tmp.write_bytes(payload)
    tmp.replace(pending_path)

    sources_count = {"heartbeat": 0, "transcript": 0, "both": 0}
    for f in fresh_sorted:
        sources_count[f["source"]] += 1

    manifest["projects"][proj_id] = {
        "fresh_sessions": fresh_sorted,
        "pending_resume_after": new_lines,
        "sources_count": sources_count,
    }
    total_live += len(fresh_sorted)
    total_transcript_only += sources_count["transcript"]

manifest["total_live_sessions"] = total_live
manifest["total_transcript_only_sessions"] = total_transcript_only
manifest["projects_with_live"] = len(manifest["projects"])
manifest["backup_dir"] = str(backup_dir)

manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

# ASCII-only summary print
print("=" * 70)
print(f"PRE-REBOOT ARM v2 COMPLETE")
print("=" * 70)
print(f"Total live sessions:           {total_live}")
print(f"Caught via transcript only:    {total_transcript_only} (would have been MISSED by heartbeat-only probe)")
print(f"Projects with live:            {len(manifest['projects'])}")
print(f"Backup dir:                    {backup_dir}")
print(f"Manifest:                      {manifest_path}")
print()
print("Per-project:")
for proj, data in manifest["projects"].items():
    short = proj if len(proj) <= 70 else proj[:67] + "..."
    n = len(data["fresh_sessions"])
    sc = data["sources_count"]
    print(f"  {short}")
    print(f"    fresh: {n}  (heartbeat={sc['heartbeat']} transcript={sc['transcript']} both={sc['both']})")
    print(f"    queue_size: {len(data['pending_resume_after'])}")
    for f in data["fresh_sessions"]:
        print(f"      > {f['session_id']}  age={f['age_sec']}s  src={f['source']}")
