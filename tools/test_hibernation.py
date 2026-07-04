#!/usr/bin/env python3
"""test_hibernation.py -- V-gates for Transparent Process Hibernation (FASE A).

Hermetic: every test uses tmp dirs + an explicit ``now`` (no global writes, no
wall-clock dependency), so the suite is stable under rapid re-runs.

Run:  python tools/test_hibernation.py    (exit 0 = all gates pass)
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.cognitive_os import process_governor as pg  # noqa: E402
from modules.cognitive_os import hibernate_runner as hr  # noqa: E402
from modules.cognitive_os import hibernation  # noqa: E402
from modules.cognitive_os import rehydration as rehy  # noqa: E402
import run_hibernation as rhn  # noqa: E402  (tools/ is sys.path[0] when run direct)


def _proj_with_idle_pane(base: Path, cwd: str, sid: str, idle_min: float):
    """Materialize a tmp projects tree with one transcript whose last turn is
    ``idle_min`` old, and return the raw scan record that maps to it."""
    enc = pg._enc(cwd)
    (base / enc).mkdir(parents=True, exist_ok=True)
    tp = base / enc / f"{sid}.jsonl"
    ts = (NOW - timedelta(minutes=idle_min)).isoformat()
    tp.write_text(json.dumps({"timestamp": ts, "type": "user"}) + "\n",
                  encoding="utf-8")
    return {"pid": 700, "wrapper_pid": 701, "ws_mb": 260.0,
            "wrapper_kind": "ps1", "sid": sid, "cwd": cwd,
            "is_foreground": False, "is_loop": False}

_passes = 0
_fails = 0


class _FakeHR:
    """Stand-in for CO-07 hibernation.HibernationResult (store outcome)."""
    def __init__(self, ok, reason="", archive_id="arc-1"):
        self.ok = ok
        self.reason = reason
        self.archive_id = archive_id


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS {gate}: {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {gate}: {diag}")


NOW = datetime(2026, 7, 3, 12, 0, 0, tzinfo=timezone.utc)


def _pane(**kw) -> pg.PaneProc:
    """A clean, hibernatable baseline pane; override fields per test."""
    base = dict(pid=1000, wrapper_pid=900, sid="s-abcdef12", cwd="C:/repo",
                ws_mb=250.0, idle_min=30.0, is_foreground=False, is_loop=False,
                wrapper_kind="ps1", has_anchor=True)
    base.update(kw)
    return pg.PaneProc(**base)


# --- SPRINT 1: Resource Governor decision gates ------------------------------

def test_governor_hibernates_clean_idle():
    # Arrange
    pane = _pane(idle_min=30.0, ws_mb=250.0)
    # Act
    d = pg.decide(pane)
    # Assert
    if d.verdict == pg.HIBERNATE and d.reclaim_mb == 250.0 and d.wakeable:
        _ok("V-GOVERNOR-HIBERNATES",
            f"clean idle pane -> hibernate, reclaim {d.reclaim_mb}MB")
    else:
        _fail("V-GOVERNOR-HIBERNATES", f"got {d.verdict} reclaim={d.reclaim_mb}")


def test_governor_respects_foreground():
    d = pg.decide(_pane(is_foreground=True))
    if d.verdict == pg.KEEP and any("foreground" in r for r in d.reasons):
        _ok("V-GOVERNOR-RESPECTS-ACTIVE", "foreground pane kept")
    else:
        _fail("V-GOVERNOR-RESPECTS-ACTIVE", f"got {d.verdict} {d.reasons}")


def test_governor_respects_loop():
    d = pg.decide(_pane(is_loop=True))
    if d.verdict == pg.KEEP and any("/loop" in r for r in d.reasons):
        _ok("V-GOVERNOR-RESPECTS-LOOP", "loop pane kept")
    else:
        _fail("V-GOVERNOR-RESPECTS-LOOP", f"got {d.verdict} {d.reasons}")


def test_governor_respects_hot():
    # A pane active 2min ago is under the 15min threshold -> hot -> keep.
    d = pg.decide(_pane(idle_min=2.0))
    if d.verdict == pg.KEEP and any("hot" in r for r in d.reasons):
        _ok("V-GOVERNOR-RESPECTS-HOT", "recently-active pane kept")
    else:
        _fail("V-GOVERNOR-RESPECTS-HOT", f"got {d.verdict} {d.reasons}")


def test_governor_keeps_unknown_idle():
    d = pg.decide(_pane(idle_min=None))
    if d.verdict == pg.KEEP and any("unknown" in r for r in d.reasons):
        _ok("V-GOVERNOR-KEEPS-UNKNOWN", "unknown idle -> fail-safe keep")
    else:
        _fail("V-GOVERNOR-KEEPS-UNKNOWN", f"got {d.verdict} {d.reasons}")


def test_governor_keeps_no_anchor():
    d = pg.decide(_pane(has_anchor=False))
    if d.verdict == pg.KEEP and any("anchor" in r for r in d.reasons):
        _ok("V-GOVERNOR-KEEPS-NOANCHOR", "no anchor -> keep (would REFUSE)")
    else:
        _fail("V-GOVERNOR-KEEPS-NOANCHOR", f"got {d.verdict} {d.reasons}")


def test_governor_keeps_raw_pane():
    d = pg.decide(_pane(wrapper_kind="none"))
    if d.verdict == pg.KEEP and any("reap deferred" in r for r in d.reasons):
        _ok("V-GOVERNOR-KEEPS-RAW", "non-wakeable pane kept (no reap in FASE A)")
    else:
        _fail("V-GOVERNOR-KEEPS-RAW", f"got {d.verdict} {d.reasons}")


def test_plan_aggregates_reclaim():
    # Arrange: 2 hibernatable + 1 foreground kept
    panes = [_pane(pid=1, ws_mb=200.0), _pane(pid=2, ws_mb=300.0),
             _pane(pid=3, is_foreground=True, ws_mb=999.0)]
    # Act
    gp = pg.plan(panes)
    # Assert
    if (gp.hibernate_count == 2 and gp.keep_count == 1
            and gp.reclaim_mb == 500.0):
        _ok("V-GOVERNOR-PLAN-RECLAIM",
            f"2 hibernate / 1 keep, reclaim {gp.reclaim_mb}MB (foreground excluded)")
    else:
        _fail("V-GOVERNOR-PLAN-RECLAIM",
              f"hib={gp.hibernate_count} keep={gp.keep_count} rec={gp.reclaim_mb}")


def test_idle_age_reader():
    # Arrange: a synthetic transcript whose last turn is 40min before NOW
    with tempfile.TemporaryDirectory() as td:
        tp = Path(td) / "sess.jsonl"
        old = (NOW - timedelta(minutes=40)).isoformat()
        recent = (NOW - timedelta(minutes=40)).isoformat()
        tp.write_text(
            json.dumps({"timestamp": old, "type": "user"}) + "\n"
            + json.dumps({"timestamp": recent, "type": "assistant"}) + "\n",
            encoding="utf-8")
        # Act
        age = pg.last_turn_age_min(tp, now=NOW)
        # Assert
        if age is not None and abs(age - 40.0) < 0.5:
            _ok("V-IDLE-AGE-READER", f"read last-turn age = {age:.1f}min")
        else:
            _fail("V-IDLE-AGE-READER", f"expected ~40, got {age}")


def test_idle_age_reader_missing():
    age = pg.last_turn_age_min("C:/nonexistent/nope.jsonl", now=NOW)
    if age is None:
        _ok("V-IDLE-AGE-MISSING", "missing transcript -> None (unknown)")
    else:
        _fail("V-IDLE-AGE-MISSING", f"expected None, got {age}")


def test_governor_keeps_no_sid():
    d = pg.decide(_pane(sid=None))
    if d.verdict == pg.KEEP and any("session id" in r for r in d.reasons):
        _ok("V-GOVERNOR-KEEPS-NOSID", "unresolved sid -> keep (cannot --resume)")
    else:
        _fail("V-GOVERNOR-KEEPS-NOSID", f"got {d.verdict} {d.reasons}")


# --- SPRINT 2: loop-boundedness advisory (post-Kickbacks, advisory only) ------

def test_advisory_unbounded():
    # Session active 150min (> 2h) but recently working (idle 10min) -> unbounded
    # NOTE (informational), never stalled.
    a = pg.loop_advisory(_pane(session_age_min=150.0, idle_min=10.0))
    if a and a["level"] == "unbounded" and "unbounded" in a["message"]:
        _ok("V-UNBOUNDED-ADVISORY",
            "150min session, idle 10min -> unbounded NOTE (informational)")
    else:
        _fail("V-UNBOUNDED-ADVISORY", f"got {a}")


def test_advisory_stalled():
    # No output in 45min AND session 90min total -> stalled WARN (stronger).
    a = pg.loop_advisory(_pane(session_age_min=90.0, idle_min=45.0))
    if a and a["level"] == "stalled" and "stalled" in a["message"]:
        _ok("V-STALLED-ADVISORY",
            "idle 45min + session 90min -> stalled WARN (probably hung)")
    else:
        _fail("V-STALLED-ADVISORY", f"got {a}")


def test_advisory_active_silent():
    # A pane with real recent work (idle 2min, session 40min) -> SILENCE.
    a = pg.loop_advisory(_pane(session_age_min=40.0, idle_min=2.0))
    d = pg.decide(_pane(session_age_min=40.0, idle_min=2.0))
    if a is None and d.verdict == pg.KEEP:
        _ok("V-ACTIVE-SILENT",
            "active pane (idle 2min) -> no advisory + kept (not hibernated)")
    else:
        _fail("V-ACTIVE-SILENT", f"advisory={a} verdict={d.verdict}")


def test_advisory_failopen_unknown_age():
    # Session age unknown -> None (silence, NEVER a false positive).
    a = pg.loop_advisory(_pane(session_age_min=None, idle_min=200.0))
    if a is None:
        _ok("V-LOOP-BOUNDEDNESS-FAILOPEN",
            "unknown session age -> None (fail-open silence, no false positive)")
    else:
        _fail("V-LOOP-BOUNDEDNESS-FAILOPEN", f"expected None, got {a}")


def test_advisory_orthogonal_to_verdict():
    # An unbounded/foreground pane: decide() KEEPS it (foreground) AND the
    # advisory fires -- proving the advisory never drives the kill decision.
    pane = _pane(is_foreground=True, session_age_min=200.0, idle_min=5.0)
    d = pg.decide(pane)
    a = pg.loop_advisory(pane)
    if d.verdict == pg.KEEP and a and a["level"] == "unbounded":
        _ok("V-GOVERNOR-ACTIVE-NOT-HIBERNATED",
            "advisory is orthogonal: foreground kept, unbounded NOTE still emitted")
    else:
        _fail("V-GOVERNOR-ACTIVE-NOT-HIBERNATED", f"verdict={d.verdict} adv={a}")


def test_session_age_reader():
    # Hermetic: a transcript whose FIRST turn is 150min before NOW.
    with tempfile.TemporaryDirectory() as td:
        tp = Path(td) / "sess.jsonl"
        first = (NOW - timedelta(minutes=150)).isoformat()
        last = (NOW - timedelta(minutes=5)).isoformat()
        tp.write_text(
            json.dumps({"timestamp": first, "type": "user"}) + "\n"
            + json.dumps({"timestamp": last, "type": "assistant"}) + "\n",
            encoding="utf-8")
        age = pg.session_start_age_min(tp, now=NOW)
        if age is not None and abs(age - 150.0) < 0.5:
            _ok("V-SESSION-AGE-READER",
                f"read session start age = {age:.0f}min (from first turn)")
        else:
            _fail("V-SESSION-AGE-READER", f"expected ~150, got {age}")


def test_plan_collects_advisories():
    # plan() collects advisories WITHOUT altering hibernate/keep counts.
    panes = [_pane(pid=1, session_age_min=150.0, idle_min=40.0),  # stalled
             _pane(pid=2, session_age_min=30.0, idle_min=20.0)]   # clean, silent
    gp = pg.plan(panes)
    if (len(gp.advisories) == 1 and gp.advisories[0]["level"] == "stalled"
            and gp.hibernate_count == 2 and gp.keep_count == 0):
        _ok("V-ADVISORY-IN-PLAN",
            "plan collects 1 advisory; hibernate/keep counts unaffected")
    else:
        _fail("V-ADVISORY-IN-PLAN",
              f"adv={len(gp.advisories)} hib={gp.hibernate_count} keep={gp.keep_count}")


# --- SPRINT 3: hibernation executor (store -> flag -> kill) -------------------

def test_hibernate_store_then_kill():
    # Arrange
    with tempfile.TemporaryDirectory() as td:
        killed = []
        pane = _pane(pid=4242, wrapper_pid=900, ws_mb=250.0)

        def kill_fn(pid):
            # Order gate: the wake flag MUST already exist when we kill.
            flag = hr.flag_path_for(900, td)
            if not flag.is_file():
                return False  # would mean flag written AFTER kill -> wrong order
            killed.append(pid)
            return True

        # Act
        run = hr.hibernate_pane(pane, flag_dir=td,
                                hibernate_fn=lambda *a, **k: _FakeHR(True),
                                kill_fn=kill_fn, now=NOW)
        # Assert
        flag = hr.flag_path_for(900, td)
        if (run.ok and run.verdict == "HIBERNATED" and killed == [4242]
                and flag.is_file() and run.reclaim_mb == 250.0):
            payload = json.loads(flag.read_text(encoding="utf-8"))
            if payload.get("sid") == pane.sid:
                _ok("V-HIBERNATE-STORE-THEN-KILL",
                    "store->flag->kill in order; flag carries sid; "
                    f"reclaim {run.reclaim_mb}MB")
            else:
                _fail("V-HIBERNATE-STORE-THEN-KILL", f"flag sid wrong: {payload}")
        else:
            _fail("V-HIBERNATE-STORE-THEN-KILL",
                  f"verdict={run.verdict} killed={killed} flag={flag.is_file()}")


def test_hibernate_refuse_no_store():
    with tempfile.TemporaryDirectory() as td:
        killed = []
        run = hr.hibernate_pane(
            _pane(pid=5, wrapper_pid=901), flag_dir=td,
            hibernate_fn=lambda *a, **k: _FakeHR(False, "anchor missing"),
            kill_fn=lambda pid: killed.append(pid) or True, now=NOW)
        flag = hr.flag_path_for(901, td)
        if (not run.ok and run.verdict == "REFUSED" and not killed
                and not flag.is_file()):
            _ok("V-HIBERNATE-REFUSE-NO-STORE",
                "CO-07 refused -> no flag, no kill, process untouched")
        else:
            _fail("V-HIBERNATE-REFUSE-NO-STORE",
                  f"verdict={run.verdict} killed={killed} flag={flag.is_file()}")


def test_hibernate_kill_rollback():
    with tempfile.TemporaryDirectory() as td:
        run = hr.hibernate_pane(
            _pane(pid=6, wrapper_pid=902), flag_dir=td,
            hibernate_fn=lambda *a, **k: _FakeHR(True),
            kill_fn=lambda pid: False, now=NOW)  # kill fails
        flag = hr.flag_path_for(902, td)
        if (not run.ok and run.verdict == "KILL_FAILED" and not run.killed
                and not flag.is_file()):
            _ok("V-HIBERNATE-KILL-ROLLBACK",
                "kill failed -> flag rolled back (no stale flag traps wrapper)")
        else:
            _fail("V-HIBERNATE-KILL-ROLLBACK",
                  f"verdict={run.verdict} flag_exists={flag.is_file()}")


def test_run_plan_executes_targets():
    with tempfile.TemporaryDirectory() as td:
        panes = [_pane(pid=10, wrapper_pid=910, ws_mb=200.0),
                 _pane(pid=11, is_foreground=True)]  # 2nd kept
        gp = pg.plan(panes)
        runs = hr.run_plan(gp, flag_dir=td,
                           hibernate_fn=lambda *a, **k: _FakeHR(True),
                           kill_fn=lambda pid: True, now=NOW)
        if len(runs) == 1 and runs[0].ok and runs[0].pid == 10:
            _ok("V-RAM-FREED",
                f"plan executed 1 target (foreground skipped), reclaim "
                f"{runs[0].reclaim_mb}MB freed")
        else:
            _fail("V-RAM-FREED", f"runs={[(r.pid, r.verdict) for r in runs]}")


# --- SPRINT 4: rehydration + G4 identity verify (real CO-07 round-trip) -------

def test_g4_verified_roundtrip():
    # REAL hibernate -> restore -> G4 identity verify (no mocks anywhere).
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        reg = tdp / "hib.jsonl"
        anchor = tdp / "sess.jsonl"
        anchor.write_text("{}\n", encoding="utf-8")
        sid = "sess-abcd-1234"
        res = hibernation.hibernate(sid, str(tdp), transcript_path=str(anchor),
                                    now=NOW, registry_path=str(reg))
        if not res.ok:
            _fail("V-G4-VERIFIED", f"CO-07 store failed: {res.reason}")
            return
        v = rehy.verify_rehydration(res.archive_id, sid, registry_path=str(reg))
        if v.verdict == "RECOVERED" and v.sid == sid and v.accepted:
            _ok("V-G4-VERIFIED",
                "real hibernate->restore->verify: RECOVERED, sid matches")
        else:
            _fail("V-G4-VERIFIED",
                  f"verdict={v.verdict} sid={v.sid} reason={v.reason}")


def test_g4_failed_sid_mismatch():
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        reg = tdp / "hib.jsonl"
        anchor = tdp / "sess.jsonl"
        anchor.write_text("{}\n", encoding="utf-8")
        res = hibernation.hibernate("real-sid", str(tdp),
                                    transcript_path=str(anchor), now=NOW,
                                    registry_path=str(reg))
        v = rehy.verify_rehydration(res.archive_id, "WRONG-sid",
                                    registry_path=str(reg))
        if v.verdict == "FAILED" and "identity" in v.missing:
            _ok("V-G4-FAILED-MISMATCH",
                "restored sid != resumed sid -> FAILED (never the wrong session)")
        else:
            _fail("V-G4-FAILED-MISMATCH", f"verdict={v.verdict} missing={v.missing}")


def test_rehydrate_flag_roundtrip():
    # The wrapper reads the wake flag via ConvertFrom-Json; prove the contract.
    with tempfile.TemporaryDirectory() as td:
        pane = _pane(pid=77, wrapper_pid=903, sid="sess-77", cwd="C:/some/repo")
        run = hr.hibernate_pane(
            pane, flag_dir=td,
            hibernate_fn=lambda *a, **k: _FakeHR(True, archive_id="arc-77"),
            kill_fn=lambda pid: True, now=NOW)
        flag = hr.flag_path_for(903, td)
        payload = json.loads(flag.read_text(encoding="utf-8"))
        if (run.ok and payload.get("sid") == "sess-77"
                and payload.get("cwd") == "C:/some/repo"
                and payload.get("archive_id") == "arc-77"):
            _ok("V-REHYDRATE-FLAG-ROUNDTRIP",
                "wrapper reads sid+cwd+archive from the wake flag (contract intact)")
        else:
            _fail("V-REHYDRATE-FLAG-ROUNDTRIP", f"payload={payload}")


def test_enrich_resolves_idle_and_anchor():
    # Hermetic: a tmp projects base with a real transcript whose last turn is
    # 40min old. enrich must resolve idle_min + has_anchor from it and, since
    # 40min > 15min threshold (and NOT force-kept by the 120min CO-08 window),
    # the pane is selected. Guards the enrich/idle-granularity bug.
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        cwd = "C:/work/repoX"
        sid = "sess-enrich-1"
        enc = pg._enc(cwd)
        (base / enc).mkdir(parents=True)
        tp = base / enc / f"{sid}.jsonl"
        old = (NOW - timedelta(minutes=40)).isoformat()
        tp.write_text(json.dumps({"timestamp": old, "type": "user"}) + "\n",
                      encoding="utf-8")
        raw = [{"pid": 321, "wrapper_pid": 320, "ws_mb": 240.0,
                "wrapper_kind": "ps1", "sid": sid, "cwd": cwd,
                "is_foreground": False, "is_loop": False}]
        panes = pg.enrich_panes(raw, now=NOW, proj_base=str(base))
        if not panes:
            _fail("V-ENRICH-RESOLVES", "enrich returned no panes")
            return
        p = panes[0]
        d = pg.decide(p)
        if (p.has_anchor and p.idle_min is not None
                and abs(p.idle_min - 40.0) < 0.5 and d.verdict == pg.HIBERNATE):
            _ok("V-ENRICH-RESOLVES",
                f"raw scan -> idle {p.idle_min:.0f}min + anchor -> hibernate "
                f"(120min window correctly NOT force-keeping a 40min-idle pane)")
        else:
            _fail("V-ENRICH-RESOLVES",
                  f"idle={p.idle_min} anchor={p.has_anchor} decide={d.verdict}")


def test_orchestrator_dry_no_side_effects():
    with tempfile.TemporaryDirectory() as td:
        base = Path(td) / "proj"
        flags = Path(td) / "flags"
        flags.mkdir()
        raw = [_proj_with_idle_pane(base, "C:/w/rx", "sess-dry", 40.0)]
        gp, runs = rhn.run(raw, flag_dir=str(flags), live=False,
                           proj_base=str(base), now=NOW)
        flag = hr.flag_path_for(701, str(flags))
        if (gp.hibernate_count == 1 and runs == []
                and not flag.is_file() and not any(flags.iterdir())):
            _ok("V-ORCHESTRATOR-DRY",
                "dry run: plan selects 1 target but writes NO flag + kills nothing")
        else:
            _fail("V-ORCHESTRATOR-DRY",
                  f"hib={gp.hibernate_count} runs={len(runs)} flag={flag.is_file()}")


def test_orchestrator_live_executes():
    with tempfile.TemporaryDirectory() as td:
        base = Path(td) / "proj"
        flags = Path(td) / "flags"
        flags.mkdir()
        raw = [_proj_with_idle_pane(base, "C:/w/rx", "sess-live", 40.0)]
        killed = []
        gp, runs = rhn.run(raw, flag_dir=str(flags), live=True,
                           proj_base=str(base), now=NOW,
                           hibernate_fn=lambda *a, **k: _FakeHR(True),
                           kill_fn=lambda pid: killed.append(pid) or True)
        if (gp.hibernate_count == 1 and len(runs) == 1 and runs[0].ok
                and killed == [700]):
            _ok("V-ORCHESTRATOR-LIVE",
                f"live run: executed 1 target, killed pid {killed[0]}")
        else:
            _fail("V-ORCHESTRATOR-LIVE",
                  f"hib={gp.hibernate_count} runs={len(runs)} killed={killed}")


def main() -> int:
    print("== Transparent Process Hibernation -- FASE A V-gates ==")
    print("- SPRINT 1/3/4/5: Governor + executor + rehydrate + orchestrator")
    for fn in (test_governor_hibernates_clean_idle,
               test_governor_respects_foreground,
               test_governor_respects_loop,
               test_governor_respects_hot,
               test_governor_keeps_unknown_idle,
               test_governor_keeps_no_anchor,
               test_governor_keeps_raw_pane,
               test_governor_keeps_no_sid,
               test_advisory_unbounded,
               test_advisory_stalled,
               test_advisory_active_silent,
               test_advisory_failopen_unknown_age,
               test_advisory_orthogonal_to_verdict,
               test_session_age_reader,
               test_plan_collects_advisories,
               test_plan_aggregates_reclaim,
               test_idle_age_reader,
               test_idle_age_reader_missing,
               test_hibernate_store_then_kill,
               test_hibernate_refuse_no_store,
               test_hibernate_kill_rollback,
               test_run_plan_executes_targets,
               test_g4_verified_roundtrip,
               test_g4_failed_sid_mismatch,
               test_rehydrate_flag_roundtrip,
               test_enrich_resolves_idle_and_anchor,
               test_orchestrator_dry_no_side_effects,
               test_orchestrator_live_executes):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            _fail(fn.__name__, f"raised {exc!r}")
    total = _passes + _fails
    print(f"HIBERNATION_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
