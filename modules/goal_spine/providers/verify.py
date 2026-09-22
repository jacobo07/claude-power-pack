#!/usr/bin/env python3
"""The verify provider -- the spine's only fully autonomous executor.

It runs the gate an obligation NAMES and returns a receipt. It never decides
what the gate means beyond the interpreter the project registered with it, and
it never marks anything satisfied: the receipt goes through `receipt.ingest`,
which goes through GSD X `closure.satisfy`.

GATES ARE REGISTERED BY THE PROJECT. The spine is generic; a project adapter
(for KobiiCraft, `tools/ksis/kseip/goal/reality_oracle.py`) registers each gate
id with the command that runs it and an interpreter that turns its output into
(exit_status, observed). The reconciler only offers `verify` for gates present in
the registry, so an unregistered gate can never be "verified" by accident.

A GATE THAT COULD NOT JUDGE NEVER READS AS A GATE THAT PASSED. A timeout, a
missing executable or an interpreter that raises produce a non-zero verdict with
a distinct `observed` text, so closure refuses it and the reason says which of
the three happened.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .. import convergence as cv
from .. import epoch as ep_
from .. import goal as gl
from .. import receipt as rc
from .. import store as gs

TIMEOUT_STATUS = 124
UNRUNNABLE_STATUS = 127
UNINTERPRETABLE_STATUS = 125

Interpreter = Callable[[int, str], "tuple[int, str]"]


def rc_interpreter(returncode: int, output: str) -> tuple[int, str]:
    """Default: the process exit code is the verdict; the tail is the observation."""
    tail = " | ".join(line.strip() for line in output.strip().splitlines()[-3:])
    return returncode, tail or f"exit {returncode}, no output"


@dataclass(frozen=True)
class Gate:
    gate_id: str
    command: tuple[str, ...]
    cwd: str
    timeout_s: int = 600
    interpret: Interpreter = field(default=rc_interpreter)


class Registry:
    def __init__(self) -> None:
        self._gates: dict[str, Gate] = {}

    def register(self, gate: Gate) -> None:
        if gate.gate_id in self._gates and self._gates[gate.gate_id] != gate:
            raise ValueError(f"gate {gate.gate_id!r} is already registered differently")
        self._gates[gate.gate_id] = gate

    def ids(self) -> frozenset[str]:
        return frozenset(self._gates)

    def get(self, gate_id: str) -> Gate:
        return self._gates[gate_id]


def run_gate(gate: Gate) -> tuple[int, str]:
    try:
        proc = subprocess.run(list(gate.command), cwd=gate.cwd, capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=gate.timeout_s)
    except subprocess.TimeoutExpired:
        return TIMEOUT_STATUS, f"TIMEOUT after {gate.timeout_s}s -- the gate could not judge"
    except OSError as exc:
        return UNRUNNABLE_STATUS, f"UNRUNNABLE -- {exc.__class__.__name__}: {exc}"
    try:
        status, observed = gate.interpret(proc.returncode, (proc.stdout or "") + (proc.stderr or ""))
    except Exception as exc:  # noqa: BLE001 -- any interpreter failure is "could not judge"
        return UNINTERPRETABLE_STATUS, f"UNINTERPRETABLE -- {exc.__class__.__name__}: {exc}"
    return int(status), str(observed)


def execute(epoch_id: str, registry: Registry) -> rc.IngestResult:
    """Run one DISPATCHed verify epoch end to end: start, run, receipt, ingest, end."""
    e = ep_.load(epoch_id)
    if e.provider != "verify":
        raise PermissionError(f"{epoch_id} belongs to {e.provider}, not verify")
    goal = gs.load(e.goal_id)
    if len(e.scope) != 1:
        raise ValueError("a verify epoch checks exactly one obligation")
    oid = e.scope[0]
    target = next((o for o in cv.load_obligations(goal) if o.identifier == oid), None)
    if target is None:
        raise LookupError(f"{oid} is not in {goal.goal_id}'s obligation store")

    ep_.mark_started_autonomous(e)
    e = ep_.save(e, expected_version=e.version)
    if target.done_gate in registry.ids():
        status, observed = run_gate(registry.get(target.done_gate))
    else:
        status, observed = UNRUNNABLE_STATUS, f"UNRUNNABLE -- gate {target.done_gate!r} is not registered"
    result = rc.ingest(goal, rc.Receipt(
        epoch_id=e.epoch_id, goal_id=goal.goal_id, goal_revision=e.goal_revision,
        obligation_id=oid, provider="verify", gate=target.done_gate,
        exit_status=status, observed=observed))
    e = ep_.load(e.epoch_id)
    ep_.end(e, ep_.COMPLETED, f"{target.done_gate} -> {status}: {observed[:160]} [{result.outcome}]")
    ep_.save(e, expected_version=e.version)
    return result
