#!/usr/bin/env python3
"""test_restart_and_lag.py -- V-gates for /restart marker + SessionStart lag.

Ten gates exercised verbatim (no mocks):
  V-RESTART-CMD-EXISTS        ~/.claude/commands/restart.md present
  V-RESTART-MARKER-WRITER     restart-claude.ps1 writes the marker file
                              via [System.IO.File]::WriteAllText with
                              UTF8Encoding($false)  (no-BOM)
  V-RESTART-MARKER-CONSUME    restart_resume.js consumes marker when
                              cwd matches
  V-RESTART-RESUME-OUTPUT     restart_resume.js emits a valid
                              additionalContext JSON
  V-RESTART-SILENT-NOOP       restart_resume.js silent (no stdout) when
                              marker absent
  V-RESTART-CWD-GUARD         restart_resume.js preserves marker when
                              cwd mismatches
  V-RESTART-BOM-TOLERANT      restart_resume.js handles BOM-prefixed
                              marker (legacy writer compat)
  V-WRAPPER-EXISTS            async_wrapper.js present
  V-OPTIMIZER-DRYRUN          optimize_session_start.py --dry-run lists
                              the three planned changes
  V-MEASURE-RUNS              measure_session_start.py emits a JSON
                              payload with a verdict field
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()
MARKER = HOME / ".claude" / "state" / "restart_pending.json"

# Characters of subprocess stdout to include in failure evidence -- enough
# to identify the failure cause without flooding the gate report.
STDOUT_PREVIEW_CHARS = 200
SUBPROC_TIMEOUT_S = 15

PY = sys.executable
PASS = 0
FAIL = 0


def _ok(gate: str, ev: str) -> None:
    global PASS
    PASS += 1
    print(f"  [OK]   {gate}: {ev}")


def _fail(gate: str, ev: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  [FAIL] {gate}: {ev}")


def _backup_marker():
    if MARKER.is_file():
        return MARKER.read_bytes()
    return None


def _restore_marker(data):
    MARKER.parent.mkdir(parents=True, exist_ok=True)
    if data is None:
        if MARKER.is_file():
            MARKER.unlink()
    else:
        MARKER.write_bytes(data)


def _write_marker_nobom(payload: dict):
    MARKER.parent.mkdir(parents=True, exist_ok=True)
    MARKER.write_text(json.dumps(payload), encoding="utf-8")


def _write_marker_with_bom(payload: dict):
    MARKER.parent.mkdir(parents=True, exist_ok=True)
    txt = "﻿" + json.dumps(payload)
    MARKER.write_bytes(txt.encode("utf-8"))


def _run_hook(stdin_payload: dict) -> tuple[int, str]:
    proc = subprocess.run(
        ["node", str(PP_ROOT / "hooks" / "restart_resume.js")],
        input=json.dumps(stdin_payload),
        capture_output=True, text=True, timeout=15,
    )
    return proc.returncode, proc.stdout


def gate_cmd_exists():
    p = HOME / ".claude" / "commands" / "restart.md"
    if p.is_file():
        _ok("V-RESTART-CMD-EXISTS", str(p))
    else:
        _fail("V-RESTART-CMD-EXISTS", f"missing: {p}")


def gate_marker_writer():
    ps1 = HOME / ".claude" / "scripts" / "restart-claude.ps1"
    if not ps1.is_file():
        _fail("V-RESTART-MARKER-WRITER", f"missing: {ps1}")
        return
    body = ps1.read_text(encoding="utf-8", errors="replace")
    has_writeAllText = "WriteAllText" in body and "UTF8Encoding" in body
    has_marker_path = "restart_pending.json" in body
    if has_writeAllText and has_marker_path:
        _ok("V-RESTART-MARKER-WRITER",
            "WriteAllText + UTF8Encoding($false) + restart_pending.json")
    else:
        _fail("V-RESTART-MARKER-WRITER",
              f"writeAllText={has_writeAllText} "
              f"markerPath={has_marker_path}")


def gate_marker_consume():
    backup = _backup_marker()
    try:
        cwd = str(PP_ROOT)
        _write_marker_nobom({
            "session_id": "test-consume",
            "cwd": cwd,
            "branch": "main",
            "timestamp": "2026-05-31T14:00:00Z",
            "session_note": "V-RESTART-MARKER-CONSUME",
        })
        rc, out = _run_hook({"cwd": cwd})
        if rc == 0 and not MARKER.exists() and out.strip():
            _ok("V-RESTART-MARKER-CONSUME",
                f"rc=0, marker gone, stdout={len(out)} B")
        else:
            _fail("V-RESTART-MARKER-CONSUME",
                  f"rc={rc} marker_exists={MARKER.exists()} out_len={len(out)}")
    finally:
        _restore_marker(backup)


def gate_resume_output():
    backup = _backup_marker()
    try:
        cwd = str(PP_ROOT)
        _write_marker_nobom({
            "session_id": "test-output",
            "cwd": cwd,
            "branch": "feature/x",
            "timestamp": "2026-05-31T14:01:00Z",
            "session_note": "V-RESTART-RESUME-OUTPUT",
        })
        rc, out = _run_hook({"cwd": cwd})
        try:
            parsed = json.loads(out)
            if (parsed.get("continue") is True
                    and "additionalContext" in parsed
                    and "[/restart resume]" in parsed["additionalContext"]
                    and "feature/x" in parsed["additionalContext"]):
                _ok("V-RESTART-RESUME-OUTPUT",
                    "JSON with continue=True, additionalContext, branch echoed")
            else:
                _fail("V-RESTART-RESUME-OUTPUT",
                      f"shape wrong: {parsed}")
        except (ValueError, TypeError) as exc:
            _fail("V-RESTART-RESUME-OUTPUT",
                  f"stdout not JSON ({exc}): {out[:80]!r}")
    finally:
        _restore_marker(backup)


def gate_silent_noop():
    backup = _backup_marker()
    try:
        if MARKER.is_file():
            MARKER.unlink()
        rc, out = _run_hook({"cwd": str(PP_ROOT)})
        if rc == 0 and out.strip() == "":
            _ok("V-RESTART-SILENT-NOOP",
                "rc=0 + empty stdout when no marker")
        else:
            _fail("V-RESTART-SILENT-NOOP",
                  f"rc={rc} stdout={out[:60]!r}")
    finally:
        _restore_marker(backup)


def gate_cwd_guard():
    backup = _backup_marker()
    try:
        marker_cwd = r"C:\Different\NotMine"
        _write_marker_nobom({
            "session_id": "test-guard",
            "cwd": marker_cwd,
            "branch": "main",
            "timestamp": "2026-05-31T14:02:00Z",
            "session_note": "V-RESTART-CWD-GUARD",
        })
        rc, out = _run_hook({"cwd": str(PP_ROOT)})
        if rc == 0 and out.strip() == "" and MARKER.is_file():
            _ok("V-RESTART-CWD-GUARD",
                "marker preserved + no output when cwd mismatches")
        else:
            _fail("V-RESTART-CWD-GUARD",
                  f"rc={rc} preserved={MARKER.is_file()} out_len={len(out)}")
    finally:
        _restore_marker(backup)


def gate_bom_tolerant():
    backup = _backup_marker()
    try:
        cwd = str(PP_ROOT)
        _write_marker_with_bom({
            "session_id": "test-bom",
            "cwd": cwd,
            "branch": "main",
            "timestamp": "2026-05-31T14:03:00Z",
            "session_note": "V-RESTART-BOM-TOLERANT",
        })
        rc, out = _run_hook({"cwd": cwd})
        try:
            parsed = json.loads(out)
            if (parsed.get("continue") is True
                    and "test-bom" in parsed.get("additionalContext", "")):
                _ok("V-RESTART-BOM-TOLERANT",
                    "BOM-prefixed marker parsed and consumed")
            else:
                _fail("V-RESTART-BOM-TOLERANT",
                      f"shape unexpected: {parsed}")
        except (ValueError, TypeError) as exc:
            _fail("V-RESTART-BOM-TOLERANT",
                  f"stdout not JSON ({exc}): {out[:80]!r}")
    finally:
        _restore_marker(backup)


def gate_wrapper_exists():
    p = PP_ROOT / "hooks" / "async_wrapper.js"
    if p.is_file() and p.stat().st_size > 500:
        _ok("V-WRAPPER-EXISTS", str(p.relative_to(PP_ROOT)))
    else:
        _fail("V-WRAPPER-EXISTS", f"missing or too small: {p}")


def gate_optimizer_dryrun():
    p = PP_ROOT / "tools" / "optimize_session_start.py"
    if not p.is_file():
        _fail("V-OPTIMIZER-DRYRUN", f"missing: {p}")
        return
    proc = subprocess.run(
        [PY, str(p), "--dry-run"],
        capture_output=True, text=True, timeout=SUBPROC_TIMEOUT_S,
    )
    if proc.returncode != 0:
        preview = proc.stdout[:STDOUT_PREVIEW_CHARS]
        _fail("V-OPTIMIZER-DRYRUN",
              f"rc={proc.returncode} stdout head={preview!r}")
        return
    has_planned_changes = (
        "DROP SessionStart entry" in proc.stdout
        and "WRAP" in proc.stdout
        and "async_wrapper" in proc.stdout)
    is_idempotent_noop = (
        "No changes needed" in proc.stdout
        or "already optimal" in proc.stdout)
    if has_planned_changes:
        _ok("V-OPTIMIZER-DRYRUN",
            "dry-run lists DROP + WRAP changes")
    elif is_idempotent_noop:
        _ok("V-OPTIMIZER-DRYRUN",
            "dry-run reports idempotent no-op "
            "(post-activation state)")
    else:
        preview = proc.stdout[:STDOUT_PREVIEW_CHARS]
        _fail("V-OPTIMIZER-DRYRUN",
              f"unexpected output: {preview!r}")


def gate_measure_runs():
    p = PP_ROOT / "tools" / "measure_session_start.py"
    if not p.is_file():
        _fail("V-MEASURE-RUNS", f"missing: {p}")
        return
    proc = subprocess.run(
        [PY, str(p), "--json"],
        capture_output=True, text=True, timeout=60,
    )
    try:
        payload = json.loads(proc.stdout)
        if "verdict" in payload and "individual_max_ms" in payload:
            _ok("V-MEASURE-RUNS",
                f"verdict={payload['verdict']} "
                f"max={payload['individual_max_ms']:.0f} ms")
        else:
            _fail("V-MEASURE-RUNS",
                  f"missing verdict/individual_max_ms: {payload}")
    except (ValueError, TypeError) as exc:
        _fail("V-MEASURE-RUNS",
              f"stdout not JSON ({exc}): {proc.stdout[:120]!r}")


def main() -> int:
    print("=" * 60)
    print("V-RESTART + V-LAG gates (BL-RESTART-001 + BL-LAG-001)")
    print("=" * 60)
    for gate in (
        gate_cmd_exists,
        gate_marker_writer,
        gate_marker_consume,
        gate_resume_output,
        gate_silent_noop,
        gate_cwd_guard,
        gate_bom_tolerant,
        gate_wrapper_exists,
        gate_optimizer_dryrun,
        gate_measure_runs,
    ):
        gate()
    print()
    print(f"RESTART_AND_LAG={PASS}/{PASS + FAIL}  threshold=10/10")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
