"""Source selector -- single source of truth for "verified backup exists".

Reads <project_root>/backups/<project>/manifest.json, which is written by
modules/backup/retention.py:apply_retention. The manifest is the contract:
a snapshot on disk WITHOUT a manifest entry is treated as if it does not
exist, because the absence means it never reached the post-restore-test
retention pass (i.e., it was either backup-warn or pre-manifest-era).

The Rollback Axis cannot trust a snapshot that the Backup Axis itself did
not certify. This module enforces that boundary.

Manifest contract (from retention.py:apply_retention):
  {
    "generated_utc": "...",
    "destination": "backups/<project>",
    "retention": {...},
    "snapshots": [
      { "name": "<ts>.tar.gz",
        "size_bytes": int,
        "mtime_utc": "ISO-8601 string",
        "sha256": "hex" },
      ...
    ]
  }
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any


def _manifest_path(project_root: Path, project: str, config: dict[str, Any] | None = None) -> Path:
    """Resolve manifest location.

    Default: <project_root>/backups/<project>/manifest.json.
    If config supplies backup_source_dir, honor it (relative to project_root).
    """
    if config and config.get("backup_source_dir"):
        base = project_root / config["backup_source_dir"]
    else:
        base = project_root / "backups" / project
    return base / "manifest.json"


def _load_manifest(manifest_file: Path) -> tuple[dict[str, Any] | None, str]:
    if not manifest_file.is_file():
        return None, f"manifest absent at {manifest_file}"
    try:
        raw = manifest_file.read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"manifest unreadable: {exc}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"manifest JSON invalid: {exc}"
    if not isinstance(data, dict):
        return None, "manifest root is not a JSON object"
    return data, ""


def _mtime_sort_key(entry: dict[str, Any]) -> float:
    raw = entry.get("mtime_utc", "")
    if not isinstance(raw, str) or not raw:
        return 0.0
    try:
        return _dt.datetime.fromisoformat(raw).timestamp()
    except ValueError:
        return 0.0


def select_source(
    project_root: Path,
    project: str,
    target: str | None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the verified snapshot to roll back from.

    Args:
      project_root: repo root (Path).
      project: project name (used as subdir under backups/).
      target: optional snapshot file name (just the basename, e.g.
              "2026-05-25-151305.tar.gz"). None means "latest verified
              by mtime descending".
      config: optional rollback config (may carry backup_source_dir override).

    Returns:
      {ok: True, path: str (absolute on disk), sha256, size_bytes,
       mtime_utc, evidence}
      OR
      {ok: False, reason: "manifest_absent"|"manifest_empty"|
                          "target_not_found"|"target_unverified",
       evidence: str}
    """
    manifest_file = _manifest_path(project_root, project, config)
    manifest, err = _load_manifest(manifest_file)
    if manifest is None:
        return {
            "ok": False,
            "reason": "manifest_absent",
            "evidence": (
                f"{err}. "
                f"No verified backup exists for {project!r}. "
                f"Ensure a /backup --project {project} has run successfully "
                "(verdict=pass) before invoking /rollback."
            ),
        }

    snapshots = manifest.get("snapshots")
    if not isinstance(snapshots, list):
        return {
            "ok": False,
            "reason": "manifest_empty",
            "evidence": (
                f"Manifest at {manifest_file} is malformed: missing 'snapshots' "
                "list. Re-run /backup to regenerate."
            ),
        }
    if not snapshots:
        return {
            "ok": False,
            "reason": "manifest_empty",
            "evidence": (
                f"Manifest at {manifest_file} exists but has zero snapshots. "
                f"Run /backup --project {project} to populate it."
            ),
        }

    destination = manifest.get("destination") or f"backups/{project}"
    sorted_entries = sorted(snapshots, key=_mtime_sort_key, reverse=True)

    if target is None:
        chosen = sorted_entries[0]
    else:
        match = None
        target_basename = Path(target).name
        for entry in sorted_entries:
            if entry.get("name") == target_basename:
                match = entry
                break
        if match is None:
            verified_names = [e.get("name", "") for e in sorted_entries[:5]]
            return {
                "ok": False,
                "reason": "target_unverified",
                "evidence": (
                    f"Target snapshot {target!r} not found in manifest at "
                    f"{manifest_file}. A snapshot on disk without a manifest "
                    "entry was either never restore-tested or is "
                    "pre-manifest-era. Verified snapshots (latest 5): "
                    f"{verified_names}"
                ),
            }
        chosen = match

    name = chosen.get("name", "")
    if not name:
        return {
            "ok": False,
            "reason": "target_not_found",
            "evidence": f"Manifest entry has empty 'name' field: {chosen}",
        }

    snap_path = (project_root / destination / name).resolve()
    if not snap_path.is_file():
        return {
            "ok": False,
            "reason": "target_not_found",
            "evidence": (
                f"Manifest references {snap_path} but the file is not present "
                "on disk. The manifest may be stale -- consider running "
                "/backup to refresh, or inspect the local backups directory."
            ),
        }

    return {
        "ok": True,
        "path": str(snap_path),
        "sha256": chosen.get("sha256", ""),
        "size_bytes": int(chosen.get("size_bytes", 0)),
        "mtime_utc": chosen.get("mtime_utc", ""),
        "evidence": (
            f"Selected verified snapshot from manifest {manifest_file}: "
            f"{name} ({chosen.get('size_bytes', 0)} bytes, "
            f"sha256 {(chosen.get('sha256', '') or '')[:12]}...)"
        ),
    }


def list_verified(
    project_root: Path,
    project: str,
    limit: int = 5,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """List the top-N verified snapshots (for /rollback --list)."""
    manifest_file = _manifest_path(project_root, project, config)
    manifest, err = _load_manifest(manifest_file)
    if manifest is None:
        return {
            "ok": False,
            "reason": "manifest_absent",
            "evidence": err,
            "snapshots": [],
        }

    snapshots = manifest.get("snapshots")
    if not isinstance(snapshots, list) or not snapshots:
        return {
            "ok": False,
            "reason": "manifest_empty",
            "evidence": f"Manifest at {manifest_file} has no snapshots",
            "snapshots": [],
        }

    sorted_entries = sorted(snapshots, key=_mtime_sort_key, reverse=True)[:limit]

    return {
        "ok": True,
        "reason": "",
        "evidence": f"Listed {len(sorted_entries)} verified snapshot(s) from {manifest_file}",
        "snapshots": [
            {
                "name": e.get("name", ""),
                "sha256_short": (e.get("sha256", "") or "")[:12],
                "size_bytes": int(e.get("size_bytes", 0)),
                "mtime_utc": e.get("mtime_utc", ""),
            }
            for e in sorted_entries
        ],
    }
