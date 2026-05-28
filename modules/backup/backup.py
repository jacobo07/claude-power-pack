"""Backup dispatcher -- entry point for the backup skill.

STDIN/STDOUT JSON contract per vault/specs/backup-skill.md §5.

Pipeline:
  1. Schema validate (reject credential-class keys, forbidden modes).
  2. Disk-full guard (df ≥ 2× expected_size_bytes; default 1 GiB floor).
  3. Dispatch runner (rsync-dir | docker-volume-tar | pg-dump).
  4. verify_restore (per §8 contract; sha256 manifest + structural_check).
  5. Apply retention (only if verify_restore PASS; manifest update).
  6. Write receipt to vault/backups/<ts>_<project>.md.

Reality contract: receipt is written ONLY after verify_restore has run.
Silent masking of failures is forbidden.

Recursion guard: CLAUDEPP_BACKUP_RUNNING is NOT set at level-1.
Opt-out: CLAUDEPP_BACKUP_DISABLED=1 -> verdict 'skip' exit 0.
Opt-out advanced: CLAUDEPP_BACKUP_SKIP_RESTORE_TEST=1 -> verify_restore
skipped; verdict can never be 'pass' (ceiling at 'backup-warn').
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from retention import apply_retention  # noqa: E402
from runners.docker_volume_tar import run_docker_volume_tar  # noqa: E402
from runners.pg_dump import run_pg_dump  # noqa: E402
from runners.rsync_dir import run_rsync_dir  # noqa: E402
from verify_restore import verify_restore  # noqa: E402


EXIT_PASS = 0
EXIT_FAIL = 2
EXIT_BACKUP_WARN = 3
EXIT_CEILING = 4

FORBIDDEN_KEY_TOKENS = (
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "passphrase",
)

FORBIDDEN_MODES = {"n8n", "zapier", "make.com", "pipedream"}

REQUIRED_KEYS = (
    "mode",
    "ssh_alias",
    "ssh_key",
    "local_destination",
    "retention",
    "restore_test",
)

DEFAULT_FREE_FLOOR_BYTES = 1 * 1024 * 1024 * 1024  # 1 GiB


def validate_config(config: dict[str, Any]) -> tuple[bool, str]:
    if not isinstance(config, dict):
        return False, "config is not a JSON object"
    for key in REQUIRED_KEYS:
        if key not in config:
            return False, f"required key missing: '{key}'"
    for key in config:
        low = key.lower()
        for tok in FORBIDDEN_KEY_TOKENS:
            if tok in low:
                return False, (
                    f"forbidden key category in config: '{key}' contains "
                    f"'{tok}'. Credentials must live in ~/.ssh/ or ~/.pgpass, "
                    "not in vault/backup/"
                )
    if config["mode"] in FORBIDDEN_MODES:
        return False, f"mode '{config['mode']}' is permanently forbidden in PP"
    if config["mode"] not in {"rsync-dir", "docker-volume-tar", "pg-dump"}:
        return False, f"mode '{config['mode']}' is not a recognised backup mode"
    return True, "ok"


def _disk_free_bytes(path: Path) -> int:
    try:
        return shutil.disk_usage(str(path)).free
    except OSError:
        return 0


def _ts() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d-%H%M%S")


def _previous_backups(project_root: Path, project: str, n: int = 5) -> list[str]:
    reports_dir = project_root / "vault" / "backups"
    if not reports_dir.is_dir():
        return []
    pattern = f"*_{project}.md"
    matches = sorted(reports_dir.glob(pattern), reverse=True)
    return [str(p.relative_to(project_root)) for p in matches[:n]]


def _write_receipt(
    project_root: Path,
    project: str,
    config: dict[str, Any],
    runner_result: dict[str, Any],
    restore_result: dict[str, Any] | None,
    retention_result: dict[str, Any] | None,
    duration_ms: int,
) -> str:
    reports_dir = project_root / "vault" / "backups"
    reports_dir.mkdir(parents=True, exist_ok=True)
    ts = _ts()
    fname = f"{ts}_{project}.md"
    fpath = reports_dir / fname

    restore_block = "(restore-test not run)" if restore_result is None else json.dumps(restore_result, indent=2)
    retention_block = "(retention not applied)" if retention_result is None else json.dumps(retention_result, indent=2)

    body = f"""# Backup receipt -- {project}

- Timestamp (UTC): {ts}
- Duration: {duration_ms} ms
- Mode: {config.get('mode')}
- SSH alias: {config.get('ssh_alias')}
- Local destination: {config.get('local_destination')}

## 1. Runner verdict

- verdict: {runner_result.get('verdict')}
- ok: {runner_result.get('ok')}
- summary: {runner_result.get('summary')}
- snapshot_path: {runner_result.get('snapshot_path')}
- snapshot_size_bytes: {runner_result.get('snapshot_size_bytes')}
- snapshot_sha256: {runner_result.get('snapshot_sha256')}

## 2. Runner receipt

```
{runner_result.get('receipt', '')}
```

## 3. Restore-test (verify_restore.py)

```
{restore_block}
```

## 4. Retention applied

```
{retention_block}
```
"""
    fpath.write_bytes(body.encode("utf-8"))
    return str(fpath.relative_to(project_root))


def _dispatch_runner(config: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    mode = config.get("mode")
    if mode == "rsync-dir":
        return run_rsync_dir(config, dry_run=dry_run)
    if mode == "docker-volume-tar":
        return run_docker_volume_tar(config, dry_run=dry_run)
    if mode == "pg-dump":
        return run_pg_dump(config, dry_run=dry_run)
    return {
        "ok": False,
        "verdict": "fail",
        "summary": f"unknown mode '{mode}'",
        "snapshot_path": None,
        "snapshot_size_bytes": 0,
        "snapshot_sha256": "",
        "receipt": "",
    }


def _load_config(
    project_root: Path,
    project: str,
    config_override: str | None,
) -> tuple[dict[str, Any], str]:
    if config_override:
        cfg_path = Path(config_override)
        if not cfg_path.is_absolute():
            cfg_path = project_root / cfg_path
    else:
        cfg_path = project_root / "vault" / "backup" / f"{project}.json"
    if not cfg_path.is_file():
        return {}, str(cfg_path)
    try:
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, str(cfg_path)
    if not isinstance(data, dict):
        return {}, str(cfg_path)
    return data, str(cfg_path)


def backup(stdin_payload: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    project_root = Path(stdin_payload.get("project_root") or os.getcwd()).resolve()
    project = stdin_payload.get("project") or project_root.name
    dry_run = bool(stdin_payload.get("dry_run", False))
    config_override = stdin_payload.get("config_override")

    if os.environ.get("CLAUDEPP_BACKUP_DISABLED") == "1":
        return {
            "verdict": "skip",
            "exit_code": EXIT_PASS,
            "mode": None,
            "duration_ms": int((time.monotonic() - started) * 1000),
            "summary": "backup disabled via CLAUDEPP_BACKUP_DISABLED=1",
        }

    config, cfg_source = _load_config(project_root, project, config_override)
    if not config:
        return {
            "verdict": "ceiling",
            "exit_code": EXIT_CEILING,
            "mode": None,
            "duration_ms": int((time.monotonic() - started) * 1000),
            "summary": f"backup config not found or invalid at {cfg_source}",
        }

    ok, reason = validate_config(config)
    if not ok:
        return {
            "verdict": "fail",
            "exit_code": EXIT_FAIL,
            "mode": config.get("mode"),
            "duration_ms": int((time.monotonic() - started) * 1000),
            "summary": f"config schema invalid: {reason}",
        }

    config.setdefault("project_root", str(project_root))

    local_dest = Path(project_root) / config["local_destination"]
    local_dest.mkdir(parents=True, exist_ok=True)
    expected = int(config.get("expected_size_bytes", 0)) or DEFAULT_FREE_FLOOR_BYTES
    free = _disk_free_bytes(local_dest)
    required = max(expected * 2, DEFAULT_FREE_FLOOR_BYTES)
    if free < required and not dry_run:
        return {
            "verdict": "ceiling",
            "exit_code": EXIT_CEILING,
            "mode": config.get("mode"),
            "duration_ms": int((time.monotonic() - started) * 1000),
            "summary": (
                f"disk-full guard: {free} free bytes < {required} required "
                f"(2x expected={expected} or floor {DEFAULT_FREE_FLOOR_BYTES})"
            ),
        }

    runner_result = _dispatch_runner(config, dry_run)

    if dry_run:
        duration_ms = int((time.monotonic() - started) * 1000)
        return {
            "verdict": "dry-run",
            "exit_code": EXIT_PASS,
            "mode": config.get("mode"),
            "duration_ms": duration_ms,
            "summary": runner_result.get("summary", "dry-run"),
            "snapshot_path": runner_result.get("snapshot_path"),
            "previous_backups": _previous_backups(project_root, project),
            "runner_receipt": runner_result.get("receipt", ""),
        }

    if runner_result.get("verdict") in {"fail", "ceiling"}:
        duration_ms = int((time.monotonic() - started) * 1000)
        exit_code = EXIT_CEILING if runner_result["verdict"] == "ceiling" else EXIT_FAIL
        return {
            "verdict": runner_result["verdict"],
            "exit_code": exit_code,
            "mode": config.get("mode"),
            "duration_ms": duration_ms,
            "summary": runner_result.get("summary", ""),
            "snapshot_path": runner_result.get("snapshot_path"),
        }

    skip_restore = os.environ.get("CLAUDEPP_BACKUP_SKIP_RESTORE_TEST") == "1"
    if skip_restore:
        restore_result = {
            "ok": False,
            "checks_passed": 0,
            "checks_total": 0,
            "evidence": "restore-test skipped via CLAUDEPP_BACKUP_SKIP_RESTORE_TEST=1; verdict cannot be 'pass'",
        }
    else:
        restore_result = verify_restore(
            runner_result["snapshot_path"],
            config.get("restore_test", {}),
        )

    retention_result: dict[str, Any] | None = None
    if restore_result.get("ok"):
        retention_result = apply_retention(
            config["local_destination"],
            config.get("retention", {}),
            str(project_root),
        )

    duration_ms = int((time.monotonic() - started) * 1000)
    receipt_path = _write_receipt(
        project_root, project, config, runner_result, restore_result, retention_result, duration_ms
    )

    if restore_result.get("ok"):
        verdict = "pass"
        exit_code = EXIT_PASS
        summary = (
            f"snapshot + restore-test OK ({runner_result.get('snapshot_size_bytes')} bytes; "
            f"{restore_result['checks_passed']}/{restore_result['checks_total']} checks)"
        )
    else:
        verdict = "backup-warn"
        exit_code = EXIT_BACKUP_WARN
        summary = (
            f"snapshot WRITTEN ({runner_result.get('snapshot_size_bytes')} bytes) "
            f"but restore-test FAILED. Snapshot kept on disk for inspection. "
            f"Receipt: {receipt_path}"
        )

    # OSA post-backup hook -- non-blocking, swallow-all-errors (sealed 2026-05-28).
    try:
        from modules.osa.dispatcher import fire_async as _osa_fire
        _osa_fire(project=project, kind="post-backup")
    except Exception:
        pass

    return {
        "verdict": verdict,
        "exit_code": exit_code,
        "mode": config.get("mode"),
        "duration_ms": duration_ms,
        "summary": summary,
        "snapshot_path": runner_result.get("snapshot_path"),
        "snapshot_size_bytes": runner_result.get("snapshot_size_bytes"),
        "snapshot_sha256": runner_result.get("snapshot_sha256"),
        "restore_test": restore_result,
        "retention_applied": retention_result,
        "receipt_path": receipt_path,
        "previous_backups": _previous_backups(project_root, project),
    }


def main() -> int:
    raw = sys.stdin.read().strip()
    if raw.startswith("﻿"):
        raw = raw[1:]
    payload = json.loads(raw) if raw else {}
    result = backup(payload)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return int(result.get("exit_code", EXIT_FAIL))


if __name__ == "__main__":
    sys.exit(main())
