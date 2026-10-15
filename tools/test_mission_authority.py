#!/usr/bin/env python
"""V-MA-* gates: a mission's Owner authority is a runtime ceiling, and its breach is an economic incident.

Mission-authority programme (vault/plans/mission-authority-econ-programme-2026-10-15.md), Stage A.
Incident: m-ce2bacd4cbb0 carried authority_tokens 45,000,000 and token_estimate 45,000,000; the breaker tripped
only at 2.0 x estimate = 90M, so the mission reached 83,778,584 and was found by a person asking for status.
These gates drive the real judge, the real supervise sweep, the real hold path, the real incident store and the
real in-turn gate (node hooks/lib/mission_gate.js) in a temp state dir. Every refusal has a paired control.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="mission-authority-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["CLAUDE_CONFIG_DIR"] = str(Path(TMP) / "cfg")
os.environ.pop("CPP_COST_HOLD_STOP", None)
os.environ.pop("CLAUDECODE", None)
os.environ.pop("CPP_GOAL", None)
os.environ["CPP_MISSION_RECOVERY"] = "off"
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import gsd_mission as gm  # noqa: E402
import mission_spend as ms  # noqa: E402
import econ_incident as ei  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None

passes = fails = 0
NOW = 1_800_000_000.0
M = 1_000_000
SPEND: dict[str, int | None] = {}
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


def _measure(rec):
    v = SPEND[rec["mission_id"]]
    if v is None:
        raise OSError("no transcript directory")
    return v


ms.processed_tokens = _measure


def worker(mid, **fields):
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    sid = f"{mid}-w"
    owner = {"session_id": sid, "pid": None, "proc_start": None, "heartbeat_at": NOW, "epoch": 1, "kind": "background"}
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW, state=gm.RUNNING,
                  epoch=1, max_hours=100.0, owner=owner, **fields)
    return sid


def sweep(mid):
    gm.supervise(now=NOW + 60, sessions=[{"sessionId": f"{mid}-w", "id": f"{mid}-w"[:8], "kind": "background",
                                          "state": "running"}],
                 runner=lambda *a, **k: "", stop_runner=lambda a: None, pid_alive=gone, gsd_status=OK_GSD,
                 fingerprint=lambda wd: None)
    return gm.load(mid)


def gate(sid, tool="PowerShell"):
    """Run the REAL in-turn gate for one PreToolUse payload; returns the deny reason or None."""
    js = ("const g=require(process.argv[1]);const r=g.decide(JSON.parse(process.argv[2]));"
          "process.stdout.write(JSON.stringify(r));")
    ev = json.dumps({"session_id": sid, "tool_name": tool, "tool_input": {"command": "echo hi"}})
    out = subprocess.run(["node", "-e", js, str(HERE.parent / "hooks" / "lib" / "mission_gate.js"), ev],
                         capture_output=True, text=True, env=os.environ, timeout=30)
    return json.loads(out.stdout or "{}").get("deny")


def main() -> int:
    # --- judge (pure) ---------------------------------------------------------------------------------------
    k3 = {"authority_tokens": 45 * M, "token_estimate": 45 * M}
    v = ms.judge(k3, 82_289_960, "fp")
    check("V-MA-K3-REPLAY-TRIPS-AT-AUTHORITY", bool(v["trip"]) and v.get("level") == "MISSION_AUTHORITY",
          f"trip={v['trip']!r:.80}")
    check("V-MA-K3-OLD-RATIO-WOULD-NOT", 82_289_960 <= 2.0 * 45 * M, "2 x estimate = 90M > 82.3M: the old breaker was silent")
    v = ms.judge(k3, 44_000_000, "fp")
    check("V-MA-CLOSEOUT-RESERVE-TRIPS-BEFORE-CAP", bool(v["trip"]), "44.0M >= 45M - 1M closeout")
    v = ms.judge(k3, 43_999_999, "fp")
    check("V-MA-CONTROL-UNDER-RESERVE-ADMITTED", v["trip"] is None, "43,999,999 < 44,000,000")
    v = ms.judge({"authority_tokens": 10 * M}, 9_600_000, None)
    check("V-MA-AUTHORITY-WITHOUT-ESTIMATE-TRIPS", bool(v["trip"]), "no token_estimate: the authority still binds")
    v = ms.judge({"authority_tokens": 10 * M}, 9_400_000, None)
    check("V-MA-AUTHORITY-WITHOUT-ESTIMATE-CONTROL", v["trip"] is None, "9.4M < 10M - 0.5M")
    check("V-MA-SMALL-AUTHORITY-SMALL-RESERVE", ms.closeout_reserve({"authority_tokens": 3 * M}) == 150_000,
          f"reserve={ms.closeout_reserve({'authority_tokens': 3 * M})}")
    check("V-MA-EXPLICIT-RESERVE", ms.closeout_reserve({"authority_tokens": 3 * M, "closeout_tokens": 0}) == 0, "")
    v = ms.judge({"token_estimate": 45 * M}, 82_289_960, "fp")
    check("V-MA-NO-AUTHORITY-KEEPS-OLD-BEHAVIOUR", v["trip"] is None, "no authority_tokens: 2 x estimate as before")
    v = ms.judge({}, 10**12, "fp")
    check("V-MA-UNJUDGED-WITHOUT-EITHER", v["trip"] is None, "")
    v = ms.judge(k3, 90 * M, "fp", as_of=NOW - 3600, now=NOW)
    check("V-MA-STALE-SNAPSHOT-NEVER-TRIPS", v["trip"] is None and bool(v.get("stale")), "stale usage stays stale")

    # --- incident store (unit) -----------------------------------------------------------------------------
    r = ei.record({"mission_id": "m-aa00ff", "authority_tokens": 45 * M}, "x", now=NOW, measure=lambda rec: 1 / 0)
    check("V-MA-INCIDENT-UNKNOWN-IS-NOT-ZERO", r["spent"] is None and r["overshoot"] is None and r["spent_error"],
          f"spent={r['spent']} err={r['spent_error']}")
    check("V-MA-INCIDENT-CLASSIFIES", ei.classify("cost breaker (phase lease): x") == "PHASE_LEASE"
          and ei.classify("cost breaker: 9 processed since the work tree last changed") == "STALL", "")

    # --- the real sweep: authority trips, hold is kind=cost, receipt written, status shows it, gate denies ---
    sid = worker("m-aa0001", authority_tokens=45 * M, token_estimate=45 * M)
    SPEND["m-aa0001"] = 82_289_960
    rec = sweep("m-aa0001")
    hold = rec.get("owner_hold") or {}
    check("V-MA-SWEEP-HOLDS-AT-AUTHORITY", hold.get("kind") == "cost" and "mission authority" in hold.get("reason", ""),
          f"hold={hold.get('reason', '')[:90]!r}")
    inc = [x for x in ei.open_incidents() if x.get("mission_id") == "m-aa0001"]
    check("V-MA-RECEIPT-WRITTEN", len(inc) == 1 and inc[0]["level"] == "MISSION_AUTHORITY"
          and inc[0]["spent"] == 82_289_960 and inc[0]["overshoot"] == 82_289_960 - 45 * M,
          f"incidents={[(x.get('level'), x.get('spent')) for x in inc]}")
    rows = [e for e in gm.lr.ledger_events("m-aa0001") if e.get("event") == "economic_incident"]
    check("V-MA-LEDGER-ROW", len(rows) == 1 and rows[0].get("level") == "MISSION_AUTHORITY", f"rows={len(rows)}")
    check("V-MA-STATUS-SURFACES-IT", any("m-aa0001" in s for s in ei.status_lines()), "")
    Path(TMP, f"mission-worker-{sid}.json").write_text(json.dumps({"mission_id": "m-aa0001"}), encoding="utf-8")
    deny = gate(sid)
    check("V-MA-IN-TURN-DENIED-AFTER-TRIP", bool(deny) and "COST HOLD" in deny, f"deny={str(deny)[:70]!r}")

    # control: same mission shape under the reserve -> no hold, no receipt, gate admits
    sid2 = worker("m-aa0002", authority_tokens=45 * M, token_estimate=45 * M)
    SPEND["m-aa0002"] = 30 * M
    rec = sweep("m-aa0002")
    check("V-MA-CONTROL-NO-HOLD", not rec.get("owner_hold"), f"hold={rec.get('owner_hold')}")
    check("V-MA-CONTROL-NO-RECEIPT", not [x for x in ei.open_incidents() if x.get("mission_id") == "m-aa0002"], "")
    Path(TMP, f"mission-worker-{sid2}.json").write_text(json.dumps({"mission_id": "m-aa0002"}), encoding="utf-8")
    check("V-MA-CONTROL-GATE-ADMITS", gate(sid2) is None, "")

    # a mission with authority but no estimate is judged at all (the sweep used to skip it)
    worker("m-aa0003", authority_tokens=5 * M)
    SPEND["m-aa0003"] = 6 * M
    rec = sweep("m-aa0003")
    check("V-MA-SWEEP-JUDGES-AUTHORITY-ONLY-MISSION", (rec.get("owner_hold") or {}).get("kind") == "cost",
          f"hold={(rec.get('owner_hold') or {}).get('reason', '')[:60]!r}")

    # acknowledge closes it in status, keeps the receipt
    ei.acknowledge(inc[0]["file"])
    check("V-MA-ACK-CLOSES-STATUS-KEEPS-FILE", not any("m-aa0001" in s for s in ei.status_lines())
          and Path(inc[0]["file"]).exists(), "")

    print(f"MISSION_AUTHORITY_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
