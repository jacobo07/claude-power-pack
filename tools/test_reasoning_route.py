#!/usr/bin/env python3
"""test_reasoning_route.py -- V-gates for CPCSC Tier-B B3 (reasoning-execution
axis, CO-03 x one_shot).

Verifies the composition that surfaces when an Owner-declared one_shot size
and CO-03's independently keyword-derived route disagree, and the model
resolution for the one escalation.py action that names one. The core
discipline under test: the check is purely advisory (never blocks or
mutates the frozen contract), fails open to an honest None on empty or
malformed input rather than a fabricated agreement, and only the
"escalate-to-opus" action resolves to a real model ID -- every other
action, including the Owner-decision STOP, resolves to None rather than a
guess.

  V-RR-ROUTE-AGREES          declared budget covers CO-03's derived route -> agrees=True
  V-RR-ROUTE-DIVERGES        MACRO-keyword description at size=S -> agrees=False, MACRO named
  V-RR-ROUTE-EMPTY           empty description -> None (honest absence)
  V-RR-MODEL-FOR-ESCALATE    "escalate-to-opus" -> CO-03's real MODEL_MACRO
  V-RR-MODEL-FOR-OTHER       proceed/retry-same-model/stop-and-escalate-to-Owner -> None
  V-RR-MODEL-FOR-UNKNOWN     an unrecognized action string -> None
  V-RR-FAIL-OPEN             malformed contract / malformed action never raise
  V-RR-COMPILER-INTEGRATION  compile_contract(cwd=...) prints [REASONING ROUTE] only on divergence
  V-RR-DETERMINISTIC         identical input -> identical output on re-run

Hermetic: pure functions plus one stderr capture via a fresh StringIO; no
global writes. V-<DOMAIN>-<NAME>; RR_VERDICT line for the done-gate grep.
"""
from __future__ import annotations

import contextlib
import io
import sys
import tempfile
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.one_shot import reasoning_route as RR  # noqa: E402
from modules.one_shot.compiler import compile_contract  # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS {gate}: {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {gate}: {diag}")


def test_route_agrees() -> None:
    # Arrange -- no keyword match -> CO-03 defaults to MICRO ($15), declared M ($15).
    c = compile_contract("add a new field to the config schema", "M")
    # Act
    rec = RR.recommend_route(c)
    # Assert
    if rec is not None and rec.agrees_with_declared_size and rec.route_class == "MICRO":
        _ok("V-RR-ROUTE-AGREES", f"MICRO@${rec.max_budget:.2f} covered by declared $15")
    else:
        _fail("V-RR-ROUTE-AGREES", f"expected agrees/MICRO, got {rec}")


def test_route_diverges() -> None:
    # Arrange -- MACRO keyword "architect" at declared size=S ($5); CO-03 derives $30.
    c = compile_contract("architect the system for the new module", "S")
    # Act
    rec = RR.recommend_route(c)
    # Assert -- 30 > 5*2, and the divergence names MACRO in its note.
    if (rec is not None and not rec.agrees_with_declared_size
            and rec.route_class == "MACRO" and "MACRO" in rec.note):
        _ok("V-RR-ROUTE-DIVERGES", f"declared $5 vs derived ${rec.max_budget:.2f} MACRO")
    else:
        _fail("V-RR-ROUTE-DIVERGES", f"expected diverges/MACRO, got {rec}")


def test_route_empty() -> None:
    # Arrange
    c = compile_contract("", "M")
    # Act
    rec = RR.recommend_route(c)
    # Assert
    if rec is None:
        _ok("V-RR-ROUTE-EMPTY", "empty description -> None, not a fabricated agreement")
    else:
        _fail("V-RR-ROUTE-EMPTY", f"expected None, got {rec}")


def test_model_for_escalate() -> None:
    # Arrange
    from modules.cost_collapse.router import MODEL_MACRO
    # Act
    model = RR.model_for_action("escalate-to-opus")
    # Assert
    if model == MODEL_MACRO:
        _ok("V-RR-MODEL-FOR-ESCALATE", f"escalate-to-opus -> {model}")
    else:
        _fail("V-RR-MODEL-FOR-ESCALATE", f"expected {MODEL_MACRO}, got {model}")


def test_model_for_other() -> None:
    # Arrange / Act
    vals = [RR.model_for_action(a) for a in
            ("proceed", "retry-same-model", "stop-and-escalate-to-Owner")]
    # Assert -- no action but escalate-to-opus names a model.
    if vals == [None, None, None]:
        _ok("V-RR-MODEL-FOR-OTHER", "proceed/retry/stop all resolve to None")
    else:
        _fail("V-RR-MODEL-FOR-OTHER", f"expected all None, got {vals}")


def test_model_for_unknown() -> None:
    # Arrange / Act
    v = RR.model_for_action("totally-unrecognized-action")
    # Assert
    if v is None:
        _ok("V-RR-MODEL-FOR-UNKNOWN", "unrecognized action -> None, never a guess")
    else:
        _fail("V-RR-MODEL-FOR-UNKNOWN", f"expected None, got {v}")


def test_fail_open() -> None:
    # Arrange / Act -- malformed contract and malformed action inputs.
    r1 = RR.recommend_route(None)
    r2 = RR.recommend_route("not a contract")
    r3 = RR.model_for_action(123)
    r4 = RR.model_for_action(None)
    # Assert -- none raised; all degrade to None.
    if r1 is None and r2 is None and r3 is None and r4 is None:
        _ok("V-RR-FAIL-OPEN", "malformed contract/action inputs never raise")
    else:
        _fail("V-RR-FAIL-OPEN", f"expected all None, got {r1}/{r2}/{r3}/{r4}")


def test_compiler_integration() -> None:
    # Arrange -- a divergent compile and an agreeing compile, both with cwd set
    # (the advisory is opt-in, matching the Spec Gate's own precedent).
    with tempfile.TemporaryDirectory() as d:
        cwd = Path(d)
        buf_diverge, buf_agree = io.StringIO(), io.StringIO()
        # Act
        with contextlib.redirect_stderr(buf_diverge):
            compile_contract("architect the system for the new module", "S", cwd=cwd)
        with contextlib.redirect_stderr(buf_agree):
            compile_contract("add a new field to the config schema", "M", cwd=cwd)
        # Assert
        diverge_out, agree_out = buf_diverge.getvalue(), buf_agree.getvalue()
        if "[REASONING ROUTE]" in diverge_out and "[REASONING ROUTE]" not in agree_out:
            _ok("V-RR-COMPILER-INTEGRATION",
                "warning fires on divergence only, silent when routes agree")
        else:
            _fail("V-RR-COMPILER-INTEGRATION",
                  f"diverge_out={diverge_out!r} agree_out={agree_out!r}")


def test_deterministic() -> None:
    # Arrange
    c = compile_contract("architect the system for the new module", "S")
    # Act -- two independent calls.
    r1, r2 = RR.recommend_route(c), RR.recommend_route(c)
    # Assert
    if r1 == r2 and r1 is not None:
        _ok("V-RR-DETERMINISTIC", f"identical output across runs: {r1}")
    else:
        _fail("V-RR-DETERMINISTIC", f"nondeterministic: {r1} != {r2}")


def main() -> int:
    print("== reasoning_route (CPCSC Tier-B B3, CO-03 x one_shot) ==")
    for t in (test_route_agrees, test_route_diverges, test_route_empty,
              test_model_for_escalate, test_model_for_other, test_model_for_unknown,
              test_fail_open, test_compiler_integration, test_deterministic):
        t()
    total = _passes + _fails
    print(f"\nRR_PASS={_passes}/{total}  threshold={total}/{total}")
    print(f"RR_VERDICT={'PASS' if _fails == 0 else 'FAIL'}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
