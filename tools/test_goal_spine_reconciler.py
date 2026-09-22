#!/usr/bin/env python3
"""V-gates for the Goal reconciler (vault/specs/goal-spine-v1.md, AC3-AC10).

Every gate drives the REAL stores: GSD X's obligation store, the spine's Goal and
epoch stores, and the real owner_queue (pointed at a temp directory so no test
writes into the Owner's own queue). The concurrency gate is a POSITIONED race --
a competing real save lands exactly between the tick's read and its claim --
because two sequential calls can never collide and would prove nothing.

    python tools/test_goal_spine_reconciler.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["GOAL_SPINE_STATE_DIR"] = tempfile.mkdtemp(prefix="goal-recon-")
os.environ["GOAL_SPINE_OWNER_QUEUE_DIR"] = tempfile.mkdtemp(prefix="goal-oq-")

from modules.goal_spine import epoch as ep_          # noqa: E402
from modules.goal_spine import goal as gl            # noqa: E402
from modules.goal_spine import reconciler as rcn     # noqa: E402
from modules.goal_spine import store as gs           # noqa: E402
from modules.gsd_x.mission import obligation as ob   # noqa: E402
from modules.gsd_x.mission import store as gsdx      # noqa: E402
from modules.owner_queue import owner_queue as oq    # noqa: E402

GATE = "kc:verify_change"
GATES = frozenset({GATE})
GIT = r"C:\Program Files\Git\cmd\git.exe"
_n = [0]


def _goal(obligations, *, done=True, budget=None, git=False) -> gl.Goal:
    _n[0] += 1
    root = tempfile.mkdtemp(prefix="recon-root-")
    if git:
        for args in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
            subprocess.run([GIT, "-C", root, *args], check=True, capture_output=True)
        _commit(root, "a")
    extra = {"budget": budget} if budget else {}
    g = gl.declare(root, f"Goal number {_n[0]}.", [o.identifier for o in obligations],
                   [{"id": "item", "text": "t", "done": done}], **extra)
    gsdx.save(Path(root), obligations, namespace=g.goal_id)
    return gs.save(g, expected_version=0)


def _commit(root: str, content: str) -> None:
    (Path(root) / "f.txt").write_text(content, encoding="utf-8")
    subprocess.run([GIT, "-C", root, "add", "f.txt"], check=True, capture_output=True)
    subprocess.run([GIT, "-C", root, "commit", "-qm", content], check=True, capture_output=True)


def _obl(ident, disposition=ob.ACCEPTED, gate=GATE, owner="unassigned") -> ob.Obligation:
    return ob.Obligation(ident, f"text {ident}", "TEST", ["fact:x"], "named consequence",
                         disposition=disposition, done_gate=gate, owner=owner)


def _satisfy_all(g: gl.Goal) -> None:
    obs = gsdx.load(Path(g.root), namespace=g.goal_id)
    for o in obs:
        o.disposition, o.disposition_reason = ob.SATISFIED, "gate observed"
    gsdx.save(Path(g.root), obs, namespace=g.goal_id)


def _end_last(g: gl.Goal, state=ep_.COMPLETED) -> ep_.Epoch:
    # The last OPEN epoch -- "the one the tick just prepared". Indexing [-1] by
    # timestamp picked an already-ended epoch whenever two shared a second.
    e = [x for x in ep_.for_goal(g.goal_id) if x.state in ep_.OPEN_STATES][-1]
    if e.state == ep_.PREPARED and e.provider in ep_.AUTONOMOUS_PROVIDERS:
        ep_.mark_started_autonomous(e)
    if e.state == ep_.PREPARED:
        # A worker epoch starts through the REAL path: a pane claims it, and the
        # claimed session's transcript shows the command after the claim. An
        # earlier version set `state = STARTED` directly, without the started_at
        # the real path records -- a fixture describing a world production never
        # enters, which the reconciler's "tried means STARTED" rule then exposed.
        ep_.claim(e, "0b7c3a1e-5f2d-4c8e-9a1b-2c3d4e5f6a7b")
        when = (datetime.strptime(e.claimed_at, "%Y-%m-%dT%H:%M:%SZ")
                .replace(tzinfo=timezone.utc) + timedelta(seconds=5))
        t = Path(tempfile.mkdtemp()) / "worker.jsonl"
        t.write_text(json.dumps({"type": "user", "timestamp": when.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                                 "message": {"content": f"<command-name>{e.command}</command-name>"}})
                     + "\n", encoding="utf-8")
        if not ep_.observe_worker_start(e, t):
            raise AssertionError("fixture could not start a worker epoch through the real path")
    ep_.end(e, state, "ran; the obligation did not close")
    return ep_.save(e, expected_version=e.version)


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []

    def ok(n, ev):
        passes.append(n)
        print(f"  OK   {n}  {ev}")

    def bad(n, ev):
        fails.append(n)
        print(f"  FAIL {n}  {ev}")

    def check(name, cond, ev):
        (ok if cond else bad)(name, ev)

    # --- first tick: an ACCEPTED obligation with a runnable gate is verified -
    g = _goal([_obl("DO-1")])
    a = rcn.tick(g.goal_id, gates=GATES)
    g = gs.load(g.goal_id)
    check("V-RECON-VERIFY-FIRST", a.kind == rcn.DISPATCH and a.provider == "verify"
          and g.state == gl.ACTIVE and len(ep_.for_goal(g.goal_id)) == 1,
          f"{a.kind}/{a.provider} state={g.state}")

    # --- an action with no packet never claims one was delivered -------------
    # `packet_delivered` defaults to False, and the mutant flipping that default
    # survived: a fail-open default on the one field the packet design rests on.
    check("V-RECON-NO-PACKET-NEVER-CLAIMS-DELIVERY",
          not a.packet_delivered and not a.packet_id,
          "a DISPATCH carries no packet and says so")

    # --- an epoch in flight is never doubled --------------------------------
    a2 = rcn.tick(g.goal_id, gates=GATES)
    check("V-RECON-INFLIGHT-WAITS", a2.kind == rcn.WAIT and len(ep_.for_goal(g.goal_id)) == 1,
          f"{a2.kind}, epochs={len(ep_.for_goal(g.goal_id))}")

    # --- no runnable gate -> a worker epoch is PREPARED, never started -------
    g = _goal([_obl("DO-1", gate="a human-judged gate")])
    a = rcn.tick(g.goal_id, gates=GATES)
    e = ep_.for_goal(g.goal_id)[0]
    check("V-RECON-WORKER-IS-PREPARED-NOT-STARTED",
          a.kind == rcn.PREPARE_WORKER and e.state == ep_.PREPARED
          and gs.load(g.goal_id).state == gl.AWAITING_WORKER and a.command == "/gsd-autonomous",
          f"{a.kind} epoch={e.state} goal={gs.load(g.goal_id).state}")
    src = Path(rcn.__file__).read_text(encoding="utf-8")
    check("V-RECON-NEVER-TOUCHES-THE-RESUME-MARKER",
          "gsd_autorun_marker" not in src and "--write" not in src,
          "no reference to the marker tool in the reconciler")

    # --- CONTROL: everything proven -> CONVERGE, then TERMINAL ---------------
    g = _goal([_obl("DO-1")])
    _satisfy_all(g)
    a = rcn.tick(g.goal_id, gates=GATES)
    after = rcn.tick(g.goal_id, gates=GATES)
    check("V-RECON-CONTROL-CONVERGES", a.kind == rcn.CONVERGE and after.kind == rcn.TERMINAL
          and gs.load(g.goal_id).state == gl.CONVERGED, f"{a.kind} then {after.kind}")

    # --- empty queue, not converged: an Owner packet, proven delivered -------
    g = _goal([_obl("DO-1")], done=False)
    _satisfy_all(g)
    a = rcn.tick(g.goal_id, gates=GATES)
    rows = {r["id"]: r for r in oq.load(Path(os.environ["GOAL_SPINE_OWNER_QUEUE_DIR"]))}
    check("V-RECON-EMPTY-QUEUE-IS-NOT-SUCCESS",
          a.kind == rcn.OWNER_PACKET and a.packet_delivered and a.packet_id in rows
          and gs.load(g.goal_id).state == gl.AWAITING_OWNER,
          f"{a.kind} delivered={a.packet_delivered} state={gs.load(g.goal_id).state}")
    again = rcn.tick(g.goal_id, gates=GATES)
    after_rows = oq.load(Path(os.environ["GOAL_SPINE_OWNER_QUEUE_DIR"]))
    check("V-RECON-PACKET-IS-IDEMPOTENT", again.packet_id == a.packet_id
          and sum(1 for r in after_rows if r["id"] == a.packet_id) == 1,
          "re-tick re-issued the same packet, not a second one")

    # --- an undeliverable packet does not claim the Owner was told -----------
    blocker = Path(tempfile.mkdtemp()) / "a-file"
    blocker.write_text("x", encoding="utf-8")
    saved_dir = os.environ["GOAL_SPINE_OWNER_QUEUE_DIR"]
    os.environ["GOAL_SPINE_OWNER_QUEUE_DIR"] = str(blocker / "cannot-be-a-dir")
    try:
        g = _goal([_obl("DO-1")], done=False)
        _satisfy_all(g)
        a = rcn.tick(g.goal_id, gates=GATES)
        st = gs.load(g.goal_id).state
        check("V-RECON-UNDELIVERED-PACKET-NOT-AWAITING-OWNER",
              a.kind == rcn.OWNER_PACKET and not a.packet_delivered and st != gl.AWAITING_OWNER,
              f"delivered={a.packet_delivered} state={st}")
    finally:
        os.environ["GOAL_SPINE_OWNER_QUEUE_DIR"] = saved_dir

    # --- judgement goes to the Owner, not to an epoch ------------------------
    g = _goal([_obl("DO-1", ob.CANDIDATE)])
    a = rcn.tick(g.goal_id, gates=GATES)
    check("V-RECON-CANDIDATE-IS-A-DECISION", a.kind == rcn.OWNER_PACKET
          and not ep_.for_goal(g.goal_id), a.reason[:70])
    g = _goal([_obl("DO-1")])
    gsdx.save(Path(g.root), [], namespace=g.goal_id)
    a = rcn.tick(g.goal_id, gates=GATES)
    check("V-RECON-MISSING-OBLIGATION-IS-A-DECISION", a.kind == rcn.OWNER_PACKET
          and "never written" in a.reason and not ep_.for_goal(g.goal_id), a.reason[:70])

    # --- no retry without new information ------------------------------------
    g = _goal([_obl("DO-1")])
    rcn.tick(g.goal_id, gates=GATES)                   # verify
    _end_last(g)
    a1 = rcn.tick(g.goal_id, gates=GATES)              # verify ran on this state -> worker
    _end_last(g)
    a2 = rcn.tick(g.goal_id, gates=GATES)              # worker ran on this state -> refuse
    check("V-RECON-NO-RETRY-WITHOUT-NEW-INFORMATION",
          a1.kind == rcn.PREPARE_WORKER and a2.kind == rcn.REFUSE_RETRY and a2.packet_delivered,
          f"{a1.kind} then {a2.kind}")

    # --- a commit IS new information: verify may run again --------------------
    g = _goal([_obl("DO-1")], git=True)
    rcn.tick(g.goal_id, gates=GATES)                   # verify
    _end_last(g)
    rcn.tick(g.goal_id, gates=GATES)                   # worker
    _end_last(g)
    _commit(g.root, "the worker changed the code")
    a = rcn.tick(g.goal_id, gates=GATES)
    check("V-RECON-A-COMMIT-IS-NEW-INFORMATION", a.kind == rcn.DISPATCH and a.provider == "verify",
          f"{a.kind}/{a.provider}")

    # --- per-obligation worker cap --------------------------------------------
    g = _goal([_obl("DO-1", gate="human")], git=True, budget={"max_epochs": 12,
                                                              "max_epochs_per_obligation": 2})
    for i in range(2):
        rcn.tick(g.goal_id, gates=GATES)
        _end_last(g)
        _commit(g.root, f"attempt {i}")
    a = rcn.tick(g.goal_id, gates=GATES)
    check("V-RECON-WORKER-CAP", a.kind == rcn.OWNER_PACKET and "worker epochs" in a.reason,
          a.reason[:70])

    # --- total epoch budget ----------------------------------------------------
    g = _goal([_obl("DO-1")], git=True, budget={"max_epochs": 2, "max_epochs_per_obligation": 3})
    for i in range(2):
        rcn.tick(g.goal_id, gates=GATES)
        _end_last(g)
        _commit(g.root, f"b{i}")
    a = rcn.tick(g.goal_id, gates=GATES)
    check("V-RECON-EPOCH-BUDGET", a.kind == rcn.OWNER_PACKET and "budget spent" in a.reason,
          a.reason[:70])

    # --- a revision strands the in-flight epoch as STALE and replans ----------
    g = _goal([_obl("DO-1")])
    rcn.tick(g.goal_id, gates=GATES)
    first = ep_.for_goal(g.goal_id)[0]
    live = gs.load(g.goal_id)
    gl.revise(live, "Goal number, now with a different target entirely.")
    gs.save(live, expected_version=live.version)
    a = rcn.tick(g.goal_id, gates=GATES)
    check("V-RECON-REVISION-STRANDS-EPOCH", ep_.load(first.epoch_id).state == ep_.STALE
          and a.kind == rcn.DISPATCH and a.epoch_id != first.epoch_id,
          f"old={ep_.load(first.epoch_id).state} new={a.kind}")

    # --- BLOCKED holds dispatch --------------------------------------------------
    g = _goal([_obl("DO-1")])
    live = gs.load(g.goal_id)
    gl.transition(live, gl.ACTIVE)
    gl.transition(live, gl.BLOCKED, category="UPSTREAM_MERGE", reason="ucr-cif not merged")
    gs.save(live, expected_version=live.version)
    a = rcn.tick(g.goal_id, gates=GATES)
    check("V-RECON-BLOCKED-HOLDS", a.kind == rcn.HELD_BLOCKED and not ep_.for_goal(g.goal_id),
          a.reason)

    # --- positioned race: a second coordinator saves between read and claim ---
    g = _goal([_obl("DO-1")])
    real_load = rcn.gs.load
    fired = [False]

    # One-shot. `rcn.gs` IS the store module, so this patch also replaces the
    # `load` that store.save calls internally; the first version re-entered itself
    # from inside the competitor's save and died of RecursionError. Only the
    # tick's own first read is raced; every later call is the real function.
    def racing_load(goal_id):
        if fired[0]:
            return real_load(goal_id)
        fired[0] = True
        stale = real_load(goal_id)
        competitor = real_load(goal_id)
        gs.save(competitor, expected_version=competitor.version)   # lands first
        return stale

    rcn.gs.load = racing_load
    try:
        a = rcn.tick(g.goal_id, gates=GATES)
    finally:
        rcn.gs.load = real_load
    check("V-RECON-SECOND-COORDINATOR-GETS-CONFLICT",
          a.kind == rcn.CONFLICT and not ep_.for_goal(g.goal_id),
          f"{a.kind}; no epoch prepared by the loser")

    # --- restart: a fresh process reaches the same decision from disk alone ---
    g = _goal([_obl("DO-1")])
    rcn.tick(g.goal_id, gates=GATES)
    probe = ("import sys; sys.path.insert(0, sys.argv[1]);"
             "from modules.goal_spine import reconciler as r;"
             "print(r.tick(sys.argv[2], gates=frozenset({sys.argv[3]})).kind)")
    out = subprocess.run([sys.executable, "-c", probe, str(ROOT), g.goal_id, GATE],
                         capture_output=True, text=True, timeout=120, env=dict(os.environ))
    check("V-RECON-RESTART-RECONSTRUCTS", out.stdout.strip() == rcn.WAIT,
          f"fresh process decided {out.stdout.strip() or out.stderr[-120:]}")

    # ---------------------------------------------------------------------------
    # Added after an independent adversarial audit and the mutation probe
    # (41/54). Each gate pins one finding the 18 above could not see.
    # ---------------------------------------------------------------------------

    # --- a coordinator arriving AFTER the claim is still refused -------------
    # The audit's HIGH: a version CAS fences only writers that read before it, so
    # a second tick loading after the first one's claim passed its own CAS and
    # prepared a second epoch -- two panes in one root.
    g = _goal([_obl("DO-1")])
    with gs.tick_lock(g.goal_id):
        held = rcn.tick(g.goal_id, gates=GATES)
    check("V-RECON-POST-CLAIM-COORDINATOR-REFUSED",
          held.kind == rcn.CONFLICT and not ep_.for_goal(g.goal_id),
          "a tick inside another tick's lock prepared nothing")
    after_release = rcn.tick(g.goal_id, gates=GATES)
    check("V-RECON-LOCK-IS-RELEASED", after_release.kind == rcn.DISPATCH,
          "the same Goal ticks normally once the lock is released")

    # --- a coordinator killed mid-tick must not park the Goal for ever -------
    g = _goal([_obl("DO-1")])
    lock = gs._goal_path(g.goal_id).with_suffix(".lock")
    lock.write_text(json.dumps({"owner": "9999:dead", "until": "2000-01-01T00:00:00Z"}),
                    encoding="utf-8")
    taken = rcn.tick(g.goal_id, gates=GATES)
    check("V-RECON-EXPIRED-LOCK-IS-TAKEN-OVER", taken.kind == rcn.DISPATCH,
          "an expired holder does not own the Goal for ever")

    # --- an epoch nobody claims is abandoned and replanned, not waited on ----
    g = _goal([_obl("DO-1", gate="human")])
    first = rcn.tick(g.goal_id, gates=GATES)
    e = ep_.load(first.epoch_id)
    e.lease_expires_at = "2000-01-01T00:00:00Z"
    ep_.save(e, expected_version=e.version)
    again = rcn.tick(g.goal_id, gates=GATES)
    check("V-RECON-UNCLAIMED-EPOCH-ABANDONED-AND-REPLANNED",
          ep_.load(first.epoch_id).state == ep_.ABANDONED
          and again.kind == rcn.PREPARE_WORKER and again.epoch_id != first.epoch_id,
          "an epoch that never started is neither a try nor an excuse to wait")

    # --- verify has its own cap, and does not consume the worker's ----------
    # Without a cap of its own, a cheap check could spend a Goal's whole budget
    # re-checking and never do the work.
    g = _goal([_obl("DO-1")], git=True,
              budget={"max_epochs": 12, "max_epochs_per_obligation": 1,
                      "max_verifies_per_obligation": 1})
    rcn.tick(g.goal_id, gates=GATES)             # verify
    _end_last(g)
    _commit(g.root, "state moved, so verify would be chosen again")
    a = rcn.tick(g.goal_id, gates=GATES)
    check("V-RECON-VERIFY-CAP-AND-WORKER-CAP-ARE-SEPARATE",
          a.kind == rcn.PREPARE_WORKER,
          "verify exhausted -> the worker is next, and verify did not eat its cap")
    _end_last(g)
    _commit(g.root, "the worker changed something too")
    a = rcn.tick(g.goal_id, gates=GATES)
    check("V-RECON-WORKER-CAP-STILL-BINDS", a.kind == rcn.OWNER_PACKET and "worker epochs" in a.reason,
          a.reason[:60])

    # --- the waiting state names WHO is being waited for --------------------
    g = _goal([_obl("DO-1")])
    rcn.tick(g.goal_id, gates=GATES)             # a verify epoch is in flight
    rcn.tick(g.goal_id, gates=GATES)
    autonomous_state = gs.load(g.goal_id).state
    g2 = _goal([_obl("DO-1", gate="human")])
    rcn.tick(g2.goal_id, gates=GATES)            # a worker epoch awaits a pane
    rcn.tick(g2.goal_id, gates=GATES)
    check("V-RECON-WAIT-STATE-NAMES-THE-BLOCKER",
          autonomous_state == gl.ACTIVE and gs.load(g2.goal_id).state == gl.AWAITING_WORKER,
          f"verify in flight -> {autonomous_state}; worker prepared -> AWAITING_WORKER")

    # --- converging ends epochs nobody will ever reconcile again ------------
    g = _goal([_obl("DO-1", gate="human")])
    a = rcn.tick(g.goal_id, gates=GATES)
    _satisfy_all(g)
    conv = rcn.tick(g.goal_id, gates=GATES)
    check("V-RECON-CONVERGE-ENDS-OPEN-EPOCHS",
          conv.kind == rcn.CONVERGE and ep_.load(a.epoch_id).state == ep_.ABANDONED,
          "a pane cannot keep working for a Goal that is finished")

    # --- a closed packet is re-asked, not silently swallowed ----------------
    g = _goal([_obl("DO-1")], done=False)
    _satisfy_all(g)
    first_packet = rcn.tick(g.goal_id, gates=GATES)
    oq.complete(first_packet.packet_id, state_dir=Path(os.environ["GOAL_SPINE_OWNER_QUEUE_DIR"]))
    second_packet = rcn.tick(g.goal_id, gates=GATES)
    rows = {r["id"]: r for r in oq.load(Path(os.environ["GOAL_SPINE_OWNER_QUEUE_DIR"]))}
    check("V-RECON-CLOSED-PACKET-IS-REASKED",
          second_packet.packet_delivered and second_packet.packet_id != first_packet.packet_id
          and rows[second_packet.packet_id]["status"] == "pending",
          "closing a packet without fixing the condition re-asks under a new id")

    total = len(passes) + len(fails)
    print(f"\nGOAL_RECONCILER_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
