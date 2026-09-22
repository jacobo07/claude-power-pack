#!/usr/bin/env python3
"""Observe a /cpp-gsd-long run as one epoch of a goal. OBSERVE ONLY.

`/cpp-gsd-long` is a long-horizon Claude execution provider, and its lifetime is
NOT the goal's: a run is one bounded epoch, the goal outlives it. This adapter
projects that run's own ledger into epoch states. It reimplements none of the
run's machinery, writes nothing to the marker and touches no threshold.

It cannot START a run, and says so rather than pretending. A resume is delivered
by typing into the pane that owns the session (certification C5), so only a
human with that pane can arm one; an adapter that "started" a run by writing a
marker would arm compaction survival for a run that never began -- the exact
state that certification measured on 4 of 9 markers in this estate.

So `dispatch` BINDS an already-armed session, and refuses one that does not
exist. The distinction that matters downstream: a run ending is not the goal
converging, and this adapter reports only what the ledger says.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from ..epoch import (CANCELLED, COMPLETED, EXPIRED, LOST, OBS_ENDED, OBS_LOST,
                     OBS_RUNNING, OBS_UNKNOWN, STALE_REVISION, EpochError,
                     Observation, Receipt)

_TOOLS = Path(__file__).resolve().parents[4] / "tools"


def _long_run():
    """Import the real tool rather than restating what it knows."""
    if str(_TOOLS) not in sys.path:
        sys.path.insert(0, str(_TOOLS))
    import gsd_long_run  # noqa: PLC0415
    return gsd_long_run


# The ledger's own vocabulary, mapped to epoch endings. `halted` carries a kind:
# a spent budget is an EXPIRED epoch, a mission that no longer matches is a
# STALE_REVISION one, and those need different reactions from the reconciler.
TERMINAL = {"finished": COMPLETED, "reaped": LOST, "cleared": CANCELLED}


class LongRunProvider:
    """Binds and observes a /cpp-gsd-long session. Never starts or stops one."""

    name = "cpp-gsd-long"

    def __init__(self, run_dir: Path, wall_bound_s: float = 24 * 3600.0):
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        # The run's own budget (default 24 h) bounds it; this is the epoch's
        # outer bound, not a second budget competing with the marker's.
        self.wall_bound_s = float(wall_bound_s)

    def _marker(self, run_token: str) -> Path:
        return self.run_dir / f"longrun-{run_token}.json"

    def dispatch(self, spec: dict) -> dict:
        """Bind an EXISTING armed session to this epoch."""
        sid = (spec.get("bind_session") or "").strip()
        if not sid:
            raise EpochError(
                "this provider cannot start a /cpp-gsd-long run: a resume is typed into "
                "the pane that owns the session, so only a human with that pane can arm "
                "one. Pass bind_session=<session id> to observe a run that exists.")
        lr = _long_run()
        if not lr.ledger_events(sid):
            raise EpochError(f"no /cpp-gsd-long ledger rows for session {sid}; "
                             "nothing to bind (arm the run first)")
        token = spec["identity"]["run_token"]
        self._marker(token).write_text(json.dumps({"session_id": sid, "bound_at": time.time()}),
                                       encoding="utf-8")
        return {"session_id": sid, "token": token, "bound_at": time.time()}

    def observe(self, handle: dict) -> Observation:
        lr = _long_run()
        rows = lr.ledger_events(handle["session_id"])
        if not rows:
            # We could not ask, or the ledger was rotated. Not "lost": that
            # would end an epoch whose run may be perfectly alive.
            return Observation(OBS_UNKNOWN, "", "no ledger rows for this session")
        for row in reversed(rows):
            ev = row.get("event")
            if ev == "halted":
                kind = (row.get("kind") or "").lower()
                outcome = STALE_REVISION if kind == "mission" else EXPIRED
                return Observation(OBS_ENDED, outcome, row.get("reason", "halted"))
            if ev in TERMINAL:
                return Observation(OBS_ENDED, TERMINAL[ev], row.get("reason", ev))
        return Observation(OBS_RUNNING, "", f"{len(rows)} ledger rows, none terminal")

    def harvest(self, handle: dict, spec: dict) -> Receipt:
        lr = _long_run()
        sid = handle["session_id"]
        rows = lr.ledger_events(sid)
        crossings = sum(1 for r in rows if r.get("event") == "crossing")
        confirmed = sum(1 for r in rows if r.get("event") == "resume_confirmed")
        failures = [{"summary": f"{r['event']}: {r.get('reason', '')}"[:200],
                     "signature": f"longrun-{r['event']}:{sid[:8]}"}
                    for r in rows if r.get("event") in ("halted", "stalled", "reaped",
                                                        "delivery_blocked")]
        # NO verdicts. A long run is work, not proof: whatever it produced is
        # evidenced by gate epochs against the tree it left behind. Emitting a
        # verdict here would let "the run ended" satisfy an obligation.
        return Receipt(spec["epoch_id"], self.name, spec["revision"],
                       head_before=spec.get("head_before", ""),
                       tree_before=spec.get("tree_before", ""),
                       failures=failures,
                       cost={"crossings": crossings, "resumes_confirmed": confirmed,
                             "ledger_rows": len(rows)},
                       narrative=f"/cpp-gsd-long session {sid}: {crossings} crossings, "
                                 f"{confirmed} confirmed resumes")

    def cancel(self, handle: dict) -> None:
        """Refused on purpose. Clearing another session's marker mid-run would
        strand a live pane: ending a run is `/cpp-gsd-long --restore` in the
        pane that owns it."""
        raise EpochError(
            f"this provider does not stop session {handle.get('session_id')}: the run is "
            "owned by the pane it types into. End it there, or let its budget expire.")

    def probe(self, identity: dict) -> dict | None:
        marker = self._marker(identity.get("run_token", ""))
        if not marker.is_file():
            return None
        try:
            data = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return {"session_id": data["session_id"], "token": identity["run_token"],
                "bound_at": data.get("bound_at", 0)}
