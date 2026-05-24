"""manual-scp runner -- build artefacts, scp to host, restart service.

Used when a project has no canonical CD pipeline but has a clear
build command, an SSH-reachable host, and a systemd service to
restart. The KobiiCraft model.

Schema validator rejects forbidden-key categories BEFORE any
runner action -- credentials never enter this module's runtime.
SSH key presence is verified before invocation; missing -> CEILING.
"""

from __future__ import annotations

import glob
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any


FORBIDDEN_KEY_TOKENS = (
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "passphrase",
)


REQUIRED_KEYS = (
    "ssh_alias",
    "ssh_key",
    "build_cmd",
    "artefact_glob",
    "remote_path",
    "post_deploy_cmd",
    "healthcheck",
)


def validate_config(config: dict[str, Any]) -> tuple[bool, str]:
    """Returns (ok, reason). On (False, reason) the dispatcher must
    exit 2 with the reason BEFORE executing anything.
    """
    if not isinstance(config, dict):
        return False, "config is not a JSON object"

    for key in REQUIRED_KEYS:
        if key not in config:
            return False, f"required key missing: '{key}'"

    for key in config.keys():
        lower = key.lower()
        for tok in FORBIDDEN_KEY_TOKENS:
            if tok in lower:
                return False, (
                    f"forbidden key category in config: '{key}' contains "
                    f"'{tok}'. Credentials must live in ~/.ssh/, not in vault/deploy/"
                )

    mode = config.get("mode", "")
    if mode in ("n8n", "zapier", "make.com", "pipedream"):
        return False, f"mode '{mode}' is permanently forbidden in PP"

    return True, "ok"


def _last_lines(text: str, n: int = 15) -> str:
    lines = (text or "").splitlines()
    return "\n".join(lines[-n:])


def _expand_key(ssh_key: str) -> Path:
    return Path(os.path.expanduser(ssh_key)).resolve()


def run_scp_systemd(
    config: dict[str, Any],
    dry_run: bool = False,
) -> dict[str, Any]:
    """Execute manual-scp deploy. Returns receipt dict.

    Flow:
      1. validate schema -> on fail, exit 2 fail verdict
      2. expand+verify ssh_key -> on missing, CEILING exit 4
      3. run build_cmd
      4. resolve artefact_glob (from project_root)
      5. scp each artefact to <ssh_alias>:<remote_path>
      6. ssh <ssh_alias> '<post_deploy_cmd>'
    """
    ok, reason = validate_config(config)
    if not ok:
        return {
            "ok": False,
            "verdict": "fail",
            "summary": f"config schema invalid: {reason}",
            "doctrine_cite": None,
            "receipt": "",
        }

    project_root = config.get("project_root")
    if not project_root:
        return {
            "ok": False,
            "verdict": "fail",
            "summary": "scp-systemd runner missing project_root",
            "doctrine_cite": None,
            "receipt": "",
        }

    ssh_alias = config["ssh_alias"]
    ssh_key = config["ssh_key"]
    build_cmd = config["build_cmd"]
    artefact_glob = config["artefact_glob"]
    remote_path = config["remote_path"]
    post_deploy_cmd = config["post_deploy_cmd"]

    key_path = _expand_key(ssh_key)
    if not key_path.is_file():
        return {
            "ok": False,
            "verdict": "ceiling",
            "summary": f"SSH key not found at {key_path}; cannot deploy",
            "doctrine_cite": None,
            "receipt": (
                f"config.ssh_key = '{ssh_key}'\n"
                f"expanded path  = '{key_path}'\n"
                f"action         = Owner must create the key or fix the path"
            ),
        }

    if dry_run:
        plan = [
            f"DRY RUN -- ssh key resolved: {key_path}",
            f"DRY RUN -- would invoke build: {build_cmd}",
            f"DRY RUN -- artefact glob: {artefact_glob}",
            f"DRY RUN -- would scp -i {key_path} <artefacts> {ssh_alias}:{remote_path}",
            f"DRY RUN -- would ssh {ssh_alias} {shlex.quote(post_deploy_cmd)}",
        ]
        return {
            "ok": True,
            "verdict": "dry-run",
            "summary": f"scp-systemd dry-run for {ssh_alias}",
            "doctrine_cite": None,
            "receipt": "\n".join(plan),
        }

    receipt_parts: list[str] = []

    try:
        build = subprocess.run(
            build_cmd,
            shell=True,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=1800,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "verdict": "fail",
            "summary": f"build timed out: {build_cmd}",
            "doctrine_cite": None,
            "receipt": f"TimeoutExpired: {exc}",
        }

    receipt_parts.append(f"BUILD ({build_cmd}) exit={build.returncode}")
    receipt_parts.append(_last_lines(build.stdout, 10))
    receipt_parts.append(_last_lines(build.stderr, 10))
    if build.returncode != 0:
        return {
            "ok": False,
            "verdict": "fail",
            "summary": f"build failed (exit {build.returncode})",
            "doctrine_cite": None,
            "receipt": "\n".join(receipt_parts),
        }

    artefacts = sorted(glob.glob(str(Path(project_root) / artefact_glob), recursive=True))
    if not artefacts:
        receipt_parts.append(f"WARN: artefact_glob '{artefact_glob}' matched 0 files")
        return {
            "ok": False,
            "verdict": "fail",
            "summary": "no artefacts matched build glob",
            "doctrine_cite": None,
            "receipt": "\n".join(receipt_parts),
        }
    receipt_parts.append(f"ARTEFACTS: {len(artefacts)} file(s) matched")

    scp_cmd = ["scp", "-i", str(key_path), "-q", *artefacts, f"{ssh_alias}:{remote_path}"]
    try:
        scp = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=600, check=False)
    except subprocess.TimeoutExpired as exc:
        receipt_parts.append(f"scp TimeoutExpired: {exc}")
        return {
            "ok": False,
            "verdict": "fail",
            "summary": "scp timed out (>10 min)",
            "doctrine_cite": None,
            "receipt": "\n".join(receipt_parts),
        }
    receipt_parts.append(f"SCP exit={scp.returncode}")
    receipt_parts.append(_last_lines(scp.stderr, 10))
    if scp.returncode != 0:
        return {
            "ok": False,
            "verdict": "fail",
            "summary": f"scp failed (exit {scp.returncode})",
            "doctrine_cite": None,
            "receipt": "\n".join(receipt_parts),
        }

    ssh_cmd = ["ssh", "-i", str(key_path), ssh_alias, post_deploy_cmd]
    try:
        ssh_run = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=300, check=False)
    except subprocess.TimeoutExpired as exc:
        receipt_parts.append(f"ssh TimeoutExpired: {exc}")
        return {
            "ok": False,
            "verdict": "fail",
            "summary": "ssh post-deploy timed out (>5 min)",
            "doctrine_cite": None,
            "receipt": "\n".join(receipt_parts),
        }
    receipt_parts.append(f"SSH POST-DEPLOY exit={ssh_run.returncode}")
    receipt_parts.append(_last_lines(ssh_run.stdout, 10))
    receipt_parts.append(_last_lines(ssh_run.stderr, 10))
    if ssh_run.returncode != 0:
        return {
            "ok": False,
            "verdict": "fail",
            "summary": f"post-deploy command failed (exit {ssh_run.returncode})",
            "doctrine_cite": None,
            "receipt": "\n".join(receipt_parts),
        }

    return {
        "ok": True,
        "verdict": "pass",
        "summary": f"scp-systemd deploy to {ssh_alias} succeeded",
        "doctrine_cite": None,
        "receipt": "\n".join(receipt_parts),
    }
