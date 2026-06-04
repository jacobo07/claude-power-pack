#!/usr/bin/env python3
"""test_auto_reset.py - V-gates for the Auto-Reset Orchestrator (M7).

Hermetic: pure evaluate()/orchestrate() cores + tempdir work_state writes, so
8/8 is stable across consecutive runs (no global ~/.claude writes, no time
window coupling). V-BASELINE-INTACT shells out to the real pytest suite.

Gates:
  V-MONITOR-HEALTHY   normal signals  -> HEALTHY
  V-MONITOR-COMPACT   RAM > WARN_GB    -> COMPACT_NEEDED
  V-MONITOR-KCLEAR    RAM > CRIT_GB    -> KCLEAR_NEEDED
  V-WORK-STATE-SAVES  save -> load round-trip, no loss
  V-WORK-STATE-FIELDS record has task + last_commit + pending (populated)
  V-ORCHESTRATOR-RUNS no crash; HEALTHY->none, COMPACT->advisory
  V-RESUME-INJECTS    saved work_state carries every field the hub reads,
                      as JSON the hub's JSON.parse accepts (live JS injection
                      verified E2E in M5)
  V-BASELINE-INTACT   pytest tests/ -> 0 failed
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  [OK]   {gate}: {evidence}")


def _fail(gate: str, detail: str) -> None:
    global _fails
    _fails += 1
    print(f"  [FAIL] {gate}: {detail}")


def test_monitor() -> None:
    from modules.cpc_os.context_monitor import (
        evaluate, HEALTHY, COMPACT_NEEDED, KCLEAR_NEEDED,
    )
    kw = dict(warn_gb=20, crit_gb=28, compact_mb=4, kclear_mb=6,
              compact_turns=1200, kclear_turns=2400)
    # NB: evaluate()'s first arg is RAM in GB (not MB) -- pass GB directly.
    h = evaluate(5, 1.0, 100, **kw)
    if h["state"] == HEALTHY:
        _ok("V-MONITOR-HEALTHY", "ram 5GB/jsonl 1MB/100 turns -> HEALTHY")
    else:
        _fail("V-MONITOR-HEALTHY", f"got {h['state']}")

    c = evaluate(21, 1.0, 100, **kw)
    if c["state"] == COMPACT_NEEDED:
        _ok("V-MONITOR-COMPACT", f"ram 21GB -> COMPACT_NEEDED {c['tripped']}")
    else:
        _fail("V-MONITOR-COMPACT", f"got {c['state']}")

    k = evaluate(29, 1.0, 100, **kw)
    if k["state"] == KCLEAR_NEEDED:
        _ok("V-MONITOR-KCLEAR", f"ram 29GB -> KCLEAR_NEEDED {k['tripped']}")
    else:
        _fail("V-MONITOR-KCLEAR", f"got {k['state']}")


def test_work_state() -> None:
    from modules.cpc_os.work_state_saver import (
        save_work_state, load_work_state_for_cwd,
    )
    with tempfile.TemporaryDirectory() as td:
        # Use the PP repo as cwd so git fields (branch/commit) populate real.
        rec = save_work_state(str(PP), session_id="m7test",
                              task="M7 work-state test", state_dir=td)
        back = load_work_state_for_cwd(str(PP), state_dir=td)
        if (back and back["task"] == "M7 work-state test"
                and back["cwd"] == str(PP)
                and back["last_commit"] == rec["last_commit"]):
            _ok("V-WORK-STATE-SAVES", "save -> load_for_cwd round-trip, no loss")
        else:
            _fail("V-WORK-STATE-SAVES", f"loaded={back}")

        has_fields = all(k in rec for k in ("task", "last_commit", "pending"))
        populated = bool(rec.get("last_commit")) and isinstance(
            rec.get("pending"), list)
        if has_fields and populated:
            _ok("V-WORK-STATE-FIELDS",
                f"task+commit+pending present; commit={rec['last_commit'][:14]}"
                f" pending={len(rec['pending'])}")
        else:
            _fail("V-WORK-STATE-FIELDS",
                  f"has_fields={has_fields} populated={populated}")


def test_orchestrator() -> None:
    from modules.cpc_os.auto_reset_orchestrator import orchestrate

    def save_fn(cwd, session_id=None, state_dir=None):
        return {"task": "t", "last_commit": "abc123 x", "last_file": "f.py",
                "pending": [], "session_id": session_id, "cwd": cwd,
                "_path": "/tmp/x.json"}

    r_ok = orchestrate("C:/x", "s",
                       assess_fn=lambda c, s: {"state": "HEALTHY",
                                               "tripped": [], "signals": {}},
                       save_fn=save_fn)
    r_c = orchestrate("C:/x", "s",
                      assess_fn=lambda c, s: {"state": "COMPACT_NEEDED",
                                              "tripped": ["x"], "signals": {}},
                      save_fn=save_fn)
    if (r_ok["action"] == "none" and r_ok["advisory"] is None
            and r_c["action"] == "compact" and r_c["advisory"]
            and "/compact focus on" in r_c["advisory"]):
        _ok("V-ORCHESTRATOR-RUNS",
            "HEALTHY->none(no advisory); COMPACT->advisory with slash line")
    else:
        _fail("V-ORCHESTRATOR-RUNS",
              f"ok={r_ok['action']}/{r_ok['advisory']} c={r_c['action']}")


def test_resume_contract() -> None:
    """Contract guard for the JS consumer (hub.hookWorkStateResume): the saved
    work_state must carry every field the hub reads, as valid JSON. Live JS
    injection was verified E2E in M5."""
    import json
    from modules.cpc_os.work_state_saver import save_work_state
    with tempfile.TemporaryDirectory() as td:
        rec = save_work_state(str(PP), session_id="m7resume",
                              task="resume contract", state_dir=td)
        try:
            parsed = json.loads(Path(rec["_path"]).read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            _fail("V-RESUME-INJECTS", f"work_state not valid JSON: {exc}")
            return
        needed = ("cwd", "task", "last_commit", "last_file", "pending")
        missing = [k for k in needed if k not in parsed]
        if not missing:
            _ok("V-RESUME-INJECTS",
                "work_state carries cwd+task+last_commit+last_file+pending "
                "(fields the hub injects); valid JSON")
        else:
            _fail("V-RESUME-INJECTS", f"missing fields: {missing}")


def test_baseline() -> None:
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q",
             "-p", "no:cacheprovider"],
            cwd=str(PP), capture_output=True, text=True, timeout=180,
        )
    except subprocess.TimeoutExpired:
        _fail("V-BASELINE-INTACT", "pytest timeout >180s")
        return
    except Exception as exc:  # noqa: BLE001
        _fail("V-BASELINE-INTACT", f"{type(exc).__name__}: {exc}")
        return
    last = (r.stdout.strip().splitlines() or [""])[-1]
    if r.returncode == 0 and "passed" in r.stdout and "failed" not in last:
        _ok("V-BASELINE-INTACT", last.strip())
    else:
        _fail("V-BASELINE-INTACT",
              f"rc={r.returncode} | {last} | {r.stderr.strip()[:120]}")


def main() -> int:
    print("=" * 64)
    print("test_auto_reset -- Auto-Reset Orchestrator V-gates (M7)")
    print("=" * 64)
    for fn in (test_monitor, test_work_state, test_orchestrator,
               test_resume_contract, test_baseline):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            _fail(fn.__name__, f"{type(exc).__name__}: {exc}")
    total = _passes + _fails
    print(f"AUTO_RESET_PASS={_passes}/{total}  fails={_fails}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
