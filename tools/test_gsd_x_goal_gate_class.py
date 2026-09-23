#!/usr/bin/env python3
"""V-gates for the DECLARED gate class.

The defect these pin, measured 2026-09-23: `sweep` built a gate spec as
`{"class": "in_game" if o.plane == cv.REALITY else "unit"}`, deriving the class
from the plane. `goal_closure` then refused a REALITY obligation whose
`verdict.gate_class` was not a runtime one -- reading back the class the plane
had just implied. The refusing branch was therefore unreachable on the
unattended path, and a unit test named as a REALITY obligation's done gate would
have satisfied a production-reality claim with a green that meant nothing.

The class is now DECLARED at acceptance. That is what makes the reality check
falsifiable: a person supplies the class, so a wrong one is expressible and the
refusal can actually fire.

Both poles are driven. Every refusal has a paired control that must be ADMITTED,
because a guard that refuses everything passes every refusal assertion.

    python tools/test_gsd_x_goal_gate_class.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.gsd_x.goal import contract as gc       # noqa: E402
from modules.gsd_x.goal import convergence as cv    # noqa: E402
from modules.gsd_x.goal import git_state as gs      # noqa: E402
from modules.gsd_x.goal import log as gl            # noqa: E402
from modules.gsd_x.goal import sweep as sw          # noqa: E402

GIT = r"C:\Program Files\Git\cmd\git.exe"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
       "PYTHONIOENCODING": "utf-8"}
REPO_ID = "7c" * 20

passes: list[str] = []
fails: list[str] = []


def _ok(gate: str, evidence: str) -> None:
    passes.append(gate)
    print(f"  PASS {gate}: {evidence}")


def _fail(gate: str, detail: str) -> None:
    fails.append(gate)
    print(f"  FAIL {gate}: {detail}")


def check(gate: str, cond: bool, ok: str, bad: str) -> None:
    _ok(gate, ok) if cond else _fail(gate, bad)


def make_repo() -> Path:
    d = Path(tempfile.mkdtemp(prefix="gsdx_gateclass_repo_"))
    subprocess.run([GIT, "init", "-q", str(d)], check=True, env=ENV)
    (d / "gate.py").write_text("import sys\nprint('1 passed')\nsys.exit(0)\n",
                               encoding="utf-8")
    subprocess.run([GIT, "-C", str(d), "add", "."], check=True, env=ENV)
    subprocess.run([GIT, "-C", str(d), "commit", "-qm", "seed"], check=True, env=ENV)
    return d


def make_goal(base: Path, gid: str) -> gl.GoalLog:
    lg = gl.GoalLog(REPO_ID, gid, base=base)
    gc.declare(lg, f"gate class {gid}", ["a player sees it"], [], {"paths": ["."]})
    for plane in cv.PLANES:
        applicable = plane in cv.ALWAYS or plane in cv.REALITY_PLANES
        cv.set_plane(lg, gc.project(lg), plane, applicable,
                     "" if applicable else "not claimed", "t")
    return lg


def raises(fn) -> str | None:
    """Return the error text, or None if the call was ADMITTED."""
    try:
        fn()
    except gl.GoalLogError as exc:
        return str(exc)
    return None


def main() -> int:
    repo = make_repo()
    pin = gs.file_pin(repo, ["gate.py"])
    cmd = f'"{sys.executable}" gate.py'

    # --- acceptance: the refusals, each with its admitted control -----------
    base = Path(tempfile.mkdtemp(prefix="gsdx_gateclass_"))
    lg = make_goal(base, "g-accept")

    err = raises(lambda: cv.accept_obligation(
        lg, gc.project(lg), "ob-unstated", cv.REALITY, "x", cmd, pin, "t"))
    check("V-GATECLASS-REALITY-REFUSES-UNSTATED", err is not None and "must declare" in err,
          f"an unstated class on a REALITY obligation is refused at acceptance: {err}",
          "a REALITY obligation was accepted with no declared gate class")

    err = raises(lambda: cv.accept_obligation(
        lg, gc.project(lg), "ob-unit", cv.REALITY, "x", cmd, pin, "t", gate_class="unit"))
    check("V-GATECLASS-REALITY-REFUSES-UNIT", err is not None,
          "a unit gate may not be registered to prove a reality claim",
          "a unit-class gate was accepted for a REALITY obligation -- the whole defect")

    err = raises(lambda: cv.accept_obligation(
        lg, gc.project(lg), "ob-bogus", cv.REALITY, "x", cmd, pin, "t",
        gate_class="wishful"))
    check("V-GATECLASS-UNKNOWN-REFUSED", err is not None and "must be one of" in err,
          "a class outside the vocabulary is refused rather than stored",
          f"an unknown gate class was accepted: {err!r}")

    err = raises(lambda: cv.accept_obligation(
        lg, gc.project(lg), "ob-reality", cv.REALITY, "a player sees it", cmd, pin, "t",
        gate_class="in_game"))
    check("V-GATECLASS-REALITY-ADMITS-INGAME", err is None,
          "the control: a declared in_game gate IS accepted, so the guard is not refusing everything",
          f"a correctly declared in_game obligation was refused: {err}")

    err = raises(lambda: cv.accept_obligation(
        lg, gc.project(lg), "ob-live", cv.REALITY, "x", cmd, pin, "t", gate_class="live"))
    check("V-GATECLASS-REALITY-ADMITS-LIVE", err is None,
          "the control: `live` is a runtime class too",
          f"a live obligation was refused: {err}")

    err = raises(lambda: cv.accept_obligation(
        lg, gc.project(lg), "ob-outcome", cv.OUTCOME, "x", cmd, pin, "t"))
    check("V-GATECLASS-NONREALITY-UNAFFECTED", err is None,
          "the negative control: a non-REALITY obligation still needs no class, so the "
          "guard is scoped to the plane it is about",
          f"the guard leaked onto a non-reality plane: {err}")

    o = cv.project_convergence(gc.project(lg)).obligations["ob-reality"]
    check("V-GATECLASS-PERSISTED", o.gate_class == "in_game",
          "the declared class survives the event log and projection",
          f"the class did not persist: {o.gate_class!r}")

    # --- the legacy case: an obligation accepted BEFORE the class existed ---
    # It cannot be created through `accept_obligation` any more, which is the
    # point, so it is appended as the raw event a pre-fix goal would carry.
    lg2 = make_goal(base, "g-legacy")
    s = gc.project(lg2)
    lg2.append(s.last_seq + 1, cv.OB_ACCEPTED,
               {"id": "ob-legacy", "plane": cv.REALITY, "text": "a player sees it",
                "done_gate": cmd, "gate_pin": [list(p) for p in pin],
                "revision": s.revision}, "t")
    legacy = cv.project_convergence(gc.project(lg2)).obligations["ob-legacy"]
    check("V-GATECLASS-LEGACY-IS-UNSTATED", legacy.gate_class == "",
          "a pre-fix obligation projects with no class -- unstated, not assumed runtime",
          f"a legacy obligation acquired a class from nowhere: {legacy.gate_class!r}")

    run_dir = Path(tempfile.mkdtemp(prefix="gsdx_gateclass_run_"))
    acted = sw.sweep_goal(lg2, repo, providers=("gate",), run_dir=run_dir)
    joined = " | ".join(acted)
    check("V-GATECLASS-SWEEP-REFUSES-LEGACY",
          "declares no runtime gate class" in joined,
          f"the unattended sweep refuses to dispatch it instead of inferring: {joined}",
          f"the sweep did not refuse an unstated REALITY obligation: {joined}")

    eps = cv.project_convergence(gc.project(lg2))
    dispatched = any(e.spec.get("obligation") == "ob-legacy"
                     for e in gc.project(lg2).epochs.values()) \
        if hasattr(gc.project(lg2), "epochs") else False
    check("V-GATECLASS-SWEEP-STARTED-NOTHING", not dispatched,
          "and no gate epoch was created for it, so nothing ran under a guessed class",
          "a gate epoch was created for an obligation with no declared class")

    # --- the control for the sweep: a DECLARED obligation is dispatched -----
    lg3 = make_goal(base, "g-declared")
    cv.accept_obligation(lg3, gc.project(lg3), "ob-real", cv.REALITY, "a player sees it",
                         cmd, pin, "t", gate_class="in_game")
    acted3 = sw.sweep_goal(lg3, repo, providers=("gate",),
                           run_dir=Path(tempfile.mkdtemp(prefix="gsdx_gc_run3_")))
    joined3 = " | ".join(acted3)
    check("V-GATECLASS-SWEEP-DISPATCHES-DECLARED",
          "declares no runtime gate class" not in joined3,
          f"the control: a declared in_game obligation is NOT refused: {joined3}",
          f"a correctly declared obligation was refused by the sweep: {joined3}")

    print(f"\nGSDX_GATE_CLASS_PASS={len(passes)}/{len(passes) + len(fails)}  "
          f"threshold={len(passes) + len(fails)}/{len(passes) + len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
