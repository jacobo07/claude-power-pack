#!/usr/bin/env python3
"""
Playwright MCP Resilience Test Suite -- BL-PLAYWRIGHT-001 (Option A).

11 V-gates verifying that the entire Playwright transport-resilience
stack is present and minimally functional.

Run:
  python tools/test_playwright_resilience.py

Exit 0 = all PASS, exit 1 = any FAIL. CI-friendly.
"""
from __future__ import annotations

import platform
import subprocess
import sys
import time
from pathlib import Path

PP = Path(__file__).resolve().parent.parent
KILLER = PP / "tools" / "playwright_stale_killer.ps1"
WATCHDOG = PP / "tools" / "playwright_watchdog.ps1"
CHECK = PP / "tools" / "check_playwright_mcp.py"
REPRO = PP / "vault" / "knowledge_base" / "playwright-transport-repro.md"
UKDL = PP / "vault" / "knowledge_base" / "ukdl-universal.md"
KILLER_LOG = Path.home() / "AppData" / "Local" / "Temp" / "pp-playwright-killer.log"


_pass = 0
_fail = 0
_results: list[tuple[str, bool, str]] = []


def gate(name: str, ok: bool, evidence: str = "") -> None:
    global _pass, _fail
    if ok:
        _pass += 1
        print(f"  PASS  {name}  {evidence}")
    else:
        _fail += 1
        print(f"  FAIL  {name}  {evidence}")
    _results.append((name, ok, evidence))


def run_ps(script: Path, *args: str, timeout: int = 30) -> tuple[int, str, str]:
    """Run a .ps1 via powershell.exe, return (rc, stdout, stderr)."""
    cmd = ["powershell.exe", "-NoProfile", "-NonInteractive",
           "-ExecutionPolicy", "Bypass", "-File", str(script)] + list(args)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except Exception as exc:
        return 125, "", str(exc)


print("=" * 64)
print("PLAYWRIGHT MCP RESILIENCE TEST -- BL-PLAYWRIGHT-001")
print("=" * 64)

# --- V-PW-KILLER-EXISTS --------------------------------------------------
gate("V-PW-KILLER-EXISTS", KILLER.is_file(),
     f"({KILLER.stat().st_size if KILLER.is_file() else 0} bytes)")

# --- V-PW-WATCHDOG-EXISTS ------------------------------------------------
gate("V-PW-WATCHDOG-EXISTS", WATCHDOG.is_file(),
     f"({WATCHDOG.stat().st_size if WATCHDOG.is_file() else 0} bytes)")

# --- V-PW-CHECK-EXISTS ---------------------------------------------------
gate("V-PW-CHECK-EXISTS", CHECK.is_file(),
     f"({CHECK.stat().st_size if CHECK.is_file() else 0} bytes)")

# --- V-PW-REPRO-DOC ------------------------------------------------------
gate("V-PW-REPRO-DOC", REPRO.is_file(),
     f"({REPRO.stat().st_size if REPRO.is_file() else 0} bytes)")

# --- V-PW-UKDL-PR --------------------------------------------------------
ukdl_text = UKDL.read_text(encoding="utf-8", errors="replace") if UKDL.is_file() else ""
gate("V-PW-UKDL-PR", "PR-PW-001" in ukdl_text,
     "(PR-PW-001 marker present)" if "PR-PW-001" in ukdl_text else "(missing)")

# --- V-PW-UKDL-TRAP ------------------------------------------------------
gate("V-PW-UKDL-TRAP", "T-PW-001" in ukdl_text,
     "(T-PW-001 marker present)" if "T-PW-001" in ukdl_text else "(missing)")

# --- V-PW-PLUGIN-SIGNAL --------------------------------------------------
sig_ok = False
sig_evidence = ""
try:
    sys.path.insert(0, str(PP))
    from modules.pp_agents.signals.health import check_playwright_mcp_plugin  # noqa: E402
    sig = check_playwright_mcp_plugin()
    sig_ok = isinstance(sig, dict) and "status" in sig
    sig_evidence = f"({sig!r})"
except Exception as exc:
    sig_evidence = f"(import/call failed: {type(exc).__name__}: {exc})"
gate("V-PW-PLUGIN-SIGNAL", sig_ok, sig_evidence)

# --- V-PW-CHECK-RUNS -----------------------------------------------------
if CHECK.is_file():
    try:
        r = subprocess.run(
            [sys.executable, str(CHECK)],
            capture_output=True, text=True, timeout=30,
        )
        check_ok = r.returncode == 0 and "PLAYWRIGHT MCP PLUGIN STATUS" in (r.stdout or "")
        check_evidence = f"(rc={r.returncode}, status banner {'present' if 'PLAYWRIGHT MCP PLUGIN STATUS' in r.stdout else 'missing'})"
    except Exception as exc:
        check_ok = False
        check_evidence = f"(crash: {exc})"
else:
    check_ok = False
    check_evidence = "(script not found)"
gate("V-PW-CHECK-RUNS", check_ok, check_evidence)

# --- V-PW-WATCHDOG-STATUS ------------------------------------------------
if platform.system() == "Windows" and WATCHDOG.is_file():
    rc, out, err = run_ps(WATCHDOG, "-Action", "status", timeout=20)
    wd_ok = rc == 0 and ("ACTIVE" in out or "NOT installed" in out)
    wd_evidence = f"(rc={rc}, output {'contains state' if wd_ok else 'unexpected'})"
elif platform.system() != "Windows":
    wd_ok = True
    wd_evidence = "(skipped: non-Windows)"
else:
    wd_ok = False
    wd_evidence = "(script not found)"
gate("V-PW-WATCHDOG-STATUS", wd_ok, wd_evidence)

# --- V-PW-KILLER-DRYRUN --------------------------------------------------
if platform.system() == "Windows" and KILLER.is_file():
    log_before = KILLER_LOG.stat().st_mtime if KILLER_LOG.is_file() else 0.0
    rc, out, err = run_ps(KILLER, "-DryRun", "-IdleThresholdMinutes", "0",
                          timeout=30)
    # Wait briefly for the log to flush, then verify the mtime advanced.
    time.sleep(0.3)
    log_after = KILLER_LOG.stat().st_mtime if KILLER_LOG.is_file() else 0.0
    killer_ok = rc == 0 and (log_after > log_before) and KILLER_LOG.is_file()
    killer_evidence = (
        f"(rc={rc}, log mtime advanced: {log_after > log_before}, "
        f"path={KILLER_LOG})"
    )
elif platform.system() != "Windows":
    killer_ok = True
    killer_evidence = "(skipped: non-Windows)"
else:
    killer_ok = False
    killer_evidence = "(script not found)"
gate("V-PW-KILLER-DRYRUN", killer_ok, killer_evidence)

# --- V-BASELINE-INTACT ---------------------------------------------------
# Lightweight: confirm our own modules still import without error.
baseline_ok = True
baseline_msg = []
for modpath in ("modules.pp_agents.signals.health",
                "modules.pp_agents.proactive_core"):
    try:
        __import__(modpath)
        baseline_msg.append(f"{modpath}: import OK")
    except Exception as exc:
        baseline_ok = False
        baseline_msg.append(f"{modpath}: FAIL {exc}")
gate("V-BASELINE-INTACT", baseline_ok, "(" + "; ".join(baseline_msg) + ")")

# --- Summary -------------------------------------------------------------
print()
print("=" * 64)
print(f"RESULT: {_pass} PASS / {_fail} FAIL ({_pass + _fail} total)")
print("=" * 64)
sys.exit(0 if _fail == 0 else 1)
