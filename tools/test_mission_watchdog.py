#!/usr/bin/env python
"""V-MCW-* gates: the mission worker's wall, end to end through the REAL watchdog module.

What this pins (spec vault/specs/mission-continuity.md):
  * a worker acked through gsd_mission.session_start gets a marker whose wall the watchdog
    ACTUALLY applies -- the first draft wrote it under a key the watchdog never reads, so
    the worker would have run on the production constants (70 %) without anything saying so;
  * at that wall a mission worker is asked to HAND OFF, never to /compact, and nothing is
    dispatched to any terminal;
  * the same wall on an ordinary armed run still produces the /compact line (control), so
    the branch discriminates rather than replacing everything.

Hermetic: state and markers go to a temp dir; the watchdog's effect doors are recorders.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TMP = tempfile.mkdtemp(prefix="mcw-state-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
sys.path.insert(0, str(ROOT / "tools"))
import gsd_autorun_marker as mk  # noqa: E402
import gsd_long_run as lr  # noqa: E402
import gsd_mission as gm  # noqa: E402

mk.STATE_DIR = Path(TMP)  # the marker module's dir is a constant; redirect it for the suite

passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def _load_watchdog():
    path = ROOT / "modules" / "zero-crash" / "hooks" / "context-watchdog.py"
    spec = importlib.util.spec_from_file_location("ctxwd_under_test", path)
    wd = importlib.util.module_from_spec(spec)
    sys.modules["ctxwd_under_test"] = wd
    spec.loader.exec_module(wd)
    wd._TOOL_CACHE.update({"gsd_autorun_marker": mk, "gsd_long_run": lr, "gsd_mission": gm})
    return wd


def main() -> int:
    wd = _load_watchdog()
    calls = {"dispatch": 0, "kclear": 0}

    def door(*a, **k):
        calls["dispatch"] += 1
        return {"route": "stub"}

    def kclear(*a, **k):
        calls["kclear"] += 1
        return {"handoff": "stub", "lessons": "stub", "insights": "stub"}

    wd._dispatch_continuation = door
    wd._kclear_equivalent = kclear
    wd._dump_telemetry = lambda *a, **k: "stub"

    def run_at(sid, pct):
        (Path(tempfile.gettempdir()) / wd.ORCH_THROTTLE_FLAG.format(session_id=sid)).write_text(
            str(time.time()), encoding="utf-8")
        os.environ["_TEST_CONTEXT_PCT"] = str(pct)
        try:
            return wd.run({"session_id": sid, "cwd": str(ROOT), "transcript_path": ""}) or {}
        finally:
            os.environ.pop("_TEST_CONTEXT_PCT", None)

    # --- a mission worker, acked the way the SessionStart hub acks it ------------------------
    bg = uuid.uuid4().hex[:8]
    sid = f"{bg}-{uuid.uuid4().hex[:4]}-mcw"
    mid = f"m-mcw-{uuid.uuid4().hex[:6]}"
    gm.create(str(ROOT), "/gsd-autonomous", mission_id=mid)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t", state=gm.LAUNCHING,
                  epoch=1, pending={"kind": "worker_start", "bg_id": bg,
                                    "deadline": time.time() + 300})
    card = gm.session_start(sid, "startup")
    rec = gm.load(mid)
    check("V-MCW-ACK-RUNNING", rec["state"] == gm.RUNNING and rec["owner"]["session_id"] == sid,
          rec["state"])
    check("V-MCW-FIRST-EPOCH-NO-CARD", card == "", repr(card[:40]))
    check("V-MCW-WALL-APPLIED", wd._thresholds(sid) == (35.0, 40.0, 30.0),
          str(wd._thresholds(sid)))

    before = dict(calls)
    out = run_at(sid, 45.0)
    reason = out.get("reason", "")
    check("V-MCW-HANDOFF-ASKED", out.get("decision") == "block" and "CONTEXT WALL" in reason
          and "gsd_mission.py" in reason and "handoff" in reason, reason[:120])
    check("V-MCW-NO-COMPACT-LINE", "/compact focus" not in reason)
    check("V-MCW-NOTHING-DISPATCHED", calls["dispatch"] == before["dispatch"],
          f"dispatch calls {calls['dispatch'] - before['dispatch']}")
    check("V-MCW-CHECKPOINT-STILL-WRITTEN", calls["kclear"] == before["kclear"] + 1)

    # the worker records its hand-off; the next worker gets a card that carries it
    gm.request_handoff(sid, "next: plan 03-02 task 3")
    rec = gm.load(mid)
    gm.transition(mid, expect_epoch=rec["epoch"], expect_state=gm.HANDOFF, event="t",
                  state=gm.LAUNCHING, epoch=2,
                  pending={"kind": "worker_start", "bg_id": "c0ffee00", "deadline": time.time() + 300})
    card2 = gm.session_start("c0ffee00-aaaa-mcw", "startup")
    check("V-MCW-SUCCESSOR-CARD", "RECONCILE BEFORE ACTING" in card2
          and "plan 03-02 task 3" in card2 and "epoch 2" in card2, card2[:80])
    check("V-MCW-SUCCESSOR-OWNS", gm.load(mid)["owner"]["session_id"] == "c0ffee00-aaaa-mcw")

    # --- control: an ordinary armed run at the same wall still asks for /compact -------------
    plain = f"mcw-plain-{uuid.uuid4().hex[:8]}"
    p = mk.write_marker(plain, "/gsd-autonomous", cwd=str(ROOT))
    data = json.loads(p.read_text(encoding="utf-8"))
    data["wall"] = dict(gm.DEFAULT_WALL)
    mk._save(p, data)
    before = dict(calls)
    out = run_at(plain, 45.0)
    check("V-MCW-CONTROL-PLAIN-COMPACTS", "/compact focus" in out.get("reason", "")
          and calls["dispatch"] == before["dispatch"] + 1, out.get("reason", "")[:80])

    print(f"MCW_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
