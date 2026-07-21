"""Prompt Compiler (CCF component #3).

concept_config + Creative Specification -> {prompt, avoid_list}, per
vault/plans/CCF_ARCHITECTURE.md §3. Deterministic: identical input always
produces an identical prompt string and avoid_list -- verified by
`input_hash`, not asserted.

The `avoid_list.semantic` field is the direct fix for CCF-F01 (the Airbnb
Belo case): a purely named `avoid` list only catches explicitly-named marks.
This module additionally extracts a normalized, keyword-tagged description of
the icon's shape category from the same icon text, so a downstream scanner
(trademark_scanner.py) can catch an *unnamed* collision like "a continuous
rounded line that loops back on itself" resembling Airbnb's mark.
"""
from __future__ import annotations

import hashlib
import json

SHAPE_KEYWORDS = (
    "loop", "circle", "ring", "line", "curve", "stroke", "bubble", "arrow",
    "triangle", "square", "spiral", "wave", "dot", "star", "leaf", "petal",
    "blade", "knot", "swoosh", "bite", "check", "chevron",
)


def extract_semantic_avoid(icon_description: str) -> list:
    """Normalize an icon description into a semantic avoid signal.

    Returns [normalized_full_description, *matched_shape_keywords] -- the
    full text supports phrase-level similarity matching downstream, the
    keywords support fast tag-based matching. Never empty for non-blank input:
    the normalized description itself is always included.
    """
    normalized = " ".join((icon_description or "").lower().split())
    if not normalized:
        return []
    keywords = [kw for kw in SHAPE_KEYWORDS if kw in normalized]
    return [normalized] + keywords


def _stable_hash(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def compile_prompt(concept: dict, spec, global_fields: dict = None) -> dict:
    """Compile one concept_config + CreativeSpecification into a prompt record.

    `spec` may be a CreativeSpecification instance or a plain dict (both
    expose the same fields); only brand_name/industry/values are consulted,
    the same values fed for the same concept always yield the same prompt.
    """
    global_fields = global_fields or {}
    spec_dict = spec.to_dict() if hasattr(spec, "to_dict") else dict(spec)

    colours = concept["colours"]
    colours_text = ", ".join(colours) if isinstance(colours, list) else str(colours)

    parts = [
        f"Brand: {spec_dict.get('brand_name')}",
        f"Font: {concept['font']}",
        f"Colours: {colours_text}",
        f"Background: {concept['bg']}",
        f'Wordmark (spelled exactly): "{concept["wordmark"]}"',
        f"Icon concept: {concept['icon']}",
    ]
    named_avoid = list(concept.get("avoid") or [])
    if named_avoid:
        parts.append(f"Avoid resembling: {', '.join(named_avoid)}")
    for field_name in ("theme", "accent", "headFont"):
        value = global_fields.get(field_name)
        if value:
            parts.append(f"{field_name}: {value}")
    if global_fields.get("labels"):
        parts.append(f"Labels: {', '.join(global_fields['labels'])}")

    prompt = " | ".join(parts)
    semantic_avoid = extract_semantic_avoid(concept.get("icon", ""))

    record = {
        "concept_id": concept["id"],
        "prompt": prompt,
        "avoid_list": {"named": named_avoid, "semantic": semantic_avoid},
    }
    record["input_hash"] = _stable_hash({
        "concept": concept,
        "global_fields": global_fields,
        "spec": {k: spec_dict.get(k) for k in ("brand_name", "industry", "values")},
    })
    return record
