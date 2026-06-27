#!/usr/bin/env python3
"""V-gate suite for the Session Resilience OS BUILD (Path A headless backbone).

Doctrine: rules/python/testing.md  -- V-<DOMAIN>-<NAME>, exit 0 iff fails==0.
Hermetic by construction: every persistence path is a fresh TemporaryDirectory,
no global writes, no time-window dedup -> identical result on repeated runs
(feedback_hermetic_test_global_writes_time_window).

Sprint coverage: G4 (acceptance arbiter) + G5 (telemetry) + G4->G5 integration.
G3/G2/G1 gates are added as those sprints land. The visual "OOM = Reload Window"
contract is ADVISORY/OWNER-RUN here (printed, not counted) -- a headless agent
cannot self-certify a GUI check (SCS C50 precedent).
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from modules.session_resilience import acceptance as G4  # noqa: E402
from modules.session_resilience import telemetry as G5  # noqa: E402

passes = 0
fails = 0


def _ok(gate: str, evidence: str) -> None:
    global passes
    passes += 1
    print(f"OK   {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global fails
    fails += 1
    print(f"FAIL {gate}: {diagnostic}")


# --- fixtures ----------------------------------------------------------------

def _state(scroll_a: float = 0.60, tabs=("a.py", "b.py"), with_focus=True) -> dict:
    return {
        "schema_version": 1,
        "captured_at": "2026-06-27T00:00:00Z",
        "windows": [
            {
                "window_id": "w1",
                "workspace_path": "C:/repos/pp",
                "foreground": True,
                "terminals": [
                    {"pane_id": "p1", "cwd": "C:/repos/pp", "conversation_id": "X"},
                    {"pane_id": "p2", "cwd": "C:/repos/pp", "conversation_id": "Y"},
                ],
                "editor": {
                    "tabs": [
                        {"path": t, "group": 0, "order": i, "pinned": False, "preview": False}
                        for i, t in enumerate(tabs)
                    ],
                    "focus": {"window_id": "w1", "group": 0, "path": "a.py"} if with_focus else None,
                    "scroll": {"a.py": scroll_a, "b.py": 0.20},
                    "panels": {"sidebar": {"visible": True, "size": 240}},
                    "splits": {"groups": 1, "layout": "single"},
                },
            }
        ],
    }


# --- G4: Recovery Acceptance Framework --------------------------------------

def gates_g4() -> None:
    ref = _state()

    # V-G4-VERDICT-RECOVERED: identical observed == reference
    sc = G4.score_recovery(ref, _state())
    v, _ = G4.classify(sc)
    if v == G4.RECOVERED and not sc.mismatches():
        _ok("V-G4-VERDICT-RECOVERED", f"identical state -> {v}, fidelity={G4.fidelity(sc):.2f}")
    else:
        _fail("V-G4-VERDICT-RECOVERED", f"got {v}, mismatches={sc.mismatches()}")

    # V-G4-VERDICT-FAILED: everything diverges
    bad = _state(scroll_a=0.05, tabs=("z.py",), with_focus=False)
    bad["windows"][0]["window_id"] = "wX"
    bad["windows"][0]["workspace_path"] = "C:/other"
    bad["windows"][0]["terminals"] = [{"pane_id": "q", "cwd": "C:/other", "conversation_id": "Q"}]
    scb = G4.score_recovery(ref, bad)
    vb, missing = G4.classify(scb)
    if vb == G4.FAILED and missing:
        _ok("V-G4-VERDICT-FAILED", f"divergent -> {vb}, {len(missing)} missing elements")
    else:
        _fail("V-G4-VERDICT-FAILED", f"got {vb}, missing={missing}")

    # V-G4-VERDICT-PARTIAL: windows/terminals match, editor diverges
    part = _state(scroll_a=0.05, tabs=("a.py", "c.py"))
    scp = G4.score_recovery(ref, part)
    vp, mp = G4.classify(scp)
    if vp == G4.PARTIAL and mp:
        _ok("V-G4-VERDICT-PARTIAL", f"partial -> {vp}, missing={[m.split(':')[0] for m in mp]}")
    else:
        _fail("V-G4-VERDICT-PARTIAL", f"got {vp}, missing={mp}")

    # V-G4-GATE: gate blocks non-RECOVERED, allows RECOVERED
    g_ok = G4.acceptance_gate(G4.score_recovery(ref, _state()))
    g_no = G4.acceptance_gate(scp)
    if g_ok.allow_complete and not g_no.allow_complete:
        _ok("V-G4-GATE", f"allow={g_ok.allow_complete} on RECOVERED; hold on {g_no.verdict}")
    else:
        _fail("V-G4-GATE", f"allow_ok={g_ok.allow_complete} allow_partial={g_no.allow_complete}")

    # V-G4-SCROLL-TOL: within tol matches, beyond fails
    near = G4.score_recovery(ref, _state(scroll_a=0.60 + 0.02))  # within default 0.03
    far = G4.score_recovery(ref, _state(scroll_a=0.60 + 0.10))   # beyond
    if near.dimensions["scroll"].matched and not far.dimensions["scroll"].matched:
        _ok("V-G4-SCROLL-TOL", "scroll +0.02 matches, +0.10 fails (host-approximate honored)")
    else:
        _fail("V-G4-SCROLL-TOL",
              f"near={near.dimensions['scroll'].matched} far={far.dimensions['scroll'].matched}")

    # V-G4-CAPABILITY: host that cannot restore scroll -> excluded, not failed
    caps = frozenset(d for d in G4.models.DIMENSIONS if d != "scroll")
    scc = G4.score_recovery(ref, _state(scroll_a=0.05))  # scroll way off
    vc = G4.equivalence_verdict(scc, host_capabilities=caps)
    vc_no = G4.equivalence_verdict(scc)  # full caps -> scroll counts -> FAILED
    if vc == G4.RECOVERED and vc_no == G4.FAILED:
        _ok("V-G4-CAPABILITY", "scroll excluded for limited host -> RECOVERED; counted otherwise -> FAILED")
    else:
        _fail("V-G4-CAPABILITY", f"limited={vc} full={vc_no}")

    # V-G4-BENCHMARK-REGRESSION: provisional baseline + regression alert
    bench = G4.compute_benchmark([{"duration_s": 2.0, "fidelity": 1.0}] * 6)
    alerts = G4.regression_check({"duration_s": 9.0, "fidelity": 0.5}, bench)
    if not bench.provisional and alerts:
        _ok("V-G4-BENCHMARK-REGRESSION", f"baseline {bench.expected_seconds:.1f}s; {len(alerts)} alert(s)")
    else:
        _fail("V-G4-BENCHMARK-REGRESSION", f"provisional={bench.provisional} alerts={alerts}")


# --- G5: Recovery Telemetry & Diagnostics -----------------------------------

def gates_g5() -> None:
    with tempfile.TemporaryDirectory() as td:
        col = G5.RecoveryEventCollector(state_dir=Path(td))

        # V-G5-TELEMETRY: emit + read back real data
        col.emit({"ts": "2026-06-27T00:00:01Z", "type": "recovery_started", "recovery_id": "r1"})
        col.emit({"ts": "2026-06-27T00:00:09Z", "type": "recovery_completed",
                  "recovery_id": "r1", "verdict": "RECOVERED", "duration_s": 8.0})
        evs = col.read()
        if len(evs) == 2 and evs[1]["verdict"] == "RECOVERED":
            _ok("V-G5-TELEMETRY", f"{len(evs)} events persisted with real fields")
        else:
            _fail("V-G5-TELEMETRY", f"events={evs}")

        # V-G5-REDACT: a fake secret never lands raw on disk
        fake = "sk-ant-" + ("A" * 50)
        col.emit({"ts": "2026-06-27T00:00:10Z", "type": "crash_detected",
                  "recovery_id": "r2", "note": f"leaked {fake}"})
        raw = col.path.read_text(encoding="utf-8")
        if fake not in raw and "[REDACTED" in raw:
            _ok("V-G5-REDACT", "fake secret redacted before persistence (URB)")
        else:
            _fail("V-G5-REDACT", "secret reached disk OR redaction marker absent")

        # V-G5-QUARANTINE: malformed event quarantined, stream uncorrupted
        before = len(col.read())
        col.emit({"type": "no_ts"})  # missing ts -> malformed
        after = len(col.read())
        if after == before and col.quarantine_path.is_file():
            _ok("V-G5-QUARANTINE", "malformed event quarantined; stream uncorrupted")
        else:
            _fail("V-G5-QUARANTINE", f"before={before} after={after} q={col.quarantine_path.is_file()}")

    # V-G5-METRICS: aggregate real numbers
    events = [
        {"ts": "1", "type": "recovery_completed", "verdict": "RECOVERED", "duration_s": 4.0},
        {"ts": "2", "type": "recovery_failed", "verdict": "FAILED", "duration_s": 6.0,
         "missing_elements": ["scroll: off", "focus: lost"]},
    ]
    m = G5.aggregate_metrics(events)
    if m.total_recoveries == 2 and m.acceptance_rate == 0.5 and m.failed_element_counts.get("scroll") == 1:
        _ok("V-G5-METRICS", f"rate={m.acceptance_rate} avg={m.avg_duration_s}s fails={m.failed_element_counts}")
    else:
        _fail("V-G5-METRICS", f"metrics={m}")

    # V-G5-DIAGNOSE: failed timeline -> determined root cause
    tl = G5.correlate([
        {"ts": "1", "type": "recovery_started", "recovery_id": "rX"},
        {"ts": "2", "type": "acceptance_scored", "recovery_id": "rX", "verdict": "FAILED",
         "missing_elements": ["focus: expected a.py != b.py"]},
        {"ts": "3", "type": "recovery_failed", "recovery_id": "rX"},
        {"ts": "9", "type": "recovery_started", "recovery_id": "other"},
    ], "rX")
    rc = G5.diagnose(tl)
    if len(tl) == 3 and rc.determined and "focus" in rc.cause:
        _ok("V-G5-DIAGNOSE", f"timeline={len(tl)} cause='{rc.cause}'")
    else:
        _fail("V-G5-DIAGNOSE", f"timeline={len(tl)} rc={rc}")

    # V-G5-HEALTH: healthy vs degraded
    healthy = G5.health_observatory([{"ts": "1", "type": "recovery_completed", "verdict": "RECOVERED"}])
    degraded = G5.health_observatory(events)
    if healthy.status == "HEALTHY" and degraded.status == "DEGRADED":
        _ok("V-G5-HEALTH", f"healthy={healthy.status} mixed={degraded.status} notes={degraded.notes}")
    else:
        _fail("V-G5-HEALTH", f"healthy={healthy.status} degraded={degraded.status}")

    # V-G5-ANOMALY: blip no alert, sustained trend alerts
    blip = G5.detect_anomalies([1, 1, 1, 1, 1, 9])
    trend = G5.detect_anomalies([1, 1, 1, 5, 6, 7])
    if not blip and trend:
        _ok("V-G5-ANOMALY", "single blip silent; sustained trend alerts")
    else:
        _fail("V-G5-ANOMALY", f"blip={blip} trend={trend}")


# --- Integration + baseline --------------------------------------------------

def gates_integration() -> None:
    # V-INTEGRATION-G4-G5: real wiring score -> gate -> emit -> metrics reflect
    with tempfile.TemporaryDirectory() as td:
        col = G5.RecoveryEventCollector(state_dir=Path(td))
        ref = _state()
        sc = G4.score_recovery(ref, _state(scroll_a=0.05, tabs=("a.py", "c.py")))
        gate = G4.acceptance_gate(sc)
        col.emit({"ts": "2026-06-27T01:00:00Z", "type": "acceptance_scored",
                  "recovery_id": "rint", "verdict": gate.verdict,
                  "missing_elements": gate.missing_elements})
        col.emit({"ts": "2026-06-27T01:00:01Z", "type": "recovery_completed",
                  "recovery_id": "rint", "verdict": gate.verdict, "duration_s": 3.0,
                  "missing_elements": gate.missing_elements})
        m = G5.aggregate_metrics(col.read())
        rc = G5.diagnose(G5.correlate(col.read(), "rint"))
        if (not gate.allow_complete and m.total_recoveries == 1
                and m.acceptance_rate == 0.0 and rc.determined):
            _ok("V-INTEGRATION-G4-G5",
                f"G4 {gate.verdict} -> G5 logged -> metrics rate={m.acceptance_rate}, cause='{rc.cause}'")
        else:
            _fail("V-INTEGRATION-G4-G5",
                  f"allow={gate.allow_complete} total={m.total_recoveries} rate={m.acceptance_rate} rc={rc.determined}")

    # V-BASELINE-INTACT: existing cpc_os snapshot still imports (no regression)
    try:
        from modules.cpc_os import snapshot  # noqa: F401
        _ok("V-BASELINE-INTACT", "modules.cpc_os.snapshot imports; no regression from new package")
    except Exception as exc:  # noqa: BLE001
        _fail("V-BASELINE-INTACT", f"import regression: {exc}")


def gates_g3() -> None:
    from modules.session_resilience import snapshot_versioning as G3M
    sh = G4.models.state_hash

    # V-G3-DELTA: identical -> 0 ops; one change -> small (proportional) delta
    same = G3M.compute_delta(_state(scroll_a=0.50), _state(scroll_a=0.50)).size()
    one = G3M.compute_delta(_state(scroll_a=0.50), _state(scroll_a=0.51)).size()
    if same == 0 and 1 <= one <= 2:
        _ok("V-G3-DELTA", f"identical->0, one-change->{one} (proportional)")
    else:
        _fail("V-G3-DELTA", f"same={same} one={one}")

    A, B = _state(scroll_a=0.10), _state(scroll_a=0.50)
    C = _state(scroll_a=0.90, tabs=("a.py", "b.py", "c.py"))
    with tempfile.TemporaryDirectory() as td:
        s = G3M.SessionVersionStore(Path(td))
        a = s.record(A, "A")
        b = s.record(B, "B")
        c = s.record(C, "C")
        rA, rB, rC = s.reconstruct(a), s.reconstruct(b), s.reconstruct(c)

        # V-G3-VERSION-RESTORE: restore to prior version B exactly (not A, not C)
        if sh(rB) == sh(B) and sh(rB) != sh(rC) and sh(rB) != sh(rA):
            _ok("V-G3-VERSION-RESTORE", "restore to B exact; != A and != C")
        else:
            _fail("V-G3-VERSION-RESTORE", f"B==recon(B):{sh(rB)==sh(B)}")

        # V-G3-G4-VALIDATED: reconstructed version validated by the G4 arbiter
        gate = G4.acceptance_gate(G4.score_recovery(B, rB))
        if gate.verdict == G4.RECOVERED and gate.allow_complete:
            _ok("V-G3-G4-VALIDATED", f"reconstructed B -> G4 {gate.verdict}")
        else:
            _fail("V-G3-G4-VALIDATED", f"verdict={gate.verdict} allow={gate.allow_complete}")

        # V-G3-CHAIN-INTEGRITY: tampered delta -> integrity break, withheld
        s._data["versions"][2]["delta"]["set"].append([["captured_at"], "TAMPERED"])
        try:
            s.reconstruct(c)
            _fail("V-G3-CHAIN-INTEGRITY", "tampered chain not detected (no raise)")
        except ValueError:
            _ok("V-G3-CHAIN-INTEGRITY", "tampered delta detected -> reconstruct withheld")

    # V-G3-COMPACTION: tagged version survives prune, stays reconstructable, ids unique
    with tempfile.TemporaryDirectory() as td:
        s = G3M.SessionVersionStore(Path(td), max_versions=3)
        s.record(_state(scroll_a=0.10), "A")
        keep = s.record(_state(scroll_a=0.20), "B", tag="keepB")
        s.record(_state(scroll_a=0.30), "C")
        s.record(_state(scroll_a=0.40), "D")
        s.record(_state(scroll_a=0.50), "E")
        ids = [v.version_id for v in s.catalog()]
        unique = len(ids) == len(set(ids))
        rk = s.reconstruct(keep)
        if keep in ids and unique and sh(rk) == sh(_state(scroll_a=0.20)):
            _ok("V-G3-COMPACTION", f"tagged kept+reconstructs; unique ids {ids}")
        else:
            _fail("V-G3-COMPACTION", f"keep_in={keep in ids} unique={unique} ids={ids}")


def main() -> int:
    gates_g4()
    gates_g5()
    gates_g3()
    gates_integration()
    print("--- ADVISORY (OWNER-RUN, not counted) ---")
    print("OWNER  V-G1-CONTRACT: 'OOM crash == Reload Window' visual indistinguishability is a")
    print("       GUI check with no CLI -- run after the G1 extension lands (SCS C50 precedent).")
    print(f"SESSION_RESILIENCE_BUILD_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
