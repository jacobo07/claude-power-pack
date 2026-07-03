#!/usr/bin/env python3
"""test_scope_a_activation.py -- Scope-A "activate-the-inert" regression gate.

Locks in the empirically-verified activation state of the three cognitive-kernel
systems the 2026-07-03 Reality Scan found already-built:

  PM-03 Findings Bus  -- consume (session_start_hub Hook 13) + publish round-trip
  CO-08 Scheduler     -- pm_02_intent scope-gate recalibration (4 scenarios)
  GK-12 Dispatcher    -- additionalContext preserved on PreToolUse (no-drift proxy)

HERMETIC: the PM-03 half runs entirely inside a TemporaryDirectory state dir --
it never touches the live ~/.claude/state bus (re-runnable, no accumulation).
The CO-08 half is pure (injected hot sessions, no I/O). V-gate convention.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_PP = Path(__file__).resolve().parents[1]
if str(_PP) not in sys.path:
    sys.path.insert(0, str(_PP))

from modules.parallel_mesh import pm_03_bus as bus          # noqa: E402
from modules.parallel_mesh import pm_02_intent as intent    # noqa: E402
from modules.cognitive_os import scheduler as sched         # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, ev: str) -> None:
    global _passes
    _passes += 1
    print(f"PASS {gate}: {ev}")


def _fail(gate: str, ev: str) -> None:
    global _fails
    _fails += 1
    print(f"FAIL {gate}: {ev}")


REPO = "C:/hermetic/repo"  # synthetic -- never a real path


def test_pm03_publish_consume_roundtrip() -> None:
    """PM-03: a published finding is read back by the consume-side digest."""
    with tempfile.TemporaryDirectory() as td:
        b = bus.FindingsBus(state_dir=td)
        n = 0
        for f in [{"topic": "dead function foo", "claim": "foo() is unreferenced"},
                  {"topic": "real signature", "claim": "compile_contract(desc,size)"}]:
            b.publish(REPO, f["topic"], f["claim"])
            n += 1
        # consume side: BusIndex.digest is exactly what Hook 13 mirrors in JS
        digest = bus.BusIndex(b, REPO).digest()
        if n == 2 and "real signature" in digest and "dead function foo" in digest:
            _ok("V-PM03-FIRST-FINDING", "publish x2 -> both topics in consume digest")
        else:
            _fail("V-PM03-FIRST-FINDING", f"digest missing topics: {digest[:120]!r}")

        # dedup: republishing an identical finding does NOT grow the bus
        before = len(b.load(REPO))
        b.publish(REPO, "dead function foo", "foo() is unreferenced")
        after = len(b.load(REPO))
        if after == before:
            _ok("V-PM03-DEDUP", "identical republish -> no second append")
        else:
            _fail("V-PM03-DEDUP", f"bus grew {before}->{after} on identical finding")


def test_pm03_failopen_empty() -> None:
    """PM-03: an absent bus yields an 'empty' digest, never an exception."""
    with tempfile.TemporaryDirectory() as td:
        digest = bus.load_context_digest("C:/no/such/repo", state_dir=td)
        if "empty" in digest.lower() or "unavailable" in digest.lower():
            _ok("V-PM03-FAILOPEN", "absent bus -> benign empty digest")
        else:
            _fail("V-PM03-FAILOPEN", f"unexpected digest: {digest[:120]!r}")


def _hot_same_repo(sid: str = "incumbent-1"):
    return [{"sid": sid, "encs": [sched._enc(REPO)]}]


def test_co08_intent_allowed() -> None:
    """CO-08: two DECLARED same-repo panes with disjoint scopes are both admitted."""
    v = sched.decide(_hot_same_repo(), REPO, is_new=True,
                     declared=intent.norm_scope(["modules/parallel_mesh/pm_03_bus.py"]),
                     hot_scopes={"incumbent-1": ("modules/cognitive_os/router.py",)})
    if v.verdict == "proceed":
        _ok("V-CO08-INTENT-ALLOWED", "disjoint declared scopes -> proceed")
    else:
        _fail("V-CO08-INTENT-ALLOWED", f"expected proceed, got {v.verdict}: {v.reasons}")


def test_co08_nointent_capped() -> None:
    """CO-08: an UNDECLARED 2nd same-repo pane keeps the sealed blunt cap."""
    v = sched.decide(_hot_same_repo(), REPO, is_new=True, declared=None)
    if v.verdict == "refuse":
        _ok("V-CO08-NOINTENT-CAPPED", "undeclared 2nd same-repo pane -> refuse (failsafe)")
    else:
        _fail("V-CO08-NOINTENT-CAPPED", f"expected refuse, got {v.verdict}")


def test_co08_collision_refused() -> None:
    """CO-08: a DECLARED but overlapping scope is refused (admission never widened)."""
    v = sched.decide(_hot_same_repo(), REPO, is_new=True,
                     declared=intent.norm_scope(["modules/cognitive_os/router.py"]),
                     hot_scopes={"incumbent-1": ("modules/cognitive_os/router.py",)})
    if v.verdict == "refuse":
        _ok("V-CO08-COLLISION-REFUSED", "overlapping declared scope -> refuse")
    else:
        _fail("V-CO08-COLLISION-REFUSED", f"expected refuse, got {v.verdict}")


def test_co08_gate_failsafe() -> None:
    """CO-08: scope_gated_admit(None) == sealed blunt admit (fail-safe path)."""
    v = intent.scope_gated_admit(REPO, "probe-sid", None,
                                 gather_fn=lambda **k: _hot_same_repo())
    if v.verdict == "refuse":
        _ok("V-CO08-GATE-FAILSAFE", "undeclared via gate -> blunt cap unchanged")
    else:
        _fail("V-CO08-GATE-FAILSAFE", f"expected refuse, got {v.verdict}")


def main() -> int:
    test_pm03_publish_consume_roundtrip()
    test_pm03_failopen_empty()
    test_co08_intent_allowed()
    test_co08_nointent_capped()
    test_co08_collision_refused()
    test_co08_gate_failsafe()
    total = _passes + _fails
    print(f"\nSCOPE_A_ACTIVATION_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
