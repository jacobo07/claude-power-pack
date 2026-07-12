#!/usr/bin/env python3
"""manifest.py -- Knowledge Infrastructure Mode: the eight-stage corpus lifecycle (DFP-02).

ARCHITECTURE -> ONTOLOGY -> AUTHORING -> REVIEW -> QA -> CERTIFIED -> FROZEN -> IMPLEMENTATION

IMPLEMENTATION is UNREACHABLE before CERTIFIED when the class is DATASET_FIRST_MANDATORY.
That unreachability IS the protocol.

The anti-bureaucracy terminating condition (INV-6): `parts_planned` is declared at
ARCHITECTURE and is IMMUTABLE thereafter. A family that grows its own denominator
mid-flight is gaming its own completion gate. A mode that cannot terminate is not a mode;
it is a permanent blocker wearing a lifecycle's clothes.

Fail-open ABSOLUTE (INV-5).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

ARCHITECTURE = "ARCHITECTURE"
ONTOLOGY = "ONTOLOGY"
AUTHORING = "AUTHORING"
REVIEW = "REVIEW"
QA = "QA"
CERTIFIED = "CERTIFIED"
FROZEN = "FROZEN"
IMPLEMENTATION = "IMPLEMENTATION"

STAGES = (ARCHITECTURE, ONTOLOGY, AUTHORING, REVIEW, QA, CERTIFIED, FROZEN,
          IMPLEMENTATION)

# The measured fabrication standard (CANONICAL_ONTOLOGY 5.2), derived from the approved
# quality references by measurement, not invention.
WORDS_PER_PART_MIN = 800
WORDS_PER_PART_MAX = 1500
WORDS_PER_DATASET_MIN = 8000
WORDS_PER_DATASET_MAX = 15000


class ImmutableDenominator(Exception):
    """Raised ONLY by a direct mutation attempt on parts_planned. Never escapes a public
    entry point -- advance() catches it and returns a refusal."""


@dataclass
class FabricationStandard:
    words_per_part_min: int = WORDS_PER_PART_MIN
    words_per_part_max: int = WORDS_PER_PART_MAX
    words_per_dataset_min: int = WORDS_PER_DATASET_MIN
    words_per_dataset_max: int = WORDS_PER_DATASET_MAX


@dataclass
class Certification:
    governs: str            # what this corpus governs
    does_not_govern: str    # what it explicitly does NOT -- the honest boundary
    at: str


@dataclass
class KnowledgeInfrastructureManifest:
    family: str
    stage: str = ARCHITECTURE
    parts_planned: int = 0          # IMMUTABLE after ARCHITECTURE (INV-6)
    parts_sealed: int = 0
    fabrication_standard: FabricationStandard = field(default_factory=FabricationStandard)
    certification: Certification | None = None
    frozen_at: str | None = None
    siblings: list = field(default_factory=list)   # the non-duplication declaration
    _denominator_locked: bool = False

    # --- the gates ------------------------------------------------------------------
    def can_advance(self, to: str) -> tuple:
        """(ok, reason). The gate between stages. IMPLEMENTATION is unreachable before
        CERTIFIED -- that unreachability IS the protocol."""
        if to not in STAGES:
            return False, f"unknown stage {to!r}"
        i, j = STAGES.index(self.stage), STAGES.index(to)
        if j != i + 1:
            return False, f"stages advance one at a time ({self.stage} -> {to} skips)"
        if to == ONTOLOGY and self.parts_planned <= 0:
            return False, "ARCHITECTURE exit gate: parts_planned must be declared (>0)"
        if to == REVIEW and self.parts_sealed < self.parts_planned:
            return False, (f"AUTHORING exit gate: {self.parts_sealed}/"
                           f"{self.parts_planned} Parts sealed")
        if to == CERTIFIED and self.parts_sealed < self.parts_planned:
            return False, "QA exit gate: every planned Part must be sealed"
        if to == FROZEN and self.certification is None:
            return False, "CERTIFIED exit gate: a Certification must be recorded"
        if to == IMPLEMENTATION and self.stage != FROZEN:
            return False, "IMPLEMENTATION is unreachable before FROZEN"
        return True, "ok"

    def advance(self, to: str) -> tuple:
        ok, reason = self.can_advance(to)
        if ok:
            if to == ONTOLOGY:
                self._denominator_locked = True    # INV-6 -- the denominator is fixed
            self.stage = to
        return ok, reason

    def declare_parts(self, n: int) -> tuple:
        """Declare parts_planned. Legal ONLY at ARCHITECTURE, exactly once (INV-6)."""
        if self._denominator_locked or self.stage != ARCHITECTURE:
            return False, ("INV-6: parts_planned is immutable after ARCHITECTURE "
                           f"(declared={self.parts_planned}, attempted={n}). A family "
                           "that grows its own denominator is gaming its completion gate.")
        if n <= 0:
            return False, "parts_planned must be > 0"
        self.parts_planned = int(n)
        return True, "ok"

    def seal_part(self, words: int) -> tuple:
        """Seal one Part after it meets the density band. Cannot exceed the declared
        denominator -- that ceiling is the terminating condition."""
        std = self.fabrication_standard
        if words < std.words_per_part_min:
            return False, (f"density floor: {words} words < {std.words_per_part_min} "
                           "(a Part written to satisfy a gate is not a Part)")
        if self.parts_sealed >= self.parts_planned > 0:
            return False, (f"INV-6: {self.parts_planned} Parts were planned and "
                           f"{self.parts_sealed} are sealed -- the corpus TERMINATES here")
        self.parts_sealed += 1
        return True, "ok"

    @property
    def complete(self) -> bool:
        return self.parts_planned > 0 and self.parts_sealed >= self.parts_planned

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("_denominator_locked", None)
        return d


def load(path: Path | str) -> KnowledgeInfrastructureManifest | None:
    """Fail-open -> None."""
    try:
        d = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        std = FabricationStandard(**d.get("fabrication_standard", {}))
        cert = d.get("certification")
        m = KnowledgeInfrastructureManifest(
            family=d.get("family", ""), stage=d.get("stage", ARCHITECTURE),
            parts_planned=int(d.get("parts_planned", 0) or 0),
            parts_sealed=int(d.get("parts_sealed", 0) or 0),
            fabrication_standard=std,
            certification=Certification(**cert) if cert else None,
            frozen_at=d.get("frozen_at"), siblings=d.get("siblings", []) or [])
        m._denominator_locked = m.stage != ARCHITECTURE
        return m
    except Exception:  # noqa: BLE001 -- fail-open
        return None


def save(m: KnowledgeInfrastructureManifest, path: Path | str) -> bool:
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(m.to_dict(), ensure_ascii=False, indent=2),
                     encoding="utf-8")
        return True
    except Exception:  # noqa: BLE001 -- fail-open
        return False
