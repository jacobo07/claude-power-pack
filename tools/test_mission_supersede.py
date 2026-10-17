#!/usr/bin/env python
"""V-SUPERSEDE-* gates for tools/mission_supersede.py. Hermetic: a throwaway state dir, no host calls."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

TMP = tempfile.mkdtemp(prefix="supersede-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP

import gsd_long_run as lr  # noqa: E402
import gsd_mission as gm  # noqa: E402
import gsdx_chain  # noqa: E402
import mission_supersede as ms  # noqa: E402

passes = 0
fails = 0


def _ok(gate: str, evidence: str) -> None:
    global passes
    passes += 1
    print(f"PASS {gate}: {evidence}")


def _fail(gate: str, diag: str) -> None:
    global fails
    fails += 1
    print(f"FAIL {gate}: {diag}")


def check(gate: str, cond: bool, evidence: str, diag: str = "") -> None:
    (_ok if cond else _fail)(gate, evidence if cond else (diag or evidence))


def make(mid: str, sid: str, state: str = gm.RUNNING, epoch: int = 2) -> None:
    rec = {"schema_version": 1, "mission_id": mid, "epoch": epoch, "state": state, "seq": 3,
           "cwd": "C:/programme/root", "created_at": time.time() - 100, "updated_at": time.time() - 50,
           "owner": {"session_id": sid, "kind": "interactive"},
           "authority": {"tokens": 12_000_000}, "spent": 17_019_507,
           "pending": {"bg_id": "x", "deadline": 1.0}}
    gm.mission_path(mid).write_text(json.dumps(rec), encoding="utf-8")


def raw(mid: str) -> dict:
    return json.loads(gm.mission_path(mid).read_text(encoding="utf-8"))


STOPPED = [{"sessionId": "dead-1", "state": "stopped"}]
LIVE = [{"sessionId": "live-1", "state": "running", "status": "busy"}]
WAITING = [{"sessionId": "wait-1", "state": "running", "waitingFor": "permission"}]


def main() -> int:
    # Arrange: a dead owner, a successor, a live owner, a waiting owner
    make("m-dead", "dead-1")
    make("m-succ", "live-1", epoch=1)
    make("m-live", "live-1")
    make("m-wait", "wait-1")
    before = raw("m-dead")

    # Act / Assert 1: dry-run is the default and writes nothing
    r = ms.supersede("m-dead", by="m-succ", reason="zombie", sessions=STOPPED)
    check("V-SUPERSEDE-DRYRUN", r["ok"] and not r["applied"] and raw("m-dead") == before
          and not lr.ledger_events("m-dead"),
          "dry-run reported the plan and left record and ledger untouched", f"got {r}")

    # 2: apply -> ORPHANED, authority/spend/owner preserved, successor and evidence recorded
    r = ms.supersede("m-dead", by="m-succ", reason="zombie", apply=True, sessions=STOPPED)
    after = raw("m-dead")
    check("V-SUPERSEDE-APPLY", r["applied"] and after["state"] == gm.ORPHANED
          and after["superseded_by"] == "m-succ" and after["supersede_reason"] == "zombie",
          "state ORPHANED with successor and reason recorded", f"got {r} / {after.get('state')}")
    check("V-SUPERSEDE-PRESERVES", all(after[k] == before[k] for k in ("authority", "spent", "owner", "cwd", "epoch")),
          "authority, spend, owner, cwd and epoch unchanged", "evidence fields were altered")
    rows = [e for e in lr.ledger_events("m-dead") if e.get("event") == ms.EVENT]
    check("V-SUPERSEDE-LEDGER", len(rows) == 1 and rows[0].get("superseded_by") == "m-succ",
          "exactly one mission_superseded ledger row", f"rows={rows}")
    check("V-SUPERSEDE-CHAIN-TERMINAL", after["state"] in gsdx_chain.TERMINAL,
          "gsdx_chain reads the result as TERMINAL (frees the one-writer rule)",
          f"{after['state']} not in {gsdx_chain.TERMINAL}")

    # 3: idempotent on a terminal mission
    r = ms.supersede("m-dead", by="m-succ", reason="again", apply=True, sessions=STOPPED)
    check("V-SUPERSEDE-IDEMPOTENT", r["ok"] and not r["applied"] and raw("m-dead")["seq"] == after["seq"],
          "second call is a no-op", f"got {r}")

    # 4: the control the refusals need -- a LIVE owner is refused and untouched
    live_before = raw("m-live")
    r = ms.supersede("m-live", by="m-succ", reason="x", apply=True, sessions=LIVE)
    check("V-SUPERSEDE-REFUSES-LIVE", not r["ok"] and raw("m-live") == live_before,
          "a LIVE owner is refused and the record is byte-identical", f"got {r}")
    wait_before = raw("m-wait")
    r = ms.supersede("m-wait", by="m-succ", reason="x", apply=True, sessions=WAITING)
    check("V-SUPERSEDE-REFUSES-WAITING", not r["ok"] and raw("m-wait") == wait_before,
          "an owner waiting on a human is refused", f"got {r}")
    r = ms.supersede("m-live", by="m-succ", reason="x", apply=True, sessions=None)
    check("V-SUPERSEDE-REFUSES-UNKNOWN", not r["ok"] and r.get("verdict") == gm.UNKNOWN
          and raw("m-live") == live_before,
          "host unreachable reads UNKNOWN and refuses", f"got {r}")

    # 5: successor validation
    make("m-orph", "dead-1")
    check("V-SUPERSEDE-SUCCESSOR-MISSING",
          not ms.supersede("m-orph", by="m-nope", reason="x", apply=True, sessions=STOPPED)["ok"]
          and raw("m-orph")["state"] == gm.RUNNING, "unknown successor refused", "applied despite missing successor")
    check("V-SUPERSEDE-SELF", not ms.supersede("m-orph", by="m-orph", reason="x", sessions=STOPPED)["ok"],
          "self-supersession refused", "self-supersession allowed")
    check("V-SUPERSEDE-NO-REASON", not ms.supersede("m-orph", by="none", reason=" ", sessions=STOPPED)["ok"],
          "empty reason refused", "empty reason accepted")
    r = ms.supersede("m-orph", by=ms.NO_SUCCESSOR, reason="no successor", apply=True, sessions=STOPPED)
    check("V-SUPERSEDE-NONE-OK", r["applied"] and raw("m-orph")["superseded_by"] == "none",
          "`--by none` retires without a successor", f"got {r}")

    # 6: a record that moved between read and write is refused, not overwritten
    make("m-race", "dead-1")
    real = gm.transition

    def moved(*a, **k):
        raise gm.CasConflict("moved")
    gm.transition = moved
    try:
        r = ms.supersede("m-race", by="none", reason="x", apply=True, sessions=STOPPED)
    finally:
        gm.transition = real
    check("V-SUPERSEDE-CAS", not r["ok"] and "moved" in r["reason"] and raw("m-race")["state"] == gm.RUNNING,
          "CAS conflict is a refusal and the record is untouched", f"got {r}")

    # 7: CLI exit code on a refusal (host unreachable -> UNKNOWN -> exit 3)
    real_hs = gm.host_sessions
    gm.host_sessions = lambda *a, **k: None
    try:
        rc = ms.main(["supersede", "m-live", "--by", "none", "--reason", "x", "--apply"])
    finally:
        gm.host_sessions = real_hs
    check("V-SUPERSEDE-CLI-EXIT", rc == 3 and raw("m-live") == live_before,
          "CLI exits 3 on refusal and writes nothing", f"rc={rc}")

    # 8: never-launched stub proof (failed arm-chain). Positive control and each clause's negative.
    def stub(mid: str, **over) -> None:
        make(mid, "x", state=gm.PREPARED, epoch=0)
        rec = raw(mid)
        rec.update(owner=None, pending=None,
                   owner_hold={"reason": "arm-chain failed: MissionError: route RECOMPILE", "set_at": 1.0})
        rec.update(over)
        gm.mission_path(mid).write_text(json.dumps(rec), encoding="utf-8")
        for ev in ("mission_prepared", "envelope_set", "route_admission", "owner_hold_set"):
            lr.ledger_append(mid, ev, mission_id=mid)

    stub("m-stub")
    r = ms.supersede("m-stub", by="none", reason="failed arm stub", apply=True, sessions=LIVE)
    check("V-SUPERSEDE-STUB-OK", r["applied"] and raw("m-stub")["state"] == gm.ORPHANED
          and "never launched" in raw("m-stub")["supersede_owner_evidence"],
          "a never-launched failed-arm stub is retired", f"got {r}")
    stub("m-stub-own", owner={"session_id": "live-1", "kind": "interactive"})
    stub("m-stub-ep", epoch=1)
    stub("m-stub-hold", owner_hold={"reason": "owner paused", "set_at": 1.0})
    stub("m-stub-pend", pending={"bg_id": "abc", "deadline": 1.0})
    stub("m-stub-ev")
    lr.ledger_append("m-stub-ev", "launched", mission_id="m-stub-ev")
    for mid in ("m-stub-own", "m-stub-ep", "m-stub-hold", "m-stub-pend", "m-stub-ev"):
        b = raw(mid)
        r = ms.supersede(mid, by="none", reason="x", apply=True, sessions=LIVE)
        check(f"V-SUPERSEDE-STUB-REFUSES-{mid[7:].upper()}", not r["ok"] and raw(mid) == b,
              "stub proof fails on this clause and the record is untouched", f"got {r}")

    print(f"SUPERSEDE_PASS={passes}/{passes + fails}  threshold=all")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
