#!/usr/bin/env python3
"""The unattended driver: advance autonomous goals, under preconditions it checks.

The sweep is what makes a goal converge while nobody is watching, and it is
therefore the most dangerous component here: it dispatches work on a schedule,
with no human reading the output. Three properties keep that honest.

**It refuses to act until the guards that catch its mistakes are proven green.**
The phase-4 audit (GAP-11) caught the ordering: shipping the driver before the
judge and the chaos suite would let a goal spend real quota unattended while
the machinery that stops a self-certifying convergence does not yet exist. So
autonomy has a PRECONDITION RECORD -- the judge suite and the chaos suite,
green, at a named commit of this repository -- and a record for a different
commit is stale, not a licence. This is a check in code, not a note in a plan.

**It only does the cheap, reversible thing.** A gate epoch reads a tree and
exits; a work epoch spends the Owner's Codex account or starts a session. The
sweep dispatches gates, harvests what ended and resolves what crashed. Anything
that spends is left for a decision somebody makes deliberately, and is reported.

**It never blocks.** A five-minute schedule cannot wait on a twenty-minute
epoch: it starts it, records the handle and returns. The next sweep observes.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from ..mission import closure as mcl
from . import contract as gc
from . import convergence as cv
from . import epoch as ep
from . import git_state as gs
from . import log as gl
from . import reconcile as rc
from .providers.gate import GateProvider

# The suites whose green is the precondition for acting unattended.
REQUIRED_SUITES = ("test_gsd_x_goal_judge.py", "test_gsd_x_goal_chaos.py")
AUTONOMY_RECORD = "autonomy_gates.json"
AUTONOMOUS_EVENT = "goal.autonomous"


def state_dir() -> Path:
    override = os.environ.get("GSDX_GOALS_ROOT")
    base = Path(override) if override else Path.home() / ".claude" / "state" / "gsd-x" / "goals"
    return base.parent if base.name == "goals" else base


def record_path() -> Path:
    return state_dir() / AUTONOMY_RECORD


def record_gates(pp_root: Path, python: str | None = None) -> dict:
    """Run the required suites here, now, and record what they said."""
    python = python or sys.executable
    head = gs.head(pp_root)
    results = {}
    for suite in REQUIRED_SUITES:
        p = Path(pp_root) / "tools" / suite
        if not p.is_file():
            results[suite] = {"ok": False, "detail": "suite missing"}
            continue
        proc = subprocess.run([python, str(p)], cwd=str(pp_root), capture_output=True,
                              text=True, timeout=3600,
                              env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        tail = [ln for ln in (proc.stdout or "").splitlines() if "_PASS=" in ln]
        results[suite] = {"ok": proc.returncode == 0, "detail": tail[-1] if tail else
                          f"exit {proc.returncode}"}
    payload = {"head": head, "ts": datetime.now(timezone.utc).isoformat(),
               "suites": results,
               "green": all(r["ok"] for r in results.values())}
    path = record_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def autonomy_verdict(pp_root: Path) -> tuple[bool, str]:
    """May the sweep act unattended right now?"""
    path = record_path()
    if not path.is_file():
        return False, (f"no autonomy record at {path}: run `record-gates` -- the judge and "
                       "chaos suites must be green before anything runs unattended")
    try:
        rec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"the autonomy record is unreadable ({exc}); that is not permission"
    if not rec.get("green"):
        bad = [s for s, r in (rec.get("suites") or {}).items() if not r.get("ok")]
        return False, f"the autonomy record is not green: {bad}"
    head = gs.head(pp_root)
    if head and rec.get("head") and rec["head"] != head:
        return False, (f"the autonomy record is for {rec['head'][:8]}, this tree is "
                       f"{head[:8]}: re-run `record-gates` on the code that would run")
    return True, f"judge and chaos suites green at {str(rec.get('head'))[:8]}"


def is_autonomous(state: gc.GoalState) -> bool:
    on = False
    for ev in state.events:
        if ev.type == AUTONOMOUS_EVENT:
            on = bool(ev.data.get("enabled"))
    return on


def set_autonomous(log: gl.GoalLog, state: gc.GoalState, enabled: bool, reason: str,
                   actor: str) -> None:
    log.append(state.last_seq + 1, AUTONOMOUS_EVENT,
               {"enabled": bool(enabled), "reason": reason}, actor)


@dataclass
class SweepReport:
    acted: list = field(default_factory=list)
    skipped: list = field(default_factory=list)
    refused: str = ""

    def render(self) -> str:
        if self.refused:
            return f"REFUSED: {self.refused}"
        if not self.acted:
            return ""            # silence when nothing happened, by design
        return "\n".join(self.acted)


def _apply_verdicts(log: gl.GoalLog, receipt, record, actor: str) -> list[str]:
    """Move an obligation on the verdict its gate produced -- or say why not.

    Ingesting a receipt banks WHAT HAPPENED; it does not decide what that means.
    Without this step a gate could run, pass, be banked, and leave its obligation
    ACCEPTED forever -- measured 2026-09-22, when the sweep did exactly that and
    then honestly reported that no justified action remained.

    The transition is still `convergence.evaluate`'s to refuse: a verdict from
    another tree or revision, an unpinned gate, or a non-runtime gate on a
    REALITY obligation is refused here exactly as it would be anywhere else.
    """
    out: list[str] = []
    ob_id = (record.spec or {}).get("obligation")
    if not ob_id:
        return out
    for v in receipt.verdicts or []:
        verdict = mcl.Verdict(v.get("gate", ""), int(v.get("exit_status", 1)),
                              v.get("observed", ""), v.get("tree_hash", ""),
                              v.get("revision", ""), v.get("gate_class", ""),
                              tuple(tuple(p) for p in (v.get("gate_pin") or ())))
        res = cv.satisfy(log, gc.project(log), ob_id, verdict, actor)
        out.append(f"{log.goal_id}: {ob_id} -> "
                   f"{'SATISFIED' if res.allowed else res.outcome}: {res.reason[:140]}")
    return out


def sweep_goal(log: gl.GoalLog, root: Path, providers=("gate",), run_dir: Path | None = None,
               dry_run: bool = False, actor: str = "sweep") -> list[str]:
    """One pass over one goal. Returns what it did (empty when it did nothing)."""
    from ..goal import judge as jd       # local: keeps the import graph shallow

    acted: list[str] = []
    state = gc.project(log)
    paths = state.scope.get("paths") or ["."]
    tree = gs.tree_id(root, paths)
    eps = ep.project_epochs(state)
    prov = GateProvider(Path(run_dir or (log.dir / "runs")))

    observations = {}
    for e in eps.values():
        if e.state == "running" and e.provider == "gate" and e.handle:
            observations[e.epoch_id] = prov.observe(e.handle)

    # The engine's own identity is part of the retry key: when the orchestrator
    # is what failed an attempt, retrying against fixed code is new information
    # rather than the same attempt again.
    engine = gs.head(Path(__file__).resolve().parents[3])
    d = rc.decide(rc.Context(state=state, tree_hash=tree,
                             scope_hash=ep.scope_hash(root, paths),
                             observations=observations, now=time.time(),
                             budget=state.budget, providers=tuple(providers),
                             # The receipt the judge banked, about THIS tree.
                             # Unread, the sweep reports READY_FOR_JUDGE forever
                             # at a goal an independent judge has already passed.
                             judge=jd.current(state, tree, state.revision),
                             engine=engine))
    if d.kind == rc.RECOVER:
        if not dry_run:
            out = ep.recover(log, state, prov, d.epoch_id, actor)
            acted.append(f"{log.goal_id}: recovered {d.epoch_id} -> {out}")
        else:
            acted.append(f"{log.goal_id}: would recover {d.epoch_id}")
    elif d.kind == rc.HARVEST:
        e = eps[d.epoch_id]
        if not dry_run:
            spec = {"epoch_id": e.epoch_id, "revision": state.revision, "root": str(root),
                    "scope_paths": paths,
                    "gate": e.spec.get("gate") or {"id": e.spec.get("obligation", "gate"),
                                                   "command": [], "class": "unit",
                                                   "files": []}}
            obs = observations.get(e.epoch_id)
            try:
                receipt = prov.harvest(e.handle or {}, spec)
                ep.ingest_receipt(log, gc.project(log), receipt, actor)
                acted.extend(_apply_verdicts(log, receipt, e, actor))
            except (ep.EpochError, KeyError) as exc:
                acted.append(f"{log.goal_id}: {e.epoch_id} harvest refused: {exc}")
            ep.end(log, gc.project(log), e.epoch_id,
                   (obs.outcome if obs else ep.LOST) or ep.LOST,
                   obs.detail if obs else "unobservable", actor)
            acted.append(f"{log.goal_id}: harvested {e.epoch_id} "
                         f"({obs.outcome if obs else 'lost'})")
        else:
            acted.append(f"{log.goal_id}: would harvest {d.epoch_id}")
    elif d.kind == rc.NEXT_EPOCH and d.provider == "gate":
        o = cv.project_convergence(state).obligations[d.spec["obligation"]]
        if dry_run:
            acted.append(f"{log.goal_id}: would run {o.identifier}'s gate")
        elif o.plane in cv.REALITY_PLANES and o.gate_class not in cv.RUNTIME_GATE_CLASSES:
            # Refuse rather than guess. This branch used to read
            # `"in_game" if o.plane == cv.REALITY else "unit"`, which derived the
            # class from the very plane `goal_closure` then checked it against --
            # so the reality check could not fail, and a unit test named as a
            # REALITY obligation's done gate would have satisfied a production
            # claim. An obligation accepted before that was fixed carries no
            # class; it needs re-accepting with one declared, not a guess here.
            acted.append(f"{log.goal_id}: {o.identifier} declares no runtime gate class "
                         f"({o.gate_class or 'nothing'}); a {o.plane} obligation is not "
                         "dispatched on an inferred one")
        else:
            gate = {"id": o.identifier, "command": jd._argv(o.done_gate),
                    "class": o.gate_class or "unit",
                    "files": [rel for rel, _ in o.gate_pin],
                    # the verdict is pinned in its obligation's scheme, or the
                    # exact pin comparison in convergence refuses it (UWCP S1-9)
                    "pin_scheme": gs.pin_scheme(o.gate_pin)}
            # The gate spec is STORED on the epoch, never rebuilt at harvest.
            # Measured 2026-09-22 on the first real goal: harvest rebuilt it from
            # an epoch record that never carried it, so every gate RAN, produced
            # an exit status nobody read, and its epoch ended `lost`. The work
            # happened and the evidence was dropped -- after which the goal
            # honestly reported that no justified action remained, which was the
            # right answer to a question the sweep had made unanswerable.
            e = ep.begin(log, state, "gate",
                         {"obligation": o.identifier, "tree_hash": tree, "gate": gate},
                         d.info_key, d.hypothesis, actor)
            spec = {"epoch_id": e.epoch_id, "revision": state.revision, "root": str(root),
                    "identity": e.identity, "scope_paths": paths, "gate": gate}
            # Non-blocking: a five-minute schedule starts the gate and returns.
            handle = prov.dispatch(spec)
            ep.mark_running(log, gc.project(log), e.epoch_id, handle, actor)
            acted.append(f"{log.goal_id}: dispatched {e.epoch_id} for {o.identifier}")
    elif d.kind in (rc.NEXT_EPOCH, rc.ESCALATE, rc.READY_FOR_JUDGE, rc.BLOCKED):
        # Everything that spends an account, needs a person, or certifies a goal
        # is REPORTED and left alone. The sweep is not an authority.
        via = f" (needs provider {d.provider})" if d.provider else ""
        acted.append(f"{log.goal_id}: {d.kind}{via} -- {d.reason[:160]}")
    return acted


def sweep(pp_root: Path, goals: list[tuple[gl.GoalLog, Path]], dry_run: bool = False,
          actor: str = "sweep") -> SweepReport:
    report = SweepReport()
    allowed, why = autonomy_verdict(pp_root)
    if not allowed:
        report.refused = why
        return report
    for log, root in goals:
        try:
            state = gc.project(log)
        except gl.GoalLogError as exc:
            report.skipped.append(f"{log.goal_id}: {exc}")
            continue
        if not is_autonomous(state):
            report.skipped.append(f"{log.goal_id}: not marked autonomous")
            continue
        try:
            report.acted.extend(sweep_goal(log, root, dry_run=dry_run, actor=actor))
        except (gl.GoalLogError, OSError) as exc:
            report.skipped.append(f"{log.goal_id}: {exc.__class__.__name__}: {exc}")
    return report
