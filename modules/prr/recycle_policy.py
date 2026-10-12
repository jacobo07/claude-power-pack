"""recycle_policy.py -- PRR physical epoch recycling decision (Stop-hook entry).

Evidence (vault/programs/prr/evidence/B-longrun-curves-gex44.md): a claude process keeps the
history it has already loaded. /compact and /clear cut the context sent to the model but not
the process's memory (+12 MB/100 turns either way). Recycling without a boundary reloads the
whole transcript. Compaction followed by a process recycle (`--resume <sid>`) is bounded
(+0.27 MB/100 turns, resume 0.3 s, same session id).

So a recycle pays exactly when THIS process crossed a semantic boundary:
  - compaction: the transcript's last compact_boundary row is newer than the process start;
  - /clear: a SessionStart hook with source "clear" fired inside this process (marker keyed by
    the claude process's pid AND create_time, so a recycled pid cannot inherit it).
A process resumed after the boundary fails both tests, so recycling cannot loop.
NOT a signal: "segment's first row is newer than the process". A fresh session writes its
first row at the first prompt, not at launch (measured: 85 s gap on a fresh pane), so that
test fires on every new pane.

Decision order (first match wins):
  subagent stop                   -> KEEP
  no dead history                 -> KEEP
  background tasks in flight      -> PIN   (recycling would orphan them)
  session crons / wakeups pending -> PIN   (session-scoped timers live in the process)
  no kclaude wrapper              -> KEEP  (no resume loop: stopping claude would close the pane)
  otherwise                       -> RECYCLE

Modes (env CPP_PRR_RECYCLE): off | observe (default: receipt only) | act (run the existing
graceful /restart handshake, scripts/restart-claude.ps1). Fail-open: any error is a receipt
and exit 0; this hook never blocks a turn.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

SKEW_S = 2.0
TAIL_CHUNK = 1 << 20
RECEIPTS = Path(os.path.expanduser("~/.claude/state/prr/receipts.jsonl"))
MARKERS = Path(os.path.expanduser("~/.claude/state/prr/cleared"))
RESTART_SCRIPT = Path(os.path.expanduser("~/.claude/scripts/restart-claude.ps1"))


@dataclass
class Decision:
    action: str
    reasons: list = field(default_factory=list)
    carry_since: float | None = None


def _ts(value) -> float | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def last_boundary_ts(path: Path) -> float | None:
    """Timestamp of the last compact_boundary row, scanning backwards in chunks."""
    needle = b'"compact_boundary"'
    try:
        with open(path, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            end = fh.tell()
            carry = b""
            while end > 0:
                start = max(0, end - TAIL_CHUNK)
                fh.seek(start)
                buf = fh.read(end - start) + carry
                lines = buf.split(b"\n")
                carry = lines[0] if start > 0 else b""
                for line in reversed(lines[1:] if start > 0 else lines):
                    if needle in line:
                        try:
                            return _ts(json.loads(line).get("timestamp"))
                        except ValueError:
                            continue
                end = start
    except OSError:
        return None
    return None


def _marker(pid: int, create_time: float) -> Path:
    return MARKERS / f"{pid}-{int(create_time)}.json"


def mark_clear(pid: int, create_time: float, sid: str | None) -> Path:
    path = _marker(pid, create_time)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"pid": pid, "create_time": create_time, "sid": sid, "ts": time.time()}),
                    encoding="utf-8")
    return path


def cleared_in_process(pid: int, create_time: float) -> float | None:
    try:
        return json.loads(_marker(pid, create_time).read_text(encoding="utf-8")).get("ts")
    except (OSError, ValueError):
        return None


def decide(*, proc_start: float, boundary_ts: float | None, cleared_ts: float | None,
           has_wrapper: bool, background_tasks: int, session_crons: int,
           is_subagent: bool = False) -> Decision:
    if is_subagent:
        return Decision("KEEP", ["subagent stop"])
    compacted = boundary_ts is not None and boundary_ts > proc_start + SKEW_S
    if not compacted and cleared_ts is None:
        return Decision("KEEP", ["no boundary crossed inside this process"], boundary_ts)
    carry = max(t for t in (boundary_ts if compacted else None, cleared_ts) if t is not None)
    why = "compact boundary" if compacted and carry == boundary_ts else "/clear inside this process"
    if background_tasks:
        return Decision("PIN", [why, f"{background_tasks} background task(s) in flight"], carry)
    if session_crons:
        return Decision("PIN", [why, f"{session_crons} session cron(s) pending"], carry)
    if not has_wrapper:
        return Decision("KEEP", [why, "no kclaude resume loop"], carry)
    return Decision("RECYCLE", [why], carry)


def _claude_ancestor():
    import psutil

    cur = psutil.Process()
    for _ in range(12):
        cur = cur.parent()
        if cur is None:
            return None, None
        if cur.name().lower() in ("claude.exe", "claude"):
            par = cur.parent()
            cmd = ""
            if par is not None:
                try:
                    cmd = " ".join(par.cmdline())
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    cmd = ""
            return cur, ("kclaude" in cmd.lower())
    return None, None


def _receipt(rec: dict) -> None:
    RECEIPTS.parent.mkdir(parents=True, exist_ok=True)
    with open(RECEIPTS, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")


def run_hook(payload: dict, mode: str) -> dict:
    rec = {"ts": time.time(), "mode": mode, "sid": payload.get("session_id"),
           "event": payload.get("hook_event_name")}
    proc, has_wrapper = _claude_ancestor()
    if proc is None:
        rec.update(action="KEEP", reasons=["no claude ancestor"])
        return rec
    if payload.get("hook_event_name") == "SessionStart":
        rec.update(pid=proc.pid, source=payload.get("source"), action="MARK" if payload.get("source") == "clear" else "NONE")
        if payload.get("source") == "clear":
            rec["marker"] = str(mark_clear(proc.pid, proc.create_time(), payload.get("session_id")))
        return rec
    mem = proc.memory_info()
    rec.update(pid=proc.pid, proc_age_h=round((time.time() - proc.create_time()) / 3600, 3),
               private_mb=round(getattr(mem, "private", getattr(mem, "vms", 0)) / 2**20, 1),
               wset_mb=round(getattr(mem, "wset", mem.rss) / 2**20, 1), wrapper=has_wrapper)
    tp = Path(payload.get("transcript_path") or "")
    d = decide(proc_start=proc.create_time(),
               boundary_ts=last_boundary_ts(tp) if tp.is_file() else None,
               cleared_ts=cleared_in_process(proc.pid, proc.create_time()),
               has_wrapper=bool(has_wrapper),
               background_tasks=len(payload.get("background_tasks") or []),
               session_crons=len(payload.get("session_crons") or []),
               is_subagent=payload.get("hook_event_name") == "SubagentStop")
    rec.update(action=d.action, reasons=d.reasons, carry_since=d.carry_since, acted=False)
    if mode == "act" and d.action == "RECYCLE" and RESTART_SCRIPT.is_file():
        subprocess.Popen(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                          "-File", str(RESTART_SCRIPT)],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        rec["acted"] = True
    return rec


def main() -> int:
    mode = os.environ.get("CPP_PRR_RECYCLE", "observe").strip().lower()
    if mode == "off":
        return 0
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        rec = run_hook(payload, mode)
    except Exception as exc:  # fail-open by contract: record, never block a turn
        rec = {"ts": time.time(), "mode": mode, "action": "ERROR", "error": f"{type(exc).__name__}: {exc}"}
    try:
        _receipt(rec)
    except OSError as exc:
        print(f"prr recycle receipt not written: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
