#!/usr/bin/env python3
"""Resident health: COMPUTED from facts, never asserted.

The one rule that matters: HEALTHY requires information gain inside the window.
A loop that is alive, cycling and dispatching, with nothing in the engine's view
of any goal moving, is STALLED -- that is the failure this exists to name, and
"the process is up" is exactly the reading that hides it.

Precedence is fixed and written down: a more specific trouble always outranks a
more comfortable reading.
"""
from __future__ import annotations

from dataclasses import dataclass, field

HEALTHY = "HEALTHY"
IDLE_NO_APPROVED_GOAL = "IDLE_NO_APPROVED_GOAL"
RUNNING = "RUNNING"
WAITING_FOR_PROVIDER = "WAITING_FOR_PROVIDER"
WAITING_FOR_EVIDENCE = "WAITING_FOR_EVIDENCE"
WAITING_FOR_AUTHORITY = "WAITING_FOR_AUTHORITY"
STALLED = "STALLED"
DEGRADED = "DEGRADED"
RECOVERING = "RECOVERING"
FAILED = "FAILED"

STATES = (HEALTHY, IDLE_NO_APPROVED_GOAL, RUNNING, WAITING_FOR_PROVIDER, WAITING_FOR_EVIDENCE,
          WAITING_FOR_AUTHORITY, STALLED, DEGRADED, RECOVERING, FAILED)


@dataclass
class HealthFacts:
    failed: str = ""                                    # an unhandled cycle error
    authority_refusal: str = ""                         # anchor / licence refusal text
    recovering: list = field(default_factory=list)      # unresolved UNCERTAIN missions
    stalled: list = field(default_factory=list)         # goal keys at K no-gain cycles
    degraded: list = field(default_factory=list)        # goals that could not be read
    admitted: int = 0
    running_missions: int = 0
    active: int = 0                                     # goals the engine moved this cycle
    waiting_provider: list = field(default_factory=list)
    waiting_evidence: list = field(default_factory=list)
    waiting_authority: list = field(default_factory=list)   # engine ESCALATE: a person decides
    last_gain_ts: float | None = None


def compute(facts: HealthFacts, now: float, window_s: float) -> tuple[str, str]:
    if facts.failed:
        return FAILED, facts.failed
    if facts.authority_refusal:
        return WAITING_FOR_AUTHORITY, facts.authority_refusal
    if facts.recovering:
        return RECOVERING, f"unresolved uncertain missions: {facts.recovering[:5]}"
    if facts.stalled:
        return STALLED, f"no information gain for K active cycles: {facts.stalled[:5]}"
    if facts.degraded:
        return DEGRADED, f"goals unreadable or refused on error: {facts.degraded[:5]}"
    if facts.admitted == 0:
        return IDLE_NO_APPROVED_GOAL, "no governed, autonomous, unpaused goal was admitted"
    gained = facts.last_gain_ts is not None and (now - facts.last_gain_ts) <= window_s
    if gained:
        return HEALTHY, f"information gain {now - facts.last_gain_ts:.0f}s ago (window {window_s:.0f}s)"
    if facts.running_missions or facts.active:
        return RUNNING, (f"{facts.running_missions} mission(s) in flight, {facts.active} goal(s) "
                         f"moved by the engine this cycle; no gain inside the {window_s:.0f}s "
                         "window yet (K no-gain active cycles make it STALLED)")
    if facts.waiting_provider:
        return WAITING_FOR_PROVIDER, f"needs a provider this resident may not dispatch: {facts.waiting_provider[:5]}"
    if facts.waiting_evidence:
        return WAITING_FOR_EVIDENCE, f"awaiting an independent judge: {facts.waiting_evidence[:5]}"
    if facts.waiting_authority:
        return WAITING_FOR_AUTHORITY, f"needs a Founder decision: {facts.waiting_authority[:5]}"
    return STALLED, f"admitted goals, nothing in flight and no gain inside {window_s:.0f}s"
