#!/usr/bin/env python
"""gsd_long_run_config — retune GSD's context warnings for an unattended run.

Spec vault/specs/gsd-autonomous-autocompact.md, gap A.

GSD's context monitor injects "wrap up current task" at 35% remaining and
"stop immediately and save state" at 25%. The Power Pack watchdog compacts at
70% used, i.e. 30% remaining — which falls BETWEEN those two. So on a long run
the agent is told to wrap up, and then to stop, before the compaction that
would have let it continue ever happens. The two systems are giving opposite
orders and GSD's are the nearer ones.

This lowers GSD's fire-points below the compaction point so the ordering
becomes: compact (30% remaining) -> continue -> compact again, with GSD's
warnings still present underneath as a genuine last-resort net. It does NOT
disable them: `hooks.context_warnings: false` would remove the floor entirely,
and a floor is the thing you want most on a run nobody is watching.

Both keys are read by ~/.claude/hooks/gsd-context-monitor.js
(`resolveThresholds`), per project, from <project>/.planning/config.json.

CLI:
    python tools/gsd_long_run_config.py --apply   [--project <path>]
    python tools/gsd_long_run_config.py --restore [--project <path>]
    python tools/gsd_long_run_config.py --show    [--project <path>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

# Below the watchdog's 30%-remaining compaction point, so a compaction always
# gets its chance first, while a genuinely exhausted context still trips GSD.
LONG_RUN_WARNING = 12
LONG_RUN_CRITICAL = 8

# LEGACY location of the parked values (inside config.json). gsd-tools warned
# "unknown config key" on every call, so v2 parks them under ~/.claude/state
# (see backup_path) and migrates this key out on the next apply/restore.
BACKUP_KEY = "_pp_long_run_backup"


class ConfigError(RuntimeError):
    """The config could not be read or written safely."""


def config_path(project: Path) -> Path:
    return project / ".planning" / "config.json"


def load_config(project: Path) -> dict:
    """Read the project's GSD config. Missing file is an empty config.

    A file that exists but does not parse raises: overwriting it would destroy
    settings the operator cannot get back, and a long-run tweak is never worth
    that.
    """
    path = config_path(project)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise ConfigError(f"{path} exists but does not parse as JSON: {exc}")
    if not isinstance(data, dict):
        raise ConfigError(f"{path} does not hold a JSON object")
    return data


def save_config(project: Path, data: dict) -> Path:
    path = config_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    return path


def backup_path(project: Path) -> Path:
    """Where the parked values live (spec gsd-long-run-v2.md, gap 13).

    Not inside config.json: gsd-tools warns "unknown config key" on every call
    for a key it does not own. Not in .planning/ either: anyone tidying that
    folder would delete it. ~/.claude/state is ours and nobody tidies it.
    """
    override = os.environ.get("GSD_LONG_RUN_STATE_DIR")
    base = Path(override) if override else Path.home() / ".claude" / "state"
    key = os.path.normcase(os.path.abspath(str(project))).rstrip("\\/")
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
    return base / "gsd-long-run-backups" / f"{digest}.json"


def _read_backup(project: Path) -> dict | None:
    path = backup_path(project)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ConfigError(f"backup {path} does not parse: {exc}")
    return data.get("values") if isinstance(data, dict) else None


def _write_backup(project: Path, values: dict) -> None:
    path = backup_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps({"project": str(project), "values": values}, indent=2),
                   encoding="utf-8")
    tmp.replace(path)


def apply_long_run(project: Path) -> tuple[Path, dict]:
    """Lower the fire-points, parking whatever was there before.

    Idempotent: applying twice does not overwrite the backup with our own
    values, so a double-apply followed by one restore still lands on the
    operator's original settings. A backup embedded by an older version is
    migrated out of config.json.
    """
    data = load_config(project)
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ConfigError("config 'hooks' is not an object")

    embedded = data.pop(BACKUP_KEY, None)
    if _read_backup(project) is None:
        _write_backup(project, embedded if isinstance(embedded, dict) else {
            "context_warning_threshold": hooks.get("context_warning_threshold"),
            "context_critical_threshold": hooks.get("context_critical_threshold"),
        })

    hooks["context_warning_threshold"] = LONG_RUN_WARNING
    hooks["context_critical_threshold"] = LONG_RUN_CRITICAL
    return save_config(project, data), data


def restore(project: Path) -> tuple[Path, dict]:
    """Put back exactly what was there, including 'the key was absent'."""
    data = load_config(project)
    embedded = data.pop(BACKUP_KEY, None)
    backup = _read_backup(project)
    if backup is None:
        backup = embedded if isinstance(embedded, dict) else None
    if backup is None:
        raise ConfigError(
            "no long-run backup for this project — nothing to restore "
            "(apply was never run here, or restore already ran)")

    hooks = data.setdefault("hooks", {})
    for key in ("context_warning_threshold", "context_critical_threshold"):
        previous = backup.get(key)
        if previous is None:
            hooks.pop(key, None)   # absent before means absent after
        else:
            hooks[key] = previous
    path = save_config(project, data)
    backup_path(project).unlink(missing_ok=True)
    return path, data


def show(project: Path) -> dict:
    data = load_config(project)
    hooks = data.get("hooks", {}) if isinstance(data.get("hooks"), dict) else {}
    return {
        "config": str(config_path(project)),
        "exists": config_path(project).is_file(),
        "context_warning_threshold": hooks.get("context_warning_threshold"),
        "context_critical_threshold": hooks.get("context_critical_threshold"),
        "context_warnings": hooks.get("context_warnings"),
        "long_run_active": backup_path(project).is_file() or data.get(BACKUP_KEY) is not None,
        "backup": str(backup_path(project)),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="GSD long-run context thresholds")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--restore", action="store_true")
    mode.add_argument("--show", action="store_true")
    ap.add_argument("--project", default=".")
    args = ap.parse_args(argv)

    project = Path(args.project).resolve()
    try:
        if args.show:
            sys.stdout.write(json.dumps(show(project), indent=2) + "\n")
            return 0
        if args.apply:
            path, _ = apply_long_run(project)
            sys.stdout.write(
                f"applied: warning={LONG_RUN_WARNING} "
                f"critical={LONG_RUN_CRITICAL} -> {path}\n")
            return 0
        path, _ = restore(project)
        sys.stdout.write(f"restored previous thresholds -> {path}\n")
        return 0
    except ConfigError as exc:
        sys.stderr.write(f"REFUSED: {exc}\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
