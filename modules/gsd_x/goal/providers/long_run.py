#!/usr/bin/env python3
"""A /cpp-gsd-long run as one epoch of a goal: bind a v2 run, or arm a v3 mission.

`/cpp-gsd-long` is a long-horizon Claude execution provider, and its lifetime is
NOT the goal's: a run is one bounded epoch, the goal outlives it.

Two shapes, and they differ in who owns the start:

  * **v2 bind (`bind_session`)** -- a compact-and-resume run whose resumes are
    typed into the pane that owns the session. Only a human with that pane can
    arm one, so this provider BINDS an already-armed session and observes its
    ledger; it never starts, stops or retunes it.
  * **v3 mission (`mission={cwd, command, ...}`)** -- UWCP S1-11. A Ralph
    mission (`tools/gsd_mission.py`) owns its own relay: fresh `claude --bg`
    workers, an epoch/CAS record, host-witnessed liveness. The goal CAN start
    one, because nothing about it depends on a pane. The mission id is derived
    from the epoch's pre-minted run_token, so intent-before-effect recovery
    (`probe`) finds a mission armed just before a crash instead of arming a
    second one.

Observation keeps ARMED apart from RUNNING: a PREPARED or LAUNCHING mission is an
epoch in flight whose worker has not acknowledged, and its detail says so. Only
the mission's own terminal states end the epoch. A run ending is not the goal
converging, and this provider emits no verdicts: gate epochs prove work.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from ..epoch import (CANCELLED, COMPLETED, EXPIRED, LOST, OBS_ENDED, OBS_LOST,
                     OBS_RUNNING, OBS_UNKNOWN, STALE_REVISION, EpochError,
                     Observation, Receipt, echo)

_TOOLS = Path(__file__).resolve().parents[4] / "tools"
CANCEL_REASON = "goal cancelled by operator"


def _tools_import(name: str):
    """Import the real tool rather than restating what it knows."""
    if str(_TOOLS) not in sys.path:
        sys.path.insert(0, str(_TOOLS))
    return __import__(name)


def _long_run():
    return _tools_import("gsd_long_run")


def _mission():
    return _tools_import("gsd_mission")


def mission_id_for(run_token: str) -> str:
    """Deterministic from the epoch's pre-minted identity -- the probe key."""
    return f"m-{run_token[:12]}"


# The ledger's own vocabulary, mapped to epoch endings. `halted` carries a kind:
# a spent budget is an EXPIRED epoch, a mission that no longer matches is a
# STALE_REVISION one, and those need different reactions from the reconciler.
TERMINAL = {"finished": COMPLETED, "reaped": LOST, "cleared": CANCELLED}

# v3 mission states that mean "in flight, NOT yet started": ARMED is not RUNNING.
_NOT_STARTED = {"PREPARED": "armed, no worker launched yet",
                "LAUNCHING": "a worker was requested; no acknowledgement from it yet"}


class LongRunProvider:
    """Binds a v2 /cpp-gsd-long session, or arms and observes a v3 mission."""

    name = "cpp-gsd-long"

    def __init__(self, run_dir: Path, wall_bound_s: float = 24 * 3600.0):
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        # The run's own budget (default 24 h) bounds it; this is the epoch's
        # outer bound, not a second budget competing with the marker's.
        self.wall_bound_s = float(wall_bound_s)

    def _marker(self, run_token: str) -> Path:
        return self.run_dir / f"longrun-{run_token}.json"

    # --- dispatch -------------------------------------------------------------

    def dispatch(self, spec: dict) -> dict:
        sid = (spec.get("bind_session") or "").strip()
        mission = spec.get("mission")
        if sid:
            return self._bind_v2(spec, sid)
        if not mission:
            raise EpochError(
                "this provider cannot start a /cpp-gsd-long run without a mission spec: pass "
                "mission={cwd, command, ...} to arm a v3 mission (fresh background workers), "
                "or bind_session=<session id> to observe a v2 run a human armed in its pane")
        return self._arm_v3(spec, mission)

    def _bind_v2(self, spec: dict, sid: str) -> dict:
        lr = _long_run()
        if not lr.ledger_events(sid):
            raise EpochError(f"no /cpp-gsd-long ledger rows for session {sid}; "
                             "nothing to bind (arm the run first)")
        token = spec["identity"]["run_token"]
        self._marker(token).write_text(json.dumps({"session_id": sid, "bound_at": time.time()}),
                                       encoding="utf-8")
        return {"session_id": sid, "token": token, "bound_at": time.time()}

    def _arm_v3(self, spec: dict, m: dict) -> dict:
        if not m.get("cwd") or not m.get("command"):
            raise EpochError("mission spec needs cwd and command")
        token = spec["identity"]["run_token"]
        mid = mission_id_for(token)
        gm = _mission()
        # Marker first: if we die between arm and return, probe still finds it.
        self._marker(token).write_text(json.dumps({"mission_id": mid, "bound_at": time.time()}),
                                       encoding="utf-8")
        try:
            gm.arm(m["cwd"], m["command"], mission_id=mid, launch=bool(m.get("launch", True)),
                   workstream=m.get("workstream"), mission_terms=m.get("mission_terms"),
                   max_cycles=m.get("max_cycles"), max_hours=m.get("max_hours"),
                   permission_mode=m.get("permission_mode"))
        except gm.MissionError as exc:
            raise EpochError(f"mission {mid} could not be armed: {exc}") from exc
        return {"mission_id": mid, "token": token, "bound_at": time.time()}

    # --- observe --------------------------------------------------------------

    def observe(self, handle: dict) -> Observation:
        if handle.get("mission_id"):
            return self._observe_v3(handle["mission_id"])
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

    def _observe_v3(self, mid: str) -> Observation:
        gm = _mission()
        try:
            rec = gm.load(mid)
        except (gm.MissionError, OSError, ValueError) as exc:
            return Observation(OBS_UNKNOWN, "", f"mission {mid} unreadable: {exc}")
        if rec is None:
            return Observation(OBS_UNKNOWN, "", f"mission {mid} has no record")
        st = rec["state"]
        if st in _NOT_STARTED:
            return Observation(OBS_RUNNING, "", f"{st}: {_NOT_STARTED[st]} (not started)")
        if st == "COMPLETED":
            return Observation(OBS_ENDED, COMPLETED, "mission completed")
        if st == "HALTED":
            why = str(rec.get("reason") or rec.get("note") or "halted")
            outcome = CANCELLED if CANCEL_REASON in why else EXPIRED
            return Observation(OBS_ENDED, outcome, why[:200])
        if st == "ORPHANED":
            return Observation(OBS_LOST, LOST, "mission orphaned: owner proven dead, "
                                               "replacement not allowed")
        if st == "BLOCKED":
            return Observation(OBS_RUNNING, "", "BLOCKED: the worker waits on a human")
        return Observation(OBS_RUNNING, "", f"{st}: worker epoch {rec.get('epoch')}, "
                                            f"{rec.get('iterations', 0)} iteration(s)")

    # --- harvest --------------------------------------------------------------

    def harvest(self, handle: dict, spec: dict) -> Receipt:
        if handle.get("mission_id"):
            return self._harvest_v3(handle["mission_id"], spec)
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
        return Receipt(spec["epoch_id"], self.name, spec["revision"], **echo(spec),
                       head_before=spec.get("head_before", ""),
                       tree_before=spec.get("tree_before", ""),
                       failures=failures,
                       cost={"crossings": crossings, "resumes_confirmed": confirmed,
                             "ledger_rows": len(rows)},
                       narrative=f"/cpp-gsd-long session {sid}: {crossings} crossings, "
                                 f"{confirmed} confirmed resumes")

    def _harvest_v3(self, mid: str, spec: dict) -> Receipt:
        from ..git_state import head  # noqa: PLC0415
        rec = _mission().load(mid) or {}
        failures = []
        if rec.get("state") in ("HALTED", "ORPHANED"):
            why = str(rec.get("reason") or rec.get("note") or rec.get("state"))
            failures.append({"summary": f"mission {rec.get('state')}: {why}"[:200],
                             "signature": f"mission-{str(rec.get('state')).lower()}:{mid}"})
        cwd = rec.get("cwd") or ""
        return Receipt(spec["epoch_id"], self.name, spec["revision"], **echo(spec),
                       head_before=spec.get("head_before", ""),
                       head_after=head(Path(cwd)) if cwd else "",
                       tree_before=spec.get("tree_before", ""), failures=failures,
                       cost={"mission_id": mid, "state": rec.get("state", "UNKNOWN"),
                             "iterations": rec.get("iterations", 0),
                             "worker_epochs": rec.get("epoch", 0)},
                       narrative=f"/cpp-gsd-long mission {mid}: {rec.get('state', 'UNKNOWN')}, "
                                 f"{rec.get('iterations', 0)} worker iteration(s)")

    # --- cancel / probe ---------------------------------------------------------

    def cancel(self, handle: dict) -> None:
        if handle.get("mission_id"):
            gm = _mission()
            rec = gm.load(handle["mission_id"])
            if rec is None or rec["state"] in gm.TERMINAL:
                return
            try:
                # HALTED through the record's own CAS; the mission supervisor's
                # orphan reaping then stops a worker that is still alive.
                gm.transition(rec["mission_id"], expect_epoch=rec["epoch"],
                              expect_state=rec["state"], event="mission_halted",
                              state=gm.HALTED, pending=None, reason=CANCEL_REASON)
            except gm.CasConflict as exc:
                raise EpochError(f"mission {rec['mission_id']} moved while cancelling; "
                                 f"re-observe and cancel again ({exc})") from exc
            return
        # Refused on purpose for v2: clearing another session's marker mid-run
        # would strand a live pane. Ending a v2 run is `/cpp-gsd-long --restore`
        # in the pane that owns it.
        raise EpochError(
            f"this provider does not stop session {handle.get('session_id')}: the run is "
            "owned by the pane it types into. End it there, or let its budget expire.")

    def probe(self, identity: dict) -> dict | None:
        token = identity.get("run_token", "")
        marker = self._marker(token)
        if marker.is_file():
            try:
                data = json.loads(marker.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                data = {}
            if data.get("session_id"):
                return {"session_id": data["session_id"], "token": token,
                        "bound_at": data.get("bound_at", 0)}
        if token:
            try:
                rec = _mission().load(mission_id_for(token))
            except Exception:     # an unreadable record is not an adoptable one
                rec = None
            if rec is not None:
                return {"mission_id": rec["mission_id"], "token": token,
                        "bound_at": rec.get("created_at", 0)}
        return None
