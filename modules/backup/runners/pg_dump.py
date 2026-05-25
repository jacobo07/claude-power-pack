"""pg-dump runner -- logical Postgres backup via pg_dump custom format.

Mechanism: ssh into the host, run pg_dump inside the postgres container
(via `docker exec`), pipe the `-Fc` custom-format output to a local file.
The dump can be restored later with `pg_restore`.

Snapshot layout:
  <local_destination>/<timestamp>.dump

Authentication: the password lives in `~/.pgpass` ON the remote host
(or in the container's env via docker-compose), NEVER in the backup
config. The schema validator rejects any password-class key in the JSON.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any


PG_DUMP_HEADER = b"PGDMP"


def _ts() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d-%H%M%S")


def _expand_key(ssh_key: str) -> Path:
    return Path(os.path.expanduser(ssh_key)).resolve()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run_pg_dump(
    config: dict[str, Any],
    dry_run: bool = False,
) -> dict[str, Any]:
    """config keys consumed:
      ssh_alias         : SSH host alias (required)
      ssh_key           : path to private key (required)
      pg_container      : docker container name on remote (required)
      pg_user           : Postgres user (required)
      pg_database       : Postgres database (required)
      local_destination : local dir for the .dump file (required)
      project_root      : repo root (required)
    """
    ssh_alias = config.get("ssh_alias")
    ssh_key = config.get("ssh_key")
    pg_container = config.get("pg_container")
    pg_user = config.get("pg_user")
    pg_database = config.get("pg_database")
    local_destination = config.get("local_destination")
    project_root = config.get("project_root")

    if not all([ssh_alias, ssh_key, pg_container, pg_user, pg_database, local_destination, project_root]):
        return {
            "ok": False,
            "verdict": "fail",
            "summary": "pg-dump runner missing required config fields",
            "snapshot_path": None,
            "snapshot_size_bytes": 0,
            "snapshot_sha256": "",
            "receipt": "",
        }

    key_path = _expand_key(ssh_key)
    if not key_path.is_file():
        return {
            "ok": False,
            "verdict": "ceiling",
            "summary": f"SSH key not found at {key_path}; cannot backup",
            "snapshot_path": None,
            "snapshot_size_bytes": 0,
            "snapshot_sha256": "",
            "receipt": (
                f"config.ssh_key = '{ssh_key}'\n"
                f"expanded path  = '{key_path}'\n"
                "action          = Owner must create the key or fix the path"
            ),
        }

    local_dir = Path(project_root) / local_destination
    local_dir.mkdir(parents=True, exist_ok=True)
    ts = _ts()
    snapshot_path = local_dir / f"{ts}.dump"

    remote_cmd = (
        f"docker exec {shlex.quote(pg_container)} "
        f"pg_dump -Fc -U {shlex.quote(pg_user)} {shlex.quote(pg_database)}"
    )
    ssh_cmd = ["ssh", "-i", str(key_path), ssh_alias, remote_cmd]

    if dry_run:
        plan = [
            f"DRY RUN -- ssh key resolved: {key_path}",
            f"DRY RUN -- ssh_alias: {ssh_alias}",
            f"DRY RUN -- pg_container: {pg_container}",
            f"DRY RUN -- pg_user: {pg_user}",
            f"DRY RUN -- pg_database: {pg_database}",
            f"DRY RUN -- remote command: {remote_cmd}",
            f"DRY RUN -- snapshot would land at: {snapshot_path}",
            "DRY RUN -- password lives in remote ~/.pgpass or container env, never in this config",
        ]
        return {
            "ok": True,
            "verdict": "dry-run",
            "summary": f"pg-dump dry-run for {pg_database}@{ssh_alias}",
            "snapshot_path": str(snapshot_path),
            "snapshot_size_bytes": 0,
            "snapshot_sha256": "",
            "receipt": "\n".join(plan),
        }

    try:
        with snapshot_path.open("wb") as out:
            proc = subprocess.run(
                ssh_cmd,
                stdout=out,
                stderr=subprocess.PIPE,
                timeout=3600,
                check=False,
            )
    except subprocess.TimeoutExpired as exc:
        if snapshot_path.exists():
            try:
                snapshot_path.unlink()
            except OSError:
                pass
        return {
            "ok": False,
            "verdict": "fail",
            "summary": "ssh+pg_dump timed out (>1 h)",
            "snapshot_path": None,
            "snapshot_size_bytes": 0,
            "snapshot_sha256": "",
            "receipt": f"TimeoutExpired: {exc}",
        }

    stderr = (proc.stderr or b"").decode("utf-8", errors="replace")
    if proc.returncode != 0:
        if snapshot_path.exists() and snapshot_path.stat().st_size == 0:
            try:
                snapshot_path.unlink()
            except OSError:
                pass
        return {
            "ok": False,
            "verdict": "fail",
            "summary": f"pg_dump failed (exit {proc.returncode})",
            "snapshot_path": str(snapshot_path) if snapshot_path.exists() else None,
            "snapshot_size_bytes": snapshot_path.stat().st_size if snapshot_path.exists() else 0,
            "snapshot_sha256": "",
            "receipt": stderr[-2000:],
        }

    size = snapshot_path.stat().st_size
    if size == 0:
        try:
            snapshot_path.unlink()
        except OSError:
            pass
        return {
            "ok": False,
            "verdict": "fail",
            "summary": "pg_dump returned 0 bytes",
            "snapshot_path": None,
            "snapshot_size_bytes": 0,
            "snapshot_sha256": "",
            "receipt": stderr[-2000:],
        }

    with snapshot_path.open("rb") as f:
        header = f.read(5)
    header_ok = header == PG_DUMP_HEADER

    sha = _sha256_file(snapshot_path)
    return {
        "ok": True,
        "verdict": "pass",
        "summary": (
            f"pg-dump snapshot OK ({size} bytes); header={header!r} "
            f"{'PGDMP magic verified' if header_ok else 'WARN: PGDMP magic missing'}"
        ),
        "snapshot_path": str(snapshot_path),
        "snapshot_size_bytes": size,
        "snapshot_sha256": sha,
        "receipt": (
            f"snapshot:    {snapshot_path}\n"
            f"database:    {pg_database}\n"
            f"container:   {pg_container}\n"
            f"size:        {size} bytes\n"
            f"sha256:      {sha}\n"
            f"header:      {header!r} (PGDMP magic {'OK' if header_ok else 'MISSING'})\n"
            f"ssh stderr (last 500): {stderr[-500:]}"
        ),
    }
