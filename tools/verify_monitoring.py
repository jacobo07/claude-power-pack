#!/usr/bin/env python3
"""verify_monitoring.py -- MONITORING_AXIS probe for verify_spp.

Five sub-checks; all must pass to return exit 0:

  1. modules/monitoring/monitor.py imports cleanly.
  2. modules/monitoring/alert.py imports cleanly.
  3. modules/monitoring/observe.py imports cleanly.
  4. vault/monitor/ contains at least 3 config files (one per
     productive project).
  5. vault/alerts/ exists or can be created (write-able).

Plus a soft sanity check: `--daemon` prints install instructions
without launching anything. This catches the worst kind of regression
(silently auto-installing a cron job).

Network availability is NOT a gate: if the host cannot reach the
productive URLs, the V-block tests (mocked) already exercise the
debounce + alert logic, and the deploy-spec's V-KOBIICRAFT SKIP
posture is honored by --once at runtime.

Exit codes:
  0 -- all 5 sub-checks pass
  1 -- one or more sub-checks failed (real defect)
"""
from __future__ import annotations

import io
import json
import os
import sys
from contextlib import redirect_stdout
from pathlib import Path

PP = Path(__file__).resolve().parents[1]


def _check_import_monitor() -> tuple[bool, str]:
    try:
        sys.path.insert(0, str(PP / "modules" / "monitoring"))
        import monitor  # noqa: F401
        return True, "monitor.py import OK"
    except Exception as exc:  # noqa: BLE001
        return False, f"monitor.py import FAILED: {type(exc).__name__}: {exc}"


def _check_import_alert() -> tuple[bool, str]:
    try:
        sys.path.insert(0, str(PP / "modules" / "monitoring"))
        import alert  # noqa: F401
        return True, "alert.py import OK"
    except Exception as exc:  # noqa: BLE001
        return False, f"alert.py import FAILED: {type(exc).__name__}: {exc}"


def _check_import_observe() -> tuple[bool, str]:
    try:
        sys.path.insert(0, str(PP / "modules" / "monitoring"))
        import observe  # noqa: F401
        return True, "observe.py import OK"
    except Exception as exc:  # noqa: BLE001
        return False, f"observe.py import FAILED: {type(exc).__name__}: {exc}"


def _check_monitor_configs() -> tuple[bool, str]:
    mdir = PP / "vault" / "monitor"
    if not mdir.is_dir():
        return False, f"vault/monitor/ not a directory: {mdir}"
    configs: list[str] = []
    for f in sorted(mdir.glob("*.json")):
        if f.name.endswith("_state.json"):
            continue
        try:
            json.loads(f.read_text(encoding="utf-8"))
            configs.append(f.stem)
        except (OSError, json.JSONDecodeError) as exc:
            return False, f"{f.name} not valid JSON: {exc}"
    if len(configs) < 3:
        return False, f"vault/monitor/ has {len(configs)} configs (<3): {configs}"
    return True, f"vault/monitor/ has {len(configs)} configs: {configs}"


def _check_alerts_dir_writable() -> tuple[bool, str]:
    adir = PP / "vault" / "alerts"
    try:
        adir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return False, f"cannot create vault/alerts/: {exc}"
    probe = adir / ".write_probe"
    try:
        probe.write_text("ok")
        probe.unlink()
    except OSError as exc:
        return False, f"vault/alerts/ not writable: {exc}"
    return True, f"vault/alerts/ writable at {adir}"


def _check_daemon_no_install() -> tuple[bool, str]:
    """Sanity: --daemon prints instructions, never invokes schtasks/crontab.

    We re-import observe with a fresh module namespace and invoke the
    daemon path against the first available config. We then assert the
    stdout contains the literal "Task Scheduler" + "crontab -e" strings,
    and that the source code of observe.cmd_daemon contains zero calls
    to subprocess that match the install targets.
    """
    sys.path.insert(0, str(PP / "modules" / "monitoring"))
    import observe as observe_mod
    import re

    mdir = PP / "vault" / "monitor"
    configs = [f.stem for f in mdir.glob("*.json") if not f.name.endswith("_state.json")]
    if not configs:
        return False, "no monitor configs to test --daemon against"

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = observe_mod.main(["--daemon", "--project", configs[0]])
    out = buf.getvalue()
    if rc != 0:
        return False, f"--daemon returned rc={rc}, expected 0"
    if "crontab -e" not in out or "Task Scheduler" not in out:
        return False, "expected crontab+Task Scheduler instructions absent from --daemon stdout"

    src = (PP / "modules" / "monitoring" / "observe.py").read_text(encoding="utf-8")
    bad = re.findall(
        r"subprocess\.\w+\s*\([^)]*(schtasks|crontab|Register-ScheduledTask)",
        src,
    )
    if bad:
        return False, f"observe.py invokes install commands: {bad}"
    return True, "--daemon prints instructions; no subprocess install sites"


def main() -> int:
    checks = [
        ("import monitor.py", _check_import_monitor),
        ("import alert.py", _check_import_alert),
        ("import observe.py", _check_import_observe),
        ("vault/monitor/ has >=3 configs", _check_monitor_configs),
        ("vault/alerts/ writable", _check_alerts_dir_writable),
        ("--daemon no auto-install", _check_daemon_no_install),
    ]
    passed = 0
    failed: list[str] = []
    for name, fn in checks:
        ok, msg = fn()
        tag = "OK  " if ok else "FAIL"
        print(f"  [{tag}] {name:<32s} {msg}")
        if ok:
            passed += 1
        else:
            failed.append(name)
    total = len(checks)
    print(f"MONITORING_AXIS: {passed}/{total} sub-checks PASS")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
