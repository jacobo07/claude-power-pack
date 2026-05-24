"""git-push-to-deploy runner.

Pushes to a server-side bare repo whose `post-receive` hook
triggers the deploy. The TUA-X model: `git push vps204 main`
checks out into a working tree and runs `docker compose up -d --build`.

Hard invariant: refuses to push to the canonical origin remote.
The deploy remote must be a DIFFERENT remote (e.g. `vps204`,
`prod`, `deploy`) configured in `.git/config`. The Owner is
responsible for pushing to the canonical remote separately.

Receipt: captures the stderr from the push (which is where the
post-receive hook prints its output) and returns the last 15 lines.
"""

from __future__ import annotations

import subprocess
from typing import Any


FORBIDDEN_REMOTE_NAMES = frozenset({"origin", "upstream", "github"})

FORBIDDEN_REMOTE_HOST_TOKENS = ("github.com", "gitlab.com", "bitbucket.org")


def _is_forbidden_remote(remote_name: str, remote_url: str) -> tuple[bool, str]:
    if remote_name.lower() in FORBIDDEN_REMOTE_NAMES:
        return True, f"remote name '{remote_name}' is in FORBIDDEN_REMOTE_NAMES"
    lower_url = (remote_url or "").lower()
    for tok in FORBIDDEN_REMOTE_HOST_TOKENS:
        if tok in lower_url:
            return True, f"remote URL contains forbidden host token '{tok}'"
    return False, ""


def _last_lines(text: str, n: int = 15) -> str:
    lines = (text or "").splitlines()
    return "\n".join(lines[-n:])


def _resolve_remote_url(project_root: str, remote_name: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", project_root, "remote", "get-url", remote_name],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""
    return (result.stdout or "").strip()


def run_git_push(
    config: dict[str, Any],
    dry_run: bool = False,
) -> dict[str, Any]:
    """config keys consumed:
      remote       : remote NAME (e.g. 'vps204'); URL is resolved by git
      branch       : branch to push (default 'main')
      project_root : repo root (required)
    """
    remote_name = (config.get("remote_name") or config.get("remote") or "").strip()
    branch = (config.get("branch") or "main").strip()
    project_root = config.get("project_root")

    if not remote_name or not project_root:
        return {
            "ok": False,
            "verdict": "fail",
            "summary": "git-push runner missing remote or project_root",
            "doctrine_cite": None,
            "receipt": "",
        }

    remote_url = _resolve_remote_url(project_root, remote_name)
    if not remote_url:
        return {
            "ok": False,
            "verdict": "ceiling",
            "summary": f"remote '{remote_name}' not configured in this repo",
            "doctrine_cite": None,
            "receipt": f"git remote get-url {remote_name} -- returned empty",
        }

    forbidden, why = _is_forbidden_remote(remote_name, remote_url)
    if forbidden:
        return {
            "ok": False,
            "verdict": "fail",
            "summary": f"refusing to push: {why}",
            "doctrine_cite": (
                "Deploy Skill invariant: this runner is for non-canonical "
                "deploy remotes only. Canonical origin remotes are off-limits "
                "for this runner. The Owner pushes to origin separately."
            ),
            "receipt": f"remote_name='{remote_name}' remote_url='{remote_url}'",
        }

    if dry_run:
        return {
            "ok": True,
            "verdict": "dry-run",
            "summary": f"git-push dry-run to {remote_name} ({remote_url}) branch {branch}",
            "doctrine_cite": None,
            "receipt": (
                f"DRY RUN -- would invoke: git push {remote_name} {branch}\n"
                f"DRY RUN -- expected receipt: server-side post-receive hook output"
            ),
        }

    try:
        push_cmd = ["git", "-C", project_root, "push", remote_name, branch]
        push = subprocess.run(
            push_cmd,
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "verdict": "fail",
            "summary": "git push timed out (>10 min)",
            "doctrine_cite": None,
            "receipt": f"TimeoutExpired: {exc}",
        }

    receipt = (push.stderr or "") + "\n--- stdout ---\n" + (push.stdout or "")
    receipt_last = _last_lines(receipt, 30)

    if push.returncode != 0:
        return {
            "ok": False,
            "verdict": "fail",
            "summary": f"git push {remote_name} {branch} failed (exit {push.returncode})",
            "doctrine_cite": None,
            "receipt": receipt_last,
        }
    return {
        "ok": True,
        "verdict": "pass",
        "summary": f"git push {remote_name} {branch} succeeded; receipt is server post-receive output",
        "doctrine_cite": None,
        "receipt": receipt_last,
    }
