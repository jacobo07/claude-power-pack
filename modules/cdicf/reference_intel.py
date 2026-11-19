"""CDICF reference intelligence (BCAP-2 Phase 8, Workstreams B/C slice). Pure logic, no network.

Covers D21-B05 (reference retrieval ranking with licence filter, diversity guard and ABSTAIN), D21-B06 (design-decision
brief required before synthesis), D21-C06 / V-D21-12 (observed token vs inferred vs UNKNOWN, never invented),
V-D21-13 (the project's approved DESIGN.md wins over an imported reference) and V-D21-18 (motion budget NONE => ABSTAIN).
EXTENDS modules/cdicf/source_intake (rights) and modules/design-md (project SSOT); it is not a second registry.
"""
from __future__ import annotations

from modules.cdicf.source_intake import admit_code

OBSERVED, INFERRED, UNKNOWN = "OBSERVED", "INFERRED", "UNKNOWN"
TOKEN_KINDS = ("color", "font", "radius", "spacing", "size")
BRIEF_FIELDS = ("source", "transferable", "forbidden_copy", "differs_by", "test_plan")


def _tok(value, evidence):
    """One design token. A value without evidence is UNKNOWN: the value is dropped, never carried as if observed."""
    if value is None or value == "":
        return {"value": None, "level": UNKNOWN}
    if evidence in (OBSERVED, INFERRED):
        return {"value": value, "level": evidence}
    return {"value": None, "level": UNKNOWN, "dropped": "value had no evidence level"}


def extract_tokens(reference: dict) -> dict:
    """reference = {kind: {"value": v, "evidence": "OBSERVED"|"INFERRED"|None}}. Absent kinds are UNKNOWN, not defaulted."""
    given = reference.get("tokens", {})
    out = {}
    for kind in TOKEN_KINDS:
        t = given.get(kind) or {}
        out[kind] = _tok(t.get("value"), t.get("evidence"))
    return out


def merge_into_project(project_tokens: dict, imported: dict) -> dict:
    """The approved project contract wins. Imported values only fill kinds the project leaves empty and only if OBSERVED
    or INFERRED; every conflict is reported, never silently applied."""
    merged, conflicts = {}, []
    for kind in TOKEN_KINDS:
        mine, theirs = project_tokens.get(kind), imported.get(kind, {"level": UNKNOWN, "value": None})
        if mine is not None:
            merged[kind] = mine
            if theirs["level"] != UNKNOWN and theirs["value"] != mine:
                conflicts.append({"kind": kind, "kept": mine, "rejected": theirs["value"]})
        elif theirs["level"] != UNKNOWN:
            merged[kind] = theirs["value"]
        else:
            merged[kind] = None
    return {"tokens": merged, "conflicts": conflicts}


def validate_brief(brief: dict):
    """D21-B06: no synthesis without a decision brief. Returns (ok, reasons)."""
    why = [f"missing {f}" for f in BRIEF_FIELDS if not (brief or {}).get(f)]
    if brief and brief.get("transferable") and brief.get("forbidden_copy") is not None and not brief["forbidden_copy"]:
        why.append("forbidden_copy empty: a brief that forbids nothing does not guard against cloning")
    if brief and brief.get("source") and brief.get("differs_by") and brief["differs_by"] == brief["source"]:
        why.append("result is declared identical to the source")
    return (not why), why


def rank(query: dict, catalog: list, k: int = 3, floor: float = 0.34):
    """D21-B05. query = {purpose, platform, sector?, motion_budget?}. catalog items = {id, purpose, platform, sector, era?,
    source_rights, license_evidence?, motion?}. Returns {"verdict": "RANKED"|"ABSTAIN", "picks": [...], "reason"}.
    Filters: licence (admit_code on the item's source), platform mismatch, motion budget NONE. Diversity: at most one
    pick per (sector, era) so the top-k are not near-duplicates."""
    if (query.get("motion_budget") or "").upper() == "NONE" and query.get("want_motion"):
        return {"verdict": "ABSTAIN", "picks": [], "reason": "motion budget NONE: no effect proposed"}
    scored = []
    for it in catalog:
        if it.get("platform") != query.get("platform"):
            continue
        ok, _ = admit_code({"rights_status": it.get("source_rights")}, it.get("license_evidence")) if query.get("need_code") \
            else (True, "")
        if not ok:
            continue
        s = 0.0
        s += 0.5 if it.get("purpose") == query.get("purpose") else 0.0
        s += 0.3 if query.get("sector") and it.get("sector") == query.get("sector") else 0.0
        s += 0.2  # platform matched
        scored.append((s, it))
    scored.sort(key=lambda p: (-p[0], p[1]["id"]))
    picks, seen = [], set()
    for s, it in scored:
        if s < floor:
            break
        key = (it.get("sector"), it.get("era"))
        if key in seen:
            continue
        seen.add(key)
        picks.append({"id": it["id"], "score": round(s, 2)})
        if len(picks) == k:
            break
    if not picks:
        return {"verdict": "ABSTAIN", "picks": [], "reason": "no reference matched purpose/platform/licence above the floor"}
    return {"verdict": "RANKED", "picks": picks, "reason": ""}
