#!/usr/bin/env python3
"""V-gates for the verify provider, including the first end-to-end autonomous loop.

Every gate runs a REAL subprocess as the gate -- no stubbed runner -- because the
thing under test is precisely what happens between a command's exit and an
obligation's disposition. The control is a Goal that converges with no human
step: tick -> DISPATCH -> the gate runs -> receipt -> ingest -> tick -> CONVERGE.

    python tools/test_goal_spine_verify.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["GOAL_SPINE_STATE_DIR"] = tempfile.mkdtemp(prefix="goal-verify-")
os.environ["GOAL_SPINE_OWNER_QUEUE_DIR"] = tempfile.mkdtemp(prefix="goal-verify-oq-")

from modules.goal_spine import epoch as ep_                 # noqa: E402
from modules.goal_spine import goal as gl                   # noqa: E402
from modules.goal_spine import receipt as rc                # noqa: E402
from modules.goal_spine import reconciler as rcn            # noqa: E402
from modules.goal_spine import store as gs                  # noqa: E402
from modules.goal_spine.providers import verify as vf       # noqa: E402
from modules.gsd_x.mission import obligation as ob          # noqa: E402
from modules.gsd_x.mission import store as gsdx             # noqa: E402

PY = sys.executable
_n = [0]


def _goal(gate_id: str) -> gl.Goal:
    _n[0] += 1
    root = tempfile.mkdtemp(prefix="verify-root-")
    g = gl.declare(root, f"Verify goal {_n[0]}.", ["DO-1"], [{"id": "i", "text": "t", "done": True}])
    gsdx.save(Path(root), [ob.Obligation("DO-1", "t", "TEST", ["fact:x"], "c",
                                         disposition=ob.ACCEPTED, done_gate=gate_id)],
              namespace=g.goal_id)
    return gs.save(g, expected_version=0)


def _registry(gate_id: str, code: str, timeout=60, interpret=vf.rc_interpreter) -> vf.Registry:
    r = vf.Registry()
    r.register(vf.Gate(gate_id, (PY, "-c", code), cwd=tempfile.gettempdir(),
                       timeout_s=timeout, interpret=interpret))
    return r


def _disposition(g: gl.Goal) -> str:
    return gsdx.load(Path(g.root), namespace=g.goal_id)[0].disposition


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []

    def check(name, cond, ev):
        (passes if cond else fails).append(name)
        print(f"  {'OK  ' if cond else 'FAIL'} {name}  {ev}")

    # --- CONTROL: the first autonomous loop converges with no human step -----
    reg = _registry("t:pass", "print('VERIFY_RESULT=DONE_VERIFIED')")
    g = _goal("t:pass")
    a1 = rcn.tick(g.goal_id, gates=reg.ids())
    res = vf.execute(a1.epoch_id, reg) if a1.kind == rcn.DISPATCH else None
    a2 = rcn.tick(g.goal_id, gates=reg.ids())
    check("V-VERIFY-AUTONOMOUS-LOOP-CONVERGES",
          a1.kind == rcn.DISPATCH and res is not None and res.outcome == rc.APPLIED
          and a2.kind == rcn.CONVERGE and gs.load(g.goal_id).state == gl.CONVERGED,
          f"{a1.kind} -> {res.outcome if res else None} -> {a2.kind}")

    # --- a failing gate satisfies nothing, and the next step is real work ----
    reg = _registry("t:fail", "import sys; print('VERIFY_RESULT=BLOCKED'); sys.exit(1)")
    g = _goal("t:fail")
    a1 = rcn.tick(g.goal_id, gates=reg.ids())
    res = vf.execute(a1.epoch_id, reg)
    a2 = rcn.tick(g.goal_id, gates=reg.ids())
    check("V-VERIFY-FAILING-GATE-LEADS-TO-WORK",
          res.outcome == rc.REFUSED and _disposition(g) == ob.ACCEPTED
          and ep_.load(a1.epoch_id).state == ep_.COMPLETED and a2.kind == rcn.PREPARE_WORKER,
          f"{res.outcome} then {a2.kind}")

    # --- three ways a gate can fail to judge; none reads as a pass -----------
    cases = [
        ("TIMEOUT", _registry("t:slow", "import time; time.sleep(30)", timeout=2)),
        ("UNRUNNABLE", None),
        ("UNINTERPRETABLE", _registry("t:bad", "print('x')",
                                      interpret=lambda rcode, out: (_ for _ in ()).throw(ValueError("no verdict line")))),
    ]
    results = []
    for label, reg in cases:
        if reg is None:
            reg = vf.Registry()
            reg.register(vf.Gate("t:none", ("definitely-not-an-executable-xyz",), cwd=tempfile.gettempdir()))
            gate_id = "t:none"
        else:
            gate_id = next(iter(reg.ids()))
        g = _goal(gate_id)
        a = rcn.tick(g.goal_id, gates=reg.ids())
        res = vf.execute(a.epoch_id, reg)
        results.append((label, res.outcome, label in res.reason, _disposition(g)))
    check("V-VERIFY-COULD-NOT-JUDGE-IS-NEVER-A-PASS",
          all(o == rc.REFUSED and named and d == ob.ACCEPTED for _, o, named, d in results),
          "; ".join(f"{lbl}={o}/{'named' if n else 'UNNAMED'}" for lbl, o, n, _ in results))

    # --- an unregistered gate is never offered to verify ---------------------
    g = _goal("t:unregistered")
    a = rcn.tick(g.goal_id, gates=vf.Registry().ids())
    check("V-VERIFY-UNREGISTERED-GATE-NOT-OFFERED", a.kind == rcn.PREPARE_WORKER, a.kind)

    # --- registry refuses a silent redefinition; execute refuses a worker epoch
    reg = _registry("t:x", "print(1)")
    try:
        reg.register(vf.Gate("t:x", (PY, "-c", "print(2)"), cwd="."))
        redefined = False
    except ValueError:
        redefined = True
    g = _goal("t:human")
    worker = rcn.tick(g.goal_id, gates=frozenset())
    try:
        vf.execute(worker.epoch_id, reg)
        refused_worker = False
    except PermissionError:
        refused_worker = True
    check("V-VERIFY-REGISTRY-AND-PROVIDER-BOUNDARIES", redefined and refused_worker,
          f"redefinition refused={redefined}; worker epoch refused={refused_worker}")

    total = len(passes) + len(fails)
    print(f"\nGOAL_VERIFY_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
