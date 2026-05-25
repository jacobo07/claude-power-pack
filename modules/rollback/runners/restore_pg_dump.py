"""restore_pg_dump runner -- inverse of backup/runners/pg_dump.py.

Stream local <ts>.dump back to the remote via ssh + docker exec + pg_restore.
The -c (--clean) flag drops + recreates database objects before reload,
which is the correct semantics for a rollback: the current state IS what
we are replacing.

Exit-code semantics:
  - exit 0                    -> verdict 'pass'
  - exit 1 with stderr only   -> verdict 'pass' with warnings_only flag.
    "warning:" lines             pg_restore -c routinely emits warnings
                                 for objects it tries to drop that do not
                                 yet exist on a fresh database; these are
                                 not failures.
  - exit !=0 with real errors -> verdict 'fail'

Authentication: ~/.pgpass on the remote host OR POSTGRES_PASSWORD in the
container env. NEVER in the rollback config (schema validator rejects).
"""

from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path
from typing import Any


def _expand_key(ssh_key: str) -> Path:
    return Path(os.path.expanduser(ssh_key)).resolve()


def _is_warnings_only(stderr_text: str) -> bool:
    """True if every non-empty stderr line starts with 'pg_restore: warning'
    (case-insensitive). Lets us treat exit 1 with only warnings as pass.
    """
    if not stderr_text:
        return True
    for line in stderr_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        low = stripped.lower()
        if low.startswith("pg_restore: warning"):
            continue
        if low.startswith("warning:"):
            continue
        return False
    return True


def run_restore_pg_dump(
    config: dict[str, Any],
    snapshot_path: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """config keys consumed:
      ssh_alias      : SSH host alias (required)
      ssh_key        : path to private key (required)
      pg_container   : docker container name on remote (required)
      pg_user        : Postgres user (required)
      pg_database    : Postgres database (required)
    """
    ssh_alias = config.get("ssh_alias")
    ssh_key = config.get("ssh_key")
    pg_container = config.get("pg_container")
    pg_user = config.get("pg_user")
    pg_database = config.get("pg_database")

    if not all([ssh_alias, ssh_key, pg_container, pg_user, pg_database, snapshot_path]):
        return {
            "ok": False,
            "verdict": "fail",
            "summary": "restore_pg_dump missing required fields",
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
        f"docker exec -i {shlex.quote(pg_container)} "
        f"pg_restore -c -U {shlex.quote(pg_user)} -d {shlex.quote(pg_database)}"
    )
    ssh_cmd = ["ssh", "-i", str(key_path), ssh_alias, remote_cmd]

    if dry_run:
        plan = [
            f"DRY RUN -- ssh key resolved: {key_path}",
            f"DRY RUN -- ssh_alias: {ssh_alias}",
            f"DRY RUN -- pg_container: {pg_container}",
            f"DRY RUN -- pg_user: {pg_user}",
            f"DRY RUN -- pg_database: {pg_database}",
            f"DRY RUN -- snapshot: {snap}",
            f"DRY RUN -- would execute: cat {snap} | ssh -i {key_path} {ssh_alias} {shlex.quote(remote_cmd)}",
            "DRY RUN -- password lives in remote ~/.pgpass or container env, never in this config",
            "DRY RUN -- -c flag drops + recreates objects before reload (correct rollback semantics)",
        ]
        return {
            "ok": True,
            "verdict": "dry-run",
            "summary": f"restore_pg_dump dry-run for {pg_database}@{ssh_alias}",
            "receipt": "\n".join(plan),
        }

    receipt_parts: list[str] = [
        f"RESTORE source: {snap} ({snap.stat().st_size} bytes)",
        f"REMOTE: docker exec -i {pg_container} pg_restore -c -U {pg_user} -d {pg_database}",
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
            "summary": "ssh+pg_restore timed out (>1 h)",
            "receipt": f"TimeoutExpired: {exc}",
        }

    stderr = (proc.stderr or b"").decode("utf-8", errors="replace")
    receipt_parts.append(f"PG_RESTORE exit={proc.returncode}")
    if stderr:
        receipt_parts.append(f"PG_RESTORE stderr (last 800): {stderr[-800:]}")

    if proc.returncode == 0:
        return {
            "ok": True,
            "verdict": "pass",
            "summary": f"pg_restore to {pg_database}@{ssh_alias} succeeded (exit 0)",
            "receipt": "\n".join(receipt_parts),
        }

    if proc.returncode == 1 and _is_warnings_only(stderr):
        receipt_parts.append("CLASSIFICATION: exit 1 but stderr contains only pg_restore warnings -> pass with warnings_only=true")
        return {
            "ok": True,
            "verdict": "pass",
            "summary": f"pg_restore to {pg_database}@{ssh_alias} succeeded with warnings",
            "warnings_only": True,
            "receipt": "\n".join(receipt_parts),
        }

    return {
        "ok": False,
        "verdict": "fail",
        "summary": f"pg_restore failed (exit {proc.returncode})",
        "receipt": "\n".join(receipt_parts),
    }
