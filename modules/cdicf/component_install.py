"""CDICF component selection-before-install plan (BCAP-2 Phase 8, D21-D03/D07/D09). Pure planning, performs NO install.

plan_install() is the gate: it returns an ordered verdict and never mutates anything. Reuses source_intake.admit_code for
licence rights (item-level evidence). Every refusal names its reason; a rollback record is mandatory for an ALLOW."""
from __future__ import annotations

from modules.cdicf.source_intake import admit_code

FILTERS = ("license", "supply_chain", "compatibility", "cost", "identity_fit", "state_coverage", "source_version", "rollback")


def plan_install(item: dict, project: dict, installed: dict = None):
    """item: {name, registry, source_rights, licence_evidence, peers, latest_version, snapshot_version, supply_chain_ok,
    states, cost, identity_fit}. project: {has_peers, accepted_registries, required_states, budget}. installed: {name: registry}.
    Returns {"verdict": ALLOW|REFUSE, "reasons": [...], "rollback": ...}."""
    why, installed = [], installed or {}
    ok, reason = admit_code({"rights_status": item.get("source_rights")}, item.get("licence_evidence"))
    if not ok:
        why.append(f"license: {reason}")
    if item.get("registry") not in project.get("accepted_registries", []):
        why.append("supply_chain: registry not accepted (malicious or unknown registry)")
    if item.get("supply_chain_ok") is not True:
        why.append("supply_chain: not verified")
    missing = [p for p in item.get("peers", []) if p not in project.get("has_peers", [])]
    if missing:
        why.append(f"compatibility: missing peer dependency {missing}")
    if item.get("snapshot_version") != item.get("latest_version"):
        why.append("source_version: stale snapshot vs registry, or renamed/drifted component; refetch required")
    held = installed.get(item.get("name"))
    if held is not None and held != item.get("registry"):
        why.append(f"compatibility: name {item.get('name')} already installed from {held}, not {item.get('registry')}")
    need = [s for s in project.get("required_states", []) if s not in item.get("states", [])]
    if need:
        why.append(f"state_coverage: missing {need}")
    if item.get("cost") is None:
        why.append("cost: unmeasured, not assumed zero")
    elif project.get("budget") is not None and item["cost"] > project["budget"]:
        why.append("cost: over budget")
    if item.get("identity_fit") is not True:
        why.append("identity_fit: not confirmed against project DESIGN.md")
    if not item.get("rollback"):
        why.append("rollback: no rollback recorded")
    return {"verdict": "REFUSE" if why else "ALLOW", "reasons": why, "rollback": item.get("rollback")}


def run_install(plan: dict, steps, rollback_fn):
    """Execute steps only for an ALLOW plan; if a step fails partway, call rollback_fn(done_steps) and report FAILED."""
    if plan["verdict"] != "ALLOW":
        return {"status": "NOT_RUN", "done": []}
    done = []
    for s in steps:
        try:
            s()
        except Exception as e:  # a failed step must roll back what landed, then surface the cause
            rollback_fn(list(done))
            return {"status": "FAILED_ROLLED_BACK", "done": done, "error": type(e).__name__}
        done.append(s)
    return {"status": "INSTALLED", "done": done}


def reference_only_catalog(entry: dict):
    """D03: restricted/pro material is catalogued as a pointer; code copy only for a separately licensed item."""
    ok, why = admit_code({"rights_status": entry.get("rights_status", "REFERENCE_ONLY")}, entry.get("licence_evidence"))
    return {"mode": "SOURCE_COPY" if ok else "REFERENCE_ONLY", "why": why}
