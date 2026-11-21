"""CDICF scenario guards for the BCAP-2 Phase 8 failure table (V-D21-19/20/21/22/23/26/27/30/34). Pure, no network, no install.

Each guard returns (ok, reasons). Unobserved input is never a pass. Scenarios whose owner already existed
(08/14/15/16/17/28/29/32/33/35) are driven in tools/test_bcap2_d21_bc.py against component_install, component_meta,
motion_select, reference_records and source_route, not re-implemented here."""
from __future__ import annotations

# existing owners for a feature: a new local engine is an overlap, not a feature (V-D21-19)
OWNERS = {"motion": "Anime.js backlog (animejs/REUSE_LEDGER.md)", "design_contract": "modules/design-md",
          "components": "modules/cdicf/component_install"}


def ownership_overlap(feature: str, proposed_owner: str, owners: dict = None):
    owners = OWNERS if owners is None else owners
    held = owners.get(feature)
    if held and proposed_owner not in (held, "reuse", "extend:" + held):
        return False, [f"overlap: {feature} is owned by {held}; a new local {proposed_owner!r} must reuse or extend it"]
    return True, []


# basemap/tile providers whose free tier forbids commercial use without a grant (V-D21-20)
RESTRICTED_TILES = {"carto": "CARTO basemaps need a commercial grant", "google": "Google tiles need an API agreement"}


def tile_license_gate(provider: str, commercial: bool, grant: str = None, alternates: list = None):
    why = []
    note = RESTRICTED_TILES.get((provider or "").lower())
    if note and commercial and not grant:
        why.append(f"tiles: {note}")
        if not alternates:
            why.append("tiles: no alternate provider considered")
    return (not why), why


# map/location controls (V-D21-21)
def location_authorization(ctrl: dict):
    why = []
    if ctrl.get("reads_location") and ctrl.get("permission_prompt") is not True:
        why.append("privacy: location read without an explicit permission prompt")
    if ctrl.get("reads_location") and ctrl.get("user_gesture") is not True:
        why.append("privacy: location read not triggered by a user gesture")
    if ctrl.get("reads_location") and ctrl.get("denied_path") is not True:
        why.append("privacy: no behaviour defined for a denied permission")
    return (not why), why


# WebGL / glass (V-D21-22)
def glass_plan(env: dict, fallback: dict):
    """env = {webgl: bool|None, mobile: bool, cost_ms: float|None}; the glass layer is allowed only when observed cheap."""
    why = []
    if env.get("webgl") is None or env.get("cost_ms") is None:
        why.append("glass: capability or cost unmeasured, not assumed available")
    elif env["webgl"] is not True or (env.get("mobile") and env["cost_ms"] > env.get("mobile_budget_ms", 16)):
        why.append("glass: unavailable or over the mobile budget")
    use_glass = not why
    if not use_glass and (fallback or {}).get("core_ui_functions") is not True:
        return {"use_glass": False, "ok": False, "reasons": why + ["glass: no safe no-glass fallback keeps the core UI working"]}
    return {"use_glass": use_glass, "ok": True, "reasons": why}


def _lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _lum(rgb):
    r, g, b = (_lin(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a, b):
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def glass_readability(text_rgb, bg_samples, minimum: float = 4.5):
    """V-D21-23: text over a complex background must clear WCAG contrast at the WORST sampled point; no samples = unmeasured."""
    if not bg_samples:
        return False, ["readability: no background samples measured"]
    worst = min(contrast_ratio(text_rgb, s) for s in bg_samples)
    return (worst >= minimum), ([] if worst >= minimum else [f"readability: worst-sample contrast {worst:.2f} < {minimum}"])


def perf_budget(measured: dict, budget: dict, fallback_named: bool):
    """V-D21-26: heavy assets are judged on measured LCP/CLS/frame time; unmeasured fails and a fallback must exist."""
    why = []
    for k, lim in budget.items():
        v = (measured or {}).get(k)
        if v is None:
            why.append(f"perf: {k} unmeasured")
        elif v > lim:
            why.append(f"perf: {k} {v} over budget {lim}")
    if why and not fallback_named:
        why.append("perf: no simpler fallback named")
    return (not why), why


def premium_claim(claim: str, evidence: dict):
    """V-D21-27: 'premium' / 'high quality' promotes nothing without a measured instrument result."""
    low = (claim or "").lower()
    if not any(w in low for w in ("premium", "luxury", "high-end", "polished")):
        return True, []
    ok = bool(evidence) and evidence.get("instrument") and evidence.get("value") is not None
    return bool(ok), ([] if ok else ["quality: premium claim has no instrument-backed measurement; no CDIO promotion"])


def cross_state(screens: dict, required=("forms", "mobile", "rtl")):
    """V-D21-30: a better static screenshot cannot pass while a required state is broken or unobserved."""
    why = [f"state: {s} unobserved" if screens.get(s) is None else f"state: {s} broken" for s in required if screens.get(s) is not True]
    return (not why), why


TIERS = ("HYPOTHESIS", "RESEARCH", "TESTED", "PROVEN")


def evidence_tier(claimed: str, sources: list):
    """V-D21-34: a social post or marketing page can support at most HYPOTHESIS; TESTED/PROVEN need a real test result."""
    real = [s for s in sources if s.get("kind") == "test" and s.get("observed") is True]
    cap = "PROVEN" if real else ("RESEARCH" if any(s.get("kind") == "paper" for s in sources) else "HYPOTHESIS")
    ok = TIERS.index(claimed) <= TIERS.index(cap)
    return ok, ([] if ok else [f"evidence: claimed {claimed} but sources support at most {cap}"])
