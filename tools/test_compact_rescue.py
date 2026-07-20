#!/usr/bin/env python3
"""Compact Rescue Test Suite -- BL-COMPACT-001 (M5).

7 V-gates verifying the /compact 95% hang rescue stack is present
and minimally functional:

  V-COMPACT-RESCUE-EXISTS    tools/compact_rescue.ps1 exists
  V-COMPACT-CMD-EXISTS       commands/compact-rescue.md exists
  V-COMPACT-DETECTOR-EXISTS  tools/compact_hang_detector.py exists
  V-COMPACT-DRYRUN           rescue DryRun emits valid JSON + log
  V-COMPACT-GUARD-ACTIVE     rescue aborts when .jsonl is recent
  V-COMPACT-UKDL-PR          ukdl-universal.md has PR-COMPACT-001
  V-BASELINE-INTACT          existing PP modules still import

Run:
  python tools/test_compact_rescue.py

Exit 0 on all PASS, exit 1 on any FAIL. CI-friendly.
"""
from __future__ import annotations

import json
import platform
import subprocess
import sys
import time
from pathlib import Path

PP = Path(__file__).resolve().parent.parent
RESCUE = PP / "tools" / "compact_rescue.ps1"
SLASH_CMD = PP / "commands" / "compact-rescue.md"
DETECTOR = PP / "tools" / "compact_hang_detector.py"
UKDL = PP / "vault" / "knowledge_base" / "ukdl-universal.md"
REPRO = PP / "vault" / "knowledge_base" / "compact-95-hang-repro.md"
RESCUE_LOG = Path.home() / "AppData" / "Local" / "Temp" / "pp-compact-rescue.log"


_pass = 0
_fail = 0


def gate(name: str, ok: bool, evidence: str = "") -> None:
    global _pass, _fail
    if ok:
        _pass += 1
        print(f"  PASS  {name}  {evidence}")
    else:
        _fail += 1
        print(f"  FAIL  {name}  {evidence}")


def run_ps(script: Path, *args: str, timeout: int = 30) -> tuple[int, str, str]:
    cmd = ["powershell.exe", "-NoProfile", "-NonInteractive",
           "-ExecutionPolicy", "Bypass", "-File", str(script)] + list(args)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except OSError as exc:
        return 125, "", str(exc)


print("=" * 64)
print("COMPACT RESCUE TEST -- BL-COMPACT-001")
print("=" * 64)

# --- V-COMPACT-RESCUE-EXISTS ---------------------------------------------
gate(
    "V-COMPACT-RESCUE-EXISTS",
    RESCUE.is_file(),
    f"({RESCUE.stat().st_size if RESCUE.is_file() else 0} bytes)",
)

# --- V-COMPACT-CMD-EXISTS -------------------------------------------------
gate(
    "V-COMPACT-CMD-EXISTS",
    SLASH_CMD.is_file(),
    f"({SLASH_CMD.stat().st_size if SLASH_CMD.is_file() else 0} bytes)",
)

# --- V-COMPACT-DETECTOR-EXISTS -------------------------------------------
gate(
    "V-COMPACT-DETECTOR-EXISTS",
    DETECTOR.is_file(),
    f"({DETECTOR.stat().st_size if DETECTOR.is_file() else 0} bytes)",
)

# --- V-COMPACT-DRYRUN ----------------------------------------------------
# DryRun with -IdleThresholdSeconds 0 bypasses the recency guard so we
# actually exercise the dry-run JSON-emit branch, not the abort branch.
if platform.system() == "Windows" and RESCUE.is_file():
    log_before = RESCUE_LOG.stat().st_mtime if RESCUE_LOG.is_file() else 0.0
    rc, out, err = run_ps(
        RESCUE, "-DryRun", "-IdleThresholdSeconds", "0", timeout=30,
    )
    time.sleep(0.3)
    log_after = RESCUE_LOG.stat().st_mtime if RESCUE_LOG.is_file() else 0.0
    # Verify: rc==0, log advanced, JSON object visible in stdout.
    json_seen = False
    try:
        # The script prints '=== DRY RUN ===' followed by a JSON block.
        start = out.find("{")
        end = out.rfind("}")
        if start >= 0 and end > start:
            parsed = json.loads(out[start:end + 1])
            json_seen = isinstance(parsed, dict) and "rescue_reason" in parsed
    except (ValueError, TypeError):
        json_seen = False
    dryrun_ok = (rc == 0) and (log_after > log_before) and json_seen
    dryrun_evidence = (
        f"(rc={rc}, log_advanced={log_after > log_before}, "
        f"json_well_formed={json_seen})"
    )
elif platform.system() != "Windows":
    dryrun_ok = True
    dryrun_evidence = "(skipped: non-Windows)"
else:
    dryrun_ok = False
    dryrun_evidence = "(script not found)"
gate("V-COMPACT-DRYRUN", dryrun_ok, dryrun_evidence)

# --- V-COMPACT-GUARD-ACTIVE ----------------------------------------------
# Default threshold (120s). Since this test session is actively writing
# .jsonl, the guard MUST fire and the rescue MUST abort with exit 1.
if platform.system() == "Windows" and RESCUE.is_file():
    rc, out, err = run_ps(RESCUE, "-DryRun", timeout=30)
    guard_ok = (rc == 1) and ("ABORT" in out or "looks active" in out.lower())
    guard_evidence = (
        f"(rc={rc} expected 1, abort_msg_present="
        f"{'ABORT' in out or 'looks active' in out.lower()})"
    )
elif platform.system() != "Windows":
    guard_ok = True
    guard_evidence = "(skipped: non-Windows)"
else:
    guard_ok = False
    guard_evidence = "(script not found)"
gate("V-COMPACT-GUARD-ACTIVE", guard_ok, guard_evidence)

# --- V-COMPACT-UKDL-PR ---------------------------------------------------
ukdl_text = UKDL.read_text(encoding="utf-8", errors="replace") if UKDL.is_file() else ""
ukdl_ok = (
    "PR-COMPACT-001" in ukdl_text
    and "T-COMPACT-001" in ukdl_text
    and "BL-COMPACT-001" in ukdl_text
)
gate(
    "V-COMPACT-UKDL-PR",
    ukdl_ok,
    "(PR+T+BL markers present)" if ukdl_ok else "(missing one or more markers)",
)

# --- V-COMPACT-INTERACTIVE-FLAG ------------------------------------------
# Detector must accept --interactive + --dry-notify without crashing.
# On a healthy session this returns "OK: no compact hang detected" rc=0;
# the interactive code path is never reached, but argparse + global
# wiring is exercised.
DETECTOR_PY = PP / "tools" / "compact_hang_detector.py"
if DETECTOR_PY.is_file():
    try:
        r = subprocess.run(
            [sys.executable, str(DETECTOR_PY), "check",
             "--interactive", "--dry-notify"],
            capture_output=True, text=True, timeout=30,
        )
        intr_ok = r.returncode == 0 and "OK" in (r.stdout or "")
        intr_evidence = (
            f"(rc={r.returncode}, OK_in_stdout="
            f"{'OK' in (r.stdout or '')})"
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        intr_ok = False
        intr_evidence = f"(crash: {exc})"
else:
    intr_ok = False
    intr_evidence = "(detector script not found)"
gate("V-COMPACT-INTERACTIVE-FLAG", intr_ok, intr_evidence)

# --- V-COMPACT-SNOOZE-CLEAR ----------------------------------------------
# clear-snooze action must drop the snooze file. Synthesise one first
# so the test exercises the real removal path, not the no-op branch.
SNOOZE_FILE = Path.home() / ".claude" / "state" / "compact_snooze_until.txt"
if DETECTOR_PY.is_file():
    try:
        SNOOZE_FILE.parent.mkdir(parents=True, exist_ok=True)
        SNOOZE_FILE.write_text(str(time.time() + 60), encoding="utf-8")
        existed_before = SNOOZE_FILE.is_file()
        r = subprocess.run(
            [sys.executable, str(DETECTOR_PY), "clear-snooze"],
            capture_output=True, text=True, timeout=10,
        )
        gone_after = not SNOOZE_FILE.is_file()
        snooze_ok = (
            r.returncode == 0 and existed_before and gone_after
        )
        snooze_evidence = (
            f"(rc={r.returncode}, existed={existed_before}, "
            f"gone_after={gone_after})"
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        snooze_ok = False
        snooze_evidence = f"(crash: {exc})"
else:
    snooze_ok = False
    snooze_evidence = "(detector script not found)"
gate("V-COMPACT-SNOOZE-CLEAR", snooze_ok, snooze_evidence)

# --- V-COMPACT-DASH-COMPAT -----------------------------------------------
# Backwards-compatibility: old --check dash form must still work after
# the argparse migration.
if DETECTOR_PY.is_file():
    try:
        r = subprocess.run(
            [sys.executable, str(DETECTOR_PY), "--check"],
            capture_output=True, text=True, timeout=30,
        )
        dash_ok = r.returncode == 0 and "OK" in (r.stdout or "")
        dash_evidence = f"(rc={r.returncode}, OK_present={'OK' in (r.stdout or '')})"
    except (subprocess.TimeoutExpired, OSError) as exc:
        dash_ok = False
        dash_evidence = f"(crash: {exc})"
else:
    dash_ok = False
    dash_evidence = "(detector script not found)"
gate("V-COMPACT-DASH-COMPAT", dash_ok, dash_evidence)

# --- V-BASELINE-INTACT ---------------------------------------------------
# Verify pre-existing modules still import cleanly -- catches regressions
# from this work touching modules unintentionally.
baseline_ok = True
baseline_msg = []
sys.path.insert(0, str(PP))
for modpath in (
    "modules.pp_agents.signals.health",
    "modules.pp_agents.proactive_core",
):
    try:
        __import__(modpath)
        baseline_msg.append(f"{modpath}: OK")
    except (ImportError, ModuleNotFoundError) as exc:
        baseline_ok = False
        baseline_msg.append(f"{modpath}: FAIL {exc}")
gate("V-BASELINE-INTACT", baseline_ok, "(" + "; ".join(baseline_msg) + ")")

# --- Summary -------------------------------------------------------------
print()
print("=" * 64)
print(f"RESULT: {_pass} PASS / {_fail} FAIL ({_pass + _fail} total)")
print("=" * 64)
def test_gate():
    """Expose the V-gate result to pytest.

    The module body above runs at import and computes _fail. Without this
    assertion pytest would collect the file, execute the gate, and report
    green regardless of the outcome.
    """
    assert _fail == 0, f"{_fail} V-gate failure(s)"


if __name__ == "__main__":
    sys.exit(0 if _fail == 0 else 1)
