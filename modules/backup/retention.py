"""Retention policy enforcer.

Applies after a successful snapshot + restore-test. Lists snapshots in
the destination dir, sorts by mtime, drops the ones outside the retention
window. Honors `min_keep` so a stale dir never gets fully wiped.

Manifest: writes <local_destination>/manifest.json with sha256 of every
retained snapshot. Used by future Rollback Axis to pick a known-good
restore point.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


SNAPSHOT_GLOB_PATTERNS = ("*.tar.gz", "*.dump", "*.tar")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _list_snapshots(directory: Path) -> list[Path]:
    out: list[Path] = []
    for pattern in SNAPSHOT_GLOB_PATTERNS:
        out.extend(directory.glob(pattern))
    return out


def apply_retention(
    local_destination: str,
    retention_spec: dict[str, Any],
    project_root: str,
) -> dict[str, Any]:
    """Apply retention rules to a destination dir.

    retention_spec:
      keep_last_n          : int, keep the N most recent snapshots (required)
      drop_older_than_days : int, drop snapshots whose mtime is older than this
      min_keep             : int, never drop below this count even on time-based
                             policy (default 1)
    """
    keep_last_n = int(retention_spec.get("keep_last_n", 5))
    drop_older_than_days = retention_spec.get("drop_older_than_days")
    min_keep = int(retention_spec.get("min_keep", 1))

    dest = Path(project_root) / local_destination
    if not dest.is_dir():
        return {"kept": 0, "dropped": 0, "dropped_files": [], "manifest_path": ""}

    snapshots = _list_snapshots(dest)
    snapshots.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    keep_set: set[Path] = set(snapshots[:keep_last_n])

    if drop_older_than_days is not None:
        cutoff = _dt.datetime.now(_dt.timezone.utc).timestamp() - (int(drop_older_than_days) * 86400)
        time_kept = [p for p in snapshots if p.stat().st_mtime >= cutoff]
        keep_set |= set(time_kept)

    if len(keep_set) < min_keep:
        for p in snapshots:
            if len(keep_set) >= min_keep:
                break
            keep_set.add(p)

    drop_list = [p for p in snapshots if p not in keep_set]
    dropped_files: list[str] = []
    for p in drop_list:
        try:
            p.unlink()
            dropped_files.append(str(p.relative_to(Path(project_root))))
        except OSError:
            continue

    retained = [p for p in snapshots if p in keep_set and p.exists()]
    manifest = {
        "generated_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "destination": str(dest.relative_to(Path(project_root))),
        "retention": {
            "keep_last_n": keep_last_n,
            "drop_older_than_days": drop_older_than_days,
            "min_keep": min_keep,
        },
        "snapshots": [
            {
                "name": p.name,
                "size_bytes": p.stat().st_size,
                "mtime_utc": _dt.datetime.fromtimestamp(p.stat().st_mtime, tz=_dt.timezone.utc).isoformat(),
                "sha256": _sha256_file(p),
            }
            for p in sorted(retained, key=lambda x: x.stat().st_mtime, reverse=True)
        ],
    }
    manifest_path = dest / "manifest.json"
    manifest_path.write_bytes(
        json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8")
    )

    return {
        "kept": len(retained),
        "dropped": len(dropped_files),
        "dropped_files": dropped_files,
        "manifest_path": str(manifest_path.relative_to(Path(project_root))),
    }
