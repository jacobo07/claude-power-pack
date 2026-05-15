"""Contract layer — loads schema.json, exposes all canonical constants.

This is the schema-driven SSOT for the v1.2 distillation contract. Every
consumer (orchestrator, validator, FastAPI router, in-session /cpp-distill
engine) reads the same constants from here, so the contract surface has
exactly ONE source of truth.

Schema resolution order (first hit wins):
  1. `KPP_HOME` env var  →  `<KPP_HOME>/tools/distiller/schema.json`
  2. Package-relative    →  `<package_root>/../../tools/distiller/schema.json`
                            (works for `pip install -e` against a PP clone)
  3. Default home        →  `~/.claude/skills/claude-power-pack/tools/distiller/schema.json`

If none resolves, raises `FileNotFoundError` loudly with the search list —
zero silent drift.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Final

SCHEMA_VERSION: Final[str] = "1.2.1"


class SchemaResolutionError(FileNotFoundError):
    """Raised when schema.json cannot be located via any resolver."""


class SchemaVersionMismatch(RuntimeError):
    """Raised when the loaded schema's version does not match SCHEMA_VERSION."""


def _candidate_paths() -> list[Path]:
    candidates: list[Path] = []
    env = os.getenv("KPP_HOME")
    if env:
        candidates.append(Path(env) / "tools" / "distiller" / "schema.json")
    # `<package>/../../tools/distiller/schema.json`. With this file at
    # `<PP>/kpp-distiller-kernel/kpp_distiller_kernel/contract.py`,
    # `parents[2]` resolves to `<PP>` (= `parents[0]=kpp_distiller_kernel`,
    # `parents[1]=kpp-distiller-kernel`, `parents[2]=<PP>`).
    candidates.append(Path(__file__).resolve().parents[2] / "tools" / "distiller" / "schema.json")
    candidates.append(
        Path.home() / ".claude" / "skills" / "claude-power-pack" / "tools" / "distiller" / "schema.json"
    )
    return candidates


def _resolve_schema_path() -> Path:
    for p in _candidate_paths():
        if p.is_file():
            return p
    raise SchemaResolutionError(
        "kpp-distiller-kernel: schema.json not found. Searched:\n  "
        + "\n  ".join(str(p) for p in _candidate_paths())
        + "\nSet KPP_HOME or install the Power Pack at the default location."
    )


SCHEMA_PATH: Final[Path] = _resolve_schema_path()
_SCHEMA: Final[dict] = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

# Loud version check (G9 from v230000 audit).
_loaded_version = _SCHEMA.get("version")
if _loaded_version != SCHEMA_VERSION:
    raise SchemaVersionMismatch(
        f"schema.json version mismatch at {SCHEMA_PATH}: "
        f"loaded={_loaded_version!r} expected={SCHEMA_VERSION!r}. "
        "Either update SCHEMA_VERSION in this module or restore the canonical schema."
    )

# ---------------------------------------------------------------------------
# Canonical markers (verbatim from schema.json)
# ---------------------------------------------------------------------------

ROI_BLOCK_MARKER: Final[str] = _SCHEMA["required_section_blocks"]["roi_block"]["marker"]
CIERRE_MARKER: Final[str] = _SCHEMA["required_section_blocks"]["closing_marker"]
ORACLE_MARKER: Final[str] = _SCHEMA["required_section_blocks"]["oracle_aside"]
KILL_SWITCH_MARKER: Final[str] = _SCHEMA["kill_switch_marker"]
DATASET_FINAL_MARKER: Final[str] = _SCHEMA["dataset_final_marker"]
GAP_MARKER: Final[str] = "<<AWAITING OWNER VERBATIM — Q1.a>>"

TIER_END_MARKERS: Final[dict[int, str]] = {
    1: _SCHEMA["tier_layout"]["Tier_1"]["end_marker"],
    2: _SCHEMA["tier_layout"]["Tier_2"]["end_marker"],
    3: _SCHEMA["tier_layout"]["Tier_3"]["end_marker"],
}

TIER_SECTIONS: Final[dict[int, list[int]]] = {
    1: list(_SCHEMA["tier_layout"]["Tier_1"]["sections"]),
    2: list(_SCHEMA["tier_layout"]["Tier_2"]["sections"]),
    3: list(_SCHEMA["tier_layout"]["Tier_3"]["sections"]),
}

SECTION_TITLES: Final[dict[int, str]] = {
    int(k): v for k, v in _SCHEMA["section_titles"].items()
}

# ---------------------------------------------------------------------------
# Schema-derived predicates
# ---------------------------------------------------------------------------


def tier_of(section: int) -> int:
    """Return the tier number (1, 2, or 3) that owns this section."""
    for tier, secs in TIER_SECTIONS.items():
        if section in secs:
            return tier
    raise ValueError(f"Section {section} not in any tier")


def is_gap_section(section: int) -> bool:
    """True if this section is awaiting Owner-verbatim content.

    v1.2 schema is fully materialized — no title starts with the gap marker —
    so this predicate is False for every legal section. Retained as a
    tested invariant guard for future schema extensions.
    """
    return SECTION_TITLES.get(section, "").startswith("<<AWAITING")


REQUIRED_MARKERS_PER_SECTION: Final[list[str]] = [
    ROI_BLOCK_MARKER,
    CIERRE_MARKER,
    ORACLE_MARKER,
]


__all__ = [
    "SCHEMA_VERSION",
    "SCHEMA_PATH",
    "SchemaResolutionError",
    "SchemaVersionMismatch",
    "ROI_BLOCK_MARKER",
    "CIERRE_MARKER",
    "ORACLE_MARKER",
    "KILL_SWITCH_MARKER",
    "DATASET_FINAL_MARKER",
    "GAP_MARKER",
    "TIER_END_MARKERS",
    "TIER_SECTIONS",
    "SECTION_TITLES",
    "REQUIRED_MARKERS_PER_SECTION",
    "tier_of",
    "is_gap_section",
]
