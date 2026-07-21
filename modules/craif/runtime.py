"""runtime.py -- orchestrates one Repair Transaction through PRECONDITIONS-CHECKED
(paused), per the Phase 1 scope in C:\\Users\\User\\.claude\\plans\\structured-
weaving-quill.md.

Single-target only this phase: no bulk "process every orphan" mode. This repo
carries many real ORPHAN rows at any given time; iterating all of them would
flood the Owner queue with noise none of which names a diagnosed surface.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[2]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.craif import authority, candidate as candidate_mod, intake, ledger as ledger_mod
from modules.craif.objects import RepairIntent, RepairIntentState, UnfalsifiableCandidateRejection
from modules.decision_review.decision_record import Registry
from modules.owner_queue import owner_queue


def run_transaction(
    row: dict,
    *,
    proposed_target_state: dict | None = None,
    ledger_path=None,
    decision_registry_path=None,
    owner_state_dir=None,
    ts: str = "",
) -> dict:
    """Run one transaction from a raw reachability row through
    PRECONDITIONS-CHECKED (paused). Returns the full ledger record. Writes
    exactly one ledger row and, unless the candidate was unfalsifiable, exactly
    one owner_queue escalation row -- nothing else."""
    lg = ledger_mod.Ledger(ledger_path)
    txn_id = lg.next_id()

    finding = intake.finding_from_reachability_row(row, ts=ts)
    if finding is None:
        record = {
            "id": txn_id,
            "target_unit": row.get("unit", "<unknown>"),
            "condition_class": "reachability-orphan",
            "state": RepairIntentState.CLOSED_REJECTED.value,
            "reason": f"row status={row.get('status')!r} is not actionable (only ORPHAN is)",
        }
        lg.append(record)
        return record

    intent = RepairIntent(id=txn_id, findings=[finding], target_unit=finding.target_unit)

    intake_result = intake.validate_intake(finding, lg.load(), now_ts=ts)
    if not intake_result.accepted:
        record = {
            "id": txn_id,
            "target_unit": intent.target_unit,
            "condition_class": finding.subtype,
            "state": RepairIntentState.CLOSED_REJECTED.value,
            "reason": intake_result.reason,
        }
        lg.append(record)
        return record
    intent.state = RepairIntentState.INTAKE_VALIDATED

    intent.evidence_freeze = intake.freeze_evidence(row, ts=ts)
    intent.state = RepairIntentState.EVIDENCE_FROZEN

    cand = candidate_mod.generate_candidate(intent, proposed_target_state)
    if isinstance(cand, UnfalsifiableCandidateRejection):
        record = {
            "id": txn_id,
            "target_unit": intent.target_unit,
            "condition_class": finding.subtype,
            "state": RepairIntentState.CLOSED_REJECTED.value,
            "reason": cand.reason,
            "missing": cand.missing,
            "evidence_freeze_hash": intent.evidence_freeze.content_hash,
        }
        lg.append(record)
        return record
    intent.state = RepairIntentState.CANDIDATE_SELECTED

    preconditions = authority.check_preconditions(intent, cand)
    drk_reg = Registry(decision_registry_path) if decision_registry_path else Registry()
    drk_record = authority.consult_drk(cand, registry=drk_reg, decision_id=txn_id, ts=ts)
    outcome = authority.acquire_authority(intent, cand, preconditions, drk_record)

    intent.state = RepairIntentState.PRECONDITIONS_CHECKED
    intent.paused = outcome.paused
    intent.pause_reason = outcome.pause_reason

    record = {
        "id": txn_id,
        "target_unit": intent.target_unit,
        "condition_class": finding.subtype,
        "state": intent.state.value,
        "paused": intent.paused,
        "pause_reason": intent.pause_reason,
        "evidence_freeze_hash": intent.evidence_freeze.content_hash,
        "candidate": {
            "target_state_assertion": cand.target_state_assertion,
            "verification_instrument": cand.verification_instrument,
            "proposed_surface": cand.proposed_surface,
        },
        "preconditions": {
            "ownership_unambiguous": preconditions.ownership_unambiguous,
            "rollback_mechanism_available": preconditions.rollback_mechanism_available,
            "rollback_gap_reason": preconditions.rollback_gap_reason,
        },
        "drk_informational": {
            "tier": outcome.drk_tier,
            "verdict": outcome.drk_verdict,
            "record_id": outcome.drk_record_id,
        },
    }
    lg.append(record)

    escalation_id = owner_queue.append(
        action="craif-repair-precondition-pause",
        command=(
            f"Review paused CRAIF transaction {txn_id} for {intent.target_unit}: "
            f"{outcome.pause_reason}"
        ),
        component=f"craif:{intent.target_unit}",
        source=txn_id,
        state_dir=owner_state_dir,
    )
    record["owner_escalation_id"] = escalation_id
    return record


def main(argv: list[str] | None = None) -> int:
    import json

    from modules.liveness import reachability

    parser = argparse.ArgumentParser(description="CRAIF Phase 1: run one repair transaction.")
    parser.add_argument("--unit", required=True, help="module path as reported by reachability.scan()")
    parser.add_argument("--proposed-surface", default=None, help="where the orphan should be wired in")
    parser.add_argument("--ledger-path", default=None)
    parser.add_argument("--owner-state-dir", default=None)
    parser.add_argument(
        "--decision-registry-path", default=None,
        help="REQUIRED in practice: without this, DRK consultation defaults to the "
             "real, git-tracked vault/decision_registry/records.jsonl.",
    )
    args = parser.parse_args(argv)
    if args.decision_registry_path is None:
        print(
            "refusing to run without --decision-registry-path: the default would "
            "write into the real, shared vault/decision_registry/records.jsonl",
            file=sys.stderr,
        )
        return 1

    rows = reachability.scan()
    row = next((r for r in rows if r["unit"] == args.unit), None)
    if row is None:
        print(f"unit not found in current scan: {args.unit}", file=sys.stderr)
        return 1

    proposed = {"surface": args.proposed_surface} if args.proposed_surface else None
    record = run_transaction(
        row,
        proposed_target_state=proposed,
        ledger_path=args.ledger_path,
        decision_registry_path=args.decision_registry_path,
        owner_state_dir=args.owner_state_dir,
    )
    print(json.dumps(record, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
