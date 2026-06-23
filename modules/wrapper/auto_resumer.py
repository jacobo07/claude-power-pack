#!/usr/bin/env python3
"""auto_resumer.py -- W2: transcript-anchored auto-resume for kclaude.

Given a cwd, resolve the resumable Claude session and return the exact
`--resume <sid>` argument so the wrapper reopens the SAME conversation (no
"History restored" new session).

THE ONLY ANCHOR IS A TRANSCRIPT .jsonl ON DISK (UKDL
T-WRAPPER-TRANSCRIPT-ANCHOR-001). A session_id without its `<sid>.jsonl` is NOT
resumable. Registry / snapshot COUNTS are never used as the anchor -- the
snapshot accrues phantom null-sid "live" entries (feedback_cursor_reload_
persistent_sessions_pane_map). Disk is truth.

Source resolution order:
  1. `~/.claude/state/pane_map.json` (built by build_pane_map.ps1 from disk
     truth: sub-sessions filtered, human topics, recency-sorted) -- each
     candidate is RE-VERIFIED to still have its `<sid>.jsonl` on disk NOW
     (pane_map can be minutes stale).
  2. Fallback: a raw disk scan of the encoded-cwd projects dir, when pane_map
     is absent/empty.
Multiple sessions for one cwd -> most recent is chosen; the rest are returned
in `.others` (numbered by the caller / W6).

Fail-open: ANY error -> ResumeResult(resume_arg=None) (a new session; the
wrapper still launches claude).
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_PROJ_BASE = Path.home() / ".claude" / "projects"
DEFAULT_STATE_DIR = Path.home() / ".claude" / "state"


@dataclass
class ResumeResult:
    resume_arg: str | None              # "--resume <sid>" or None (new session)
    session_id: str | None
    others: list = field(default_factory=list)   # older candidates [{...}]
    source: str = ""                    # pane_map | disk | none | error


def _encode_cwd(cwd: str) -> str:
    """Claude Code project-dir encoding: every non-alphanumeric -> '-'.
    Matches build_pane_map.ps1 (`-replace '[^a-zA-Z0-9]','-'`)."""
    return re.sub(r"[^a-zA-Z0-9]", "-", cwd or "")


def _proj_dir(cwd: str, proj_base) -> Path:
    return Path(proj_base or DEFAULT_PROJ_BASE) / _encode_cwd(cwd)


def _jsonl_exists(cwd: str, sid: str, proj_base) -> bool:
    try:
        return (_proj_dir(cwd, proj_base) / f"{sid}.jsonl").is_file()
    except OSError:
        return False


def _disk_candidates(cwd: str, proj_base) -> list[dict]:
    """[{session_id, topic, lastActivity}] from disk transcripts, newest first.
    lastActivity is the file mtime ISO (string) so it sorts with pane_map's."""
    d = _proj_dir(cwd, proj_base)
    out: list[tuple[str, float]] = []
    if not d.is_dir():
        return []
    try:
        for p in d.glob("*.jsonl"):
            try:
                if p.is_file():
                    out.append((p.stem, p.stat().st_mtime))
            except OSError:
                continue
    except OSError:
        return []
    out.sort(key=lambda t: t[1], reverse=True)
    return [{"session_id": sid, "topic": "", "lastActivity": ""} for sid, _ in out]


def _panemap_candidates(cwd: str, state_dir, proj_base) -> list[dict]:
    """pane_map.json panes for this cwd, RE-VERIFIED on disk, newest first.
    [] when pane_map is absent/unreadable (caller falls back to disk)."""
    pj = Path(state_dir or DEFAULT_STATE_DIR) / "pane_map.json"
    if not pj.is_file():
        return []
    try:
        data = json.loads(pj.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return []
    cwd_l = (cwd or "").lower()
    cands: list[dict] = []
    for pane in (data.get("panes") or []):
        if (pane.get("cwd") or "").lower() != cwd_l:
            continue
        sid = pane.get("sessionId")
        if not sid or not _jsonl_exists(cwd, sid, proj_base):
            continue  # transcript-on-disk anchor: skip if the .jsonl is gone
        cands.append({
            "session_id": sid,
            "topic": pane.get("topic", ""),
            "lastActivity": pane.get("lastActivity", ""),
        })
    cands.sort(key=lambda c: c["lastActivity"], reverse=True)
    return cands


def list_candidates(cwd: str, state_dir=None, proj_base=None) -> list[dict]:
    """Public: transcript-verified resumable candidates for `cwd`, newest first.

    pane_map.json primary (each `<sid>.jsonl` re-verified on disk), raw disk
    scan fallback. Each item: {session_id, topic, lastActivity}. Reused by W4
    (repo_coordinator) for the same anchor guarantees as W2. Fail-open [].
    """
    try:
        cands = _panemap_candidates(cwd, state_dir, proj_base)
        if cands:
            return cands
        return _disk_candidates(cwd, proj_base)
    except Exception:  # noqa: BLE001
        return []


def get_resume(cwd: str, state_dir=None, proj_base=None) -> ResumeResult:
    """Resolve the resumable session for `cwd`. Fail-open."""
    try:
        cands = _panemap_candidates(cwd, state_dir, proj_base)
        source = "pane_map"
        if not cands:
            cands = _disk_candidates(cwd, proj_base)
            source = "disk" if cands else "none"
        if not cands:
            return ResumeResult(None, None, [], "none")
        best = cands[0]
        return ResumeResult(
            resume_arg=f"--resume {best['session_id']}",
            session_id=best["session_id"],
            others=cands[1:],
            source=source,
        )
    except Exception:  # noqa: BLE001 -- fail-open: never block the launch
        return ResumeResult(None, None, [], "error")


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--cwd", default=None)
    args = ap.parse_args(argv)
    r = get_resume(args.cwd or os.getcwd())
    if r.resume_arg:
        print(r.resume_arg)
        if r.others:
            print(f"# (+{len(r.others)} older session(s) for this repo)")
    else:
        print("# new session (no transcript on disk for this cwd)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
