#!/usr/bin/env python3
"""Spec Gate -- PP BL-SPEC-GATE-001.

For L/XL tasks: verify a spec exists in the current repo BEFORE the agent
starts coding. Prevents CLASE 1 (API assumptions) and CLASE 2 (false
premises) by forcing the agent to read/write the spec first.

Advisory by contract: it reports gate_passed + a recommended action; it
does NOT hard-block (the JIT/agent layer decides how to act). S/M tasks
are exempt -- the auto-injected One-Shot contract is sufficient there.

Cross-repo: takes the active project cwd; uses no hardcoded paths.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# Spec locations honored, in priority order. Aligned with the JIT
# loader's _active_spec() (.specify + vault/specs) plus common roots.
SPEC_GLOBS = (
    ".specify/specs/*/spec.md",
    "vault/specs/*.md",
    "vault/plans/*.md",
    "*.prd.md",
    "spec.md", "SPEC.md", "PRD.md", "requirements.md",
    "docs/spec.md", "docs/PRD.md", "docs/requirements.md",
)

_LXL = {"L", "XL"}


@dataclass
class SpecGateResult:
    has_spec: bool
    spec_path: str | None
    gate_passed: bool
    action: str       # "proceed" | "read_spec" | "create_spec"
    message: str


def _find_spec(cwd: Path) -> Path | None:
    candidates: list[Path] = []
    for pattern in SPEC_GLOBS:
        try:
            candidates.extend(p for p in cwd.glob(pattern) if p.is_file())
        except (OSError, ValueError):
            continue
    if not candidates:
        return None
    try:
        return max(candidates, key=lambda p: p.stat().st_mtime)
    except OSError:
        return candidates[0]


def check_spec_gate(task_description: str,
                    cwd: Path | str | None = None,
                    task_size: str = "M") -> SpecGateResult:
    """Check whether an L/XL task has a spec. S/M -> always proceed."""
    if task_size not in _LXL:
        return SpecGateResult(
            has_spec=True, spec_path=None, gate_passed=True,
            action="proceed",
            message=f"{task_size} task -- spec gate not required.")

    root = Path(cwd) if cwd else Path.cwd()
    spec = _find_spec(root)
    if spec is not None:
        try:
            shown = spec.relative_to(root)
        except ValueError:
            shown = spec
        return SpecGateResult(
            has_spec=True, spec_path=str(spec), gate_passed=True,
            action="read_spec",
            message=(f"Spec found: {shown}. Read it before coding -- the "
                     "plan's scope and done-gate live there."))

    return SpecGateResult(
        has_spec=False, spec_path=None, gate_passed=False,
        action="create_spec",
        message=(
            "No spec found for this L/XL task. Before coding, establish one:\n"
            "  A) the One-Shot contract auto-injected by the JIT loader on "
            "L/XL prompts (scope + done-gate + budget), or\n"
            "  B) python modules/karimo-harness/prd_parser.py <prd> for a "
            "full PRD -> deterministic task list.\n"
            "Spec gate prevents CLASE 1 (API assumptions) + CLASE 2 "
            "(false premises)."))
