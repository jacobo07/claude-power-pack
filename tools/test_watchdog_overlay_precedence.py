#!/usr/bin/env python
"""V-OVLY-* — the auto-reset advisory must not swallow an armed run's Stop.

Spec: vault/specs/gsd-long-run-v2.md (the continuation path), and
      context-watchdog.py's own Auto-Reset Orchestrator overlay (M4).

WHY THIS GATE EXISTS (measured 2026-09-20, session 37cfb187)
-------------------------------------------------------------
`_run_inner` opens with:

    overlay = _orchestrator_overlay(event)
    if overlay:
        return overlay

Everything the long-run mechanism needs lives BELOW that return: the used_pct
read, the endpoint refresh, the resume confirmation, the rearm, the
post-compaction resume, the snapshot, the crossing and the `/compact`
instruction. So when the overlay fires, an armed run loses that entire Stop.

The overlay is once-per-session, so the blast radius is one Stop -- but it
fires on CONTEXT PRESSURE (turn count, active-jsonl bytes, RAM), which is the
same condition that produces a crossing. The single Stop it is most likely to
land on is therefore exactly the Stop the run cannot afford to lose. That is
the guard-reachability shape one level in: the advisory is reached precisely
when the load-bearing path is needed, and it wins.

An armed session must keep its continuation path. The advisory is still worth
surfacing -- it saves work_state and tells the Owner something true -- so the
fix layers it on rather than replacing it, and V-OVLY-ARMED-ADVISORY-AUDIBLE
below is what stops a fix from silencing it.

THE DISCRIMINATOR
-----------------
`_LAST["used_pct"]` is stamped at the line immediately after the metrics read
and is reachable ONLY past the overlay's early return. Asserting on it drives
the exact branch without entering the crossing or resume paths, so this gate
spawns no daemon, writes no trigger flag and sends nothing to any terminal --
it is safe to run on a host with no memory headroom, which is the host this
was written on (603 MB free of 32 GB).

HERMETIC: every marker, flag and endpoint is namespaced to a synthetic session
id created here and removed in `main`'s finally. The percentage is forced, so
the real session's metrics file is never read.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WATCHDOG = ROOT / "modules" / "zero-crash" / "hooks" / "context-watchdog.py"
STATE_DIR = Path.home() / ".claude" / "state"

# Ledger rows go to a throwaway dir: this suite must never write synthetic
# sessions into the Owner's real long-run ledger.
os.environ["GSD_LONG_RUN_STATE_DIR"] = tempfile.mkdtemp(prefix="ovly-state-")

# ABSOLUTE, never derived from the module under test. 25% is what a
# post-compaction reading MEANS; it sits below every floor, so the legacy path
# is reached and then has nothing to do -- which is the quiet window this gate
# needs in order to observe the branch and nothing else.
QUIET_PCT = 25.0

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  OK   {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {gate}: {diagnostic}")


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _arm(session_id: str) -> Path:
    """Write a minimal armed marker for a synthetic session."""
    path = STATE_DIR / f"gsd-autorun-{session_id}.json"
    now = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "+00:00"
    path.write_text(json.dumps({
        "session_id": session_id,
        "resume_command": "/gsd-autonomous",
        "cwd": str(ROOT),
        "phase": None,
        "ts": now,
        "armed_at": now,
        "cycles": 0,
        "max_cycles": 12,
        "max_hours": 24.0,
        "schema_version": 2,
        "mission": {"terms": ["overlay"], "matched": ["overlay"],
                    "active_milestone": "synthetic"},
        "wall": {"snapshot": 35.0, "advisory": 40.0, "rearm": 30.0,
                 "stamped_at": now},
    }), encoding="utf-8")
    return path


def _run_forced(wd, session_id: str, pct: float) -> dict:
    """One Stop with the overlay FORCED to fire and the percentage pinned."""
    # The M1 STATE name, not the orchestrator's action name: `_ACTION` maps
    # COMPACT_NEEDED -> "compact", and an unknown state maps to "none", which
    # returns no overlay at all. Passing "compact" here cost one run and the
    # positive control is what named it.
    os.environ["_TEST_ORCH_STATE"] = "COMPACT_NEEDED"
    os.environ["_TEST_CONTEXT_PCT"] = str(pct)
    try:
        return wd.run({"session_id": session_id, "cwd": str(ROOT),
                       "transcript_path": ""}) or {}
    finally:
        os.environ.pop("_TEST_ORCH_STATE", None)
        os.environ.pop("_TEST_CONTEXT_PCT", None)


def _cleanup(session_id: str) -> None:
    for pat in (f"gsd-autorun-{session_id}.json",
                f"continuation-endpoint-{session_id}.json",
                f"work_state_{session_id}.json",
                f"ctxwd-thresholds-{session_id}.json"):
        try:
            (STATE_DIR / pat).unlink()
        except OSError:
            pass
    tmp = Path(tempfile.gettempdir())
    for pat in (f"claude-orch-{session_id}.ts",
                f"claude-orch-adv-{session_id}.flag"):
        try:
            (tmp / pat).unlink()
        except OSError:
            pass


# --------------------------------------------------------------------------
def gate_control(wd, sid: str) -> bool:
    """POSITIVE CONTROL: the forcing works and the overlay really fires.

    Without this every assertion below is satisfied by an overlay that simply
    never ran, which is the same observable as a fix that works.
    """
    out = _run_forced(wd, sid, QUIET_PCT)
    msg = out.get("systemMessage") or ""
    if "AUTO-RESET" in msg:
        _ok("V-OVLY-CONTROL-FORCED",
            f"overlay fired on an unarmed session: {msg[:60]}...")
        return True
    _fail("V-OVLY-CONTROL-FORCED",
          f"_TEST_ORCH_STATE did not produce an overlay (got {out!r}) — "
          "every other gate in this file would pass vacuously")
    return False


def gate_unarmed_short_circuits(wd, sid: str) -> None:
    """An UNARMED session keeps today's behaviour exactly: overlay wins.

    The fix must not change the ordinary session. If this goes red, the fix
    widened its blast radius beyond armed runs.
    """
    out = _run_forced(wd, sid, QUIET_PCT)
    reached = wd._LAST.get("used_pct")
    if "AUTO-RESET" in (out.get("systemMessage") or "") and reached is None:
        _ok("V-OVLY-UNARMED-SHORT-CIRCUITS",
            "unarmed: advisory returned, legacy path skipped (used_pct unset)")
    else:
        _fail("V-OVLY-UNARMED-SHORT-CIRCUITS",
              f"unarmed behaviour changed — used_pct={reached!r}, out={out!r}")


def gate_armed_legacy_reached(wd, sid: str) -> None:
    """THE DEFECT. An ARMED run must keep its continuation path.

    `_LAST['used_pct']` is stamped just past the overlay's early return, so a
    value here is proof the Stop reached the rearm / resume / crossing logic.
    """
    _arm(sid)
    out = _run_forced(wd, sid, QUIET_PCT)
    reached = wd._LAST.get("used_pct")
    if reached == QUIET_PCT:
        _ok("V-OVLY-ARMED-LEGACY-REACHED",
            f"armed: reached the continuation path at used_pct={reached}")
    else:
        _fail("V-OVLY-ARMED-LEGACY-REACHED",
              f"armed run lost this Stop to the auto-reset advisory — "
              f"used_pct={reached!r} (expected {QUIET_PCT}); the rearm, the "
              f"resume and the crossing were all skipped. out={out!r}")


def gate_armed_advisory_audible(wd, sid: str) -> None:
    """The advisory must survive the fix, not be traded away for it.

    At QUIET_PCT the legacy path has nothing to say, so whatever comes back is
    the overlay or nothing. Silence here means a fix bought the continuation
    path by deleting a true warning.
    """
    _arm(sid)
    out = _run_forced(wd, sid, QUIET_PCT)
    if "AUTO-RESET" in (out.get("systemMessage") or ""):
        _ok("V-OVLY-ARMED-ADVISORY-AUDIBLE",
            "armed: the auto-reset advisory still reaches the Owner")
    else:
        _fail("V-OVLY-ARMED-ADVISORY-AUDIBLE",
              f"the advisory was silenced for armed runs — out={out!r}")


def main() -> int:
    wd = _load(WATCHDOG, "ctxwd_ovly")
    sessions = [f"ovly-{uuid.uuid4().hex[:12]}" for _ in range(4)]
    try:
        print("V-OVLY-* — auto-reset advisory vs the armed continuation path")
        if not gate_control(wd, sessions[0]):
            print(f"\nOVLY_PASS={_passes}/{_passes + _fails}  threshold=4/4  "
                  "HARNESS-FAILED: the positive control could not fire")
            return 2
        gate_unarmed_short_circuits(wd, sessions[1])
        gate_armed_legacy_reached(wd, sessions[2])
        gate_armed_advisory_audible(wd, sessions[3])
    finally:
        for sid in sessions:
            _cleanup(sid)

    total = _passes + _fails
    print(f"\nOVLY_PASS={_passes}/{total}  threshold=4/4")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
