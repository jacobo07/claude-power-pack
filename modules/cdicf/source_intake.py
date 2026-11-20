"""CDICF source intake (BCAP-2 Phase 8, Workstream A gate): the 21 design-resource sources as typed records, and the
rights gate that decides what may become code/assets in CPP. Pure logic, no network.

Principles (backlog 2026-10-30 section 2): visibility is not a licence; the component/item-level licence is authoritative;
absent access is UNKNOWN_ACCESS, never an invented term; marketing counts are never gate denominators; a coverage pass
cannot be manufactured by shrinking the corpus. EXTENDS modules/cdicf (and lib/license_gate.js for on-disk licence tiers);
it is NOT a second registry: component selection stays in selector.js.
"""
from __future__ import annotations

import json
import os

from modules.ccf.asset_validator import license_conflict

REQUIRED_IDS = tuple(f"D21-{i:02d}" for i in range(1, 22))  # non-shrinking denominator, pinned in code
RIGHTS = ("OPEN_PERMISSIVE", "RESTRICTED", "REFERENCE_ONLY", "MIXED", "UNKNOWN", "UNKNOWN_ACCESS")
PERMISSIVE = {"MIT", "Apache-2.0", "BSD", "ISC", "Unlicense", "CC0"}
DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "vault", "programs", "bcap-2",
                            "design-resources", "SOURCES.json")


def load(path: str = DEFAULT_PATH) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def coverage(registry: dict) -> dict:
    """Source-level coverage against the pinned 21. Names every missing id and every malformed record."""
    have = {r.get("id"): r for r in registry.get("sources", [])}
    missing = [i for i in REQUIRED_IDS if i not in have]
    bad = [i for i, r in have.items() if i in REQUIRED_IDS and (r.get("rights_status") not in RIGHTS or not r.get("urls"))]
    return {"required": len(REQUIRED_IDS), "registered": len(REQUIRED_IDS) - len(missing), "missing": missing,
            "malformed": bad, "ok": not missing and not bad}


def count_drift(screenshot_claim, observed):
    """A marketing/screenshot count is a historical claim. Returns ('MATCH'|'DRIFT'|'UNKNOWN', detail); never asserts 100%."""
    if observed is None:
        return "UNKNOWN", "no live observation of the count"
    if observed != screenshot_claim:
        return "DRIFT", f"claim {screenshot_claim} vs observed {observed}: denominator is the versioned observation"
    return "MATCH", f"{observed}"


def admit_code(record: dict, evidence: dict = None):
    """May code/assets (UNKNOWN/MIXED sources can still admit an item that carries its own licence evidence: item-level wins) from this source (or one item of it) be copied into CPP? Fail-closed.
    `evidence` = {spdx, version, license_sha256, readme, license_text} retrieved for the exact item+version."""
    status = record.get("rights_status")
    if status in ("RESTRICTED", "REFERENCE_ONLY", "UNKNOWN_ACCESS"):
        return False, f"{status}: pointer/reference only, no code or asset copy"
    ev = evidence or {}
    if not (ev.get("spdx") and ev.get("version") and ev.get("license_sha256")):
        return False, "no item-level licence evidence (spdx + version + licence hash): MIXED/unverified is not permissive"
    if ev["spdx"] not in PERMISSIVE:
        return False, f"licence {ev['spdx']} is not in the permissive set"
    if ev.get("readme") is not None or ev.get("license_text") is not None:
        blocked, why = license_conflict(ev.get("readme", ""), ev.get("license_text", ""))
        if blocked:
            return False, "LICENSE_CONFLICT: " + why
    return True, f"{ev['spdx']} @ {ev['version']}"


def asset_license_ok(item: dict):
    """3dicons/Kitbitz style: a source-level 'CC0' label does not cover a premium or third-party item."""
    if item.get("tier") not in (None, "free", "v1"):
        if item.get("license") != "CC0-explicit":
            return False, f"tier {item['tier']!r} needs its own explicit grant, not the source's CC0 label"
    if item.get("third_party_marks") or item.get("provenance") is None:
        return False, "provenance missing or third-party marks present"
    return True, "item-level grant recorded"


def done_check(registry: dict, vetted_entries: int) -> dict:
    """DONE needs the absolute denominator AND vetted entries; 21 URLs and zero vetted entries is not production coverage."""
    cov = coverage(registry)
    ok = cov["ok"] and vetted_entries > 0
    return {"ok": ok, "coverage": cov, "vetted_entries": vetted_entries,
            "reason": None if ok else ("coverage incomplete" if not cov["ok"] else "zero vetted entries")}
