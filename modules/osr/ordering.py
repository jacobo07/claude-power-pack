#!/usr/bin/env python3
"""ordering.py -- OSR-L1: reaching a state does not witness the order that led there.

The law, stated once. A system can arrive at a correct-looking terminal state
while skipping, reordering or silently failing the contracts that were supposed
to produce it. The screen is right and the system is wrong, and every check that
looks at the terminal state agrees the system is fine.

The estate already holds the general form of this in two places -- Mistake #16
("compiles is not works") and Mistake #17 ("static verification does not prove
runtime works") -- and CLAE Part XXV gates production reality at four lifecycle
points. What none of them states is the ORDERING claim: that a reached terminal
state witnesses nothing about the sequence of prerequisite contracts, and that
an arrival check is therefore not an ordering check.

This module makes the law executable. Given the contracts a terminal state
requires and a trace of what actually happened, it answers whether the arrival
was earned. It does not guess the required sequence -- a required sequence that
the checker derives from the observed run is a checker grading itself, and it
would pass every run by construction.
"""
from __future__ import annotations

from typing import Any, Iterable, Sequence

SATISFIED = "SATISFIED"
MISSING_PREREQUISITE = "MISSING_PREREQUISITE"
OUT_OF_ORDER = "OUT_OF_ORDER"
AFTER_TERMINAL = "AFTER_TERMINAL"
TERMINAL_NOT_REACHED = "TERMINAL_NOT_REACHED"
UNMEASURED = "UNMEASURED"


def verify_ordering(
    required: Sequence[str],
    observed: Iterable[str],
    terminal: str | None = None,
) -> dict[str, Any]:
    """Verify that a declared prerequisite sequence was honoured.

    `required` is the DECLARED contract order -- it must come from a spec, a
    boot manifest or an architectural sequence contract, never from a previous
    run of the system under test.

    `terminal` names the state whose arrival is being questioned. Prerequisites
    satisfied only *after* it are reported as AFTER_TERMINAL, which is the exact
    shape of the failure this law exists to catch: the state was reached, and
    then the things that should have preceded it happened anyway.
    """
    steps = [s for s in observed]
    if not required:
        return _result(UNMEASURED, "no required sequence was declared", required, steps)
    if not steps:
        return _result(UNMEASURED, "no observed trace was supplied", required, steps)

    first_index: dict[str, int] = {}
    for idx, step in enumerate(steps):
        first_index.setdefault(step, idx)

    terminal_index = first_index.get(terminal) if terminal else None
    if terminal is not None and terminal_index is None:
        return _result(
            TERMINAL_NOT_REACHED,
            f"terminal state {terminal!r} never appears in the observed trace",
            required, steps,
        )

    missing = [c for c in required if c not in first_index]
    if missing:
        return _result(
            MISSING_PREREQUISITE,
            f"declared prerequisites never observed: {missing}",
            required, steps, missing=missing,
        )

    late = [c for c in required if terminal_index is not None and first_index[c] > terminal_index]
    if late:
        return _result(
            AFTER_TERMINAL,
            (
                f"terminal {terminal!r} was reached before {late} -- arrival did not "
                "witness the prerequisite contracts"
            ),
            required, steps, after_terminal=late, terminal_index=terminal_index,
        )

    observed_positions = [first_index[c] for c in required]
    inversions = [
        {"expected_before": required[i], "observed_after": required[i + 1]}
        for i in range(len(required) - 1)
        if observed_positions[i] > observed_positions[i + 1]
    ]
    if inversions:
        return _result(
            OUT_OF_ORDER,
            "declared order was violated",
            required, steps, inversions=inversions,
        )

    return _result(
        SATISFIED,
        "every declared prerequisite occurred, in order, before the terminal state",
        required, steps, terminal_index=terminal_index,
    )


def gate(result: dict[str, Any]) -> bool:
    """True only on SATISFIED.

    UNMEASURED is deliberately False. An ordering claim nobody measured is not a
    satisfied one, and a gate that treats absence of evidence as a pass is the
    defect this whole module was derived from.
    """
    return result.get("verdict") == SATISFIED


def _result(
    verdict: str,
    detail: str,
    required: Sequence[str],
    observed: Sequence[str],
    **extra: Any,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "law": "OSR-L1",
        "verdict": verdict,
        "detail": detail,
        "required": list(required),
        "observed_length": len(observed),
    }
    out.update(extra)
    return out
