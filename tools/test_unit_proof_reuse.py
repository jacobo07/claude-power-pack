#!/usr/bin/env python
"""WU-S6 gates: supervise emits the unit receipt, the ledger fills deterministically from receipts, and an
unchanged PROVEN unit is admitted NO_WORK -- on a fresh project whose route and prompt never mention proofs.
Mutation drill: GSD_MISSION_DRILL_DIR holding a mutated gsd_mission.py."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="unit-proof-reuse-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_CLAIM_LEDGER"] = str(Path(TMP) / "claims.json")
os.environ["CPP_UNIT_RECEIPTS"] = str(Path(TMP) / "receipts.jsonl")
os.environ.pop("CPP_ROUTE_ADMISSION", None)
os.environ["CPP_CLAUDE_EXE"] = "__no_such_claude_in_tests__"
sys.path.insert(0, str(Path(__file__).resolve().parent))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
import gsd_mission as gm  # noqa: E402
import work_proof as wp  # noqa: E402

FLOORS = str(Path(__file__).resolve().parent.parent / "vault" / "config" / "route-floors.json")
ENV = {"target": 3_500_000, "warn": 4_500_000, "stop": 5_500_000, "calls": 25}
ROUTE = {"envelope": ENV, "workers": [{"name": "w", "profile": "top-level-worker", "calls": 25, "packet": 4000}]}
NOW = 1_800_000_000.0
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def write(name, obj):
    p = Path(TMP) / name
    p.write_text(obj if isinstance(obj, str) else json.dumps(obj), encoding="utf-8")
    return str(p)


def armed(mid, packet):
    gm.create(TMP, "/gsd-autonomous --ws wsx", mission_id=mid, now=NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t", now=NOW, state=gm.RUNNING, epoch=1)
    gm.set_envelope(mid, wu_packet=packet, token_estimate=5_000_000, now=NOW)
    return gm.load(mid)


pkt = write("WU-canary.md", "# WU canary\ndo the thing\n")
route = write("route.json", ROUTE)   # no proof, no work_class: nothing names A4/A5/A6

# G1 no proof recorded -> ADMISSIBLE (absence is not proof)
armed("m-a", pkt)
a = gm.admit_route("m-a", route, floors_path=FLOORS)["admission"]
check("G1 unproven unit is admissible", a["verdict"] == "ADMISSIBLE", a["verdict"])
check("G1b tier recorded (unknown class -> DEFAULT)", a.get("tier") == "DEFAULT", str(a.get("tier")))

# G2 unit end emits receipt + PROVEN claim
out = gm.emit_unit_receipt(gm.load("m-a"), now=NOW, measure=lambda r: 1_200_000)
rows = [json.loads(x) for x in Path(os.environ["CPP_UNIT_RECEIPTS"]).read_text().splitlines()]
check("G2 receipt emitted", out.startswith("emitted") and rows and rows[0]["processed"] == 1_200_000, out)
check("G2b overhead computed", rows[0]["overhead_multiplier"] is not None and rows[0]["tier"] == "DEFAULT")
check("G2c claim PROVEN", wp.load_ledger()["claims"].get("unit:WU-canary", {}).get("status") == "PROVEN")

# G3 unknown spend is skipped, never zero
n = len(rows)
out2 = gm.emit_unit_receipt(gm.load("m-a"), now=NOW, measure=lambda r: None)
check("G3 unmeasurable spend writes nothing", out2.startswith("skipped") and
      len(Path(os.environ["CPP_UNIT_RECEIPTS"]).read_text().splitlines()) == n, out2)

# G4 fresh mission, same unchanged packet -> NO_WORK; arm_chain completes it without a worker
armed("m-b", pkt)
b = gm.admit_route("m-b", route, floors_path=FLOORS)["admission"]
check("G4 unchanged PROVEN unit is NO_WORK", b["verdict"] == "NO_WORK", b["verdict"])
check("G4b NO_WORK is not launchable", gm.admission_refusal(gm.load("m-b")) is not None)

# G5 packet changed -> back to ADMISSIBLE
Path(pkt).write_text("# WU canary\nchanged\n", encoding="utf-8")
armed("m-c", pkt)
c = gm.admit_route("m-c", route, floors_path=FLOORS)["admission"]
check("G5 changed packet re-runs", c["verdict"] == "ADMISSIBLE", c["verdict"])

# G6 ledger fills deterministically from receipts
rd = Path(TMP) / "rc"
rd.mkdir()
(rd / "WU-x.md").write_text("# x\n", encoding="utf-8")
(rd / "WU-x-receipt.md").write_text("# x receipt\nStatus: DONE\n", encoding="utf-8")
(rd / "WU-y.md").write_text("# y\n", encoding="utf-8")
(rd / "WU-y-receipt.md").write_text("# y receipt\nStatus: BLOCKED_HUMAN\n", encoding="utf-8")
(rd / "WU-z-receipt.md").write_text("# z receipt\nStatus: DONE\n", encoding="utf-8")   # no packet
led = str(Path(TMP) / "l2.json")
got = wp.populate_from_receipts(rd, ledger_path=led)
check("G6 only DONE receipts with a packet become PROVEN", got == ["unit:WU-x"], str(got))
check("G6b idempotent", wp.populate_from_receipts(rd, ledger_path=led) == got)

# G7 arm_chain on an unchanged PROVEN unit completes with no worker
Path(pkt).write_text("# WU canary\nchanged\n", encoding="utf-8")
wp.record_proof("unit:WU-canary", [str(Path(pkt).resolve())])
r = gm.arm_chain(TMP, "/gsd-autonomous --ws wsy", wu_packet=pkt, token_estimate=5_000_000, route=route,
                 floors_path=FLOORS)
check("G7 arm_chain NO_WORK completes", r.get("ok") and r.get("no_work") and r["mission"]["state"] == gm.COMPLETED,
      str({k: r.get(k) for k in ("ok", "no_work", "why")}))

print(f"{passes} pass, {fails} fail")
sys.exit(1 if fails else 0)
