#!/usr/bin/env python3
"""The independent judge: re-run the pinned gates, or refuse to certify.

The component being changed cannot be its sole judge. A reconciler that reads
its own closure and writes CONVERGED has certified itself, and the phase-4 audit
named the sharper version of the problem: re-running a gate AT THE FINAL TREE
re-runs whatever the builder left there. A builder that weakened its own done
gate gets an honest re-run of a rigged gate, and tree-hash binding binds the rig.

So the judge is independent in three ways that can each be checked:

  * **It refuses to run inside an epoch.** Every provider stamps its child with
    an epoch marker; a judge invoked from one is the builder wearing a hat.
  * **It re-verifies the PINS.** Each obligation pinned its gate's files at
    acceptance. If any pinned file differs at the tree being judged, the gate
    that would run is not the gate that was accepted -- refused, with the file
    named, unless someone explicitly re-accepted it.
  * **It runs in a worktree it was given and checks that worktree IS the tree
    being judged.** Judging tree A while standing in tree B is the same class of
    error as a verdict that names no tree at all.

It answers PASS, REFUSED or UNJUDGEABLE. Those are different facts -- a gate
that failed, a pin that moved, and a judge that could not run need different
reactions, and collapsing them would let "we could not check" read as "we
checked and it is fine".
"""
from __future__ import annotations

import hashlib
import os
import shlex
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .contract import GoalState
from .convergence import SATISFIED, project_convergence
from .git_state import tree_id

PASS, REFUSED, UNJUDGEABLE = "PASS", "REFUSED", "UNJUDGEABLE"
EPOCH_ENV = "GSDX_GOAL_EPOCH"
DEFAULT_GATE_TIMEOUT_S = 900.0
JUDGED = "goal.judged"


@dataclass
class JudgeReceipt:
    verdict: str
    reason: str
    goal_id: str
    revision: str
    tree_hash: str
    gates: list = field(default_factory=list)
    ts: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def record(log, state: GoalState, receipt: JudgeReceipt, actor: str) -> None:
    """Bank a judge receipt on the goal log -- PASS, REFUSED or UNJUDGEABLE.

    Recording only the passes was the first version, and it made the
    reconciler's "the judge refused, escalate" branch unreachable: there was no
    refusal to read. A refusal is a fact about the goal and the most useful one
    there is, so all three verdicts are banked and the LATEST about a given tree
    is what counts.
    """
    log.append(state.last_seq + 1, JUDGED, receipt.to_dict(), actor)


def current(state: GoalState, tree_hash: str, revision: str) -> dict | None:
    """The judge's verdict ABOUT THIS tree and revision, if one was recorded.

    Not merely the latest receipt. A receipt taken against another tree says
    exactly as much about this one as a gate verdict from another tree does --
    nothing -- and returning it would either certify a goal on evidence about a
    state nobody is closing, or strand it on a refusal that has since been
    addressed.

    This reader is the reason CONVERGED is reachable at all. Until it existed
    the judge wrote receipts that nothing read, so the terminal state of the
    whole design could be produced only by a test that built the receipt by
    hand.
    """
    found = None
    for ev in state.events:
        if ev.type != JUDGED:
            continue
        d = ev.data or {}
        if d.get("tree_hash") == tree_hash and d.get("revision") == revision:
            found = dict(d)
    return found


def _argv(command: str) -> list[str]:
    """Split a done-gate command into argv on this host.

    `posix=False` is required so a Windows path's backslashes survive, and it
    KEEPS the quotes around a quoted path -- which then becomes an argv[0] that
    matches no file. Stripping the wrapping quotes per token is what makes
    `"C:\\...\\python.exe" gate.py` actually runnable, and without it every gate
    on this host reports UNJUDGEABLE.
    """
    out = []
    for tok in shlex.split(command, posix=False):
        if len(tok) >= 2 and tok[0] == tok[-1] and tok[0] in ("'", '"'):
            tok = tok[1:-1]
        out.append(tok)
    return out


def _refuse(kind: str, reason: str, st: GoalState, tree_hash: str,
            gates: list | None = None) -> JudgeReceipt:
    return JudgeReceipt(kind, reason, st.goal_id, st.revision, tree_hash, gates or [],
                        datetime.now(timezone.utc).isoformat())


def judge(state: GoalState, tree_hash: str, worktree: Path,
          scope_paths: list | None = None, timeout_s: float = DEFAULT_GATE_TIMEOUT_S,
          env: dict | None = None) -> JudgeReceipt:
    """Re-run every satisfied obligation's pinned gate in `worktree`."""
    environ = dict(os.environ if env is None else env)
    if environ.get(EPOCH_ENV):
        return _refuse(UNJUDGEABLE,
                       f"this process is an epoch ({EPOCH_ENV}={environ[EPOCH_ENV]}); "
                       "a builder cannot judge itself", state, tree_hash)
    worktree = Path(worktree)
    if not worktree.is_dir():
        return _refuse(UNJUDGEABLE, f"no worktree to judge in: {worktree}", state, tree_hash)
    actual = tree_id(worktree, scope_paths)
    if actual != tree_hash:
        return _refuse(UNJUDGEABLE,
                       f"this worktree is {actual}, not the tree being judged ({tree_hash})",
                       state, tree_hash)

    cv = project_convergence(state)
    satisfied = [o for o in cv.obligations.values() if o.disposition == SATISFIED]
    if not satisfied:
        # Nothing to re-run is not a pass. A goal with no proven obligation has
        # not been judged; it has been skipped.
        return _refuse(UNJUDGEABLE, "no satisfied obligation to re-run; nothing was judged",
                       state, tree_hash)

    results = []
    for o in satisfied:
        # 1. the gate that would run must BE the gate that was accepted
        moved = []
        for rel, digest in o.gate_pin:
            p = worktree / rel
            if not p.is_file():
                moved.append(f"{rel} (missing)")
            elif hashlib.sha256(p.read_bytes()).hexdigest() != digest:
                moved.append(rel)
        if moved:
            results.append({"obligation": o.identifier, "gate": o.done_gate,
                            "verdict": REFUSED,
                            "detail": f"pinned gate files differ at this tree: {moved}"})
            continue
        # 2. re-run it, here, now
        try:
            argv = _argv(o.done_gate)
            started = time.time()
            proc = subprocess.run(argv, cwd=str(worktree), capture_output=True, text=True,
                                  timeout=timeout_s,
                                  env={**environ, "PYTHONIOENCODING": "utf-8"})
            tail = (proc.stdout or "").strip().splitlines()
            results.append({"obligation": o.identifier, "gate": o.done_gate,
                            "verdict": PASS if proc.returncode == 0 else REFUSED,
                            "exit_status": proc.returncode,
                            "observed": tail[-1][:200] if tail else "",
                            "seconds": round(time.time() - started, 1)})
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            # The judge could not run this gate. That is about the judge, not
            # about the obligation, and it outranks any subject failure.
            results.append({"obligation": o.identifier, "gate": o.done_gate,
                            "verdict": UNJUDGEABLE,
                            "detail": f"{exc.__class__.__name__}: {exc}"})

    if any(r["verdict"] == UNJUDGEABLE for r in results):
        return _refuse(UNJUDGEABLE, "at least one gate could not be run; this run proves "
                                    "nothing about what it skipped", state, tree_hash, results)
    bad = [r for r in results if r["verdict"] == REFUSED]
    if bad:
        return _refuse(REFUSED, "; ".join(f"{r['obligation']}: "
                                          f"{r.get('detail') or 'exit ' + str(r.get('exit_status'))}"
                                          for r in bad), state, tree_hash, results)
    return JudgeReceipt(PASS, f"{len(results)} pinned gate(s) re-run and passed at {tree_hash}",
                        state.goal_id, state.revision, tree_hash, results,
                        datetime.now(timezone.utc).isoformat())
