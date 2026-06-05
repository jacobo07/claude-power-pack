#!/usr/bin/env python3
"""work_state_saver.py - capture/restore exact work-in-progress before a reset.

Auto-Reset Orchestrator M2 (2026-06-04). The context-watchdog already writes a
PROSE handoff; this writes STRUCTURED, resume-injectable work_state so a NEW
session after an auto-reset knows exactly what it was doing and continues
without friction. Composes existing primitives (SCS C28): PaneRegistry
(task, last_commit), git (branch/HEAD/changed files).

State file: <state_dir>/work_state_<key>.json  (state_dir defaults to
~/.claude/state). key = session_id when known (the Stop event has it), else
'cwd-<hash>'. RESUME reconciles by CWD -- the new session has a different
session_id, so cwd is the stable join key. (The plan's literal said pane_id;
the Stop event exposes session_id + cwd, NOT pane_id -- cwd is the honest
join, documented per "honor intent, correct literal".)

Schema (schema_version 1):
  { schema_version, ts, session_id, cwd, branch, task, last_file,
    last_commit, pending: [str] }

API (state_dir param everywhere so tests are hermetic):
  save_work_state(cwd, session_id=None, task=None, pending=None,
                  state_dir=None) -> dict
  load_work_state_for_cwd(cwd, state_dir=None) -> dict | None
  load_work_state(key, state_dir=None) -> dict | None
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]

SCHEMA_VERSION = 1
DEFAULT_STATE_DIR = Path.home() / ".claude" / "state"
_MAX_PENDING = 8


def _state_dir(state_dir: Path | str | None) -> Path:
    return Path(state_dir) if state_dir else DEFAULT_STATE_DIR


def _git_exe() -> str:
    """Resolve git. PowerShell -NonInteractive lacks git on PATH on this host
    (PATH-gap lesson); a plain python subprocess usually has it, but fall back
    to the known absolute path to be safe."""
    found = shutil.which("git")
    if found:
        return found
    abs_git = r"C:\Program Files\Git\cmd\git.exe"
    return abs_git if Path(abs_git).is_file() else "git"


def _git(args: list[str], cwd: str) -> str | None:
    try:
        r = subprocess.run([_git_exe(), "-C", cwd, *args],
                           capture_output=True, text=True, timeout=8)
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:  # noqa: BLE001
        return None
    return None


def _branch(cwd: str) -> str | None:
    return _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd) or None


def _head_commit(cwd: str) -> str | None:
    out = _git(["log", "-1", "--format=%h %s"], cwd)
    return out or None


def _changed_files(cwd: str) -> list[str]:
    out = _git(["status", "--porcelain"], cwd)
    if not out:
        return []
    files = []
    for line in out.splitlines():
        # porcelain: "XY <path>" (XY = 2 status chars + space)
        path = line[3:].strip() if len(line) > 3 else line.strip()
        if path:
            files.append(path)
    return files


def _registry_task(session_id: str | None, cwd: str) -> str | None:
    """Best-effort task from the CPC PaneRegistry: match session_id, else the
    most-recent active pane for this cwd."""
    try:
        sys.path.insert(0, str(_PP_ROOT))
        from modules.cpc_os.registry import PaneRegistry  # type: ignore
        reg = PaneRegistry.load()
        cwd_l = (cwd or "").lower()
        best = None
        for rec in reg.panes.values():
            if session_id and rec.session_id == session_id:
                if rec.task and rec.task != "active":
                    return rec.task
            if (rec.cwd or "").lower() == cwd_l and rec.status == "active":
                if best is None or rec.last_heartbeat_at > best.last_heartbeat_at:
                    best = rec
        if best and best.task and best.task != "active":
            return best.task
    except Exception:  # noqa: BLE001
        pass
    return None


def _last_user_prompt(cwd: str, session_id: str | None) -> str | None:
    """The most-recent genuine user text prompt from the active transcript --
    the actual current intent. A far better 'task' than the last commit, which
    is already-COMPLETED work (the old fallback showed a stale/cross-repo
    commit as the task, e.g. a KobiiCraft commit on a power-pack session).
    Best-effort; None on any failure. Reuses context_monitor's transcript
    resolver (SCS C28: compose, do not duplicate)."""
    tail_bytes = 200_000  # transcript tail bytes scanned for the last user turn
    try:
        sys.path.insert(0, str(_PP_ROOT))
        from modules.cpc_os.context_monitor import _active_transcript  # type: ignore
        tp = _active_transcript(cwd, session_id)
        if not tp or not tp.is_file():
            return None
        with tp.open("rb") as fh:
            size = tp.stat().st_size
            if size > tail_bytes:
                fh.seek(-tail_bytes, 2)
                fh.readline()
            lines = fh.read().decode("utf-8", errors="replace").splitlines()
        for ln in reversed(lines):
            ln = ln.strip()
            if not ln:
                continue
            try:
                e = json.loads(ln)
            except Exception:
                continue
            if (e.get("type") or e.get("role")) != "user":
                continue
            msg = e.get("message") or e
            content = msg.get("content") if isinstance(msg, dict) else ""
            if isinstance(content, list):
                # Keep real text; skip tool_result-only user turns.
                text = " ".join(
                    c.get("text", "") for c in content
                    if isinstance(c, dict) and c.get("type") == "text"
                ).strip()
            else:
                text = str(content).strip()
            if text:
                return text[:120]
    except Exception:  # noqa: BLE001
        return None
    return None


def _resolve_task(cwd: str, session_id: str | None,
                  task: str | None) -> str:
    if task:
        return task
    env_task = os.environ.get("PP_PANE_TASK")
    if env_task and env_task != "active":
        return env_task
    reg_task = _registry_task(session_id, cwd)
    if reg_task:
        return reg_task
    # The user's last request is the live intent -- prefer it over a commit.
    prompt = _last_user_prompt(cwd, session_id)
    if prompt:
        return f"(from last request) {prompt}"
    head = _head_commit(cwd)
    if head:
        # last commit subject as a weak "what was happening" hint
        return f"(inferred from last commit) {head}"
    return "(unknown task)"


def _key(session_id: str | None, cwd: str) -> str:
    if session_id:
        return session_id
    h = hashlib.sha1((cwd or "").encode("utf-8")).hexdigest()[:12]
    return f"cwd-{h}"


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        sys.path.insert(0, str(_PP_ROOT))
        from modules.cpc_os.registry import _atomic_write  # type: ignore
        _atomic_write(path, json.dumps(payload, indent=2))
    except Exception:  # noqa: BLE001
        # Fallback: direct write (still safe enough for a state sidecar).
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def save_work_state(cwd: str, session_id: str | None = None,
                    task: str | None = None,
                    pending: list[str] | None = None,
                    state_dir: Path | str | None = None) -> dict:
    """Capture structured work-in-progress and persist it. Returns the record."""
    cwd = cwd or os.getcwd()
    changed = _changed_files(cwd)
    auto_pending = [f"uncommitted: {f}" for f in changed[:_MAX_PENDING]]
    record = {
        "schema_version": SCHEMA_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "session_id": session_id,
        "cwd": cwd,
        "branch": _branch(cwd),
        "task": _resolve_task(cwd, session_id, task),
        "last_file": changed[0] if changed else None,
        "last_commit": _head_commit(cwd),
        "pending": (list(pending) if pending else auto_pending),
    }
    path = _state_dir(state_dir) / f"work_state_{_key(session_id, cwd)}.json"
    _atomic_write_json(path, record)
    record["_path"] = str(path)
    return record


def load_work_state(key: str, state_dir: Path | str | None = None) -> dict | None:
    path = _state_dir(state_dir) / f"work_state_{key}.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:  # noqa: BLE001
        return None


def load_work_state_for_cwd(cwd: str,
                            state_dir: Path | str | None = None) -> dict | None:
    """Most-recent work_state whose cwd matches -- the resume join (the new
    session has a different session_id, so cwd is the stable key)."""
    d = _state_dir(state_dir)
    if not d.is_dir():
        return None
    cwd_l = (cwd or "").lower()
    best = None
    best_mtime = -1.0
    for p in d.glob("work_state_*.json"):
        try:
            rec = json.loads(p.read_text(encoding="utf-8-sig"))
        except Exception:  # noqa: BLE001
            continue
        if (rec.get("cwd") or "").lower() != cwd_l:
            continue
        try:
            mtime = p.stat().st_mtime
        except OSError:
            continue
        if mtime > best_mtime:
            best, best_mtime = rec, mtime
    return best


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--save", action="store_true")
    ap.add_argument("--load", action="store_true")
    ap.add_argument("--cwd", default=None)
    ap.add_argument("--session-id", default=None)
    args = ap.parse_args(argv)
    cwd = args.cwd or os.getcwd()
    if args.save:
        rec = save_work_state(cwd, session_id=args.session_id)
        print(json.dumps(rec, indent=2))
    elif args.load:
        rec = load_work_state_for_cwd(cwd)
        print(json.dumps(rec, indent=2) if rec else "(no work_state for cwd)")
    else:
        ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
