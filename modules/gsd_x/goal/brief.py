#!/usr/bin/env python3
"""Compile an epoch brief from DURABLE state, and from nothing else.

A fresh-context epoch has no memory of the conversation that created the goal,
and that is the point: if an executor needs the chat to know what it is doing,
the goal was never durable. So the brief is built only from the goal log and
what can be projected from its owners -- the Founder's own words, the current
revision, the open convergence gaps, what the last epochs actually produced,
and the boundaries the epoch may not cross.

Two things it deliberately does NOT carry:

  * a transcript, a summary of a session, or any narrative an executor wrote
    about itself. The previous epochs appear as RECEIPTS -- what changed, what
    a gate observed, what failed -- because an account of work is not evidence
    of it;
  * authority. The brief states the ceiling and the refusals, so an executor
    reading it cannot conclude it may write to production: v1 has no such path
    at all.
"""
from __future__ import annotations

from .contract import GoalState
from .convergence import Convergence, project_convergence
from .epoch import project_epochs

MAX_RECEIPT_LINES = 12


def compile_brief(state: GoalState, closure_blocking: list[str], scope_root: str,
                  task: str, authority: dict | None = None) -> str:
    """The text an epoch is given. Deterministic: same state, same brief."""
    cv: Convergence = project_convergence(state)
    eps = project_epochs(state)
    auth = dict(authority or state.authority or {})
    lines: list[str] = []
    a = lines.append

    a(f"# Goal {state.goal_id} @ revision {state.revision}")
    a("")
    a("## What the Founder asked for, verbatim")
    a(state.intent.strip() or "(no intent recorded -- this is a defect, stop and report it)")
    if state.acceptance:
        a("")
        a("## Acceptance criteria")
        for c in state.acceptance:
            a(f"- {c}")
    if state.constraints:
        a("")
        a("## Constraints")
        for c in state.constraints:
            a(f"- {c}")
    a("")
    a("## This epoch's task")
    a(task.strip())
    a("")
    a(f"## Where you work\n{scope_root}")
    if state.scope.get("paths"):
        a("Scope paths (a change outside them is out of this goal's scope):")
        for p in state.scope["paths"]:
            a(f"- {p}")

    a("")
    a("## What is still open")
    if closure_blocking:
        for b in closure_blocking[:MAX_RECEIPT_LINES]:
            a(f"- {b}")
    else:
        a("- nothing is blocking closure; do not invent work")

    open_obs = [o for o in cv.obligations.values() if o.disposition == "ACCEPTED"]
    if open_obs:
        a("")
        a("## Obligations you can move, and what would prove them")
        for o in open_obs[:MAX_RECEIPT_LINES]:
            a(f"- {o.identifier} ({o.plane}): {o.text} -- proven by: {o.done_gate}")

    ended = [e for e in eps.values() if e.state == "ended"]
    if ended:
        a("")
        a("## What previous epochs actually did (receipts, not accounts)")
        for e in ended[-MAX_RECEIPT_LINES:]:
            a(f"- {e.epoch_id} [{e.provider}] ended {e.outcome}; "
              f"hypothesis={e.hypothesis}; receipts={len(e.receipts)}")

    undisposed = [f for f in cv.failures.values() if not f["disposition"]]
    if undisposed:
        a("")
        a("## Failures nobody has dispositioned yet")
        for f in undisposed[:MAX_RECEIPT_LINES]:
            a(f"- {f['summary'][:160]}")

    a("")
    a("## Boundaries")
    a(f"- Authority ceiling: {auth.get('ceiling', 'local code behind a green scoped verifier')}")
    a("- You may NOT write to any production system, deploy, or touch a live server.")
    a("- You may NOT mark anything converged: a gate that ran is what proves an obligation.")
    a("- If you are blocked by something outside this repository, say so and stop; "
      "a blocked goal names its external condition.")
    a("- Report what you changed. Your own account of success is not evidence.")
    return "\n".join(lines)
