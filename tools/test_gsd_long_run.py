"""V-GSDLR-* gates for /cpp-gsd-long v2 (spec vault/specs/gsd-long-run-v2.md).

Everything that would touch the Owner's live state is redirected:
  GSD_LONG_RUN_STATE_DIR / _HOOKS_DIR / _PROJECTS_DIR -> temp dirs,
  GSD_LONG_RUN_NO_SPAWN=1 (the sweep never launches the real Enter daemon),
  the watchdog's _write_trigger_flag/_spawn_daemon are recorders.
The one exception is the marker file itself (tools/gsd_autorun_marker.py keeps
its STATE_DIR constant, as the existing suite relies on): markers are written
under random `gsdlr-` session ids and removed in `finally`.

One gate reads a REAL project read-only (V-GSDLR-REAL-GSD-ABSW2): the whole
point of gap 8 is what the real gsd-tools parser does with a real roadmap.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
WATCHDOG = ROOT / "modules" / "zero-crash" / "hooks" / "context-watchdog.py"
PY = sys.executable
ABSW2 = Path.home() / "Desktop" / "Cursor Projects" / "Wii Projects" / "ABSW2-Wii"

TMP = Path(tempfile.mkdtemp(prefix="gsdlr-"))
STATE = TMP / "state"
HOOKS = TMP / "hooks"
PROJECTS = TMP / "projects"
SESSIONS = TMP / "sessions"
for d in (STATE, HOOKS, PROJECTS, SESSIONS):
    d.mkdir(parents=True)
os.environ.update({"GSD_LONG_RUN_STATE_DIR": str(STATE), "GSD_LONG_RUN_HOOKS_DIR": str(HOOKS),
                   "GSD_LONG_RUN_PROJECTS_DIR": str(PROJECTS), "GSD_LONG_RUN_NO_SPAWN": "1",
                   # the liveness instrument reads the session registry; never the Owner's
                   "GSD_LONG_RUN_SESSIONS_DIR": str(SESSIONS)})

passes = fails = inconclusive = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


def skip(gate, why):
    """This run could not judge its subject, which is not a verdict about it.

    A gate whose precondition was unavailable and a gate whose subject was wrong
    are different evidence, and only one of them is about the code. Counted
    separately so a host that starves mid-run cannot manufacture a red, and so
    a suite that judged nothing cannot read like a clean one.
    """
    global inconclusive
    inconclusive += 1
    print(f"SKIP {gate}: INCONCLUSIVE -- {why}")


def load(path: Path, name: str):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_ISSUED: list[str] = []


def sid() -> str:
    s = f"gsdlr-{uuid.uuid4().hex[:12]}"
    _ISSUED.append(s)
    return s


def project(terms_text: str = "") -> Path:
    p = Path(tempfile.mkdtemp(prefix="gsdlr-proj-", dir=TMP))
    (p / ".planning").mkdir()
    (p / ".planning" / "STATE.md").write_text(f"milestone: v1\n\n{terms_text}\n", encoding="utf-8")
    (p / ".planning" / "ROADMAP.md").write_text(f"# Roadmap\n{terms_text}\n", encoding="utf-8")
    return p


def transcript(session: str, cwd: str, rows=(), idle_s: float = 0.0) -> Path:
    d = PROJECTS / "proj"
    d.mkdir(exist_ok=True)
    t = d / f"{session}.jsonl"
    lines = [{"type": "system", "cwd": cwd}] + list(rows)
    t.write_text("\n".join(json.dumps(r) for r in lines) + "\n", encoding="utf-8")
    if idle_s:
        ts = time.time() - idle_s
        os.utime(t, (ts, ts))
    return t


def asst(text: str) -> dict:
    return {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}}


def user_cmd(cmd: str, when: float) -> dict:
    iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(when)) + "Z"
    return {"type": "user", "timestamp": iso,
            "message": {"role": "user", "content": f"<command-name>{cmd}</command-name>"}}


def boundary_row(when: float) -> dict:
    """A compact_boundary row. Since C1 (spec exact-target-continuation.md) Stop A
    fires only when one postdates the marker -- a low reading alone is not one."""
    iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(when)) + ".000Z"
    return {"type": "system", "subtype": "compact_boundary", "uuid": uuid.uuid4().hex,
            "timestamp": iso, "compactMetadata": {"trigger": "auto"}}


def compacted(session: str) -> str:
    return str(transcript(session, str(ROOT), rows=[boundary_row(time.time() + 2)]))


def events(session: str) -> list[str]:
    return [e["event"] for e in lr.ledger_events(session)]


def gsd(outcome: str, **kw) -> str:
    base = {"outcome": outcome, "reason": outcome.lower(), "phase_count": 3, "completed": 1,
            "incomplete": 2, "all_complete": outcome == "ALL_COMPLETE"}
    base.update(kw)
    return json.dumps(base)


lr = load(TOOLS / "gsd_long_run.py", "gsd_long_run")
mk = load(TOOLS / "gsd_autorun_marker.py", "gsd_autorun_marker")
cfg = load(TOOLS / "gsd_long_run_config.py", "gsd_long_run_config")


# ------------------------------------------------------------------ gap 6 + 8
def gates_preflight():
    s = sid()
    transcript(s, r"C:\p\SessionHome")
    ok, why = lr.arm_preflight(s, r"C:\p\Other", "/absw2-continue")
    check("V-GSDLR-PRE-CWD-MISMATCH", not ok and "this session runs in" in why, why)

    os.environ["_TEST_GSD_STATUS"] = gsd("OK")
    ok, why = lr.arm_preflight(s, r"C:\p\SessionHome", "/gsd-autonomous")
    check("V-GSDLR-PRE-CWD-MATCH", ok, why)

    ok, why = lr.arm_preflight(sid(), r"C:\p\SessionHome", "/gsd-autonomous")
    check("V-GSDLR-PRE-NO-TRANSCRIPT", not ok and "transcript" in why, why)

    os.environ["_TEST_GSD_STATUS"] = gsd("NO_PHASES", reason="GSD parses 0 phases from ROADMAP.md")
    ok, why = lr.arm_preflight(s, r"C:\p\SessionHome", "/gsd-autonomous")
    check("V-GSDLR-PRE-NO-PHASES", not ok and "0 phases" in why, why)
    ok2, why2 = lr.arm_preflight(s, r"C:\p\SessionHome", "/absw2-continue")
    check("V-GSDLR-PRE-CUSTOM-CMD-SKIPS-PHASES", ok2, why2)

    os.environ["_TEST_GSD_STATUS"] = gsd("UNAVAILABLE", reason="node not found")
    ok, why = lr.arm_preflight(s, r"C:\p\SessionHome", "/gsd-autonomous")
    check("V-GSDLR-PRE-GSD-UNAVAILABLE-DISTINCT", not ok and "could not ask GSD" in why, why)
    os.environ.pop("_TEST_GSD_STATUS", None)

    if not ABSW2.is_dir():
        skip("V-GSDLR-REAL-GSD-ABSW2", f"{ABSW2} absent on this host")
    else:
        st = lr.gsd_status(ABSW2)
        if st["outcome"] == "UNAVAILABLE":
            # `gsd_status` itself says UNAVAILABLE means "we could not ask", and
            # this gate used to call that a FAIL -- reporting a verdict about the
            # subject on a run that never reached it. Measured 2026-09-20: the
            # node call timed out at 45 s with the host at 711 MB free of 32 GB,
            # passed after reaping, and failed again under load. A gate that goes
            # red on memory pressure trains everyone to ignore red.
            skip("V-GSDLR-REAL-GSD-ABSW2", f"could not ask gsd-tools: {st.get('reason')}")
        else:
            check("V-GSDLR-REAL-GSD-ABSW2",
                  st["outcome"] == "NO_PHASES" and st.get("phase_count") == 0,
                  f"real gsd-tools on ABSW2 -> {st}")


# ------------------------------------------------------------------ gap 11 + 7
def gates_budget_and_mission():
    now = time.time()
    iso = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(now))
    ok, why = lr.budget_verdict({"cycles": 3, "max_cycles": 3, "armed_at": iso}, now)
    check("V-GSDLR-BUDGET-CYCLES-HALT", not ok and "cycle budget" in why, why)
    old = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(now - 5 * 3600))
    ok, why = lr.budget_verdict({"cycles": 0, "max_hours": 4, "armed_at": old}, now)
    check("V-GSDLR-BUDGET-HOURS-HALT", not ok and "time budget" in why, why)
    ok, why = lr.budget_verdict({"cycles": 1, "armed_at": iso}, now)
    check("V-GSDLR-BUDGET-DEFAULTS-ALLOW", ok and f"/{lr.DEFAULT_MAX_CYCLES}" in why, why)

    good = project("angry birds rovio powerpc slingshot")
    terms = ["angry", "birds", "rovio", "powerpc", "slingshot"]
    g = lr.resume_gate({"cycles": 0, "armed_at": iso, "cwd": str(good), "mission": {"terms": terms}}, now)
    check("V-GSDLR-MISSION-FRESH-CONTINUES", not g["halt"], g["reason"])
    stale = project("page two native gameselect")
    g = lr.resume_gate({"cycles": 0, "armed_at": iso, "cwd": str(stale), "mission": {"terms": terms}}, now)
    check("V-GSDLR-MISSION-STALE-HALTS", g["halt"] and g["kind"] == "mission" and "STALE" in g["reason"], g["reason"])
    gone = TMP / "no-such-project"
    g = lr.resume_gate({"cycles": 0, "armed_at": iso, "cwd": str(gone), "mission": {"terms": terms}}, now)
    check("V-GSDLR-MISSION-UNREADABLE-HALTS", g["halt"] and "UNREADABLE" in g["reason"], g["reason"])


# ------------------------------------------------------------------ watchdog
def _stamp(wd, s):
    (Path(tempfile.gettempdir()) / wd.ORCH_THROTTLE_FLAG.format(session_id=s)).write_text(
        str(time.time()), encoding="utf-8")


def _run(wd, s, pct, tp=""):
    os.environ["_TEST_CONTEXT_PCT"] = str(pct)
    try:
        return wd.run({"session_id": s, "cwd": str(ROOT), "transcript_path": tp}) or {}
    finally:
        os.environ.pop("_TEST_CONTEXT_PCT", None)


def _clear_wd(wd, s):
    for f in (wd.RESUME_ARMED_FLAG, wd.RESUME_DONE_FLAG, wd.RESUME_CONFIRMED_FLAG, wd.ADVISORY_FLAG,
              wd.SNAPSHOT_FLAG):
        wd._clear_flag(s, f)
    mk.clear_marker(s)


def gates_watchdog():
    wd = load(WATCHDOG, "ctxwd_under_test")
    calls = []
    # C4 (spec exact-target-continuation.md): Stop B dispatches through the one
    # door, `_dispatch_continuation`; the foreground flag is no longer the
    # default path, so the recorder sits on the door. Routing itself is proven
    # in test_continuation_transport / test_continuation_wiring.
    saved = wd._dispatch_continuation
    wd._dispatch_continuation = lambda s_, kind, **k: calls.append(dict(k, kind=kind)) or \
        {"route": "orca-exact", "pane_key": "stub"}
    try:
        # budget halt
        s = sid(); _stamp(wd, s)
        mk.write_marker(s, "/gsd-autonomous", cwd=str(ROOT), max_cycles=1)
        mk.bump_cycles(s)
        out = _run(wd, s, 25.0, compacted(s))
        check("V-GSDLR-WD-BUDGET-HALTS",
              out.get("decision") == "block" and "HALTED" in out.get("reason", "")
              and mk.read_marker(s) is None and "halted" in events(s) and not calls,
              f"reason={out.get('reason', '')[:90]!r} events={events(s)} dispatches={len(calls)}")
        out2 = _run(wd, s, 25.0)
        check("V-GSDLR-WD-HALT-IS-FINAL", not out2 and not calls, f"second stop -> {out2!r}")
        _clear_wd(wd, s)

        # RAM low vs ok, and cycle counting
        s = sid(); _stamp(wd, s)
        mk.write_marker(s, "/gsd-autonomous", cwd=str(ROOT))
        os.environ["_TEST_FREE_MB"] = "500"
        out = _run(wd, s, 25.0, compacted(s))
        os.environ.pop("_TEST_FREE_MB", None)
        check("V-GSDLR-WD-RAM-LOW-WAITS", "wait-ram" in out.get("reason", "") and "/gsd-autonomous" in out.get("reason", ""),
              out.get("reason", "")[-160:])
        check("V-GSDLR-WD-CYCLE-COUNTED", (mk.read_marker(s) or {}).get("cycles") == 1
              and "resume_requested" in events(s), f"marker={mk.read_marker(s)} events={events(s)}")

        # Stop B carries the expected line + transcript to the daemon
        tp = transcript(s, str(ROOT))
        _run(wd, s, 25.0, str(tp))
        k = calls[-1] if calls else {}
        check("V-GSDLR-WD-FLAG-EXPECTS-LINE",
              k.get("expect_line") == "/gsd-autonomous" and k.get("transcript") == str(tp)
              and "resume_dispatched" in events(s), f"kwargs={k} events={events(s)}")

        # confirmation: absent until the transcript shows the command submitted
        _run(wd, s, 30.0, str(tp))
        check("V-GSDLR-WD-NO-CONFIRM-WITHOUT-EVIDENCE", "resume_confirmed" not in events(s), f"events={events(s)}")
        transcript(s, str(ROOT), rows=[asst("/gsd-autonomous"), user_cmd("/gsd-autonomous", time.time())])
        _run(wd, s, 30.0, str(tp))
        check("V-GSDLR-WD-CONFIRMS-FROM-TRANSCRIPT",
              events(s).count("resume_confirmed") == 1 and wd._flag_exists(s, wd.RESUME_CONFIRMED_FLAG),
              f"events={events(s)}")
        _run(wd, s, 30.0, str(tp))
        check("V-GSDLR-WD-CONFIRMS-ONCE", events(s).count("resume_confirmed") == 1, f"events={events(s)}")
        _clear_wd(wd, s)

        # RAM fine -> no wait instruction
        s = sid(); _stamp(wd, s)
        mk.write_marker(s, "/gsd-autonomous", cwd=str(ROOT))
        os.environ["_TEST_FREE_MB"] = "9000"
        out = _run(wd, s, 25.0, compacted(s))
        os.environ.pop("_TEST_FREE_MB", None)
        check("V-GSDLR-WD-RAM-OK-NO-WAIT", "wait-ram" not in out.get("reason", "") and out.get("decision") == "block",
              out.get("reason", "")[:80])
        _clear_wd(wd, s)
    finally:
        wd._dispatch_continuation = saved

    # tier-2 crossing: ledger row + /compact prefix expectation
    wd2 = load(WATCHDOG, "ctxwd_under_test_t2")
    rec = []

    class _Null:
        def atomic_append_jsonl(self, *a, **k):
            return None

        def atomic_write_bytes(self, *a, **k):
            return None

    wd2._import_atomic_write = lambda *a, **k: _Null()
    wd2._kclear_equivalent = lambda *a, **k: {}
    wd2._dump_telemetry = lambda *a, **k: None
    wd2._append_progress_md = lambda *a, **k: None
    legacy = []
    wd2._write_trigger_flag = lambda *a, **k: legacy.append(k) or "flag"
    wd2._spawn_daemon = lambda *a, **k: legacy.append("spawn") or True
    wd2._dispatch_continuation = lambda s_, kind, **k: rec.append(dict(k, kind=kind)) or \
        {"route": "manual", "why": "stub: no exact route"}
    s = sid(); _stamp(wd2, s)
    try:
        mk.write_marker(s, "/gsd-autonomous", cwd=str(ROOT))
        out = _run(wd2, s, 75.0, str(TMP / "t.jsonl"))
        check("V-GSDLR-WD-CROSSING-LEDGERED", "crossing" in events(s) and out.get("decision") == "block",
              f"events={events(s)}")
        check("V-GSDLR-WD-COMPACT-EXPECTS-PREFIX",
              rec and rec[-1].get("kind") == "compact" and rec[-1].get("expect_prefix") == "/compact",
              f"kwargs={rec[-1] if rec else None}")
        # C4: the text states the route that will actually be used, and no
        # longer promises an Enter delivered by whichever window has focus.
        reason = out.get("reason", "")
        check("V-GSDLR-WD-TEXT-NAMES-ROUTE",
              "Delivery: MANUAL" in reason and "focused window" not in reason and not legacy,
              f"route sentence present={('Delivery:' in reason)} legacy_calls={legacy}")
    finally:
        _clear_wd(wd2, s)


def gates_test_thresholds():
    """CTXWD_TEST_THRESHOLDS lowers the wall for ONE session; a typo must never disable it."""
    wd = load(WATCHDOG, "ctxwd_thresholds")

    class _Null:
        def atomic_append_jsonl(self, *a, **k):
            return None

        def atomic_write_bytes(self, *a, **k):
            return None

    for n, v in (("_import_atomic_write", lambda *a, **k: _Null()), ("_kclear_equivalent", lambda *a, **k: {}),
                 ("_dump_telemetry", lambda *a, **k: None), ("_append_progress_md", lambda *a, **k: None),
                 ("_write_trigger_flag", lambda *a, **k: "flag"), ("_spawn_daemon", lambda *a, **k: True)):
        setattr(wd, n, v)
    try:
        s = sid(); _stamp(wd, s)
        out = _run(wd, s, 40.0)
        check("V-GSDLR-THR-DEFAULT-NO-FIRE-AT-40", out.get("decision") != "block", f"{out.get('decision')!r}")
        _clear_wd(wd, s)

        os.environ["CTXWD_TEST_THRESHOLDS"] = "31,36,30"
        s = sid(); _stamp(wd, s)
        out = _run(wd, s, 40.0)
        check("V-GSDLR-THR-KNOB-FIRES-AT-40", out.get("decision") == "block" and ">= 36%" in out.get("reason", ""),
              out.get("reason", "")[:70])
        check("V-GSDLR-THR-KNOB-VALUES", wd._thresholds() == (31.0, 36.0, 30.0), f"{wd._thresholds()}")
        _clear_wd(wd, s)

        for bad in ("70,36,30", "31,36", "a,b,c", "31,36,31"):
            os.environ["CTXWD_TEST_THRESHOLDS"] = bad
            if wd._thresholds() != (wd.THRESHOLD_SNAPSHOT_PCT, wd.THRESHOLD_ADVISORY_PCT, wd.THRESHOLD_REARM_PCT):
                check("V-GSDLR-THR-INVALID-FALLS-BACK", False, f"{bad!r} -> {wd._thresholds()}")
                break
        else:
            check("V-GSDLR-THR-INVALID-FALLS-BACK", True, "4 malformed values -> constants")
    finally:
        os.environ.pop("CTXWD_TEST_THRESHOLDS", None)


# ------------------------------------------------------------------ gap 2 + 9
def _marker_file(s: str, **kw) -> Path:
    body = {"session_id": s, "resume_command": "/gsd-autonomous", "cwd": "", "cycles": 0}
    body.update(kw)
    p = STATE / f"gsd-autorun-{s}.json"
    p.write_text(json.dumps(body), encoding="utf-8")
    return p


def gates_sweep():
    for p in STATE.glob("gsd-autorun-*.json"):
        p.unlink()
    s_dead = sid(); m_dead = _marker_file(s_dead)
    s_fin = sid(); proj = project("x")
    cfg.apply_long_run(proj)
    m_fin = _marker_file(s_fin, cwd=str(proj))
    transcript(s_fin, str(proj))
    s_rec = sid(); m_rec = _marker_file(s_rec, resume_command="/absw2-continue")
    transcript(s_rec, "x", rows=[asst("compacted.\n/absw2-continue")], idle_s=1800)
    s_st = sid(); m_st = _marker_file(s_st, resume_command="/absw2-continue")
    transcript(s_st, "x", rows=[asst("Let me check the next phase.")], idle_s=1800)
    s_fresh = sid(); _marker_file(s_fresh, resume_command="/absw2-continue")
    transcript(s_fresh, "x", rows=[asst("working")])

    # A legacy flag left by an opted-in session: the sweep still owes it a daemon.
    legacy_flag = HOOKS / f"auto-compact-pending-{sid()}.flag"
    legacy_flag.write_text(json.dumps({"session_id": "legacy", "cwd": "x"}) + "\n", encoding="utf-8")

    os.environ["_TEST_GSD_STATUS"] = gsd("ALL_COMPLETE")
    acts = lr.sweep()
    os.environ.pop("_TEST_GSD_STATUS", None)
    by = {(a.get("session_id"), a["action"]) for a in acts}

    check("V-GSDLR-SWEEP-REAPS-DEAD", (s_dead, "reaped") in by and not m_dead.exists(), f"{acts}")
    check("V-GSDLR-SWEEP-FINISHES", (s_fin, "finished") in by and not m_fin.exists()
          and "finished" in events(s_fin), f"{acts}")
    shown = cfg.show(proj)
    check("V-GSDLR-SWEEP-RESTORES-CONFIG", shown["context_warning_threshold"] is None and not shown["long_run_active"],
          f"{shown}")
    # Re-specified 2026-09-18 (spec exact-target-continuation.md, C4). The flag is
    # still written, but its consumer changed: the daemon routes it by SESSION id
    # to the terminal inbox and, by default, refuses rather than typing into the
    # focused window -- the path that sent `/absw2-continue` into another session.
    flag = HOOKS / f"auto-compact-trigger-{s_rec}.flag"
    body = json.loads(flag.read_text(encoding="utf-8")) if flag.exists() else {}
    rec = [e for e in lr.ledger_events(s_rec) if e.get("event") == "recovered"]
    check("V-GSDLR-SWEEP-RECOVERS-VIA-INBOX",
          (s_rec, "recovered") in by and rec and rec[-1].get("route") == "terminal-inbox"
          and body.get("session_id") == s_rec and body.get("expect_line") == "/absw2-continue",
          f"flag={body} recovered={rec}")
    # A delivery the sweep requests must be VISIBLE to `report`, exactly as the
    # watchdog's own branch is (context-watchdog.py:675). Until 2026-09-21 this
    # path wrote the flag and no row, so a delivery that SUCCEEDED could not be
    # counted by the milestone gate it was serving -- and the deadlock-breaking
    # hand call that found this left no trace either.
    inbox_rows = [e for e in lr.ledger_events(s_rec) if e.get("event") == "delivery_inbox_requested"]
    check("V-GSDLR-INBOX-DELIVERY-IS-LEDGERED", len(inbox_rows) == 1, f"{inbox_rows}")
    # Derived from the flag just written, not recomputed: the row and the flag
    # cannot disagree about what is being delivered. /absw2-continue is a resume.
    check("V-GSDLR-INBOX-ROW-KIND-DERIVED",
          bool(inbox_rows) and inbox_rows[-1].get("kind") == "resume"
          and inbox_rows[-1].get("expect_line") == body.get("expect_line"),
          f"row={inbox_rows[-1] if inbox_rows else None} flag={body}")
    # Two producers now write this event name. A row that cannot say which one
    # emitted it cannot distinguish a swept re-delivery from a watchdog crossing.
    # The expected cid is DERIVED from the sibling row the same action wrote, not
    # re-stat'd from a file. First version of this assertion used the MARKER's
    # mtime where the cid is built from the TRANSCRIPT's, and failed against a
    # correct row -- the recompute-from-a-second-source defect this whole change
    # is about, reproduced inside its own gate.
    check("V-GSDLR-INBOX-ROW-NAMES-PRODUCER",
          bool(inbox_rows) and bool(rec)
          and inbox_rows[-1].get("producer") == "gsd_long_run.write_trigger"
          and inbox_rows[-1].get("cid") == f"{s_rec}:recover:{rec[-1].get('transcript_mtime')}",
          f"row={inbox_rows[-1] if inbox_rows else None} recovered={rec[-1] if rec else None}")
    check("V-GSDLR-SWEEP-RECORDS-STALL", (s_st, "stalled") in by and "stalled" in events(s_st), f"{acts}")
    check("V-GSDLR-SWEEP-FRESH-UNTOUCHED", not any(a.get("session_id") == s_fresh for a in acts), f"{acts}")
    check("V-GSDLR-SWEEP-DAEMON-FOR-FLAGS", any(a["action"] == "daemon" for a in acts), f"{acts}")

    legacy_flag.unlink(missing_ok=True)
    flag.unlink(missing_ok=True)   # so NO-DUPLICATES is held by the ledger dedupe, not the flag
    acts2 = lr.sweep()
    again = {(a.get("session_id"), a["action"]) for a in acts2}
    check("V-GSDLR-SWEEP-NO-DUPLICATES", (s_rec, "recovered") not in again and (s_st, "stalled") not in again,
          f"{acts2}")
    m_rec.unlink(); m_st.unlink()


# ------------------------------------------------------------------ gap 5
def gates_report():
    s = sid()
    for ev in ("armed", "crossing", "resume_requested", "resume_confirmed", "crossing", "resume_confirmed"):
        lr.ledger_append(s, ev)
    check("V-GSDLR-REPORT-PROVEN", lr.report(s)["verdict"] == "PROVEN", f"{lr.report(s)['verdict']}")
    s2 = sid()
    for ev in ("crossing", "resume_confirmed", "crossing"):
        lr.ledger_append(s2, ev)
    check("V-GSDLR-REPORT-PARTIAL", lr.report(s2)["verdict"] == "PARTIAL", lr.report(s2)["verdict"])
    s3 = sid()
    lr.ledger_append(s3, "crossing")
    lr.ledger_append(s3, "crossing")
    lr.ledger_append(s3, "resume_confirmed")
    check("V-GSDLR-REPORT-ONE-CONFIRM-ONE-CYCLE", lr.report(s3)["verdict"] == "PARTIAL",
          f"2 crossings, 1 confirm -> {lr.report(s3)['verdict']}")
    check("V-GSDLR-REPORT-EMPTY", lr.report(sid())["verdict"] == "NO_CROSSINGS", "no rows")


# ------------------------------------------------------------------ gap 13
def gates_config():
    p = project("x")
    cfg.apply_long_run(p)
    raw = json.loads((p / ".planning" / "config.json").read_text(encoding="utf-8"))
    check("V-GSDLR-CFG-NOT-IN-CONFIG", cfg.BACKUP_KEY not in raw and cfg.backup_path(p).is_file(), f"{raw}")
    cfg.restore(p)
    check("V-GSDLR-CFG-BACKUP-CONSUMED", not cfg.backup_path(p).exists(), "backup removed after restore")
    q = project("x")
    (q / ".planning" / "config.json").write_text(json.dumps(
        {"hooks": {"context_warning_threshold": 12, "context_critical_threshold": 8},
         cfg.BACKUP_KEY: {"context_warning_threshold": 40, "context_critical_threshold": None}}), encoding="utf-8")
    cfg.restore(q)
    after = json.loads((q / ".planning" / "config.json").read_text(encoding="utf-8"))
    check("V-GSDLR-CFG-MIGRATES-EMBEDDED", after["hooks"].get("context_warning_threshold") == 40
          and "context_critical_threshold" not in after["hooks"] and cfg.BACKUP_KEY not in after, f"{after}")


# ------------------------------------------------------------------ marker CLI boundary
def gates_cli():
    good = project("angry birds rovio powerpc slingshot")
    s = sid()
    transcript(s, r"C:\p\SomewhereElse")
    args = [PY, str(TOOLS / "gsd_autorun_marker.py"), "--write", "--session", s, "--command", "/absw2-continue",
            "--cwd", str(good), "--mission", "angry,birds,rovio,powerpc,slingshot",
            "--legacy-compact"]  # v2 arming is opt-in since 2026-09-24
    r = subprocess.run(args, capture_output=True, text=True, env=dict(os.environ))
    check("V-GSDLR-CLI-REFUSES-WRONG-SESSION-DIR", r.returncode == 2 and "this session runs in" in r.stderr,
          f"rc={r.returncode} err={r.stderr.strip()[:140]}")
    s2 = sid()
    transcript(s2, str(good))
    r = subprocess.run(args[:4] + [s2] + args[5:] + ["--max-cycles", "5"], capture_output=True, text=True,
                       env=dict(os.environ))
    m = mk.read_marker(s2) or {}
    check("V-GSDLR-CLI-ARMS-WITH-BUDGET", r.returncode == 0 and m.get("max_cycles") == 5 and "armed" in events(s2),
          f"rc={r.returncode} err={r.stderr.strip()[:120]} marker={m}")
    mk.clear_marker(s2)

    # One arming must not produce two disagreeing records. write_marker stores
    # resolve_cwd(cwd); the ledger row used to store the RAW argument, so a marker
    # naming an absolute directory sat beside a row naming ".". No later reader can
    # resolve that row -- it resolves against whoever is reading, which is exactly
    # the failure marker_project REFUSES rather than guesses (gsd_long_run.py:739).
    # Armed here the way the estate actually arms: --cwd "." with the process running
    # IN the project (measured 2026-09-19, 8 of 9 markers held ".").
    good2 = project("angry birds rovio powerpc slingshot")
    s3 = sid()
    transcript(s3, str(good2))
    base = [PY, str(TOOLS / "gsd_autorun_marker.py"), "--write", "--session", s3,
            "--command", "/absw2-continue", "--mission", "angry,birds,rovio,powerpc,slingshot",
            "--legacy-compact"]
    r3 = subprocess.run(base + ["--cwd", "."], capture_output=True, text=True,
                        cwd=str(good2), env=dict(os.environ))
    rows3 = [e for e in lr.ledger_events(s3) if e.get("event") == "armed"]
    row_cwd = rows3[-1].get("cwd") if rows3 else None
    marker3 = mk.read_marker(s3) or {}
    check("V-GSDLR-LEDGER-CWD-ABSOLUTE",
          bool(rows3) and isinstance(row_cwd, str) and row_cwd != ""
          and Path(row_cwd).is_absolute(),
          f"rc={r3.returncode} row_cwd={row_cwd!r} err={r3.stderr.strip()[:120]}")
    check("V-GSDLR-LEDGER-CWD-MATCHES-MARKER",
          bool(rows3) and row_cwd == marker3.get("cwd"),
          f"row={row_cwd!r} marker={marker3.get('cwd')!r}")
    mk.clear_marker(s3)

    # Empty stays empty in BOTH records. This is the gate that discriminates: a naive
    # repair spelled resolve_cwd(args.cwd or ".") passes the two above and silently
    # turns "unknown" into the arming process's own directory -- the same guess one
    # layer earlier, which is what resolve_cwd's docstring refuses.
    good3 = project("angry birds rovio powerpc slingshot")
    s4 = sid()
    transcript(s4, str(good3))
    r4 = subprocess.run([PY, str(TOOLS / "gsd_autorun_marker.py"), "--write", "--session", s4,
                         "--command", "/absw2-continue",
                         "--mission", "angry,birds,rovio,powerpc,slingshot", "--legacy-compact"],
                        capture_output=True, text=True, cwd=str(good3), env=dict(os.environ))
    rows4 = [e for e in lr.ledger_events(s4) if e.get("event") == "armed"]
    row4_cwd = rows4[-1].get("cwd") if rows4 else None
    marker4 = mk.read_marker(s4) or {}
    check("V-GSDLR-LEDGER-CWD-EMPTY-STAYS-EMPTY",
          bool(rows4) and row4_cwd == "" and marker4.get("cwd") == "",
          f"rc={r4.returncode} row={row4_cwd!r} marker={marker4.get('cwd')!r} "
          f"err={r4.stderr.strip()[:120]}")
    mk.clear_marker(s4)


def gates_session_thresholds():
    """A RUNNING session can narrow its own wall; a malformed ask never widens it.

    The env knob is read from the launching process, so /cpp-gsd-long -- which is
    invoked from inside an already-running session -- could never reach it. These
    gates drive the file source end to end: the writer's refusals, the reader's
    precedence over a valid env, and the fall-through when the file is junk.
    """
    lr = load(TOOLS / "gsd_long_run.py", "lr_thresholds")
    wd = load(WATCHDOG, "ctxwd_session_thresholds")
    prod = (wd.THRESHOLD_SNAPSHOT_PCT, wd.THRESHOLD_ADVISORY_PCT, wd.THRESHOLD_REARM_PCT)
    try:
        s = sid()
        # Negative control FIRST: with no file and no env this session is ordinary.
        check("V-GSDLR-SESSTHR-ABSENT-IS-PRODUCTION", wd._thresholds(s) == prod, f"{wd._thresholds(s)}")

        lr.write_thresholds(s, "35,40,30", reason="gate")
        check("V-GSDLR-SESSTHR-FILE-APPLIES", wd._thresholds(s) == (35.0, 40.0, 30.0), f"{wd._thresholds(s)}")
        check("V-GSDLR-SESSTHR-LEDGERED",
              any(r.get("event") == "thresholds_set" for r in lr.ledger_events(s)),
              f"{[r.get('event') for r in lr.ledger_events(s)]}")

        # Another session is untouched by this one's file -- the knob is per session.
        other = sid()
        check("V-GSDLR-SESSTHR-SCOPED-TO-SESSION", wd._thresholds(other) == prod, f"{wd._thresholds(other)}")

        # The file is the only source that can change mid-run, so it outranks the env.
        os.environ["CTXWD_TEST_THRESHOLDS"] = "31,36,30"
        try:
            check("V-GSDLR-SESSTHR-FILE-BEATS-ENV", wd._thresholds(s) == (35.0, 40.0, 30.0), f"{wd._thresholds(s)}")
            check("V-GSDLR-SESSTHR-ENV-STILL-WORKS", wd._thresholds(other) == (31.0, 36.0, 30.0),
                  f"{wd._thresholds(other)}")
            # A junk file is not an answer: fall through to the env, never to "off".
            lr.thresholds_path(s).write_text("{ not json", encoding="utf-8")
            check("V-GSDLR-SESSTHR-JUNK-FALLS-THROUGH", wd._thresholds(s) == (31.0, 36.0, 30.0),
                  f"{wd._thresholds(s)}")
        finally:
            os.environ.pop("CTXWD_TEST_THRESHOLDS", None)
        check("V-GSDLR-SESSTHR-JUNK-THEN-PRODUCTION", wd._thresholds(s) == prod, f"{wd._thresholds(s)}")

        # A file that parses but breaks the rule must be refused on WRITE, and a
        # hand-written one must be refused on READ -- both poles, same rule.
        refused = 0
        for bad in ("70,36,30", "31,36", "a,b,c", "31,36,31", "31,36,4", "31,36,96"):
            try:
                lr.write_thresholds(s, bad)
            except ValueError:
                refused += 1
        check("V-GSDLR-SESSTHR-WRITER-REFUSES-BAD", refused == 6, f"{refused}/6 refused")
        lr.thresholds_path(s).write_text(json.dumps({"snapshot": 70, "advisory": 36, "rearm": 30}),
                                         encoding="utf-8")
        check("V-GSDLR-SESSTHR-READER-REFUSES-BAD", wd._thresholds(s) == prod, f"{wd._thresholds(s)}")

        check("V-GSDLR-SESSTHR-CLEAR", lr.clear_thresholds(s) and wd._thresholds(s) == prod,
              f"{wd._thresholds(s)}")
        check("V-GSDLR-SESSTHR-CLEAR-ABSENT-IS-FALSE", lr.clear_thresholds(s) is False, "second clear")

        # End to end through the watchdog's own decision, not just the accessor.
        class _Null:
            def atomic_append_jsonl(self, *a, **k):
                return None

            def atomic_write_bytes(self, *a, **k):
                return None

        for n, v in (("_import_atomic_write", lambda *a, **k: _Null()), ("_kclear_equivalent", lambda *a, **k: {}),
                     ("_dump_telemetry", lambda *a, **k: None), ("_append_progress_md", lambda *a, **k: None),
                     ("_write_trigger_flag", lambda *a, **k: "flag"), ("_spawn_daemon", lambda *a, **k: True)):
            setattr(wd, n, v)
        s2 = sid(); _stamp(wd, s2)
        out = _run(wd, s2, 42.0)
        check("V-GSDLR-SESSTHR-E2E-QUIET-WITHOUT-FILE", out.get("decision") != "block", f"{out.get('decision')!r}")
        _clear_wd(wd, s2)
        lr.write_thresholds(s2, "35,40,30", reason="gate-e2e")
        _stamp(wd, s2)
        out = _run(wd, s2, 42.0)
        check("V-GSDLR-SESSTHR-E2E-FIRES-WITH-FILE",
              out.get("decision") == "block" and ">= 40%" in out.get("reason", ""),
              f"{out.get('decision')!r} {out.get('reason', '')[:60]}")
        _clear_wd(wd, s2)
        lr.clear_thresholds(s2)
    finally:
        for s in _ISSUED:
            try:
                lr.clear_thresholds(s)
            except Exception:
                pass


def gates_compact_tail():
    """The two opposite states a `/compact` tail is the SAME in (spec C1).

    Measured 2026-09-19 on session 37cfb187: the sweep re-delivered one
    `/compact` line three times, because `last_assistant_text` returns that line
    both when it was never submitted AND after the compaction landed -- the
    agent has not spoken since, so the tail does not move. Two states, one
    observable, opposite correct actions. The run idled nine hours and the
    resume it was owed was never sent.

    `mk.STATE_DIR` is redirected here (it is a module constant, see the module
    docstring) so the cycle bump is both observable and kept off live state.
    """
    real_state = mk.STATE_DIR
    mk.STATE_DIR = STATE
    try:
        for p in STATE.glob("gsd-autorun-*.json"):
            p.unlink()
        armed = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() - 3600)) + "Z"
        line = "/compact focus on narrow-wall crossing delivery fix"
        cmd = "/gsd-autonomous"

        # --- the decision, driven directly ----------------------------------
        s_no = sid()
        t_no = transcript(s_no, "x", rows=[asst(line)], idle_s=1800)
        owed = lr.owed_line(s_no, {"armed_at": armed}, t_no, line, cmd)
        check("V-GSDLR-OWED-NO-BOUNDARY-KEEPS-COMPACT",
              owed["line"] == line and owed["compaction"] == "unobserved" and not owed["halt"],
              f"{owed}")

        s_yes = sid()
        bnd = boundary_row(time.time())
        t_yes = transcript(s_yes, "x", rows=[asst(line), bnd], idle_s=1800)
        owed = lr.owed_line(s_yes, {"armed_at": armed}, t_yes, line, cmd)
        check("V-GSDLR-OWED-AFTER-COMPACT-IS-RESUME",
              owed["line"] == cmd and owed["compaction"] == "observed"
              and not owed["halt"] and owed.get("boundary_ts"), f"{owed}")

        owed = lr.owed_line(s_yes, {"armed_at": armed, "cycles": 12, "max_cycles": 12},
                            t_yes, line, cmd)
        check("V-GSDLR-OWED-HALTS-ON-SPENT-BUDGET",
              owed["halt"] and owed["line"] is None and owed.get("kind") == "budget", f"{owed}")

        owed = lr.owed_line(s_yes, {"armed_at": armed}, t_yes, line, "")
        check("V-GSDLR-OWED-NO-COMMAND-KEEPS-TAIL",
              owed["line"] == line and not owed["halt"], f"{owed}")

        # --- end to end, through the sweep the daemon actually reads ---------
        s_e2e = sid()
        _marker_file(s_e2e, armed_at=armed)
        b2 = boundary_row(time.time())
        transcript(s_e2e, "x", rows=[asst(line), b2], idle_s=1800)
        by = {(a.get("session_id"), a["action"]) for a in lr.sweep()}
        flag = HOOKS / f"auto-compact-trigger-{s_e2e}.flag"
        body = json.loads(flag.read_text(encoding="utf-8")) if flag.exists() else {}
        rows = lr.ledger_events(s_e2e)
        req = [e for e in rows if e.get("event") == "resume_requested"]
        rec = [e for e in rows if e.get("event") == "recovered"]
        check("V-GSDLR-SWEEP-SENDS-RESUME-AFTER-COMPACT",
              (s_e2e, "recovered") in by and body.get("expect_line") == cmd
              and rec and rec[-1].get("compaction") == "observed", f"flag={body} rec={rec}")
        check("V-GSDLR-SWEEP-LEDGERS-RESUME-REQUEST",
              len(req) == 1 and req[0].get("via") == "sweep"
              and req[0].get("boundary_ts") and req[0].get("cycles") == 1, f"{req}")

        # The same boundary must not license a second resume. The transcript moves
        # (new mtime clears the dedupe) but carries the SAME boundary, so the fence
        # -- which reads `resume_requested` rows -- must now read it as spent.
        flag.unlink(missing_ok=True)
        transcript(s_e2e, "x", rows=[asst(line), b2], idle_s=1799)
        lr.sweep()
        body2 = json.loads(flag.read_text(encoding="utf-8")) if flag.exists() else {}
        req2 = [e for e in lr.ledger_events(s_e2e) if e.get("event") == "resume_requested"]
        check("V-GSDLR-SWEEP-ONE-RESUME-PER-BOUNDARY",
              len(req2) == 1 and body2.get("expect_line") == line, f"req={req2} flag={body2}")

        s_halt = sid()
        m_halt = _marker_file(s_halt, armed_at=armed, cycles=12, max_cycles=12)
        transcript(s_halt, "x", rows=[asst(line), boundary_row(time.time())], idle_s=1800)
        by = {(a.get("session_id"), a["action"]) for a in lr.sweep()}
        check("V-GSDLR-SWEEP-HALTS-SPENT-RUN",
              (s_halt, "halted") in by and not m_halt.exists() and "halted" in events(s_halt)
              and not (HOOKS / f"auto-compact-trigger-{s_halt}.flag").exists(), f"{by}")
    finally:
        mk.STATE_DIR = real_state


def gates_confirm_aperture():
    """A resume is confirmed at the END of the turn it started, so the turn's own
    output is already in the transcript ahead of it.

    Measured 2026-09-19, session 37cfb187: the `/gsd-autonomous` row sat 598 KB
    from the end of a 5.8 MB transcript while the reader's window was 256 KB, so
    every Stop chain read False and the run could not confirm its own resume.
    The coupling is perverse -- the more the turn did, the further back the row
    goes -- so the instrument failed precisely in the case it exists for.

    The control here is the OLD window passed explicitly: without it, a gate that
    merely asserts True would pass against a predicate that had stopped looking
    at timestamps at all.
    """
    s = sid()
    cmd = "/gsd-autonomous"
    t_issue = time.time()
    since = t_issue - 5
    # >256 KB of turn output written AFTER the command row, as a real turn does.
    pad = [asst("x" * 4000) for _ in range(80)]
    t = transcript(s, "x", rows=[user_cmd(cmd, t_issue)] + pad)
    size = t.stat().st_size

    check("V-GSDLR-CONFIRM-BEYOND-OLD-WINDOW",
          size > 262144 and lr.user_issued_command_since(t, cmd, since) is True,
          f"transcript={size}B, row is {size - 262144}B beyond the old window")
    check("V-GSDLR-CONFIRM-OLD-WINDOW-WAS-BLIND",
          lr.user_issued_command_since(t, cmd, since, tail_bytes=262144) is False,
          "the 256 KB window cannot see it -- this is what made the gate above fail in production")
    check("V-GSDLR-CONFIRM-STILL-DISCRIMINATES",
          lr.user_issued_command_since(t, "/no-such-command", since) is False,
          "a command nobody issued is still False, so the widening did not become 'always True'")
    check("V-GSDLR-CONFIRM-TIME-BOUND-HOLDS",
          lr.user_issued_command_since(t, cmd, t_issue + 3600) is False,
          "a row older than `since` is still refused, so the window did not replace the clock")


def gates_wall_survives_its_sidecar():
    """The wall must not vanish silently when its sidecar does.

    Measured 2026-09-19: something iterated the armed markers and cleared their
    thresholds files; `_thresholds()` fell back to the production constants and
    a 45 % reading passed a 40 % wall for eleven hours while `status` said armed,
    `report` said PARTIAL and every gate stayed green.
    """
    wd = load(WATCHDOG, "ctxwd_wall_sidecar")
    prod = (wd.THRESHOLD_SNAPSHOT_PCT, wd.THRESHOLD_ADVISORY_PCT, wd.THRESHOLD_REARM_PCT)
    s = sid()
    mk.write_marker(s, "/gsd-autonomous", str(ROOT))
    lr.write_thresholds(s, "35,40,30", reason="gate")

    marker = json.loads(mk.marker_path(s).read_text(encoding="utf-8"))
    check("V-GSDLR-WALL-STAMPED-ON-MARKER",
          (marker.get("wall") or {}).get("advisory") == 40.0
          and (marker.get("wall") or {}).get("rearm") == 30.0,
          f"marker wall={marker.get('wall')}")

    # The sidecar disappears the way it did in production: the file, nothing else.
    lr.thresholds_path(s).unlink()
    for p in STATE.glob(f"ctxwd-wall_restored_from_marker-{s}-*.flag"):
        p.unlink()
    restored = wd._thresholds(s)
    check("V-GSDLR-WALL-SURVIVES-SIDECAR-LOSS", restored == (35.0, 40.0, 30.0),
          f"sidecar gone -> {restored} (production would be {prod})")
    rows = [e for e in lr.ledger_events(s) if e.get("event") == "wall_restored_from_marker"]
    check("V-GSDLR-WALL-RESTORATION-IS-AUDIBLE", len(rows) == 1 and rows[-1].get("advisory") == 40.0,
          f"{rows}")
    wd._thresholds(s); wd._thresholds(s)
    rows2 = [e for e in lr.ledger_events(s) if e.get("event") == "wall_restored_from_marker"]
    check("V-GSDLR-WALL-RESTORATION-SAYS-IT-ONCE", len(rows2) == 1,
          f"{len(rows2)} rows after three resolutions")

    # A deliberate clear must mean what it says: BOTH homes, or `--clear` is a
    # no-op wearing the costume of an instruction.
    lr.write_thresholds(s, "35,40,30", reason="gate2")
    cleared = lr.clear_thresholds(s)
    after = json.loads(mk.marker_path(s).read_text(encoding="utf-8"))
    for p in STATE.glob(f"ctxwd-wall_restored_from_marker-{s}-*.flag"):
        p.unlink()
    check("V-GSDLR-WALL-CLEAR-REMOVES-BOTH",
          cleared and "wall" not in after and wd._thresholds(s) == prod,
          f"cleared={cleared} wall_present={'wall' in after} "
          f"sidecar={lr.thresholds_path(s).is_file()} thresholds={wd._thresholds(s)} "
          f"marker={lr._marker_file(s)} same_as_mk={lr._marker_file(s) == mk.marker_path(s)}")
    mk.clear_marker(s)

    # Negative control: no marker, no sidecar -> the constants, and NO ledger row.
    s2 = sid()
    for p in STATE.glob(f"ctxwd-wall_restored_from_marker-{s2}-*.flag"):
        p.unlink()
    check("V-GSDLR-WALL-NO-MARKER-IS-PRODUCTION",
          wd._thresholds(s2) == prod
          and not [e for e in lr.ledger_events(s2) if e.get("event") == "wall_restored_from_marker"],
          f"{wd._thresholds(s2)}")


# ------------------------------------------------------------------ phase 4
def _registry_row(session: str, pid: int) -> Path:
    p = SESSIONS / f"{pid}.json"
    p.write_text(json.dumps({"pid": pid, "sessionId": session, "status": "idle"}), encoding="utf-8")
    return p


def _dead_pid() -> int:
    """A pid nothing owns. Spawn-and-wait, so the number is genuinely retired."""
    r = subprocess.run([PY, "-c", "import os; print(os.getpid())"], capture_output=True, text=True)
    return int(r.stdout.strip())


def gates_reap_liveness():
    """Phase 4. The reap path's two instruments, and the project it names.

    Measured 2026-09-19 on nine live markers: the file-mtime clock ran up to
    19.0 h behind the conversation clock on a 48 h threshold, and 8 of 9 markers
    stored `cwd: "."`, which the sweep resolves against ITSELF.
    """
    for p in STATE.glob("gsd-autorun-*.json"):
        p.unlink()
    for p in SESSIONS.glob("*.json"):
        p.unlink()
    old = time.time() - 60 * 3600          # silent for 60 h, past DEAD_HOURS=48
    dead_h = 60.0

    # -- D1: the clock ------------------------------------------------------
    # mtime is FRESH (something wrote metadata just now); the conversation is 60 h old.
    s_quiet = sid()
    t_quiet = transcript(s_quiet, "x", rows=[user_cmd("/gsd-autonomous", old),
                                             {"type": "cost-state", "usd": 1.0}])
    idle_s, clock = lr.session_idle_seconds(t_quiet)
    check("V-GSDLR-REAP-CLOCK-IS-THE-CONVERSATION",
          clock == "conversation" and abs(idle_s / 3600.0 - dead_h) < 0.2,
          f"clock={clock} idle_h={idle_s / 3600.0:.2f} mtime_idle_h="
          f"{(time.time() - t_quiet.stat().st_mtime) / 3600.0:.2f}")

    # No timestamped row at all: the weaker clock is used AND labelled as such.
    s_mt = sid()
    t_mt = transcript(s_mt, "x", rows=[{"type": "custom-title", "title": "x"}], idle_s=60 * 3600)
    idle_mt, clock_mt = lr.session_idle_seconds(t_mt)
    check("V-GSDLR-REAP-MTIME-FALLBACK-IS-LABELLED",
          clock_mt == "mtime" and abs(idle_mt / 3600.0 - dead_h) < 0.2,
          f"clock={clock_mt} idle_h={idle_mt / 3600.0:.2f}")

    # -- D2: liveness -------------------------------------------------------
    check("V-GSDLR-LIVENESS-NO-ROW-IS-UNKNOWN", lr.session_liveness(s_quiet) == "unknown",
          f"{lr.session_liveness(s_quiet)}")
    r_live = _registry_row(s_quiet, os.getpid())
    check("V-GSDLR-LIVENESS-RUNNING-PID-IS-LIVE", lr.session_liveness(s_quiet) == "live",
          f"pid={os.getpid()} -> {lr.session_liveness(s_quiet)}")
    check("V-GSDLR-REAP-LIVE-SESSION-VETOES-THE-CLOCK",
          lr.reap_decision(s_quiet, t_quiet)["reap"] is False
          and "running CLI" in lr.reap_decision(s_quiet, t_quiet)["reason"],
          f"{lr.reap_decision(s_quiet, t_quiet)}")
    r_live.unlink()
    # A row naming a pid nobody owns is not evidence of death either -- pid files
    # go stale, and only PRESENCE speaks. Measured: fa6961b6 was actively
    # conversing with no registry row at all.
    r_dead = _registry_row(s_quiet, _dead_pid())
    check("V-GSDLR-LIVENESS-DEAD-PID-IS-STILL-UNKNOWN", lr.session_liveness(s_quiet) == "unknown",
          f"{lr.session_liveness(s_quiet)}")
    d = lr.reap_decision(s_quiet, t_quiet)
    check("V-GSDLR-REAP-SILENT-AND-NOT-LIVE", d["reap"] is True and d["clock"] == "conversation"
          and d["liveness"] == "unknown", f"{d}")
    r_dead.unlink()
    check("V-GSDLR-REAP-MISSING-TRANSCRIPT-STILL-REAPS",
          lr.reap_decision(sid(), None)["reap"] is True, "no transcript")

    # -- D3: the project ----------------------------------------------------
    proj = project("x")
    check("V-GSDLR-PROJECT-ABSOLUTE-RESOLVES", lr.marker_project({"cwd": str(proj)}) == proj,
          f"{lr.marker_project({'cwd': str(proj)})}")
    check("V-GSDLR-PROJECT-REFUSES-RELATIVE",
          lr.marker_project({"cwd": "."}) is None and lr.marker_project({"cwd": ""}) is None
          and lr.marker_project({"cwd": "x"}) is None, "'.' / '' / 'x' all refused")
    # Asserted on what write_marker STORES, not on resolve_cwd's return: the
    # first version of this gate called the helper directly, and a mutation that
    # put the raw `cwd` back into the payload survived the whole suite.
    s_arm = sid()
    armed = json.loads(mk.write_marker(s_arm, "/gsd-autonomous", ".").read_text(encoding="utf-8"))
    s_blank = sid()
    blank = json.loads(mk.write_marker(s_blank, "/gsd-autonomous", "").read_text(encoding="utf-8"))
    check("V-GSDLR-MARKER-ARMS-ABSOLUTE-CWD",
          Path(armed["cwd"]).is_absolute() and lr.marker_project(armed) is not None
          and blank["cwd"] == "", f"stored cwd={armed['cwd']!r} blank={blank['cwd']!r}")

    # The hazard in one gate: ALL_COMPLETE in whatever project the sweep runs in
    # must not finish a marker that never named a project.
    s_rel = sid(); m_rel = _marker_file(s_rel, cwd=".")
    transcript(s_rel, "x", rows=[asst("working")])
    os.environ["_TEST_GSD_STATUS"] = gsd("ALL_COMPLETE")
    acts = lr.sweep(dry_run=True, explain=True)
    os.environ.pop("_TEST_GSD_STATUS", None)
    check("V-GSDLR-RELATIVE-CWD-CANNOT-BE-FINISHED",
          not any(a.get("session_id") == s_rel and a["action"] == "finished" for a in acts)
          and m_rel.exists(), f"{[a for a in acts if a.get('session_id') == s_rel]}")

    # -- an empty sweep that can say why it is empty -------------------------
    kept = [a for a in acts if a["action"] == "kept" and a.get("session_id") == s_rel]
    check("V-GSDLR-SWEEP-EXPLAIN-NAMES-THE-CLAUSE",
          len(kept) == 1 and "ago" in kept[0]["held_by"] and kept[0]["liveness"] == "unknown",
          f"{kept}")
    check("V-GSDLR-SWEEP-EXPLAIN-IS-OPT-IN",
          not any(a["action"] == "kept" for a in lr.sweep(dry_run=True)), "no kept rows by default")

    # -- the reap's own instrument, recorded --------------------------------
    s_reap = sid(); m_reap = _marker_file(s_reap)
    transcript(s_reap, "x", rows=[user_cmd("/gsd-autonomous", old)])
    lr.sweep()
    row = [e for e in lr.ledger_events(s_reap) if e.get("event") == "reaped"]
    check("V-GSDLR-REAP-LEDGERS-ITS-INSTRUMENT",
          not m_reap.exists() and row and row[-1].get("clock") == "conversation"
          and row[-1].get("liveness") == "unknown" and row[-1].get("idle_h") is not None,
          f"{row}")
    m_rel.unlink(missing_ok=True)


def main() -> int:
    try:
        gates_preflight()
        gates_budget_and_mission()
        gates_watchdog()
        gates_test_thresholds()
        gates_session_thresholds()
        gates_sweep()
        gates_compact_tail()
        gates_confirm_aperture()
        gates_reap_liveness()
        gates_wall_survives_its_sidecar()
        gates_report()
        gates_config()
        gates_cli()
    finally:
        # Markers live in the REAL state dir (see module docstring). A mutant that
        # skips a halt skips the per-gate cleanup too, so every id issued is
        # cleared here unconditionally -- measured: one run leaked a marker.
        for s in _ISSUED:
            mk.clear_marker(s)
            for p in Path(tempfile.gettempdir()).glob(f"claude-*{s}*"):
                p.unlink(missing_ok=True)
        shutil.rmtree(TMP, ignore_errors=True)
    total = passes + fails
    tail = f"  inconclusive={inconclusive}" if inconclusive else ""
    print(f"GSDLR_PASS={passes}/{total}  threshold={total}/{total}{tail}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
