#!/usr/bin/env python3
"""V-gates for the Goal Spine (vault/specs/goal-spine-v1.md).

Each gate names the acceptance criterion it pins. Every refusal gate is paired
with a control in which the same call succeeds, because a spine that refused
everything would pass every refusal assertion.

    python tools/test_goal_spine.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Isolate state BEFORE importing the store: no test may touch ~/.claude/state.
_STATE = tempfile.mkdtemp(prefix="goal-spine-test-")
os.environ["GOAL_SPINE_STATE_DIR"] = _STATE

from modules.goal_spine import goal as gl     # noqa: E402
from modules.goal_spine import store as gs    # noqa: E402

INTENT = "Make every KSEIP role provably wired."
OUTCOME = [{"id": "wiring-gate", "text": "a wiring gate exists and passes"}]


def _declare(intent: str = INTENT, ids=("DO-1",)) -> gl.Goal:
    return gl.declare("C:/repo", intent, list(ids), [dict(i) for i in OUTCOME])


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []

    def ok(g, ev):
        passes.append(g)
        print(f"  OK   {g}  {ev}")

    def bad(g, ev):
        fails.append(g)
        print(f"  FAIL {g}  {ev}")

    # --- identity is an intent IN A PLACE --------------------------------------
    # Found by the receipt suite: identity once hashed the intent alone, so two
    # repositories with the same sentence shared one global record.
    here = gl.declare("C:/repo-one", INTENT, ["DO-1"], [dict(i) for i in OUTCOME])
    there = gl.declare("C:/repo-two", INTENT, ["DO-1"], [dict(i) for i in OUTCOME])
    respelled = gl.declare("c:\\REPO-ONE", INTENT, ["DO-1"], [dict(i) for i in OUTCOME])
    if here.goal_id != there.goal_id and here.goal_id == respelled.goal_id \
            and here.intent_sha == there.intent_sha:
        ok("V-GOAL-ID-IS-INTENT-IN-A-PLACE",
           "same intent, two roots -> two Goals; one root respelled -> same Goal")
    else:
        bad("V-GOAL-ID-IS-INTENT-IN-A-PLACE", f"{here.goal_id} {there.goal_id} {respelled.goal_id}")

    # --- AC2: identity and revision -------------------------------------------
    a, b = _declare(), _declare("  Make every KSEIP   role provably wired.\n")
    if a.goal_id == b.goal_id and a.revision == b.revision == 1:
        ok("V-GOAL-ID-STABLE-ACROSS-WHITESPACE", a.goal_id)
    else:
        bad("V-GOAL-ID-STABLE-ACROSS-WHITESPACE", f"{a.goal_id} vs {b.goal_id}")

    g = _declare()
    moved_ws = gl.revise(g, "Make every KSEIP role\tprovably   wired.")
    moved_sem = gl.revise(g, "Make every KSEIP role provably wired AND dispatched.")
    if not moved_ws and moved_sem and g.revision == 2:
        ok("V-GOAL-REVISION-ONLY-ON-SEMANTIC-CHANGE", "ws=no-op, semantic=rev 2")
    else:
        bad("V-GOAL-REVISION-ONLY-ON-SEMANTIC-CHANGE",
            f"ws={moved_ws} sem={moved_sem} rev={g.revision}")

    # --- AC3: required obligations are mandatory (with control) --------------
    try:
        _declare(ids=())
        bad("V-GOAL-REFUSES-EMPTY-OBLIGATIONS", "declared with no obligations")
    except ValueError:
        ok("V-GOAL-REFUSES-EMPTY-OBLIGATIONS", "ValueError; control declares fine" if _declare() else "")

    # --- AC6: BLOCKED must be external (with control) -------------------------
    # One fresh ACTIVE Goal per category. An earlier version reused one Goal, so
    # when a mutant accepted the first internal cause the Goal was left BLOCKED,
    # the next attempt raised PermissionError, and the suite died instead of
    # reporting -- a crash the drill then scored as a surviving mutant.
    refused = []
    for cat in ("TESTS_FAILING", "CONTEXT_EXHAUSTED", "EPOCH_ENDED", ""):
        probe_goal = _declare()
        gl.transition(probe_goal, gl.ACTIVE)
        try:
            gl.transition(probe_goal, gl.BLOCKED, category=cat, reason="x")
        except ValueError:
            refused.append(cat)
    g = _declare()
    gl.transition(g, gl.ACTIVE)
    try:
        gl.transition(g, gl.BLOCKED, category="HOST_RESOURCE", reason="")
        empty_reason_ok = False
    except ValueError:
        empty_reason_ok = True
    gl.transition(g, gl.BLOCKED, category="HOST_RESOURCE",
                  reason="memory reaper kills idle jobs at 12% free")
    if len(refused) == 4 and empty_reason_ok and g.state == gl.BLOCKED:
        ok("V-GOAL-BLOCKED-MUST-BE-EXTERNAL", "4 internal causes refused; named external accepted")
    else:
        bad("V-GOAL-BLOCKED-MUST-BE-EXTERNAL",
            f"refused={refused} empty_reason_refused={empty_reason_ok} state={g.state}")

    # --- AC4: CONVERGED is not requestable ------------------------------------
    g = _declare()
    gl.transition(g, gl.ACTIVE)
    # The state table alone already refuses CONVERGED (it is never an allowed
    # target), so the explicit guard is defence in depth; its distinct value is
    # that the refusal names the ONE legitimate path. A refusal that only says
    # "not allowed" sends the caller hunting. The mutation drill scored the
    # guard's removal as an equivalent mutant until this message was pinned.
    try:
        gl.transition(g, gl.CONVERGED)
        bad("V-GOAL-CONVERGED-NOT-REQUESTABLE", "transition accepted CONVERGED")
    except PermissionError as exc:
        if "convergence verdict" in str(exc) and g.state == gl.ACTIVE:
            ok("V-GOAL-CONVERGED-NOT-REQUESTABLE", "refused, and names the verdict path")
        else:
            bad("V-GOAL-CONVERGED-NOT-REQUESTABLE", f"refused without naming the path: {exc}")

    # --- AC1: restart reconstructs from durable state -------------------------
    g = gs.save(_declare(), expected_version=0)
    probe = (
        "import sys,json; sys.path.insert(0, sys.argv[1]);"
        "from modules.goal_spine import store as s;"
        "print(json.dumps(s.load(sys.argv[2]).to_dict(), sort_keys=True))"
    )
    env = dict(os.environ, GOAL_SPINE_STATE_DIR=_STATE, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "-c", probe, str(ROOT), g.goal_id],
                       capture_output=True, text=True, env=env, timeout=60)
    fresh = json.loads(r.stdout) if r.returncode == 0 else None
    if fresh == json.loads(json.dumps(g.to_dict(), sort_keys=True)):
        ok("V-GOAL-RESTART-RECONSTRUCTS", f"fresh process read {g.goal_id} v{fresh['version']}")
    else:
        bad("V-GOAL-RESTART-RECONSTRUCTS", f"rc={r.returncode} err={r.stderr[-200:]}")

    # --- AC7: single writer ---------------------------------------------------
    first = gs.load(g.goal_id)
    second = gs.load(g.goal_id)
    gl.transition(first, gl.ACTIVE)
    gs.save(first, expected_version=second.version)
    try:
        gl.transition(second, gl.ABORTED)
        gs.save(second, expected_version=second.version)
        bad("V-GOAL-SINGLE-WRITER", "a stale writer overwrote the record")
    except gs.ConflictError:
        state_after = gs.load(g.goal_id).state
        if state_after == gl.ACTIVE:
            ok("V-GOAL-SINGLE-WRITER", "stale writer refused; first write kept")
        else:
            bad("V-GOAL-SINGLE-WRITER", f"refused but state is {state_after}")

    # --- corrupt record raises; it is never an absent Goal --------------------
    p = Path(_STATE) / f"{g.goal_id}.json"
    p.write_text("{truncated", encoding="utf-8")
    try:
        gs.load(g.goal_id)
        bad("V-GOAL-CORRUPT-RAISES", "a corrupt record loaded")
    except RuntimeError:
        ok("V-GOAL-CORRUPT-RAISES", "RuntimeError")

    # --- a record from a newer writer is refused, not silently truncated ------
    extra = dict(_declare().to_dict(), field_from_the_future=1)
    try:
        gl.Goal.from_dict(extra)
        bad("V-GOAL-UNKNOWN-FIELDS-REFUSED", "unknown field dropped silently")
    except ValueError:
        ok("V-GOAL-UNKNOWN-FIELDS-REFUSED", "ValueError")

    # --- an empty outcome contract is not an empty backlog --------------------
    g = _declare()
    if not g.explicit_backlog_empty:
        g.outcome_contract[0]["done"] = True
        if g.explicit_backlog_empty:
            ok("V-GOAL-BACKLOG-FROM-OWN-CONTRACT", "open item -> False; all done -> True")
        else:
            bad("V-GOAL-BACKLOG-FROM-OWN-CONTRACT", "all done still reads non-empty")
    else:
        bad("V-GOAL-BACKLOG-FROM-OWN-CONTRACT", "an open item read as an empty backlog")

    # ---------------------------------------------------------------------------
    # Added after tools/mutation_probe.py (a pre-existing, independent judge)
    # found store.py 4/15 and goal.py 18/24 against a suite my own hand-picked
    # drill had scored 6/6. Each gate below closes one survivor classified as a
    # REAL gap; the equivalent survivors are recorded in the spec, not tested around.
    # ---------------------------------------------------------------------------

    # --- a Goal's default authority denies production mutation ----------------
    g = _declare()
    if g.authority.get("production_mutation") is False:
        ok("V-GOAL-DEFAULT-AUTHORITY-NO-PROD-MUTATION", g.authority)
    else:
        bad("V-GOAL-DEFAULT-AUTHORITY-NO-PROD-MUTATION", g.authority)

    # --- malformed outcome items are refused, each on its own (with control) --
    refused = 0
    for item in ({"id": "bad id!", "text": "t"}, {"id": "ok-id", "text": "   "},
                 {"text": "no id"}):
        try:
            gl.declare("C:/repo", INTENT, ["DO-1"], [item])
        except ValueError:
            refused += 1
    control = gl.declare("C:/repo", INTENT, ["DO-1"], [{"id": "ok-id", "text": "t"}])
    if refused == 3 and control.outcome_contract[0]["done"] is False:
        ok("V-GOAL-OUTCOME-ITEMS-VALIDATED", "3/3 malformed refused; well-formed accepted")
    else:
        bad("V-GOAL-OUTCOME-ITEMS-VALIDATED", f"refused {refused}/3")

    # --- leaving BLOCKED clears the block, so a stale reason cannot survive ---
    g = _declare()
    gl.transition(g, gl.ACTIVE)
    gl.transition(g, gl.BLOCKED, category="UPSTREAM_MERGE", reason="ucr-cif not merged")
    gl.transition(g, gl.ACTIVE)
    if g.blocked_category == "" and g.blocked_reason == "":
        ok("V-GOAL-UNBLOCK-CLEARS-REASON", "BLOCKED -> ACTIVE left no stale reason")
    else:
        bad("V-GOAL-UNBLOCK-CLEARS-REASON", f"{g.blocked_category!r} {g.blocked_reason!r}")

    # --- a fresh machine: the state directory does not exist yet --------------
    nested = Path(tempfile.mkdtemp()) / "a" / "b" / "goal-spine"
    os.environ["GOAL_SPINE_STATE_DIR"] = str(nested)
    try:
        fresh = gs.save(_declare(), expected_version=0)
        gs.append_event(fresh.goal_id, "declared")
        v2 = gs.save(gs.load(fresh.goal_id), expected_version=1)
        if nested.is_dir() and v2.version == 2 and gs.events(fresh.goal_id):
            ok("V-GOAL-FRESH-MACHINE-AND-VERSION-COUNTS-WRITES",
               "nested dir created; two saves -> version 2")
        else:
            bad("V-GOAL-FRESH-MACHINE-AND-VERSION-COUNTS-WRITES", f"version={v2.version}")
    except (OSError, gs.ConflictError) as exc:
        bad("V-GOAL-FRESH-MACHINE-AND-VERSION-COUNTS-WRITES", repr(exc))
    finally:
        os.environ["GOAL_SPINE_STATE_DIR"] = _STATE

    # --- the event log is filtered by goal and keeps order --------------------
    # A NESTED, not-yet-existing directory: an event can be logged before any
    # Goal is saved (the reconciler records what it refused), so the log must
    # create its own directory. The probe caught this surviving when the only
    # fresh-machine test happened to save a Goal first.
    os.environ["GOAL_SPINE_STATE_DIR"] = str(Path(tempfile.mkdtemp()) / "x" / "y")
    try:
        gs.append_event("g-aaaaaaaaaaaa", "one")
        gs.append_event("g-bbbbbbbbbbbb", "other")
        gs.append_event("g-aaaaaaaaaaaa", "two")
        mine = [e["kind"] for e in gs.events("g-aaaaaaaaaaaa")]
        every = [e["kind"] for e in gs.events()]
        if mine == ["one", "two"] and every == ["one", "other", "two"]:
            ok("V-GOAL-EVENTS-FILTERED-AND-ORDERED", f"mine={mine} all={every}")
        else:
            bad("V-GOAL-EVENTS-FILTERED-AND-ORDERED", f"mine={mine} all={every}")
    finally:
        os.environ["GOAL_SPINE_STATE_DIR"] = _STATE

    total = len(passes) + len(fails)
    print(f"\nGOAL_SPINE_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
