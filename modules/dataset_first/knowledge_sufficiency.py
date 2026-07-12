#!/usr/bin/env python3
"""knowledge_sufficiency.py -- DFP Knowledge Sufficiency Engine.

Answers one question: is the knowledge we already hold sufficient to GOVERN this build?

Ten dimensions, each scored 0-10 (a NUMBER, never an adjective). Four are read from
sealed providers; six are derived from the proposal text and are CAPPED in aggregate so
that eloquence can move the score within a class but never across a class boundary
(DFP-00 VI.10 -- the anti-eloquence cap).

Composed providers (signatures verified at source, HR-PREMISE-001):
  spec_gate.classify_tier(description) -> TierResult(tier, size, requires_spec, ...)
  d2a_engine.run(Proposal(description, name)) -> D2AVerdict(.dupe.coverage_pct)
  epistemic_ladder.epistemic_level(fingerprint, repo) -> "E0".."E6"

Reversibility is READ, never computed here: the caller (DRK's kernel, which has already
classified it) passes reversibility="A"|"B"|"C". Absent it, the engine degrades to a text
signal and says so in the rationale. DFP never constructs a DecisionObject and never
assigns an epistemic level (INV-2).

Fail-open ABSOLUTE: any provider error degrades that dimension to its neutral value and
records the degradation. The engine never raises and never blocks.
"""
from __future__ import annotations

import hashlib
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

# --- The four project classes (CANONICAL_ONTOLOGY 2.1, closed at four) ---------------
DIRECT_IMPLEMENTATION = "DIRECT_IMPLEMENTATION"
EXPERIMENT_FIRST = "EXPERIMENT_FIRST"
HYBRID = "HYBRID"
DATASET_FIRST_MANDATORY = "DATASET_FIRST_MANDATORY"

PROJECT_CLASSES = (DIRECT_IMPLEMENTATION, EXPERIMENT_FIRST, HYBRID,
                   DATASET_FIRST_MANDATORY)

# Cost ordering (DFP-00 IV.7): a tie resolves to the CHEAPER class.
CLASS_COST = {DIRECT_IMPLEMENTATION: 0, EXPERIMENT_FIRST: 1, HYBRID: 2,
              DATASET_FIRST_MANDATORY: 3}

# --- The seven kinds of knowledge (CANONICAL_ONTOLOGY 2.2) ---------------------------
FOUNDATIONAL_SCIENCE = "FOUNDATIONAL_SCIENCE"
GOVERNANCE = "GOVERNANCE"
ONTOLOGY = "ONTOLOGY"
TAXONOMY = "TAXONOMY"
PROTOCOL = "PROTOCOL"
BENCHMARK = "BENCHMARK"
EVALUATOR = "EVALUATOR"

KNOWLEDGE_TYPES = (FOUNDATIONAL_SCIENCE, GOVERNANCE, ONTOLOGY, TAXONOMY, PROTOCOL,
                   BENCHMARK, EVALUATOR)

# --- The ten dimensions (CANONICAL_ONTOLOGY 4). PROVIDER_DIMS are read from a sealed
# sibling; TEXT_DIMS are derived from the proposal prose and are capped in aggregate.
PROVIDER_DIMS = ("cost_of_error", "reuse_breadth", "institutional_capacity",
                 "transversality")
TEXT_DIMS = ("domain_complexity", "governance_need", "uncertainty", "lifespan",
             "criticality", "prior_science_need")
DIMENSIONS = PROVIDER_DIMS + TEXT_DIMS

# Thresholds (CANONICAL_ONTOLOGY 4). HYPOTHESES, owned by DFP-05, required to move under
# evidence. A threshold unmoved after 20 records is unmeasured, never perfect.
THRESHOLD_KNOWLEDGE_FIRST = 70
THRESHOLD_HYBRID = 40
CAPACITY_CONJUNCT = 6      # DFP-00 VI.3 -- the clause that makes this a knowledge gate
UNCERTAINTY_EXPERIMENT = 8

# The anti-eloquence cap (DFP-00 VI.10): the six text-derived dimensions may not, on
# their own, lift a verdict past HYBRID when every provider dimension is low.
PROVIDER_FLOOR_FOR_ESCALATION = 4

# --- Text signals. Deterministic keyword evidence, never an agent's opinion. ---------
_SIG = {
    "domain_complexity": ("architecture", "authority", "kernel", "protocol", "ontology",
                          "taxonomy", "consensus", "distributed", "concurrent",
                          "governance", "semantics", "invariant"),
    "governance_need": ("authority", "decide", "permission", "forbid", "policy", "rule",
                        "govern", "who may", "approval", "override", "sealed"),
    "uncertainty": ("unknown", "unclear", "explore", "investigate", "whether", "measure",
                    "degrade", "behave", "under load", "latency", "benchmark", "probe"),
    "lifespan": ("permanent", "forever", "every repo", "standard", "constitution",
                 "invariant", "sealed", "durable", "long-lived", "outlive"),
    "criticality": ("production", "blocking", "critical", "security", "data loss",
                    "corruption", "irreversible", "outage"),
    "prior_science_need": ("science", "first principles", "theory", "model of",
                           "ontology", "taxonomy", "no precedent", "novel", "unproven"),
}
# Empirical-uncertainty markers: the open question is about REALITY, answerable by a
# cheap probe -> EXPERIMENT_FIRST, never a corpus (DFP-00 III.4).
_EMPIRICAL = ("measure", "benchmark", "under load", "latency", "throughput", "degrade",
              "how fast", "does it actually", "profile", "reproduce", "observe")


@dataclass
class KnowledgeSufficiencyVerdict:
    sufficient: bool
    score: int                        # 0-100
    dimensions: dict                  # dim -> 0..10
    missing: list = field(default_factory=list)        # KnowledgeType names
    existing_assets: list = field(default_factory=list)
    acis_ceiling: int = 0             # 0..7 -- READ from ACIS, never assigned here
    verdict: str = DIRECT_IMPLEMENTATION
    confidence: int = 0               # distance to the runner-up class (DFP-00 VI.11)
    rationale: str = ""
    degraded: list = field(default_factory=list)       # providers that failed (fail-open)


def _hits(text: str, words) -> int:
    return sum(1 for w in words if w in text)


def _text_score(text: str, dim: str) -> int:
    """0-10 from keyword density. Deterministic -> hermetic."""
    words = _SIG.get(dim, ())
    if not words:
        return 5
    n = _hits(text, words)
    return max(0, min(10, n * 2 + 1))


def _fingerprint(description: str) -> str:
    """Stable fingerprint for the ACIS lookup. Mirrors the flywheel's scheme; falls back
    to a local sha256 so a parent refactor can never kill this engine."""
    try:
        from modules.fable_distillation.fd_07_flywheel import _fingerprint as _fp
        return _fp("dataset_first", description)
    except Exception:  # noqa: BLE001 -- fail-open shim
        return hashlib.sha256(description.encode("utf-8", "replace")).hexdigest()[:16]


def _read_acis_ceiling(description: str, repo: str, degraded: list) -> int:
    """READ the epistemic level of any deposited claim governing this domain.
    E0 (no deposit) is not an error -- it is the signal: no deposited claim governs this
    domain, therefore the institutional capacity to govern the build is absent."""
    try:
        from modules.fable_distillation.epistemic_ladder import epistemic_level
        lvl = epistemic_level(_fingerprint(description), repo)
        m = re.match(r"E(\d)", str(lvl or "E0"))
        return int(m.group(1)) if m else 0
    except Exception:  # noqa: BLE001 -- fail-open
        degraded.append("acis")
        return 0


def _read_d2a(description: str, name: str, degraded: list) -> tuple:
    """READ how much of this proposal the sealed families already own.

    Returns (coverage_pct, functional). BOTH are returned, and only `functional` is
    allowed to move institutional_capacity. This is not a stylistic choice -- it is a
    measured correction:

        proposal                       coverage  functional   truth
        Token Budget Planner (dupe)         95%         29    duplicate
        maximal foundational (novel)        92%          7    NOVEL
        rate limiter (trivial)              14%         12    science exists

    `coverage_pct` is inflated by D2A's architectural term, which forces >=80% whenever
    the proposal's tokens touch >=4 families -- something a long, rich, foundational
    proposal does BY CONSTRUCTION, purely from vocabulary. Mapping coverage to capacity
    made a genuinely-novel proposal look 92% owned, drove capacity to 1, and rendered
    DATASET_FIRST_MANDATORY UNREACHABLE -- a dead class, and with it a dead eleventh
    verdict in DRK.

    `functional` is the per-family PRECISION: the fraction of the proposal's own tokens
    that the best parent actually owns. It separates a true duplicate (29) from a rich
    novel proposal (7) cleanly, and it does not rise with length.

    Sealed as T-DFP-COVERAGE-AS-CAPACITY-001; the same failure class as
    T-DRK-PRECEDENT-LENGTH-BIAS-001 and T-D2A-LEXICAL-BLINDNESS-001. DFP-00 VI.6 warned
    about exactly this and the first implementation did it anyway, which is the strongest
    possible argument for the control-set discipline of VI.8.
    """
    try:
        from modules.duplicate_to_advantage.d2a_engine import Proposal, run
        d = run(Proposal(description, name)).dupe
        return int(d.coverage_pct), int(d.functional)
    except Exception:  # noqa: BLE001 -- fail-open
        degraded.append("d2a")
        return 0, 0


def _read_tier(description: str, degraded: list) -> int:
    """READ the task tier. Never re-derived here (INV-7 -- spec_gate owns it)."""
    try:
        from modules.spec_gate.gate import classify_tier
        return int(classify_tier(description).tier)
    except Exception:  # noqa: BLE001 -- fail-open
        degraded.append("spec_gate")
        return 1


_REVERSIBILITY_COST = {"A": 1, "B": 5, "C": 9}


def evaluate(description: str,
             name: str = "",
             *,
             repo: str = "claude-power-pack",
             reversibility: str | None = None) -> KnowledgeSufficiencyVerdict:
    """Score the ten dimensions and return the sufficiency verdict.

    `reversibility` ("A"|"B"|"C") is READ from the caller -- DRK's kernel has already
    classified it. DFP never computes it (INV-7). Absent, a text signal is used and the
    degradation is recorded in the rationale.
    """
    degraded: list = []
    try:
        text = f"{name} {description}".lower().strip()
        if not text:
            return KnowledgeSufficiencyVerdict(
                sufficient=True, score=0, dimensions={},
                verdict=DIRECT_IMPLEMENTATION, confidence=0,
                rationale="empty proposal -- silence (fail-open)")

        dims: dict = {}

        # --- provider-read dimensions ------------------------------------------------
        if reversibility in _REVERSIBILITY_COST:
            dims["cost_of_error"] = _REVERSIBILITY_COST[reversibility]
        else:
            degraded.append("reversibility-not-supplied")
            dims["cost_of_error"] = _text_score(text, "criticality")

        coverage, functional = _read_d2a(description, name, degraded)
        acis = _read_acis_ceiling(description, repo, degraded)

        # institutional_capacity = how little governing knowledge already exists.
        # Driven by FUNCTIONAL precision, never by coverage_pct (see _read_d2a: coverage
        # is length-biased and made this class unreachable). A PROVEN deposit (ACIS E3+)
        # is hard evidence that the governing claim is established, so it lowers capacity
        # further -- read from ACIS, never assigned here (INV-2).
        capacity = 10 - round(functional / 4)
        if acis >= 3:
            capacity -= 4
        dims["institutional_capacity"] = max(0, min(10, capacity))

        # No deposit (E0) means nothing in the epistemics ledger governs this domain.
        dims["reuse_breadth"] = max(0, min(10, 8 - acis))

        tier = _read_tier(description, degraded)
        dims["transversality"] = max(0, min(10, tier * 3))

        # --- text-derived dimensions (capped in aggregate) ----------------------------
        for d in TEXT_DIMS:
            dims[d] = _text_score(text, d)

        score = int(round(100 * sum(dims.values()) / (10 * len(DIMENSIONS))))

        # --- the anti-eloquence cap (DFP-00 VI.10) -----------------------------------
        provider_max = max(dims[d] for d in PROVIDER_DIMS)
        capped = provider_max < PROVIDER_FLOOR_FOR_ESCALATION

        # --- classification ----------------------------------------------------------
        empirical = any(w in text for w in _EMPIRICAL)
        capacity = dims["institutional_capacity"]
        uncertainty = dims["uncertainty"]

        # EXPERIMENT_FIRST is NOT gated on the aggregate score, and the reason is a design
        # bug caught by DFP-00's own worked example (IV.11) failing against this engine on
        # day one. A cheap empirical probe is LOW-scoring by construction: the aggregate
        # measures how much governing knowledge is NEEDED, not how cheaply the open
        # question could be answered by looking. Gating experiment-first behind a high
        # score made it unreachable for exactly the proposals it exists to catch, and
        # would have sent a two-hour probe to write a corpus or to guess in code -- the
        # most embarrassing failure this family can produce (DFP-00 III.4).
        if empirical and uncertainty >= UNCERTAINTY_EXPERIMENT:
            verdict = EXPERIMENT_FIRST
        elif score >= THRESHOLD_KNOWLEDGE_FIRST and capacity >= CAPACITY_CONJUNCT:
            verdict = DATASET_FIRST_MANDATORY
        elif score >= THRESHOLD_HYBRID:
            verdict = HYBRID
        else:
            verdict = DIRECT_IMPLEMENTATION

        if capped and CLASS_COST[verdict] > CLASS_COST[HYBRID]:
            verdict = HYBRID   # eloquence may move within a class, never across

        missing = _missing_kinds(text, capacity, acis)
        # INV-1: no corpus without a NAMED missing science.
        if verdict == DATASET_FIRST_MANDATORY and not missing:
            verdict = HYBRID

        # Confidence = distance to the nearest threshold boundary (DFP-00 VI.11).
        edges = [abs(score - THRESHOLD_KNOWLEDGE_FIRST), abs(score - THRESHOLD_HYBRID)]
        confidence = max(0, min(100, min(edges) * 5))

        bits = [f"score={score}", f"capacity={capacity}", f"acis=E{acis}",
                f"d2a_coverage={coverage}%", f"tier={tier}"]
        if capped:
            bits.append("text-cap applied (providers low)")
        if degraded:
            bits.append("degraded: " + ",".join(degraded))

        return KnowledgeSufficiencyVerdict(
            sufficient=(verdict == DIRECT_IMPLEMENTATION),
            score=score, dimensions=dims, missing=missing,
            existing_assets=[f"d2a-parent-coverage:{coverage}%"] if coverage else [],
            acis_ceiling=acis, verdict=verdict, confidence=confidence,
            rationale="; ".join(bits), degraded=degraded)

    except Exception as e:  # noqa: BLE001 -- fail-open ABSOLUTE (INV-5)
        return KnowledgeSufficiencyVerdict(
            sufficient=True, score=0, dimensions={}, verdict=DIRECT_IMPLEMENTATION,
            confidence=0, rationale=f"fail-open: {type(e).__name__}",
            degraded=["engine"])


def _missing_kinds(text: str, capacity: int, acis: int) -> list:
    """Which of the seven kinds are absent. INV-1: a knowledge-first verdict REQUIRES at
    least one named kind. 'This feels big' is not a signal."""
    if capacity < CAPACITY_CONJUNCT:
        return []                       # the science exists -> nothing is missing
    missing = []
    if any(w in text for w in ("authority", "govern", "decide", "permission", "policy",
                               "forbid", "override")):
        missing.append(GOVERNANCE)
    if any(w in text for w in ("ontology", "what is a", "naming", "concept", "model of",
                               "semantics")):
        missing.append(ONTOLOGY)
    if any(w in text for w in ("taxonomy", "classify", "kinds", "categories", "types of")):
        missing.append(TAXONOMY)
    if any(w in text for w in ("protocol", "sequence", "lifecycle", "state machine",
                               "stages", "transition")):
        missing.append(PROTOCOL)
    if any(w in text for w in ("benchmark", "threshold", "score", "metric", "measure")):
        missing.append(BENCHMARK)
    if any(w in text for w in ("evaluate", "evaluator", "check", "verify", "gate",
                               "falsif")):
        missing.append(EVALUATOR)
    if acis == 0 and any(w in text for w in ("science", "first principles", "theory",
                                             "no precedent", "novel", "unproven")):
        missing.append(FOUNDATIONAL_SCIENCE)
    return missing
