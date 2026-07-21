"""Creative Evaluation Engine (CCF component #6).

Objective checks (no human) + a subjective human_gate_queue (never
auto-resolved), per vault/plans/CCF_ARCHITECTURE.md §6. Honest scope: objective
checks here operate on what the pipeline actually controls -- config, the
compiled prompt, the artifact bundle, and the Trademark Scanner verdict. They
do NOT include OCR/pixel-level verification of the rendered image (this
engine has no vision access to the generated PNG) -- that would be a
different, not-yet-built capability, not silently assumed here.
"""
from __future__ import annotations


def evaluate_concept(concept: dict, prompt_record: dict, scan_verdict: dict, human_ack: bool = False) -> dict:
    """Run objective checks for one concept.

    `human_ack` mirrors whether a human has recorded acknowledgment of a WARN
    verdict (per the TRADEMARK_COLLISION_GATE semantics) -- required for that
    check to pass when the verdict is WARN.
    """
    checks = {}

    checks["wordmark_in_prompt"] = concept["wordmark"] in prompt_record["prompt"]

    named_avoid = concept.get("avoid") or []
    icon_lower = (concept.get("icon") or "").lower()
    checks["avoid_terms_not_in_icon_text"] = not any(
        term.lower() in icon_lower for term in named_avoid
    )

    verdict = scan_verdict.get("verdict")
    if verdict == "PASS":
        checks["trademark_scan_ok"] = True
    elif verdict == "WARN":
        checks["trademark_scan_ok"] = bool(human_ack)
    else:  # BLOCK
        checks["trademark_scan_ok"] = False

    passed = all(checks.values())
    return {"concept_id": concept["id"], "checks": checks, "passed": passed}


def evaluate_bundle(artifact_bundle: dict) -> dict:
    """Evaluate the Artifact Compiler's output bundle.

    Restates CCF-F02's fix at the evaluation layer (belt-and-braces, per the
    architecture doc): a bundle with `built: False` (no concept had a usable
    image) always fails -- there is nothing valid to release.
    """
    if not artifact_bundle.get("built"):
        return {
            "passed": False,
            "reason": "no artifact was built -- no concept had a usable image",
            "skipped": artifact_bundle.get("skipped", []),
        }
    return {
        "passed": True,
        "included_ids": artifact_bundle["included_ids"],
        "skipped": artifact_bundle.get("skipped", []),
    }


def queue_human_gates(concept_ids: list) -> list:
    """Subjective checks are never auto-resolved -- this only enumerates what
    a human must act on (concept selection is the canonical case, per
    Institutional Extraction §F), it never picks one itself.
    """
    return [
        {"gate": "concept_selection", "candidates": list(concept_ids), "resolved": False}
    ]
