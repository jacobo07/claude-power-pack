"""Release Manager (CCF component #8).

Refuses to release until: human concept-selection is recorded, the selected
concept's Trademark Scanner verdict is PASS or an acknowledged WARN (never an
un-cleared BLOCK), and all objective evaluation checks passed -- per
vault/plans/CCF_ARCHITECTURE.md §8 / CCF_QUALITY_GATES.md's release gate.
"""
from __future__ import annotations

from modules.ccf import trademark_scanner


def release(
    prompt_records: dict,
    scan_verdicts: dict,
    artifact_bundle: dict,
    evaluation_result: dict,
    selection,
    human_acks: dict = None,
) -> dict:
    human_acks = human_acks or {}

    if not selection:
        return {"status": "BLOCKED", "reason": "no human concept selection recorded"}

    selected_id = selection["concept_id"]
    verdict_record = scan_verdicts.get(selected_id) or {}
    verdict = verdict_record.get("verdict")

    # BI-04/BR-05: a missing, malformed or stale scan is UNASSESSED, never an implied PASS.
    if verdict not in ("PASS", "WARN", "BLOCK"):
        return {"status": "BLOCKED", "readiness": "UNASSESSED",
                "reason": f"selected concept '{selected_id}' has no valid trademark scan verdict (UNASSESSED)"}
    if verdict_record.get("corpus_version") != trademark_scanner.CORPUS_VERSION:
        return {"status": "BLOCKED", "readiness": "UNASSESSED",
                "reason": f"selected concept '{selected_id}' scan used corpus "
                          f"{verdict_record.get('corpus_version')!r}, current is "
                          f"{trademark_scanner.CORPUS_VERSION!r}: re-scan (UNASSESSED)"}

    if verdict == "BLOCK":
        return {
            "status": "BLOCKED",
            "reason": f"selected concept '{selected_id}' has an un-cleared trademark BLOCK",
        }
    if verdict == "WARN" and not human_acks.get(selected_id):
        return {
            "status": "BLOCKED",
            "reason": (
                f"selected concept '{selected_id}' has a WARN verdict with no "
                f"recorded human acknowledgment"
            ),
        }
    if not evaluation_result.get("passed"):
        return {"status": "BLOCKED", "reason": "objective evaluation checks did not all pass"}
    if selected_id not in artifact_bundle.get("included_ids", []):
        return {
            "status": "BLOCKED",
            "reason": f"selected concept '{selected_id}' has no compiled artifact",
        }

    artifact_hash = (artifact_bundle.get("artifact_hashes") or {}).get(selected_id)
    if not artifact_hash:
        return {
            "status": "BLOCKED",
            "reason": f"selected concept '{selected_id}' has no positive artifact evidence (verified image hash)",
        }

    package = {
        "selected_concept_id": selected_id,
        "selection": selection,
        "prompts": prompt_records,
        "scan_verdicts": scan_verdicts,
        "evaluation": evaluation_result,
        "artifact_included_ids": artifact_bundle["included_ids"],
        "artifact_hashes": {selected_id: artifact_hash},
        "artifact_skipped": artifact_bundle.get("skipped", []),
    }
    return {"status": "SEALED", "package": package}
