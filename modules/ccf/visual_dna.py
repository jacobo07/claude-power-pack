"""Typed Visual DNA contract (BCAP2-07 / BI-12).

A versioned data contract for a selected identity. `validate` returns a list of problems (empty = valid);
it never repairs. It is a contract for compiling into DESIGN.md / tokens, not a second source of truth:
`tokens_for` derives tokens FROM the DNA and refuses when the project already pins a different value
(project SSOT wins, never forked).
"""
from __future__ import annotations

import re

VERSION = "1.0"
REQUIRED = ("brand_id", "approved_brief_ref", "territory", "symbol_strategy", "geometric_constraints",
            "shape_language", "relative_proportion", "palette_roles", "typography", "spacing", "variants",
            "forbidden_patterns", "avatar_rules", "small_size_rules", "applications", "selection_evidence")
POLICIES = ("photography_policy", "icon_policy", "motion_policy")
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def validate(dna: dict) -> list:
    p = []
    if not isinstance(dna, dict):
        return ["DNA must be an object"]
    if dna.get("schema_version") != VERSION:
        p.append(f"schema_version must be {VERSION!r}")
    for k in REQUIRED:
        if dna.get(k) in (None, "", [], {}):
            p.append(f"missing {k}")
    roles = dna.get("palette_roles")
    if isinstance(roles, dict):
        for r, v in roles.items():
            if not (isinstance(v, str) and HEX.match(v)):
                p.append(f"palette role {r!r} is not a #RRGGBB colour")
    t = dna.get("typography")
    if isinstance(t, dict) and not (t.get("family") and t.get("source")):
        p.append("typography needs family and source (font metadata)")
    ev = dna.get("selection_evidence")
    if isinstance(ev, dict) and not (ev.get("selected_by") and ev.get("critique_ref")):
        p.append("selection_evidence needs selected_by and critique_ref")
    for k in POLICIES:
        if k in dna and not isinstance(dna[k], dict):
            p.append(f"{k} must be an object or absent")
    return p


def tokens_for(dna: dict, project_tokens: dict) -> dict:
    """Colour tokens derived from the DNA. Raises ValueError if the DNA is invalid or if it would
    override a token the project already pins to a different value."""
    probs = validate(dna)
    if probs:
        raise ValueError("invalid Visual DNA: " + "; ".join(probs))
    out = {}
    for role, val in dna["palette_roles"].items():
        name = f"color.{role}"
        pinned = (project_tokens or {}).get(name)
        if pinned is not None and pinned.lower() != val.lower():
            raise ValueError(f"{name}: DNA {val} conflicts with project-pinned {pinned}; project SSOT wins")
        out[name] = pinned if pinned is not None else val
    return out
