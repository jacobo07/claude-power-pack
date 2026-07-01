#!/usr/bin/env python3
"""test_parallel_mesh.py -- Parallel Cognitive Mesh done-gates. Hermetic
(tmp state dirs, injected gather_fn, fixed clock), re-runnable. Grows one
sprint at a time.

Sprint 1 (PM-02): scope-gate recalibration of CO-08's blunt same-repo cap.
"""
from __future__ import annotations

import sys
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.cognitive_os import scheduler as S       # noqa: E402
from modules.parallel_mesh import pm_02_intent as PM2  # noqa: E402

_p = 0
_f = 0


def _ok(gate, ev):
    global _p
    _p += 1
    print(f"  PASS {gate}: {ev}")


def _fail(gate, diag):
    global _f
    _f += 1
    print(f"  FAIL {gate}: {diag}")


CWD = "/repo/tua-x"
ENC = S._enc(CWD)
NOW = datetime(2026, 7, 1, 12, 0, 0, tzinfo=timezone.utc)


def _hot(*sids):
    """Build scheduler hot items for the same repo."""
    return [{"sid": s, "encs": [ENC]} for s in sids]


def _gather(hot):
    """Injected gather_fn honoring exclude_sid, ignoring the rest."""
    def g(**kw):
        ex = kw.get("exclude_sid")
        return [h for h in hot if h["sid"] != ex]
    return g


def main():
    print("[PM-02 -- scope-gate recalibration]")

    # V-PM02-INTENT-ALLOWED: two declared, disjoint same-repo panes -> both run.
    with tempfile.TemporaryDirectory() as td:
        reg = PM2.PaneIntentRegistry(state_dir=td)
        reg.declare("A", CWD, ["modules/x.py"], now=NOW)
        v = PM2.scope_gated_admit(CWD, "B", ["modules/y.py"], registry=reg,
                                  now=NOW, gather_fn=_gather(_hot("A")))
        if v.verdict == "proceed":
            _ok("V-PM02-INTENT-ALLOWED",
                "2 disjoint declared same-repo panes admitted simultaneously")
        else:
            _fail("V-PM02-INTENT-ALLOWED",
                  f"expected proceed, got {v.verdict}: {v.reasons}")

    # V-PM02-COLLISION-REFUSED: two declared, OVERLAPPING scopes -> refuse.
    with tempfile.TemporaryDirectory() as td:
        reg = PM2.PaneIntentRegistry(state_dir=td)
        reg.declare("A", CWD, ["modules/x.py"], now=NOW)
        v = PM2.scope_gated_admit(CWD, "B", ["modules/x.py"], registry=reg,
                                  now=NOW, gather_fn=_gather(_hot("A")))
        if v.verdict == "refuse" and any("collides" in r for r in v.reasons):
            _ok("V-PM02-COLLISION-REFUSED",
                f"overlapping scope refused with resolution: {v.reasons[0]}")
        else:
            _fail("V-PM02-COLLISION-REFUSED",
                  f"expected refuse-on-collision, got {v.verdict}: {v.reasons}")

    # V-PM02-UNKNOWNSCOPE-REFUSED: declared pane, but incumbent has no intent ->
    # non-overlap cannot be proven -> refuse (conservative).
    with tempfile.TemporaryDirectory() as td:
        reg = PM2.PaneIntentRegistry(state_dir=td)  # A intentionally NOT declared
        v = PM2.scope_gated_admit(CWD, "B", ["modules/y.py"], registry=reg,
                                  now=NOW, gather_fn=_gather(_hot("A")))
        if v.verdict == "refuse" and any(
                "non-overlap cannot be proven" in r for r in v.reasons):
            _ok("V-PM02-UNKNOWNSCOPE-REFUSED",
                "undeclared incumbent blocks a declared pane (disjoint unprovable)")
        else:
            _fail("V-PM02-UNKNOWNSCOPE-REFUSED",
                  f"expected refuse-unknown, got {v.verdict}: {v.reasons}")

    # V-SCHEDULER-FAILSAFE: undeclared pane -> blunt SAME_REPO_CAP=1 intact.
    with tempfile.TemporaryDirectory() as td:
        reg = PM2.PaneIntentRegistry(state_dir=td)
        v = PM2.scope_gated_admit(CWD, "C", None, registry=reg, now=NOW,
                                  gather_fn=_gather(_hot("A")))
        if v.verdict == "refuse" and any("blunt cap" in r for r in v.reasons):
            _ok("V-SCHEDULER-FAILSAFE",
                "undeclared same-repo pane hits the sealed blunt cap")
        else:
            _fail("V-SCHEDULER-FAILSAFE",
                  f"expected blunt-cap refuse, got {v.verdict}: {v.reasons}")

    # V-PM02-REGISTRY-ROUNDTRIP: declared intent reads back fresh; expires past
    # the freshness window.
    with tempfile.TemporaryDirectory() as td:
        reg = PM2.PaneIntentRegistry(state_dir=td)
        reg.declare("A", CWD, ["a.py"], now=NOW)
        fresh = reg.active(CWD, now=NOW)
        stale = reg.active(CWD, now=NOW + timedelta(minutes=200))
        if len(fresh) == 1 and fresh[0].sid == "A" and not stale:
            _ok("V-PM02-REGISTRY-ROUNDTRIP",
                "intent persisted+read fresh; expired beyond the 120min window")
        else:
            _fail("V-PM02-REGISTRY-ROUNDTRIP",
                  f"fresh={[i.sid for i in fresh]} stale={[i.sid for i in stale]}")

    # V-BASELINE-INTACT: decide(declared=None) reproduces sealed CO-08 behavior.
    v0 = S.decide(_hot("A"), CWD, is_new=True)   # 1 same-repo, undeclared
    v1 = S.decide([], CWD, is_new=True)          # empty
    if v0.verdict == "refuse" and v1.verdict == "proceed":
        _ok("V-BASELINE-INTACT",
            "decide(declared=None) unchanged: 1-incumbent refuse / empty proceed")
    else:
        _fail("V-BASELINE-INTACT",
              f"sealed behavior drifted: {v0.verdict}/{v1.verdict}")

    total = _p + _f
    print(f"PARALLEL_MESH_PASS={_p}/{total}  threshold={total}/{total}")
    return 0 if _f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
