#!/usr/bin/env python3
"""Does the convergence owner actually bound itself, and can it say why it stopped?

Phase III asked whether bounded self-prompting improves one-shot engineering and
who should own it. The answer to the second half was already in the repository:
modules/sleepless_qa/healer/orchestrator.py is a convergence loop with a retry
budget, a repository lock, iteration accounting, diff-delta tracking and
diminishing-return detection. Nothing new was built. `/loops` was not created.

So the question this suite asks is the one that was still open: does the
incumbent satisfy the convergence safety contract, or does it only look like it
does? The properties under test are bounded iteration and an OBSERVABLE stop
reason -- a loop that halts for a reason nobody can read is not distinguishable
from one that halted arbitrarily, and the run log is where an operator has to
reconstruct what happened hours later.

These are driven against the real orchestrator in a real temporary directory
with a real repository lock. The heal dispatcher is never reached, because
every scenario here terminates before the dispatch seam -- which is the point:
the termination paths are the subject.
"""

from __future__ import annotations

import ast
import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from modules.sleepless_qa.dumpers.base import ActionScript  # noqa: E402
from modules.sleepless_qa.healer.orchestrator import run  # noqa: E402

PASSES = 0
FAILS = 0

ORCHESTRATOR = _ROOT / "modules" / "sleepless_qa" / "healer" / "orchestrator.py"


def check(gate: str, cond: bool, evidence: str) -> None:
    global PASSES, FAILS
    if cond:
        PASSES += 1
        print(f"  OK   {gate}  {evidence}")
    else:
        FAILS += 1
        print(f"  FAIL {gate}  {evidence}")


def _probe(budget: int, runtime_class: str = "cli"):
    action = ActionScript(
        name="convergence-probe",
        runtime_class=runtime_class,
        description="drive a termination path",
        setup={},
        steps=[],
        expectations={},
    )
    return run(Path(tempfile.mkdtemp()), action, {},
               runtime_class=runtime_class, max_retry_budget=budget)


def _stop_reasons() -> tuple:
    """Enumerate every value the loop can record as its stop reason.

    Read structurally from the source rather than grepped: a text search finds
    the assignments it can spell, and the interesting one here is an f-string.
    """
    tree = ast.parse(ORCHESTRATOR.read_text(encoding="utf-8"))
    literals, dynamic = set(), 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "terminated"
                   for t in node.targets):
            continue
        v = node.value
        if isinstance(v, ast.Constant) and isinstance(v.value, str):
            literals.add(v.value)
        elif isinstance(v, ast.JoinedStr):
            dynamic += 1
        elif isinstance(v, ast.BoolOp):
            for operand in v.values:
                if isinstance(operand, ast.Constant) and isinstance(operand.value, str):
                    literals.add(operand.value)
    return literals, dynamic


def main() -> int:
    # --- the owner is the incumbent, not something this phase invented ------
    check("V-CONV-INCUMBENT-OWNER", ORCHESTRATOR.exists(),
          f"convergence owner is the existing {ORCHESTRATOR.relative_to(_ROOT).as_posix()}")
    check("V-CONV-NO-RIVAL-LOOP",
          not (_ROOT / "commands" / "loops.md").exists(),
          "no competing /loops surface was created alongside the incumbent")

    literals, dynamic = _stop_reasons()
    # Positive control: a parser that silently matched nothing would make every
    # assertion below vacuous, and an empty set passes a 'no empty reason' test.
    check("V-CONV-PARSE-CONTROL", len(literals) >= 5,
          f"structural pass found {len(literals)} literal stop reasons "
          f"+ {dynamic} composed at runtime")
    check("V-CONV-DIMINISHING-RETURNS", "fix_loop_stuck" in literals,
          "the loop detects two consecutive identical repairs and stops")
    check("V-CONV-BUDGET-STOP", "budget_exhausted" in literals,
          "iteration is accounted and exhausting it is a named stop")

    # --- every terminating run must be able to say why ---------------------
    # A stop reason that is the empty string reaches the run log and the
    # verdict json as an absent field. An operator reading it later cannot
    # distinguish "the loop was never entered" from "nobody recorded it", and
    # the accompanying verdict is UNCERTAIN, which reads as ambiguity about the
    # SUBJECT when the truth is that no attempt was ever made.
    zero = _probe(0)
    check("V-CONV-STOP-OBSERVABLE-ZERO",
          bool(zero.terminated_because.strip()),
          f"budget 0 -> attempts={zero.attempts}, "
          f"terminated_because={zero.terminated_because!r}")
    check("V-CONV-ZERO-NOT-A-SUBJECT-VERDICT",
          zero.terminated_because != "pass",
          "a loop that never ran never reports a passing subject")

    neg = _probe(-3)
    check("V-CONV-STOP-OBSERVABLE-NEGATIVE",
          bool(neg.terminated_because.strip()) and neg.attempts == 0,
          f"budget -3 -> attempts={neg.attempts}, "
          f"terminated_because={neg.terminated_because!r}")

    # A real attempt against a directory with nothing to drive: the loop must
    # enter, fail at the evidence boundary, and stop with a named reason inside
    # its budget rather than spinning.
    one = _probe(1)
    check("V-CONV-BOUNDED-ATTEMPTS", one.attempts <= 1,
          f"budget 1 -> attempts={one.attempts} (never exceeds its budget)")
    check("V-CONV-STOP-OBSERVABLE-REAL",
          bool(one.terminated_because.strip()),
          f"a real attempt stopped with {one.terminated_because!r}")

    # --- no permission escalation inside the loop (section 27) -------------
    src = ORCHESTRATOR.read_text(encoding="utf-8")
    check("V-CONV-NO-ESCALATION",
          not any(tok in src for tok in ("sudo ", "runas", "chmod 777")),
          "the loop acquires no privilege it was not started with")

    print(f"CONVERGENCE_PASS={PASSES}/{PASSES + FAILS}  "
          f"threshold={PASSES + FAILS}/{PASSES + FAILS}")
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
