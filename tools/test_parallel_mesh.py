#!/usr/bin/env python3
"""test_parallel_mesh.py -- Parallel Cognitive Mesh done-gates. Hermetic
(tmp state dirs, injected gather_fn, fixed clock), re-runnable. Grows one
sprint at a time.

Sprint 1 (PM-02): scope-gate recalibration of CO-08's blunt same-repo cap.
Sprint 2 (PM-03): shared findings bus + redundancy tax.
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
from modules.parallel_mesh import pm_03_bus as PM3     # noqa: E402

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
REPO = CWD
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


def sprint1():
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


def sprint2():
    print("[PM-03 -- shared findings bus + redundancy tax]")

    # V-PM03-REDUNDANCY-TAX: a bus hit reuses; reason_fn NEVER runs (0 tokens).
    with tempfile.TemporaryDirectory() as td:
        bus = PM3.FindingsBus(state_dir=td)
        bus.publish(REPO, "optimize loops in tua-x", "batch the io calls",
                    sid="A", now=NOW)
        tax = PM3.RedundancyTax(bus=bus)
        calls = []

        def _reason():
            calls.append(1)
            return "SHOULD-NOT-RUN"

        claim, reused, _ = tax.reason_or_reuse(
            REPO, "optimize loops in tua-x", _reason, sid="B", now=NOW)
        if reused and not calls and claim == "batch the io calls":
            _ok("V-PM03-REDUNDANCY-TAX",
                "bus hit reused A's finding; reason_fn never ran (0 new tokens)")
        else:
            _fail("V-PM03-REDUNDANCY-TAX",
                  f"reused={reused} calls={len(calls)} claim={claim!r}")

    # V-PM03-MISS-REASONS: a miss reasons once, publishes, then becomes a hit.
    with tempfile.TemporaryDirectory() as td:
        tax = PM3.RedundancyTax(bus=PM3.FindingsBus(state_dir=td))
        calls = []

        def _reason():
            calls.append(1)
            return "derived answer"

        claim, reused, _ = tax.reason_or_reuse(
            REPO, "fresh topic", _reason, sid="A", now=NOW)
        hit, _, _ = tax.consult(REPO, "fresh topic")
        if (not reused) and len(calls) == 1 and claim == "derived answer" and hit:
            _ok("V-PM03-MISS-REASONS",
                "miss reasoned once and published; a subsequent consult hits")
        else:
            _fail("V-PM03-MISS-REASONS",
                  f"reused={reused} calls={len(calls)} hit={hit} claim={claim!r}")

    # V-PM03-BUS-PERSISTS: a finding survives across bus instances (== sessions).
    with tempfile.TemporaryDirectory() as td:
        PM3.FindingsBus(state_dir=td).publish(REPO, "t", "c", sid="A", now=NOW)
        reloaded = PM3.FindingsBus(state_dir=td).load(REPO)  # new instance, same disk
        if len(reloaded) == 1 and reloaded[0].claim == "c":
            _ok("V-PM03-BUS-PERSISTS",
                "finding persisted on disk across bus instances (survives sessions)")
        else:
            _fail("V-PM03-BUS-PERSISTS",
                  f"reloaded={[f.claim for f in reloaded]}")

    # V-PM03-DEDUP: identical finding published twice -> stored once.
    with tempfile.TemporaryDirectory() as td:
        bus = PM3.FindingsBus(state_dir=td)
        bus.publish(REPO, "T", "same claim", sid="A", now=NOW)
        bus.publish(REPO, "T", "same claim", sid="B", now=NOW)
        n = len(bus.load(REPO))
        if n == 1:
            _ok("V-PM03-DEDUP",
                "identical finding published twice stored once (bus is not a log)")
        else:
            _fail("V-PM03-DEDUP", f"expected 1 stored, got {n}")

    # V-PM03-PUBLISH-ON-SESSION-END: Stop-hook publishes new findings; malformed
    # entries skipped.
    with tempfile.TemporaryDirectory() as td:
        n = PM3.publish_session_findings(REPO, [
            {"topic": "a", "claim": "c1"},
            {"topic": "b", "claim": "c2"},
            {"topic": "", "claim": "skip-me"},
        ], sid="A", now=NOW, state_dir=td)
        loaded = PM3.FindingsBus(state_dir=td).load(REPO)
        if n == 2 and len(loaded) == 2:
            _ok("V-PM03-PUBLISH-ON-SESSION-END",
                "Cross-Pane Commit published 2 findings; malformed entry skipped")
        else:
            _fail("V-PM03-PUBLISH-ON-SESSION-END",
                  f"published={n} loaded={len(loaded)}")


def main():
    sprint1()
    sprint2()
    total = _p + _f
    print(f"PARALLEL_MESH_PASS={_p}/{total}  threshold={total}/{total}")
    return 0 if _f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
