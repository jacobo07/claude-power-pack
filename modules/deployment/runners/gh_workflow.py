"""gh-workflow runner -- invokes an existing GitHub Actions workflow.

Reality contract: this runner INVOKES the canonical pipeline; it
does NOT replace it. When the workflow file path matches the §77
Deploy Sovereignty pattern (`deploy-vps.yml`), the runner emits a
doctrine citation in stdout AND in the returned dict.

Hard invariant: this module never pushes to the canonical origin
remote. It uses the gh CLI to trigger workflows -- that is a
GitHub API call, not a push.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any


SECTION_77_PATTERN = "deploy-vps.yml"

SECTION_77_CITE = (
    "§77 Deploy Sovereignty -- the workflow at {wf} is the canonical CD pipeline. "
    "This runner INVOKES it via the gh API; it does not replace it."
)


def _gh_available() -> bool:
    return shutil.which("gh") is not None


def _last_lines(text: str, n: int = 15) -> str:
    lines = (text or "").splitlines()
    return "\n".join(lines[-n:])


def run_gh_workflow(
    config: dict[str, Any],
    dry_run: bool = False,
) -> dict[str, Any]:
    """Invoke a workflow via gh CLI. Returns receipt dict.

    config keys consumed:
      workflow_file : path to .github/workflows/*.yml (required)
      ref           : git ref to run against (default 'main')
      project_root  : repo root (required, for cwd)
    """
    workflow_file = config.get("workflow_file")
    project_root = config.get("project_root")
    ref = config.get("ref", "main")

    if not workflow_file or not project_root:
        return {
            "ok": False,
            "verdict": "fail",
            "summary": "gh-workflow runner missing workflow_file or project_root",
            "doctrine_cite": None,
            "receipt": "",
        }

    wf_path = Path(workflow_file)
    wf_name = wf_path.name
    doctrine_cite: str | None = None
    if SECTION_77_PATTERN in wf_name.lower():
        doctrine_cite = SECTION_77_CITE.format(wf=str(wf_path))
        print(doctrine_cite)

    if dry_run:
        plan_lines = [
            f"DRY RUN -- would invoke: gh workflow run {wf_name} --ref {ref}",
            f"DRY RUN -- then: gh run watch --exit-status (poll until terminal state)",
            f"DRY RUN -- workflow file: {wf_path}",
            f"DRY RUN -- doctrine: {doctrine_cite or 'none'}",
        ]
        return {
            "ok": True,
            "verdict": "dry-run",
            "summary": f"gh-workflow dry-run for {wf_name}",
            "doctrine_cite": doctrine_cite,
            "receipt": "\n".join(plan_lines),
        }

    if not _gh_available():
        return {
            "ok": False,
            "verdict": "ceiling",
            "summary": "gh CLI not found on PATH; cannot invoke workflow",
            "doctrine_cite": doctrine_cite,
            "receipt": "gh: command not found",
        }

    try:
        invoke = subprocess.run(
            ["gh", "workflow", "run", wf_name, "--ref", ref],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "verdict": "fail",
            "summary": "gh workflow run timed out",
            "doctrine_cite": doctrine_cite,
            "receipt": f"TimeoutExpired: {exc}",
        }

    invoke_output = (invoke.stdout or "") + (invoke.stderr or "")
    if invoke.returncode != 0:
        return {
            "ok": False,
            "verdict": "fail",
            "summary": f"gh workflow run failed (exit {invoke.returncode})",
            "doctrine_cite": doctrine_cite,
            "receipt": _last_lines(invoke_output, 15),
        }

    try:
        watch = subprocess.run(
            ["gh", "run", "watch", "--exit-status"],
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
            "summary": "gh run watch timed out (>30 min)",
            "doctrine_cite": doctrine_cite,
            "receipt": f"TimeoutExpired: {exc}",
        }

    watch_output = (watch.stdout or "") + (watch.stderr or "")
    combined = f"INVOKE OUTPUT:\n{invoke_output}\n\nWATCH OUTPUT (last 15):\n{_last_lines(watch_output, 15)}"

    if watch.returncode == 0:
        return {
            "ok": True,
            "verdict": "pass",
            "summary": f"gh-workflow {wf_name} run completed successfully",
            "doctrine_cite": doctrine_cite,
            "receipt": combined,
        }
    return {
        "ok": False,
        "verdict": "fail",
        "summary": f"gh-workflow {wf_name} run failed (exit {watch.returncode})",
        "doctrine_cite": doctrine_cite,
        "receipt": combined,
    }
