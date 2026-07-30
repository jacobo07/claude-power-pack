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

import re
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


# --- Tier classification (SDD-OS, Sprint 2 / M5) ------------------------
# The SDD-OS dataset (Dataset SDD-OS 1.txt, PARTE I sec. 3-4) defines FOUR
# task tiers, not five -- Tier 3 ("Strategic / Platform Task") already
# absorbs new-OS / framework / cross-repo work. This classifier maps a
# free-text task description to a tier via keyword signals mirroring the
# dataset's per-tier examples + the PRD-trigger keyword list.
#
# Tier <-> spec-gate size: 0->S, 1->M, 2->L, 3->XL. Tier >= 2 requires a
# PRD before execution ("ejecutar sin PRD queda prohibido", sec. 4).

TIER_TO_SIZE: dict[int, str] = {0: "S", 1: "M", 2: "L", 3: "XL"}

# Keywords that FORCE a PRD (>= Tier 2): dataset PARTE I, section 4.
_PRD_TRIGGER: tuple[str, ...] = (
    "system", "sistema", "os", "framework", "pipeline", "universal",
    "cross-repo", "every repo", "all repos", "platform", "plataforma",
    "scalable", "escalable", "robust", "robusto", "provisioning",
    "spec-driven", "standard", "estandar",
)
# Tier 3 -- Strategic / Platform (fundacional, multi-module, becomes a
# reusable standard).
_TIER3: tuple[str, ...] = (
    "redesign", "re-architect", "rearchitect", "overhaul", "new os",
    "internal os", "global standard", "agent system",
    "universal framework", "security layer", "execution mode",
    "spec-driven development", "ground-up", "platform", "strategic",
)
# Tier 2 -- Feature / System (new capability or architecture/data/UX/
# security/workflow/integration impact).
_TIER2: tuple[str, ...] = (
    "feature", "agent", "workflow", "module", "endpoint", "integration",
    "integrate", "api", "persistence", "database", "schema",
    "observability", "monitoring", "plugin", "automation", "automate",
    "auth", "authentication", "authorization", "billing", "payment",
    "migration",
)
# Tier 1 -- Standard (moderate functional change, limited impact).
_TIER1: tuple[str, ...] = (
    "improve", "enhance", "modify", "add option", "add command",
    "fix bug", "bugfix", "tweak", "adjust", "extend",
)
# Tier 0 -- Micro (trivial, localized, reversible, no systemic impact).
_TIER0: tuple[str, ...] = (
    "typo", "rename", "comment", "docstring", "label", "whitespace",
    "format", "lint", "indent", "wording",
)


@dataclass
class TierResult:
    tier: int            # 0..3
    size: str            # S / M / L / XL
    requires_spec: bool  # tier >= 2
    requires_prd: bool   # tier >= 2
    reason: str


def _kw_hit(tokens: tuple[str, ...], text: str) -> str | None:
    for t in tokens:
        if re.search(r"\b" + re.escape(t) + r"\b", text):
            return t
    return None


def classify_tier(description: str) -> TierResult:
    """Map a free-text task description to an SDD-OS tier (0-3).

    Highest matching tier wins (3 > 2 > 1 > 0). A PRD-trigger keyword
    forces at least Tier 2. No explicit signal -> Tier 1 (Standard) as a
    safe non-trivial default (the dataset escalates under ambiguity).
    """
    text = (description or "").lower()
    hit3 = _kw_hit(_TIER3, text)
    prd = _kw_hit(_PRD_TRIGGER, text)
    hit2 = _kw_hit(_TIER2, text)
    hit1 = _kw_hit(_TIER1, text)
    hit0 = _kw_hit(_TIER0, text)

    if hit3:
        tier, reason = 3, f"strategic/platform signal: {hit3!r}"
    elif hit2 or prd:
        tier, reason = 2, f"feature/system signal: {(hit2 or prd)!r}"
    elif hit1:
        tier, reason = 1, f"standard signal: {hit1!r}"
    elif hit0:
        tier, reason = 0, f"micro signal: {hit0!r}"
    else:
        tier, reason = 1, "no explicit signal -> default Standard (Tier 1)"

    return TierResult(
        tier=tier, size=TIER_TO_SIZE[tier],
        requires_spec=tier >= 2, requires_prd=tier >= 2, reason=reason)


# --- Novelty proof gate (PR-NOVELTY-PROOF-REQUIRED-001) -----------------
# Sealed 2026-07-30 after the IIG Compendium audit: 0 of 30 proposed
# "mega-system" candidates (institutional fabric/OS/platform/kernel/
# compendium) survived a mechanism-level check against a discovered
# denominator -- the sixth consecutive proposal of this shape (AISHF,
# RE Baseline's 3 NEW families -> 1, KSF's 22 -> 4-deferred, the UKR
# Compendium's 8-step escalation -> 0, this IIG pass -> 0) to measure as
# majority-or-fully owned. Each time, the check was run manually by Owner
# ruling at real audit cost. This gate exists to catch the next one at the
# spec stage instead. See vault/plans/iig-compendium-2026-07-30.md.

NOVELTY_PROOF_QUESTIONS: tuple[str, ...] = (
    "What concrete problem has no owner today?",
    "What new outcome would this produce?",
    "What real consumer needs it?",
    "Why is extending an existing owner insufficient?",
    "What new primitive does it require?",
    "What decisions would it make that nobody makes today?",
    "What evidence would it produce?",
    "What failure class does it prevent?",
    "What interfaces would it have with existing owners?",
    "How would its value be measured?",
    "What complexity would it introduce?",
    "What condition would justify retiring it?",
    "Why is this not a rhetorical layer over systems that already exist?",
)

# Keywords signaling a proposal to mint a new named institutional
# mega-system, as opposed to a normal feature/module/extension.
_NOVELTY_TRIGGER: tuple[str, ...] = (
    "fabric", "compendium", "institutional operating system", "kernel",
    "civilization", "governance layer", "intelligence platform",
    "operating system", "meta-system", "mega-system", "new dataset family",
    "universal runtime", "constitutional layer",
)


@dataclass
class NoveltyGateResult:
    applies: bool
    matched: str | None
    questions: tuple[str, ...]
    message: str


def check_novelty_gate(task_description: str) -> NoveltyGateResult:
    """PR-NOVELTY-PROOF-REQUIRED-001: before admitting a new institutional
    fabric/OS/platform/kernel/compendium, require the 13-question novelty
    proof, mechanism-checked against a DISCOVERED denominator (grep the
    real repo), never against the proposal's own curated owner list.

    Advisory: returns the questions for the agent/Owner to answer with
    evidence. Does not itself decide the verdict -- a name without a
    verified owner gap is not proof; only cited file:line non-ownership is.
    """
    text = (task_description or "").lower()
    hit = _kw_hit(_NOVELTY_TRIGGER, text)
    if not hit:
        return NoveltyGateResult(
            applies=False, matched=None, questions=(),
            message="No new-mega-system signal detected -- gate not required.")

    return NoveltyGateResult(
        applies=True, matched=hit, questions=NOVELTY_PROOF_QUESTIONS,
        message=(
            f"Novelty-system signal detected ({hit!r}). Before treating this "
            "as a new dataset family, answer all 13 questions above with "
            "cited file:line evidence from a DISCOVERED sweep of this repo "
            "(grep for the mechanism, not the name) -- never from the "
            "proposal's own list of what it assumes doesn't exist. Base "
            "rate on this repo across 6 independent audits: 0-1 of every "
            "22-30 proposed candidates survive. Missing evidence on any "
            "question -> not a new dataset; classify instead as "
            "EXTEND_EXISTING_OWNER, NEW_MODULE, NEW_VIEW, NEW_POLICY_PACK, "
            "NEW_SCANNER_OR_GATE, or REJECT."))
