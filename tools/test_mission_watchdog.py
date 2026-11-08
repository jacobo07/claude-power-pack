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
# The watchdog under test wrote the LIVE checkout's snapshot ledger and heartbeat log
# (tools/test_state_isolation.py, 2026-09-28); markers follow the same private state dir.
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CTXWD_HEARTBEAT_LOG"] = str(Path(TMP) / "context-watchdog.log")
os.environ["CTXWD_SNAPSHOT_LEDGER"] = str(Path(TMP) / "context_snapshots.jsonl")
# The watchdog spawns `rollover.py shadow` DETACHED for the plain sessions below; without this the
# child wrote shadow_candidate rows + capsules into the LIVE ~/.claude/state/rollover (measured
# 2026-09-30: 4 rows + 2 capsules per run, 70 mcw-plain rows accumulated, 44 % of all shadow rows).
LIVE_ROLLOVER = Path.home() / ".claude" / "state" / "rollover"
os.environ["CPP_ROLLOVER_STATE_DIR"] = str(Path(TMP) / "rollover")
PROJECT = Path(TMP) / "project"
(PROJECT / "vault").mkdir(parents=True)
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
        calls["last"] = k
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
            # A private project, never ROOT: the watchdog appends its roll-up to <cwd>/vault/progress.md,
            # and cwd=ROOT made this suite write the LIVE checkout's progress.md (test_state_isolation,
            # run from the live checkout, 2026-09-28).
            return wd.run({"session_id": sid, "cwd": str(PROJECT), "transcript_path": ""}) or {}
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
          and gm.NOTE_TAG in reason, reason[:120])
    # the hand-off must need no tool: an acceptEdits worker cannot run a shell here (W0 E8)
    check("V-MCW-HANDOFF-NEEDS-NO-SHELL", "python" not in reason.lower()
          and "gsd_mission.py" not in reason, reason[:120])
    check("V-MCW-NO-COMPACT-LINE", "/compact focus" not in reason)
    check("V-MCW-NOTHING-DISPATCHED", calls["dispatch"] == before["dispatch"],
          f"dispatch calls {calls['dispatch'] - before['dispatch']}")
    check("V-MCW-CHECKPOINT-STILL-WRITTEN", calls["kclear"] == before["kclear"] + 1)

    # asked mid-turn already (hooks/mission_wall.js flag) -> the Stop must NOT block again,
    # or the turn cannot end and the relay cannot happen (measured W8)
    bg2 = uuid.uuid4().hex[:8]
    sid2 = f"{bg2}-{uuid.uuid4().hex[:4]}-mcw"
    mid2 = f"m-mcw2-{uuid.uuid4().hex[:6]}"
    gm.create(str(ROOT), "/gsd-autonomous", mission_id=mid2)
    gm.transition(mid2, expect_epoch=0, expect_state=gm.PREPARED, event="t", state=gm.LAUNCHING,
                  epoch=1, pending={"kind": "worker_start", "bg_id": bg2, "deadline": time.time() + 300})
    gm.session_start(sid2, "startup")
    (Path(TMP) / f"mission-wall-{sid2}-e1.flag").write_text("1", encoding="utf-8")
    out2 = run_at(sid2, 45.0)
    check("V-MCW-MIDTURN-ASKED-STOP-DOES-NOT-BLOCK", out2.get("decision") != "block", str(out2)[:80])

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

    # --- control: an ordinary armed run at the same wall still gets a continuation ------------
    # INVERTED 2026-09-28, in place. This control pinned `/compact`; active rollover (42da3d1,
    # Owner-authorized, ON by default) asks for `/kclear` at the wall instead. test_gsd_long_run
    # was inverted with that commit and this sibling was not, so it went red on the live checkout
    # for a reason unrelated to missions. The diff of this assertion is the evidence.
    plain = f"mcw-plain-{uuid.uuid4().hex[:8]}"
    p = mk.write_marker(plain, "/gsd-autonomous", cwd=str(ROOT))
    data = json.loads(p.read_text(encoding="utf-8"))
    data["wall"] = dict(gm.DEFAULT_WALL)
    mk._save(p, data)
    # INVERTED AGAIN 2026-10-06, following 118e5994 (2026-09-29) as test_gsd_long_run did in
    # 2e4be931: /kclear is work the MODEL does, never a keystroke. The wall asks for it in the
    # block reason, ledgers `rollover_kclear_asked`, and dispatches nothing. Red here since 09-29.
    before = dict(calls)
    out = run_at(plain, 45.0)
    plain_events = [e["event"] for e in lr.ledger_events(plain)]
    check("V-MCW-CONTROL-PLAIN-ROLLOVER-KCLEAR", out.get("decision") == "block"
          and "invoke the `kclear` skill" in out.get("reason", "")
          and "rollover_kclear_asked" in plain_events and calls["dispatch"] == before["dispatch"],
          (out.get("decision"), plain_events, calls["dispatch"] - before["dispatch"]))
    # The kill switch must restore the old crossing exactly, or "rollover is on" and "the
    # /compact path is gone" are the same observable.
    plain2 = f"mcw-plain-{uuid.uuid4().hex[:8]}"
    p2 = mk.write_marker(plain2, "/gsd-autonomous", cwd=str(ROOT))
    data2 = json.loads(p2.read_text(encoding="utf-8"))
    data2["wall"] = dict(gm.DEFAULT_WALL)
    mk._save(p2, data2)
    os.environ["CPP_ROLLOVER_ACTIVE"] = "0"
    try:
        before = dict(calls)
        out2 = run_at(plain2, 45.0)
    finally:
        os.environ.pop("CPP_ROLLOVER_ACTIVE", None)
    last2 = calls.get("last") or {}
    check("V-MCW-CONTROL-KILLSWITCH-COMPACTS", "/compact focus" in out2.get("reason", "")
          and last2.get("expect_prefix") == "/compact" and calls["dispatch"] == before["dispatch"] + 1,
          (last2.get("kind"), out2.get("reason", "")[:60]))

    # Isolation of the detached shadow child: its rows must land in the private ledger (positive
    # control: the child ran and was redirected, not silenced) and never in the live one.
    def rows_for(ledger: Path) -> int:
        try:
            text = ledger.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            return 0
        return sum(1 for line in text.splitlines() if plain in line or plain2 in line)

    private = Path(TMP) / "rollover" / "rollover-ledger.jsonl"  # not the env: a drill that drops it must FAIL, not crash
    deadline = time.time() + 20  # bounded on the condition, not a fixed flush
    while time.time() < deadline and rows_for(private) == 0:
        time.sleep(0.25)
    check("V-MCW-SHADOW-REDIRECTED", rows_for(private) > 0, f"private rows {rows_for(private)}")
    # shadow-capsules/ since G12 (ed172f48): the detached shadow seals there, not in capsules/.
    check("V-MCW-LIVE-ROLLOVER-UNTOUCHED", rows_for(LIVE_ROLLOVER / "rollover-ledger.jsonl") == 0
          and not any(p for sub in ("capsules", "shadow-capsules") for s in (plain, plain2)
                      for p in (LIVE_ROLLOVER / sub).glob(f"{s}*")),
          f"live rows {rows_for(LIVE_ROLLOVER / 'rollover-ledger.jsonl')}")

    print(f"MCW_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
