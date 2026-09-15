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
import json
import sys
from pathlib import Path

# Below the watchdog's 30%-remaining compaction point, so a compaction always
# gets its chance first, while a genuinely exhausted context still trips GSD.
LONG_RUN_WARNING = 12
LONG_RUN_CRITICAL = 8

# Where the previous values are parked so --restore is exact rather than a
# guess at the defaults. Stored inside the same config under our own key: a
# sidecar file would be deleted by anyone tidying .planning/.
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


def apply_long_run(project: Path) -> tuple[Path, dict]:
    """Lower the fire-points, parking whatever was there before.

    Idempotent: applying twice does not overwrite the backup with our own
    values, so a double-apply followed by one restore still lands on the
    operator's original settings.
    """
    data = load_config(project)
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ConfigError("config 'hooks' is not an object")

    if BACKUP_KEY not in data:
        data[BACKUP_KEY] = {
            "context_warning_threshold": hooks.get("context_warning_threshold"),
            "context_critical_threshold": hooks.get("context_critical_threshold"),
        }

    hooks["context_warning_threshold"] = LONG_RUN_WARNING
    hooks["context_critical_threshold"] = LONG_RUN_CRITICAL
    return save_config(project, data), data


def restore(project: Path) -> tuple[Path, dict]:
    """Put back exactly what was there, including 'the key was absent'."""
    data = load_config(project)
    backup = data.pop(BACKUP_KEY, None)
    if backup is None:
        raise ConfigError(
            "no long-run backup in this config — nothing to restore "
            "(apply was never run here, or restore already ran)")

    hooks = data.setdefault("hooks", {})
    for key in ("context_warning_threshold", "context_critical_threshold"):
        previous = backup.get(key)
        if previous is None:
            hooks.pop(key, None)   # absent before means absent after
        else:
            hooks[key] = previous
    return save_config(project, data), data


def show(project: Path) -> dict:
    data = load_config(project)
    hooks = data.get("hooks", {}) if isinstance(data.get("hooks"), dict) else {}
    return {
        "config": str(config_path(project)),
        "exists": config_path(project).is_file(),
        "context_warning_threshold": hooks.get("context_warning_threshold"),
        "context_critical_threshold": hooks.get("context_critical_threshold"),
        "context_warnings": hooks.get("context_warnings"),
        "long_run_active": data.get(BACKUP_KEY) is not None,
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
