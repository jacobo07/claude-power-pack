#!/usr/bin/env python3
"""test_wrapper.py -- V-gates for the kclaude wrapper (W1-W5 + prelaunch).

Hermetic, no-mock-where-possible. W1 (turn_counter) uses an injected assess_fn;
W2 (auto_resumer) builds a real tmp projects tree + pane_map.json; W3/W4/W5 use
injected readers/clocks so there are NO real sleeps and NO live transcripts.

Gates:
  W1/W2 (existing):
    V-TURN-ADVISORY        long transcript -> advisory string (COMPACT/KCLEAR)
    V-TURN-SILENCE         healthy transcript -> None
    V-TURN-FAIL-OPEN       assess_fn raises -> None (no crash)
    V-AUTO-RESUME          cwd with on-disk transcript -> --resume <sid>
    V-AUTO-NEW             cwd with no transcript -> None (no crash)
    V-AUTO-DISK-FALLBACK   no pane_map -> disk scan resolves --resume
    V-AUTO-ANCHOR          pane_map sid whose .jsonl is GONE -> not resumed
  W3/W4/W5 (this round):
    V-SESSION-NAMING       new sid via snapshot -> pane_map.md entry, label set
    V-SESSION-NAMING-RESUME --resume -> updated_at bumped in names store
    V-COORDINATOR-WARN     active <2h session on cwd -> warning produced
    V-COORDINATOR-DEFAULT-S default action carries --resume <sid>
    V-COST-GATE-REAL-DATA  burn over threshold (token_ground_truth source) -> line
    V-COST-GATE-SILENT-FAIL no data + healthy -> silence (no crash, no mock)
    V-W3W4W5-FAILOPEN      a raising injected fn in each feature -> safe, no crash
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.wrapper import (  # noqa: E402
    turn_counter, auto_resumer, session_namer, repo_coordinator, cost_gate,
)

PASS = 0
FAIL = 0
NOW = datetime(2026, 6, 23, 12, 0, 0, tzinfo=timezone.utc)


def _ok(g, ev):
    global PASS
    PASS += 1
    print(f"  [OK]   {g}: {ev}")


def _fail(g, ev):
    global FAIL
    FAIL += 1
    print(f"  [FAIL] {g}: {ev}")


_LONG = {"state": "KCLEAR_NEEDED",
         "signals": {"ram_gb": 1.0, "jsonl_mb": 30, "turns": 13000},
         "tripped": ["jsonl 30MB>=24MB"]}
_HEALTHY = {"state": "HEALTHY",
            "signals": {"ram_gb": 1.0, "jsonl_mb": 1, "turns": 10},
            "tripped": []}


# --- W1 -----------------------------------------------------------------
def gate_turn_advisory():
    a = turn_counter.check("x", gaming=False, assess_fn=lambda c, s: _LONG)
    if a and ("KCLEAR" in a or "COMPACT" in a) and "turn-guard" in a:
        _ok("V-TURN-ADVISORY", a[:60] + "...")
    else:
        _fail("V-TURN-ADVISORY", repr(a))


def gate_turn_silence():
    a = turn_counter.check("x", gaming=False, assess_fn=lambda c, s: _HEALTHY)
    _ok("V-TURN-SILENCE", "healthy -> None") if a is None else _fail(
        "V-TURN-SILENCE", repr(a))


def gate_turn_fail_open():
    def boom(c, s):
        raise RuntimeError("injected")
    a = turn_counter.check("x", gaming=False, assess_fn=boom)
    _ok("V-TURN-FAIL-OPEN", "raise -> None") if a is None else _fail(
        "V-TURN-FAIL-OPEN", repr(a))


# --- W2 -----------------------------------------------------------------
def _seed(proj_base: Path, cwd: str, sid: str):
    d = proj_base / auto_resumer._encode_cwd(cwd)
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{sid}.jsonl").write_text('{"type":"summary","summary":"t"}\n',
                                    encoding="utf-8")
    return d


def gate_auto_resume():
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        proj, state = base / "projects", base / "state"
        state.mkdir()
        cwd = r"C:\fake\KobiiCraft"
        sid = "11111111-2222-3333-4444-555555555555"
        _seed(proj, cwd, sid)
        (state / "pane_map.json").write_text(json.dumps({"panes": [
            {"cwd": cwd, "sessionId": sid, "topic": "kc",
             "lastActivity": "2026-06-23T10:00:00Z"}]}), encoding="utf-8")
        r = auto_resumer.get_resume(cwd, state_dir=state, proj_base=proj)
        if r.resume_arg == f"--resume {sid}" and r.source == "pane_map":
            _ok("V-AUTO-RESUME", f"{r.resume_arg} (source={r.source})")
        else:
            _fail("V-AUTO-RESUME", f"{r.resume_arg} source={r.source}")


def gate_auto_new():
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        r = auto_resumer.get_resume(r"C:\fake\NoSuchRepo",
                                    state_dir=base / "state",
                                    proj_base=base / "projects")
        _ok("V-AUTO-NEW", f"no transcript -> None ({r.source})") \
            if r.resume_arg is None else _fail("V-AUTO-NEW", f"{r.resume_arg}")


def gate_auto_disk_fallback():
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        proj = base / "projects"
        cwd = r"C:\fake\TUA-X"
        sid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        _seed(proj, cwd, sid)
        r = auto_resumer.get_resume(cwd, state_dir=base / "state",
                                    proj_base=proj)
        if r.resume_arg == f"--resume {sid}" and r.source == "disk":
            _ok("V-AUTO-DISK-FALLBACK", f"{r.resume_arg} (source={r.source})")
        else:
            _fail("V-AUTO-DISK-FALLBACK", f"{r.resume_arg} source={r.source}")


def gate_auto_anchor():
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        proj, state = base / "projects", base / "state"
        proj.mkdir()
        state.mkdir()
        cwd = r"C:\fake\Ghost"
        ghost = "00000000-0000-0000-0000-000000000000"
        (state / "pane_map.json").write_text(json.dumps({"panes": [
            {"cwd": cwd, "sessionId": ghost, "topic": "ghost",
             "lastActivity": "2026-06-23T10:00:00Z"}]}), encoding="utf-8")
        r = auto_resumer.get_resume(cwd, state_dir=state, proj_base=proj)
        _ok("V-AUTO-ANCHOR", "pane_map sid w/o .jsonl -> not resumed") \
            if r.resume_arg is None else _fail("V-AUTO-ANCHOR",
                                                f"resumed ghost: {r.resume_arg}")


# --- W3 -----------------------------------------------------------------
def gate_session_naming():
    with tempfile.TemporaryDirectory() as td:
        state = Path(td)
        cwd = r"C:\fake\NewRepo"
        new_sid = "99999999-aaaa-bbbb-cccc-dddddddddddd"
        snap = [{"cwd": cwd, "session_id": new_sid, "since": "2026-06-23T11:59:00Z"}]
        r = session_namer.name_session(
            cwd, known_sids={"OLD-SID"}, state_dir=state,
            timeout_s=1.0, interval_s=0.01,
            snapshot_reader=lambda: snap, sleep_fn=lambda s: None,
            git_subject_fn=lambda c: "do real work", now=NOW)
        pm = (state / session_namer.PANE_MAP_MD)
        store = json.loads((state / session_namer.NAMES_STORE).read_text("utf-8"))
        md = pm.read_text("utf-8") if pm.is_file() else ""
        if (r.source == "named" and r.label and new_sid in md
                and store.get(new_sid, {}).get("label")):
            _ok("V-SESSION-NAMING", f"label={r.label!r} in pane_map.md")
        else:
            _fail("V-SESSION-NAMING", f"src={r.source} label={r.label!r} md={new_sid in md}")


def gate_session_naming_resume():
    with tempfile.TemporaryDirectory() as td:
        state = Path(td)
        sid = "55555555-6666-7777-8888-999999999999"
        r = session_namer.touch_resume(sid, r"C:\fake\R", state_dir=state, now=NOW)
        store = json.loads((state / session_namer.NAMES_STORE).read_text("utf-8"))
        ua = store.get(sid, {}).get("updated_at", "")
        if r.source == "resume-touch" and ua.startswith("2026-06-23"):
            _ok("V-SESSION-NAMING-RESUME", f"updated_at={ua}")
        else:
            _fail("V-SESSION-NAMING-RESUME", f"src={r.source} ua={ua}")


# --- W4 -----------------------------------------------------------------
def gate_coordinator_warn_and_default():
    cwd = r"C:\fake\BusyRepo"
    recent = (NOW - timedelta(minutes=30)).isoformat()
    cands = [{"session_id": "S1", "topic": "work", "lastActivity": recent}]
    d = repo_coordinator.coordinate(cwd, now=NOW, list_fn=lambda *a, **k: cands)
    if d.active and d.warning and "BusyRepo" in d.warning:
        _ok("V-COORDINATOR-WARN", d.warning)
    else:
        _fail("V-COORDINATOR-WARN", f"active={d.active} warn={d.warning!r}")
    if d.default_resume == "--resume S1":
        _ok("V-COORDINATOR-DEFAULT-S", d.default_resume)
    else:
        _fail("V-COORDINATOR-DEFAULT-S", f"{d.default_resume}")


def gate_coordinator_stale_not_active():
    # a session older than 2h must NOT trigger a warning
    cwd = r"C:\fake\IdleRepo"
    old = (NOW - timedelta(hours=5)).isoformat()
    cands = [{"session_id": "OLD", "topic": "x", "lastActivity": old}]
    d = repo_coordinator.coordinate(cwd, now=NOW, list_fn=lambda *a, **k: cands)
    _ok("V-COORDINATOR-STALE", "5h-old -> not active") if not d.active else \
        _fail("V-COORDINATOR-STALE", f"active={d.active}")


# --- W5 -----------------------------------------------------------------
def gate_cost_gate_real_data():
    # token_ground_truth.today_output_tokens must exist (the only valid source)
    from tools.token_ground_truth import today_output_tokens  # noqa: F401
    g = cost_gate.cost_gate(
        r"C:\fake\R", now=NOW,
        burn_fn=lambda **k: 150_000_000,
        assess_fn=lambda c, s: {"state": "HEALTHY"})
    if g.source == "advisory" and any("salida hoy" in ln for ln in g.lines):
        _ok("V-COST-GATE-REAL-DATA", g.lines[0][:55] + "...")
    else:
        _fail("V-COST-GATE-REAL-DATA", f"src={g.source} lines={g.lines}")


def gate_cost_gate_silent_fail():
    g = cost_gate.cost_gate(
        r"C:\fake\R", burn_fn=lambda **k: None,
        assess_fn=lambda c, s: {"state": "HEALTHY"})
    if g.source == "silent" and g.lines == []:
        _ok("V-COST-GATE-SILENT-FAIL", "no data -> silence")
    else:
        _fail("V-COST-GATE-SILENT-FAIL", f"src={g.source} lines={g.lines}")


# --- fail-open across W3/W4/W5 ------------------------------------------
def gate_w3w4w5_failopen():
    errs = []

    def boom(*a, **k):
        raise RuntimeError("injected")

    # W3: snapshot reader raises -> name_session must not raise
    try:
        r = session_namer.name_session(
            r"C:\x", known_sids=set(), timeout_s=0.2, interval_s=0.01,
            snapshot_reader=boom, sleep_fn=lambda s: None)
        if r.session_id is not None:
            errs.append(f"W3 unexpected sid {r.session_id}")
    except Exception as e:  # noqa: BLE001
        errs.append(f"W3 raised {e!r}")

    # W4: list_fn raises -> coordinate fail-open inactive
    try:
        d = repo_coordinator.coordinate(r"C:\x", now=NOW, list_fn=boom)
        if d.active:
            errs.append("W4 active on error")
    except Exception as e:  # noqa: BLE001
        errs.append(f"W4 raised {e!r}")

    # W5: burn + assess raise -> silent, no crash
    try:
        g = cost_gate.cost_gate(r"C:\x", burn_fn=boom, assess_fn=boom)
        if g.lines:
            errs.append(f"W5 leaked lines {g.lines}")
    except Exception as e:  # noqa: BLE001
        errs.append(f"W5 raised {e!r}")

    _ok("V-W3W4W5-FAILOPEN", "all 3 fail-open, no crash") if not errs else \
        _fail("V-W3W4W5-FAILOPEN", "; ".join(errs))


def main() -> int:
    print("=" * 62)
    print("kclaude wrapper V-gates (W1 turn / W2 resume / W3 name / W4 coord / W5 cost)")
    print("=" * 62)
    gates = (
        gate_turn_advisory, gate_turn_silence, gate_turn_fail_open,
        gate_auto_resume, gate_auto_new, gate_auto_disk_fallback,
        gate_auto_anchor,
        gate_session_naming, gate_session_naming_resume,
        gate_coordinator_warn_and_default, gate_coordinator_stale_not_active,
        gate_cost_gate_real_data, gate_cost_gate_silent_fail,
        gate_w3w4w5_failopen,
    )
    for g in gates:
        try:
            g()
        except Exception as exc:  # noqa: BLE001
            _fail(g.__name__, f"raised {type(exc).__name__}: {exc}")
    print()
    print(f"WRAPPER={PASS}/{PASS + FAIL}  threshold=15/15")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
