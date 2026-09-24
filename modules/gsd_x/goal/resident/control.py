#!/usr/bin/env python3
"""Recovery census (F9) and cancel-by-handle with an orphan census (F7).

CENSUS. On start, every non-terminal mission is classified:

  DONE        a receipt is available (the provider reports the run ended, or
              the mission already returned)
  INCOMPLETE  provably not started (no intent was ever written -- dispatch only
              ever follows an intent) or provably dead with no effect (the
              provider reports it lost AND its process group is empty)
  UNCERTAIN   anything else

An UNCERTAIN mission is reconciled against the PROVIDER'S OWN RECORD of the
attempt id (`probe`) before anything else happens to its goal. The census never
dispatches; a mission is never re-dispatched blind.

CANCEL. By handle, not by pgid alone: the provider's cancel (which kills the
POSIX process group), a scope-unit stop and a `claude stop <id>` when the record
carries one, then an orphan census of the process group. Every step's outcome is
recorded on the mission. A step that failed is a recorded failure and makes the
cancel NOT clean; it is never swallowed.
"""
from __future__ import annotations

import subprocess
import time

from .. import epoch as ep
from . import missions as ms
from . import procs

DONE, INCOMPLETE, UNCERTAIN = "DONE", "INCOMPLETE", "UNCERTAIN"
CLEAN, ORPHANS, UNJUDGED, NO_PGID = "CLEAN", "ORPHANS", "UNJUDGED", "NO_PGID"
# A cancel is clean only when every step succeeded AND the census is one of these.
# UNJUDGED (a pgid exists but this host cannot see process groups) is NOT clean.
CLEAN_CENSUS = frozenset({CLEAN, NO_PGID})


def run_command(argv: list, timeout: float = 60.0) -> tuple[int, str]:
    """The default command runner for unit/session stops."""
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout,
                           stdin=subprocess.DEVNULL)
    except FileNotFoundError as exc:
        return 127, f"{argv[0]}: not found ({exc})"
    except subprocess.TimeoutExpired:
        return 124, f"{argv[0]}: timed out after {timeout}s"
    return p.returncode, ((p.stdout or "") + (p.stderr or "")).strip()[:400]


def orphan_census(pgid, info: procs.ProcInfo) -> dict:
    if pgid is None:
        return {"status": NO_PGID, "pgid": None,
                "detail": "the handle exposes no process group; the provider's cancel is "
                          "the only stop there is"}
    members = info.pgid_members(pgid)
    if members is None:
        return {"status": UNJUDGED, "pgid": pgid,
                "detail": "process groups are not observable on this host"}
    if members:
        return {"status": ORPHANS, "pgid": pgid, "pids": members}
    return {"status": CLEAN, "pgid": pgid, "pids": []}


def cancel_by_handle(mission: dict, provider, info: procs.ProcInfo,
                     runner=run_command, grace_s: float = 0.5) -> dict:
    """Cancel one mission's run. Returns the record of every step."""
    steps = []
    handle = mission.get("handle")
    if provider is None:
        steps.append({"step": "provider_cancel", "ok": False,
                      "error": f"PROVIDER_UNAVAILABLE: {mission.get('provider')}"})
    elif not handle:
        steps.append({"step": "provider_cancel", "ok": False,
                      "error": "NO_HANDLE: nothing to cancel by"})
    else:
        try:
            provider.cancel(handle)
            steps.append({"step": "provider_cancel", "ok": True})
        except Exception as exc:        # any provider failure is RECORDED, then judged
            steps.append({"step": "provider_cancel", "ok": False,
                          "error": f"{exc.__class__.__name__}: {exc}"})
    unit = mission.get("scope_unit")
    if unit:
        rc, out = runner(["systemctl", "--user", "stop", str(unit)])
        steps.append({"step": "unit_stop", "unit": unit, "ok": rc == 0, "rc": rc,
                      "output": out})
    bg = mission.get("claude_bg_id")
    if bg:
        rc, out = runner(["claude", "stop", str(bg)])
        steps.append({"step": "claude_stop", "id": bg, "ok": rc == 0, "rc": rc, "output": out})
    if grace_s > 0 and mission.get("pgid") is not None:
        time.sleep(grace_s)                 # SIGKILL delivery is asynchronous
    census = orphan_census(mission.get("pgid"), info)
    failed = [s for s in steps if not s["ok"]]
    return {"ts": time.time(), "steps": steps, "orphan_census": census,
            "clean": not failed and census["status"] in CLEAN_CENSUS,
            "failures": [s.get("error") or f"{s['step']} rc={s.get('rc')}" for s in failed]
                        + ([f"orphans in pgid {census['pgid']}: {census['pids']}"]
                           if census["status"] == ORPHANS else [])
                        + ([f"pgid {census['pgid']} could not be censused on this host"]
                           if census["status"] == UNJUDGED else [])}


def classify(mission: dict, provider, intents, info: procs.ProcInfo) -> tuple[str, str]:
    state = mission.get("state")
    if state in (ms.RETURNED, ms.HARVESTED, ms.JUDGED):
        return DONE, f"already {state}: its receipt is available to the engine"
    if state == ms.PROPOSED:
        return INCOMPLETE, "proposed and never admitted: nothing was dispatched"
    if state in (ms.ADMITTED, ms.ISOLATED):
        if not intents.has(mission.get("attempt_id", "")):
            return INCOMPLETE, "no intent was written, and dispatch only ever follows one"
        return UNCERTAIN, ("intent recorded, no handle: the resident may have died inside "
                           "dispatch")
    if provider is None:
        return UNCERTAIN, f"PROVIDER_UNAVAILABLE: {mission.get('provider')}"
    try:
        obs = provider.observe(mission.get("handle") or {})
    except Exception as exc:          # an unreadable observation is not an ending
        return UNCERTAIN, f"observe raised {exc.__class__.__name__}: {exc}"
    if obs.state == ep.OBS_ENDED:
        return DONE, f"provider reports it ended {obs.outcome}"
    if obs.state == ep.OBS_LOST:
        census = orphan_census(mission.get("pgid"), info)
        if census["status"] == CLEAN:
            return INCOMPLETE, "provider reports it lost and its process group is empty"
        if census["status"] == ORPHANS:
            return UNCERTAIN, f"provider reports it lost, but pgid holds {census['pids']}"
        return UNCERTAIN, "provider reports it lost; its process group cannot be observed here"
    if obs.state == ep.OBS_RUNNING:
        verdict, why = procs.liveness(mission.get("pid"), mission.get("start_time"), info)
        if verdict == procs.DEAD:
            return UNCERTAIN, f"provider says running but {why}"
        return UNCERTAIN, f"IN_FLIGHT: provider says running ({why}); adopted, never re-dispatched"
    return UNCERTAIN, f"provider observation {obs.state}: {obs.detail}"


def census(store_: ms.MissionStore, providers: dict, intents, info: procs.ProcInfo) -> list:
    """Classify and reconcile every non-terminal mission. Returns one row each."""
    rows = []
    for m in store_.non_terminal():
        prov = providers.get(m.get("provider"))
        label, why = classify(m, prov, intents, info)
        row = {"mission": m["id"], "goal": m.get("goal"), "from": m["state"],
               "classification": label, "reason": why, "action": ""}
        if label == DONE:
            if m["state"] in (ms.DISPATCHED, ms.RUNNING):
                store_.advance(m["id"], ms.RETURNED)
                row["action"] = "RETURNED: the engine harvests it next cycle"
            else:
                row["action"] = "left for the engine's harvest"
        elif label == INCOMPLETE:
            store_.advance(m["id"], ms.LOST, lost_reason=why)
            row["action"] = "LOST; the engine resolves its epoch through its own recovery"
        elif m["state"] in (ms.ADMITTED, ms.ISOLATED):
            # Reconcile against the provider's own record of this attempt id.
            if prov is None:
                store_.advance(m["id"], ms.UNCERTAIN, uncertain=list(m.get("uncertain") or [])
                               + [why])
                row["action"] = "UNCERTAIN (terminal): no provider to ask; blocks its goal"
            else:
                try:
                    found = prov.probe(m.get("identity") or {})
                except Exception as exc:     # the provider could not answer: recorded
                    store_.advance(m["id"], ms.UNCERTAIN,
                                   uncertain=list(m.get("uncertain") or [])
                                   + [f"probe raised {exc.__class__.__name__}: {exc}"])
                    row["action"] = "UNCERTAIN (terminal): probe failed; blocks its goal"
                else:
                    if found is not None:
                        store_.advance(m["id"], ms.DISPATCHED, handle=found,
                                       pid=found.get("pid"),
                                       uncertain=list(m.get("uncertain") or []) + [why])
                        row["action"] = "ADOPTED: the provider's record shows the run"
                    else:
                        store_.advance(m["id"], ms.LOST,
                                       lost_reason="provider record: no run for this attempt",
                                       uncertain=list(m.get("uncertain") or []) + [why])
                        row["action"] = ("LOST: the provider's record shows no run; the "
                                         "engine's info key refuses a blind retry")
        else:
            store_.advance(m["id"], uncertain=list(m.get("uncertain") or []) + [why])
            row["action"] = "flagged; the engine keeps observing it and dispatches nothing"
        rows.append(row)
    return rows
