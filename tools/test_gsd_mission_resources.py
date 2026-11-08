#!/usr/bin/env python
"""V-RES-* gates for typed resource requirements (stage M2 of the knowledge-acquisition plan).

A mission record may carry `requires`: [{id, kind, arg, obligation}]. The 5-minute sweep evaluates them with no
model call. Unmet -> owner_hold kind "resource" (wait type WAIT_RESOURCE, not an Owner wait, not a cost incident).
Met -> RESOURCE_AVAILABLE, hold lifted, the ordinary relay path launches the successor. Unmeasurable -> UNKNOWN,
which is never AVAILABLE. Different obligations are independent siblings.

Hermetic like test_gsd_mission_cost_hold.py; probes are injected so no gate reads this machine's RAM.
Mutation drill: GSD_MISSION_DRILL_DIR holding a mutated gsd_mission.py is imported instead of the real one.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="gsd-mission-res-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_MISSION_RECOVERY"] = "off"
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
import gsd_mission as gm  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None
try:
    import mission_resources as mres  # noqa: E402
except ImportError:
    mres = None

passes = fails = 0
NOW = 1_800_000_000.0
gone = lambda pid: False  # noqa: E731
OK_GSD = lambda cwd, workstream=None: {"outcome": "OK"}  # noqa: E731


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


RAM = [3.2]
PATHS: set[str] = set()
CALLS: list[str] = []
BOOM: list[str | None] = [None]


def _ram(arg):
    CALLS.append("ram")
    if BOOM[0]:
        raise RuntimeError(BOOM[0])
    return RAM[0]


def _install_probes() -> None:
    if mres is None:
        return
    mres.PROBES.update({"ram_free_gb": _ram,
                        "path_exists": lambda arg: (CALLS.append("path"), arg in PATHS)[1],
                        "no_process": lambda arg: (CALLS.append("proc"), 0)[1]})


def _running(mid: str, requires=None) -> dict:
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    owner = {"session_id": f"{mid}-w", "pid": None, "proc_start": None, "heartbeat_at": NOW,
             "epoch": 1, "kind": "background"}
    extra = {"requires": requires} if requires is not None else {}
    return gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW,
                         state=gm.RUNNING, epoch=1, max_hours=100.0, owner=owner, **extra)


def _req(oid, kind, arg, n=1):
    return {"id": f"{oid}-{kind}-{n}", "kind": kind, "arg": arg, "obligation": oid}


def _sup(launches: list) -> dict:
    # every fixture worker has finished its turn: the host lists it done, so the owner is positively DEAD
    done = [{"sessionId": f"{m['mission_id']}-w", "id": f"{m['mission_id']}-w"[:8], "kind": "background",
             "state": "done"} for m in gm.all_missions()]
    rows = gm.supervise(now=NOW, sessions=done, runner=lambda *a, **k: launches.append(a) or "",
                        stop_runner=lambda a: None, pid_alive=gone, gsd_status=OK_GSD,
                        fingerprint=lambda wd: None)
    return {r["mission_id"]: r for r in rows}


def _events(mid: str) -> list[str]:
    return [e.get("event") for e in gm.lr.ledger_events(mid)]


def main() -> int:
    _install_probes()
    check("V-RES-MODULE-PRESENT", mres is not None and hasattr(gm, "resource_gate"), "mission_resources + gm.resource_gate")
    check("V-RES-VOCAB", "WAIT_RESOURCE" in getattr(gm, "WAIT_TYPES", ())
          and "WAIT_RESOURCE" not in gm.OWNER_WAIT_TYPES, "WAIT_RESOURCE is a wait type but not an Owner wait")

    # 5. control (runs first, while no other mission exists to call a probe): a mission without `requires` runs
    # today's path; no probe, no field, no row.
    mid = "m-res-absent"
    _running(mid)
    CALLS.clear()
    launches: list = []
    row = _sup(launches).get(mid, {})
    rec = gm.load(mid)
    check("V-RES-ABSENT-FIELD-UNCHANGED", not CALLS and "requires" not in rec and "resource_eval" not in rec
          and not rec.get("owner_hold") and not any(str(e).startswith("RESOURCE") for e in _events(mid))
          and row.get("action") in ("relay", "replace", "launch", "settle", "halt"),
          f"calls={CALLS} action={row.get('action')}")

    # 1. unmet -> parked as WAIT_RESOURCE with the measured value; no relaunch, no cost incident.
    mid = "m-res-unmet"
    _running(mid, [_req("O-70", "ram_free_gb", 6)])
    RAM[0] = 3.2
    launches: list = []
    row = _sup(launches).get(mid, {})
    rec = gm.load(mid)
    hold = rec.get("owner_hold") or {}
    check("V-RES-UNMET-PARKS", hold.get("kind") == "resource" and hold.get("wait_type") == "WAIT_RESOURCE"
          and "3.2" in str(hold.get("reason")) and row.get("action") == "none" and not launches,
          f"hold={hold.get('kind')}/{hold.get('wait_type')} action={row.get('action')} launches={len(launches)} "
          f"reason={str(hold.get('reason'))[:100]}")
    evs = _events(mid)
    check("V-RES-UNMET-NOT-CAPITAL-NOT-INCIDENT", hold.get("wait_type") != "CAPITAL_EXHAUSTED"
          and "economic_incident" not in evs and not gm.is_cost_hold(hold) and hold.get("kind") == "resource", str(evs))
    row2 = _sup(launches).get(mid, {})
    check("V-RES-UNMET-STAYS-PARKED", row2.get("action") == "none" and not launches
          and (gm.load(mid).get("owner_hold") or {}).get("kind") == "resource", f"{row2.get('action')}")

    # 2. met on a later pass -> RESOURCE_AVAILABLE, hold cleared, ordinary relay proceeds.
    RAM[0] = 8.0
    row = _sup(launches).get(mid, {})
    rec = gm.load(mid)
    check("V-RES-MET-WAKES", "RESOURCE_AVAILABLE" in _events(mid) and not rec.get("owner_hold")
          and row.get("action") in ("relay", "replace", "launch"),
          f"events={_events(mid)[-4:]} hold={rec.get('owner_hold')} action={row.get('action')}")

    # 3. sibling independence: O-65 needs an absent path, O-70 only RAM (met) -> admissible; card names both.
    mid = "m-res-sib"
    _running(mid, [_req("O-65", "path_exists", "R:\\nope"), _req("O-70", "ram_free_gb", 6)])
    RAM[0] = 8.0
    launches = []
    _sup(launches)
    rec = gm.load(mid)
    ev = rec.get("resource_eval") or {}
    card = gm.render_card(rec)
    check("V-RES-SIBLING-INDEPENDENT", not rec.get("owner_hold") and ev.get("actionable") == ["O-70"]
          and ev.get("waiting") == ["O-65"] and "O-70" in card and "O-65" in card and "R:\\nope" in card,
          f"hold={rec.get('owner_hold')} eval={ev.get('actionable')}/{ev.get('waiting')}")
    PATHS.add("R:\\nope")
    check("V-RES-SIBLING-CONTROL-ALL-MET", mres is not None and mres.evaluate(rec["requires"])["waiting"] == [],
          "when the path exists nothing waits")
    PATHS.discard("R:\\nope")

    # 4. a probe that raises is UNKNOWN: parked, the error named, never AVAILABLE; recovery wakes it.
    mid = "m-res-unk"
    _running(mid, [_req("O-70", "ram_free_gb", 6)])
    BOOM[0] = "wmi down"
    launches = []
    row = _sup(launches).get(mid, {})
    rec = gm.load(mid)
    hold = rec.get("owner_hold") or {}
    blob = json.dumps(gm.lr.ledger_events(mid), default=str)
    check("V-RES-UNKNOWN-NOT-AVAILABLE", hold.get("kind") == "resource" and "RESOURCE_AVAILABLE" not in _events(mid)
          and "UNKNOWN" in str(hold.get("reason")) and "wmi down" in blob and not launches,
          f"hold={hold.get('kind')} reason={str(hold.get('reason'))[:100]}")
    BOOM[0] = None
    RAM[0] = 8.0
    _sup(launches)
    check("V-RES-UNKNOWN-CONTROL-WAKES", "RESOURCE_AVAILABLE" in _events(mid) and not gm.load(mid).get("owner_hold"),
          "a measurable value wakes it")

    # 6. a cost or Owner hold is never lifted by a met resource, and a cost hold set over a resource hold wins.
    for mid, kind in (("m-res-cost", "cost"), ("m-res-owner", None)):
        _running(mid, [_req("O-70", "ram_free_gb", 6)])
        gm.set_owner_hold(mid, "cost breaker: processed 9,000,000 > 2 x estimate 4,000,000" if kind else "Owner park",
                          now=NOW, kind=kind)
        RAM[0] = 8.0
        _sup([])
        rec = gm.load(mid)
        h = rec.get("owner_hold") or {}
        check(f"V-RES-COST-HOLD-WINS-{kind or 'owner'}", bool(h) and h.get("kind") == kind
              and "RESOURCE_AVAILABLE" not in _events(mid), f"hold={h.get('kind')}/{str(h.get('reason'))[:30]}")
    mid = "m-res-over"
    _running(mid, [_req("O-70", "ram_free_gb", 6)])
    RAM[0] = 3.0
    _sup([])
    gm.set_owner_hold(mid, "cost breaker: processed 9,000,000 > 2 x estimate 4,000,000", now=NOW, kind="cost")
    RAM[0] = 8.0
    _sup([])
    check("V-RES-COST-HOLD-WINS-OVER-RESOURCE", (gm.load(mid).get("owner_hold") or {}).get("kind") == "cost",
          f"{(gm.load(mid).get('owner_hold') or {}).get('kind')}")

    # 7. CLI: set/replace per obligation, siblings kept, --clear removes only that obligation.
    mid = "m-res-cli"
    _running(mid)
    py = [sys.executable, str(HERE / "gsd_mission.py")]
    run = lambda *a: subprocess.run([*py, *a], capture_output=True, text=True, timeout=120, env=os.environ)  # noqa: E731
    run("requires", "--mission", mid, "--obligation", "O-65", "--path", "R:\\hwf")
    r1 = run("requires", "--mission", mid, "--obligation", "O-70", "--ram-free-gb", "6", "--no-process", "electron")
    reqs = gm.load(mid).get("requires") or []
    k70 = sorted(r["kind"] for r in reqs if r["obligation"] == "O-70")
    check("V-RES-CLI-SET", r1.returncode == 0 and k70 == ["no_process", "ram_free_gb"]
          and [r["kind"] for r in reqs if r["obligation"] == "O-65"] == ["path_exists"], f"{reqs} {r1.stderr[-120:]}")
    run("requires", "--mission", mid, "--obligation", "O-70", "--ram-free-gb", "9")
    reqs = gm.load(mid).get("requires") or []
    check("V-RES-CLI-REPLACE", [r["arg"] for r in reqs if r["obligation"] == "O-70"] == [9.0]
          and len(reqs) == 2, str(reqs))
    run("requires", "--mission", mid, "--clear", "O-70")
    reqs = gm.load(mid).get("requires") or []
    check("V-RES-CLI-CLEAR", [r["obligation"] for r in reqs] == ["O-65"], str(reqs))

    print(f"RES_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
