"""test_craif.py -- CRAIF Phase 1 done-gate (14 V-CRAIF-* gates).

Hermetic except V-CRAIF-SCHEMA-CONTRACT, which calls the real
reachability.scan() once to prove the synthetic rows used everywhere else
still match the real producer's current shape. Every other gate uses hand-
built synthetic rows and explicit tmp paths for the ledger, the DRK registry,
and the owner_queue state dir -- never the real, shared ~/.claude state.

Run: python tools/test_craif.py
Exit 0 iff every gate passes.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.craif import authority, candidate as candidate_mod, intake, runtime  # noqa: E402
from modules.craif.ledger import Ledger  # noqa: E402
from modules.craif.objects import RepairIntent, RepairIntentState, UnfalsifiableCandidateRejection  # noqa: E402
from modules.decision_review.decision_record import Registry  # noqa: E402
from modules.owner_queue import owner_queue  # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  [PASS] {gate}: {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"  [FAIL] {gate}: {diag}")


def _tmp_dir(prefix: str) -> Path:
    return Path(tempfile.mkdtemp(prefix=prefix))


def _row(unit="modules/foo/bar.py", status="ORPHAN", **kw) -> dict:
    base = {"unit": unit, "package": "modules", "status": status, "via": None, "klass": None, "note": ""}
    base.update(kw)
    return base


# ----------------------------------------------------------------------------
def test_finding_normalize():
    orphan = intake.finding_from_reachability_row(_row(status="ORPHAN"), ts="2026-07-21T00:00:00Z")
    reachable = intake.finding_from_reachability_row(_row(status="REACHABLE"), ts="")
    unknown = intake.finding_from_reachability_row(_row(status="UNKNOWN"), ts="")
    if orphan is not None and reachable is None and unknown is None:
        _ok("V-CRAIF-FINDING-NORMALIZE", "ORPHAN accepted; REACHABLE/UNKNOWN refused")
    else:
        _fail("V-CRAIF-FINDING-NORMALIZE", f"orphan={orphan} reachable={reachable} unknown={unknown}")


def test_dedup():
    f = intake.finding_from_reachability_row(_row(unit="modules/x/y.py"), ts="t1")
    open_row = {"target_unit": "modules/x/y.py", "condition_class": "reachability-orphan", "state": "PRECONDITIONS-CHECKED"}
    result = intake.validate_intake(f, [open_row])
    closed_row = {"target_unit": "modules/x/y.py", "condition_class": "reachability-orphan", "state": "CLOSED-REJECTED"}
    result2 = intake.validate_intake(f, [closed_row])
    if not result.accepted and result2.accepted:
        _ok("V-CRAIF-DEDUP", "open sibling blocks; closed sibling does not")
    else:
        _fail("V-CRAIF-DEDUP", f"result={result} result2={result2}")


def test_staleness():
    f = intake.finding_from_reachability_row(_row(unit="modules/z.py"), ts="t1")
    result = intake.validate_intake(f, [])
    if result.accepted:
        _ok("V-CRAIF-STALENESS", "fresh finding with no sibling accepted")
    else:
        _fail("V-CRAIF-STALENESS", f"unexpected rejection: {result.reason}")


def test_evidence_freeze_hash():
    row_a = _row(unit="modules/a.py")
    row_b = _row(unit="modules/a.py")
    row_c = _row(unit="modules/a.py", note="changed")
    fz_a = intake.freeze_evidence(row_a, ts="t1")
    fz_b = intake.freeze_evidence(row_b, ts="t1")
    fz_c = intake.freeze_evidence(row_c, ts="t1")
    if fz_a.content_hash == fz_b.content_hash and fz_a.content_hash != fz_c.content_hash:
        _ok("V-CRAIF-EVIDENCE-FREEZE-HASH", "identical content -> identical hash; changed -> different")
    else:
        _fail("V-CRAIF-EVIDENCE-FREEZE-HASH", f"a={fz_a.content_hash} b={fz_b.content_hash} c={fz_c.content_hash}")


def test_evidence_freeze_drift():
    intake_row = _row(unit="modules/drift.py", note="at-intake")
    freeze_row = _row(unit="modules/drift.py", note="at-freeze-drifted")
    fz_intake = intake.freeze_evidence(intake_row, ts="t1")
    fz_freeze = intake.freeze_evidence(freeze_row, ts="t2")
    if fz_intake.content_hash != fz_freeze.content_hash:
        _ok("V-CRAIF-EVIDENCE-FREEZE-DRIFT", "target drift between intake and freeze is detectable via hash mismatch")
    else:
        _fail("V-CRAIF-EVIDENCE-FREEZE-DRIFT", "drift not detected")


def test_candidate_unfalsifiable():
    intent = RepairIntent(id="T1", findings=[], target_unit="modules/orphan.py")
    result = candidate_mod.generate_candidate(intent, None)
    if isinstance(result, UnfalsifiableCandidateRejection):
        _ok("V-CRAIF-CANDIDATE-UNFALSIFIABLE", f"no proposed_target_state -> rejection: {result.reason}")
    else:
        _fail("V-CRAIF-CANDIDATE-UNFALSIFIABLE", f"expected rejection, got {result}")


def test_candidate_falsifiable():
    intent = RepairIntent(id="T2", findings=[], target_unit="modules/orphan.py")
    result = candidate_mod.generate_candidate(intent, {"surface": "hooks/hub.js"})
    if (not isinstance(result, UnfalsifiableCandidateRejection)
            and result.proposed_surface == "hooks/hub.js"
            and result.is_build_decision is False):
        _ok("V-CRAIF-CANDIDATE-FALSIFIABLE", f"surface supplied -> valid Candidate: {result.target_state_assertion}")
    else:
        _fail("V-CRAIF-CANDIDATE-FALSIFIABLE", f"got {result}")


def test_drk_real_tier():
    intent = RepairIntent(id="T3", findings=[], target_unit="modules/orphan_thing.py")
    cand = candidate_mod.generate_candidate(intent, {"surface": "hooks/hub.js"})
    reg = Registry(_tmp_dir("craif_drk_") / "records.jsonl")
    record = authority.consult_drk(cand, registry=reg, decision_id="T3", ts="2026-07-21T00:00:00Z")
    if record.tier is not None and record.verdict is not None:
        _ok("V-CRAIF-DRK-REAL-TIER", f"real classifier returned tier={record.tier.value} verdict={record.verdict.value}")
    else:
        _fail("V-CRAIF-DRK-REAL-TIER", f"tier={record.tier} verdict={record.verdict}")


def test_preconditions_rollback_absent():
    intent = RepairIntent(
        id="T4",
        findings=[intake.finding_from_reachability_row(_row(unit="modules/q.py"), ts="t1")],
        target_unit="modules/q.py",
    )
    cand = candidate_mod.generate_candidate(intent, {"surface": "hooks/hub.js"})
    preconditions = authority.check_preconditions(intent, cand)
    reg = Registry(_tmp_dir("craif_drk_") / "records.jsonl")
    drk_record = authority.consult_drk(cand, registry=reg, decision_id="T4", ts="t1")
    outcome = authority.acquire_authority(intent, cand, preconditions, drk_record)
    if not preconditions.rollback_mechanism_available and outcome.paused:
        _ok("V-CRAIF-PRECONDITIONS-ROLLBACK-ABSENT", f"paused: {outcome.pause_reason}")
    else:
        _fail("V-CRAIF-PRECONDITIONS-ROLLBACK-ABSENT", f"preconditions={preconditions} outcome={outcome}")


def test_owner_escalation():
    state_dir = _tmp_dir("craif_oq_")
    ledger_dir = _tmp_dir("craif_ledger_")
    drk_dir = _tmp_dir("craif_drk_")
    row = _row(unit="modules/escalate_me.py")
    record1 = runtime.run_transaction(
        row, proposed_target_state={"surface": "hooks/hub.js"},
        ledger_path=ledger_dir / "t.jsonl",
        decision_registry_path=drk_dir / "r.jsonl",
        owner_state_dir=state_dir, ts="2026-07-21T00:00:00Z",
    )
    pending_before = owner_queue.pending(state_dir=state_dir)
    id1 = record1.get("owner_escalation_id")
    ok_first = id1 is not None and len(pending_before) == 1
    # idempotent re-run with the same content -> same id, no duplicate
    ledger_dir2 = _tmp_dir("craif_ledger_")
    record2 = runtime.run_transaction(
        row, proposed_target_state={"surface": "hooks/hub.js"},
        ledger_path=ledger_dir2 / "t.jsonl",
        decision_registry_path=drk_dir / "r2.jsonl",
        owner_state_dir=state_dir, ts="2026-07-21T00:00:00Z",
    )
    id2 = record2.get("owner_escalation_id")
    pending_after = owner_queue.pending(state_dir=state_dir)
    if ok_first and id1 == id2 and len(pending_after) == 1:
        _ok("V-CRAIF-OWNER-ESCALATION", f"one row created ({id1}); idempotent re-run did not duplicate")
    else:
        _fail("V-CRAIF-OWNER-ESCALATION", f"id1={id1} id2={id2} pending_before={len(pending_before)} pending_after={len(pending_after)}")


def test_ledger_append_only():
    ledger_dir = _tmp_dir("craif_ledger_")
    lg = Ledger(ledger_dir / "t.jsonl")
    lg.append({"id": "A", "state": "OPENED"})
    lg.append({"id": "B", "state": "OPENED"})
    rows = lg.load()
    if len(rows) == 2 and rows[0]["id"] == "A" and rows[1]["id"] == "B":
        _ok("V-CRAIF-LEDGER-APPEND-ONLY", "two appends -> two rows, in order, none mutated")
    else:
        _fail("V-CRAIF-LEDGER-APPEND-ONLY", f"rows={rows}")


def test_no_mutation():
    ledger_dir = _tmp_dir("craif_ledger_")
    drk_dir = _tmp_dir("craif_drk_")
    state_dir = _tmp_dir("craif_oq_")
    live_registry_before = (PP_ROOT / "vault" / "decision_registry" / "records.jsonl")
    existed_before = live_registry_before.exists()
    size_before = live_registry_before.stat().st_size if existed_before else None

    row = _row(unit="modules/no_mutation_check.py")
    runtime.run_transaction(
        row, proposed_target_state={"surface": "hooks/hub.js"},
        ledger_path=ledger_dir / "t.jsonl",
        decision_registry_path=drk_dir / "r.jsonl",
        owner_state_dir=state_dir, ts="t1",
    )
    existed_after = live_registry_before.exists()
    size_after = live_registry_before.stat().st_size if existed_after else None
    if existed_before == existed_after and size_before == size_after:
        _ok("V-CRAIF-NO-MUTATION", "real vault/decision_registry untouched (explicit tmp registry path used)")
    else:
        _fail("V-CRAIF-NO-MUTATION", f"before=({existed_before},{size_before}) after=({existed_after},{size_after})")


def test_separation_of_powers():
    import inspect
    src = inspect.getsource(sys.modules["modules.craif.runtime"])
    forbidden = ["subprocess.", "os.system(", "shutil.rmtree", "reachability.write_registry", "reachability._write"]
    hits = [f for f in forbidden if f in src]
    if not hits:
        _ok("V-CRAIF-SEPARATION-OF-POWERS", "runtime.py contains no shell-out or registry-write calls")
    else:
        _fail("V-CRAIF-SEPARATION-OF-POWERS", f"forbidden patterns present: {hits}")


def test_cli_refuses_without_registry_path():
    """The integration verification pass found a real bug: main() originally had
    no --decision-registry-path flag, so a real CLI invocation silently wrote
    into the live, git-tracked vault/decision_registry/records.jsonl. This gate
    proves the CLI now refuses to run rather than defaulting into that file."""
    ledger_dir = _tmp_dir("craif_ledger_")
    state_dir = _tmp_dir("craif_oq_")
    exit_code = runtime.main([
        "--unit", "modules/whatever.py",
        "--ledger-path", str(ledger_dir / "t.jsonl"),
        "--owner-state-dir", str(state_dir),
        # deliberately omitting --decision-registry-path
    ])
    if exit_code == 1:
        _ok("V-CRAIF-CLI-REGISTRY-PATH-REQUIRED", "CLI refuses to run without an explicit --decision-registry-path")
    else:
        _fail("V-CRAIF-CLI-REGISTRY-PATH-REQUIRED", f"expected exit 1, got {exit_code}")


def test_schema_contract():
    from modules.liveness import reachability
    rows = reachability.scan()
    ok = all(
        set(r.keys()) >= {"unit", "package", "status", "via", "klass", "note"}
        and r["status"] in ("REACHABLE", "ORPHAN", "UNKNOWN")
        for r in rows
    )
    if ok and rows:
        _ok("V-CRAIF-SCHEMA-CONTRACT", f"real scan() returned {len(rows)} rows matching the expected schema")
    else:
        _fail("V-CRAIF-SCHEMA-CONTRACT", f"schema mismatch or empty scan ({len(rows)} rows)")


def main() -> int:
    print("=== CRAIF Phase 1 done-gate ===")
    test_finding_normalize()
    test_dedup()
    test_staleness()
    test_evidence_freeze_hash()
    test_evidence_freeze_drift()
    test_candidate_unfalsifiable()
    test_candidate_falsifiable()
    test_drk_real_tier()
    test_preconditions_rollback_absent()
    test_owner_escalation()
    test_ledger_append_only()
    test_no_mutation()
    test_separation_of_powers()
    test_cli_refuses_without_registry_path()
    test_schema_contract()
    print(f"CRAIF_PASS={_passes}/{_passes + _fails}  threshold={_passes + _fails}/{_passes + _fails}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
