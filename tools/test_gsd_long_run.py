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
for d in (STATE, HOOKS, PROJECTS):
    d.mkdir(parents=True)
os.environ.update({"GSD_LONG_RUN_STATE_DIR": str(STATE), "GSD_LONG_RUN_HOOKS_DIR": str(HOOKS),
                   "GSD_LONG_RUN_PROJECTS_DIR": str(PROJECTS), "GSD_LONG_RUN_NO_SPAWN": "1"})

passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


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

    if ABSW2.is_dir():
        st = lr.gsd_status(ABSW2)
        check("V-GSDLR-REAL-GSD-ABSW2", st["outcome"] == "NO_PHASES" and st.get("phase_count") == 0,
              f"real gsd-tools on ABSW2 -> {st}")
    else:
        check("V-GSDLR-REAL-GSD-ABSW2", False, f"INCONCLUSIVE: {ABSW2} absent on this host")


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
    saved = (wd._write_trigger_flag, wd._spawn_daemon)
    wd._write_trigger_flag = lambda *a, **k: calls.append(k) or "flag"
    wd._spawn_daemon = lambda *a, **k: True
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
        wd._write_trigger_flag, wd._spawn_daemon = saved

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
    wd2._write_trigger_flag = lambda *a, **k: rec.append(k) or "flag"
    wd2._spawn_daemon = lambda *a, **k: True
    s = sid(); _stamp(wd2, s)
    try:
        mk.write_marker(s, "/gsd-autonomous", cwd=str(ROOT))
        out = _run(wd2, s, 75.0, str(TMP / "t.jsonl"))
        check("V-GSDLR-WD-CROSSING-LEDGERED", "crossing" in events(s) and out.get("decision") == "block",
              f"events={events(s)}")
        check("V-GSDLR-WD-COMPACT-EXPECTS-PREFIX", rec and rec[-1].get("expect_prefix") == "/compact",
              f"kwargs={rec[-1] if rec else None}")
        check("V-GSDLR-WD-TEXT-FIXED", "auto-compact-pending-<session>.flag" in out.get("reason", "")
              and "auto-compact-pending.flag " not in out.get("reason", ""), "tier-2 names the per-session flag")
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
    flag = HOOKS / f"auto-compact-trigger-{s_rec}.flag"
    body = json.loads(flag.read_text(encoding="utf-8")) if flag.exists() else {}
    check("V-GSDLR-SWEEP-RECOVERS", (s_rec, "recovered") in by and body.get("expect_line") == "/absw2-continue",
          f"flag={body}")
    check("V-GSDLR-SWEEP-RECORDS-STALL", (s_st, "stalled") in by and "stalled" in events(s_st), f"{acts}")
    check("V-GSDLR-SWEEP-FRESH-UNTOUCHED", not any(a.get("session_id") == s_fresh for a in acts), f"{acts}")
    check("V-GSDLR-SWEEP-DAEMON-FOR-FLAGS", any(a["action"] == "daemon" for a in acts), f"{acts}")

    flag.unlink()
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
            "--cwd", str(good), "--mission", "angry,birds,rovio,powerpc,slingshot"]
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


def main() -> int:
    try:
        gates_preflight()
        gates_budget_and_mission()
        gates_watchdog()
        gates_test_thresholds()
        gates_sweep()
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
    print(f"GSDLR_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
