"""Brand-kit readiness (CCF, BCAP2-07 / BI-05, BI-12..BI-13, BI-28).

Maps verified evidence onto the target state machine of the backlog WITHOUT renaming the historical
release enum (SEALED stays "a release record exists"). BRAND_KIT_READY is stronger: every visual
deliverable parses, the PDF depicts the selected mark, the mark survives 16px, and the asset was
generated from the concept as it is NOW. Anything unmeasured is REVIEW_REQUIRED, never READY.
"""
from __future__ import annotations

import hashlib
import json

from modules.ccf import asset_validator as av


def concept_sha(concept: dict) -> str:
    """Identity of a concept's generative inputs (BR-13): changes if icon/colours/font/wordmark/bg change."""
    keys = ("id", "font", "colours", "bg", "wordmark", "icon", "avoid")
    blob = json.dumps({k: concept.get(k) for k in keys}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def provenance(concept: dict, manifest_entry: dict):
    """(state, reason): MATCH | MISMATCH | UNRECORDED. A mismatch means the asset was generated from a
    different concept version than the one being packaged."""
    recorded = (manifest_entry or {}).get("concept_sha")
    if not recorded:
        return "UNRECORDED", "asset has no recorded concept_sha (legacy artifact)"
    if recorded != concept_sha(concept):
        return "MISMATCH", "concept definition changed after the asset was generated"
    return "MATCH", "asset was generated from this concept version"


def assess(png: bytes, pdf: bytes, concept: dict, manifest_entry: dict, extras: dict = None) -> dict:
    """Return {state, checks, reasons}. `extras` maps file name -> bytes for svg/ico deliverables
    that were actually produced (validated by their own parser). State is one of BLOCKED,
    REVIEW_REQUIRED, BRAND_KIT_READY."""
    checks, reasons = {}, []

    def rec(name, res):
        ok, why = res
        checks[name] = bool(ok)
        if not ok:
            reasons.append(f"{name}: {why}")

    rec("png_valid", av.validate_png(png))
    rec("pdf_depicts_mark", av.validate_kit_pdf(pdf, png))
    rec("small_size_16px", av.small_size_check(png))
    for name, data in sorted((extras or {}).items()):
        low = name.lower()
        if low.endswith(".svg"):
            rec(f"svg:{name}", av.validate_svg(data))
        elif low.endswith(".ico"):
            rec(f"ico:{name}", av.validate_ico(data))
        elif low.endswith(".png"):
            rec(f"png:{name}", av.validate_png(data))
    prov, why = provenance(concept, manifest_entry)
    checks["provenance_match"] = prov == "MATCH"
    if prov != "MATCH":
        reasons.append(f"provenance_{prov.lower()}: {why}")

    hard = [k for k in ("png_valid", "pdf_depicts_mark") if not checks[k]] + \
           [k for k, v in checks.items() if (k.startswith(("svg:", "ico:", "png:"))) and not v]
    if prov == "MISMATCH":
        hard.append("provenance_match")
    if hard:
        state = "BLOCKED"
    elif all(checks.values()):
        state = "BRAND_KIT_READY"
    else:
        state = "REVIEW_REQUIRED"
    return {"state": state, "checks": checks, "reasons": reasons}
