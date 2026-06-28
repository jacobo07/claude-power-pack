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


def gates_g2() -> None:
    from modules.session_resilience import multi_window as G2M
    from modules.session_resilience import snapshot_versioning as G3M
    with tempfile.TemporaryDirectory() as td:
        r = [Path(td) / f"r{i}" for i in range(3)]
        for p in r:
            p.mkdir()
        reg = G2M.WindowRegistry(Path(td))
        reg.register("win-1", str(r[0]), foreground=True,
                     panes=[{"pane_id": "p1", "cwd": str(r[0]), "conversation_id": "X"}])
        reg.register("win-2", str(r[1]),
                     panes=[{"pane_id": "p2", "cwd": str(r[1]), "conversation_id": "Y"}])
        reg.register("win-3", str(r[2]),
                     panes=[{"pane_id": "p3", "cwd": str(r[2]), "conversation_id": "Z"}])
        topo = G2M.cross_window_topology(reg)

        # V-G2-WINDOWS-DETECTED: 3 windows captured individually
        if len(reg.windows()) == 3 and topo["count"] == 3 and topo["foreground"] == "win-1":
            _ok("V-G2-WINDOWS-DETECTED", f"3 windows captured, fg={topo['foreground']}")
        else:
            _fail("V-G2-WINDOWS-DETECTED", f"topo={topo}")

        # V-G2-IDENTITY: stable, PID-free, marker-disambiguated
        i1 = G2M.resolve_window_identity(str(r[0]), "m1")
        i1b = G2M.resolve_window_identity(str(r[0]), "m1")
        i2 = G2M.resolve_window_identity(str(r[0]), "m2")
        if i1 == i1b and i1 != i2 and i1.startswith("win-"):
            _ok("V-G2-IDENTITY", "stable + PID-free + marker disambiguates same workspace")
        else:
            _fail("V-G2-IDENTITY", f"i1={i1} i1b={i1b} i2={i2}")

        # V-G2-BINDING: existing dir ok; missing path flagged
        ok1, _ = G2M.bind_workspace(str(r[0]))
        ok2, _ = G2M.bind_workspace(str(Path(td) / "ghost"))
        if ok1 and not ok2:
            _ok("V-G2-BINDING", "existing workspace ok; missing path blocked-with-reason")
        else:
            _fail("V-G2-BINDING", f"ok1={ok1} ok2={ok2}")

        # V-G2-WINDOW-RESTORE: crash disappearance preserves the window + census
        life = G2M.WindowLifecycle(reg)
        life.crash_gone("win-2")
        if (reg.expected_census() == 3 and reg.get("win-2").status == G2M.RECOVERY_PENDING
                and reg.get("win-1").status == G2M.OPEN and reg.get("win-3").status == G2M.OPEN):
            _ok("V-G2-WINDOW-RESTORE", "crashed win-2 preserved (recovery_pending); census stays 3")
        else:
            _fail("V-G2-WINDOW-RESTORE", f"census={reg.expected_census()}")

        # V-G2-ISOLATION: clean-close one window does not affect the others
        life.clean_close("win-3")
        if reg.expected_census() == 2 and reg.get("win-1").status == G2M.OPEN:
            _ok("V-G2-ISOLATION", "clean-close win-3 -> census 2; win-1 untouched")
        else:
            _fail("V-G2-ISOLATION", f"census={reg.expected_census()} win1={reg.get('win-1').status}")

        # V-G2-FOCUS: exactly one foreground after restore
        fg, why = G2M.arbitrate_focus(reg)
        if fg == "win-1":
            _ok("V-G2-FOCUS", f"single foreground -> {fg} ({why})")
        else:
            _fail("V-G2-FOCUS", f"fg={fg} ({why})")

        # V-G2-LOCK: two windows claiming one conversation -> conflict, single grant
        reg.register("win-4", str(r[0]),
                     panes=[{"pane_id": "p4", "cwd": str(r[0]), "conversation_id": "X"}])
        lc = G2M.lock_coordinator(reg)
        confs = [c for c in lc["conflicts"] if c["conversation_id"] == "X"]
        if confs and lc["grants"]["X"] == "win-1" and "win-4" in confs[0]["blocked"]:
            _ok("V-G2-LOCK", "conflict on X -> granted to foreground win-1, win-4 blocked")
        else:
            _fail("V-G2-LOCK", f"conflicts={lc['conflicts']} grants={lc['grants']}")

        # V-G2-ORDER: sequential under resource pressure; locked window first
        reg.get("win-2").panes = [{"pane_id": "p2", "cwd": str(r[1]),
                                   "conversation_id": "Y", "locked": True}]
        reg._save()
        plan = G2M.restoration_order(reg, resource_pressure=True)
        if not plan["parallel_allowed"] and plan["order"][0] == "win-2":
            _ok("V-G2-ORDER", f"sequential under pressure; locked win-2 first: {plan['order']}")
        else:
            _fail("V-G2-ORDER", f"plan={plan}")

        # V-G2-G3-BRIDGE: per-window description -> G3 versioned -> G4 RECOVERED
        wdesc = G2M.window_state_description(reg.get("win-1"))
        with tempfile.TemporaryDirectory() as td2:
            st = G3M.SessionVersionStore(Path(td2))
            v = st.record(wdesc, "w1")
            back = st.reconstruct(v)
        gate = G4.acceptance_gate(G4.score_recovery(wdesc, back))
        if gate.verdict == G4.RECOVERED:
            _ok("V-G2-G3-BRIDGE", "per-window desc -> G3 versioned -> G4 RECOVERED")
        else:
            _fail("V-G2-G3-BRIDGE", f"verdict={gate.verdict}")


def gates_g1() -> None:
    from modules.session_resilience import ui_state as G1M
    from modules.session_resilience import multi_window as G2M
    from modules.session_resilience import snapshot_versioning as G3M

    def _ed(scroll):
        return G1M.build_editor(
            tabs=[{"path": "a.py", "group": 0, "order": 0, "pinned": False, "preview": False},
                  {"path": "b.py", "group": 0, "order": 1, "pinned": True, "preview": False}],
            focus={"window_id": "w1", "group": 0, "path": "a.py"},
            scroll={"a.py": scroll, "b.py": 0.2})

    # V-G1-MODEL: manifest builds + validates; bad focus is rejected
    ok_good, _ = G1M.validate_editor(_ed(0.6))
    bad = G1M.build_editor(tabs=[{"path": "a.py", "group": 0, "order": 0}],
                           focus={"window_id": "w1", "group": 0, "path": "ghost.py"})
    ok_bad, _ = G1M.validate_editor(bad)
    if ok_good and not ok_bad:
        _ok("V-G1-MODEL", "manifest valid; focus-not-in-tabs rejected")
    else:
        _fail("V-G1-MODEL", f"good={ok_good} bad={ok_bad}")

    # V-G1-DIFF: canonical stable; one scroll change -> small leaf delta
    stable = G1M.canonical_editor(_ed(0.6)) == G1M.canonical_editor(_ed(0.6))
    n = G1M.editor_change_count(_ed(0.6), _ed(0.61))
    if stable and 1 <= n <= 2:
        _ok("V-G1-DIFF", f"canonical stable; one-change leaves={n} (proportional)")
    else:
        _fail("V-G1-DIFF", f"stable={stable} n={n}")

    # V-G1-CAPABILITY: host that cannot restore scroll -> dropped + reported
    full, rep_full = G1M.mark_unrestorable(_ed(0.6), G1M.DEFAULT_HOST_CAPABILITIES)
    ltd, rep_ltd = G1M.mark_unrestorable(_ed(0.6), frozenset({"tabs", "focus"}))
    if "scroll" in full and "scroll" not in ltd and any("scroll" in r for r in rep_ltd):
        _ok("V-G1-CAPABILITY", "limited host drops+reports scroll; full host keeps it")
    else:
        _fail("V-G1-CAPABILITY", f"full_has_scroll={'scroll' in full} ltd_has={'scroll' in ltd}")

    # V-G1-G4-CAPABILITY-WIRE: scroll-limited host -> RECOVERED; full host -> FAILED
    def _desc(ed):
        return {"schema_version": 1, "captured_at": "t", "windows": [{
            "window_id": "w1", "workspace_path": "C:/r", "foreground": True,
            "terminals": [{"pane_id": "p1", "cwd": "C:/r", "conversation_id": "X"}],
            "editor": ed}]}
    sc = G4.score_recovery(_desc(_ed(0.6)), _desc(_ed(0.1)))  # scroll diverges beyond tol
    v_ltd = G4.equivalence_verdict(sc, host_capabilities=G1M.g4_host_capabilities(frozenset({"tabs", "focus"})))
    v_full = G4.equivalence_verdict(sc, host_capabilities=G1M.g4_host_capabilities())
    if v_ltd == G4.RECOVERED and v_full == G4.FAILED:
        _ok("V-G1-G4-CAPABILITY-WIRE", "scroll-limited host -> RECOVERED; scroll-capable -> FAILED")
    else:
        _fail("V-G1-G4-CAPABILITY-WIRE", f"limited={v_ltd} full={v_full}")

    # V-G1-COMPOSE: editor -> per-window desc (G2) -> G3 versioned -> G4 RECOVERED
    with tempfile.TemporaryDirectory() as td:
        wsp = Path(td) / "repo"
        wsp.mkdir()
        reg = G2M.WindowRegistry(Path(td))
        reg.register("w1", str(wsp), foreground=True,
                     panes=[{"pane_id": "p1", "cwd": str(wsp), "conversation_id": "X"}])
        wdesc = G2M.window_state_description(reg.get("w1"), editor=_ed(0.6))
        with tempfile.TemporaryDirectory() as td2:
            st = G3M.SessionVersionStore(Path(td2))
            back = st.reconstruct(st.record(wdesc, "w1"))
        gate = G4.acceptance_gate(G4.score_recovery(wdesc, back))
        if gate.verdict == G4.RECOVERED:
            _ok("V-G1-COMPOSE", "editor -> G2 window desc -> G3 versioned -> G4 RECOVERED")
        else:
            _fail("V-G1-COMPOSE", f"verdict={gate.verdict}")

    # V-G1-EXTENSION-SPEC: the capture/apply contract artifact exists (not stubbed code)
    spec = _ROOT / "vault" / "knowledge_base" / "session_resilience" / "G1_EXTENSION_CAPTURE_SPEC.md"
    if spec.is_file() and "Owner-run" in spec.read_text(encoding="utf-8-sig"):
        _ok("V-G1-EXTENSION-SPEC", "extension capture/apply spec present; visual gate marked Owner-run")
    else:
        _fail("V-G1-EXTENSION-SPEC", f"spec_exists={spec.is_file()}")


def gates_sprint6() -> None:
    from modules.session_resilience import integration as INT

    A = _state(scroll_a=0.5)

    # V-INTEGRATION-HUB: crash with state preserved -> RECOVERED verdict from hub
    with tempfile.TemporaryDirectory() as td:
        INT.on_session_start(Path(td), A, crash_suspected=False)      # v0 = A
        r = INT.on_session_start(Path(td), A, crash_suspected=True)   # current==prior -> RECOVERED
        if r.get("recovery") and r["recovery"]["verdict"] == G4.RECOVERED and not r["fail_open"]:
            _ok("V-INTEGRATION-HUB", f"crash + preserved state -> hub verdict {r['recovery']['verdict']}")
        else:
            _fail("V-INTEGRATION-HUB", f"r={r}")

    # V-INTEGRATION-HUB-GAP: crash with changed state -> gap detected + G5 event
    with tempfile.TemporaryDirectory() as td:
        INT.on_session_start(Path(td), A, crash_suspected=False)
        B = _state(scroll_a=0.5, tabs=("a.py",))  # differs (tabs/editor)
        r = INT.on_session_start(Path(td), B, crash_suspected=True)
        evs = G5.RecoveryEventCollector(state_dir=Path(td)).read()
        has_crash = any(e.get("type") == "crash_detected" for e in evs)
        if r["recovery"]["verdict"] != G4.RECOVERED and has_crash:
            _ok("V-INTEGRATION-HUB-GAP", f"gap -> {r['recovery']['verdict']}; G5 logged crash_detected")
        else:
            _fail("V-INTEGRATION-HUB-GAP", f"verdict={r['recovery']['verdict']} crash_logged={has_crash}")

    # V-INTEGRATION-HUB-FAILOPEN: a storage failure must NOT block session start
    with tempfile.TemporaryDirectory() as td:
        afile = Path(td) / "not_a_dir"
        afile.write_text("x", encoding="utf-8")
        r = INT.on_session_start(afile, A, crash_suspected=False)
        if r.get("fail_open"):
            _ok("V-INTEGRATION-HUB-FAILOPEN", "store failure -> fail-open, session start not blocked")
        else:
            _fail("V-INTEGRATION-HUB-FAILOPEN", f"r={r}")

    # V-INTEGRATION-RAM: ram threshold -> validated snapshot + safe advisory
    with tempfile.TemporaryDirectory() as td:
        r = INT.on_ram_threshold(Path(td), A)
        if r["valid"] and r["advisory"] == "snapshot seguro guardado":
            _ok("V-INTEGRATION-RAM", "ram threshold -> G4-validated snapshot; advisory='snapshot seguro guardado'")
        else:
            _fail("V-INTEGRATION-RAM", f"r={r}")


def gates_g6() -> None:
    from modules.session_resilience import power_beacon as PB
    from modules.session_resilience import reentry as RE
    from modules.session_resilience import resume_identity as RI

    NOW = "2026-06-29T12:00:00Z"

    # V-G6-BEACON-PERSISTS: an active beacon survives a simulated power-loss (the
    # process dies without a graceful close) -- the fsync'd file is on disk and a
    # fresh classify reads it as ungraceful via the two-signal rule.
    with tempfile.TemporaryDirectory() as td:
        PB.write_active_beacon(td, session_id="s1", cwd="C:/repos/pp", now=NOW)
        persisted = (Path(td) / PB.BEACON_FILENAME).is_file()  # survived "kill -9"
        cls = PB.classify_startup(td, live_terminal_count=0)
        if persisted and cls["class"] == PB.UNGRACEFUL and len(cls["signals"]) >= 2:
            _ok("V-G6-BEACON-PERSISTS",
                f"fsync'd beacon survives crash -> {cls['class']} ({len(cls['signals'])} signals)")
        else:
            _fail("V-G6-BEACON-PERSISTS", f"persisted={persisted} cls={cls['class']}")

    # V-G6-CLASSIFY: first-run vs reload vs graceful-reopen are all distinct.
    with tempfile.TemporaryDirectory() as td:
        first = PB.classify_startup(td, 0)["class"]
        PB.write_active_beacon(td, now=NOW)
        reload_c = PB.classify_startup(td, live_terminal_count=3)["class"]
        PB.write_graceful_exit(td, now=NOW)
        graceful = PB.classify_startup(td, 0)["class"]
        if first == PB.FIRST_RUN and reload_c == PB.RELOAD and graceful == PB.GRACEFUL_REOPEN:
            _ok("V-G6-CLASSIFY", f"first={first} reload={reload_c} graceful={graceful} (distinct)")
        else:
            _fail("V-G6-CLASSIFY", f"first={first} reload={reload_c} graceful={graceful}")

    pane_map = {"panes": [
        {"sessionId": "aaa", "cwd": "C:/repos/pp", "repo": "pp",
         "resumeCmd": "claude --resume aaa", "live": True, "topic": "G6 power transitions build"},
        {"sessionId": "bbb", "cwd": "C:/repos/x", "repo": "x",
         "resumeCmd": "claude --resume bbb", "live": True, "topic": "fix crash in loader"},
        {"sessionId": "ccc", "cwd": "C:/repos/y", "repo": "y",
         "resumeCmd": "claude --resume ccc", "live": False, "topic": "old research audit"},
    ]}

    # V-G6-REENTRY-EVENT: ungraceful -> G5 stream w/ cause + G4 RECOVERED (all live restorable).
    with tempfile.TemporaryDirectory() as td:
        PB.write_active_beacon(td, now=NOW)
        cls = PB.classify_startup(td, 0)
        res = RE.record_reentry(td, cls, pane_map, now=NOW)
        evs = G5.RecoveryEventCollector(state_dir=Path(td)).read()
        started = [e for e in evs if e.get("type") == "recovery_started" and e.get("cause") == RE.CAUSE]
        completed = [e for e in evs if e.get("type") == "recovery_completed"]
        if (res["verdict"] == G4.RECOVERED and res["restorable_panes"] == 2
                and started and completed and completed[0]["verdict"] == G4.RECOVERED):
            _ok("V-G6-REENTRY-EVENT",
                f"ungraceful -> G5 cause={RE.CAUSE}, G4={res['verdict']}, panes={res['restorable_panes']}")
        else:
            _fail("V-G6-REENTRY-EVENT",
                  f"res={res} started={len(started)} completed={len(completed)}")

    # V-G6-REENTRY-GAP: a live pane missing its session id is a real miss -> not RECOVERED.
    gap_map = {"panes": [
        {"sessionId": "aaa", "cwd": "C:/repos/pp", "repo": "pp",
         "resumeCmd": "claude --resume aaa", "live": True, "topic": "build"},
        {"sessionId": "", "cwd": "C:/repos/z", "repo": "z",
         "resumeCmd": "", "live": True, "topic": "unrestorable pane"},
    ]}
    with tempfile.TemporaryDirectory() as td:
        PB.write_active_beacon(td, now=NOW)
        cls = PB.classify_startup(td, 0)
        res = RE.record_reentry(td, cls, gap_map, now=NOW)
        if res["verdict"] != G4.RECOVERED and res["missing"] and res["restorable_panes"] == 1:
            _ok("V-G6-REENTRY-GAP",
                f"unrestorable live pane -> {res['verdict']}, missing={len(res['missing'])}")
        else:
            _fail("V-G6-REENTRY-GAP", f"res={res}")

    # V-G6-NO-OP: a graceful reopen records NOTHING (no false recovery).
    with tempfile.TemporaryDirectory() as td:
        PB.write_graceful_exit(td, now=NOW)
        cls = PB.classify_startup(td, 0)
        res = RE.record_reentry(td, cls, pane_map, now=NOW)
        evs = G5.RecoveryEventCollector(state_dir=Path(td)).read()
        if res["verdict"] is None and not evs:
            _ok("V-G6-NO-OP", "graceful reopen -> no recovery recorded (no false positive)")
        else:
            _fail("V-G6-NO-OP", f"res={res} evs={len(evs)}")

    # V-RESUME-TASKTYPE: work-type classification across the taxonomy.
    cases = {
        "fix the crash in the loader": "debug",
        "ULTRA-PLAN MODE design the dataset family": "architecture",
        "research the audit findings": "research",
        "build G6 runtime and wire it": "feature",
        "say hello": "general",
    }
    got = {k: RI.classify_task_type(k) for k in cases}
    if got == cases:
        _ok("V-RESUME-TASKTYPE", f"5/5 work-types classified: {sorted(set(got.values()))}")
    else:
        _fail("V-RESUME-TASKTYPE", f"got={got}")

    # V-RESUME-LABEL: a human label, never a raw UUID.
    lbl = RI.build_label("claude-power-pack", "G6 Power Transitions runtime build", task_type="feature")
    uuid_lbl = RI.build_label("pp", "4fc2ab12-0000-1111-2222-333344445555")
    if RI.label_is_human(lbl) and "(feature)" in lbl and not RI.label_is_human(uuid_lbl):
        _ok("V-RESUME-LABEL", f"human label '{lbl}'; raw-uuid topic flagged non-human")
    else:
        _fail("V-RESUME-LABEL",
              f"lbl='{lbl}' human={RI.label_is_human(lbl)} uuid_human={RI.label_is_human(uuid_lbl)}")

    # V-RESUME-CATALOG: persisted catalog with real fields.
    with tempfile.TemporaryDirectory() as td:
        cat = RI.build_catalog(pane_map["panes"], td, now=NOW)
        loaded = RI.load_catalog(td)
        entry = next((e for e in loaded if e["session_id"] == "aaa"), None)
        if ((Path(td) / RI.CATALOG_FILENAME).is_file() and len(cat) == 3
                and entry and entry["task_type"] and entry["repo"] == "pp"):
            _ok("V-RESUME-CATALOG",
                f"{len(cat)} sessions persisted; real fields (aaa type={entry['task_type']})")
        else:
            _fail("V-RESUME-CATALOG", f"cat={len(cat)} entry={entry}")

    # V-RESUME-SEARCH: relevant query ranks; nonsense query returns [].
    with tempfile.TemporaryDirectory() as td:
        RI.build_catalog(pane_map["panes"], td, now=NOW)
        cat = RI.load_catalog(td)
        hits = RI.search(cat, "crash loader")
        none = RI.search(cat, "zzzznomatch")
        if hits and hits[0]["session_id"] == "bbb" and not none:
            _ok("V-RESUME-SEARCH", f"'crash loader' -> {hits[0]['repo']} top; nonsense -> []")
        else:
            _fail("V-RESUME-SEARCH", f"hits={[h['session_id'] for h in hits]} none={none}")


def main() -> int:
    gates_g4()
    gates_g5()
    gates_g3()
    gates_g2()
    gates_g1()
    gates_integration()
    gates_sprint6()
    gates_g6()
    print("--- ADVISORY (OWNER-RUN, not counted) ---")
    print("OWNER  V-G1-CONTRACT: 'OOM crash == Reload Window' visual indistinguishability is a")
    print("       GUI check with no CLI -- run after the G1 extension lands (SCS C50 precedent).")
    print(f"SESSION_RESILIENCE_BUILD_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
