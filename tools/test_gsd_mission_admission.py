#!/usr/bin/env python
"""V-ADM-* gates: a compiled work unit launches only through route admission, and the admitted
envelope becomes the worker's session envelope (tools/gsd_mission.py admit_route / launch_worker /
ack_session / adopt_launched; tools/route_admission.py).

Origin: Live QA W0 (m-8bbdf725cd52, 2026-10-05) launched a heavy GSD topology into a 4M envelope and
spent 53.7M before the cost breaker held it. Every refusal here has a launching control, so a gate
that refuses (or admits) everything cannot go green.

Hermetic like test_gsd_mission_envelope.py: state in a temp dir BEFORE import, an injected runner,
no real worker. Mutation drill: GSD_MISSION_DRILL_DIR holding a mutated gsd_mission.py.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

TMP = tempfile.mkdtemp(prefix="gsd-mission-admission-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ.pop("CPP_MISSION_RENEW", None)
os.environ.pop("CPP_ROUTE_ADMISSION", None)
os.environ["CPP_CLAUDE_EXE"] = "__no_such_claude_in_tests__"
sys.path.insert(0, str(Path(__file__).resolve().parent))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
import gsd_mission as gm  # noqa: E402
import mission_spend as ms  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None
FLOORS = str(Path(__file__).resolve().parent.parent / "vault" / "config" / "route-floors.json")

passes = fails = 0
NOW = 1_800_000_000.0
ENV = {"target": 3_500_000, "warn": 4_500_000, "stop": 5_500_000, "calls": 25}
THIN = {"envelope": ENV, "workers": [{"name": "w0r", "profile": "top-level-worker", "calls": 25, "packet": 4000}]}
HEAVY = {"envelope": ENV, "workers": [
    {"name": "orch", "profile": "top-level-worker", "calls": 40, "packet": 5000},
    *({"name": f"exec-{i}", "profile": "gsd-executor", "calls": 20, "packet": 20000} for i in range(3))]}


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def refused(fn) -> bool:
    try:
        fn()
    except gm.MissionError:
        return True
    return False


calls: list = []


def runner(argv, cwd):
    calls.append(argv)   # a distinct bg id per launch: an ack must find exactly ONE launching mission
    return SimpleNamespace(stdout=f"backgrounded · c0ffee{len(calls):02x} · {argv[3]}", stderr="", returncode=0)


def worker_sid(mid: str) -> str:
    return gm.load(mid)["pending"]["bg_id"] + "-0000-4000-8000-000000000000"


def write(name: str, obj) -> str:
    p = Path(TMP) / name
    p.write_text(obj if isinstance(obj, str) else json.dumps(obj), encoding="utf-8")
    return str(p)


def mission(mid: str, packet: bool = True) -> dict:
    gm.create(TMP, "/gsd-autonomous --ws wsx", mission_id=mid, now=NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW,
                  state=gm.RUNNING, epoch=1)
    if packet:
        gm.set_envelope(mid, wu_packet=write(f"{mid}-WU.md", f"# WU {mid}\n"), now=NOW)
    return gm.load(mid)


def launch(mid: str) -> dict:
    cur = gm.load(mid)
    return gm.launch_worker(mid, expect_epoch=cur["epoch"], expect_state=cur["state"], reason="t",
                            runner=runner, now=NOW)


def admit(mid: str, route_name: str, route=THIN, measure=lambda r: None) -> dict:
    return gm.admit_route(mid, write(route_name, route), floors_path=FLOORS, now=NOW, measure=measure)


def refused_launch(mid: str) -> tuple[bool, str]:
    n, before = len(calls), gm.load(mid)["epoch"]
    res = launch(mid)
    ok = res["ok"] is False and len(calls) == n and gm.load(mid)["epoch"] == before
    return ok, res.get("why", "")


def main() -> int:
    # 1. an unadmitted packet refuses BEFORE the claim; the refusal is on the ledger
    mission("m-un")
    ok, why = refused_launch("m-un")
    check("V-ADM-UNADMITTED-REFUSED", ok and "not admitted" in why, why)
    check("V-ADM-REFUSAL-LEDGERED", any(e.get("event") == "launch_refused_admission" for e in gm.lr.ledger_events("m-un")))

    # 2. heavy route recorded as RECOMPILE and refused; thin route ADMISSIBLE launches (control)
    mission("m-heavy")
    h = admit("m-heavy", "heavy.json", HEAVY)["admission"]
    ok, why = refused_launch("m-heavy")
    check("V-ADM-HEAVY-RECORDED-AND-REFUSED", h["verdict"] == "RECOMPILE" and ok, f"{h['verdict']}: {why}")
    mission("m-thin")
    t = admit("m-thin", "thin.json")["admission"]
    res = launch("m-thin")
    check("V-ADM-THIN-LAUNCHES", t["verdict"] == "ADMISSIBLE" and res.get("ok") is True, str(res))

    # 3. the admission is bound to the packet and the route file
    mission("m-pkt")
    admit("m-pkt", "pkt-route.json")
    write("m-pkt-WU.md", "# WU m-pkt EDITED\n")
    ok, why = refused_launch("m-pkt")
    check("V-ADM-PACKET-CHANGE-REFUSED", ok and "packet changed" in why, why)
    admit("m-pkt", "pkt-route.json")
    check("V-ADM-READMIT-LAUNCHES", launch("m-pkt").get("ok") is True)
    mission("m-route")
    admit("m-route", "route-r.json")
    write("route-r.json", {**THIN, "workers": [{**THIN["workers"][0], "calls": 24}]})
    ok, why = refused_launch("m-route")
    check("V-ADM-ROUTE-CHANGE-REFUSED", ok and "route file" in why, why)

    # 4. a mission without a packet (the GSD resume route) is not judged here (control)
    mission("m-gsd", packet=False)
    check("V-ADM-NO-PACKET-NOT-JUDGED", launch("m-gsd").get("ok") is True)

    # 5. kill switch: launches, and the bypass is on the ledger
    mission("m-kill")
    os.environ["CPP_ROUTE_ADMISSION"] = "off"
    try:
        res = launch("m-kill")
    finally:
        os.environ.pop("CPP_ROUTE_ADMISSION", None)
    check("V-ADM-KILL-SWITCH", res.get("ok") is True
          and any(e.get("event") == "admission_bypassed" for e in gm.lr.ledger_events("m-kill")), str(res))

    # 6. DEFER from the breaker's own numbers: 2 x 2M estimate - 3M attributed spend = 1M left
    mission("m-defer")
    gm.set_envelope("m-defer", token_estimate="2M", now=NOW)
    d = admit("m-defer", "defer.json", measure=lambda r: 3_000_000)["admission"]
    ok, _ = refused_launch("m-defer")
    check("V-ADM-DEFER-FROM-BREAKER", d["verdict"] == "DEFER" and d["remaining"] == 1_000_000 and ok, str(d["reasons"]))
    d2 = admit("m-defer", "defer.json", measure=lambda r: 100_000)["admission"]
    check("V-ADM-DEFER-CONTROL", d2["verdict"] == "ADMISSIBLE", f"remaining {d2['remaining']:,}")

    # 7. refusals of admit itself write nothing
    mission("m-nopkt", packet=False)
    seq = gm.load("m-nopkt")["seq"]
    check("V-ADM-ADMIT-NEEDS-PACKET", refused(lambda: admit("m-nopkt", "x.json")) and gm.load("m-nopkt")["seq"] == seq)
    seq = gm.load("m-thin")["seq"]
    check("V-ADM-MALFORMED-ROUTE-REFUSED",
          refused(lambda: gm.admit_route("m-thin", write("bad.json", "{not json"), floors_path=FLOORS, now=NOW))
          and refused(lambda: admit("m-thin", "bad2.json", {"envelope": ENV, "workers": []}))
          and gm.load("m-thin")["seq"] == seq)

    # 8. the worker's ack declares the admitted envelope as its SESSION envelope
    sid = worker_sid("m-thin")
    acked = gm.ack_session(sid, pid=1, now=NOW + 5)   # m-thin is LAUNCHING with its own bg_id
    bp = ms.budget_path(sid)
    budget = json.loads(bp.read_text(encoding="utf-8")) if bp.is_file() else {}
    check("V-ADM-ACK-DECLARES-ENVELOPE", acked and acked["mission_id"] == "m-thin"
          and (budget.get("target"), budget.get("stop"), budget.get("calls_estimate")) == (3_500_000, 5_500_000, 25),
          str(budget))
    check("V-ADM-ENVELOPE-LEDGERED", any(e.get("event") == "worker_envelope_declared" and e.get("worker") == sid
                                         for e in gm.lr.ledger_events("m-thin")))
    gsd_sid = worker_sid("m-gsd")
    gacked = gm.ack_session(gsd_sid, pid=2, now=NOW + 5)          # m-gsd: no packet, no admission
    check("V-ADM-NO-ADMISSION-NO-ENVELOPE", gacked and gacked["mission_id"] == "m-gsd"
          and not ms.budget_path(gsd_sid).exists())

    # 9. adoption (the worker's own ack never arrived) declares it too
    mission("m-adopt")
    admit("m-adopt", "adopt.json")
    launch("m-adopt")
    asid = worker_sid("m-adopt")
    gm.adopt_launched(gm.load("m-adopt"), {"sessionId": asid, "pid": 3}, now=NOW + 6)
    check("V-ADM-ADOPT-DECLARES-ENVELOPE", ms.budget_path(asid).is_file())

    # 10. CLI: admitted exit 0, rejected exit 3
    mission("m-cli")
    rc_ok = gm._cli(["admit", "--mission", "m-cli", "--route", write("cli-thin.json", THIN), "--floors", FLOORS])
    rc_no = gm._cli(["admit", "--mission", "m-cli", "--route", write("cli-heavy.json", HEAVY), "--floors", FLOORS])
    check("V-ADM-CLI", (rc_ok, rc_no) == (0, 3), f"{rc_ok} {rc_no}")

    print(f"ADM_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
