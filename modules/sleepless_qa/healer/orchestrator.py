"""
Healer orchestrator — the main loop.

    run(repo, runtime_class, action_script)
      -> acquire_lock
      -> launch dumper
      -> trigger action
      -> capture evidence
      -> verdict
        -> PASS       : log, release, return
        -> UNCERTAIN  : notify desktop, log, release, return
        -> FAIL       :
            if retry_budget exhausted       : log FAIL_BUDGET_EXHAUSTED, return
            elif pattern_cache hit          : log hint, re-verify
            else                            : dispatcher_bridge.heal() + re-verify
            if two consecutive fixes == same diff : abort FIX_LOOP_STUCK

This is the main wiring site the CLI will call.
"""

from __future__ import annotations

import logging
import os
import subprocess
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..dumpers import autodetect, get_dumper
from ..dumpers.base import ActionScript, DumperError, EvidenceBundle
from ..verdict import judge
from ..verdict.schema import Verdict, VerdictStatus
from . import dispatcher_bridge, pattern_cache, run_log
from .lock import repo_lock

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorResult:
    run_id: str
    final_verdict: Verdict
    attempts: int
    repo_path: Path
    action_name: str
    terminated_because: str = ""
    heal_commits: list[str] = field(default_factory=list)


def _notify_desktop(title: str, body: str) -> None:
    """Best-effort desktop notification across Windows/Linux/macOS."""
    try:
        if os.name == "nt":
            # PowerShell burnttoast or fallback to print
            subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    f"[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null; "
                    f"[System.Windows.Forms.MessageBox]::Show('{body}','{title}') | Out-Null",
                ],
                timeout=5,
                check=False,
            )
            return
        if os.uname().sysname == "Darwin":  # type: ignore[attr-defined]
            subprocess.run(
                ["osascript", "-e", f'display notification "{body}" with title "{title}"'],
                timeout=5,
                check=False,
            )
            return
        subprocess.run(["notify-send", title, body], timeout=5, check=False)
    except Exception:
        logger.info("desktop notification unavailable; body=%s", body)


def _git_head(repo_path: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        logger.exception("git head query failed")
    return None


def _git_dirty(repo_path: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return bool(result.stdout.strip())
    except Exception:
        return True


def _git_diff_since(repo_path: Path, since_sha: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "diff", since_sha, "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return result.stdout
    except Exception:
        return ""


def run(
    repo_path: Path,
    action: ActionScript,
    config: dict[str, Any],
    runtime_class: str | None = None,
    max_retry_budget: int = 3,
) -> OrchestratorResult:
    """Execute the full QA + heal loop for a single action script."""
    repo_path = Path(repo_path).resolve()
    if not repo_path.exists():
        raise ValueError(f"Repo path does not exist: {repo_path}")

    run_id = str(uuid.uuid4())
    run_log.append_event(run_id, {"event": "run_start", "repo": str(repo_path)})

    if runtime_class is None or runtime_class == "auto":
        runtime_class = autodetect(repo_path)
        run_log.append_event(run_id, {"event": "autodetect", "runtime_class": runtime_class})

    dumper_cls = get_dumper(runtime_class)
    dumper_config = (config.get("dumpers") or {}).get(runtime_class, {})
    dumper_config.setdefault(
        "subprocess_timeout_seconds",
        config.get("subprocess_timeout_seconds", 600),
    )

    uncertain_threshold = float(
        config.get("uncertain_confidence_threshold", 0.7)
    )

    require_clean = bool(
        (config.get("healer") or {}).get("require_clean_git_status", True)
    )

    previous_diffs: list[str] = []
    attempts = 0
    terminated = ""
    last_verdict: Verdict | None = None
    heal_commits: list[str] = []

    try:
        with repo_lock(repo_path):
            while attempts < max_retry_budget:
                attempts += 1
                run_log.append_event(run_id, {"event": "attempt_start", "n": attempts})

                dumper = dumper_cls(repo_path=repo_path, config=dumper_config, run_id=run_id)
                try:
                    with dumper:
                        dumper.trigger(action)
                        bundle: EvidenceBundle = dumper.capture()
                except DumperError as exc:
                    logger.error("Dumper failed on attempt %d: %s", attempts, exc)
                    last_verdict = Verdict(
                        status=VerdictStatus.UNCERTAIN,
                        confidence=0.0,
                        reason=f"Dumper error: {exc}",
                        strategy="aggregate",
                        evidence_refs=[],
                        priority_level=1,
                    )
                    run_log.append_event(run_id, {"event": "dumper_error", "reason": str(exc)})
                    terminated = "dumper_error"
                    break

                verdict = judge(bundle, action, uncertain_threshold=uncertain_threshold)
                last_verdict = verdict
                run_log.append_event(
                    run_id,
                    {
                        "event": "verdict",
                        "attempt": attempts,
                        "status": verdict.status.value,
                        "confidence": verdict.confidence,
                        "reason": verdict.reason,
                        "cost_usd": verdict.api_cost_estimate_usd,
                    },
                )

                if verdict.status == VerdictStatus.PASS:
                    terminated = "pass"
                    break

                if verdict.status == VerdictStatus.UNCERTAIN:
                    _notify_desktop(
                        "Sleepless QA — UNCERTAIN",
                        f"{action.name}: {verdict.reason[:140]}",
                    )
                    terminated = "uncertain"
                    break

                # FAIL path
                if require_clean and _git_dirty(repo_path):
                    run_log.append_event(
                        run_id,
                        {"event": "dirty_worktree_abort"},
                    )
                    terminated = "dirty_worktree"
                    break

                if attempts >= max_retry_budget:
                    terminated = "budget_exhausted"
                    break

                # Pattern cache hint (passed to dispatcher in prompt)
                cached = pattern_cache.match(verdict.reason)
                if cached:
                    run_log.append_event(
                        run_id,
                        {"event": "pattern_cache_hit", "name": cached.name},
                    )

                # Git HEAD snapshot for diff comparison
                head_before = _git_head(repo_path)
                run_log.append_event(
                    run_id,
                    {"event": "heal_dispatch", "attempt": attempts, "head_before": head_before},
                )
                code, out, err = dispatcher_bridge.dispatch_heal(
                    repo_path=repo_path,
                    verdict=verdict,
                    bundle=bundle,
                    action=action,
                    attempt=attempts,
                    timeout_seconds=int(config.get("subprocess_timeout_seconds", 600)),
                )
                run_log.append_event(
                    run_id,
                    {"event": "heal_result", "exit_code": code, "stdout_tail": out[-500:]},
                )

                if code != 0:
                    terminated = f"dispatcher_exit_{code}"
                    break

                head_after = _git_head(repo_path)
                if head_after and head_after != head_before:
                    heal_commits.append(head_after)
                    diff = _git_diff_since(repo_path, head_before or "")
                    if any(diff == prev for prev in previous_diffs):
                        run_log.append_event(run_id, {"event": "fix_loop_stuck"})
                        terminated = "fix_loop_stuck"
                        break
                    previous_diffs.append(diff)
                else:
                    run_log.append_event(run_id, {"event": "no_commit_made"})

            # End while
    except Exception as exc:
        logger.exception("Orchestrator crashed")
        last_verdict = last_verdict or Verdict(
            status=VerdictStatus.UNCERTAIN,
            confidence=0.0,
            reason=f"Orchestrator crash: {exc}",
            strategy="aggregate",
            evidence_refs=[],
            priority_level=1,
        )
        terminated = terminated or "orchestrator_crash"

    # Final bookkeeping
    if last_verdict is None:
        last_verdict = Verdict(
            status=VerdictStatus.UNCERTAIN,
            confidence=0.0,
            reason="No verdict produced",
            strategy="aggregate",
            evidence_refs=[],
            priority_level=1,
        )

    run_log.write_verdict_json(
        run_id,
        {
            "run_id": run_id,
            "repo_path": str(repo_path),
            "action_name": action.name,
            "runtime_class": runtime_class,
            "attempts": attempts,
            "terminated_because": terminated,
            "heal_commits": heal_commits,
            "verdict": last_verdict.model_dump(),
        },
    )
    run_log.append_event(
        run_id,
        {"event": "run_end", "terminated_because": terminated, "attempts": attempts},
    )

    if terminated == "pass" and heal_commits:
        run_log.log_correction(
            f"sleepless-qa healed {action.name} in {repo_path.name} "
            f"after {attempts} attempts. Final verdict: PASS. "
            f"Commits: {', '.join(heal_commits)}"
        )

    return OrchestratorResult(
        run_id=run_id,
        final_verdict=last_verdict,
        attempts=attempts,
        repo_path=repo_path,
        action_name=action.name,
        terminated_because=terminated,
        heal_commits=heal_commits,
    )
