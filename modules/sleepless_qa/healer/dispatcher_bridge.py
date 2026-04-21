"""
Dispatcher bridge — wraps modules/dispatcher/dispatch.py to fire a healing
prompt at the target repo with verdict + evidence attached.

Builds a self-contained prompt file containing:
  - The verdict's failure reason
  - Paths to captured evidence (screenshots, logs)
  - The action script that failed
  - Relevant mistakes-registry excerpts

Then shells out to the dispatcher CLI which in turn runs `claude -p <prompt>`
inside the target repo so that repo's CLAUDE.md context loads.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from ..dumpers.base import ActionScript, EvidenceBundle
from ..verdict.schema import Verdict

logger = logging.getLogger(__name__)

DISPATCHER_DEFAULT = Path(
    "~/.claude/skills/claude-power-pack/modules/dispatcher/dispatch.py"
).expanduser()


def _build_prompt(
    repo_path: Path,
    verdict: Verdict,
    bundle: EvidenceBundle,
    action: ActionScript,
    attempt: int,
) -> str:
    lines: list[str] = []
    lines.append("# Sleepless QA — Auto-Heal Request")
    lines.append("")
    lines.append(f"**Target repo:** `{repo_path}`")
    lines.append(f"**Attempt:** {attempt}")
    lines.append(f"**Run ID:** {bundle.run_id}")
    lines.append(f"**Runtime class:** {bundle.runtime_class}")
    lines.append(f"**Action script:** {action.name}")
    lines.append("")
    lines.append("## Verdict")
    lines.append(f"- **Status:** {verdict.status.value}")
    lines.append(f"- **Confidence:** {verdict.confidence:.2f}")
    lines.append(f"- **Priority:** L{verdict.priority_level}")
    lines.append(f"- **Strategy:** {verdict.strategy}")
    lines.append(f"- **Reason:** {verdict.reason}")
    lines.append("")
    lines.append("## Captured Evidence")
    if bundle.screenshots:
        lines.append("### Screenshots")
        for s in bundle.screenshots:
            lines.append(f"- `{s}`")
    if bundle.http_responses:
        lines.append("### HTTP Responses")
        for r in bundle.http_responses[:10]:
            lines.append(f"- `{r.method} {r.url}` → {r.status} ({r.duration_ms}ms)")
    if bundle.log_excerpts:
        lines.append("### Log excerpts (truncated to 2KB each)")
        for key, text in bundle.log_excerpts.items():
            if isinstance(text, str):
                lines.append(f"#### {key}")
                lines.append("```")
                lines.append(text[-2048:])
                lines.append("```")
    lines.append("")
    lines.append("## Action script that failed")
    lines.append("```json")
    lines.append(action.model_dump_json(indent=2))
    lines.append("```")
    lines.append("")
    lines.append("## Heal request")
    lines.append(
        "Diagnose the failure above and apply a MINIMAL fix to the target repo. "
        "Follow the repo's own CLAUDE.md rules. After the fix, commit with a "
        "message starting with `[sqa-heal]` so sleepless-qa can detect the heal "
        "attempt. Do NOT push. Do NOT run destructive git commands. Priority "
        f"level is L{verdict.priority_level} (1=stability, 2=functionality, "
        "3=aesthetics, 4=polish) — do not work below this level until L{N} is "
        "clean."
    )
    return "\n".join(lines)


def dispatch_heal(
    repo_path: Path,
    verdict: Verdict,
    bundle: EvidenceBundle,
    action: ActionScript,
    attempt: int,
    timeout_seconds: int = 600,
) -> tuple[int, str, str]:
    """
    Fire a heal request. Returns (exit_code, stdout_tail, stderr_tail).

    Uses the dispatcher CLI by subprocess. We do NOT import dispatcher as a
    module because it owns its own argparse and logging setup.
    """
    if not DISPATCHER_DEFAULT.exists():
        return (
            2,
            "",
            f"dispatcher not found at {DISPATCHER_DEFAULT} — heal skipped",
        )

    prompt_text = _build_prompt(repo_path, verdict, bundle, action, attempt)
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".md",
        prefix=f"sqa-heal-{bundle.run_id}-",
        delete=False,
        encoding="utf-8",
    ) as tf:
        tf.write(prompt_text)
        prompt_path = Path(tf.name)

    repo_name = repo_path.name
    cmd = [
        sys.executable,
        str(DISPATCHER_DEFAULT),
        repo_name,
        str(prompt_path),
        "--repo-path",
        str(repo_path),
    ]
    logger.info("Dispatching heal: %s", cmd)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return (124, "", f"dispatcher timeout after {timeout_seconds}s: {exc}")
    except Exception as exc:
        logger.exception("dispatcher invocation failed")
        return (1, "", f"dispatcher exception: {exc}")

    return (
        result.returncode,
        (result.stdout or "")[-8_000:],
        (result.stderr or "")[-8_000:],
    )
