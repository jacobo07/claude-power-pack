"""CDICF reference record contracts (BCAP-2 Phase 8, D21-B01..B04). Pure validation, no network, no third-party content.

Each validator returns (ok, reasons). A record is a structured observation about a reference; none of them copies a
reference's assets. Unobserved attributes must be the literal UNKNOWN, never guessed. EXTENDS reference_intel."""
from __future__ import annotations

UNKNOWN = "UNKNOWN"
GALLERY_FIELDS = ("audience", "sector", "density", "typography", "editorial_hierarchy", "photography",
                  "structure", "motion_intensity", "conversion_layout", "differentiation", "era")
MOBILE_FIELDS = ("platform", "app_family", "navigation", "onboarding", "empty_state", "success_state", "error_state",
                 "touch_targets", "gestures")
COMPONENT_JOBS = ("name", "synonyms", "primary_job", "a11y_variants", "states", "related_systems")
STOP_CONDITIONS = ("exact_copy", "trademark_cloning", "template_cloning")


def _fields(rec, names, label):
    why = []
    for f in names:
        v = (rec or {}).get(f)
        if v in (None, "", [], {}):
            why.append(f"{label}: {f} missing (use UNKNOWN if unobserved)")
    return why


def validate_gallery_record(rec):
    """B01: every axis present or explicitly UNKNOWN; a trademark/template cloning intent is refused."""
    why = _fields(rec, GALLERY_FIELDS, "gallery")
    if (rec or {}).get("clone_intent"):
        why.append("gallery: trademark/template cloning is excluded")
    known = [f for f in GALLERY_FIELDS if (rec or {}).get(f) not in (None, "", UNKNOWN)]
    if not why and not known:
        why.append("gallery: every axis UNKNOWN, record carries no observation")
    return (not why), why


def validate_transform_trace(t):
    """B02: reference -> brief transform is traceable to a render evaluation and names its stop conditions."""
    why = _fields(t, ("reference_id", "brief_id", "render_evaluation"), "trace")
    stops = set((t or {}).get("stop_conditions") or [])
    why += [f"trace: stop condition {s} not declared" for s in STOP_CONDITIONS if s not in stops]
    if (t or {}).get("render_evaluation") and not (t or {}).get("render_evaluation_observed"):
        why.append("trace: render evaluation cited but not observed")
    return (not why), why


def validate_mobile_pattern(rec):
    """B03: licence/access verified first; mobile patterns feed CDIO-08 only."""
    why = []
    if (rec or {}).get("access_verified") is not True or (rec or {}).get("licence_verified") is not True:
        why.append("mobile: access and licence must be verified before cataloguing")
    why += _fields(rec, MOBILE_FIELDS, "mobile")
    if (rec or {}).get("feeds") not in (None, "CDIO-08"):
        why.append("mobile: patterns feed CDIO-08, not generic desktop rules")
    elif (rec or {}).get("feeds") is None:
        why.append("mobile: feeds missing (CDIO-08)")
    return (not why), why


def validate_component_entry(rec):
    """B04: taxonomy entry; gallery editorial choices are not standard mandates."""
    why = _fields(rec, COMPONENT_JOBS, "component")
    if (rec or {}).get("claims_official_standard"):
        why.append("component: gallery choices are not official standard mandates")
    return (not why), why
