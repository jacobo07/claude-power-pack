"""Dataset First Protocol (DFP) -- the Knowledge-Necessity axis of Claude Power Pack.

Governs one question no sibling answers: does the institutional science that must govern
this build exist yet, and what does it cost to demand it when it does not?

  classifier.classify(description)        -> ProjectClassification
  knowledge_sufficiency.evaluate(desc)    -> KnowledgeSufficiencyVerdict
  necessity_record.record(...)            -> DatasetNecessityRecord  (append-only)
  manifest.KnowledgeInfrastructureManifest -> the 8-stage corpus lifecycle
  calibrator.calibrate()                  -> ProtocolCalibrationRecord (can retire the family)

Composes DRK (decisions), ACIS (epistemic levels), D2A (duplicates), spec_gate (tiers).
Forks none of them. Fail-open absolutely: DFP is an advisor wired into an authority, never
an authority itself, and it never blocks on its own account (INV-5).
"""
from modules.dataset_first.knowledge_sufficiency import (
    DATASET_FIRST_MANDATORY,
    DIRECT_IMPLEMENTATION,
    EXPERIMENT_FIRST,
    HYBRID,
    KNOWLEDGE_TYPES,
    PROJECT_CLASSES,
    KnowledgeSufficiencyVerdict,
    evaluate,
)
from modules.dataset_first.classifier import ProjectClassification, Signal, classify
from modules.dataset_first.necessity_record import (
    DatasetNecessityRecord,
    Outcome,
    Override,
    Prediction,
    admissible,
    read_all,
    record,
)
from modules.dataset_first.manifest import (
    STAGES,
    Certification,
    KnowledgeInfrastructureManifest,
)
from modules.dataset_first.calibrator import (
    ProtocolCalibrationRecord,
    calibrate,
    thresholds,
)

__all__ = [
    "DATASET_FIRST_MANDATORY", "DIRECT_IMPLEMENTATION", "EXPERIMENT_FIRST", "HYBRID",
    "PROJECT_CLASSES", "KNOWLEDGE_TYPES",
    "KnowledgeSufficiencyVerdict", "evaluate",
    "ProjectClassification", "Signal", "classify",
    "DatasetNecessityRecord", "Prediction", "Outcome", "Override",
    "record", "read_all", "admissible",
    "KnowledgeInfrastructureManifest", "Certification", "STAGES",
    "ProtocolCalibrationRecord", "calibrate", "thresholds",
]
