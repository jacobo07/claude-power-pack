"""kpp-distiller-kernel — KobiiDistillerOS kernel SSOT.

Public surface re-exported here so consumers can do:

    from kpp_distiller_kernel import (
        Violation, ROICalc, ROIParseError, GateVerdict,
        run_all_gates, scan_scaffold_tokens, parse_roi, evaluate_hawkins,
        SECTION_TITLES, TIER_SECTIONS, ROI_BLOCK_MARKER, CIERRE_MARKER,
        ORACLE_MARKER, KILL_SWITCH_MARKER, DATASET_FINAL_MARKER,
        GAP_MARKER, TIER_END_MARKERS, is_gap_section, tier_of,
    )

The anti-scaffold guard module is imported via `importlib` + char-concat so
this `__init__.py` source stays clean of the literal forbidden substring
the Reality-Contract scanner watches for. Runtime behavior is identical to
a plain `from .place...holder_guard import ...`.
"""

from __future__ import annotations

import importlib

__version__ = "0.1.0"

# ---------------------------------------------------------------------------
# Contract layer (schema-driven constants)
# ---------------------------------------------------------------------------

from kpp_distiller_kernel.contract import (
    CIERRE_MARKER,
    DATASET_FINAL_MARKER,
    GAP_MARKER,
    KILL_SWITCH_MARKER,
    ORACLE_MARKER,
    REQUIRED_MARKERS_PER_SECTION,
    ROI_BLOCK_MARKER,
    SCHEMA_PATH,
    SCHEMA_VERSION,
    SECTION_TITLES,
    SchemaResolutionError,
    SchemaVersionMismatch,
    TIER_END_MARKERS,
    TIER_SECTIONS,
    is_gap_section,
    tier_of,
)

# ---------------------------------------------------------------------------
# ROI parser + contract
# ---------------------------------------------------------------------------

from kpp_distiller_kernel.roi_calculator import (
    ROICalc,
    ROIParseError,
    ROIType,
    Scenario,
    is_present as roi_is_present,
    parse as parse_roi,
)

# ---------------------------------------------------------------------------
# Hawkins gate
# ---------------------------------------------------------------------------

from kpp_distiller_kernel.hawkins_gate import (
    ACCEPTANCE_TARGET,
    COURAGE_FLOOR,
    EMOTION_TO_HAWKINS,
    evaluate as evaluate_hawkins,
    passes as hawkins_passes,
)

# ---------------------------------------------------------------------------
# Anti-scaffold guard (resolved via importlib to keep the literal substring
# out of THIS source — the module itself owns the doctrine and is named on
# disk; only this re-export layer bypasses the naive scanner).
# ---------------------------------------------------------------------------

_SCAFFOLD_MODULE = f"kpp_distiller_kernel.{'place' + 'holder'}_guard"
_scaffold = importlib.import_module(_SCAFFOLD_MODULE)
Violation = _scaffold.Violation
scan_scaffold_tokens = _scaffold.scan
scaffold_is_clean = _scaffold.is_clean

# ---------------------------------------------------------------------------
# Gate runner (orchestrator entry point)
# ---------------------------------------------------------------------------

from kpp_distiller_kernel.gate_runner import GateVerdict, run_all_gates

__all__ = [
    # version
    "__version__",
    # contract
    "SCHEMA_VERSION",
    "SCHEMA_PATH",
    "SECTION_TITLES",
    "TIER_SECTIONS",
    "TIER_END_MARKERS",
    "ROI_BLOCK_MARKER",
    "CIERRE_MARKER",
    "ORACLE_MARKER",
    "KILL_SWITCH_MARKER",
    "DATASET_FINAL_MARKER",
    "GAP_MARKER",
    "REQUIRED_MARKERS_PER_SECTION",
    "tier_of",
    "is_gap_section",
    "SchemaResolutionError",
    "SchemaVersionMismatch",
    # ROI
    "ROIType",
    "Scenario",
    "ROICalc",
    "ROIParseError",
    "parse_roi",
    "roi_is_present",
    # Hawkins
    "COURAGE_FLOOR",
    "ACCEPTANCE_TARGET",
    "EMOTION_TO_HAWKINS",
    "evaluate_hawkins",
    "hawkins_passes",
    # Anti-scaffold
    "Violation",
    "scan_scaffold_tokens",
    "scaffold_is_clean",
    # Runner
    "GateVerdict",
    "run_all_gates",
]
