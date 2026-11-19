"""CDICF motion selection record, motion semantics and runtime-verification contract (BCAP-2 Phase 8, D21-E05/E06/E07). Pure.

Each check returns (ok, reasons). Unmeasured values are None and never count as satisfied. Trendiness is not an input."""
from __future__ import annotations

OPTIONS = ("css_transition", "waapi", "motion_primitives", "anime_js", "bespoke_js", "no_animation")
CRITERIA = ("purpose", "platform", "input_model", "interruptible", "latency_ms", "frame_budget_ms", "bundle_bytes")
EXPRESSIVENESS = ("none", "restrained", "moderate", "high")
BUDGET = ("none", "low", "medium", "high")
MAX_BUDGET = {"none": "none", "restrained": "low", "moderate": "medium", "high": "high"}  # budget ceiling per expressiveness
LIBRARY_OPTIONS = ("motion_primitives", "anime_js", "bespoke_js")
RUNTIME_CASES = ("interrupted", "rapid_toggle", "unmount_while_active", "navigate_away", "resize_orientation_zoom",
                 "listener_cleanup", "concurrency", "nested_scroll", "touch", "keyboard", "reduced_motion", "fps_long_tasks")


def check_motion_decision(rec):
    """E05: a record picks one option from stated criteria; a library needs a reason the platform cannot do it; no_animation is valid."""
    why = []
    choice = rec.get("choice")
    if choice not in OPTIONS:
        return False, [f"decision: choice {choice!r} not in {OPTIONS}"]
    if choice == "no_animation":
        if not rec.get("purpose_absent_reason"):
            why.append("decision: no_animation needs the reason motion does not serve the purpose")
        return (not why), why
    crit = rec.get("criteria") or {}
    why += [f"decision: criterion {c} missing (use None only with unmeasured_reason)" for c in CRITERIA
            if c not in crit or (crit[c] in (None, "") and c not in (rec.get("unmeasured") or {}))]
    if choice in LIBRARY_OPTIONS and not rec.get("css_waapi_insufficient"):
        why.append("decision: a library or bespoke JS needs the stated reason CSS/WAAPI cannot meet the purpose")
    if rec.get("justification") in {"popular", "trending", "modern"} or set(rec.get("reasons", [])) & {"popular", "trending"}:
        why.append("decision: popularity is not a criterion")
    if not rec.get("baseline_no_motion_compared"):
        why.append("decision: no comparison against the no-motion baseline")
    if choice == "bespoke_js" and not rec.get("cleanup_plan"):
        why.append("decision: bespoke JS needs a cleanup plan")
    return (not why), why


def check_motion_semantics(c, anim):
    """E06: anim vs a CDIO-07 contract c ({expressiveness, motion_budget, reduced_motion}). anim = {level, purpose,
    reduced_motion_equivalent, fake_loading, progress_illusion, nondeterministic_state}."""
    why = []
    exp = c.get("expressiveness")
    if exp not in EXPRESSIVENESS or c.get("motion_budget") not in BUDGET:
        return False, ["semantics: contract expressiveness/motion_budget missing or invalid"]
    if BUDGET.index(c["motion_budget"]) > BUDGET.index(MAX_BUDGET[exp]):
        why.append(f"semantics: contract incoherent: budget {c['motion_budget']} above expressiveness {exp}")
    lvl = anim.get("level")
    if lvl not in BUDGET:
        why.append("semantics: animation level unmeasured")
    elif BUDGET.index(lvl) > BUDGET.index(c["motion_budget"]):
        why.append(f"semantics: level {lvl} exceeds declared budget {c['motion_budget']}")
    if lvl not in (None, "none") and exp == "none":
        why.append("semantics: expressiveness none permits no animation")
    if anim.get("reduced_motion_equivalent") is not True:
        why.append("semantics: reduced-motion equivalent not confirmed")
    for k, m in (("fake_loading", "fake loading"), ("progress_illusion", "progress illusion"),
                 ("nondeterministic_state", "non-deterministic state transition")):
        if anim.get(k) is not False:
            why.append(f"semantics: {m} not ruled out")
    return (not why), why


def check_runtime_report(rep):
    """E07: a runtime report must carry an observed result for every case; absent = unobserved, never pass."""
    res = (rep or {}).get("results") or {}
    why = []
    for k in RUNTIME_CASES:
        v = res.get(k)
        if v is None:
            why.append(f"runtime: {k} unobserved")
        elif v.get("observed") is not True or not v.get("evidence"):
            why.append(f"runtime: {k} has no observed evidence")
        elif v.get("pass") is not True:
            why.append(f"runtime: {k} failed")
    return (not why), why
