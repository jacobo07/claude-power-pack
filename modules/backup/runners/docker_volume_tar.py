"""docker-volume-tar runner -- snapshots a named docker volume.

Mechanism: ssh into the host, run an ephemeral alpine container with
the volume bind-mounted read-only, tar+gzip its contents to stdout,
pipe to a local file. Container is `--rm` so no remote cleanup needed.

Snapshot layout:
  <local_destination>/<timestamp>.tar.gz
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any


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


def run_docker_volume_tar(
    config: dict[str, Any],
    dry_run: bool = False,
) -> dict[str, Any]:
    """config keys consumed:
      ssh_alias         : SSH host alias (required)
      ssh_key           : path to private key (required)
      volume_name       : docker volume name on the remote (required)
      local_destination : local dir to write the .tar.gz (required)
      project_root      : repo root (required)
      docker_image      : optional, default 'alpine:3.20'
    """
    ssh_alias = config.get("ssh_alias")
    ssh_key = config.get("ssh_key")
    volume_name = config.get("volume_name")
    local_destination = config.get("local_destination")
    project_root = config.get("project_root")
    docker_image = config.get("docker_image", "alpine:3.20")

    if not all([ssh_alias, ssh_key, volume_name, local_destination, project_root]):
        return {
            "ok": False,
            "verdict": "fail",
            "summary": "docker-volume-tar runner missing required config fields",
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
    snapshot_path = local_dir / f"{ts}.tar.gz"

    remote_cmd = (
        f"docker run --rm -v {shlex.quote(volume_name)}:/data:ro {shlex.quote(docker_image)} "
        f"sh -c 'cd /data && tar -czf - .'"
    )
    ssh_cmd = ["ssh", "-i", str(key_path), ssh_alias, remote_cmd]

    if dry_run:
        plan = [
            f"DRY RUN -- ssh key resolved: {key_path}",
            f"DRY RUN -- ssh_alias: {ssh_alias}",
            f"DRY RUN -- volume: {volume_name}",
            f"DRY RUN -- docker_image: {docker_image}",
            f"DRY RUN -- remote command: {remote_cmd}",
            f"DRY RUN -- snapshot would land at: {snapshot_path}",
        ]
        return {
            "ok": True,
            "verdict": "dry-run",
            "summary": f"docker-volume-tar dry-run for volume {volume_name}",
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
            "summary": "ssh+docker run timed out (>1 h)",
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
            "summary": f"docker volume tar failed (exit {proc.returncode})",
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
            "summary": "docker volume tar returned 0 bytes",
            "snapshot_path": None,
            "snapshot_size_bytes": 0,
            "snapshot_sha256": "",
            "receipt": stderr[-2000:],
        }

    sha = _sha256_file(snapshot_path)
    return {
        "ok": True,
        "verdict": "pass",
        "summary": f"docker-volume-tar snapshot OK ({size} bytes)",
        "snapshot_path": str(snapshot_path),
        "snapshot_size_bytes": size,
        "snapshot_sha256": sha,
        "receipt": (
            f"snapshot: {snapshot_path}\n"
            f"volume:   {volume_name}\n"
            f"size:     {size} bytes\n"
            f"sha256:   {sha}\n"
            f"ssh stderr (last 500): {stderr[-500:]}"
        ),
    }
