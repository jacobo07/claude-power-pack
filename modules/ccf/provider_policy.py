"""Structured creative provider policy (BCAP2-07 / BI-13).

Pure decisions, no provider calls. (1) `route` picks deterministic/vector construction unless the
intent is shown to need an image model. (2) `plan_call` bounds a provider call: a tool-use budget,
a declared fallback model, and mandatory cost/latency/token tracking fields. (3) `REFUSED_IMPORTS`
names what is not absorbed from the evaluated sources (parallel orchestration, memories, unverified
claims). Unknown cost is recorded as None, never 0.
"""
from __future__ import annotations

REFUSED_IMPORTS = ("parallel_orchestration", "agent_memories", "unverified_claims")
MAX_TOOL_CALLS = 4
TRACKED = ("tokens_in", "tokens_out", "cost_usd", "latency_ms")


def route(intent: dict) -> dict:
    """intent: {deterministic_possible: bool|None, needs: [str]}. None = unmeasured -> deterministic first,
    flagged, because a missing answer is not permission to spend on an image model."""
    det = intent.get("deterministic_possible")
    if det is True:
        return {"route": "DETERMINISTIC_VECTOR", "reason": "construction can meet intent"}
    if det is False and intent.get("needs"):
        return {"route": "IMAGE_MODEL", "reason": "deterministic construction cannot meet: " + ", ".join(intent["needs"])}
    return {"route": "DETERMINISTIC_VECTOR", "reason": "unmeasured or unjustified; image model needs a stated need", "flag": "UNMEASURED"}


def plan_call(model: str, fallback_model, tool_calls: int, requested_imports=()) -> dict:
    """Return {ok, problems, tracking}. A call without a fallback, over the tool budget, or importing a
    refused capability is not ok."""
    p = [f"refused import {i!r}" for i in requested_imports if i in REFUSED_IMPORTS]
    if not fallback_model or fallback_model == model:
        p.append("a distinct fallback model must be declared")
    if tool_calls > MAX_TOOL_CALLS:
        p.append(f"tool_calls {tool_calls} exceeds bound {MAX_TOOL_CALLS}")
    return {"ok": not p, "problems": p, "tracking": {k: None for k in TRACKED}}
