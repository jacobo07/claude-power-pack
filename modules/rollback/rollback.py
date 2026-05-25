"""Rollback dispatcher -- entry point for the Rollback Axis.

STDIN/STDOUT JSON contract per vault/specs/rollback-skill.md sec 5.

Pipeline:
  1. Honor CLAUDEPP_ROLLBACK_DISABLED -> skip exit 0.
  2. Load vault/rollback/<project>.json (or config_override).
  3. Schema validate (reject credential-class keys, forbidden modes).
  4. source_selector.select_source -- CEILING on any failure mode.
  5. Optional rescue_current=true -> snapshot current state first.
  6. Dispatch runner (restore_rsync_dir | restore_pg_dump | restore_docker_volume).
  7. Healthcheck (imported from modules/deployment/healthcheck.py).
  8. Optional include_code_rollback=true + project=infinityops:
     print sec 77 cite + invoke gh workflow run on prev_sha.
  9. Write receipt to vault/rollbacks/<ts>_<project>.md.

Reality contract: receipt is written ONLY after the post-restore healthcheck
has run. A successful runner with a failed healthcheck yields rollback-warn
(exit 3), not pass. No silent masking.

Recursion guard: CLAUDEPP_ROLLBACK_RUNNING is NOT set at level-1.

The Deploy Axis NEVER invokes this module directly. On a failed deploy,
deploy.py only SUGGESTS the /rollback command; the Owner decides.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

DEPLOYMENT_DIR = THIS_DIR.parent / "deployment"
if str(DEPLOYMENT_DIR) not in sys.path:
    sys.path.append(str(DEPLOYMENT_DIR))

BACKUP_DIR = THIS_DIR.parent / "backup"

from source_selector import select_source  # noqa: E402
from runners.restore_docker_volume import run_restore_docker_volume  # noqa: E402
from runners.restore_pg_dump import run_restore_pg_dump  # noqa: E402
from runners.restore_rsync_dir import run_restore_rsync_dir  # noqa: E402

from healthcheck import run_healthcheck  # noqa: E402

EXIT_PASS = 0
EXIT_FAIL = 2
EXIT_ROLLBACK_WARN = 3
EXIT_CEILING = 4

FORBIDDEN_KEY_TOKENS = (
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "passphrase",
)
FORBIDDEN_MODES = {"n8n", "zapier", "make.com", "pipedream"}
KNOWN_MODES = {"rsync-dir", "pg-dump", "docker-volume-tar"}

REQUIRED_KEYS = ("mode", "ssh_alias", "ssh_key", "healthcheck")

SEC77_CITE = (
    "sec 77 Deploy Sovereignty: code rollback for infinityops invokes the "
    "canonical deploy-vps.yml workflow on ref {ref}. This skill INVOKES "
    "that pipeline; it does not replace it."
)

HEAD_SHA_RE = re.compile(r"^- HEAD:\s+([0-9a-fA-F]{7,40})\s*$", re.MULTILINE)


def _ts() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d-%H%M%S")


def validate_config(config: dict[str, Any]) -> tuple[bool, str]:
    if not isinstance(config, dict):
        return False, "config is not a JSON object"
    for key in REQUIRED_KEYS:
        if key not in config:
            return False, f"required key missing: '{key}'"
    for key in config:
        low = key.lower()
        for tok in FORBIDDEN_KEY_TOKENS:
            if tok in low:
                return False, (
                    f"forbidden key category in config: '{key}' contains "
                    f"'{tok}'. Credentials must live in ~/.ssh/ or ~/.pgpass, "
                    "not in vault/rollback/"
                )
    mode = config.get("mode")
    if mode in FORBIDDEN_MODES:
        return False, f"mode '{mode}' is permanently forbidden in PP"
    if mode not in KNOWN_MODES:
        return False, f"mode '{mode}' is not a recognised rollback mode"
    return True, "ok"


def _load_config(
    project_root: Path,
    project: str,
    config_override: str | None,
) -> tuple[dict[str, Any], str]:
    if config_override:
        cfg_path = Path(config_override)
        if not cfg_path.is_absolute():
            cfg_path = project_root / cfg_path
    else:
        cfg_path = project_root / "vault" / "rollback" / f"{project}.json"
    if not cfg_path.is_file():
        return {}, str(cfg_path)
    try:
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, str(cfg_path)
    if not isinstance(data, dict):
        return {}, str(cfg_path)
    return data, str(cfg_path)


def _previous_rollbacks(project_root: Path, project: str, n: int = 5) -> list[str]:
    reports_dir = project_root / "vault" / "rollbacks"
    if not reports_dir.is_dir():
        return []
    pattern = f"*_{project}.md"
    matches = sorted(reports_dir.glob(pattern), reverse=True)
    return [str(p.relative_to(project_root)) for p in matches[:n]]


def _take_rescue(
    project_root: Path,
    project: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Take a rescue snapshot of current state to vault/rescues/.

    Reuses the backup runner for the same project's BACKUP config (not the
    rollback config) so the rescue captures exactly what backup would capture.
    Returns {ok, path, evidence}. On ok=False the dispatcher returns CEILING.
    """
    backup_cfg_path = project_root / "vault" / "backup" / f"{project}.json"
    if not backup_cfg_path.is_file():
        return {
            "ok": False,
            "path": None,
            "evidence": (
                f"rescue requested but backup config not found at {backup_cfg_path}; "
                "rescue depends on the same source-paths as backup"
            ),
        }
    try:
        backup_cfg = json.loads(backup_cfg_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "path": None, "evidence": f"backup config unreadable: {exc}"}

    rescues_dir = project_root / "vault" / "rescues"
    rescues_dir.mkdir(parents=True, exist_ok=True)

    rescue_cfg = dict(backup_cfg)
    rescue_cfg["project_root"] = str(project_root)
    rescue_cfg["local_destination"] = f"vault/rescues/{project}/"

    mode = backup_cfg.get("mode")
    if str(BACKUP_DIR) not in sys.path:
        sys.path.append(str(BACKUP_DIR))
    backup_runners_dir = BACKUP_DIR / "runners"
    if str(backup_runners_dir) not in sys.path:
        sys.path.append(str(backup_runners_dir))
    if mode == "rsync-dir":
        from rsync_dir import run_rsync_dir as _run_rsync  # noqa: E402

        result = _run_rsync(rescue_cfg, dry_run=False)
    elif mode == "pg-dump":
        from pg_dump import run_pg_dump as _run_pg  # noqa: E402

        result = _run_pg(rescue_cfg, dry_run=False)
    elif mode == "docker-volume-tar":
        from docker_volume_tar import run_docker_volume_tar as _run_dv  # noqa: E402

        result = _run_dv(rescue_cfg, dry_run=False)
    else:
        return {
            "ok": False,
            "path": None,
            "evidence": f"rescue: backup config has unknown mode {mode!r}",
        }

    if result.get("verdict") != "pass":
        return {
            "ok": False,
            "path": result.get("snapshot_path"),
            "evidence": (
                f"rescue snapshot did not reach verdict=pass "
                f"(got {result.get('verdict')}): {result.get('summary')}"
            ),
        }
    return {
        "ok": True,
        "path": result.get("snapshot_path"),
        "evidence": f"rescue OK: {result.get('summary')}",
    }


def _extract_prev_sha(project_root: Path, project: str) -> tuple[str | None, str]:
    """Extract latest deployed sha from vault/deploys/*_<project>.md.

    Returns (sha, evidence). sha is None on any failure path.
    """
    deploys_dir = project_root / "vault" / "deploys"
    if not deploys_dir.is_dir():
        return None, f"no deploy receipts directory at {deploys_dir}"
    pattern = f"*_{project}.md"
    matches = sorted(deploys_dir.glob(pattern), reverse=True)
    if not matches:
        return None, f"no deploy receipts for {project} under {deploys_dir}"
    latest = matches[0]
    try:
        text = latest.read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"deploy receipt unreadable: {exc}"
    m = HEAD_SHA_RE.search(text)
    if not m:
        return None, (
            f"deploy receipt {latest.name} does not contain a parseable "
            "'- HEAD: <sha>' line (this happens for dry-run receipts where "
            "git was not on PATH)"
        )
    return m.group(1), f"extracted prev_sha {m.group(1)[:12]} from {latest.name}"


def _run_code_rollback_gh_workflow(
    project_root: Path,
    config: dict[str, Any],
    dry_run: bool,
) -> dict[str, Any]:
    prev_sha, evidence = _extract_prev_sha(project_root, "infinityops")
    if prev_sha is None:
        return {
            "ok": False,
            "ref": None,
            "evidence": evidence,
            "doctrine_cite": "",
        }

    cite = SEC77_CITE.format(ref=prev_sha)
    print(cite)

    workflow_file = config.get("code_rollback_workflow", "deploy-vps.yml")
    if dry_run:
        return {
            "ok": True,
            "ref": prev_sha,
            "evidence": (
                f"DRY RUN -- would invoke: gh workflow run {workflow_file} --ref {prev_sha}"
            ),
            "doctrine_cite": cite,
        }

    cmd = ["gh", "workflow", "run", workflow_file, "--ref", prev_sha]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {
            "ok": False,
            "ref": prev_sha,
            "evidence": f"gh workflow run failed: {exc}",
            "doctrine_cite": cite,
        }
    if proc.returncode != 0:
        return {
            "ok": False,
            "ref": prev_sha,
            "evidence": (
                f"gh workflow run exit {proc.returncode}; "
                f"stderr (last 500): {(proc.stderr or '')[-500:]}"
            ),
            "doctrine_cite": cite,
        }
    return {
        "ok": True,
        "ref": prev_sha,
        "evidence": f"gh workflow run dispatched on ref {prev_sha}",
        "doctrine_cite": cite,
    }


def _write_receipt(
    project_root: Path,
    project: str,
    config: dict[str, Any],
    source: dict[str, Any],
    rescue: dict[str, Any] | None,
    runner_result: dict[str, Any],
    healthcheck_result: dict[str, Any],
    code_rollback: dict[str, Any] | None,
    verdict: str,
    duration_ms: int,
) -> str:
    reports_dir = project_root / "vault" / "rollbacks"
    reports_dir.mkdir(parents=True, exist_ok=True)
    ts = _ts()
    fname = f"{ts}_{project}.md"
    fpath = reports_dir / fname

    rescue_block = "(rescue not requested)" if rescue is None else json.dumps(rescue, indent=2)
    code_block = "(code rollback not requested)" if code_rollback is None else json.dumps(code_rollback, indent=2)

    body = f"""# Rollback receipt -- {project}

- Timestamp (UTC): {ts}
- Duration: {duration_ms} ms
- Verdict: {verdict}
- Mode: {config.get('mode')}
- SSH alias: {config.get('ssh_alias')}

## 1. Source snapshot (selected from manifest)

```
{json.dumps(source, indent=2)}
```

## 2. Rescue snapshot (pre-rollback current state)

```
{rescue_block}
```

## 3. Runner verdict

- verdict: {runner_result.get('verdict')}
- ok: {runner_result.get('ok')}
- summary: {runner_result.get('summary')}

## 4. Runner receipt

```
{runner_result.get('receipt', '')}
```

## 5. Healthcheck (post-rollback)

```
{json.dumps(healthcheck_result, indent=2)}
```

## 6. Code rollback (sec 77 path, infinityops only)

```
{code_block}
```
"""
    fpath.write_bytes(body.encode("utf-8"))
    return str(fpath.relative_to(project_root))


def _dispatch_runner(
    config: dict[str, Any],
    snapshot_path: str,
    dry_run: bool,
) -> dict[str, Any]:
    mode = config.get("mode")
    if mode == "rsync-dir":
        return run_restore_rsync_dir(config, snapshot_path, dry_run=dry_run)
    if mode == "pg-dump":
        return run_restore_pg_dump(config, snapshot_path, dry_run=dry_run)
    if mode == "docker-volume-tar":
        return run_restore_docker_volume(config, snapshot_path, dry_run=dry_run)
    return {
        "ok": False,
        "verdict": "fail",
        "summary": f"unknown mode '{mode}'",
        "receipt": "",
    }


def rollback(stdin_payload: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    project_root = Path(stdin_payload.get("project_root") or os.getcwd()).resolve()
    project = stdin_payload.get("project") or project_root.name
    dry_run = bool(stdin_payload.get("dry_run", False))
    target_snapshot = stdin_payload.get("target_snapshot")
    rescue_current = bool(stdin_payload.get("rescue_current", False))
    include_code_rollback = bool(stdin_payload.get("include_code_rollback", False))
    config_override = stdin_payload.get("config_override")

    if os.environ.get("CLAUDEPP_ROLLBACK_DISABLED") == "1":
        return {
            "verdict": "skip",
            "exit_code": EXIT_PASS,
            "mode": None,
            "duration_ms": int((time.monotonic() - started) * 1000),
            "summary": "rollback disabled via CLAUDEPP_ROLLBACK_DISABLED=1",
        }

    config, cfg_source = _load_config(project_root, project, config_override)
    if not config:
        return {
            "verdict": "ceiling",
            "exit_code": EXIT_CEILING,
            "mode": None,
            "duration_ms": int((time.monotonic() - started) * 1000),
            "summary": f"rollback config not found or invalid at {cfg_source}",
        }

    ok, reason = validate_config(config)
    if not ok:
        return {
            "verdict": "fail",
            "exit_code": EXIT_FAIL,
            "mode": config.get("mode"),
            "duration_ms": int((time.monotonic() - started) * 1000),
            "summary": f"config schema invalid: {reason}",
        }

    source = select_source(project_root, project, target_snapshot, config)
    if not source.get("ok"):
        return {
            "verdict": "ceiling",
            "exit_code": EXIT_CEILING,
            "mode": config.get("mode"),
            "duration_ms": int((time.monotonic() - started) * 1000),
            "summary": f"source selector CEILING: {source.get('reason')} -- {source.get('evidence')}",
            "source_selector": source,
        }

    if dry_run:
        runner_result = _dispatch_runner(config, source["path"], dry_run=True)
        code_rollback: dict[str, Any] | None = None
        if include_code_rollback and project == "infinityops":
            code_rollback = _run_code_rollback_gh_workflow(project_root, config, dry_run=True)
        return {
            "verdict": "dry-run",
            "exit_code": EXIT_PASS,
            "mode": config.get("mode"),
            "duration_ms": int((time.monotonic() - started) * 1000),
            "summary": runner_result.get("summary", "dry-run"),
            "source_snapshot": source["path"],
            "source_sha256": source.get("sha256", ""),
            "source_verified": True,
            "rescue_path": None,
            "code_rollback_invoked": bool(code_rollback and code_rollback.get("ok")),
            "code_rollback_ref": (code_rollback or {}).get("ref"),
            "healthcheck_result": {"ok": None, "kind": (config.get("healthcheck") or {}).get("kind"), "evidence": "dry-run; healthcheck not executed"},
            "runner_receipt": runner_result.get("receipt", ""),
            "previous_rollbacks": _previous_rollbacks(project_root, project),
            "code_rollback_detail": code_rollback,
        }

    rescue: dict[str, Any] | None = None
    if rescue_current:
        rescue = _take_rescue(project_root, project, config)
        if not rescue.get("ok"):
            return {
                "verdict": "ceiling",
                "exit_code": EXIT_CEILING,
                "mode": config.get("mode"),
                "duration_ms": int((time.monotonic() - started) * 1000),
                "summary": f"rescue requested but failed: {rescue.get('evidence')}",
                "rescue": rescue,
            }

    runner_result = _dispatch_runner(config, source["path"], dry_run=False)
    if runner_result.get("verdict") in {"fail", "ceiling"}:
        verdict = runner_result["verdict"]
        exit_code = EXIT_CEILING if verdict == "ceiling" else EXIT_FAIL
        duration_ms = int((time.monotonic() - started) * 1000)
        receipt_path = _write_receipt(
            project_root,
            project,
            config,
            source,
            rescue,
            runner_result,
            {"ok": False, "kind": (config.get("healthcheck") or {}).get("kind"), "evidence": "runner failed -- healthcheck not attempted"},
            None,
            verdict,
            duration_ms,
        )
        return {
            "verdict": verdict,
            "exit_code": exit_code,
            "mode": config.get("mode"),
            "duration_ms": duration_ms,
            "summary": runner_result.get("summary", ""),
            "source_snapshot": source["path"],
            "rescue_path": (rescue or {}).get("path"),
            "receipt_path": receipt_path,
            "previous_rollbacks": _previous_rollbacks(project_root, project),
        }

    healthcheck_result = run_healthcheck(config.get("healthcheck") or {})

    code_rollback: dict[str, Any] | None = None
    if include_code_rollback and project == "infinityops":
        code_rollback = _run_code_rollback_gh_workflow(project_root, config, dry_run=False)

    if healthcheck_result.get("ok"):
        verdict = "pass"
        exit_code = EXIT_PASS
        summary = (
            f"rollback OK from {Path(source['path']).name}; healthcheck "
            f"{healthcheck_result.get('kind')} passed in {healthcheck_result.get('attempts')} attempt(s)"
        )
    else:
        verdict = "rollback-warn"
        exit_code = EXIT_ROLLBACK_WARN
        summary = (
            f"rollback bytes restored from {Path(source['path']).name} but "
            f"healthcheck {healthcheck_result.get('kind')} FAILED. "
            "Owner investigates."
        )

    duration_ms = int((time.monotonic() - started) * 1000)
    receipt_path = _write_receipt(
        project_root,
        project,
        config,
        source,
        rescue,
        runner_result,
        healthcheck_result,
        code_rollback,
        verdict,
        duration_ms,
    )

    return {
        "verdict": verdict,
        "exit_code": exit_code,
        "mode": config.get("mode"),
        "duration_ms": duration_ms,
        "summary": summary,
        "source_snapshot": source["path"],
        "source_sha256": source.get("sha256", ""),
        "source_verified": True,
        "rescue_path": (rescue or {}).get("path"),
        "code_rollback_invoked": bool(code_rollback and code_rollback.get("ok")),
        "code_rollback_ref": (code_rollback or {}).get("ref"),
        "healthcheck_result": healthcheck_result,
        "receipt_path": receipt_path,
        "previous_rollbacks": _previous_rollbacks(project_root, project),
    }


def main() -> int:
    raw = sys.stdin.read().strip()
    if raw.startswith("﻿"):
        raw = raw[1:]
    payload = json.loads(raw) if raw else {}
    result = rollback(payload)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return int(result.get("exit_code", EXIT_FAIL))


if __name__ == "__main__":
    sys.exit(main())
