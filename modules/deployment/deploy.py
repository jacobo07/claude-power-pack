"""Deploy dispatcher -- entry point for the deployment skill.

Reads STDIN JSON, runs the detector, dispatches to the matched runner,
executes the healthcheck, writes the receipt to vault/deploys/, emits
the verdict JSON to STDOUT.

Hard invariant: vault/deploys/<ts>_*.md is written ONLY after the
healthcheck has run. Silent masking is forbidden. A healthcheck
failure with a successful deploy yields verdict 'deploy-warn' AND
the report states the failure in plain text.

Recursion guard: CLAUDEPP_DEPLOY_RUNNING is NOT set at level-1
(the entry point itself). It is checked on entry as a short-circuit
for level-2+ chains only. This pattern was sealed as lesson L2 in
the code-review skill cycle.

Opt-out: CLAUDEPP_DEPLOY_DISABLED=1 -> verdict 'skip' exit 0.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from detectors import detect_deploy_target  # noqa: E402
from healthcheck import run_healthcheck  # noqa: E402
from runners.gh_workflow import run_gh_workflow  # noqa: E402
from runners.git_push import run_git_push  # noqa: E402
from runners.scp_systemd import run_scp_systemd, validate_config  # noqa: E402


EXIT_PASS = 0
EXIT_FAIL = 2
EXIT_DEPLOY_WARN = 3
EXIT_CEILING = 4


def _git_head_short(project_root: str) -> str:
    import subprocess

    try:
        result = subprocess.run(
            ["git", "-C", project_root, "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode == 0:
            return (result.stdout or "").strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return ""


def _previous_deploys(project_root: Path, project: str, n: int = 5) -> list[str]:
    """Return the most recent N prior deploy report filenames for the
    same project. Mechanical -- glob + sort + slice. Used for the
    closed-loop signal returned to the caller.
    """
    reports_dir = project_root / "vault" / "deploys"
    if not reports_dir.is_dir():
        return []
    pattern = f"*_{project}_*.md"
    matches = sorted(reports_dir.glob(pattern), reverse=True)
    return [str(p.relative_to(project_root)) for p in matches[:n]]


def _write_receipt(
    project_root: Path,
    project: str,
    env: str,
    detection: dict[str, Any],
    runner_result: dict[str, Any],
    healthcheck_result: dict[str, Any] | None,
    head_sha: str,
    duration_ms: int,
) -> str:
    reports_dir = project_root / "vault" / "deploys"
    reports_dir.mkdir(parents=True, exist_ok=True)
    ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    fname = f"{ts}_{project}_{env}.md"
    fpath = reports_dir / fname

    cite = runner_result.get("doctrine_cite") or ""
    hc_block = "(no healthcheck spec)" if healthcheck_result is None else json.dumps(
        healthcheck_result, indent=2, ensure_ascii=False
    )

    body = f"""# Deploy receipt -- {project} / {env}

- Timestamp (UTC): {ts}
- HEAD: {head_sha or 'unknown'}
- Duration: {duration_ms} ms
- Mode: {detection.get('mode')}
- Detection evidence: {detection.get('evidence')}
- Doctrine cite: {cite or '(none)'}

## 1. Mode detected

```
{json.dumps(detection, indent=2, ensure_ascii=False)}
```

## 2. Build summary / Runner verdict

- verdict: {runner_result.get('verdict')}
- ok: {runner_result.get('ok')}
- summary: {runner_result.get('summary')}

## 3. Receipt (runner output, last lines)

```
{runner_result.get('receipt', '')}
```

## 4. Healthcheck

```
{hc_block}
```
"""
    fpath.write_bytes(body.encode("utf-8"))
    return str(fpath.relative_to(project_root))


def _dispatch_runner(
    detection: dict[str, Any],
    config: dict[str, Any],
    dry_run: bool,
) -> dict[str, Any]:
    mode = detection.get("mode")
    if mode == "gh-workflow":
        config_with_wf = dict(config)
        config_with_wf.setdefault("workflow_file", detection.get("workflow_file"))
        return run_gh_workflow(config_with_wf, dry_run=dry_run)
    if mode == "git-push-to-deploy":
        return run_git_push(config, dry_run=dry_run)
    if mode == "manual-scp":
        return run_scp_systemd(config, dry_run=dry_run)
    return {
        "ok": False,
        "verdict": "ceiling",
        "summary": f"no runner for mode '{mode}'",
        "doctrine_cite": None,
        "receipt": "",
    }


def _load_config(
    project_root: Path,
    project: str,
    config_override: str | None,
) -> tuple[dict[str, Any], str]:
    """Load vault/deploy/<project>.json or the override path.
    Returns (config_dict, source_path).
    """
    if config_override:
        cfg_path = Path(config_override)
        if not cfg_path.is_absolute():
            cfg_path = project_root / cfg_path
    else:
        cfg_path = project_root / "vault" / "deploy" / f"{project}.json"
    if not cfg_path.is_file():
        return {}, str(cfg_path)
    try:
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, str(cfg_path)
    if not isinstance(data, dict):
        return {}, str(cfg_path)
    return data, str(cfg_path)


def deploy(stdin_payload: dict[str, Any]) -> dict[str, Any]:
    """Pure function: run the deploy pipeline. Returns verdict dict."""
    started = time.monotonic()
    project_root = Path(stdin_payload.get("project_root") or os.getcwd()).resolve()
    project = stdin_payload.get("project") or project_root.name
    env = stdin_payload.get("env", "prod")
    dry_run = bool(stdin_payload.get("dry_run", False))
    config_override = stdin_payload.get("config_override")

    if os.environ.get("CLAUDEPP_DEPLOY_DISABLED") == "1":
        return {
            "verdict": "skip",
            "exit_code": EXIT_PASS,
            "mode": None,
            "head_sha": "",
            "duration_ms": int((time.monotonic() - started) * 1000),
            "summary": "deploy disabled via CLAUDEPP_DEPLOY_DISABLED=1",
            "doctrine_cite": None,
        }

    detection = detect_deploy_target(project_root)
    if detection["mode"] == "none":
        return {
            "verdict": "ceiling",
            "exit_code": EXIT_CEILING,
            "mode": "none",
            "head_sha": _git_head_short(str(project_root)),
            "duration_ms": int((time.monotonic() - started) * 1000),
            "summary": f"no deploy signal: {detection['evidence']}",
            "doctrine_cite": None,
        }

    config, cfg_source = _load_config(project_root, project, config_override)
    config.setdefault("project_root", str(project_root))

    needs_hc = detection["mode"] in {"gh-workflow", "git-push-to-deploy", "manual-scp"}
    healthcheck_spec = config.get("healthcheck")
    if needs_hc and not healthcheck_spec:
        return {
            "verdict": "fail",
            "exit_code": EXIT_FAIL,
            "mode": detection["mode"],
            "head_sha": _git_head_short(str(project_root)),
            "duration_ms": int((time.monotonic() - started) * 1000),
            "summary": (
                f"healthcheck spec missing from config '{cfg_source}'. "
                "A deploy without a verified healthcheck is not a deploy."
            ),
            "doctrine_cite": None,
        }

    if detection["mode"] == "manual-scp":
        ok, reason = validate_config(config)
        if not ok:
            return {
                "verdict": "fail",
                "exit_code": EXIT_FAIL,
                "mode": detection["mode"],
                "head_sha": _git_head_short(str(project_root)),
                "duration_ms": int((time.monotonic() - started) * 1000),
                "summary": f"config validation failed: {reason}",
                "doctrine_cite": None,
            }

    runner_result = _dispatch_runner(detection, config, dry_run)

    if runner_result.get("verdict") in {"fail", "ceiling"}:
        head_sha = _git_head_short(str(project_root))
        duration_ms = int((time.monotonic() - started) * 1000)
        receipt_path = (
            _write_receipt(project_root, project, env, detection, runner_result, None, head_sha, duration_ms)
            if not dry_run
            else None
        )
        exit_code = EXIT_CEILING if runner_result["verdict"] == "ceiling" else EXIT_FAIL
        return {
            "verdict": runner_result["verdict"],
            "exit_code": exit_code,
            "mode": detection["mode"],
            "head_sha": head_sha,
            "duration_ms": duration_ms,
            "summary": runner_result.get("summary", ""),
            "doctrine_cite": runner_result.get("doctrine_cite"),
            "receipt_path": receipt_path,
            "previous_deploys": _previous_deploys(project_root, project),
        }

    if dry_run:
        duration_ms = int((time.monotonic() - started) * 1000)
        return {
            "verdict": "dry-run",
            "exit_code": EXIT_PASS,
            "mode": detection["mode"],
            "head_sha": _git_head_short(str(project_root)),
            "duration_ms": duration_ms,
            "summary": runner_result.get("summary", "dry-run"),
            "doctrine_cite": runner_result.get("doctrine_cite"),
            "receipt_path": None,
            "previous_deploys": _previous_deploys(project_root, project),
        }

    hc_result = run_healthcheck(healthcheck_spec)
    head_sha = _git_head_short(str(project_root))
    duration_ms = int((time.monotonic() - started) * 1000)
    receipt_path = _write_receipt(
        project_root, project, env, detection, runner_result, hc_result, head_sha, duration_ms
    )

    if hc_result.get("ok"):
        verdict = "pass"
        exit_code = EXIT_PASS
        summary = f"deploy + healthcheck OK ({hc_result.get('attempts')} attempts)"
    else:
        verdict = "deploy-warn"
        exit_code = EXIT_DEPLOY_WARN
        summary = (
            f"deploy executed but healthcheck FAILED after {hc_result.get('attempts')} "
            f"attempts -- target may not be live. Report: {receipt_path}"
        )

    return {
        "verdict": verdict,
        "exit_code": exit_code,
        "mode": detection["mode"],
        "head_sha": head_sha,
        "duration_ms": duration_ms,
        "summary": summary,
        "doctrine_cite": runner_result.get("doctrine_cite"),
        "receipt_path": receipt_path,
        "healthcheck": hc_result,
        "previous_deploys": _previous_deploys(project_root, project),
    }


def main() -> int:
    raw = sys.stdin.read().strip()
    if raw.startswith("﻿"):
        raw = raw[1:]
    payload = json.loads(raw) if raw else {}
    result = deploy(payload)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return int(result.get("exit_code", EXIT_FAIL))


if __name__ == "__main__":
    sys.exit(main())
