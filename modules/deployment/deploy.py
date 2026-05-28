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
import subprocess
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


def _rollback_suggestion(project: str) -> str:
    """Literal suggestion string surfaced on failed deploys.

    The Rollback Axis is NEVER invoked from this module. V-NO-AUTO in
    modules/rollback/test_v_block.py grep-asserts there is zero call site
    of the rollback dispatcher here. This function only emits text the
    Owner can copy and run themselves. See spec sec 10.
    """
    return (
        f"To roll back: /rollback --project {project}   "
        "(NOT auto-invoked; Owner decides)"
    )


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
    overall_verdict: str | None = None,
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

    effective_verdict = overall_verdict or runner_result.get("verdict") or ""
    if effective_verdict in {"fail", "ceiling", "deploy-warn"}:
        rollback_block = _rollback_suggestion(project)
    elif effective_verdict == "pass":
        rollback_block = "(deploy succeeded -- rollback not applicable)"
    else:
        rollback_block = "(verdict not classified)"

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

## 5. Rollback

{rollback_block}
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


def _run_pre_deploy_backup_if_enabled(
    config: dict[str, Any],
    project: str,
    project_root: Path,
    dry_run: bool,
) -> dict[str, Any] | None:
    """If the deploy config has `pre_deploy_backup: true`, spawn the
    backup dispatcher BEFORE the deploy runner. The backup verdict
    gates the deploy: anything other than pass/dry-run/skip aborts
    with CEILING.

    Returns the backup result dict, or None if the gate is not enabled.

    NOTE: this is a level-1 piggyback spawn. The recursion-guard env
    var CLAUDEPP_BACKUP_RUNNING is NOT set here (lesson L2 sealed in
    code-review + deploy cycles).
    """
    if not config.get("pre_deploy_backup"):
        return None
    if os.environ.get("CLAUDEPP_BACKUP_DISABLED") == "1":
        return {"verdict": "skip", "summary": "backup gate skipped via CLAUDEPP_BACKUP_DISABLED=1"}
    backup_script = Path(__file__).resolve().parent.parent / "backup" / "backup.py"
    if not backup_script.is_file():
        return {"verdict": "fail", "summary": f"backup dispatcher missing at {backup_script}"}
    payload = json.dumps({
        "project_root": str(project_root),
        "project": project,
        "dry_run": dry_run,
    })
    try:
        result = subprocess.run(
            [sys.executable, str(backup_script)],
            input=payload,
            capture_output=True,
            text=True,
            timeout=3700,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {"verdict": "fail", "summary": f"backup spawn error: {type(exc).__name__}: {exc}"}
    out = (result.stdout or "").strip()
    if out.startswith("﻿"):
        out = out[1:]
    try:
        return json.loads(out) if out else {"verdict": "fail", "summary": "backup produced no stdout"}
    except json.JSONDecodeError as exc:
        return {"verdict": "fail", "summary": f"backup stdout not JSON: {exc}; raw={out[:200]}"}


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

    pre_backup_result = _run_pre_deploy_backup_if_enabled(config, project, project_root, dry_run)
    if pre_backup_result is not None and pre_backup_result.get("verdict") not in {"pass", "dry-run", "skip"}:
        return {
            "verdict": "ceiling",
            "exit_code": EXIT_CEILING,
            "mode": detection["mode"],
            "head_sha": _git_head_short(str(project_root)),
            "duration_ms": int((time.monotonic() - started) * 1000),
            "summary": (
                f"pre-deploy backup gate FAILED (verdict={pre_backup_result.get('verdict')}): "
                f"{pre_backup_result.get('summary', '')}. Deploy refused.\n  -> "
                f"{_rollback_suggestion(project)}"
            ),
            "doctrine_cite": None,
            "pre_deploy_backup": pre_backup_result,
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
        verdict = runner_result["verdict"]
        receipt_path = (
            _write_receipt(
                project_root, project, env, detection, runner_result,
                None, head_sha, duration_ms, overall_verdict=verdict,
            )
            if not dry_run
            else None
        )
        exit_code = EXIT_CEILING if verdict == "ceiling" else EXIT_FAIL
        summary = (
            f"{runner_result.get('summary', '')}\n  -> {_rollback_suggestion(project)}"
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
            "pre_deploy_backup": pre_backup_result,
        }

    hc_result = run_healthcheck(healthcheck_spec)
    head_sha = _git_head_short(str(project_root))
    duration_ms = int((time.monotonic() - started) * 1000)
    overall_verdict_for_receipt = "pass" if hc_result.get("ok") else "deploy-warn"
    receipt_path = _write_receipt(
        project_root, project, env, detection, runner_result, hc_result,
        head_sha, duration_ms, overall_verdict=overall_verdict_for_receipt,
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
            f"attempts -- target may not be live. Report: {receipt_path}\n  -> "
            f"{_rollback_suggestion(project)}"
        )

    # OSA post-deploy hook -- non-blocking, swallow-all-errors (sealed 2026-05-28).
    try:
        from modules.osa.dispatcher import fire_async as _osa_fire
        _osa_fire(project=project, kind="post-deploy")
    except Exception:
        pass

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
        "pre_deploy_backup": pre_backup_result,
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
