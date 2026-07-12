"""decision_record.py -- canonical Decision Object / Record + append-only Registry.

The schema is fixed by DRK-00 (vault/knowledge_base/decision_review/
drk_00_foundations_canonical_objects.md). Author-supplied fields are required;
derived fields (reversibility, blast_radius, confidence, review_tier, verdict)
default empty and are filled by decision_kernel.py -- an author cannot self-assign
them (No-Autopromotion, DRK-00 III.1 invariant 2).

Determinism: no wall-clock is read here; the caller supplies `ts` (an ISO string)
so records are reproducible in tests. The Registry is append-only JSONL; a
retraction is a new superseding record, never an erasure (DRK-05).

Fail-open: every disk operation swallows OSError and returns a falsy result;
this module never raises on I/O so the kernel can stay fail-open to DEFER.

Stdlib only. No hardcoded absolute paths (PP core E11): paths derive from
PP_ROOT or an explicit `registry_path` argument.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = PP_ROOT / "vault" / "decision_registry" / "records.jsonl"


class EvidenceType(str, Enum):
    """The evidence model (DRK-00 I.4). Ordered strong -> conditioning."""

    FACT = "fact"
    OBSERVED_EVIDENCE = "observed_evidence"
    INFERENCE = "inference"
    HYPOTHESIS = "hypothesis"
    PREDICTION = "prediction"
    ASSUMPTION = "assumption"
    PREFERENCE = "preference"
    CONSTRAINT = "constraint"
    UNCERTAINTY = "uncertainty"
    UNKNOWN = "unknown"


# Weight class per evidence type. "strong" items are what a high burden counts.
EVIDENCE_WEIGHT = {
    EvidenceType.FACT: "strong",
    EvidenceType.OBSERVED_EVIDENCE: "strong",
    EvidenceType.INFERENCE: "medium",
    EvidenceType.HYPOTHESIS: "weak",
    EvidenceType.PREDICTION: "weak",
    EvidenceType.ASSUMPTION: "weak",
    EvidenceType.PREFERENCE: "non_evidential",
    EvidenceType.CONSTRAINT: "conditioning",
    EvidenceType.UNCERTAINTY: "conditioning",
    EvidenceType.UNKNOWN: "conditioning",
}


class Reversibility(str, Enum):
    """DRK-02 Tipo classification."""

    A = "A"  # trivially undone
    B = "B"  # hard to undo, has a cost
    C = "C"  # practically irreversible


class ReviewTier(str, Enum):
    """DRK-00 II.3 risk-based review routing. Ln is open by extension."""

    L0 = "L0"  # no review (out of scope)
    L1 = "L1"  # record only
    L2 = "L2"  # standard
    L3 = "L3"  # deep (adversarial + counterfactual)
    L4 = "L4"  # foundational (block-gate authority)


class Verdict(str, Enum):
    """DRK-00 II.2 -- the closed ELEVEN-verdict ontology.

    Amended 2026-07-12 (DFP, governed under DRK-07's evolution protocol; recorded as a
    DecisionRecord and reviewed by this kernel itself before being made).

    BUILD-KNOWLEDGE-FIRST is the eleventh member. It is NOT a synonym for
    REQUEST-EVIDENCE: that verdict means "go and get evidence FOR THIS DECISION", whereas
    this one means "the decision is not the problem -- the governing science does not
    exist yet, and building now would permanently encode a choice nobody knows how to
    make." Different instruction, different exit. The kernel was already shaped to hold
    the case (a build whose governing science is absent IS an irreversible act taken under
    insufficient evidence); it had simply never been given a name for it.
    """

    REJECT = "REJECT"
    REFRAME = "REFRAME"
    REQUEST_EVIDENCE = "REQUEST-EVIDENCE"
    RUN_EXPERIMENT = "RUN-EXPERIMENT"
    BUILD_KNOWLEDGE_FIRST = "BUILD-KNOWLEDGE-FIRST"
    DEFER = "DEFER"
    KEEP_LOCAL = "KEEP-LOCAL"
    CONSOLIDATE = "CONSOLIDATE"
    REMOVE = "REMOVE"
    APPROVE_WITH_CONDITIONS = "APPROVE-WITH-CONDITIONS"
    APPROVE = "APPROVE"


@dataclass
class Evidence:
    """One evidence item (DRK-00 I.4). `acis_level` is read from ACIS (E0-E7),
    never assigned here. `observable` is required for PREDICTION items so the
    accountability layer can score them (Parte VI VI.2)."""

    type: EvidenceType
    claim: str
    source: str = ""
    acis_level: int | None = None  # 0..7 from ACIS; None = unlevelled
    observable: str = ""           # required iff type == PREDICTION

    @property
    def weight(self) -> str:
        return EVIDENCE_WEIGHT.get(self.type, "weak")

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "claim": self.claim,
            "source": self.source,
            "acis_level": self.acis_level,
            "observable": self.observable,
        }


@dataclass
class DecisionObject:
    """The input to review (DRK-00 I.3). Required fields are author-supplied;
    derived fields default empty and are filled by the kernel."""

    # --- required (author-supplied) ---
    id: str
    statement: str
    problem: str
    options: list[str]
    chosen: str
    rationale: str
    accepted_risks: list[str] = field(default_factory=list)
    discarded_alternatives: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    predicted_consequences: list[dict] = field(default_factory=list)
    is_build_decision: bool = False  # routes Stage 7 (D2A placement)

    # --- derived (kernel-filled; None/empty until reviewed) ---
    reversibility: Reversibility | None = None
    blast_radius: dict = field(default_factory=dict)
    confidence: int | None = None  # DCS 0-100
    review_tier: ReviewTier | None = None
    verdict: Verdict | None = None
    owner_override: dict | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "statement": self.statement,
            "problem": self.problem,
            "options": self.options,
            "chosen": self.chosen,
            "rationale": self.rationale,
            "accepted_risks": self.accepted_risks,
            "discarded_alternatives": self.discarded_alternatives,
            "dependencies": self.dependencies,
            "evidence": [e.to_dict() for e in self.evidence],
            "predicted_consequences": self.predicted_consequences,
            "is_build_decision": self.is_build_decision,
            "reversibility": self.reversibility.value if self.reversibility else None,
            "blast_radius": self.blast_radius,
            "confidence": self.confidence,
            "review_tier": self.review_tier.value if self.review_tier else None,
            "verdict": self.verdict.value if self.verdict else None,
            "owner_override": self.owner_override,
        }

    def missing_required(self) -> list[str]:
        """Required fields absent or empty. A one-option decision is itself a
        signal (Default Suspicion Rule, DRK-01 Stage 2) -- surfaced, not raised."""
        missing = []
        if not self.statement.strip():
            missing.append("statement")
        if not self.problem.strip():
            missing.append("problem")
        if len(self.options) < 2:
            missing.append("options(<2)")
        if not self.chosen.strip():
            missing.append("chosen")
        if not self.rationale.strip():
            missing.append("rationale")
        return missing


@dataclass
class DecisionRecord:
    """The after-object (DRK-00 I.5): the decision + review trace + (later) the
    accountability fields written when the outcome is known (Parte VI)."""

    obj: DecisionObject
    ts: str = ""                             # caller-supplied ISO time
    tier: ReviewTier | None = None
    verdict: Verdict | None = None
    cited_sources: list[dict] = field(default_factory=list)
    guards_fired: list[str] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)   # for APPROVE-WITH-CONDITIONS
    blocked: bool = False
    # --- accountability (Parte VI; filled at OBSERVED/ATTRIBUTED) ---
    realized_consequences: list[dict] = field(default_factory=list)
    prediction_error: dict | None = None
    attribution: dict | None = None          # reasoning/execution/luck/context
    superseded_by: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.obj.id if self.obj is not None else None,
            "ts": self.ts,
            "tier": self.tier.value if self.tier else None,
            "verdict": self.verdict.value if self.verdict else None,
            "blocked": self.blocked,
            "cited_sources": self.cited_sources,
            "guards_fired": self.guards_fired,
            "conditions": self.conditions,
            "decision": self.obj.to_dict() if self.obj is not None else None,
            "realized_consequences": self.realized_consequences,
            "prediction_error": self.prediction_error,
            "attribution": self.attribution,
            "superseded_by": self.superseded_by,
        }


class Registry:
    """Append-only JSONL Decision Registry (DRK-00 I.5, DRK-05).

    Append-only: a retraction is a new record with `superseded_by`, never an
    erasure. Fail-open: every disk op swallows OSError and returns falsy; the
    kernel stays fail-open to DEFER.
    """

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else DEFAULT_REGISTRY

    def next_id(self) -> str:
        """DEC-<n>, derived from the count on disk. Deterministic given state."""
        n = self.count() + 1
        return f"DEC-{n:04d}"

    def count(self) -> int:
        try:
            if not self.path.exists():
                return 0
            with self.path.open("r", encoding="utf-8") as fh:
                return sum(1 for line in fh if line.strip())
        except OSError:
            return 0

    def append(self, record: DecisionRecord) -> bool:
        """Append one record as a JSONL line. Returns False on any I/O failure
        (fail-open); never raises."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            line = json.dumps(record.to_dict(), ensure_ascii=False)
            # Binary append with explicit LF avoids Windows text-mode CRLF
            # compounding (feedback_windows_text_mode_compounding).
            flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_BINARY", 0)
            fd = os.open(str(self.path), flags, 0o644)
            try:
                os.write(fd, (line + "\n").encode("utf-8"))
            finally:
                os.close(fd)
            return True
        except (OSError, TypeError, ValueError, AttributeError):
            return False

    def load(self) -> list[dict]:
        """Read all records (for precedent + accountability). Fail-open to []."""
        out: list[dict] = []
        try:
            if not self.path.exists():
                return out
            with self.path.open("r", encoding="utf-8-sig") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        out.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except OSError:
            return out
        return out
