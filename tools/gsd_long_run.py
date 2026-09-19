#!/usr/bin/env python
"""gsd_long_run -- the self-checking half of /cpp-gsd-long (spec vault/specs/gsd-long-run-v2.md).

The marker (tools/gsd_autorun_marker.py) says a run is in flight; the watchdog
(modules/zero-crash/hooks/context-watchdog.py) compacts and asks for the resume
line; the daemon (~/.claude/hooks/auto-compact-sendkeys-daemon.ps1) presses
Enter. This module is what lets that chain be judged instead of trusted:

  * a per-run LEDGER of what actually happened,
  * ARM-TIME preflight (right project, GSD can see phases),
  * a RESUME GATE (budget, mission still current),
  * a RAM floor before resuming,
  * a SWEEP that recovers stalled runs and cleans up finished/dead ones,
  * a REPORT whose verdict is derived from the ledger, never asserted.

CLI:
    python tools/gsd_long_run.py report  --session <sid>
    python tools/gsd_long_run.py status
    python tools/gsd_long_run.py sweep   [--dry-run]
    python tools/gsd_long_run.py wait-ram [--floor 1500] [--timeout 600] [--session <sid>]
    python tools/gsd_long_run.py preflight --session <sid> --cwd <path> --command <cmd>
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

CLAUDE_HOME = Path.home() / ".claude"
PROJECTS_DIR = CLAUDE_HOME / "projects"
HOOKS_DIR = CLAUDE_HOME / "hooks"
GSD_TOOLS = CLAUDE_HOME / "gsd-core" / "bin" / "gsd-tools.cjs"
DAEMON = HOOKS_DIR / "auto-compact-sendkeys-daemon.ps1"
LEDGER_NAME = "gsd-autorun-ledger.jsonl"

RAM_FLOOR_MB = 1500
DEFAULT_MAX_CYCLES = 12
DEFAULT_MAX_HOURS = 24.0
STALL_MINUTES = 20
DEAD_HOURS = 48
TAIL_BYTES = 262144


# --------------------------------------------------------------------------- paths
def state_dir() -> Path:
    """Resolved at call time so a test can redirect it without patching a copy."""
    override = os.environ.get("GSD_LONG_RUN_STATE_DIR")
    return Path(override) if override else CLAUDE_HOME / "state"


THRESHOLDS_TEMPLATE = "ctxwd-thresholds-{session_id}.json"
WATCHDOG = CLAUDE_HOME / "skills" / "claude-power-pack" / "modules" / "zero-crash" / "hooks" / "context-watchdog.py"


def thresholds_path(session_id: str) -> Path:
    if not re.match(r"^[A-Za-z0-9._-]{1,128}$", session_id or ""):
        raise ValueError(f"invalid session id: {session_id!r}")
    return state_dir() / THRESHOLDS_TEMPLATE.format(session_id=session_id)


def _watchdog_validator():
    """The watchdog's OWN rule, loaded lazily. Raises when it cannot be had.

    Imported rather than restated: two copies of "rearm < snapshot <= advisory"
    drift, and the copy that drifts is the one nobody drives. Lazy because the
    watchdog imports THIS module at runtime, and a module-level import back
    would close the cycle.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("_ctxwd_for_validation", WATCHDOG)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load the watchdog at {WATCHDOG}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.valid_thresholds


def write_thresholds(session_id: str, spec: str, reason: str = "") -> dict:
    """Ask the watchdog to use `snapshot,advisory,rearm` for THIS session.

    Fails CLOSED at the boundary: if the watchdog's validator cannot be loaded
    the file is not written at all, because an unvalidated file is exactly the
    thing the validator exists to refuse.
    """
    checked = _watchdog_validator()(*[x.strip() for x in str(spec).split(",")]) \
        if str(spec).count(",") == 2 else None
    if checked is None:
        raise ValueError(
            f"refused {spec!r}: need snapshot,advisory,rearm with rearm < snapshot <= advisory, all 5..95")
    snap, adv, rearm = checked
    payload = {"session_id": session_id, "snapshot": snap, "advisory": adv, "rearm": rearm,
               "reason": reason, "written_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")}
    path = thresholds_path(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)
    ledger_append(session_id, "thresholds_set", snapshot=snap, advisory=adv, rearm=rearm, reason=reason)
    return payload


def read_thresholds(session_id: str) -> dict | None:
    try:
        return json.loads(thresholds_path(session_id).read_text(encoding="utf-8"))
    except Exception:
        return None


def clear_thresholds(session_id: str) -> bool:
    try:
        thresholds_path(session_id).unlink()
    except (FileNotFoundError, ValueError, OSError):
        return False
    ledger_append(session_id, "thresholds_cleared")
    return True


def ledger_path() -> Path:
    return state_dir() / LEDGER_NAME


def hooks_dir() -> Path:
    override = os.environ.get("GSD_LONG_RUN_HOOKS_DIR")
    return Path(override) if override else HOOKS_DIR


def projects_dir() -> Path:
    override = os.environ.get("GSD_LONG_RUN_PROJECTS_DIR")
    return Path(override) if override else PROJECTS_DIR


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def _parse_iso(value) -> float | None:
    try:
        return _dt.datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def norm_dir(path) -> str:
    return os.path.normcase(os.path.abspath(str(path))).rstrip("\\/")


# --------------------------------------------------------------------------- ledger
def ledger_append(session_id: str, event: str, **fields) -> None:
    """Append one event. Never raises: a ledger write must not break the loop it records."""
    try:
        path = ledger_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        row = {"ts": _now_iso(), "session_id": session_id, "event": event}
        row.update(fields)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def ledger_events(session_id: str | None = None) -> list[dict]:
    path = ledger_path()
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        try:
            row = json.loads(line)
        except Exception:
            continue
        if session_id is None or row.get("session_id") == session_id:
            out.append(row)
    return out


# --------------------------------------------------------------------------- host
def free_ram_mb() -> float | None:
    """Free physical memory in MB, or None when it cannot be measured."""
    forced = os.environ.get("_TEST_FREE_MB")
    if forced:
        try:
            return float(forced)
        except ValueError:
            return None
    if os.name != "nt":
        return None
    try:
        import ctypes

        class _MS(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        ms = _MS()
        ms.dwLength = ctypes.sizeof(_MS)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms)):
            return None
        return ms.ullAvailPhys / (1024 * 1024)
    except Exception:
        return None


# --------------------------------------------------------------------------- transcripts
def find_transcript(session_id: str) -> Path | None:
    root = projects_dir()
    if not root.is_dir() or not session_id:
        return None
    for path in root.glob(f"*/{session_id}.jsonl"):
        if path.is_file():
            return path
    return None


def session_cwd(transcript: Path) -> str | None:
    """The session's own working directory: the first `cwd` its transcript records."""
    try:
        with open(transcript, encoding="utf-8", errors="replace") as fh:
            for i, line in enumerate(fh):
                if i > 400:
                    break
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                cwd = row.get("cwd") if isinstance(row, dict) else None
                if cwd:
                    return str(cwd)
    except OSError:
        return None
    return None


def _tail_rows(transcript: Path, tail_bytes: int = TAIL_BYTES) -> list[dict]:
    try:
        size = transcript.stat().st_size
        with open(transcript, "rb") as fh:
            fh.seek(max(0, size - tail_bytes))
            raw = fh.read().decode("utf-8", errors="replace")
    except OSError:
        return []
    rows = []
    lines = raw.splitlines()
    if size > tail_bytes and lines:
        lines = lines[1:]  # first line is a fragment
    for line in lines:
        try:
            row = json.loads(line)
        except Exception:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _text_of(message) -> str:
    content = (message or {}).get("content")
    if isinstance(content, str):
        return content
    parts = []
    for block in content or []:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text") or "")
    return "\n".join(parts)


def last_assistant_text(transcript: Path) -> str | None:
    """Text of the LAST assistant entry, or None. An entry with no text (a tool call) is ''."""
    for row in reversed(_tail_rows(transcript)):
        if row.get("type") == "assistant":
            return _text_of(row.get("message"))
    return None


def last_line(text: str | None) -> str:
    for line in reversed((text or "").splitlines()):
        if line.strip():
            return line.strip().strip("`").strip()
    return ""


CONFIRM_TAIL_BYTES = 8 * 1024 * 1024


def user_issued_command_since(transcript: Path, command: str, since_epoch: float,
                              tail_bytes: int = CONFIRM_TAIL_BYTES) -> bool:
    """True when a user entry after `since_epoch` carries the command.

    Claude Code records a slash command as `<command-name>/name</command-name>`;
    typed text is recorded verbatim. Either counts.

    The window is 8 MB rather than the 256 KB `_tail_rows` default, and that is a
    measured defect rather than caution. A resume is confirmed by a Stop hook
    running at the END of the turn the resume began -- and that turn has already
    written its whole tool output into the transcript by then. Measured
    2026-09-19 on session 37cfb187: the `/gsd-autonomous` row sat 598 KB from the
    end of a 5.8 MB transcript, so a 256 KB window could not see it, every Stop
    chain read False, and the run could never confirm its own resume. The
    coupling is perverse -- the more work the turn did, the further back the row
    is pushed -- so the confirmation failed exactly when the run was working
    hardest, which is the case the whole mechanism exists for.

    Widening is affordable because only lines that CONTAIN the command name are
    parsed: the cost is a substring scan, not 8 MB of JSON inside a hook budget.
    """
    name = (command or "").split()[0] if command else ""
    if not name:
        return False
    needle = name.encode("utf-8", errors="replace")
    try:
        size = transcript.stat().st_size
        with open(transcript, "rb") as fh:
            fh.seek(max(0, size - tail_bytes))
            raw = fh.read()
    except OSError:
        return False
    lines = raw.split(b"\n")
    if size > tail_bytes and lines:
        lines = lines[1:]  # first line is a fragment
    for line in lines:
        if needle not in line:
            continue
        try:
            row = json.loads(line.decode("utf-8", errors="replace"))
        except Exception:
            continue
        if not isinstance(row, dict) or row.get("type") != "user":
            continue
        ts = _parse_iso(row.get("timestamp"))
        if ts is None or ts < since_epoch:
            continue
        text = _text_of(row.get("message"))
        if f"<command-name>{name}</command-name>" in text or text.strip().startswith(name):
            return True
    return False


# --------------------------------------------------------------------------- compaction truth
# Spec vault/specs/exact-target-continuation.md (C1). A low context reading is
# not a compaction: a RESUMED session reads ~15-23% too, and on 2026-09-18 that
# is exactly what told session 8178f7d0 "COMPACTION LANDED" 25 hours after its
# last compaction. The host writes a `compact_boundary` system row when it
# compacts; that row is the post-condition, and nothing else is.
BOUNDARY_TAIL_BYTES = 8 * 1024 * 1024


def compaction_observed(transcript, since_epoch: float | None) -> dict:
    """Is there a compaction boundary in `transcript` newer than `since_epoch`?

    Returns {"state": "observed"|"unobserved"|"unreadable", "boundary_ts",
    "boundary_uuid", "trigger", "reason"}. Rows are parsed, never substring-
    matched: this estate's own transcripts quote the boundary row in prose.
    A boundary older than the tail window reads as unobserved, which refuses a
    resume -- the safe direction for a claim that licenses an effect.
    """
    path = Path(transcript) if transcript else None
    if path is None or not path.is_file():
        return {"state": "unreadable", "reason": f"no transcript at {transcript!r}"}
    if since_epoch is None:
        return {"state": "unobserved", "reason": "no cycle reference to compare against"}
    try:
        size = path.stat().st_size
        with open(path, "rb") as fh:
            fh.seek(max(0, size - BOUNDARY_TAIL_BYTES))
            raw = fh.read()
    except Exception as exc:
        return {"state": "unreadable", "reason": f"{exc.__class__.__name__} reading transcript"}
    latest = None
    # Only lines carrying the token are parsed (this runs inside a Stop hook with
    # a 6 s budget); the parsed type/subtype is what decides, not the token.
    for line in raw.split(b"\n"):
        if b"compact_boundary" not in line:
            continue
        try:
            row = json.loads(line.decode("utf-8", errors="replace"))
        except Exception:
            continue
        if not isinstance(row, dict):
            continue
        if row.get("type") != "system" or row.get("subtype") != "compact_boundary":
            continue
        ts = _parse_iso(row.get("timestamp"))
        if ts is not None and (latest is None or ts > latest[0]):
            latest = (ts, row)
    if latest is None:
        return {"state": "unobserved", "reason": "no compact_boundary row in the transcript tail"}
    ts, row = latest
    found = {"boundary_ts": row.get("timestamp"), "boundary_uuid": row.get("uuid"),
             "trigger": (row.get("compactMetadata") or {}).get("trigger")}
    if ts <= since_epoch:
        return {"state": "unobserved", **found,
                "reason": "latest boundary is not newer than the cycle reference"}
    return {"state": "observed", **found, "reason": "boundary newer than the cycle reference"}


def resume_reference(session_id: str, marker: dict) -> float | None:
    """The instant a boundary must postdate to license a resume.

    max(marker armed_at -- or `ts` on a schema-1 marker --, the boundary_ts of
    the last resume this session already requested). Each boundary therefore
    licenses at most one resume.
    """
    marker = marker or {}
    points = [_parse_iso(marker.get("armed_at") or marker.get("ts"))]
    for row in ledger_events(session_id):
        if row.get("event") == "resume_requested" and row.get("boundary_ts"):
            points.append(_parse_iso(row.get("boundary_ts")))
    points = [p for p in points if p is not None]
    return max(points) if points else None


# --------------------------------------------------------------------------- GSD
def gsd_status(project, timeout: int = 45) -> dict:
    # 45 s, not 20: measured 5 s alone and >20 s beside other suites on this host
    # at 2.5 GB free. A short ceiling turns a loaded host into an arming refusal.
    """Ask GSD what it sees in `project`. Outcomes: OK, NO_PHASES, ALL_COMPLETE, UNAVAILABLE.

    UNAVAILABLE means we could not ask -- it is never read as "0 phases".
    """
    forced = os.environ.get("_TEST_GSD_STATUS")
    if forced:
        return json.loads(forced)
    node = shutil.which("node")
    if not node or not GSD_TOOLS.is_file():
        return {"outcome": "UNAVAILABLE", "reason": "node or gsd-tools.cjs not found"}
    try:
        # stdin=DEVNULL is load-bearing: with an inherited pipe gsd-tools waits on
        # stdin and the call times out (measured: 20 s from Python, instant from a TTY).
        r = subprocess.run([node, str(GSD_TOOLS), "query", "init.manager"], cwd=str(project),
                           stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout,
                           encoding="utf-8", errors="replace")
    except Exception as exc:
        return {"outcome": "UNAVAILABLE", "reason": f"{exc.__class__.__name__}: {exc}"}
    out = (r.stdout or "").strip()
    if out.startswith("@file:"):
        try:
            out = Path(out[6:]).read_text(encoding="utf-8")
        except OSError as exc:
            return {"outcome": "UNAVAILABLE", "reason": f"cannot read {out[6:]}: {exc}"}
    try:
        data = json.loads(out)
    except Exception:
        return {"outcome": "UNAVAILABLE", "reason": f"gsd-tools rc={r.returncode}: {(r.stderr or out)[:200]}"}
    total = int(data.get("phase_count") or 0)
    done = int(data.get("completed_count") or 0)
    base = {"phase_count": total, "completed": done, "incomplete": max(0, total - done),
            "milestone": data.get("milestone_version"), "all_complete": bool(data.get("all_complete"))}
    if not data.get("roadmap_exists") or not data.get("state_exists"):
        return dict(base, outcome="NO_PHASES", reason="GSD finds no ROADMAP.md/STATE.md")
    if total == 0:
        return dict(base, outcome="NO_PHASES",
                    reason="GSD parses 0 phases from ROADMAP.md (headings must be GSD phases)")
    if base["all_complete"] or base["incomplete"] == 0:
        return dict(base, outcome="ALL_COMPLETE", reason=f"{done}/{total} phases complete")
    return dict(base, outcome="OK", reason=f"{done}/{total} phases complete")


# --------------------------------------------------------------------------- arm / resume gates
def arm_preflight(session_id: str, cwd: str, command: str) -> tuple[bool, str]:
    """Refuse to arm a run that would execute somewhere else, or do nothing.

    Gap 6: `--cwd` is metadata; the run executes in the SESSION's directory.
    Gap 8: a roadmap GSD cannot parse yields a run with nothing to do.
    """
    transcript = find_transcript(session_id)
    if transcript is None:
        return False, (f"cannot find this session's transcript ({session_id}); "
                       "cannot tell which project the run would execute in")
    actual = session_cwd(transcript)
    if not actual:
        return False, "the session transcript records no cwd; cannot tell where the run executes"
    if norm_dir(actual) != norm_dir(cwd or "."):
        return False, (f"this session runs in {actual!r} but --cwd is {cwd!r}; the resumed command "
                       f"would execute in the session's project. Open the session in {cwd!r} and arm there")
    if (command or "").strip().startswith("/gsd-autonomous"):
        st = gsd_status(cwd)
        if st["outcome"] == "UNAVAILABLE":
            return False, f"could not ask GSD for the phase list: {st['reason']}"
        if st["outcome"] == "NO_PHASES":
            return False, st["reason"]
        if st["outcome"] == "ALL_COMPLETE":
            return False, f"nothing to run: {st['reason']}"
    return True, "ok"


def budget_verdict(marker: dict, now: float | None = None) -> tuple[bool, str]:
    now = time.time() if now is None else now
    max_cycles = int(marker.get("max_cycles") or DEFAULT_MAX_CYCLES)
    max_hours = float(marker.get("max_hours") or DEFAULT_MAX_HOURS)
    cycles = int(marker.get("cycles") or 0)
    if cycles >= max_cycles:
        return False, f"cycle budget spent: {cycles}/{max_cycles} resumes"
    started = _parse_iso(marker.get("armed_at") or marker.get("ts"))
    if started is not None and (now - started) / 3600.0 >= max_hours:
        return False, f"time budget spent: {(now - started) / 3600.0:.1f} h of {max_hours:g} h"
    return True, f"{cycles}/{max_cycles} resumes"


def resume_gate(marker: dict, now: float | None = None) -> dict:
    """Decide at resume time whether the run may continue. Budget first, then mission."""
    ok, why = budget_verdict(marker, now)
    if not ok:
        return {"halt": True, "reason": why, "kind": "budget"}
    mission = marker.get("mission") or {}
    terms = mission.get("terms")
    cwd = marker.get("cwd")
    if terms and cwd:
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            import gsd_mission_freshness as _mf
            verdict = _mf.check(cwd, terms)
        except Exception as exc:
            return {"halt": True, "kind": "mission",
                    "reason": f"mission re-check could not run: {exc.__class__.__name__}: {exc}"}
        if not verdict.armable:
            return {"halt": True, "kind": "mission",
                    "reason": f"mission {verdict.outcome}: {verdict.reason}"}
        return {"halt": False, "reason": why + f"; mission {verdict.outcome}", "kind": "ok"}
    return {"halt": False, "reason": why + "; mission unchecked (marker carries none)", "kind": "ok"}


def owed_line(session_id: str, marker: dict, transcript, tail: str, cmd: str) -> dict:
    """What a stalled run is owed NOW: the line to re-deliver, or a halt.

    `tail` is the transcript's last assistant line, and when it is a `/compact`
    line it is the same in two OPPOSITE states: the line was never submitted,
    and the line WAS submitted and the compaction landed. After a compaction the
    agent has not spoken yet, so the tail does not move -- the two states are
    indistinguishable from the tail alone, and they need opposite actions.
    Re-typing `/compact` is right only in the first; in the second the host
    answers "Not enough messages to compact" and the run can never advance.

    Measured 2026-09-19 on session 37cfb187: one `/compact` line, three sweep
    recoveries that each re-typed it, then nine idle hours. What was owed after
    the compaction was the resume command, and nothing ever sent it.

    The boundary row is the only thing that separates the two states (C1), so
    this asks it, and gates the resume exactly as the watchdog does -- a resume
    issued from outside the session is still a resume and still spends budget.
    """
    if not tail.startswith("/compact") or not cmd:
        return {"line": tail, "compaction": "n/a", "halt": False}
    obs = compaction_observed(transcript, resume_reference(session_id, marker))
    if obs.get("state") != "observed":
        # Not observed means the compaction cannot be claimed, so the `/compact`
        # line is still owed. Fail-safe: re-typing it is idempotent, re-typing
        # the resume when nothing compacted would skip the wall entirely.
        return {"line": tail, "compaction": obs.get("state"), "halt": False,
                "reason": obs.get("reason")}
    gate = resume_gate(marker)
    if gate.get("halt"):
        return {"line": None, "compaction": "observed", "halt": True,
                "reason": gate.get("reason"), "kind": gate.get("kind")}
    return {"line": cmd, "compaction": "observed", "halt": False,
            "gate": gate.get("reason"),
            "boundary_ts": obs.get("boundary_ts"), "boundary_uuid": obs.get("boundary_uuid")}


def _marker_module():
    """Lazy import: the marker module imports nothing from here, but keep it late anyway."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import gsd_autorun_marker as mk
        return mk
    except Exception:
        return None


# --------------------------------------------------------------------------- flags
def _flag_names(session_id: str) -> list[str]:
    return [f"auto-compact-{k}-{session_id}.flag" for k in ("trigger", "pending", "refused")]


def flags_for(session_id: str) -> list[Path]:
    return [hooks_dir() / n for n in _flag_names(session_id) if (hooks_dir() / n).exists()]


def write_trigger(session_id: str, cwd: str, transcript: str, expect_line: str) -> Path:
    path = hooks_dir() / f"auto-compact-trigger-{session_id}.flag"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"ts": _now_iso(), "session_id": session_id, "cwd": cwd, "used_pct": None,
               "transcript": transcript, "expect_line": expect_line}
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    return path


def daemon_alive() -> bool:
    lock = hooks_dir() / ".auto-compact-daemon.lock"
    if not lock.is_file():
        return False
    try:
        pid = int(lock.read_text(encoding="ascii").split("|")[0])
    except Exception:
        return False
    try:
        r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True,
                           text=True, timeout=10)
        return str(pid) in (r.stdout or "")
    except Exception:
        return True  # cannot tell: do not stack a second daemon


def spawn_daemon() -> bool:
    if os.environ.get("GSD_LONG_RUN_NO_SPAWN") == "1" or not DAEMON.is_file():
        return False
    try:
        subprocess.Popen(["cmd.exe", "/c", "start", "", "/B", "powershell.exe", "-NoProfile",
                          "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", str(DAEMON)],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=0x08000000)
        return True
    except Exception:
        return False


# --------------------------------------------------------------------------- sweep
def _markers() -> list[tuple[Path, dict]]:
    out = []
    for path in sorted(state_dir().glob("gsd-autorun-*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict) and data.get("session_id"):
            out.append((path, data))
    return out


def _already(session_id: str, event: str, key: str, value) -> bool:
    return any(e.get("event") == event and e.get(key) == value for e in ledger_events(session_id))


def _restore_config(project: str) -> str:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import gsd_long_run_config as cfg
        cfg.restore(Path(project))
        return "restored"
    except Exception as exc:
        return f"not restored: {exc}"


def _recover_via_transport(sid: str, cwd: str, transcript: str, tail: str, cmd: str,
                           mtime: int) -> str:
    """Re-deliver a stalled run's line to the session's OWN terminal, or to nobody.

    Spec exact-target-continuation.md (C4). This path used to write a trigger
    flag keyed by cwd only; on 2026-09-18 the daemon then typed
    `/absw2-continue` into a different session's Cursor window. The sweep runs
    outside the session, so an Orca-hosted run uses the endpoint its own hook
    recorded; any other run goes to the terminal inbox by SESSION id (the
    daemon types only through the extension that owns that terminal, and by
    default refuses when none answers).
    """
    cid = f"{sid}:recover:{mtime}"
    if (os.environ.get("CPP_CONTINUATION_TRANSPORT") or "").lower() == "off":
        ledger_append(sid, "delivery_blocked", cid=cid, outcome="BLOCKED_TRANSPORT_DISABLED")
        return "manual"
    try:
        import continuation_transport as ct  # lazy: it imports this module
    except Exception as exc:
        ledger_append(sid, "delivery_blocked", cid=cid, outcome="TRANSPORT_UNAVAILABLE",
                      why=exc.__class__.__name__)
        return "manual"
    compact = tail.startswith("/compact")
    ep = ct.read_endpoint(sid) or {}
    if ep.get("host") == "orca":
        if ct.spawn_delivery(sid, "compact" if compact else "resume",
                             None if compact else cmd, "/compact" if compact else None,
                             transcript, cid):
            return "orca-exact"
        ledger_append(sid, "delivery_blocked", cid=cid, outcome="WORKER_SPAWN_FAILED")
        return "manual"
    write_trigger(sid, cwd, transcript, tail)
    return "terminal-inbox"


def sweep(now: float | None = None, dry_run: bool = False) -> list[dict]:
    """One pass. Every action is also a ledger event, so the sweep audits itself."""
    now = time.time() if now is None else now
    actions: list[dict] = []
    cleared_projects: set[str] = set()

    for path, m in _markers():
        sid = m["session_id"]
        cmd = m.get("resume_command") or ""
        cwd = m.get("cwd") or ""
        transcript = find_transcript(sid)
        idle_s = (now - transcript.stat().st_mtime) if transcript else None

        if transcript is None or idle_s > DEAD_HOURS * 3600:
            why = "transcript missing" if transcript is None else f"idle {idle_s / 3600:.0f} h"
            actions.append({"session_id": sid, "action": "reaped", "reason": why})
            if not dry_run:
                path.unlink(missing_ok=True)
                ledger_append(sid, "reaped", reason=why)
                if cwd:
                    cleared_projects.add(cwd)
            continue

        if cmd.startswith("/gsd-autonomous") and cwd and Path(cwd).is_dir():
            st = gsd_status(cwd)
            if st["outcome"] == "ALL_COMPLETE":
                actions.append({"session_id": sid, "action": "finished", "reason": st["reason"]})
                if not dry_run:
                    path.unlink(missing_ok=True)
                    ledger_append(sid, "finished", reason=st["reason"])
                    cleared_projects.add(cwd)
                continue

        if idle_s < STALL_MINUTES * 60:
            continue
        mtime = int(transcript.stat().st_mtime)
        tail = last_line(last_assistant_text(transcript))
        waiting = [p for p in flags_for(sid) if "refused" not in p.name]
        resumable = tail == cmd or tail.startswith("/compact")
        if resumable and not waiting:
            if _already(sid, "recovered", "transcript_mtime", mtime):
                continue
            owed = owed_line(sid, m, transcript, tail, cmd)
            if owed["halt"]:
                actions.append({"session_id": sid, "action": "halted", "reason": owed["reason"]})
                if not dry_run:
                    path.unlink(missing_ok=True)
                    ledger_append(sid, "halted", kind=owed.get("kind"),
                                  reason=owed.get("reason"), via="sweep")
                continue
            line = owed["line"]
            actions.append({"session_id": sid, "action": "recovered", "line": line,
                            "compaction": owed["compaction"]})
            if not dry_run:
                if line == cmd and owed["compaction"] == "observed":
                    # This IS the resume request the watchdog never got to make:
                    # it spends a cycle and advances the one-resume-per-boundary
                    # fence, which reads `resume_requested` rows carrying a
                    # boundary_ts. A bare `recovered` row would leave the fence
                    # where it was and let the same boundary license a resume again.
                    mk = _marker_module()
                    cycles = mk.bump_cycles(sid) if mk is not None else None
                    ledger_append(sid, "resume_requested", cycles=cycles, via="sweep",
                                  gate=owed.get("gate"),
                                  boundary_ts=owed.get("boundary_ts"),
                                  boundary_uuid=owed.get("boundary_uuid"))
                route = _recover_via_transport(sid, cwd, str(transcript), line, cmd, mtime)
                ledger_append(sid, "recovered", line=line, transcript_mtime=mtime, route=route,
                              compaction=owed["compaction"])
            continue
        if not _already(sid, "stalled", "transcript_mtime", mtime):
            actions.append({"session_id": sid, "action": "stalled", "idle_min": round(idle_s / 60),
                            "last_line": tail[:120], "flags": [p.name for p in flags_for(sid)]})
            if not dry_run:
                ledger_append(sid, "stalled", idle_min=round(idle_s / 60), last_line=tail[:120],
                              transcript_mtime=mtime)

    live = {norm_dir(m.get("cwd") or "") for _, m in _markers()}
    for project in cleared_projects:
        if norm_dir(project) in live:
            continue
        result = "dry-run" if dry_run else _restore_config(project)
        actions.append({"action": "config", "project": project, "result": result})

    pending = [p for p in hooks_dir().glob("auto-compact-*.flag")
               if p.name.startswith(("auto-compact-trigger", "auto-compact-pending"))]
    if pending and not daemon_alive():
        spawned = False if dry_run else spawn_daemon()
        actions.append({"action": "daemon", "flags": len(pending), "spawned": spawned})
    return actions


# --------------------------------------------------------------------------- report
def report(session_id: str) -> dict:
    """Verdict derived from the ledger. PROVEN = >= 2 crossings, each followed by a confirmed resume."""
    events = ledger_events(session_id)
    cycles = []
    current = None
    for e in events:
        ev = e.get("event")
        if ev == "crossing":
            current = {"crossing": e.get("ts"), "confirmed": None}
            cycles.append(current)
        elif ev == "resume_confirmed" and current is not None and current["confirmed"] is None:
            current["confirmed"] = e.get("ts")
    confirmed = sum(1 for c in cycles if c["confirmed"])
    if len(cycles) >= 2 and confirmed == len(cycles):
        verdict = "PROVEN"
    elif confirmed:
        verdict = "PARTIAL"
    elif cycles:
        verdict = "UNPROVEN"
    else:
        verdict = "NO_CROSSINGS"
    counts: dict[str, int] = {}
    for e in events:
        counts[e.get("event")] = counts.get(e.get("event"), 0) + 1
    return {"session_id": session_id, "verdict": verdict, "crossings": len(cycles),
            "confirmed": confirmed, "cycles": cycles, "counts": counts,
            "last": events[-1] if events else None}


def status() -> list[dict]:
    rows = []
    for _, m in _markers():
        sid = m["session_id"]
        r = report(sid)
        rows.append({"session_id": sid, "command": m.get("resume_command"), "cwd": m.get("cwd"),
                     "cycles": m.get("cycles", 0), "max_cycles": m.get("max_cycles"),
                     "verdict": r["verdict"], "flags": [p.name for p in flags_for(sid)],
                     "last_event": (r["last"] or {}).get("event")})
    return rows


def wait_ram(floor: float, timeout: float, session_id: str = "") -> int:
    deadline = time.time() + timeout
    while True:
        free = free_ram_mb()
        if free is None:
            print("RAM UNMEASURABLE -- proceeding (cannot tell, not low)")
            return 0
        if free >= floor:
            print(f"RAM OK {free:.0f} MB free (floor {floor:.0f})")
            return 0
        if time.time() >= deadline:
            print(f"RAM TIMEOUT {free:.0f} MB free after {timeout:.0f} s (floor {floor:.0f}) -- "
                  "do NOT emit the resume line; tell the Owner")
            if session_id:
                ledger_append(session_id, "ram_timeout", free_mb=round(free))
            return 1
        time.sleep(15)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="/cpp-gsd-long self-checking tools")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("report")
    r.add_argument("--session", required=True)
    sub.add_parser("status")
    s = sub.add_parser("sweep")
    s.add_argument("--dry-run", action="store_true")
    w = sub.add_parser("wait-ram")
    w.add_argument("--floor", type=float, default=RAM_FLOOR_MB)
    w.add_argument("--timeout", type=float, default=600)
    w.add_argument("--session", default="")
    p = sub.add_parser("preflight")
    p.add_argument("--session", required=True)
    p.add_argument("--cwd", required=True)
    p.add_argument("--command", required=True)
    t = sub.add_parser("thresholds", help="narrow THIS session's context wall while it is running")
    t.add_argument("--session", required=True)
    t.add_argument("--set", dest="spec", default="",
                   help='"snapshot,advisory,rearm" as percentages used, e.g. "35,40,30"')
    t.add_argument("--reason", default="")
    t.add_argument("--clear", action="store_true")
    args = ap.parse_args(argv)

    if args.cmd == "report":
        print(json.dumps(report(args.session), indent=2))
        return 0
    if args.cmd == "status":
        print(json.dumps(status(), indent=2))
        return 0
    if args.cmd == "sweep":
        print(json.dumps(sweep(dry_run=args.dry_run), indent=2))
        return 0
    if args.cmd == "wait-ram":
        return wait_ram(args.floor, args.timeout, args.session)
    if args.cmd == "thresholds":
        if args.clear:
            print("CLEARED" if clear_thresholds(args.session) else "ABSENT")
            return 0
        if not args.spec:
            current = read_thresholds(args.session)
            print(json.dumps(current, indent=2) if current else "ABSENT (watchdog uses env or the constants)")
            return 0 if current else 1
        try:
            print(json.dumps(write_thresholds(args.session, args.spec, args.reason), indent=2))
        except (ValueError, RuntimeError) as exc:
            sys.stderr.write(f"REFUSED: {exc}\n")
            return 2
        return 0
    ok, why = arm_preflight(args.session, args.cwd, args.command)
    print(("OK: " if ok else "REFUSED: ") + why)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
