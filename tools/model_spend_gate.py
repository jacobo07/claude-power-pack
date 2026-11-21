#!/usr/bin/env python3
"""BAMR obligation 5: the account check for `claude -p` spend OUTSIDE the mission machinery.

The missions ask the account governor before every model-spending launch (gsd_mission.account_refusal). Seven
tools spawned `claude -p` with no check at all (named by the BAMR P2 review): asc_design_gate_run,
asc_inherit_run, agent_carrier_run, compound_unattended, ccn_bench, exp_successor_packet, agent_discovery_curve.
Each now calls `refusal(tool)` or `require(tool)` immediately before its spawn, after any dry-run or
deterministic branch (those spend nothing and stay allowed).

Same policy as the missions: the governor's verdict with action `arm` (a new autonomous spend), unknown quota
refuses, and a governor fault is unknown -- never an allowance (Owner decision 2026-11-20).

  refusal(tool) -> None when admitted, else the reason (for tools whose result already carries a status)
  require(tool) -> raises SpendRefused (for measurement runs, where a partial run must not be recorded)

Kill switch: CPP_MODEL_SPEND_ADMISSION=off. State dir: CPP_MODEL_SPEND_STATE_DIR (default the governor's own,
~/.claude/state); suites point it at an isolated directory so they never write the real governor ledger.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

SWITCH = "CPP_MODEL_SPEND_ADMISSION"
STATE_ENV = "CPP_MODEL_SPEND_STATE_DIR"
ACTION = "arm"


class SpendRefused(RuntimeError):
    """The account governor did not admit a `claude -p` spawn; nothing was spawned."""


def _off() -> bool:
    return str(os.environ.get(SWITCH) or "").strip().lower() in ("0", "off", "false")


def refusal(tool: str) -> str | None:
    if _off():
        return None
    try:
        import account_governor as ag
        code, verdict, why, _ = ag.check(os.environ.get(STATE_ENV) or ag.DEFAULT_STATE, ACTION)
    except Exception as exc:  # noqa: BLE001 -- a broken governor is an unknown quota, never an allowance
        return f"{tool}: account governor fault ({type(exc).__name__}: {exc}) -- quota unknown, model call refused"[:400]
    return None if code == 0 else f"{tool}: {verdict}: {why}"[:400]


def require(tool: str) -> None:
    why = refusal(tool)
    if why:
        raise SpendRefused(why)
