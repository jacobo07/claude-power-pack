#!/usr/bin/env python3
"""M7 -- Token Intelligence System (TIS) probe for verify_spp.

Four sub-checks:

  T1  tools/tis.py imports cleanly from cold state.
  T2  vault/token_logs/ directory exists or can be created.
  T3  tools/tis_report.py --summary exits 0 (may be empty).
  T4  tools/tis_handoff.py exits 0 (may report INSUFFICIENT_TELEMETRY).

Exit 0 iff all 4 pass. Exit 1 if any sub-check fails.
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PP_ROOT = HERE.parent
PYTHON = sys.executable


def _step(label: str, ok: bool, detail: str = "") -> bool:
    print(f"{'OK' if ok else 'FAIL'}  {label}  {detail}")
    return ok


def t1_import_tis() -> bool:
    try:
        sys.path.insert(0, str(HERE))
        import tis  # noqa: F401
        return _step("T1 tis-import", True, "module imports")
    except Exception as exc:
        return _step("T1 tis-import", False,
                     f"{type(exc).__name__}: {exc}")


def t2_logs_dir() -> bool:
    try:
        sys.path.insert(0, str(HERE))
        import tis  # noqa: E402
        tis.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        ok = tis.LOGS_DIR.is_dir()
        return _step("T2 logs-dir", ok,
                     f"path={tis.LOGS_DIR.relative_to(PP_ROOT)}")
    except Exception as exc:
        return _step("T2 logs-dir", False,
                     f"{type(exc).__name__}: {exc}")


def t3_report_summary() -> bool:
    proc = subprocess.run(
        [PYTHON, str(HERE / "tis_report.py"), "--summary"],
        capture_output=True, text=True, timeout=30,
    )
    ok = proc.returncode == 0
    return _step("T3 report-summary", ok,
                 f"rc={proc.returncode} stdout_lines="
                 f"{len(proc.stdout.splitlines())}")


def t4_handoff() -> bool:
    proc = subprocess.run(
        [PYTHON, str(HERE / "tis_handoff.py")],
        capture_output=True, text=True, timeout=30,
    )
    ok = proc.returncode == 0 and (
        "recommended_action" in proc.stdout
        or "INSUFFICIENT_TELEMETRY" in proc.stdout
    )
    return _step("T4 handoff", ok,
                 f"rc={proc.returncode} has_action="
                 f"{'recommended_action' in proc.stdout}")


def main() -> int:
    results = [t1_import_tis(), t2_logs_dir(),
               t3_report_summary(), t4_handoff()]
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"\nTIS_PROBE = {passed}/{total}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
