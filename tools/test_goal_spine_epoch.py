#!/usr/bin/env python3
"""V-gates for execution epochs (vault/specs/goal-spine-v1.md, AC8 + AC9).

The start-detection gates drive `/cpp-gsd-long`'s REAL detector
(`tools/gsd_long_run.user_issued_command_since`) over transcripts written in the
real row shape -- no stub, so no test double can be looser than the contract.
Every "did not start" case is paired with the control that does start, because an
epoch that never started would pass every negative case in this file.

    python tools/test_goal_spine_epoch.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["GOAL_SPINE_STATE_DIR"] = tempfile.mkdtemp(prefix="goal-epoch-")

from modules.goal_spine import epoch as ep_     # noqa: E402
from modules.goal_spine import goal as gl       # noqa: E402
from modules.goal_spine import store as gs      # noqa: E402

SID = "0b7c3a1e-5f2d-4c8e-9a1b-2c3d4e5f6a7b"
CMD = "/gsd-autonomous"


def _goal() -> gl.Goal:
    g = gl.declare("C:/repo", "Prove the wiring.", ["DO-PR", "DO-GATE"],
                   [{"id": "gate", "text": "t"}])
    gl.transition(g, gl.ACTIVE)
    return g


def _ts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _transcript(rows: list[dict]) -> Path:
    p = Path(tempfile.mkdtemp()) / f"{SID}.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return p


def _row(kind: str, when: datetime, text: str) -> dict:
    return {"type": kind, "timestamp": _ts(when), "message": {"content": text}}


def _claimed() -> ep_.Epoch:
    e = ep_.prepare(_goal(), "gsd_long", ["DO-GATE"], "digest-1", command=CMD)
    ep_.claim(e, SID)
    return e


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []

    def ok(n, ev):
        passes.append(n)
        print(f"  OK   {n}  {ev}")

    def bad(n, ev):
        fails.append(n)
        print(f"  FAIL {n}  {ev}")

    g = _goal()

    # --- prepare validates its inputs (with control) --------------------------
    refused = 0
    for args, kw in ((("bogus", ["DO-GATE"], "d"), {}),
                     (("verify", [], "d"), {}),
                     (("verify", ["DO-NOT-DECLARED"], "d"), {}),
                     (("gsd_long", ["DO-GATE"], "d"), {"command": "run it please"})):
        try:
            ep_.prepare(g, *args, **kw)
        except ValueError:
            refused += 1
    control = ep_.prepare(g, "verify", ["DO-GATE"], "d")
    if refused == 4 and control.state == ep_.PREPARED:
        ok("V-EPOCH-PREPARE-VALIDATES", "4/4 malformed refused; control PREPARED")
    else:
        bad("V-EPOCH-PREPARE-VALIDATES", f"refused {refused}/4")

    # --- AC9: the fingerprint is structured; rewording cannot reset it -------
    a = ep_.fingerprint("verify", ["DO-GATE", "DO-PR"], "digest-1")
    b = ep_.fingerprint("verify", ["DO-PR", "DO-GATE"], "digest-1")
    c = ep_.fingerprint("verify", ["DO-PR", "DO-GATE"], "digest-2")
    d = ep_.fingerprint("codex", ["DO-PR", "DO-GATE"], "digest-1")
    if a == b and a != c and a != d:
        ok("V-EPOCH-FINGERPRINT-STRUCTURED", "order-free; moves only with provider/scope/state")
    else:
        bad("V-EPOCH-FINGERPRINT-STRUCTURED", f"{a} {b} {c} {d}")

    # --- the spine cannot start a worker run; it can start its own ----------
    worker = ep_.prepare(g, "gsd_long", ["DO-GATE"], "d", command=CMD)
    auto = ep_.prepare(g, "verify", ["DO-GATE"], "d")
    ep_.mark_started_autonomous(auto)
    try:
        ep_.mark_started_autonomous(worker)
        bad("V-EPOCH-SPINE-CANNOT-START-A-WORKER", "self-started a worker epoch")
    except PermissionError:
        if auto.state == ep_.STARTED and worker.state == ep_.PREPARED:
            ok("V-EPOCH-SPINE-CANNOT-START-A-WORKER", "worker refused; autonomous STARTED")
        else:
            bad("V-EPOCH-SPINE-CANNOT-START-A-WORKER", f"{auto.state} {worker.state}")

    # --- AC8: STARTED only on the claimed session's own command, after claim --
    cases = []
    e = _claimed()
    t0 = datetime.strptime(e.claimed_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    cases.append(("command BEFORE the claim",
                  ep_.observe_worker_start(e, _transcript([_row("user", t0 - timedelta(minutes=5), f"<command-name>{CMD}</command-name>")]))))
    e = _claimed()
    cases.append(("unrelated user work after the claim",
                  ep_.observe_worker_start(e, _transcript([_row("user", t0 + timedelta(seconds=5), "please fix the lobby NPC")]))))
    e = _claimed()
    cases.append(("the command quoted by the ASSISTANT, not submitted",
                  ep_.observe_worker_start(e, _transcript([_row("assistant", t0 + timedelta(seconds=5), f"next I will run {CMD}")]))))
    control = _claimed()
    started = ep_.observe_worker_start(
        control, _transcript([_row("user", t0 + timedelta(seconds=5), f"<command-name>{CMD}</command-name>")]))
    false_starts = [name for name, got in cases if got]
    if not false_starts and started and control.state == ep_.STARTED:
        ok("V-EPOCH-STARTED-ONLY-ON-CLAIMED-COMMAND", "3 look-alikes refused; the real submit STARTED")
    else:
        bad("V-EPOCH-STARTED-ONLY-ON-CLAIMED-COMMAND", f"false starts={false_starts} control={started}")

    # --- an unclaimed epoch never starts, whatever the transcript says -------
    unclaimed = ep_.prepare(g, "gsd_long", ["DO-GATE"], "d", command=CMD)
    if not ep_.observe_worker_start(unclaimed, _transcript([_row("user", datetime.now(timezone.utc) + timedelta(seconds=5), f"<command-name>{CMD}</command-name>")])):
        ok("V-EPOCH-UNCLAIMED-NEVER-STARTS", "PREPARED stays PREPARED")
    else:
        bad("V-EPOCH-UNCLAIMED-NEVER-STARTS", "a transcript started an epoch nobody claimed")

    # --- one claim per epoch --------------------------------------------------
    e = _claimed()
    try:
        ep_.claim(e, "1111aaaa-2222-bbbb-3333-cccc4444dddd")
        bad("V-EPOCH-SINGLE-CLAIM", "second claim accepted")
    except PermissionError:
        ok("V-EPOCH-SINGLE-CLAIM", f"kept by {e.claimed_by[:8]}")

    # --- stale on revision; lease expiry; ends once with a reason -------------
    g2 = _goal()
    e = ep_.prepare(g2, "verify", ["DO-GATE"], "d")
    fresh = not ep_.is_stale(e, g2)
    gl.revise(g2, "Prove the wiring and dispatch every role once.")
    if fresh and ep_.is_stale(e, g2):
        ok("V-EPOCH-STALE-WHEN-GOAL-REVISES", "fresh at rev 1, STALE at rev 2")
    else:
        bad("V-EPOCH-STALE-WHEN-GOAL-REVISES", f"fresh={fresh}")

    e = _claimed()
    later = datetime.now(timezone.utc) + timedelta(hours=25)
    if not ep_.lease_expired(e) and ep_.lease_expired(e, now=later):
        ok("V-EPOCH-LEASE-EXPIRES", "live now, expired at +25h")
    else:
        bad("V-EPOCH-LEASE-EXPIRES", e.lease_expires_at)

    e = ep_.prepare(g, "verify", ["DO-GATE"], "d")
    ep_.mark_started_autonomous(e)
    try:
        ep_.end(e, ep_.COMPLETED, "   ")
        no_reason_ok = False
    except ValueError:
        no_reason_ok = True
    ep_.end(e, ep_.COMPLETED, "verifier ran, rc=0")
    try:
        ep_.end(e, ep_.ABANDONED, "again")
        bad("V-EPOCH-ENDS-ONCE-WITH-A-REASON", "ended twice")
    except PermissionError:
        if no_reason_ok:
            ok("V-EPOCH-ENDS-ONCE-WITH-A-REASON", "blank outcome refused; second end refused")
        else:
            bad("V-EPOCH-ENDS-ONCE-WITH-A-REASON", "ended with a blank outcome")

    # --- persistence: round-trip, single writer, corrupt raises, per-goal list -
    e = ep_.save(ep_.prepare(g, "verify", ["DO-GATE"], "d"), expected_version=0)
    same = ep_.load(e.epoch_id).to_dict() == e.to_dict()
    a1, a2 = ep_.load(e.epoch_id), ep_.load(e.epoch_id)
    ep_.save(a1, expected_version=a2.version)
    try:
        ep_.save(a2, expected_version=a2.version)
        writer_ok = False
    except gs.ConflictError:
        writer_ok = True
    listed = [x.epoch_id for x in ep_.for_goal(g.goal_id)]
    (ep_._epochs_dir() / f"{e.epoch_id}.json").write_text("{", encoding="utf-8")
    try:
        ep_.load(e.epoch_id)
        corrupt_ok = False
    except RuntimeError:
        corrupt_ok = True
    if same and writer_ok and corrupt_ok and e.epoch_id in listed:
        ok("V-EPOCH-PERSISTENCE", "round-trip, single writer, corrupt raises, listed")
    else:
        bad("V-EPOCH-PERSISTENCE", f"same={same} writer={writer_ok} corrupt={corrupt_ok} listed={e.epoch_id in listed}")

    # ---------------------------------------------------------------------------
    # Added after tools/mutation_probe.py scored epoch.py 29/39 against the 10
    # gates above. Each closes a survivor classified as REAL; the equivalent ones
    # are recorded in the spec.
    # ---------------------------------------------------------------------------

    # --- a claimed session with no findable transcript has NOT started -------
    # The mutant returning True here survived: a caller trusting the bool would
    # have believed a run began that nobody observed.
    e = _claimed()
    e.claimed_by = "ffffffff-0000-0000-0000-00000000dead"   # no such transcript anywhere
    if ep_.observe_worker_start(e) is False and e.state == ep_.CLAIMED:
        ok("V-EPOCH-NO-TRANSCRIPT-IS-NOT-STARTED", "False, and still CLAIMED")
    else:
        bad("V-EPOCH-NO-TRANSCRIPT-IS-NOT-STARTED", f"state={e.state}")

    # --- an ENDED epoch never expires; an unclaimed one does, on its own lease --
    # PREPARED epochs carry a lease from birth now: one nobody claims must be
    # abandoned and replanned, not waited on forever.
    done = _claimed()
    ep_.end(done, ep_.COMPLETED, "finished")
    unclaimed = ep_.prepare(g, "gsd_long", ["DO-GATE"], "d", command=CMD)
    before = datetime.now(timezone.utc) + timedelta(hours=ep_.UNCLAIMED_LEASE_HOURS - 1)
    after = datetime.now(timezone.utc) + timedelta(hours=ep_.UNCLAIMED_LEASE_HOURS + 1)
    if (not ep_.lease_expired(done, now=after) and not ep_.lease_expired(unclaimed, now=before)
            and ep_.lease_expired(unclaimed, now=after)):
        ok("V-EPOCH-UNCLAIMED-EXPIRES-ENDED-NEVER",
           f"PREPARED live at {ep_.UNCLAIMED_LEASE_HOURS - 1}h, expired after; COMPLETED never")
    else:
        bad("V-EPOCH-UNCLAIMED-EXPIRES-ENDED-NEVER",
            f"done={ep_.lease_expired(done, now=after)} "
            f"unclaimed_before={ep_.lease_expired(unclaimed, now=before)} "
            f"unclaimed_after={ep_.lease_expired(unclaimed, now=after)}")

    # --- a fresh machine, and version counts writes ---------------------------
    prev = os.environ["GOAL_SPINE_STATE_DIR"]
    os.environ["GOAL_SPINE_STATE_DIR"] = str(Path(tempfile.mkdtemp()) / "no" / "such" / "dir")
    try:
        first = ep_.save(ep_.prepare(g, "verify", ["DO-GATE"], "d"), expected_version=0)
        second = ep_.save(ep_.load(first.epoch_id), expected_version=1)
        if first.version == 1 and second.version == 2:
            ok("V-EPOCH-FRESH-MACHINE-AND-VERSION-COUNTS-WRITES", "nested dir created; v1 -> v2")
        else:
            bad("V-EPOCH-FRESH-MACHINE-AND-VERSION-COUNTS-WRITES", f"{first.version} {second.version}")
    except OSError as exc:
        bad("V-EPOCH-FRESH-MACHINE-AND-VERSION-COUNTS-WRITES", repr(exc))
    finally:
        os.environ["GOAL_SPINE_STATE_DIR"] = prev

    total = len(passes) + len(fails)
    print(f"\nGOAL_EPOCH_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
