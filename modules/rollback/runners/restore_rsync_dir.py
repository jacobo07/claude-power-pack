"""restore_rsync_dir runner -- inverse of backup/runners/rsync_dir.py.

Stream local <ts>.tar.gz back to the remote via ssh+tar -xzf -. The backup
was taken with `tar --create -P <abs_paths>` so the archive entries are
absolute and recreate exactly where they came from when extracted at /.

Optional post_restore_cmd runs after the extraction (e.g.
"sudo systemctl restart kobiicraft@main").

Same SSH key + alias pattern as the backup runner -- credentials live in
~/.ssh/config / ~/.ssh/<keyfile>, never in the rollback config.
"""

from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path
from typing import Any


def _expand_key(ssh_key: str) -> Path:
    return Path(os.path.expanduser(ssh_key)).resolve()


def run_restore_rsync_dir(
    config: dict[str, Any],
    snapshot_path: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """config keys consumed:
      ssh_alias        : SSH host alias (required)
      ssh_key          : path to private key (required)
      post_restore_cmd : optional post-extraction shell command on remote
    """
    ssh_alias = config.get("ssh_alias")
    ssh_key = config.get("ssh_key")
    post_restore_cmd = config.get("post_restore_cmd", "").strip()

    if not all([ssh_alias, ssh_key, snapshot_path]):
        return {
            "ok": False,
            "verdict": "fail",
            "summary": "restore_rsync_dir missing required fields (ssh_alias|ssh_key|snapshot_path)",
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

    remote_extract_cmd = "tar -xzf - -C /"
    ssh_extract = ["ssh", "-i", str(key_path), ssh_alias, remote_extract_cmd]

    if dry_run:
        plan = [
            f"DRY RUN -- ssh key resolved: {key_path}",
            f"DRY RUN -- ssh_alias: {ssh_alias}",
            f"DRY RUN -- snapshot: {snap}",
            f"DRY RUN -- would execute: cat {snap} | ssh -i {key_path} {ssh_alias} {shlex.quote(remote_extract_cmd)}",
        ]
        if post_restore_cmd:
            plan.append(
                f"DRY RUN -- would execute (post-restore): ssh -i {key_path} {ssh_alias} {shlex.quote(post_restore_cmd)}"
            )
        else:
            plan.append("DRY RUN -- no post_restore_cmd configured")
        return {
            "ok": True,
            "verdict": "dry-run",
            "summary": f"restore_rsync_dir dry-run for {ssh_alias}",
            "receipt": "\n".join(plan),
        }

    receipt_parts: list[str] = []
    receipt_parts.append(f"RESTORE source: {snap} ({snap.stat().st_size} bytes)")

    try:
        with snap.open("rb") as src:
            proc = subprocess.run(
                ssh_extract,
                stdin=src,
                capture_output=True,
                timeout=3600,
                check=False,
            )
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "verdict": "fail",
            "summary": "ssh+tar restore timed out (>1 h)",
            "receipt": f"TimeoutExpired: {exc}",
        }

    stderr_extract = (proc.stderr or b"").decode("utf-8", errors="replace")
    receipt_parts.append(f"EXTRACT exit={proc.returncode}")
    if stderr_extract:
        receipt_parts.append(f"EXTRACT stderr (last 500): {stderr_extract[-500:]}")

    if proc.returncode != 0:
        return {
            "ok": False,
            "verdict": "fail",
            "summary": f"ssh+tar extract failed (exit {proc.returncode})",
            "receipt": "\n".join(receipt_parts),
        }

    if post_restore_cmd:
        ssh_post = ["ssh", "-i", str(key_path), ssh_alias, post_restore_cmd]
        try:
            post = subprocess.run(ssh_post, capture_output=True, timeout=600, check=False)
        except subprocess.TimeoutExpired as exc:
            receipt_parts.append(f"POST-RESTORE TimeoutExpired: {exc}")
            return {
                "ok": False,
                "verdict": "fail",
                "summary": "post-restore command timed out (>10 min)",
                "receipt": "\n".join(receipt_parts),
            }
        post_stderr = (post.stderr or b"").decode("utf-8", errors="replace")
        receipt_parts.append(f"POST-RESTORE ({post_restore_cmd}) exit={post.returncode}")
        if post_stderr:
            receipt_parts.append(f"POST-RESTORE stderr (last 500): {post_stderr[-500:]}")
        if post.returncode != 0:
            return {
                "ok": False,
                "verdict": "fail",
                "summary": f"post-restore command failed (exit {post.returncode})",
                "receipt": "\n".join(receipt_parts),
            }

    return {
        "ok": True,
        "verdict": "pass",
        "summary": f"restore_rsync_dir to {ssh_alias} succeeded",
        "receipt": "\n".join(receipt_parts),
    }
