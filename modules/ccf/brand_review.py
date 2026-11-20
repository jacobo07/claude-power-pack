"""Typed SVG parts, multilingual font coverage, logo review lens, benchmark set, independent review (BCAP2-07 / BI-17, 19, 28, 31, 35).
Pure. Builds on asset_validator (allowlist parse, font registry); adds no renderer, no provider call.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

from modules.ccf import asset_validator as AV

PARTS = ("icon", "wordmark", "combined")
LANGS = {  # characters that must be covered per language (diacritics are the failure mode)
    "ES": "áéíóúüñÁÉÍÓÚÜÑ¿¡", "PT": "ãõâêôçáéíóúÃÕÂÊÔÇ", "FR": "àâçéèêëîïôûùüÿœÀÂÇÉÈÊËÎÏÔÛÙÜŸŒ",
    "DE": "äöüßÄÖÜ", "EN": "",
}


def split_parts(svg: bytes) -> dict:
    """Typed parts via explicit data-part on top-level <g>; never regex over markup. Unsafe svg -> refused."""
    ok, why = AV.validate_svg(svg)
    if not ok:
        return {"ok": False, "why": why, "parts": {}}
    root = ET.fromstring(svg)
    found = {}
    for g in list(root):
        part = g.attrib.get("data-part")
        if part is None:
            continue
        if part not in PARTS:
            return {"ok": False, "why": f"unknown part {part!r}", "parts": {}}
        if part in found:
            return {"ok": False, "why": f"duplicate part {part!r}", "parts": {}}
        found[part] = ET.tostring(g)
    if not found:
        return {"ok": False, "why": "no typed parts (data-part) present", "parts": {}}
    return {"ok": True, "why": "typed", "parts": found}


def language_coverage(font_name: str, registry: dict, langs=("ES", "EN", "PT", "FR", "DE")) -> dict:
    entry = (registry or {}).get(font_name)
    if not entry:
        return {"ok": False, "why": "unregistered font (no silent substitution)", "missing": {}}
    glyphs = entry.get("glyphs", "")
    missing = {l: sorted({c for c in LANGS[l] if c not in glyphs}) for l in langs if l in LANGS}
    missing = {l: m for l, m in missing.items() if m}
    return {"ok": not missing, "why": "all requested languages covered" if not missing else "glyph gaps", "missing": missing}


LENS = ("spelling", "small_size", "silhouette", "negative_space", "monochrome", "dark_light", "print_web",
        "file_format", "font_glyph", "token_consumption", "provenance", "human_signoff")


def logo_lens(evidence: dict) -> dict:
    """Each criterion needs an observed entry {observed: bool, instrument: str}; absent = UNASSESSED, never pass.
    Scoped to logos: returns no UI Design Quality Score."""
    rows, fails, unassessed = {}, [], []
    for k in LENS:
        e = evidence.get(k)
        if not e or not e.get("instrument"):
            rows[k] = "UNASSESSED"; unassessed.append(k)
        elif e.get("observed") is True:
            rows[k] = "PASS"
        else:
            rows[k] = "FAIL"; fails.append(k)
    verdict = "BLOCK" if fails else ("INCOMPLETE" if unassessed else "APPROVE_PENDING_HUMAN")
    if verdict == "APPROVE_PENDING_HUMAN" and not (evidence.get("human_signoff") or {}).get("observed"):
        verdict = "INCOMPLETE"
    return {"verdict": verdict, "rows": rows, "fails": fails, "unassessed": unassessed, "ui_score": None}


CATEGORIES = ("creation", "refresh_keep", "icon_only", "wordmark", "multilingual", "fashion_luxury", "software",
              "hospitality", "professional_services", "consumer_product", "adversarial_imitation")


def check_benchmark(briefs: list) -> list:
    p = []
    if len(briefs) < 12:
        p.append(f"needs >= 12 briefs, got {len(briefs)}")
    ids = [b.get("id") for b in briefs]
    if len(set(ids)) != len(ids):
        p.append("duplicate brief ids")
    cov = {c for b in briefs for c in b.get("categories", [])}
    p += [f"category not covered: {c}" for c in CATEGORIES if c not in cov]
    for b in briefs:
        if not b.get("frozen_sha256"):
            p.append(f"brief {b.get('id')}: not frozen (no hash)")
    return p


def review_independent(review: dict) -> list:
    p = []
    if not review.get("reviewer") or review.get("reviewer") == review.get("implementer"):
        p.append("reviewer must be distinct from implementer")
    if not review.get("refusal_cases_proven"):
        p.append("no proof that gates refuse deliberately broken cases")
    for k in ("commit_refs", "test_counts", "revert_path"):
        if not review.get(k):
            p.append(f"missing {k}")
    if review.get("status") not in ("DONE", "NOT_DONE"):
        p.append("status must be DONE or NOT_DONE")
    return p
