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


def _check_knowledge_sufficiency(task_description: str) -> SpecGateResult | None:
    """DFP wiring (ukr-runtime-2026-07-30.md item 1 -- candidate C). dataset_first
    self-describes as "an advisor wired into an authority, never an authority
    itself" (INV-5); this makes spec_gate that authority on the L/XL axis, the
    same role it already plays for plain spec-existence. Returns None (no
    block) unless DFP's verdict is DATASET_FIRST_MANDATORY. Fail-open: DFP is
    optional infrastructure, never a hard dependency of the spec gate."""
    try:
        from modules.dataset_first.knowledge_sufficiency import (
            DATASET_FIRST_MANDATORY, evaluate)
    except Exception:
        return None
    try:
        v = evaluate(task_description)
    except Exception:
        return None
    if v.verdict != DATASET_FIRST_MANDATORY:
        return None
    missing = ", ".join(v.missing) if v.missing else "unspecified"
    capacity = v.dimensions.get("institutional_capacity", "?")
    return SpecGateResult(
        has_spec=False, spec_path=None, gate_passed=False,
        action="knowledge_first_required",
        message=(
            f"Knowledge Sufficiency Engine (DFP) verdict: "
            f"DATASET_FIRST_MANDATORY (score={v.score}, missing={missing}, "
            f"institutional_capacity={capacity}/10, ACIS ceiling=E"
            f"{v.acis_ceiling}). The governing science/ontology/protocol this "
            "build needs does not yet exist. This is not a spec-writing gap -- "
            "writing a spec against knowledge that doesn't exist yet just "
            "documents the guess. Establish the missing knowledge kind(s) "
            "first."))


def check_spec_gate(task_description: str,
                    cwd: Path | str | None = None,
                    task_size: str = "M") -> SpecGateResult:
    """Check whether an L/XL task has a spec. S/M -> always proceed."""
    if task_size not in _LXL:
        return SpecGateResult(
            has_spec=True, spec_path=None, gate_passed=True,
            action="proceed",
            message=f"{task_size} task -- spec gate not required.")

    kv = _check_knowledge_sufficiency(task_description)
    if kv is not None:
        return kv

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

# A keyword list is bounded by its own vocabulary: an idiom nobody thought to
# add reads as zero, and zero never trips a gate. Measured 2026-08-04 by
# replaying this rule against its own incident class -- it fired on the IIG
# *compendium* and stayed silent on UCEIMR ("Universal Capability Evolution &
# Institutional Mining Runtime, 15 datasets"), the seventh proposal of exactly
# the class it was sealed to catch, purely because that title splits the two
# words of "universal runtime".
#
# The shape, not the noun, is what all seven incidents shared: an enumerated
# catalog of datasets. Counting them is vocabulary-independent.
_NOVELTY_SHAPE = re.compile(
    r"\b\d{1,3}\s+(?:new\s+|proposed\s+)?"
    r"(?:datasets?|dataset\s+famil(?:y|ies)|corpora|meta-systems?)\b",
    re.I,
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
        shape = _NOVELTY_SHAPE.search(text)
        hit = f"enumerated catalog: {shape.group(0).strip()!r}" if shape else None
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


# --- Problem-reframing gate (EFAIF residue R2) --------------------------
# The EFAIF audit (vault/plans/efaif-corpus-2026-08-04.md) rejected all 26
# proposed datasets and left two residues. R2: the `lateral-thinking` skill
# already owns the frames and owns them well, but nothing FIRES it. Its own
# description activates it on Owner phrasing -- "I'm stuck", "no idea",
# "atascado". A task that arrives already committed to a solution never
# produces those words, which is exactly the case where reframing pays. The
# frames exist and are never reached on the path that needs them.
#
# This gate is the missing trigger, not a second copy of the frames. It fires
# on one measurable shape: a description that commits to building a specific
# artifact while stating no problem the artifact would solve. That shape has
# no falsifiable objective -- there is nothing to check the solution against,
# so solution-fixation cannot be caught downstream either.
#
# Vocabulary limit, stated rather than hidden (feedback_zero_cannot_fall):
# the solution arm is a keyword list and is bounded by its own vocabulary --
# an idiom nobody added reads as no-signal. The problem arm is built the
# other way round: it looks for the PRESENCE of any problem marker and treats
# absence as the trigger. So an unrecognized way of phrasing a solution fails
# toward silence (no false alarm), while an unrecognized way of phrasing a
# problem is the only false-alarm path. That asymmetry is deliberate: this
# gate is advisory, and a spurious prompt to think costs one paragraph,
# whereas a missed reframe costs a corpus.

REFRAMING_FRAMES: tuple[str, ...] = (
    "Reframing -- is the stated request the actual objective, or a symptom?",
    "Inversion -- what if the opposite requirement were true?",
    "Cross-domain analogy -- who already solved this shape elsewhere?",
    "Constraint removal -- which constraint here is assumed, not real?",
    "First principles -- what remains true independent of the current design?",
)

# Commitment to producing a named artifact.
_SOLUTION_SIGNAL: tuple[str, ...] = (
    "build", "create", "implement", "add", "write", "make", "ship",
    "scaffold", "generate", "set up", "wire", "introduce", "design",
    "construir", "construye", "crear", "crea", "implementar", "implementa",
    "escribir", "generar",
)
# Any marker that a problem, symptom, cause or objective was stated.
_PROBLEM_SIGNAL: tuple[str, ...] = (
    "because", "since", "currently", "today", "fails", "failing", "broken",
    "breaks", "bug", "error", "regression", "slow", "duplicate", "missing",
    "cannot", "doesn't", "does not", "never", "gap", "risk", "problem",
    "issue", "incident", "root cause", "symptom", "so that", "in order to",
    "porque", "actualmente", "falla", "roto", "no funciona", "problema",
    "causa", "riesgo",
)


@dataclass
class ReframingGateResult:
    applies: bool
    matched: str | None
    frames: tuple[str, ...]
    message: str


def check_reframing_gate(task_description: str,
                         min_tier: int = 2) -> ReframingGateResult:
    """Fire the reframing frames before a plan commits to a solution.

    Applies only at tier >= min_tier (default 2, the tier at which SDD-OS
    already requires a spec). Reframing a typo is theater, and a gate that
    fires on everything is ignored on everything.
    """
    text = (task_description or "").lower()
    if not text.strip():
        return ReframingGateResult(
            applies=False, matched=None, frames=(),
            message="Empty description -- reframing gate not applicable.")

    tier = classify_tier(task_description).tier
    if tier < min_tier:
        return ReframingGateResult(
            applies=False, matched=None, frames=(),
            message=(f"Tier {tier} < {min_tier} -- reframing gate not "
                     "required for localized work."))

    solution = _kw_hit(_SOLUTION_SIGNAL, text)
    if not solution:
        return ReframingGateResult(
            applies=False, matched=None, frames=(),
            message="No solution-commitment signal -- gate not required.")

    problem = _kw_hit(_PROBLEM_SIGNAL, text)
    if problem:
        return ReframingGateResult(
            applies=False, matched=None, frames=(),
            message=(f"Problem stated ({problem!r}) alongside the proposed "
                     "solution -- the objective is checkable; gate satisfied."))

    return ReframingGateResult(
        applies=True, matched=solution, frames=REFRAMING_FRAMES,
        message=(
            f"Solution committed ({solution!r}) with no problem stated. This "
            "plan names what to build and never names what breaks without it, "
            "so there is no objective to check the build against and no way "
            "to catch solution-fixation later. Answer the frames above before "
            "the plan is approved -- or state the problem explicitly and the "
            "gate clears. Advisory: it does not block."))
