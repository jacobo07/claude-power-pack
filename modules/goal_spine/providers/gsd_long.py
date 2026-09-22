#!/usr/bin/env python3
"""The /cpp-gsd-long worker provider -- PREPARE ONLY, by measurement.

This provider cannot start a run, and that is a property of the runtime rather
than a caution:

* `gsd_autorun_marker.py --write` REQUIRES `--session` (tools/gsd_autorun_marker.py:207).
  A marker belongs to an existing pane; a reconciler process has no session of
  its own to arm.
* Arming starts nothing anyway. It makes a run SURVIVE a compaction; the pane's
  own agent still has to invoke the command (`commands/cpp-gsd-long.md`, "Steps 1
  and 2 start nothing"). Measured in that same file: 4 of 9 markers were armed
  with no evidence a run ever began.
* The resume daemon presses Enter only after a compaction, and with no window for
  the project it types into whichever Cursor window has focus
  (`cpp-gsd-long.md`, "Limits that remain"). A marker written by the spine onto a
  live pane would therefore re-issue /gsd-autonomous inside unrelated work.

So the spine emits an INSTRUCTION and waits. A pane claims the epoch by id, runs
the command, and the epoch becomes STARTED only when that claimed session's own
transcript shows it (epoch.observe_worker_start).

`preflight` reports what would refuse the run BEFORE a human spends a pane on it,
using `/cpp-gsd-long`'s own view of GSD rather than a second opinion.
"""
from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path

from .. import epoch as ep_
from .. import goal as gl

_PP_ROOT = Path(__file__).resolve().parents[3]


def _long_run():
    spec = importlib.util.spec_from_file_location(
        "_gsd_long_run_for_provider", _PP_ROOT / "tools" / "gsd_long_run.py")
    if spec is None or spec.loader is None:      # pragma: no cover - defensive
        raise RuntimeError("cannot load tools/gsd_long_run.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@dataclass(frozen=True)
class Preflight:
    ok: bool
    findings: tuple[str, ...]

    def render(self) -> str:
        head = "preflight OK" if self.ok else "preflight WOULD REFUSE"
        return head + "".join(f"\n  - {f}" for f in self.findings)


def preflight(goal: gl.Goal) -> Preflight:
    """What GSD itself says about this root, before a pane is spent on it."""
    findings: list[str] = []
    root = Path(goal.root)
    if not (root / ".planning").is_dir():
        findings.append(".planning/ is absent: run /gsd-new-milestone IN this worktree "
                        "first, or mission freshness refuses to arm")
    try:
        status = _long_run().gsd_status(str(root))
    except Exception as exc:  # noqa: BLE001 -- a preflight never raises at its caller
        return Preflight(False, tuple(findings + [f"could not ask GSD: {exc.__class__.__name__}"]))
    # gsd_status' own vocabulary, read from the source rather than assumed:
    # OK | NO_PHASES | ALL_COMPLETE | UNAVAILABLE. UNAVAILABLE means we could not
    # ask and is never read as "0 phases" -- different facts, different fixes, and
    # only one of them is about the project (cpp-gsd-long.md's refusal table).
    outcome = status.get("outcome")
    reason = status.get("reason", "")
    if outcome == "UNAVAILABLE":
        findings.append(f"could not ask GSD (not the same as no phases): {reason}")
    elif outcome == "NO_PHASES":
        findings.append(f"GSD sees no phases here: {reason}")
    elif outcome == "ALL_COMPLETE":
        findings.append(f"GSD has nothing left to run here: {reason}; arming refuses "
                        "'nothing to run' -- this Goal needs its own milestone")
    return Preflight(not findings, tuple(findings))


def instruction(goal: gl.Goal, epoch: ep_.Epoch) -> str:
    """The exact steps a pane must take. Nothing here is executed by the spine."""
    pf = preflight(goal)
    return "\n".join([
        f"GOAL {goal.goal_id} rev {goal.revision} -- epoch {epoch.epoch_id}",
        f"obligations: {', '.join(epoch.scope)}",
        "",
        f"1. Open a Cursor window AT {goal.root} (the resume cwd must equal the session cwd).",
        f"2. Claim this epoch:  python -m modules.goal_spine.cli claim {epoch.epoch_id}",
        f"3. Run:  {epoch.command}",
        "",
        "The spine does not arm a resume marker and does not press Enter. If this run",
        "must survive a compaction, follow /cpp-gsd-long in THIS pane after claiming.",
        "",
        pf.render(),
    ])


def claim(epoch_id: str, session_id: str, *, lease_hours: float = 24.0) -> ep_.Epoch:
    """Called BY the worker pane, in the worker pane, with its own session id."""
    e = ep_.load(epoch_id)
    ep_.claim(e, session_id, lease_hours=lease_hours)
    return ep_.save(e, expected_version=e.version)


def observe(epoch_id: str) -> ep_.Epoch:
    """CLAIMED -> STARTED when the claimed session's transcript shows the command."""
    e = ep_.load(epoch_id)
    if ep_.observe_worker_start(e):
        e = ep_.save(e, expected_version=e.version)
    return e
