"""A3-chain: a packet mission relays across sessions with ZERO manual admit.

An admission pays for one launch (review F3). With no resident orchestrator nobody re-admits, so the
supervisor re-admits deterministically from the recorded route file when the only refusal is "consumed".
Controls: a RECOMPILE/DEFER verdict, a changed packet or a changed route still stops the successor.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

TMP = tempfile.mkdtemp(prefix="gsd-mission-chain-test-")
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

gm.progress_fingerprint = lambda work_dir: None
FLOORS = str(Path(__file__).resolve().parent.parent / "vault" / "config" / "route-floors.json")
NOW = 1_800_000_000.0
ENV = {"target": 3_500_000, "warn": 4_500_000, "stop": 5_500_000, "calls": 25}
THIN = {"envelope": ENV, "workers": [{"name": "w0r", "profile": "top-level-worker", "calls": 25, "packet": 4000}]}
passes = fails = 0
calls: list = []


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def runner(argv, cwd):
    calls.append(argv)
    return SimpleNamespace(stdout=f"backgrounded · c0ffee{len(calls):02x} · {argv[3]}", stderr="", returncode=0)


def write(name, obj):
    p = Path(TMP) / name
    p.write_text(obj if isinstance(obj, str) else json.dumps(obj), encoding="utf-8")
    return str(p)


def consumed_mission(mid, measure=lambda r: None, cmd="/gsd-autonomous --ws wsx"):
    """A packet mission admitted once, whose single admission was used by its first launch."""
    gm.create(TMP, cmd, mission_id=mid, now=NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW,
                  state=gm.RUNNING, epoch=1)
    gm.set_envelope(mid, wu_packet=write(f"{mid}-WU.md", f"# WU {mid}\n"), now=NOW)
    gm.admit_route(mid, write(f"{mid}-route.json", THIN), floors_path=FLOORS, now=NOW, measure=measure)
    cur = gm.load(mid)
    res = gm.launch_worker(mid, expect_epoch=cur["epoch"], expect_state=cur["state"], reason="t",
                           runner=runner, now=NOW)
    assert res.get("ok"), res
    return gm.load(mid)


def fresh_launch(mid):
    cur = gm.load(mid)
    return gm.launch_worker(mid, expect_epoch=cur["epoch"], expect_state=cur["state"], reason="t",
                            runner=runner, now=NOW)


def main() -> int:
    # 1. the consumed admission is re-admitted from the route file; the successor launches, no manual admit
    rec = consumed_mission("m-chain")
    check("V-CHAIN-PREMISE-CONSUMED", rec["admission"].get("consumed_epoch") is not None
          and "used by epoch" in (gm.admission_refusal(rec) or ""))
    out = gm.readmit_for_relay(rec, now=NOW + 10, measure=lambda r: 100_000)
    after = out["rec"]
    check("V-CHAIN-READMITTED", out["readmitted"] and after["admission"]["verdict"] == "ADMISSIBLE"
          and after["admission"].get("consumed_epoch") is None, str(after["admission"]))
    n = len(calls)
    check("V-CHAIN-SUCCESSOR-LAUNCHES", gm.admission_refusal(after) is None and fresh_launch("m-chain").get("ok")
          and len(calls) == n + 1)
    check("V-CHAIN-LEDGERED", any(e.get("event") == "relay_readmitted" for e in gm.lr.ledger_events("m-chain")))

    # 2. a second relay chains again (three sessions, zero manual admit)
    out2 = gm.readmit_for_relay(gm.load("m-chain"), now=NOW + 20, measure=lambda r: 200_000)
    check("V-CHAIN-THIRD-SESSION", out2["readmitted"] and fresh_launch("m-chain").get("ok"))

    # 3. controls: the re-admission never lifts a real refusal
    r3 = consumed_mission("m-changed-pkt")
    write("m-changed-pkt-WU.md", "# EDITED\n")
    o3 = gm.readmit_for_relay(r3, now=NOW + 10)
    check("V-CHAIN-PACKET-CHANGE-NOT-READMITTED", not o3["readmitted"] and gm.admission_refusal(gm.load("m-changed-pkt")))
    r4 = consumed_mission("m-changed-route")
    write("m-changed-route-route.json", {**THIN, "workers": [{**THIN["workers"][0], "calls": 24}]})
    check("V-CHAIN-ROUTE-CHANGE-NOT-READMITTED", not gm.readmit_for_relay(r4, now=NOW + 10)["readmitted"])
    gm.create(TMP, "/gsd-autonomous --ws wsx", mission_id="m-never", now=NOW)
    gm.transition("m-never", expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW,
                  state=gm.RUNNING, epoch=1)
    gm.set_envelope("m-never", wu_packet=write("m-never-WU.md", "# w\n"), now=NOW)
    check("V-CHAIN-NEVER-ADMITTED-STAYS-REFUSED", not gm.readmit_for_relay(gm.load("m-never"), now=NOW)["readmitted"]
          and gm.admission_refusal(gm.load("m-never")) is not None)

    # 4. DEFER: remaining budget exhausted at re-admission -> recorded DEFER, successor refused
    r5 = consumed_mission("m-defer")
    gm.set_envelope("m-defer", token_estimate="2M", now=NOW)
    o5 = gm.readmit_for_relay(gm.load("m-defer"), now=NOW + 10, measure=lambda r: 3_900_000)
    check("V-CHAIN-DEFER-STOPS-SUCCESSOR", o5["readmitted"] and o5["rec"]["admission"]["verdict"] != "ADMISSIBLE"
          and gm.admission_refusal(gm.load("m-defer")) is not None, str(o5["rec"]["admission"]["verdict"]))

    # 5. kill switch is honoured
    r6 = consumed_mission("m-off")
    os.environ["CPP_ROUTE_ADMISSION"] = "off"
    try:
        check("V-CHAIN-SWITCH-OFF-NOOP", not gm.readmit_for_relay(r6, now=NOW)["readmitted"])
    finally:
        os.environ.pop("CPP_ROUTE_ADMISSION", None)

    # 6. supervise wiring: a dead owner of a consumed packet mission is relayed with zero manual admit
    r7 = consumed_mission("m-sup", cmd="/packet-unit run")
    sid = r7["pending"]["bg_id"] + "-0000-4000-8000-000000000000"
    gm.ack_session(sid, pid=1, now=NOW + 5)
    n = len(calls)
    rows = gm.supervise(now=NOW + 4000, sessions=[{"sessionId": sid, "state": "stopped"}], pid_alive=lambda p: False, runner=runner)
    row = next((r for r in rows if r.get("mission_id") == "m-sup"), {})
    check("V-CHAIN-SUPERVISE-RELAYS-WITHOUT-ADMIT", row.get("readmitted") is True
          and (row.get("launch") or {}).get("ok") is True and len(calls) == n + 1, str(row)[:400])

    # 7. WU-S7b: release of a held packet mission re-admits from the recorded route (red: sha changed)
    consumed_mission("m-rel")
    gm.set_owner_hold("m-rel", "t", now=NOW + 30)
    rr = gm.release_owner_hold("m-rel", now=NOW + 40)
    check("V-S7B-RELEASE-READMITS", not rr.get("owner_hold") and rr["admission"]["verdict"] == "ADMISSIBLE"
          and rr["admission"].get("consumed_epoch") is None and gm.admission_refusal(rr) is None, str(rr["admission"])[:300])
    consumed_mission("m-rel-red")
    gm.set_owner_hold("m-rel-red", "t", now=NOW + 30)
    write("m-rel-red-WU.md", "# EDITED\n")
    rr2 = gm.release_owner_hold("m-rel-red", now=NOW + 40)
    check("V-S7B-RELEASE-SHA-CHANGED-NO-READMIT", not rr2.get("owner_hold") and rr2["admission"].get("consumed_epoch") is not None
          and gm.admission_refusal(rr2) is not None)

    print(f"{passes} passed, {fails} failed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
