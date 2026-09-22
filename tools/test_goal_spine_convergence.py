#!/usr/bin/env python3
"""V-gates for Goal convergence (vault/specs/goal-spine-v1.md, AC4 + AC5).

The spine never judges; GSD X's closure does. These gates pin that every way a
Goal could falsely converge is refused -- and, as the control, that a Goal whose
obligations are genuinely closed DOES converge. A convergence module that refused
everything would pass every other gate in this file.

Fixture note: obligations are written to the GSD X store with a disposition
already set. That is a fixture shortcut for this stage only; moving an obligation
to SATISFIED through a real verifier verdict is the receipt stage's job (G6),
gated separately.

    python tools/test_goal_spine_convergence.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["GOAL_SPINE_STATE_DIR"] = tempfile.mkdtemp(prefix="goal-conv-")

from modules.goal_spine import convergence as cv                # noqa: E402
from modules.goal_spine import goal as gl                       # noqa: E402
from modules.gsd_x.mission import obligation as ob              # noqa: E402
from modules.gsd_x.mission import store as gsdx_store           # noqa: E402

OUTCOME = [{"id": "gate", "text": "a wiring gate exists and passes"}]


def _goal(required=("DO-PR", "DO-GATE"), done=True, intent="Prove the wiring.") -> gl.Goal:
    root = tempfile.mkdtemp(prefix="goal-root-")
    g = gl.declare(root, intent, list(required), [dict(OUTCOME[0], done=done)])
    gl.transition(g, gl.ACTIVE)
    return g


def _obl(ident, disposition=ob.SATISFIED, reason="") -> ob.Obligation:
    return ob.Obligation(ident, f"text {ident}", "TEST", ["fact:x"], "named consequence",
                         disposition=disposition, disposition_reason=reason,
                         done_gate="verify_change.py", proof="VERIFY_RESULT=DONE_VERIFIED")


def _store(g: gl.Goal, obligations) -> None:
    gsdx_store.save(Path(g.root), list(obligations), namespace=g.goal_id)


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []

    def ok(n, ev):
        passes.append(n)
        print(f"  OK   {n}  {ev}")

    def bad(n, ev):
        fails.append(n)
        print(f"  FAIL {n}  {ev}")

    def expect_open(name, g, needle):
        v = cv.compute(g)
        hit = [b for b in v.blocking if needle in b]
        if not v.converged and hit:
            ok(name, hit[0][:110])
        else:
            bad(name, f"converged={v.converged} blocking={list(v.blocking)}")

    # --- CONTROL: genuinely closed obligations converge ----------------------
    g = _goal()
    _store(g, [_obl("DO-PR"), _obl("DO-GATE")])
    v = cv.compute(g)
    try:
        cv.apply_verdict(g, v)
        if g.state == gl.CONVERGED and g.converged_receipt.get("obligations_digest"):
            ok("V-GOAL-CONV-CONTROL-CONVERGES", f"CONVERGED with receipt {v.obligations_digest[:12]}")
        else:
            bad("V-GOAL-CONV-CONTROL-CONVERGES", f"state={g.state}")
    except PermissionError as exc:
        bad("V-GOAL-CONV-CONTROL-CONVERGES", f"refused a genuine convergence: {exc}")

    # --- AC5: an empty or missing store never converges -----------------------
    expect_open("V-GOAL-CONV-MISSING-STORE-IS-OPEN", _goal(), "absent from the obligation store")

    g = _goal()
    _store(g, [])
    expect_open("V-GOAL-CONV-EMPTY-STORE-IS-OPEN", g, "absent from the obligation store")

    # --- a declared id missing while its sibling is satisfied -----------------
    g = _goal()
    _store(g, [_obl("DO-PR")])
    expect_open("V-GOAL-CONV-MISSING-REQUIRED-ID-IS-OPEN", g, "DO-GATE is a declared requirement")

    # --- Production Reality ACCEPTED and unproven blocks, by closure's rule --
    g = _goal()
    _store(g, [_obl("DO-PR", ob.ACCEPTED), _obl("DO-GATE")])
    expect_open("V-GOAL-CONV-PRODUCTION-REALITY-OPEN-BLOCKS", g, "DO-PR is ACCEPTED and unproven")

    # --- the Goal's own backlog, not GSD's milestone --------------------------
    g = _goal(done=False)
    _store(g, [_obl("DO-PR"), _obl("DO-GATE")])
    expect_open("V-GOAL-CONV-OWN-BACKLOG-OPEN-BLOCKS", g, "explicit backlog is not empty")

    # --- an unrelated milestone in the same repo moves; the verdict does not --
    g = _goal()
    _store(g, [_obl("DO-PR", ob.ACCEPTED), _obl("DO-GATE")])
    planning = Path(g.root) / ".planning"
    planning.mkdir()
    (planning / "STATE.md").write_text("milestone: 'P0-A'\nstatus: in-progress\n", encoding="utf-8")
    before = cv.compute(g)
    (planning / "STATE.md").write_text("milestone: 'P0-A'\nstatus: complete\n", encoding="utf-8")
    after = cv.compute(g)
    if (before.converged, before.blocking) == (after.converged, after.blocking) and not after.converged:
        ok("V-GOAL-CONV-UNRELATED-MILESTONE-IGNORED", "P0-A completing changed nothing")
    else:
        bad("V-GOAL-CONV-UNRELATED-MILESTONE-IGNORED", f"{before.blocking} -> {after.blocking}")

    # --- a required obligation closed with no reason is open ------------------
    g = _goal()
    _store(g, [_obl("DO-PR", ob.NOT_APPLICABLE, reason=""), _obl("DO-GATE")])
    expect_open("V-GOAL-CONV-CLOSED-WITHOUT-REASON-IS-OPEN", g, "closed as NOT_APPLICABLE with no reason")
    g2 = _goal()
    _store(g2, [_obl("DO-PR", ob.DEFERRED, reason="needs ucr-cif merged"), _obl("DO-GATE")])
    v2 = cv.compute(g2)
    if v2.converged and any("DO-PR deferred" in r for r in v2.residual_risk):
        ok("V-GOAL-CONV-REASONED-DEFERRAL-IS-RESIDUAL-RISK", v2.residual_risk[0][:80])
    else:
        bad("V-GOAL-CONV-REASONED-DEFERRAL-IS-RESIDUAL-RISK",
            f"converged={v2.converged} residual={v2.residual_risk} blocking={v2.blocking}")

    # --- two Goals in one root do not see each other's obligations -----------
    a = _goal()
    b = gl.declare(a.root, "A different goal in the same repository.", ["DO-B"],
                   [dict(OUTCOME[0], done=True)])
    gl.transition(b, gl.ACTIVE)
    _store(a, [_obl("DO-PR", ob.ACCEPTED), _obl("DO-GATE")])
    _store(b, [_obl("DO-B")])
    if cv.compute(b).converged and not cv.compute(a).converged:
        ok("V-GOAL-CONV-GOALS-ISOLATED-IN-ONE-ROOT", "b converges; a's open obligation stays a's")
    else:
        bad("V-GOAL-CONV-GOALS-ISOLATED-IN-ONE-ROOT", "cross-goal leakage")

    # --- a verdict computed before the state moved authorises nothing --------
    g = _goal()
    _store(g, [_obl("DO-PR"), _obl("DO-GATE")])
    stale = cv.compute(g)
    _store(g, [_obl("DO-PR", ob.STALE), _obl("DO-GATE")])
    try:
        cv.apply_verdict(g, stale)
        bad("V-GOAL-CONV-STALE-VERDICT-REFUSED", "converged on a verdict the store no longer supports")
    except PermissionError as exc:
        ok("V-GOAL-CONV-STALE-VERDICT-REFUSED", str(exc)[:80]) if g.state == gl.ACTIVE \
            else bad("V-GOAL-CONV-STALE-VERDICT-REFUSED", f"state={g.state}")

    # --- a verdict for an older revision is refused ---------------------------
    g = _goal()
    _store(g, [_obl("DO-PR"), _obl("DO-GATE")])
    v = cv.compute(g)
    gl.revise(g, "Prove the wiring AND dispatch every role once.")
    try:
        cv.apply_verdict(g, v)
        bad("V-GOAL-CONV-REVISION-MISMATCH-REFUSED", "converged on an old revision's verdict")
    except PermissionError as exc:
        ok("V-GOAL-CONV-REVISION-MISMATCH-REFUSED", str(exc)[:80])

    # --- a non-converged verdict, a forged verdict, a verdict for another goal -
    g = _goal()
    _store(g, [_obl("DO-PR", ob.ACCEPTED), _obl("DO-GATE")])
    refused = 0
    other = _goal(intent="Some other goal entirely.")
    _store(other, [_obl("DO-PR"), _obl("DO-GATE")])
    for candidate in (cv.compute(g),                                  # not converged
                      {"converged": True, "goal_id": g.goal_id},     # forged dict
                      cv.compute(other)):                             # another goal
        try:
            cv.apply_verdict(g, candidate)
        except PermissionError:
            refused += 1
    if refused == 3 and g.state == gl.ACTIVE:
        ok("V-GOAL-CONV-ONLY-A-REAL-VERDICT-CONVERGES", "3/3 refused")
    else:
        bad("V-GOAL-CONV-ONLY-A-REAL-VERDICT-CONVERGES", f"refused {refused}/3 state={g.state}")

    # --- a tampered verdict converges nothing ---------------------------------
    # (a) the naive forgery is stopped by immutability; (b) the determined one --
    # object.__setattr__ past `frozen` -- is stopped by recomputation, because the
    # flag is never what apply_verdict believes.
    g = _goal()
    _store(g, [_obl("DO-PR", ob.ACCEPTED), _obl("DO-GATE")])
    v = cv.compute(g)
    naive_blocked = False
    try:
        v.converged = True   # type: ignore[misc]
    except AttributeError:
        naive_blocked = True
    object.__setattr__(v, "converged", True)
    object.__setattr__(v, "blocking", ())
    try:
        cv.apply_verdict(g, v)
        bad("V-GOAL-CONV-TAMPERED-VERDICT-REFUSED", "a flipped flag converged an open Goal")
    except PermissionError as exc:
        if naive_blocked and g.state == gl.ACTIVE:
            ok("V-GOAL-CONV-TAMPERED-VERDICT-REFUSED", "frozen + recompute: " + str(exc)[:60])
        else:
            bad("V-GOAL-CONV-TAMPERED-VERDICT-REFUSED", f"naive_blocked={naive_blocked}")

    # --- a corrupt obligation store raises; it is never an empty one ---------
    g = _goal()
    p = gsdx_store.store_path(Path(g.root), namespace=g.goal_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("{", encoding="utf-8")
    try:
        cv.compute(g)
        bad("V-GOAL-CONV-CORRUPT-STORE-RAISES", "computed a verdict over an unreadable store")
    except RuntimeError:
        ok("V-GOAL-CONV-CORRUPT-STORE-RAISES", "RuntimeError")

    total = len(passes) + len(fails)
    print(f"\nGOAL_CONVERGENCE_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
