"""Cascade detection -- per-surface detectors; never raises."""
from __future__ import annotations

from typing import Callable

from .types import CascadeHit, CascadeSeverity, CascadeType

# Thresholds (OD2-derived; tune via config later if measurement disagrees).
CONTEXT_WARN_PCT = 85
CONTEXT_BLOCK_PCT = 95
# Ratio of touched-files / planned-files at which scope is considered
# to be creeping (3 touched on a 2-file plan = 1.5x).
SCOPE_CREEP_FILE_RATIO = 1.5

# Caller-populated allowlist of paths that should NOT be edited (e.g.
# .git/HEAD, vault/secrets/*, ~/.claude/settings.json). Empty by default;
# the caller injects project-specific guardrails.
LOCKED_PATHS: set[str] = set()


def _detect_deploy(ctx: dict) -> list[CascadeHit]:
    hits: list[CascadeHit] = []
    if not ctx.get("is_deploy"):
        return hits
    if not ctx.get("tests_passed", False):
        hits.append(CascadeHit(
            cascade_type=CascadeType.DEPLOY_WITHOUT_TEST,
            severity=CascadeSeverity.C4,
            surface="deploy",
            reason="deploy initiated with tests_passed=False",
        ))
    if not ctx.get("rollback_plan"):
        hits.append(CascadeHit(
            cascade_type=CascadeType.MISSING_ROLLBACK,
            severity=CascadeSeverity.C3,
            surface="deploy",
            reason="deploy without explicit rollback plan",
        ))
    return hits


def _detect_edit(ctx: dict) -> list[CascadeHit]:
    hits: list[CascadeHit] = []
    path = ctx.get("file_path")
    if path and path in LOCKED_PATHS:
        hits.append(CascadeHit(
            cascade_type=CascadeType.EDIT_LOCKED_FILE,
            severity=CascadeSeverity.C4,
            surface="edit",
            reason=f"edit on locked path {path}",
        ))
    return hits


def _detect_commit(ctx: dict) -> list[CascadeHit]:
    hits: list[CascadeHit] = []
    if ctx.get("is_commit") and not ctx.get("verified", True):
        hits.append(CascadeHit(
            cascade_type=CascadeType.COMMIT_WITHOUT_VERIFY,
            severity=CascadeSeverity.C3,
            surface="commit",
            reason="commit without verification step (lint/test)",
        ))
    return hits


def _detect_context(ctx: dict) -> list[CascadeHit]:
    hits: list[CascadeHit] = []
    pct = ctx.get("context_pct", 0)
    if pct >= CONTEXT_BLOCK_PCT:
        hits.append(CascadeHit(
            cascade_type=CascadeType.CONTEXT_OVERFLOW,
            severity=CascadeSeverity.C4,
            surface="context",
            reason=f"context at {pct}% (>= {CONTEXT_BLOCK_PCT}%); block",
        ))
    elif pct >= CONTEXT_WARN_PCT:
        hits.append(CascadeHit(
            cascade_type=CascadeType.CONTEXT_OVERFLOW,
            severity=CascadeSeverity.C3,
            surface="context",
            reason=f"context at {pct}% (>= {CONTEXT_WARN_PCT}%); warn",
        ))
    return hits


def _detect_task(ctx: dict) -> list[CascadeHit]:
    hits: list[CascadeHit] = []
    touched = ctx.get("files_touched", 0)
    planned = ctx.get("files_planned", 0)
    if planned > 0 and touched > planned * SCOPE_CREEP_FILE_RATIO:
        hits.append(CascadeHit(
            cascade_type=CascadeType.SCOPE_CREEP,
            severity=CascadeSeverity.C3,
            surface="task",
            reason=(
                f"touched {touched} files vs planned {planned} "
                f"(ratio > {SCOPE_CREEP_FILE_RATIO})"
            ),
        ))
    return hits


def _detect_bash(ctx: dict) -> list[CascadeHit]:
    hits: list[CascadeHit] = []
    cmd = (ctx.get("command") or "").strip()
    if cmd.startswith("rm -rf") and not ctx.get("has_backup"):
        hits.append(CascadeHit(
            cascade_type=CascadeType.DELETE_WITHOUT_BACKUP,
            severity=CascadeSeverity.C4,
            surface="bash",
            reason="rm -rf without explicit backup",
        ))
    return hits


def _detect_session(ctx: dict) -> list[CascadeHit]:
    return []


SURFACE_DETECTORS: dict[str, Callable[[dict], list[CascadeHit]]] = {
    "bash": _detect_bash,
    "edit": _detect_edit,
    "deploy": _detect_deploy,
    "commit": _detect_commit,
    "context": _detect_context,
    "task": _detect_task,
    "session": _detect_session,
}


def detect(surface: str, ctx: dict | None = None) -> list[CascadeHit]:
    """Run the surface-specific detector against ctx; never raises."""
    detector = SURFACE_DETECTORS.get(surface)
    if detector is None:
        return []
    try:
        return detector(ctx or {})
    except Exception:
        # Engine MUST be silent under input shape errors -- fail-open.
        return []
