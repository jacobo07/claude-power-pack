#!/usr/bin/env python
"""mission_supersede -- retire a mission whose owner is proven dead, without erasing it.

Why this exists: `gsdx_chain` arms nothing while any non-terminal mission holds the programme
root (one writer). A mission whose owner died and whose own authority is exhausted stays
RUNNING forever: `plan_next` holds it before its `replace` rule can fire, and the CLI has no verb
that ends it. This verb is that missing edge, and nothing else.

Contract:
  * DRY-RUN by default; `--apply` writes.
  * Refuses unless `gsd_mission.liveness` says DEAD. ALIVE, WAITING_HUMAN and UNKNOWN all refuse:
    UNKNOWN never licenses an action on a worker that may still be running.
  * The target state is ORPHANED (owner proven dead, replacement not allowed), the terminal
    value `gsdx_chain` and `gsd_mission` already read as TERMINAL. Authority, spend, owner and
    evidence stay on the record; the supersession is added beside them.
  * Goes through `gsd_mission.transition`, so it is a compare-and-swap under the mission lock
    and writes one ledger row (event `mission_superseded`). A record that moved between the
    read and the write is refused, not overwritten.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_mission as gm  # noqa: E402

EVENT = "mission_superseded"
NO_SUCCESSOR = "none"


def supersede(mission_id: str, *, by: str, reason: str, apply: bool = False,
              sessions: list[dict] | None = None, pid_alive=None, now: float | None = None) -> dict:
    """Judge (and, with ``apply``, commit) the retirement of ``mission_id``.

    ``sessions`` is the host's session list; None means the host could not be asked, which
    liveness reads as UNKNOWN and this function therefore refuses.
    Returns {"ok", "applied", "reason", ...}; never raises for a refusal."""
    if not (reason or "").strip():
        return _refuse(mission_id, "a reason is required")
    try:
        rec = gm.load(mission_id)
    except gm.MissionError as e:
        return _refuse(mission_id, f"unreadable mission: {e}")
    if rec is None:
        return _refuse(mission_id, "no such mission")
    if rec["state"] in gm.TERMINAL:
        return {"ok": True, "applied": False, "mission_id": mission_id, "state": rec["state"],
                "reason": "already terminal; nothing to do"}
    if by != NO_SUCCESSOR:
        if by == mission_id:
            return _refuse(mission_id, "a mission cannot supersede itself")
        try:
            other = gm.load(by)
        except gm.MissionError as e:
            return _refuse(mission_id, f"successor unreadable: {e}")
        if other is None:
            return _refuse(mission_id, f"successor {by} does not exist")
    kwargs = {} if pid_alive is None else {"pid_alive": pid_alive}
    verdict, why = gm.liveness(rec.get("owner"), sessions, **kwargs)
    if verdict != gm.DEAD:
        return _refuse(mission_id, f"owner is {verdict}, not DEAD: {why}", verdict=verdict)
    plan = {"ok": True, "applied": False, "mission_id": mission_id, "epoch": rec["epoch"],
            "from_state": rec["state"], "to_state": gm.ORPHANED, "superseded_by": by,
            "owner_evidence": why, "reason": "dry-run: pass --apply to write"}
    if not apply:
        return plan
    stamp = time.time() if now is None else now
    try:
        out = gm.transition(
            mission_id, expect_epoch=rec["epoch"], expect_state=rec["state"], event=EVENT, now=stamp,
            state=gm.ORPHANED, superseded_by=by, superseded_at=stamp,
            supersede_reason=reason.strip(), supersede_owner_evidence=why, pending=None,
            reason=f"superseded by {by}: {reason.strip()}",
            ledger_extra={"superseded_by": by, "owner_evidence": why, "from_state": rec["state"]})
    except gm.CasConflict as e:
        return _refuse(mission_id, f"record moved before the write: {e}")
    plan.update(applied=True, seq=out["seq"], reason="superseded")
    return plan


def _refuse(mission_id: str, reason: str, **extra) -> dict:
    return {"ok": False, "applied": False, "mission_id": mission_id, "reason": reason, **extra}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("supersede")
    s.add_argument("mission_id")
    s.add_argument("--by", required=True, help="the mission that continues the work, or 'none'")
    s.add_argument("--reason", required=True)
    s.add_argument("--apply", action="store_true", help="write; without it this is a dry run")
    a = ap.parse_args(argv)
    res = supersede(a.mission_id, by=a.by, reason=a.reason, apply=a.apply, sessions=gm.host_sessions())
    print(json.dumps(res, indent=1))
    return 0 if res["ok"] else 3


if __name__ == "__main__":
    sys.exit(main())
