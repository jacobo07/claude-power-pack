#!/usr/bin/env python
"""V-PB-* gates for the Prompt Broker (tools/prompt_broker.py, oic-v1 S3).

1. The 12 real host texts captured 2026-10-10 (tools/fixtures/prompt_broker_live_2026-10-10.json) against
   a HAND-WRITTEN expectation below, never against the class stored in the fixture.
2. Synthetic controls for the classes the live estate did not show (opaque, login, unknown).
3. Hermetic routing: fake jobs dir + mission records; only Owner-class rows reach the decision queue,
   mechanical / event-wait rows never do.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="prompt-broker-test-")
for k in ("GSD_LONG_RUN_STATE_DIR", "CPP_OWNER_DECISIONS_DIR", "CPP_AUTHORITY_DIR"):
    os.environ[k] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["CPP_AUTONOMY_RECEIPTS"] = str(Path(TMP) / "audit.jsonl")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import prompt_broker as pb  # noqa: E402

passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


EXPECTED = {   # read by a person from each row's text, 2026-10-10
    "m-0fdcdcadd6f5": "CAPITAL", "m-2f45a4047992": "CAPITAL", "m-4d1b851262ff": "CAPITAL",
    "m-d84de9dd1edb": "CAPITAL", "m-5709490db84c": "GENUINE_HUMAN_BOUNDARY",
    "m-906ce1fae68c": "GENUINE_HUMAN_BOUNDARY", "m-608c8d8d761f": "MECHANICAL",
    "m-6f7451aefe40": "MECHANICAL", "m-9bee7894f20f": "MECHANICAL", "m-c74a2125495b": "MECHANICAL",
    "m-80016a4bb9f2": "EVENT_WAIT", "m-cd548e5d2ada": "EVENT_WAIT",
}
fx = json.loads((HERE / "fixtures" / "prompt_broker_live_2026-10-10.json").read_text(encoding="utf-8"))["rows"]
check("V-PB-FIXTURE-COMPLETE", {r["mission_id"] for r in fx} == set(EXPECTED), str(len(fx)))
wrong = {r["mission_id"]: pb.classify(r["needs"], r["detail"])["class"] for r in fx
         if pb.classify(r["needs"], r["detail"])["class"] != EXPECTED.get(r["mission_id"])}
check("V-PB-LIVE-12-CLASSIFIED", not wrong, str(wrong))
cmd = pb.classify(next(r for r in fx if r["mission_id"] == "m-608c8d8d761f")["needs"], None)
check("V-PB-MECHANICAL-NAMES-COMMAND", (cmd.get("command") or "").startswith("node "), str(cmd.get("command")))

check("V-PB-OPAQUE", pb.classify(None, "")["class"] == pb.OPAQUE)
check("V-PB-LOGIN-IS-PRESENCE", pb.classify("login required", None)["class"] == pb.PRESENCE)
check("V-PB-UNKNOWN-IS-HIGH-RISK", pb.classify("the gizmo wants a blue widget", None)["class"] == pb.UNKNOWN)

# Hermetic routing over fake missions + host job files.
jobs = Path(os.environ["CPP_CLAUDE_JOBS_DIR"])
fake = {"m-mech0000001": ("aaaaaaaa", "run `node x.cjs query a`"),
        "m-wait0000001": ("bbbbbbbb", "You've hit your weekly limit · resets Oct 12, 9am"),
        "m-human000001": ("cccccccc", 'Reply "All good — continue" to accept the merge gates'),
        "m-cap00000001": ("dddddddd", "Supply a new goal id (goal is over its 16M cap)"),
        "m-running0001": ("eeeeeeee", None)}
for mid, (sid, needs) in fake.items():
    (Path(TMP) / f"gsd-mission-{mid}.json").write_text(json.dumps(
        {"mission_id": mid, "state": "RUNNING", "owner": {"session_id": sid + "-0000"}, "cwd": "C:/x"}),
        encoding="utf-8")
    (jobs / sid).mkdir(parents=True, exist_ok=True)
    st = {"state": "blocked", "needs": needs} if needs else {"state": "working", "tempo": "active"}
    (jobs / sid / "state.json").write_text(json.dumps(st), encoding="utf-8")
(Path(TMP) / "gsd-mission-m-halted00001.json").write_text(json.dumps({"state": "HALTED"}), encoding="utf-8")

rows = {r["mission_id"]: r for r in pb.scan(record=True, route=True)}
check("V-PB-RUNNING-NOT-SUSPENDED", "m-running0001" not in rows and len(rows) == 4, str(sorted(rows)))
check("V-PB-MECHANICAL-NOT-ROUTED", "routed" not in rows["m-mech0000001"])
check("V-PB-EVENT-WAIT-NOT-ROUTED", "routed" not in rows["m-wait0000001"]
      and rows["m-wait0000001"].get("reset", "").startswith("Oct 12"), str(rows["m-wait0000001"].get("reset")))
check("V-PB-HUMAN-ROUTED", rows["m-human000001"].get("routed") == "queued")
check("V-PB-CAPITAL-ROUTED", rows["m-cap00000001"].get("routed") == "queued")
rows2 = {r["mission_id"]: r for r in pb.scan(record=False, route=True)}
check("V-PB-REPEAT-SCAN-SUBSCRIBES-NOT-DUPLICATES", rows2["m-human000001"].get("routed") == "subscribed")
susp = (Path(TMP) / "oic" / "suspensions.jsonl").read_text(encoding="utf-8").splitlines()
check("V-PB-SUSPENSION-RECORDED", len(susp) == 4 and all(json.loads(x)["class"] for x in susp))

os.environ["CPP_OIC"] = "off"
check("V-PB-KILL-SWITCH", pb.main(["scan"]) == 0)

print(f"PROMPT_BROKER_PASS={passes}/{passes + fails}")
sys.exit(0 if fails == 0 else 1)
