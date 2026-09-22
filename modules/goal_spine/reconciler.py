#!/usr/bin/env python3
"""The Goal reconciler -- one deterministic tick, exactly one justified Action.

This is the only part of the spine that decides what happens next, and it is
deliberately small and dumb. It makes no model calls and does no open-ended
work. Each tick it reads durable state from its owners, reconciles the epochs,
asks GSD X closure whether the Goal has converged, and otherwise names ONE next
action: dispatch an autonomous epoch, prepare a worker epoch, write an Owner
decision packet, or wait. Judgement -- designing an experiment, resolving a
product ambiguity, deciding what a STALE obligation now means -- is never made
here; it becomes an Owner packet or a provider's job (audit gap 12).

INVARIANTS, each pinned in tools/test_goal_spine_reconciler.py
--------------------------------------------------------------
* An empty queue is never success. A Goal with no open obligation that has not
  converged gets an Owner packet naming why, not a CONVERGED.
* CONVERGED comes only from `convergence.apply_verdict`, which recomputes.
* No retry without new information. The fingerprint is (provider, scope, state)
  and state = Goal revision + obligations digest + repository HEAD. A worker that
  COMMITTED code has produced new information; one that changed nothing has not.
  Uncommitted work is not evidence -- and hashing the dirty tree would let any
  other pane in a shared checkout mint "new information" on this Goal's behalf.
* Bounded three ways: `max_epochs` per Goal, `max_epochs_per_obligation` worker
  attempts, and `max_verifies_per_obligation` -- because a cheap check with no cap
  of its own can spend a whole budget re-checking and never do the work.
* Every epoch carries a lease from birth, so one nobody claims or executes is
  abandoned and replanned instead of leaving the Goal waiting forever.
* Single writer per tick: an exclusive, EXPIRING lock spans load -> decide -> save.
  The version CAS alone is not a lease; it fences only coordinators that read
  before it, so one loading after the claim would pass its own CAS and prepare a
  second epoch for the same obligation.
* The spine never starts a worker run and never writes a resume marker. A
  worker epoch is PREPARED and the Goal waits in AWAITING_WORKER.
* An Owner packet counts as delivered only when a PENDING row can be read back:
  `owner_queue.append` is fail-open, and it is idempotent across every status, so
  a closed row is re-asked under a fresh identity rather than silently swallowed.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from modules.gsd_x.mission import obligation as gsdx_obligation
from modules.owner_queue import owner_queue

from . import convergence as cv
from . import epoch as ep_
from . import goal as gl
from . import store as gs

TERMINAL = "TERMINAL"
CONFLICT = "CONFLICT"
CONVERGE = "CONVERGE"
DISPATCH = "DISPATCH"                # an autonomous epoch is ready for the runner
PREPARE_WORKER = "PREPARE_WORKER"    # a worker epoch awaits a pane
WAIT = "WAIT"                        # an epoch is already in flight
OWNER_PACKET = "OWNER_PACKET"
REFUSE_RETRY = "REFUSE_RETRY"
HELD_BLOCKED = "HELD_BLOCKED"

WORKER_COMMAND = "/gsd-autonomous"
_GIT = r"C:\Program Files\Git\cmd\git.exe" if os.name == "nt" else "git"


@dataclass(frozen=True)
class Action:
    kind: str
    goal_id: str
    revision: int
    reason: str
    epoch_id: str = ""
    provider: str = ""
    obligation_ids: tuple[str, ...] = field(default_factory=tuple)
    command: str = ""
    packet_id: str = ""
    packet_delivered: bool = False


def repo_state(root: str) -> str:
    """The COMMITTED state of the repository. Unknown is a value, never "".

    HEAD only, deliberately. An earlier version also hashed `git status
    --porcelain`, which made any other pane's uncommitted save look like new
    information -- and this estate's main repository is a shared tree with several
    live writers. The consequences were measured by audit: the retry refusal was
    effectively disabled, and repeated verify runs could burn a Goal's whole epoch
    budget while the obligation was never worked.

    The rule it encodes is right anyway: uncommitted work is not evidence. A worker
    that changed something proves it by committing, which is this estate's
    micro-commit law, and then HEAD moves.
    """
    try:
        head = subprocess.run([_GIT, "-C", root, "rev-parse", "HEAD"], capture_output=True,
                              text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"unknown:{exc.__class__.__name__}"
    if head.returncode != 0:
        return "nogit"
    return head.stdout.strip()


def state_digest(goal: gl.Goal, obligations) -> str:
    # The revision is part of the state: a Founder change moved the target, which
    # is new information by definition. Without it, an epoch stranded STALE by a
    # revision read as "already tried on this exact state" and blocked the very
    # work the new revision asked for (caught by V-RECON-REVISION-STRANDS-EPOCH).
    return hashlib.sha256(
        f"rev{goal.revision}|{cv.obligations_digest(obligations)}|{repo_state(goal.root)}"
        .encode("utf-8")).hexdigest()


def _packet_dir():
    d = os.environ.get("GOAL_SPINE_OWNER_QUEUE_DIR")
    return Path(d) if d else None


def _deliver_packet(goal: gl.Goal, text: str, unblocks: str) -> tuple[str, bool]:
    """Write an Owner packet and PROVE it landed by reading it back.

    Two properties, and the second cost a real stall to find. `owner_queue.append`
    is idempotent on sha(action, command) and returns early when that id exists in
    ANY status -- so once a row was closed without the underlying condition being
    fixed, every later tick regenerated the same text, hit the early return, read
    back `done`, and the Goal sat in AWAITING_OWNER with nothing pending for anyone
    to see. A closed row therefore means RE-ASK: the same question with a fresh
    identity, counting the times it has been closed, so the Owner sees that this
    has come back rather than a silent repeat.
    """
    command = f"python -m modules.goal_spine.cli status {goal.goal_id}"
    base = f"[GOAL {goal.goal_id} rev {goal.revision}] {text}"
    for attempt in range(1, 6):
        action = base if attempt == 1 else f"{base}  (re-asked; closed {attempt - 1}x without change)"
        rid = owner_queue.append(action, command, unblocks=unblocks, component=goal.goal_id,
                                 source="goal-spine", state_dir=_packet_dir())
        rows = {r["id"]: r for r in owner_queue.load(_packet_dir())}
        row = rows.get(rid)
        if row is None:
            return rid, False                    # append is fail-open: nothing landed
        if row.get("status") == "pending":
            return rid, True
    return rid, False


def _enter(goal: gl.Goal, state: str) -> None:
    if goal.state == state:
        return
    if state not in gl._ALLOWED.get(goal.state, set()):
        # Route through ACTIVE when a direct edge does not exist (e.g. BLOCKED ->
        # AWAITING_OWNER). ACTIVE is reachable from every non-terminal state.
        gl.transition(goal, gl.ACTIVE)
    if goal.state != state:
        gl.transition(goal, state)


def tick(goal_id: str, *, gates: frozenset[str] = frozenset()) -> Action:
    """One reconciliation, under an exclusive lock over the whole decision.

    The lock -- not the version CAS -- is what makes a tick single-writer. A
    compare-and-set on the Goal record fences only coordinators that read BEFORE
    it; one that loads after the claim lands passes its own CAS and prepares a
    second epoch for the same obligation, which on the worker path means two panes
    each running /gsd-autonomous in one root. Found by adversarial audit before it
    could happen in production.
    """
    try:
        with gs.tick_lock(goal_id):
            return _locked_tick(goal_id, gates)
    except gs.LockBusy as exc:
        goal = gs.load(goal_id)
        return Action(CONFLICT, goal.goal_id, goal.revision, str(exc))


def _locked_tick(goal_id: str, gates: frozenset[str]) -> Action:
    goal = gs.load(goal_id)
    if goal.state in gl.TERMINAL:
        return Action(TERMINAL, goal.goal_id, goal.revision, f"Goal is {goal.state}")

    # The version CAS stays as a SECOND line of defence: the lock serialises
    # coordinators that use it, and this still refuses a writer that did not.
    read_version = goal.version
    goal.updated_at = gl.now_iso()
    try:
        goal = gs.save(goal, expected_version=read_version)
    except gs.ConflictError as exc:
        return Action(CONFLICT, goal.goal_id, goal.revision, str(exc))
    if goal.state == gl.DECLARED:
        gl.transition(goal, gl.ACTIVE)

    action = _decide(goal, gates)
    try:
        gs.save(goal, expected_version=goal.version)
    except gs.ConflictError as exc:
        # Someone wrote the record while we held the lock, so they were not using
        # it. Report the conflict rather than letting it escape AFTER the side
        # effects, which would lose the action and write no tick event.
        gs.append_event(goal.goal_id, "tick", action=CONFLICT, reason=str(exc),
                        epoch_id=action.epoch_id, revision=goal.revision)
        return Action(CONFLICT, goal.goal_id, goal.revision,
                      f"the record moved under the tick lock: {exc}")
    gs.append_event(goal.goal_id, "tick", action=action.kind, reason=action.reason,
                    epoch_id=action.epoch_id, packet_id=action.packet_id,
                    delivered=action.packet_delivered, revision=goal.revision)
    return action


def _owner(goal: gl.Goal, kind: str, text: str, unblocks: str,
           obligation_ids=()) -> Action:
    rid, delivered = _deliver_packet(goal, text, unblocks)
    if delivered:
        _enter(goal, gl.AWAITING_OWNER)
    # If delivery could not be proven the Goal does NOT claim to await an Owner
    # who was never told; it stays where it is and the event records the failure.
    return Action(kind, goal.goal_id, goal.revision, text, packet_id=rid,
                  packet_delivered=delivered, obligation_ids=tuple(obligation_ids))


def _decide(goal: gl.Goal, gates: frozenset[str]) -> Action:
    # --- 1. reconcile epochs -----------------------------------------------------
    epochs = ep_.for_goal(goal.goal_id)
    for e in epochs:
        if e.state not in ep_.OPEN_STATES:
            continue
        snapshot = e.to_dict()
        if ep_.is_stale(e, goal):
            ep_.end(e, ep_.STALE, f"Goal revised to {goal.revision}")
        elif ep_.lease_expired(e):
            ep_.end(e, ep_.ABANDONED, "lease expired with no completion")
        elif e.state == ep_.CLAIMED:
            ep_.observe_worker_start(e)
        if e.to_dict() != snapshot:
            ep_.save(e, expected_version=e.version)
    epochs = ep_.for_goal(goal.goal_id)

    # --- 2. has it converged? GSD X closure decides ----------------------------
    verdict = cv.compute(goal)
    if verdict.converged:
        # Nothing reconciles a CONVERGED Goal again (tick returns TERMINAL), so any
        # epoch still open at this moment would stay open forever and a pane could
        # go on working for a Goal that is finished. End them here, with the reason.
        for e in epochs:
            if e.state in ep_.OPEN_STATES:
                ep_.end(e, ep_.ABANDONED, "the Goal converged before this epoch ran")
                ep_.save(e, expected_version=e.version)
        _enter(goal, gl.ACTIVE)
        cv.apply_verdict(goal, verdict)
        return Action(CONVERGE, goal.goal_id, goal.revision,
                      f"closure may close; receipt {verdict.obligations_digest[:12]}")

    if goal.state == gl.BLOCKED:
        return Action(HELD_BLOCKED, goal.goal_id, goal.revision,
                      f"{goal.blocked_category}: {goal.blocked_reason}")

    # --- 3. something already in flight? -----------------------------------------
    live = [e for e in epochs if e.state in ep_.OPEN_STATES]
    if live:
        waiting_on_pane = any(e.provider in ep_.WORKER_PROVIDERS and e.state != ep_.STARTED
                              for e in live)
        _enter(goal, gl.AWAITING_WORKER if waiting_on_pane else gl.ACTIVE)
        return Action(WAIT, goal.goal_id, goal.revision,
                      f"{len(live)} epoch(s) in flight", epoch_id=live[0].epoch_id,
                      provider=live[0].provider)

    obligations = cv.load_obligations(goal)
    by_id = {o.identifier: o for o in obligations}
    open_ids = [rid for rid in goal.required_obligation_ids
                if rid not in by_id or by_id[rid].disposition in gsdx_obligation.OPEN_DISPOSITIONS]

    # --- 4. empty queue, not converged: never success --------------------------
    if not open_ids:
        return _owner(goal, OWNER_PACKET,
                      "no open obligation, yet the Goal has not converged: "
                      + "; ".join(verdict.blocking), "Goal convergence")

    # --- 5. budget -------------------------------------------------------------
    if len(epochs) >= int(goal.budget.get("max_epochs", 12)):
        return _owner(goal, OWNER_PACKET,
                      f"epoch budget spent ({len(epochs)}); extend it or re-scope the Goal",
                      "Goal budget", open_ids)

    oid = open_ids[0]
    o = by_id.get(oid)
    if o is None:
        return _owner(goal, OWNER_PACKET,
                      f"{oid} is a declared requirement that was never written to the "
                      "obligation store; derive and accept it", "Goal obligations", [oid])
    if o.disposition != gsdx_obligation.ACCEPTED:
        return _owner(goal, OWNER_PACKET,
                      f"{oid} is {o.disposition}; judging it is a decision, not work",
                      "Goal obligations", [oid])

    # "Tried" means STARTED. An epoch stranded while PREPARED (revised away, or
    # never claimed before its lease ran out) produced no evidence and so neither
    # counts as an attempt nor as a prior run on this state. The TOTAL budget
    # above still counts every epoch, so prepare-and-strand churn stays bounded.
    ran = [e for e in epochs if e.state not in ep_.OPEN_STATES and e.started_at]
    mine = [e for e in ran if oid in e.scope]
    worker_attempts = [e for e in mine if e.provider in ep_.WORKER_PROVIDERS]
    cap = int(goal.budget.get("max_epochs_per_obligation", 3))
    if len(worker_attempts) >= cap:
        return _owner(goal, OWNER_PACKET,
                      f"{oid} took {len(worker_attempts)} worker epochs without closing; "
                      "a new approach needs a human", "Goal obligations", [oid])
    # Verify needs its OWN cap. It is cheap, so it was bounded only by the Goal's
    # total budget -- and whenever the state digest moved for any reason, verify was
    # preferred again. An obligation could therefore spend a Goal's entire budget
    # re-checking itself and never be worked on at all (adversarial audit, 2026-09-22).
    verify_attempts = [e for e in mine if e.provider == "verify"]
    verify_cap = int(goal.budget.get("max_verifies_per_obligation", cap))
    verify_exhausted = len(verify_attempts) >= verify_cap

    # --- 6. choose a provider and refuse an uninformed retry -------------------
    state = state_digest(goal, obligations)
    ended = ran     # only epochs that actually started are evidence of a prior try
    verify_fp = ep_.fingerprint("verify", [oid], state)
    if (o.done_gate in gates and not verify_exhausted
            and not any(e.fingerprint == verify_fp for e in ended)):
        provider = "verify"
    else:
        provider = o.owner if o.owner in ep_.WORKER_PROVIDERS | {"codex"} else "gsd_long"
    fp = ep_.fingerprint(provider, [oid], state)
    same = [e for e in ended if e.fingerprint == fp]
    if same:
        return _owner(goal, REFUSE_RETRY,
                      f"{oid}: epoch {same[-1].epoch_id} already ran {provider} on this exact "
                      "state and nothing changed; repeating it teaches nothing",
                      "Goal retry", [oid])

    # --- 7. prepare the epoch --------------------------------------------------
    worker = provider in ep_.WORKER_PROVIDERS
    e = ep_.prepare(goal, provider, [oid], state,
                    command=WORKER_COMMAND if worker else "", cwd=goal.root)
    try:
        ep_.save(e, expected_version=0)
    except gs.ConflictError as exc:
        # Defence in depth behind the epoch-id nonce: an id that already exists is
        # somebody else's record, and overwriting it would destroy an epoch this
        # tick did not create. Report rather than let it escape after the
        # housekeeping writes, which is how the first occurrence was found.
        return Action(CONFLICT, goal.goal_id, goal.revision,
                      f"could not create an epoch for {oid}: {exc}")
    if worker:
        _enter(goal, gl.AWAITING_WORKER)
        return Action(PREPARE_WORKER, goal.goal_id, goal.revision,
                      f"{oid} needs work; a pane must claim {e.epoch_id} and run "
                      f"{WORKER_COMMAND} in {goal.root}",
                      epoch_id=e.epoch_id, provider=provider, obligation_ids=(oid,),
                      command=WORKER_COMMAND)
    _enter(goal, gl.ACTIVE)
    return Action(DISPATCH, goal.goal_id, goal.revision, f"{oid}: run {provider}",
                  epoch_id=e.epoch_id, provider=provider, obligation_ids=(oid,))
