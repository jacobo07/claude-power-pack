#!/usr/bin/env python3
"""auto_reset_orchestrator.py - the brain of the Auto-Reset Orchestrator (M3).

Composes context_monitor (M1) + work_state_saver (M2). Given a session's
cwd + session_id:

  1. assess context pressure (M1 -> HEALTHY / COMPACT_NEEDED / KCLEAR_NEEDED).
  2. HEALTHY                  -> action 'none', no advisory.
  3. COMPACT_NEEDED           -> save work_state (M2) + a /compact advisory
                                 whose message embeds the saved state so the
                                 compacted session continues without friction.
  4. KCLEAR_NEEDED            -> save work_state + a /kclear advisory carrying
                                 the exact `claude --resume <sid>` line.

CANNOT force slash commands (BL-0003: a hook cannot auto-fire /compact or
/kclear). The orchestrator's job is the three things it CAN do: save exact
state, emit an urgent advisory the model surfaces, and make the resume
frictionless (M5 reads the saved work_state on the next SessionStart). The
model emitting the pre-filled slash line is its contribution to the chain
(same contract as the existing BL-0033 context-watchdog).

orchestrate(cwd, session_id, state_dir=None, assess_fn=None) -> dict
  { state, action, advisory, work_state_path, work_state, resume_hint }

assess_fn is injectable so tests force a state without a live RAM reading.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]

# Map M1 states -> orchestrator action.
_ACTION = {
    "HEALTHY": "none",
    "COMPACT_NEEDED": "compact",
    "KCLEAR_NEEDED": "kclear",
}


def _fmt_pending(pending) -> str:
    if not pending:
        return "(none)"
    items = list(pending)[:5]
    more = f" (+{len(pending) - 5} more)" if len(pending) > 5 else ""
    return "; ".join(items) + more


def build_advisory(state: str, work_state: dict, tripped=None) -> str:
    """Pure message builder -- the unit-testable core. Embeds the saved
    work_state so the resumed session continues without friction."""
    task = work_state.get("task") or "(unknown task)"
    commit = work_state.get("last_commit") or "(none)"
    last_file = work_state.get("last_file") or "(none)"
    pending = _fmt_pending(work_state.get("pending"))
    sid = work_state.get("session_id") or ""
    why = (", ".join(tripped) if tripped else "threshold crossed")
    short_task = task[:60]

    head = (f"AUTO-RESET [{state}] — context pressure: {why}. "
            f"Work-state SAVED (task + last commit + pending). "
            f"Task: {task}. Last commit: {commit}. Last file: {last_file}. "
            f"Pending: {pending}. ")

    if state == "KCLEAR_NEEDED":
        resume = f"claude --resume {sid}" if sid else "claude --resume"
        tail = (
            f"This is SEVERE pressure — a hard reset reclaims the most RAM. "
            f"End your next response with a SINGLE trailing line — exactly "
            f"`/kclear` — to checkpoint + reset. On the next session start the "
            f"saved work-state is injected automatically (no Owner action). "
            f"Exact resume if needed: {resume}. Per BL-0003 the hook cannot "
            f"auto-dispatch the slash command; emitting the line is your part."
        )
    else:  # COMPACT_NEEDED
        tail = (
            f"End your next response with a SINGLE trailing line — exactly "
            f"`/compact focus on {short_task}` — no preface, no markdown. The "
            f"saved work-state will be re-injected on resume so you continue "
            f"exactly here. Per BL-0003 the hook cannot auto-dispatch; emitting "
            f"the line is your part of the chain."
        )
    return head + tail


def orchestrate(cwd: str | None = None, session_id: str | None = None,
                state_dir=None, assess_fn=None,
                save_fn=None) -> dict:
    """Decide + (on pressure) save work_state + build advisory. Pure of any
    Stop-schema concern -- M4 maps the result onto the hook contract.

    assess_fn(cwd, session_id) -> M1 decision dict   (injectable for tests)
    save_fn(cwd, session_id, task, pending, state_dir) -> record (injectable)
    """
    cwd = cwd or os.getcwd()

    if assess_fn is None:
        sys.path.insert(0, str(_PP_ROOT))
        from modules.cpc_os.context_monitor import assess as assess_fn  # type: ignore
    if save_fn is None:
        sys.path.insert(0, str(_PP_ROOT))
        from modules.cpc_os.work_state_saver import save_work_state as save_fn  # type: ignore

    decision = assess_fn(cwd, session_id)
    state = decision.get("state", "HEALTHY")
    action = _ACTION.get(state, "none")

    if action == "none":
        return {
            "state": state, "action": "none", "advisory": None,
            "work_state_path": None, "work_state": None,
            "resume_hint": None, "signals": decision.get("signals"),
        }

    # Pressure -> save the exact work-state FIRST (save then free, BL-0033).
    work_state = save_fn(cwd, session_id=session_id, state_dir=state_dir)
    advisory = build_advisory(state, work_state, tripped=decision.get("tripped"))
    sid = work_state.get("session_id") or ""
    resume_hint = (f"claude --resume {sid}" if sid and action == "kclear"
                   else None)
    return {
        "state": state, "action": action, "advisory": advisory,
        "work_state_path": work_state.get("_path"),
        "work_state": work_state,
        "resume_hint": resume_hint,
        "signals": decision.get("signals"),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--cwd", default=None)
    ap.add_argument("--session-id", default=None)
    args = ap.parse_args(argv)
    result = orchestrate(cwd=args.cwd, session_id=args.session_id)
    if args.json:
        print(json.dumps(result))
    else:
        print(f"{result['state']} -> action={result['action']}")
        if result["advisory"]:
            print(result["advisory"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
