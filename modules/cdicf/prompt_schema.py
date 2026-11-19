"""CDICF prompt classification + DESIGN.md cross-source compatibility (BCAP-2 Phase 8, D21-C03/C04/C05). Pure, no network.

C03: a section/page prompt is classified into a job record with complete acceptance criteria; verbatim proprietary
prompt text is refused. C04: a prompt source's identity/content rights must be verified before method import.
C05: one canonical project truth (Google DESIGN.md format); every other source maps through a derivative, reversible
transform or is declared lossy. Returns (ok, reasons)."""
from __future__ import annotations

PROMPT_FIELDS = ("target_job", "audience", "data_dependencies", "accessibility", "motion_budget", "visual_family",
                 "acceptance_criteria")
CATEGORIES = ("hero", "pricing", "benefits", "bento", "dashboard", "navigation", "walkthrough")
CANONICAL = "google-design-md"
SOURCES = ("google-design-md", "refero", "designmd.ai", "jiro", "vibeprompt", "cpp-template")


def classify_prompt(rec):
    why = [f"prompt: {f} missing" for f in PROMPT_FIELDS if (rec or {}).get(f) in (None, "", [], {})]
    if (rec or {}).get("verbatim_text"):
        why.append("prompt: verbatim proprietary prompt text must not be stored")
    ac = (rec or {}).get("acceptance_criteria")
    if isinstance(ac, list) and any(not str(c).strip() for c in ac):
        why.append("prompt: acceptance criterion is blank")
    return (not why), why


def vibeprompt_import_allowed(src):
    """C04: identity and content rights verified first, and only compatible categories map."""
    why = []
    if (src or {}).get("identity_verified") is not True:
        why.append("vibeprompt: site identity not verified")
    if (src or {}).get("content_rights") != "AUTHORIZED":
        why.append("vibeprompt: content rights not AUTHORIZED, method import refused")
    bad = [c for c in (src or {}).get("categories", []) if c not in CATEGORIES]
    why += [f"vibeprompt: category {c} not in compatible set" for c in bad]
    return (not why), why


def validate_matrix(matrix):
    """C05: matrix = {source: {"maps_to_canonical": bool, "reversible": bool, "lossy_fields": [..]}}. Every known source is
    present, only the canonical source is the truth, a non-reversible mapping must name its lossy fields."""
    why = [f"matrix: source {s} absent" for s in SOURCES if s not in (matrix or {})]
    for s, row in (matrix or {}).items():
        if s == CANONICAL:
            if row.get("maps_to_canonical") is not True:
                why.append("matrix: canonical source must map to itself")
            continue
        if row.get("canonical"):
            why.append(f"matrix: {s} claims to be canonical, one project truth only")
        if row.get("reversible") is False and not row.get("lossy_fields"):
            why.append(f"matrix: {s} is not reversible but names no lossy fields")
    return (not why), why
