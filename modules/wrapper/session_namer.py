#!/usr/bin/env python3
"""session_namer.py -- W3: name a newly-launched session in pane_map fast.

At launch of a NEW (non --resume) session, the transcript .jsonl does not exist
yet (~1-2 min lag; UKDL T-RESTORE-STALE-SID-001), so build_pane_map.ps1 -- which
derives pane_map from DISK TRUTH -- cannot see the session for minutes. This
fills that <10s gap from the FAST source: session_snapshot.json, written by the
SessionStart hub (session_start_hub.js -> snapshot.py) within seconds, carrying
the live session_id + cwd.

W3 therefore:
  1. polls session_snapshot.json for a session_id on this cwd that was NOT
     present before launch (timeout 10s, interval 500ms),
  2. derives a label = repo-leaf + git subject (`git -C cwd log -1 --format=%s`;
     git failure -> repo-leaf only),
  3. writes a DURABLE record to wrapper_session_names.json (sid -> {cwd, label,
     updated_at}) -- this is the authoritative wrapper store, never clobbered,
  4. appends a marked fast-path block to pane_map.md so the new pane is visible
     immediately (bridges until build_pane_map regenerates from disk).

--resume case: no polling; just bump `updated_at` for the known sid.

Fail-open: ANY error -> no-op (the launch already happened; naming is cosmetic).
All time / git / snapshot reads are injectable so the done-gate is hermetic and
instant (no real sleeps).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_STATE_DIR = Path.home() / ".claude" / "state"
NAMES_STORE = "wrapper_session_names.json"
PANE_MAP_MD = "pane_map.md"
SNAPSHOT = "session_snapshot.json"

# Markers delimiting the wrapper-owned fast-path block inside pane_map.md.
# build_pane_map.ps1 owns the rest of the file (disk-truth regeneration); this
# block is the <10s bridge and is rewritten idempotently per sid.
_BLOCK_START = "<!-- kclaude-fastpath:start -->"
_BLOCK_END = "<!-- kclaude-fastpath:end -->"


@dataclass
class NameResult:
    session_id: str | None
    label: str | None
    source: str           # named | resume-touch | timeout | error | skip


def _iso(now: datetime) -> str:
    return now.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: Path, default):
    try:
        if not path.is_file():
            return default
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return default


def _atomic_write(path: Path, text: str) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(text, encoding="utf-8", newline="\n")
        os.replace(tmp, path)
        return True
    except OSError:
        return False


def derive_label(cwd: str, git_subject_fn=None) -> str:
    """repo-leaf + ': ' + git subject; fail-open to repo-leaf only."""
    repo = Path(cwd).name or cwd or "session"
    try:
        subj = (git_subject_fn or _git_subject)(cwd)
    except Exception:  # noqa: BLE001
        subj = None
    subj = (subj or "").strip()
    if subj:
        if len(subj) > 60:
            subj = subj[:60] + "..."
        return f"{repo}: {subj}"
    return repo


def _git_subject(cwd: str) -> str | None:
    """`git -C <cwd> log -1 --format=%s`. None on any failure (not a repo,
    git absent, timeout). Tries the Program Files absolute path first (this
    Windows host keeps git off the -NonInteractive PATH)."""
    exe = r"C:\Program Files\Git\cmd\git.exe"
    git = exe if os.path.isfile(exe) else "git"
    try:
        out = subprocess.run(
            [git, "-C", cwd, "log", "-1", "--format=%s"],
            capture_output=True, text=True, timeout=4)
        if out.returncode == 0:
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def _snapshot_sids_for_cwd(snapshot_path: Path, cwd: str,
                           snapshot_reader=None) -> dict:
    """{session_id: since} for panes whose cwd matches (case-insensitive)."""
    data = (snapshot_reader() if snapshot_reader
            else _read_json(snapshot_path, []))
    out: dict[str, str] = {}
    cwd_l = (cwd or "").lower()
    for pane in (data or []):
        if not isinstance(pane, dict):
            continue
        if (pane.get("cwd") or "").lower() != cwd_l:
            continue
        sid = pane.get("session_id")
        if sid:
            out[sid] = pane.get("since", "")
    return out


def poll_new_sid(cwd: str, known_sids, *, snapshot_path: Path,
                 timeout_s: float = 10.0, interval_s: float = 0.5,
                 snapshot_reader=None, sleep_fn=None, clock=None) -> str | None:
    """Return the first session_id on `cwd` not in `known_sids`, or None on
    timeout. clock/sleep_fn injectable for instant hermetic tests."""
    known = set(known_sids or ())
    clock = clock or time.monotonic
    sleep_fn = sleep_fn or time.sleep
    deadline = clock() + timeout_s
    while True:
        sids = _snapshot_sids_for_cwd(snapshot_path, cwd, snapshot_reader)
        fresh = {s: since for s, since in sids.items() if s not in known}
        if fresh:
            # newest by `since` if present, else arbitrary-but-stable
            return sorted(fresh.items(), key=lambda kv: kv[1], reverse=True)[0][0]
        if clock() >= deadline:
            return None
        sleep_fn(interval_s)


def _update_names_store(store_path: Path, sid: str, cwd: str, label: str,
                        now: datetime) -> None:
    store = _read_json(store_path, {})
    if not isinstance(store, dict):
        store = {}
    store[sid] = {"cwd": cwd, "label": label, "updated_at": _iso(now)}
    _atomic_write(store_path, json.dumps(store, ensure_ascii=False, indent=2))


def _render_fastpath_block(store: dict) -> str:
    lines = [_BLOCK_START,
             "## kclaude fast-path (bridges until build_pane_map regenerates "
             "from disk)", ""]
    # newest updated_at first
    rows = sorted(store.items(), key=lambda kv: kv[1].get("updated_at", ""),
                  reverse=True)
    for sid, rec in rows:
        lines.append(f"- **{rec.get('label', sid)}** "
                     f"(updated {rec.get('updated_at', '?')})")
        lines.append(f"  - `cd \"{rec.get('cwd', '')}\" ; "
                     f"claude --resume {sid}`")
    lines.append(_BLOCK_END)
    return "\n".join(lines) + "\n"


def _write_pane_map_block(pane_map_path: Path, store: dict) -> None:
    """Idempotently replace the wrapper fast-path block in pane_map.md.
    Creates the file with just the block if it does not exist."""
    block = _render_fastpath_block(store)
    existing = ""
    try:
        if pane_map_path.is_file():
            existing = pane_map_path.read_text(encoding="utf-8-sig")
    except OSError:
        existing = ""
    if _BLOCK_START in existing and _BLOCK_END in existing:
        pre = existing.split(_BLOCK_START, 1)[0]
        post = existing.split(_BLOCK_END, 1)[1]
        new = pre + block + post
    else:
        sep = "" if existing.endswith("\n") or not existing else "\n"
        new = existing + sep + "\n" + block
    _atomic_write(pane_map_path, new)


def name_session(cwd: str, known_sids, *, state_dir=None, timeout_s: float = 10.0,
                 interval_s: float = 0.5, git_subject_fn=None,
                 snapshot_reader=None, sleep_fn=None, clock=None,
                 now: datetime | None = None) -> NameResult:
    """Poll for the new sid, derive a label, persist it. Fail-open."""
    try:
        sd = Path(state_dir or DEFAULT_STATE_DIR)
        now = now or datetime.now(timezone.utc)
        sid = poll_new_sid(cwd, known_sids, snapshot_path=sd / SNAPSHOT,
                           timeout_s=timeout_s, interval_s=interval_s,
                           snapshot_reader=snapshot_reader, sleep_fn=sleep_fn,
                           clock=clock)
        if not sid:
            return NameResult(None, None, "timeout")
        label = derive_label(cwd, git_subject_fn)
        _update_names_store(sd / NAMES_STORE, sid, cwd, label, now)
        store = _read_json(sd / NAMES_STORE, {})
        _write_pane_map_block(sd / PANE_MAP_MD, store)
        return NameResult(sid, label, "named")
    except Exception:  # noqa: BLE001 -- naming is cosmetic, never block
        return NameResult(None, None, "error")


def touch_resume(sid: str, cwd: str, *, state_dir=None,
                 now: datetime | None = None) -> NameResult:
    """--resume path: bump updated_at for a known sid (keep its label)."""
    try:
        sd = Path(state_dir or DEFAULT_STATE_DIR)
        now = now or datetime.now(timezone.utc)
        store = _read_json(sd / NAMES_STORE, {})
        if not isinstance(store, dict):
            store = {}
        rec = store.get(sid) or {}
        label = rec.get("label") or derive_label(cwd)
        store[sid] = {"cwd": rec.get("cwd", cwd), "label": label,
                      "updated_at": _iso(now)}
        _atomic_write(sd / NAMES_STORE,
                      json.dumps(store, ensure_ascii=False, indent=2))
        _write_pane_map_block(sd / PANE_MAP_MD, store)
        return NameResult(sid, label, "resume-touch")
    except Exception:  # noqa: BLE001
        return NameResult(None, None, "error")


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--cwd", default=None)
    ap.add_argument("--known", default="", help="comma-sep sids present pre-launch")
    ap.add_argument("--resume-sid", default=None)
    ap.add_argument("--timeout", type=float, default=10.0)
    args = ap.parse_args(argv)
    cwd = args.cwd or os.getcwd()
    if args.resume_sid:
        r = touch_resume(args.resume_sid, cwd)
    else:
        known = [s for s in args.known.split(",") if s]
        r = name_session(cwd, known, timeout_s=args.timeout)
    print(f"{r.source}: sid={r.session_id} label={r.label!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
