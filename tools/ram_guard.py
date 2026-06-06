#!/usr/bin/env python3
"""ram_guard.py - pre-crash RAM advisory for the Claude Code session.

FASE -1 forensics (2026-06-04, RAM Optimization Sprint) established the
empirical reality:

  * The PP's OWN footprint (node hooks + python) is a flat ~12 MB. The
    "378 MB node" reading at session start was a hook-fanout spike that
    self-cleaned to ~10 MB within minutes (``child.unref()`` works).
  * The RAM that crashes the host is ``claude.exe`` itself -- a native
    V8 heap that grew 5.9 GB -> 25 GB resident (65 GB committed) within a
    SINGLE long session, stable across samples.

The PP cannot shrink that heap by killing processes. The ONLY lever is
reducing context: ``/kclear``, ``/compact``, or a session restart. So
``ram_guard`` is an ADVISORY, not a reaper. It samples ``claude.exe``
working-set and, when it crosses a threshold, recommends ``/kclear`` and
ensures a crash-recovery snapshot exists BEFORE the possible OOM -- not
after.

Thresholds (working set summed across ``claude.exe`` procs), env-tunable:
  >= PP_RAM_WARN_GB (default 20) -> advisory: "consider /kclear" + ensure snapshot
  >= PP_RAM_CRIT_GB (default 28) -> CRITICAL: force a fresh snapshot now

NOTE on calibration: the RAM Optimization Sprint plan named 8 GB / 11 GB.
Those were pre-forensic guesses. The forensics observed claude.exe stable
at 25 GB resident WITHOUT a crash, so 8/11 would fire on essentially every
long session (alert fatigue = monitor theater). The defaults are
recalibrated to the observed danger zone; override via env for your host.

Measurement is via PowerShell ``Get-Process`` (NOT ``Get-CimInstance``,
which hung twice under ``-NonInteractive`` on this host -- sealed
2026-06-04). ``psutil`` is used when importable (cross-platform). If
neither yields a number the status is ``no-measurement`` -- an honest
sentinel, never a fabricated 0.

Exit code is ALWAYS 0 (advisory; never blocks a Stop event).

Usage:
  python tools/ram_guard.py            # human one-liner
  python tools/ram_guard.py --json     # machine-readable verdict
  python tools/ram_guard.py --no-snapshot   # measure+advise, skip snapshot
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

PP_PATH = Path(__file__).resolve().parents[1]

# Threshold calibration (GB). NORMAL = the forensic danger zone (claude.exe was
# stable at 25 GB without crashing). GAMING = aggressive thresholds for when a
# Minecraft JVM (javaw.exe) is co-resident eating 4-8 GB, so a 32 GB host
# exhausts far sooner -- fire the /kclear advisory EARLY, before OOM.
NORMAL_WARN_GB = 20.0
NORMAL_CRIT_GB = 28.0
GAMING_WARN_GB = 8.0
GAMING_CRIT_GB = 12.0

# Backward-compatible module constants (evaluate() defaults + any importer):
# the NORMAL thresholds, env-overridable. Gaming resolution happens per-run in
# resolve_thresholds() so an explicit env override ALWAYS wins.
WARN_GB = float(os.environ.get("PP_RAM_WARN_GB", NORMAL_WARN_GB))
CRIT_GB = float(os.environ.get("PP_RAM_CRIT_GB", NORMAL_CRIT_GB))


def resolve_thresholds(gaming_mode: bool) -> tuple[float, float]:
    """(warn_gb, crit_gb) for this run. Gaming mode lowers the DEFAULTS to 8/12;
    an explicit PP_RAM_WARN_GB / PP_RAM_CRIT_GB env var always wins (a
    host-specific override is honored gaming or not)."""
    warn_default = GAMING_WARN_GB if gaming_mode else NORMAL_WARN_GB
    crit_default = GAMING_CRIT_GB if gaming_mode else NORMAL_CRIT_GB
    warn = float(os.environ.get("PP_RAM_WARN_GB", warn_default))
    crit = float(os.environ.get("PP_RAM_CRIT_GB", crit_default))
    return warn, crit


def _javaw_count(timeout: int = 10) -> int:
    """Number of javaw.exe (Minecraft JVM) processes. psutil first, PowerShell
    Get-Process fallback (NOT CIM -- the host-hang sentinel). 0 on any failure
    (fail-safe: never falsely activate gaming mode)."""
    try:
        import psutil  # type: ignore
        return sum(
            1 for p in psutil.process_iter(["name"])
            if (p.info.get("name") or "").lower() in ("javaw.exe", "javaw")
        )
    except Exception:  # noqa: BLE001
        pass
    cmd = ("(Get-Process javaw -ErrorAction SilentlyContinue | "
           "Measure-Object).Count")
    for exe in ("powershell.exe", "powershell", "pwsh"):
        try:
            r = subprocess.run(
                [exe, "-NoProfile", "-NonInteractive", "-Command", cmd],
                capture_output=True, text=True, timeout=timeout,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
        except Exception:  # noqa: BLE001
            return 0
        out = (r.stdout or "").strip().lstrip("﻿")
        if r.returncode == 0 and out:
            try:
                return int(out.splitlines()[-1].strip())
            except ValueError:
                return 0
    return 0


def minecraft_active(_count_fn=None) -> bool:
    """True when a Minecraft JVM (javaw.exe) is running -> Gaming Mode.
    _count_fn injectable for hermetic tests. Fail-safe: any error -> False."""
    fn = _count_fn or _javaw_count
    try:
        return fn() > 0
    except Exception:  # noqa: BLE001
        return False


def build_gaming_advisory(verdict: dict, work_state: dict | None) -> str:
    """Gaming-mode advisory embedding the saved work_state (task + commit +
    exact resume). ASCII-only ([GAMING MODE] marker, not an emoji) so it is
    safe to print on a cp1252 Windows console. Fail-open: work_state None ->
    still a valid /kclear advisory."""
    ws_gb = verdict.get("ws_gb")
    warn_gb = verdict.get("warn_gb")
    crit_gb = verdict.get("crit_gb")
    crit = verdict.get("level") == "critical"
    tag = "RAM CRITICAL" if crit else "RAM high"
    if work_state:
        task = work_state.get("task") or "(unknown task)"
        commit = work_state.get("last_commit") or "(none)"
        sid = work_state.get("session_id") or ""
        resume = f"claude --resume {sid}" if sid else "claude --resume <session_id>"
        saved = (f"Work state SAVED: {task[:80]} ({commit}). "
                 f"After /kclear, resume with: {resume}. ")
    else:
        saved = "Work-state save unavailable (fail-open -- advisory still fires). "
    return (
        f"[GAMING MODE] {tag}: claude.exe {ws_gb} GB "
        f"(Minecraft/javaw active -> aggressive thresholds {warn_gb}/{crit_gb} GB). "
        f"{saved}Run /kclear now to reclaim context RAM before the host OOMs."
    )


def _save_work_state_safe(cwd: str, session_id: str | None) -> dict | None:
    """save_work_state, fail-open. Resolves an exact session_id from the cwd's
    latest transcript when none was passed, so the resume line is exact even
    when ram_guard runs without --session-id. None on any failure."""
    try:
        sys.path.insert(0, str(PP_PATH))
        from modules.cpc_os.work_state_saver import save_work_state  # type: ignore
        if not session_id:
            try:
                from modules.cpc_os.snapshot import resolve_last_session  # type: ignore
                session_id = resolve_last_session(cwd)
            except Exception:  # noqa: BLE001
                session_id = None
        return save_work_state(cwd, session_id=session_id)
    except Exception:  # noqa: BLE001
        return None

# PowerShell measurement: Get-Process only (no CIM). Sums WorkingSet64
# across every claude.exe process and writes the MB integer to stdout.
_PS_MEASURE = (
    "$ErrorActionPreference='SilentlyContinue';"
    "$c = Get-Process claude -ErrorAction SilentlyContinue;"
    "if ($c) {"
    " [math]::Round((($c | Measure-Object WorkingSet64 -Sum).Sum)/1MB) }"
    " else { 0 }"
)


def _claude_ram_mb_psutil() -> float | None:
    """Sum RSS of every claude* process via psutil. None if unavailable."""
    try:
        import psutil  # type: ignore
    except Exception:  # noqa: BLE001
        return None
    try:
        total = 0
        found = False
        for p in psutil.process_iter(["name", "memory_info"]):
            name = (p.info.get("name") or "").lower()
            if "claude" in name:
                mi = p.info.get("memory_info")
                if mi is not None:
                    total += mi.rss
                    found = True
        return round(total / (1024 * 1024), 1) if found else 0.0
    except Exception:  # noqa: BLE001
        return None


def _claude_ram_mb_powershell() -> float | None:
    """Sum WorkingSet64 of claude.exe via PowerShell Get-Process. None on
    failure (honest sentinel; the caller distinguishes 0.0 'no procs' from
    None 'could not measure')."""
    for exe in ("powershell.exe", "powershell", "pwsh"):
        try:
            r = subprocess.run(
                [exe, "-NoProfile", "-NonInteractive", "-Command", _PS_MEASURE],
                capture_output=True, text=True, timeout=15,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
        except Exception:  # noqa: BLE001
            return None
        out = (r.stdout or "").strip().lstrip("﻿")
        if r.returncode == 0 and out:
            try:
                return float(out.splitlines()[-1].strip())
            except ValueError:
                return None
    return None


def claude_ram_mb() -> float | None:
    """Best-effort claude.exe RAM in MB. psutil first (cross-platform),
    PowerShell fallback (Windows), else None."""
    v = _claude_ram_mb_psutil()
    if v is not None:
        return v
    return _claude_ram_mb_powershell()


def evaluate(ws_mb: float | None,
             warn_gb: float = WARN_GB,
             crit_gb: float = CRIT_GB) -> dict:
    """Pure verdict function (no I/O) -- the unit-testable core.

    Returns a dict with: level, ws_mb, ws_gb, warn_gb, crit_gb,
    snapshot (bool: should a snapshot be ensured), advisory (str).
    """
    if ws_mb is None:
        return {
            "level": "no-measurement",
            "ws_mb": None, "ws_gb": None,
            "warn_gb": warn_gb, "crit_gb": crit_gb,
            "snapshot": False,
            "advisory": ("RAM not measured (no psutil, PowerShell "
                         "unavailable or claude.exe query failed)."),
        }
    ws_gb = round(ws_mb / 1024, 2)
    if ws_mb >= crit_gb * 1024:
        level, snap = "critical", True
        advisory = (
            f"CRITICAL: claude.exe working set {ws_gb} GB >= {crit_gb} GB. "
            "OOM risk. A fresh crash-recovery snapshot is being forced now. "
            "Run /kclear (or /compact) immediately to reclaim context RAM."
        )
    elif ws_mb >= warn_gb * 1024:
        level, snap = "warn", True
        advisory = (
            f"WARN: claude.exe working set {ws_gb} GB >= {warn_gb} GB. "
            "Consider /kclear soon to reclaim context RAM. Snapshot ensured."
        )
    else:
        level, snap = "ok", False
        advisory = (
            f"OK: claude.exe working set {ws_gb} GB (< {warn_gb} GB warn)."
        )
    return {
        "level": level, "ws_mb": ws_mb, "ws_gb": ws_gb,
        "warn_gb": warn_gb, "crit_gb": crit_gb,
        "snapshot": snap, "advisory": advisory,
    }


def ensure_snapshot() -> dict:
    """Best-effort crash-recovery snapshot via the CPC-OS snapshot module.
    Never raises; returns {ok, detail}."""
    try:
        sys.path.insert(0, str(PP_PATH))
        from modules.cpc_os.snapshot import generate_snapshot  # type: ignore
        generate_snapshot()
        return {"ok": True, "detail": "generate_snapshot() ok"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "detail": f"{type(exc).__name__}: {exc}"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--json", action="store_true",
                    help="emit JSON verdict on stdout")
    ap.add_argument("--no-snapshot", action="store_true",
                    help="do not force/ensure a snapshot even at warn/crit")
    ap.add_argument("--cwd", default=None,
                    help="session cwd for work-state (default: getcwd)")
    ap.add_argument("--session-id", default=None,
                    help="session id for the exact resume line (default: "
                         "PP_EVT_SID env, else resolved from cwd's transcript)")
    args = ap.parse_args(argv)

    cwd = args.cwd or os.getcwd()
    session_id = args.session_id or os.environ.get("PP_EVT_SID")

    # Gaming Mode: a Minecraft JVM (javaw.exe) co-resident -> aggressive
    # thresholds (8/12 GB) so the /kclear advisory fires before the 32 GB host
    # OOMs. Non-gaming -> identical to before (NORMAL 20/28).
    gaming = minecraft_active()
    warn_gb, crit_gb = resolve_thresholds(gaming)

    verdict = evaluate(claude_ram_mb(), warn_gb=warn_gb, crit_gb=crit_gb)
    verdict["gaming_mode"] = gaming

    if verdict["snapshot"] and not args.no_snapshot:
        # Gaming order (M2): save work_state FIRST (fail-open), THEN refresh the
        # snapshot (M3), THEN emit the advisory embedding the saved state. The
        # non-gaming path is byte-identical to before.
        work_state = None
        if gaming:
            work_state = _save_work_state_safe(cwd, session_id)
            verdict["work_state_path"] = (work_state or {}).get("_path")
        verdict["snapshot_result"] = ensure_snapshot()
        if gaming:
            verdict["advisory"] = build_gaming_advisory(verdict, work_state)

    if args.json:
        print(json.dumps(verdict))
    else:
        print(verdict["advisory"])

    # ALWAYS exit 0: advisory never blocks a Stop event.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
