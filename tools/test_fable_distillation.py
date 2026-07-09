#!/usr/bin/env python3
"""test_fable_distillation.py -- V-gates for the FD EXECUTION-mode activation.

Verifies the two live hooks the FD datasets documented as their next build:
  FD-00 admission gate  -- rejects at-floor / dataset-covered demand; admits genuine
                           above-floor discovery; fail-open ABSOLUTE (never blocks).
  FD-07 flywheel        -- classifies/triages/writes back real deltas idempotently;
                           fail-open; frontier-session gated.
  CO-12 fd_metrics      -- the fd_* signals accrue and surface (reused, not forked).

Hermetic: every gate uses a fresh tempfile state dir -- NO global writes, so the
suite is identical on re-run (run it x3). V-<DOMAIN>-<NAME> convention; DOMAIN_PASS
line for the done-gate grep. Exit 0 iff all gates pass.
"""
from __future__ import annotations

import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.fable_distillation.fd_00_gate import check_admission  # noqa: E402
from modules.fable_distillation.fd_07_flywheel import (  # noqa: E402
    run_flywheel, _is_frontier_session, triage_destination, _deposits_path)
from modules.cognitive_os.co_12_telemetry import (  # noqa: E402
    fd_metrics, readiness_report, record_signal)

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS {gate}: {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {gate}: {diag}")


@dataclass
class _FakeDecision:
    """A CO-03 RouteDecision stand-in so a gate test can force the cascade to a
    chosen rung deterministically (isolating the branch under test)."""
    rung: str
    reason: str = "forced"


def _tmp() -> Path:
    return Path(tempfile.mkdtemp(prefix="fd_vgate_"))


# --------------------------------------------------------------------------- #
def gate_fd00() -> None:
    # V-FD00-ADMIT-DISCOVERY: an above-floor discovery/critique, floor silent
    # (empty kb dir) + frontier rung forced -> ADMIT.
    empty_kb = _tmp()
    dec = check_admission(
        "design a novel adversarial critique strategy for an unfamiliar domain",
        kb_dir=empty_kb, route_fn=lambda t: _FakeDecision("opus"))
    if dec.action == "admit" and dec.verdict == "ADMIT":
        _ok("V-FD00-ADMIT-DISCOVERY", f"{dec.verdict}: {dec.reason[:60]}")
    else:
        _fail("V-FD00-ADMIT-DISCOVERY", f"got {dec.verdict}/{dec.action}: {dec.reason}")

    # V-FD00-REJECT-EXISTING: a task a PP dataset already governs -> REJECT, even
    # when the cascade is forced to the frontier rung (isolates the covers-branch).
    kb = _tmp()
    (kb / "fd_01_fable_delta_extraction_engine.md").write_text("# x", encoding="utf-8")
    dec = check_admission(
        "escribe un dataset sobre the fable delta extraction engine",
        kb_dir=kb, route_fn=lambda t: _FakeDecision("opus"))
    if dec.action == "reject" and "dataset" in dec.baseline_ref:
        _ok("V-FD00-REJECT-EXISTING", f"{dec.verdict}: {dec.baseline_ref}")
    else:
        _fail("V-FD00-REJECT-EXISTING", f"got {dec.verdict}/{dec.action}: {dec.reason}")

    # V-FD00-REJECT-MECHANICAL: a purely mechanical transform is at-floor -> REJECT.
    dec = check_admission("reformat this config file and fix the typo",
                          kb_dir=_tmp())
    if dec.action == "reject" and dec.verdict == "DECLINE":
        _ok("V-FD00-REJECT-MECHANICAL", f"{dec.verdict}: {dec.reason[:50]}")
    else:
        _fail("V-FD00-REJECT-MECHANICAL", f"got {dec.verdict}/{dec.action}")

    # V-FD00-FAILOPEN: a pathological input that breaks the body must NOT raise and
    # must fail-open to ADMIT (never block the Owner's call).
    try:
        dec = check_admission(object())  # .strip() on a non-str -> outer fail-open
        if dec.action == "admit" and "fail-open" in dec.reason:
            _ok("V-FD00-FAILOPEN", f"non-str input -> {dec.verdict} (no raise)")
        else:
            _fail("V-FD00-FAILOPEN", f"expected fail-open ADMIT, got {dec.verdict}")
    except Exception as e:  # noqa: BLE001
        _fail("V-FD00-FAILOPEN", f"gate RAISED (must fail-open): {e}")


# --------------------------------------------------------------------------- #
def gate_fd07() -> None:
    # V-FD07-HOOK-FIRES: a mixed finding set is processed; the loop reports its turn.
    st = _tmp()
    findings = [
        {"topic": "pane-isolation", "claim": "never rebase while a reviewer reads "
         "the worktree; a mid-read rebase invalidates the approve (a hard trap)"},
        {"topic": "dedup", "claim": "use a sha-256 content hash as the canonical "
         "dedup recipe for a findings ledger"},
        {"topic": "noise", "claim": "ok done"},                       # -> DISCARD
    ]
    res = run_flywheel("REPO-A", "sid-1", findings=findings, state_dir=st, record=True)
    if res.processed == 3 and res.deposited >= 1:
        _ok("V-FD07-HOOK-FIRES",
            f"processed={res.processed} deposited={res.deposited} "
            f"dup={res.dup} discarded={res.discarded}")
    else:
        _fail("V-FD07-HOOK-FIRES", f"processed={res.processed} deposited={res.deposited}")

    # V-FD07-ASSETS-WRITTEN: the classified deltas land in the deposits ledger at
    # the CORRECT destination (rule-shaped -> hard_rule; recipe-shaped -> asset).
    dep_file = _deposits_path("REPO-A", st)
    if dep_file.is_file():
        import json
        deposits = [json.loads(l) for l in dep_file.read_text(
            encoding="utf-8").splitlines() if l.strip()]
        dests = {d["destination"] for d in deposits}
        has_rule = triage_destination(findings[0]["claim"]) == "hard_rule"
        if deposits and "hard_rule" in dests and "asset" in dests and has_rule:
            _ok("V-FD07-ASSETS-WRITTEN",
                f"{len(deposits)} deposit(s) written, destinations={sorted(dests)}")
        else:
            _fail("V-FD07-ASSETS-WRITTEN", f"deposits={len(deposits)} dests={dests}")
    else:
        _fail("V-FD07-ASSETS-WRITTEN", "deposits ledger not written")

    # V-FD07-IDEMPOTENT: a second turn over the SAME findings deposits nothing new
    # (SHA-256 fingerprint idempotency -- the no-progress guard, FD-07 II.2).
    res2 = run_flywheel("REPO-A", "sid-2", findings=findings, state_dir=st, record=False)
    if res2.deposited == 0 and res2.dup >= 1:
        _ok("V-FD07-IDEMPOTENT", f"re-run deposited={res2.deposited} dup={res2.dup}")
    else:
        _fail("V-FD07-IDEMPOTENT", f"re-run deposited={res2.deposited} (want 0)")

    # V-FD07-FAILOPEN: malformed findings must NOT crash the flywheel.
    try:
        bad = run_flywheel("REPO-B", "sid-3",
                           findings=[{"claim": None}, {"x": 1}, 42], state_dir=_tmp())
        _ok("V-FD07-FAILOPEN", f"malformed input -> no raise (processed={bad.processed})")
    except Exception as e:  # noqa: BLE001
        _fail("V-FD07-FAILOPEN", f"flywheel RAISED (must fail-open): {e}")

    # V-FD07-FRONTIER-GATED: the flywheel only turns for a frontier session.
    import os
    prev = os.environ.pop("PP_FRONTIER_SESSION", None)
    try:
        off = _is_frontier_session()
        os.environ["PP_FRONTIER_SESSION"] = "1"
        on = _is_frontier_session()
        if (not off) and on:
            _ok("V-FD07-FRONTIER-GATED", "off without env, on with PP_FRONTIER_SESSION=1")
        else:
            _fail("V-FD07-FRONTIER-GATED", f"off={off} on={on}")
    finally:
        os.environ.pop("PP_FRONTIER_SESSION", None)
        if prev is not None:
            os.environ["PP_FRONTIER_SESSION"] = prev


# --------------------------------------------------------------------------- #
def gate_co12() -> None:
    # V-CO12-METRICS-EXIST: the fd_* metrics the prompt named are all present.
    st = _tmp()
    m = fd_metrics(state_dir=st)
    required = ("fd_sessions_count", "fd_deltas_extracted", "fd_assets_written",
                "fd_rejection_rate", "fd_dependence_reduction")
    missing = [k for k in required if k not in m]
    if not missing and m.get("measured") is False:
        _ok("V-CO12-METRICS-EXIST",
            f"all 5 fd_* metrics present; empty-state measured=False")
    else:
        _fail("V-CO12-METRICS-EXIST", f"missing={missing} measured={m.get('measured')}")

    # V-CO12-ACCRUES: after a deposit signal is recorded, the metric moves and
    # 'measured' flips -- proving REAL accrual (not a faked number).
    record_signal("fd_delta_deposited",
                  {"delta_class": "NEW", "destination": "hard_rule",
                   "portability_target": "mid-model", "portability_proven": False},
                  state_dir=st)
    m2 = fd_metrics(state_dir=st)
    if m2["fd_assets_written"] == 1 and m2["measured"] is True:
        _ok("V-CO12-ACCRUES", f"fd_assets_written={m2['fd_assets_written']} measured=True")
    else:
        _fail("V-CO12-ACCRUES", f"fd_assets_written={m2['fd_assets_written']} "
              f"measured={m2['measured']}")

    # V-CO12-IN-REPORT: readiness_report folds in the fd_distillation surface.
    rep = readiness_report(state_dir=st)
    if "fd_distillation" in rep and rep["fd_distillation"]["fd_assets_written"] == 1:
        _ok("V-CO12-IN-REPORT", "readiness_report carries fd_distillation")
    else:
        _fail("V-CO12-IN-REPORT", "fd_distillation absent from readiness_report")


def main() -> int:
    print("== FD EXECUTION-mode V-gates ==")
    print("[FD-00 admission gate]")
    gate_fd00()
    print("[FD-07 flywheel]")
    gate_fd07()
    print("[CO-12 fd_metrics]")
    gate_co12()
    total = _passes + _fails
    print(f"\nFD_ACTIVATION_PASS={_passes}/{total}  threshold={total}/{total}")
    verdict = "PASS" if _fails == 0 else "FAIL"
    print(f"DATASET_FAMILY_VERDICT={verdict}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
