"""Release Manager (CCF component #8).

Refuses to release until: human concept-selection is recorded, the selected
concept's Trademark Scanner verdict is PASS or an acknowledged WARN (never an
un-cleared BLOCK), and all objective evaluation checks passed -- per
vault/plans/CCF_ARCHITECTURE.md §8 / CCF_QUALITY_GATES.md's release gate.
"""
from __future__ import annotations


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
    verdict_record = scan_verdicts.get(selected_id, {})
    verdict = verdict_record.get("verdict")

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

    package = {
        "selected_concept_id": selected_id,
        "selection": selection,
        "prompts": prompt_records,
        "scan_verdicts": scan_verdicts,
        "evaluation": evaluation_result,
        "artifact_included_ids": artifact_bundle["included_ids"],
        "artifact_skipped": artifact_bundle.get("skipped", []),
    }
    return {"status": "SEALED", "package": package}
