#!/usr/bin/env python3
"""test_wrapper.py -- V-gates for the kclaude wrapper (W1-W2 so far).

Hermetic, no-mock-where-possible. W1 (turn_counter) uses an injected assess_fn
so it never depends on a live transcript; W2 (auto_resumer) builds a real tmp
projects tree + pane_map.json (transcript-on-disk anchor exercised for real).

Gates here (extended in W9 with coordinator/cost/naming/overhead/baseline):
  V-TURN-ADVISORY    long transcript -> advisory string (COMPACT/KCLEAR)
  V-TURN-SILENCE     healthy transcript -> None
  V-TURN-FAIL-OPEN   assess_fn raises -> None (no crash)
  V-AUTO-RESUME      cwd with on-disk transcript -> --resume <sid> (correct sid)
  V-AUTO-NEW         cwd with no transcript -> None (no crash)
  V-AUTO-DISK-FALLBACK  no pane_map -> disk scan still resolves --resume
  V-AUTO-ANCHOR      pane_map lists a sid whose .jsonl is GONE -> not resumed
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.wrapper import turn_counter, auto_resumer  # noqa: E402

PASS = 0
FAIL = 0


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


def gate_turn_advisory():
    a = turn_counter.check("x", gaming=False, assess_fn=lambda c, s: _LONG)
    if a and ("KCLEAR" in a or "COMPACT" in a) and "turn-guard" in a:
        _ok("V-TURN-ADVISORY", a[:70] + "...")
    else:
        _fail("V-TURN-ADVISORY", repr(a))


def gate_turn_silence():
    a = turn_counter.check("x", gaming=False, assess_fn=lambda c, s: _HEALTHY)
    if a is None:
        _ok("V-TURN-SILENCE", "healthy -> None")
    else:
        _fail("V-TURN-SILENCE", repr(a))


def gate_turn_fail_open():
    def boom(c, s):
        raise RuntimeError("injected")
    a = turn_counter.check("x", gaming=False, assess_fn=boom)
    if a is None:
        _ok("V-TURN-FAIL-OPEN", "assess_fn raised -> None (no crash)")
    else:
        _fail("V-TURN-FAIL-OPEN", repr(a))


def _seed(proj_base: Path, cwd: str, sid: str, mtime_iso: str | None = None):
    enc = auto_resumer._encode_cwd(cwd)
    d = proj_base / enc
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{sid}.jsonl").write_text('{"type":"summary","summary":"t"}\n',
                                    encoding="utf-8")
    return d


def gate_auto_resume():
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        proj = base / "projects"
        state = base / "state"
        state.mkdir()
        cwd = r"C:\fake\KobiiCraft"
        sid = "11111111-2222-3333-4444-555555555555"
        _seed(proj, cwd, sid)
        pane_map = {"panes": [{"cwd": cwd, "sessionId": sid, "topic": "kc",
                               "lastActivity": "2026-06-23T10:00:00Z"}]}
        (state / "pane_map.json").write_text(json.dumps(pane_map),
                                             encoding="utf-8")
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
        if r.resume_arg is None and r.session_id is None:
            _ok("V-AUTO-NEW", f"no transcript -> None (source={r.source})")
        else:
            _fail("V-AUTO-NEW", f"{r.resume_arg}")


def gate_auto_disk_fallback():
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        proj = base / "projects"
        cwd = r"C:\fake\TUA-X"
        sid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        _seed(proj, cwd, sid)
        # NO pane_map.json -> must fall back to disk scan
        r = auto_resumer.get_resume(cwd, state_dir=base / "state",
                                    proj_base=proj)
        if r.resume_arg == f"--resume {sid}" and r.source == "disk":
            _ok("V-AUTO-DISK-FALLBACK", f"{r.resume_arg} (source={r.source})")
        else:
            _fail("V-AUTO-DISK-FALLBACK", f"{r.resume_arg} source={r.source}")


def gate_auto_anchor():
    """pane_map lists a sid whose .jsonl does NOT exist -> must NOT resume it."""
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        proj = base / "projects"
        proj.mkdir()
        state = base / "state"
        state.mkdir()
        cwd = r"C:\fake\Ghost"
        ghost_sid = "00000000-0000-0000-0000-000000000000"
        pane_map = {"panes": [{"cwd": cwd, "sessionId": ghost_sid,
                               "topic": "ghost",
                               "lastActivity": "2026-06-23T10:00:00Z"}]}
        (state / "pane_map.json").write_text(json.dumps(pane_map),
                                             encoding="utf-8")
        # NOTE: no <ghost_sid>.jsonl on disk.
        r = auto_resumer.get_resume(cwd, state_dir=state, proj_base=proj)
        if r.resume_arg is None:
            _ok("V-AUTO-ANCHOR",
                "pane_map sid without .jsonl -> not resumed (disk anchor)")
        else:
            _fail("V-AUTO-ANCHOR", f"resumed a ghost: {r.resume_arg}")


def main() -> int:
    print("=" * 60)
    print("kclaude wrapper V-gates (W1 turn_counter + W2 auto_resumer)")
    print("=" * 60)
    for gate in (
        gate_turn_advisory,
        gate_turn_silence,
        gate_turn_fail_open,
        gate_auto_resume,
        gate_auto_new,
        gate_auto_disk_fallback,
        gate_auto_anchor,
    ):
        try:
            gate()
        except Exception as exc:  # noqa: BLE001
            _fail(gate.__name__, f"raised {type(exc).__name__}: {exc}")
    print()
    print(f"WRAPPER_W1W2={PASS}/{PASS + FAIL}  threshold=7/7")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
