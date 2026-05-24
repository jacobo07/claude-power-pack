"""Deploy-mode detector.

Returns the FIRST matching mode per the spec's ordered probe:
  1. gh-workflow      -- .github/workflows/deploy*.yml present
  2. git-push-to-deploy -- deploy/post-receive OR non-origin remote configured
  3. manual-scp       -- build manifest + vault/deploy/<project>.json with mode=scp-systemd
  4. none             -- documented ceiling

The detector is pure I/O against the filesystem; it never invokes
network calls and never reads credentials.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


GH_WORKFLOW_NAME_RE = re.compile(r"^deploy.*\.ya?ml$", re.IGNORECASE)

GH_TRIGGER_TOKENS = ("workflow_dispatch", "push:")

NON_ORIGIN_REMOTE_RE = re.compile(
    r"^[a-z][a-z0-9_-]*@[^:/]+:[^/].*\.git$",
    re.IGNORECASE,
)


def _looks_like_gh_deploy_workflow(yml_path: Path) -> bool:
    """A workflow file under .github/workflows/ is a deploy candidate
    when its name starts with 'deploy' AND its body contains either a
    workflow_dispatch trigger or a push trigger. This is intentionally
    forgiving -- the detector errs on the side of detecting; the
    runner is responsible for failing loudly if the workflow is not
    actually runnable.
    """
    try:
        body = yml_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    if not GH_WORKFLOW_NAME_RE.match(yml_path.name):
        return False
    return any(token in body for token in GH_TRIGGER_TOKENS)


def _find_gh_deploy_workflow(project_root: Path) -> Path | None:
    wf_dir = project_root / ".github" / "workflows"
    if not wf_dir.is_dir():
        return None
    for entry in sorted(wf_dir.iterdir()):
        if entry.is_file() and _looks_like_gh_deploy_workflow(entry):
            return entry
    return None


def _has_post_receive_hook(project_root: Path) -> Path | None:
    candidate = project_root / "deploy" / "post-receive"
    return candidate if candidate.is_file() else None


def _has_non_origin_git_remote(project_root: Path) -> str | None:
    """Return the first non-origin remote URL that looks like a deploy
    target (user@host:/path/repo.git), or None.
    """
    if not (project_root / ".git").exists():
        return None
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), "remote", "-v"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        name, url = parts[0], parts[1]
        if name == "origin":
            continue
        if "github.com" in url.lower():
            continue
        if NON_ORIGIN_REMOTE_RE.match(url):
            return f"{name} {url}"
    return None


def _find_scp_config(project_root: Path) -> Path | None:
    """Look for vault/deploy/*.json files declaring mode=scp-systemd.
    Returns the first matching config path.
    """
    deploy_dir = project_root / "vault" / "deploy"
    if not deploy_dir.is_dir():
        return None
    for entry in sorted(deploy_dir.iterdir()):
        if entry.suffix.lower() != ".json":
            continue
        try:
            data = json.loads(entry.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and data.get("mode") == "scp-systemd":
            return entry
    return None


def _has_build_manifest(project_root: Path) -> str | None:
    """Returns the name of the first build manifest found, or None."""
    candidates = (
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "mix.exs",
        "package.json",
        "Cargo.toml",
        "pyproject.toml",
    )
    for name in candidates:
        if (project_root / name).is_file():
            return name
    return None


def detect_deploy_target(project_root: Path) -> dict[str, Any]:
    """Detect the deploy mode of a project. Pure function; no side
    effects beyond filesystem reads.

    Returns a dict with keys:
      mode:      one of gh-workflow | git-push-to-deploy | manual-scp | none
      evidence:  human-readable string identifying the signal
      config_path: path to the matching vault/deploy/*.json (manual-scp only) or None
      workflow_file: path to the matched gh workflow (gh-workflow only) or None
      remote:    remote name+url (git-push-to-deploy only) or None
    """
    project_root = Path(project_root).resolve()

    workflow = _find_gh_deploy_workflow(project_root)
    if workflow is not None:
        return {
            "mode": "gh-workflow",
            "evidence": f"workflow file: {workflow.relative_to(project_root)}",
            "config_path": None,
            "workflow_file": str(workflow),
            "remote": None,
        }

    post_receive = _has_post_receive_hook(project_root)
    if post_receive is not None:
        return {
            "mode": "git-push-to-deploy",
            "evidence": f"post-receive hook: {post_receive.relative_to(project_root)}",
            "config_path": None,
            "workflow_file": None,
            "remote": None,
        }
    remote = _has_non_origin_git_remote(project_root)
    if remote is not None:
        return {
            "mode": "git-push-to-deploy",
            "evidence": f"non-origin remote: {remote}",
            "config_path": None,
            "workflow_file": None,
            "remote": remote,
        }

    scp_config = _find_scp_config(project_root)
    if scp_config is not None and _has_build_manifest(project_root) is not None:
        return {
            "mode": "manual-scp",
            "evidence": (
                f"manifest: {_has_build_manifest(project_root)}; "
                f"config: {scp_config.relative_to(project_root)}"
            ),
            "config_path": str(scp_config),
            "workflow_file": None,
            "remote": None,
        }

    return {
        "mode": "none",
        "evidence": "no deploy signal detected (no workflow, no post-receive, no non-origin remote, no scp-systemd config)",
        "config_path": None,
        "workflow_file": None,
        "remote": None,
    }


if __name__ == "__main__":
    import sys

    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    print(json.dumps(detect_deploy_target(target), indent=2))
