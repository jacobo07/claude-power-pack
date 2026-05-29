"""V-gates for tools/register_global_hooks.py + check_hook_status.py.

Sealed BL-HOOKS-REG-001 (2026-05-29).

The tests redirect ``SETTINGS_PATH`` to a per-test ``tmp`` copy so the
real ``~/.claude/settings.json`` is never touched, even though the
registration script normally writes to that path.

V-gates:
  V-HOOKS-SCRIPT-EXISTS       script + check_hook_status exist + executable
  V-HOOKS-SCRIPT-DRYRUN       --dry-run does NOT modify the settings file
  V-HOOKS-SCRIPT-BACKUP       real run creates .pre-pp-hooks-<ts>.bak
  V-HOOKS-SCRIPT-IDEMPOTENT   running twice does not duplicate entries
  V-HOOKS-CHECK-STATUS        check_hook_status runs from /tmp without crash
  V-HOOKS-MARKER-PRE          uqf_pre_edit_gate referenced by the script
  V-HOOKS-MARKER-POST-OSA     osa_deploy_detector referenced by the script
  V-HOOKS-MARKER-POST-CEPS    bug-hunter-ceps-bridge referenced by the script
  V-HOOKS-MARKER-SESSION      session-start-check referenced by the script
  V-HOOKS-MARKER-STOP         jobs_woz_gate referenced by the script
  V-HOOKS-FILES-EXIST         the 4 JS hooks exist on disk
  V-HOOKS-DOCS-EXIST          docs/HOOKS_SETUP.md exists + non-trivial
  V-BASELINE-INTACT           pytest tests/ -q returns 0 failed
"""
from __future__ import annotations

import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

passes = 0
fails = 0


def _ok(name: str, msg: str = "") -> None:
    global passes
    passes += 1
    print(f"PASS  {name:34s} {msg}")


def _fail(name: str, msg: str = "") -> None:
    global fails
    fails += 1
    print(f"FAIL  {name:34s} {msg}")


def _seed_settings(target_dir: Path) -> Path:
    """Make a minimal settings.json copy under target_dir/.claude/."""
    claude_dir = target_dir / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    target = claude_dir / "settings.json"
    target.write_text(json.dumps({"hooks": {}, "_test_seed": True},
                                 indent=2),
                      encoding="utf-8")
    return target


def _load_register_module():
    sys.path.insert(0, str(ROOT / "tools"))
    mod = importlib.import_module("register_global_hooks")
    return importlib.reload(mod)


def _check_script_exists() -> None:
    reg = ROOT / "tools" / "register_global_hooks.py"
    chk = ROOT / "tools" / "check_hook_status.py"
    if reg.is_file() and chk.is_file() and reg.stat().st_size > 500:
        _ok("V-HOOKS-SCRIPT-EXISTS",
            f"{reg.stat().st_size}+{chk.stat().st_size} bytes")
    else:
        _fail("V-HOOKS-SCRIPT-EXISTS",
              f"register={reg.is_file()} check={chk.is_file()}")


def _check_dryrun_does_not_modify() -> None:
    with tempfile.TemporaryDirectory(prefix="pphooks_dry_") as td:
        td_p = Path(td)
        settings = _seed_settings(td_p)
        original = settings.read_text(encoding="utf-8-sig")
        mod = _load_register_module()
        mod.SETTINGS_PATH = settings
        rc = mod.main(["--dry-run"])
        after = settings.read_text(encoding="utf-8-sig")
        if rc == 0 and original == after:
            _ok("V-HOOKS-SCRIPT-DRYRUN",
                f"rc=0 file unchanged ({len(original)} bytes)")
        else:
            _fail("V-HOOKS-SCRIPT-DRYRUN",
                  f"rc={rc} mutated={original != after}")


def _check_real_run_creates_backup() -> None:
    with tempfile.TemporaryDirectory(prefix="pphooks_real_") as td:
        td_p = Path(td)
        settings = _seed_settings(td_p)
        mod = _load_register_module()
        mod.SETTINGS_PATH = settings
        rc = mod.main([])
        backups = list(settings.parent.glob(
            "settings.pre-pp-hooks-*.bak"))
        if rc == 0 and len(backups) == 1 and backups[0].stat().st_size > 0:
            _ok("V-HOOKS-SCRIPT-BACKUP",
                f"backup={backups[0].name}")
        else:
            _fail("V-HOOKS-SCRIPT-BACKUP",
                  f"rc={rc} backups={[b.name for b in backups]}")


def _check_idempotency() -> None:
    with tempfile.TemporaryDirectory(prefix="pphooks_idem_") as td:
        td_p = Path(td)
        settings = _seed_settings(td_p)
        mod = _load_register_module()
        mod.SETTINGS_PATH = settings
        rc1 = mod.main([])
        first = json.loads(settings.read_text(encoding="utf-8-sig"))
        first_hooks = first.get("hooks", {})
        first_counts = {ev: len(es) for ev, es in first_hooks.items()}

        rc2 = mod.main([])
        second = json.loads(settings.read_text(encoding="utf-8-sig"))
        second_hooks = second.get("hooks", {})
        second_counts = {ev: len(es) for ev, es in second_hooks.items()}

        if (rc1 == 0 and rc2 == 0 and first_counts == second_counts
                and sum(first_counts.values()) == 5):
            _ok("V-HOOKS-SCRIPT-IDEMPOTENT",
                f"2x runs -> identical counts {first_counts}")
        else:
            _fail("V-HOOKS-SCRIPT-IDEMPOTENT",
                  f"rc1={rc1} rc2={rc2} a={first_counts} b={second_counts}")


def _check_check_status_no_crash_from_tmp() -> None:
    with tempfile.TemporaryDirectory(prefix="ppcheck_") as td:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        proc = subprocess.run(
            [sys.executable,
             str(ROOT / "tools" / "check_hook_status.py")],
            cwd=td, capture_output=True, text=True, timeout=30,
            env=env,
        )
        body = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode in (0, 1) and "PP AGENT STATUS" in body:
            _ok("V-HOOKS-CHECK-STATUS",
                f"rc={proc.returncode} from cwd={td}")
        else:
            _fail("V-HOOKS-CHECK-STATUS",
                  f"rc={proc.returncode} body[:120]={body[:120]!r}")


def _marker_check(marker: str, gate_name: str) -> None:
    body = (ROOT / "tools" / "register_global_hooks.py").read_text(
        encoding="utf-8")
    if marker in body:
        _ok(gate_name, f"'{marker}' present in script")
    else:
        _fail(gate_name, f"'{marker}' missing")


def _check_marker_pre() -> None:
    _marker_check("uqf_pre_edit_gate", "V-HOOKS-MARKER-PRE")


def _check_marker_post_osa() -> None:
    _marker_check("osa_deploy_detector", "V-HOOKS-MARKER-POST-OSA")


def _check_marker_post_ceps() -> None:
    _marker_check("bug-hunter-ceps-bridge", "V-HOOKS-MARKER-POST-CEPS")


def _check_marker_session() -> None:
    _marker_check("session-start-check", "V-HOOKS-MARKER-SESSION")


def _check_marker_stop() -> None:
    _marker_check("jobs_woz_gate", "V-HOOKS-MARKER-STOP")


def _check_files_exist() -> None:
    required = [
        "hooks/uqf_pre_edit_gate.js",
        "hooks/osa_deploy_detector.js",
        "hooks/bug-hunter-ceps-bridge.js",
        "hooks/jobs_woz_gate.js",
    ]
    missing = [r for r in required if not (ROOT / r).is_file()]
    if not missing:
        _ok("V-HOOKS-FILES-EXIST",
            f"{len(required)}/{len(required)} JS hooks present")
    else:
        _fail("V-HOOKS-FILES-EXIST", f"missing={missing}")


def _check_docs_exist() -> None:
    docs = ROOT / "docs" / "HOOKS_SETUP.md"
    if docs.is_file() and docs.stat().st_size > 500:
        _ok("V-HOOKS-DOCS-EXIST", f"{docs.stat().st_size} bytes")
    else:
        _fail("V-HOOKS-DOCS-EXIST",
              f"is_file={docs.is_file()} size={docs.stat().st_size if docs.is_file() else 0}")


def _check_baseline_intact() -> None:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=line"],
        cwd=str(ROOT), capture_output=True, text=True, timeout=240,
        env=env,
    )
    last = (proc.stdout.strip().splitlines() or [""])[-1]
    if proc.returncode == 0 and "passed" in last:
        _ok("V-BASELINE-INTACT", f"rc=0 last='{last}'")
    else:
        _fail("V-BASELINE-INTACT",
              f"rc={proc.returncode} last='{last}'")


def main() -> int:
    print("=== test_hooks_registration (BL-HOOKS-REG-001) ===")
    print(f"  pp root: {ROOT}")
    print()

    _check_script_exists()
    _check_dryrun_does_not_modify()
    _check_real_run_creates_backup()
    _check_idempotency()
    _check_check_status_no_crash_from_tmp()
    _check_marker_pre()
    _check_marker_post_osa()
    _check_marker_post_ceps()
    _check_marker_session()
    _check_marker_stop()
    _check_files_exist()
    _check_docs_exist()
    _check_baseline_intact()

    total = passes + fails
    print()
    print(f"HOOKS_REG_PASS={passes}/{total}  threshold=13/13")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
