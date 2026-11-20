"""CDICF source-discovery routing, explainable selection and material arbitration (BCAP-2 Phase 8, D21-H01/H02/F06). Pure.

Reuses source_intake.admit_code for rights. Does not hold a catalogue: callers pass the index they already own."""
from __future__ import annotations

from modules.cdicf.source_intake import admit_code

LAYERS = ("reference", "design_contract", "component", "motion", "map", "material", "art")
_HINTS = {"reference": ("inspiration", "reference", "moodboard", "gallery"), "design_contract": ("design.md", "tokens", "contract"),
          "component": ("hero", "navbar", "pricing", "button", "form", "component", "card"),
          "motion": ("animation", "animate", "spring", "transition", "micro"), "map": ("map", "route", "marker", "geolocation"),
          "material": ("glass", "blur", "gradient", "depth", "texture"), "art": ("illustration", "icon", "3d", "artwork", "mascot")}
MATERIALS = ("glass", "depth", "gradient", "micro_motion")
_BENEFITS = ("hierarchy", "trust", "differentiation", "accessibility")


def infer_layers(goal):
    """H01: layers a goal touches, from explicit words only. No match = no layer (caller must ABSTAIN), never a default."""
    g = (goal or "").lower()
    return [l for l in LAYERS if any(h in g for h in _HINTS[l])]


def route(goal, index):
    """index = [{id, layer, rights_status, evidence?, summary, sources:[...]}]. Returns verdict + grounded rows or ABSTAIN with the reason."""
    layers = infer_layers(goal)
    if not layers:
        return {"verdict": "ABSTAIN", "reason": "no layer inferable from the goal", "rows": []}
    rows = [i for i in index if i.get("layer") in layers and i.get("sources")]
    if not rows:
        return {"verdict": "ABSTAIN", "reason": f"no grounded index entry for layers {layers}", "layers": layers, "rows": []}
    return {"verdict": "ROUTED", "layers": layers, "rows": sorted(rows, key=lambda r: r["id"])}


def select(candidates, project):
    """H02: licensing first, then compatibility, then measured cost; popularity is never read. Deterministic for equal input
    (ties break on id). Every verdict carries its reason. candidates = [{id, rights_status, evidence, frameworks, bundle_bytes, popularity}]."""
    out = []
    for c in sorted(candidates, key=lambda x: x["id"]):
        ok, why = admit_code({"rights_status": c.get("rights_status")}, c.get("evidence"))
        if not ok:
            out.append({"id": c["id"], "verdict": "REFUSED", "reason": "licence: " + why}); continue
        if project.get("framework") not in (c.get("frameworks") or []):
            out.append({"id": c["id"], "verdict": "REFUSED", "reason": "incompatible framework"}); continue
        out.append({"id": c["id"], "verdict": "ELIGIBLE", "reason": why, "cost": c.get("bundle_bytes")})
    elig = [o for o in out if o["verdict"] == "ELIGIBLE"]
    # unmeasured cost sorts last and is flagged, never treated as zero
    elig.sort(key=lambda o: (o["cost"] is None, o["cost"] if o["cost"] is not None else 0, o["id"]))
    return {"ranked": elig, "refused": [o for o in out if o["verdict"] == "REFUSED"],
            "unmeasured_cost": [o["id"] for o in elig if o["cost"] is None]}


def arbitrate_material(m):
    """F06: a material is justified only by a stated benefit, a safe no-feature fallback and no trust-critical conflict.
    m = {material, benefits:[...], baseline_opaque_compared, fallback, trust_posture}. Simpler opaque UI wins by default."""
    why = []
    if m.get("material") not in MATERIALS:
        return False, [f"material {m.get('material')!r} not in {MATERIALS}"]
    good = [b for b in m.get("benefits", []) if b in _BENEFITS]
    if not good:
        why.append("material: no stated benefit among hierarchy/trust/differentiation/accessibility")
    if m.get("baseline_opaque_compared") is not True:
        why.append("material: not compared against the simpler opaque baseline")
    if not m.get("fallback"):
        why.append("material: no safe no-feature fallback")
    if m.get("trust_posture") == "critical" and m["material"] in ("glass", "micro_motion"):
        why.append("material: trust-critical surface refuses glass/micro-motion by default")
    return (not why), why
