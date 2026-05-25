"""restore_docker_volume runner -- inverse of backup/runners/docker_volume_tar.py.

Stream local <ts>.tar.gz back to the remote and extract into the named docker
volume via an ephemeral alpine container. The container mounts the volume
read-write, cd into /data, and runs `tar -xzf -` reading stdin (which is
the local snapshot piped over ssh).

The backup runner takes snapshots with `cd /data && tar -czf - .` (relative
paths), so the inverse extracts with `cd /data && tar -xzf -` (also relative)
to land back in the same tree shape.
"""

from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path
from typing import Any


def _expand_key(ssh_key: str) -> Path:
    return Path(os.path.expanduser(ssh_key)).resolve()


def run_restore_docker_volume(
    config: dict[str, Any],
    snapshot_path: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """config keys consumed:
      ssh_alias      : SSH host alias (required)
      ssh_key        : path to private key (required)
      volume_name    : docker volume name on the remote (required)
      docker_image   : optional, default 'alpine:3.20'
    """
    ssh_alias = config.get("ssh_alias")
    ssh_key = config.get("ssh_key")
    volume_name = config.get("volume_name")
    docker_image = config.get("docker_image", "alpine:3.20")

    if not all([ssh_alias, ssh_key, volume_name, snapshot_path]):
        return {
            "ok": False,
            "verdict": "fail",
            "summary": "restore_docker_volume missing required fields",
            "receipt": "",
        }

    key_path = _expand_key(ssh_key)
    if not key_path.is_file():
        return {
            "ok": False,
            "verdict": "ceiling",
            "summary": f"SSH key not found at {key_path}; cannot restore",
            "receipt": (
                f"config.ssh_key = '{ssh_key}'\n"
                f"expanded path  = '{key_path}'\n"
                "action          = Owner must create the key or fix the path"
            ),
        }

    snap = Path(snapshot_path)
    if not snap.is_file():
        return {
            "ok": False,
            "verdict": "ceiling",
            "summary": f"snapshot path does not exist: {snapshot_path}",
            "receipt": f"snapshot expected at: {snap}\naction = source_selector returned a stale path",
        }

    remote_cmd = (
        f"docker run --rm -i -v {shlex.quote(volume_name)}:/data {shlex.quote(docker_image)} "
        "sh -c 'cd /data && tar -xzf -'"
    )
    ssh_cmd = ["ssh", "-i", str(key_path), ssh_alias, remote_cmd]

    if dry_run:
        plan = [
            f"DRY RUN -- ssh key resolved: {key_path}",
            f"DRY RUN -- ssh_alias: {ssh_alias}",
            f"DRY RUN -- volume: {volume_name}",
            f"DRY RUN -- docker_image: {docker_image}",
            f"DRY RUN -- snapshot: {snap}",
            f"DRY RUN -- would execute: cat {snap} | ssh -i {key_path} {ssh_alias} {shlex.quote(remote_cmd)}",
        ]
        return {
            "ok": True,
            "verdict": "dry-run",
            "summary": f"restore_docker_volume dry-run for {volume_name}",
            "receipt": "\n".join(plan),
        }

    receipt_parts: list[str] = [
        f"RESTORE source: {snap} ({snap.stat().st_size} bytes)",
        f"REMOTE: docker run --rm -i -v {volume_name}:/data {docker_image} 'cd /data && tar -xzf -'",
    ]

    try:
        with snap.open("rb") as src:
            proc = subprocess.run(
                ssh_cmd,
                stdin=src,
                capture_output=True,
                timeout=3600,
                check=False,
            )
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "verdict": "fail",
            "summary": "ssh+docker tar restore timed out (>1 h)",
            "receipt": f"TimeoutExpired: {exc}",
        }

    stderr = (proc.stderr or b"").decode("utf-8", errors="replace")
    receipt_parts.append(f"DOCKER-TAR exit={proc.returncode}")
    if stderr:
        receipt_parts.append(f"DOCKER-TAR stderr (last 500): {stderr[-500:]}")

    if proc.returncode != 0:
        return {
            "ok": False,
            "verdict": "fail",
            "summary": f"docker-volume restore failed (exit {proc.returncode})",
            "receipt": "\n".join(receipt_parts),
        }

    return {
        "ok": True,
        "verdict": "pass",
        "summary": f"restore_docker_volume to {volume_name}@{ssh_alias} succeeded",
        "receipt": "\n".join(receipt_parts),
    }
