"""ROI parser — pre-emit gate #2.

Parses the canonical `🧮 Calculadora de ROI` block (5 fields, per
`tools/distiller/schema.json#required_section_blocks.roi_block`) from a Tier
artifact's Markdown body and returns a typed ROICalc. If the block is
missing or malformed, raises ROIParseError.

Canonical fields in the block:
  Tipo            — Temporal / Patrimonial / Riesgo / Soberanía / Escalabilidad
  ROI Temporal    — multiplier (e.g. `50×–100×`); the low end is stored numeric
  ROI Riesgo      — Crítico / Alto / Moderado / Bajo  → stored in ROICalc.risk_roi
  Escenario       — Conservador / Realista / Agresivo
  Explicación     — free-form 1-3 sentences  → stored in ROICalc.explanation

Both the `ROICalc` Pydantic model AND the parser live here so the contract
travels as one unit (avoids the prior split between `data_contracts/roi_calc.py`
and `kernel/roi_calculator.py`).
"""

from __future__ import annotations

import re
from typing import Final, Literal, cast

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# ROICalc contract
# ---------------------------------------------------------------------------

ROIType = Literal["temporal", "economico", "patrimonial", "riesgo", "escalabilidad", "soberania"]
Scenario = Literal["conservador", "realista", "agresivo"]


class ROICalc(BaseModel):
    """Quantified ROI for a distilled artifact.

    The orchestrator extracts these fields from the LLM output by parsing the
    mandatory `🧮 Calculadora de ROI` block emitted in every Tier artifact.
    """

    tipo: ROIType = Field(description="Primary ROI category")
    multiplicador: float = Field(ge=0.0, description="Numeric multiplier (e.g., 50.0 means 50x)")
    escenario: Scenario = Field(description="ROI scenario assumed")
    explanation: str = Field(min_length=10, description="One-line justification")
    risk_roi: str | None = Field(default=None, description="Risk axis qualifier")


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

ROI_HEADER: Final[str] = "🧮 Calculadora de ROI"

_TIPO_VALID = {"temporal", "economico", "patrimonial", "riesgo", "escalabilidad", "soberania"}
_ESCENARIO_VALID = {"conservador", "realista", "agresivo"}


class ROIParseError(ValueError):
    """Raised when an artifact body cannot yield a valid ROICalc."""


def _strip_accents_lower(s: str) -> str:
    """Cheap accent-fold (económico -> economico) + lowercase + strip."""
    table = str.maketrans("áéíóúÁÉÍÓÚñÑ", "aeiouAEIOUnN")
    return s.translate(table).lower().strip()


def _extract_field(block: str, key: str) -> str | None:
    """Find a `* **Key:** value`, `* Key:` or bare `Key:` line in the block."""
    pattern = rf"(?im)^\s*[*+\-]?\s*\*?\*?{re.escape(key)}\*?\*?\s*:\s*(.+?)\s*$"
    m = re.search(pattern, block)
    return m.group(1).strip().rstrip("*").strip() if m else None


_ROI_BLOCK_WINDOW: Final[int] = 1500


def parse(artifact_body: str) -> ROICalc:
    """Extract a ROICalc from the body's `🧮 Calculadora de ROI` block."""
    idx = artifact_body.find(ROI_HEADER)
    if idx == -1:
        raise ROIParseError(f"Missing '{ROI_HEADER}' block in artifact body")

    block = artifact_body[idx : idx + _ROI_BLOCK_WINDOW]

    tipo_raw = _extract_field(block, "Tipo")
    mult_raw = _extract_field(block, "ROI Temporal")
    risk_raw = _extract_field(block, "ROI Riesgo")
    esc_raw = _extract_field(block, "Escenario")
    just_raw = _extract_field(block, "Explicación") or _extract_field(block, "Explicacion")

    if not all([tipo_raw, mult_raw, risk_raw, esc_raw, just_raw]):
        missing = [
            name
            for name, val in [
                ("Tipo", tipo_raw),
                ("ROI Temporal", mult_raw),
                ("ROI Riesgo", risk_raw),
                ("Escenario", esc_raw),
                ("Explicación", just_raw),
            ]
            if not val
        ]
        raise ROIParseError(f"ROI block missing required fields: {missing}")

    tipo_norm = _strip_accents_lower(tipo_raw)
    if tipo_norm not in _TIPO_VALID:
        raise ROIParseError(f"Invalid ROI tipo: {tipo_raw!r} (allowed: {sorted(_TIPO_VALID)})")

    esc_norm = _strip_accents_lower(esc_raw)
    if esc_norm not in _ESCENARIO_VALID:
        raise ROIParseError(f"Invalid ROI escenario: {esc_raw!r} (allowed: {sorted(_ESCENARIO_VALID)})")

    # ROI Temporal may be numeric ("50", "50×", "50-100"), "Crítico positivo",
    # "Permanente", "Diferido", etc. Numeric parsing first; falls back to 0.0
    # for qualitative labels so the kernel doesn't reject narrative ROI values.
    mult_clean = mult_raw.replace("×", "").replace("x", "").replace("X", "")
    range_match = re.match(r"^\s*([0-9]+(?:[.,][0-9]+)?)\s*[-–—]\s*([0-9]+(?:[.,][0-9]+)?)", mult_clean)
    if range_match:
        mult_value = float(range_match.group(1).replace(",", "."))
    else:
        num_match = re.match(r"^\s*([0-9]+(?:[.,][0-9]+)?)", mult_clean)
        mult_value = float(num_match.group(1).replace(",", ".")) if num_match else 0.0

    return ROICalc(
        tipo=cast(ROIType, tipo_norm),
        multiplicador=mult_value,
        escenario=cast(Scenario, esc_norm),
        explanation=just_raw,
        risk_roi=risk_raw,
    )


def is_present(artifact_body: str) -> bool:
    """True if the canonical ROI header appears in the body."""
    return ROI_HEADER in artifact_body


__all__ = [
    "ROIType",
    "Scenario",
    "ROICalc",
    "ROIParseError",
    "ROI_HEADER",
    "parse",
    "is_present",
]
