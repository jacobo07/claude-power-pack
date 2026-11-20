"""CDICF normalized component metadata, stack/a11y resolution and composition QA (BCAP-2 Phase 8, D21-D05/D06/D08). Pure.

Each check returns (ok, reasons). Unobserved attributes are UNKNOWN and never count as satisfied."""
from __future__ import annotations

UNKNOWN = "UNKNOWN"
KINDS = ("hero", "navbar", "cta", "pricing", "testimonials", "faq", "benefits", "bento", "cards", "tables", "dashboard",
         "forms", "modals", "icons", "charts", "backgrounds", "text_effects", "empty_error_states")
META_FIELDS = ("kind", "frameworks", "tailwind", "ssr_safe", "semantic_html", "keyboard_focus", "aria", "responsive",
               "rtl", "theme_modes", "reduced_motion")
A11Y = ("semantic_html", "keyboard_focus", "aria", "reduced_motion")


def validate_meta(m):
    why = []
    if (m or {}).get("kind") not in KINDS:
        why.append(f"meta: kind {(m or {}).get('kind')!r} not in the normalized set")
    why += [f"meta: {f} missing (use UNKNOWN)" for f in META_FIELDS[1:] if (m or {}).get(f) in (None, "", [])]
    return (not why), why


def resolve_stack(m, project):
    """D06: a component is usable only where its framework/tailwind/SSR/a11y are known and match; UNKNOWN is not a pass."""
    why = []
    if project.get("framework") not in (m.get("frameworks") or []):
        why.append(f"stack: framework {project.get('framework')} unsupported")
    if m.get("tailwind") in (None, UNKNOWN) or str(m["tailwind"]).split(".")[0] != str(project.get("tailwind")).split(".")[0]:
        why.append("stack: tailwind major version unknown or different")
    if project.get("ssr") and m.get("ssr_safe") is not True:
        why.append("stack: SSR/hydration safety not confirmed")
    why += [f"a11y: {a} not confirmed" for a in A11Y if m.get(a) is not True]
    if project.get("rtl") and m.get("rtl") is not True:
        why.append("a11y: RTL not confirmed")
    return (not why), why


def composition_qa(parts):
    """D08: parts = [{name, source, spacing_scale, type_scale, palette, z_index, button_variants, deps:{pkg:ver}, card}].
    Multi-source assembly must share tokens, avoid dep and z-index collisions, duplicate button variants, card soup."""
    why = []
    for key in ("spacing_scale", "type_scale", "palette"):
        if len({str(p.get(key)) for p in parts}) > 1:
            why.append(f"composition: {key} differs across sources")
    z = [p["z_index"] for p in parts if p.get("z_index") is not None]
    if len(z) != len(set(z)):
        why.append("composition: z-index collision")
    seen, dup = set(), set()
    for p in parts:
        for b in p.get("button_variants", []):
            (dup if b in seen else seen).add(b)
    if dup:
        why.append(f"composition: duplicate button variants {sorted(dup)}")
    vers = {}
    for p in parts:
        for pkg, v in (p.get("deps") or {}).items():
            vers.setdefault(pkg, set()).add(v)
    why += [f"composition: dependency {k} at conflicting versions {sorted(v)}" for k, v in vers.items() if len(v) > 1]
    if sum(1 for p in parts if p.get("card")) > 4 and sum(1 for p in parts if p.get("card")) > len(parts) / 2:
        why.append("composition: card soup")
    if len({p.get("project_design_md") for p in parts}) > 1:
        why.append("composition: more than one DESIGN.md source of truth")
    return (not why), why
