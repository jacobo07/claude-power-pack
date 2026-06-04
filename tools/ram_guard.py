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

# Env-tunable thresholds in GB (see module docstring for calibration).
WARN_GB = float(os.environ.get("PP_RAM_WARN_GB", "20"))
CRIT_GB = float(os.environ.get("PP_RAM_CRIT_GB", "28"))

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
    args = ap.parse_args(argv)

    verdict = evaluate(claude_ram_mb())
    if verdict["snapshot"] and not args.no_snapshot:
        verdict["snapshot_result"] = ensure_snapshot()

    if args.json:
        print(json.dumps(verdict))
    else:
        print(verdict["advisory"])

    # ALWAYS exit 0: advisory never blocks a Stop event.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
