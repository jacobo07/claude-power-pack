#!/usr/bin/env python3
"""classifier.py -- DFP project classifier.

Produces a ProjectClassification: what KIND of unit of work is this, before we decide how
to start it. The tier is DELEGATED to spec_gate.classify_tier and never re-derived here
(INV-7 -- spec_gate owns the tier axis; DFP owns the knowledge axis; conflating them is
how a knowledge gate becomes a size gate, DFP-00 II.5).

Fail-open ABSOLUTE (INV-5): any error returns DIRECT_IMPLEMENTATION with the degradation
recorded. Silence, never a block.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.dataset_first.knowledge_sufficiency import (  # noqa: E402
    DIRECT_IMPLEMENTATION, evaluate,
)

# Observable signals (CANONICAL_ONTOLOGY 3). Each must be observable from the repository
# or the proposal text -- never from the agent's opinion.
PRECEDENT_ABSENT = "PRECEDENT_ABSENT"
PRECEDENT_PRESENT = "PRECEDENT_PRESENT"
HIGH_TRANSVERSALITY = "HIGH_TRANSVERSALITY"
LONG_LIFESPAN = "LONG_LIFESPAN"
IRREVERSIBLE = "IRREVERSIBLE"
LOW_ACIS = "LOW_ACIS"
EMPIRICAL_UNCERTAINTY = "EMPIRICAL_UNCERTAINTY"
TIER_LOW = "TIER_LOW"
SPEC_EXISTS = "SPEC_EXISTS"
CORPUS_OPEN = "CORPUS_OPEN"


@dataclass
class Signal:
    name: str
    observable: str          # WHAT was observed (never "it felt big")
    pushes_toward: str


@dataclass
class ProjectClassification:
    project_class: str
    tier: int                                     # delegated to spec_gate, never re-derived
    signals: list = field(default_factory=list)
    rationale: str = ""
    confidence: int = 0
    sufficiency: object = None                    # the KnowledgeSufficiencyVerdict


def _tier(description: str) -> int:
    try:
        from modules.spec_gate.gate import classify_tier
        return int(classify_tier(description).tier)
    except Exception:  # noqa: BLE001 -- fail-open
        return 1


def _spec_exists(cwd: Path) -> bool:
    try:
        from modules.spec_gate.gate import check_spec_gate
        return bool(check_spec_gate("", cwd, "L").has_spec)
    except Exception:  # noqa: BLE001 -- fail-open
        return False


def _open_corpus(cwd: Path) -> str:
    """CORPUS_OPEN (CANONICAL_ONTOLOGY 5.3): another family mid-build with unsealed Parts.
    Observed from disk. Returns the family name, or an empty string.

    Reads only STATUS TABLE ROWS (lines beginning with a pipe). An earlier version scanned
    the whole document for NOT_STARTED and was defeated by the doctrinal sentence every
    index carries -- "COMPLETE is never declared while any Part is NOT_STARTED" -- which
    made a prose statement about completeness look like a completeness marker. The signal
    on which this family's entire founding story rests was silently dead. Read the data,
    not the prose about the data.
    """
    try:
        kb = Path(cwd) / "vault" / "knowledge_base"
        for idx in sorted(kb.glob("*/*_INDEX.md")):
            fam = idx.parent.name
            if fam == "dataset_first":
                continue
            try:
                text = idx.read_text(encoding="utf-8-sig", errors="replace")
            except OSError:
                continue
            rows = [ln for ln in text.splitlines() if ln.lstrip().startswith("|")]
            if any("NOT_STARTED" in ln for ln in rows):
                return fam
    except Exception:  # noqa: BLE001 -- fail-open
        pass
    return ""


def classify(description: str,
             name: str = "",
             cwd: Path | str | None = None,
             *,
             reversibility: str | None = None) -> ProjectClassification:
    """Classify a proposed unit of work. Composes spec_gate (tier), the sufficiency
    engine (which itself composes D2A + ACIS), and the observable signals."""
    try:
        root = Path(cwd) if cwd else _PP_ROOT
        suff = evaluate(description, name, reversibility=reversibility)
        tier = _tier(description)
        text = f"{name} {description}".lower()

        signals: list = []
        cov = suff.dimensions.get("institutional_capacity", 0)
        if cov >= 6:
            signals.append(Signal(PRECEDENT_ABSENT,
                                  f"D2A coverage low (capacity={cov}/10)",
                                  "DATASET_FIRST"))
        else:
            signals.append(Signal(PRECEDENT_PRESENT,
                                  f"D2A coverage high (capacity={cov}/10)", "DIRECT"))
        if tier >= 2:
            signals.append(Signal(HIGH_TRANSVERSALITY, f"spec_gate tier={tier}",
                                  "DATASET_FIRST"))
        else:
            signals.append(Signal(TIER_LOW, f"spec_gate tier={tier}", "DIRECT"))
        if suff.dimensions.get("lifespan", 0) >= 6:
            signals.append(Signal(LONG_LIFESPAN, "durability markers in the proposal",
                                  "DATASET_FIRST"))
        if reversibility == "C":
            signals.append(Signal(IRREVERSIBLE, "DRK-02 returned Tipo C", "DATASET_FIRST"))
        if suff.acis_ceiling < 3:
            signals.append(Signal(LOW_ACIS,
                                  f"ACIS ceiling E{suff.acis_ceiling} (<E3, unproven)",
                                  "DATASET_FIRST"))
        if any(w in text for w in ("measure", "benchmark", "under load", "latency")):
            signals.append(Signal(EMPIRICAL_UNCERTAINTY,
                                  "the open question is answerable by a probe",
                                  "EXPERIMENT_FIRST"))
        if _spec_exists(root):
            signals.append(Signal(SPEC_EXISTS, "spec_gate found a spec in-repo", "DIRECT"))
        fam = _open_corpus(root)
        if fam:
            signals.append(Signal(CORPUS_OPEN,
                                  f"'{fam}' is mid-build with unsealed Parts", "DEFER"))

        return ProjectClassification(
            project_class=suff.verdict, tier=tier, signals=signals,
            rationale=suff.rationale, confidence=suff.confidence, sufficiency=suff)

    except Exception as e:  # noqa: BLE001 -- fail-open ABSOLUTE (INV-5)
        return ProjectClassification(
            project_class=DIRECT_IMPLEMENTATION, tier=1, signals=[],
            rationale=f"fail-open: {type(e).__name__}", confidence=0)
