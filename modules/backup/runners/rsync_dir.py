"""rsync-dir runner -- tar+gzip+ssh pipe to a local file.

Used for filesystem-tree snapshots (KobiiCraft worlds + plugin data).
Pure tar; no rsync binary required (despite the legacy mode name).
The remote host needs only `tar` + `gzip` -- both present on any
Linux distro the VPS runs.

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


def _build_remote_tar_cmd(remote_paths: list[str]) -> str:
    """Build the remote-side `tar` command. Uses absolute paths;
    each path is processed via its own basename relative to '/'.
    The receiver gets a single .tar.gz stream.
    """
    quoted = " ".join(shlex.quote(p) for p in remote_paths)
    return f"tar --create -P {quoted} | gzip -1"


def run_rsync_dir(
    config: dict[str, Any],
    dry_run: bool = False,
) -> dict[str, Any]:
    """Execute the rsync-dir backup. Returns receipt dict.

    config keys consumed:
      ssh_alias         : SSH host alias (required)
      ssh_key           : path to private key (required)
      remote_paths      : list of absolute paths on the remote (required, non-empty)
      local_destination : local dir to write the .tar.gz (required)
      project_root      : repo root (required, used to resolve local_destination)
    """
    ssh_alias = config.get("ssh_alias")
    ssh_key = config.get("ssh_key")
    remote_paths = config.get("remote_paths") or []
    local_destination = config.get("local_destination")
    project_root = config.get("project_root")

    if not all([ssh_alias, ssh_key, remote_paths, local_destination, project_root]):
        return {
            "ok": False,
            "verdict": "fail",
            "summary": "rsync-dir runner missing required config fields",
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

    remote_cmd = _build_remote_tar_cmd(remote_paths)
    ssh_cmd = ["ssh", "-i", str(key_path), ssh_alias, remote_cmd]

    if dry_run:
        plan = [
            f"DRY RUN -- ssh key resolved: {key_path}",
            f"DRY RUN -- ssh_alias: {ssh_alias}",
            f"DRY RUN -- remote paths: {remote_paths}",
            f"DRY RUN -- would execute: ssh -i {key_path} {ssh_alias} {shlex.quote(remote_cmd)}",
            f"DRY RUN -- snapshot would land at: {snapshot_path}",
        ]
        return {
            "ok": True,
            "verdict": "dry-run",
            "summary": f"rsync-dir dry-run for {ssh_alias}",
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
            "summary": "ssh+tar timed out (>1 h)",
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
            "summary": f"ssh+tar failed (exit {proc.returncode})",
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
            "summary": "ssh+tar returned 0 bytes; snapshot is empty",
            "snapshot_path": None,
            "snapshot_size_bytes": 0,
            "snapshot_sha256": "",
            "receipt": stderr[-2000:],
        }

    sha = _sha256_file(snapshot_path)
    return {
        "ok": True,
        "verdict": "pass",
        "summary": f"rsync-dir snapshot OK ({size} bytes)",
        "snapshot_path": str(snapshot_path),
        "snapshot_size_bytes": size,
        "snapshot_sha256": sha,
        "receipt": (
            f"snapshot: {snapshot_path}\n"
            f"size:     {size} bytes\n"
            f"sha256:   {sha}\n"
            f"ssh stderr (last 500): {stderr[-500:]}"
        ),
    }
