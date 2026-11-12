#!/usr/bin/env python
"""V-TOPUP-* / V-ARM-PIVOT-* gates: spec vault/specs/mission-checkpoint-autonomy.md (C2, C3).

Origin (2026-11-12, GEX44 S30T m-2e14179c5b6a): the arm granted "20M + 2x4M top-ups" as text only; at 1.35M room after
the reserve the next wave would have parked for the Owner although the capital was already granted. Hermetic: state in a
temp dir before import, spend injected, nothing launched, no channel reached (notifier injected).
`--drills`: each mutant of gsd_mission.py must turn the named gate red.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="gsd-mission-topup-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_MISSION_RECOVERY"] = "off"
for k in ("CPP_MISSION_TOPUP", "CPP_PIVOT_AUTONOMY"):
    os.environ.pop(k, None)
sys.path.insert(0, str(Path(__file__).resolve().parent))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
import gsd_mission as gm  # noqa: E402
import mission_spend as ms  # noqa: E402

gm.host_sessions = lambda *a, **k: None
passes = fails = 0
NOW = 1_800_000_000.0
SID = "0wnerTurn-1234-5678"
TS = "2026-11-12T11:59:12"


def check(gate, cond, ev=""):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


TRANSCRIPT = Path(TMP) / f"{SID}.jsonl"
TRANSCRIPT.write_text(json.dumps({"type": "user", "timestamp": TS + ".172Z", "uuid": "turn-uuid-1",
                                  "message": {"content": "recarga y si no sale cambia de estrategia"}}) + "\n",
                      encoding="utf-8")
FINDER = lambda sid: TRANSCRIPT if sid == SID else None   # noqa: E731


def _mission(mid: str, authority: int = 20_000_000, topups: int | None = 2, hold=None, state=None) -> dict:
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW, state=state or gm.RUNNING,
                  epoch=1, authority_tokens=authority, owner_hold=hold)
    if topups is not None:
        gm.set_topups(mid, topups, "4M", f"{SID}:{TS}", finder=FINDER, now=NOW)
    return gm.load(mid)


def _spent_for_room(rec: dict, room: int) -> int:
    return int(rec["authority_tokens"]) - int(ms.closeout_reserve(rec) or 0) - room


def main() -> int:
    seen = []
    note = lambda mid, key, why: seen.append((mid, key, why))   # noqa: E731

    r = _mission("m-due")
    spent = _spent_for_room(r, 1_300_000)
    row = gm.apply_topup(r, NOW + 60, measure=lambda rec: spent, notifier=note)
    a = gm.load("m-due")
    last = (a.get("authority_receipts") or [{}])[-1]
    check("V-TOPUP-APPLIES", row and a["authority_tokens"] == 24_000_000 and a["topups"]["left"] == 1
          and last.get("actor") == "sweep:topup" and (last.get("owner_turn") or {}).get("uuid") == "turn-uuid-1"
          and last.get("spent_at_set") == spent,
          f"row={row} auth={a.get('authority_tokens')} topups={a.get('topups', {}).get('left')} last={last.get('actor')}")
    ev = [e.get("event") for e in gm.lr.ledger_events("m-due")]
    check("V-TOPUP-LEDGERED", "topup_applied" in ev and "topups_set" in ev, str(ev[-4:]))
    check("V-TOPUP-NOTIFIED", len(seen) == 1 and seen[0][1] == "topup:m-due:1", str(seen))
    again = gm.apply_topup(gm.load("m-due"), NOW + 120, measure=lambda rec: spent, notifier=note)
    check("V-TOPUP-ONCE", again is None and gm.load("m-due")["authority_tokens"] == 24_000_000,
          f"second pass at room ~5.3M: {again}")

    # Review 2026-11-12 (HIGH): after one top-up was spent, re-running the same Owner turn must not reset `left`.
    replay = gm.set_topups("m-due", 2, "4M", f"{SID}:{TS}", finder=FINDER, now=NOW + 200)
    other = ""
    try:
        gm.set_topups("m-due", 5, "4M", f"{SID}:{TS}", finder=FINDER, now=NOW + 200)
    except gm.MissionError as exc:
        other = str(exc)
    check("V-TOPUP-REPLAY-NOOP", replay["topups"]["left"] == 1 and gm.load("m-due")["topups"]["left"] == 1
          and "already granted" in other, f"left={gm.load('m-due')['topups'].get('left')} other={other[:90]}")

    r = _mission("m-room")
    check("V-TOPUP-ROOM", gm.apply_topup(r, NOW, measure=lambda rec: _spent_for_room(r, 5_000_000)) is None
          and gm.load("m-room")["authority_tokens"] == 20_000_000, "room 5M >= 3M trigger")

    r = _mission("m-none", topups=0)
    check("V-TOPUP-NONE-LEFT", gm.apply_topup(r, NOW, measure=lambda rec: _spent_for_room(r, 100)) is None, "left 0")
    r = _mission("m-nogrant", topups=None)
    check("V-TOPUP-NO-GRANT", gm.apply_topup(r, NOW, measure=lambda rec: _spent_for_room(r, 100)) is None,
          "authority without a typed top-up grant")

    r = _mission("m-unm")
    boom = lambda rec: (_ for _ in ()).throw(OSError("no transcript"))   # noqa: E731
    check("V-TOPUP-UNMEASURED", gm.apply_topup(r, NOW, measure=boom) is None
          and gm.apply_topup(r, NOW, measure=lambda rec: None) is None
          and gm.load("m-unm")["authority_tokens"] == 20_000_000, "raising and None spend both refuse")

    r = _mission("m-cost", hold={"kind": "cost", "reason": "cost breaker (mission authority): spent", "set_at": NOW})
    check("V-TOPUP-OWNER-HOLD", gm.apply_topup(r, NOW, measure=lambda rec: _spent_for_room(r, 100)) is None,
          "a tripped breaker stays the Owner path")
    r = _mission("m-own", hold={"kind": "owner", "reason": "Owner hold", "set_at": NOW})
    check("V-TOPUP-OWNER-HOLD-2", gm.apply_topup(r, NOW, measure=lambda rec: _spent_for_room(r, 100)) is None, "")
    r = _mission("m-cp", hold={"kind": gm.CHECKPOINT_KIND, "reason": "NEXT_PLAN_REQUIRED: x", "set_at": NOW})
    check("V-TOPUP-CHECKPOINT-OK", gm.apply_topup(r, NOW, measure=lambda rec: _spent_for_room(r, 100),
                                                  notifier=note) is not None, "a checkpoint wait may be topped up")
    r = _mission("m-term", state=gm.HALTED)
    check("V-TOPUP-TERMINAL", gm.apply_topup(r, NOW, measure=lambda rec: _spent_for_room(r, 100)) is None, "")

    refused = ""
    try:
        gm.set_topups("m-room", 1, "4M", None, finder=FINDER)
    except gm.MissionError as exc:
        refused = str(exc)
    bad_turn = ""
    try:
        gm.set_topups("m-room", 1, "4M", f"{SID}:2001-01-01T00:00:00", finder=FINDER)
    except gm.MissionError as exc:
        bad_turn = str(exc)
    check("V-TOPUP-SET-NEEDS-TURN", "owner-turn" in refused and "0 Owner message" in bad_turn, f"{refused} | {bad_turn}")

    r = _mission("m-off")
    os.environ["CPP_MISSION_TOPUP"] = "off"
    off_rows = gm.topup_pass(NOW, measure=lambda rec: _spent_for_room(rec, 100))   # due if the switch were ignored
    os.environ.pop("CPP_MISSION_TOPUP")
    check("V-TOPUP-OFF", off_rows == [] and gm.load("m-off")["authority_tokens"] == 20_000_000, str(off_rows))

    called = []
    real = gm.topup_pass
    gm.topup_pass = lambda *a, **k: called.append(1) or []
    try:
        gm.supervise()
    except Exception as exc:  # noqa: BLE001 -- the wiring question is whether the pass was reached
        print(f"  (supervise raised {type(exc).__name__}: {exc})")
    gm.topup_pass = real
    check("V-TOPUP-WIRED", called == [1], f"supervise reached topup_pass {len(called)} time(s)")
    called.clear()
    gm.topup_pass = lambda *a, **k: called.append(1) or []
    gm.supervise(None, True)
    gm.topup_pass = real
    check("V-TOPUP-NOT-IN-DRY-RUN", called == [], f"dry run reached topup_pass {len(called)} time(s)")

    on = gm.arm(TMP, "/gsd-autonomous", launch=False, preflighted=True, mission_id="m-arm-on")["mission"]
    off = gm.arm(TMP, "/gsd-autonomous", launch=False, preflighted=True, pivot=False, mission_id="m-arm-off")["mission"]
    check("V-ARM-PIVOT-DEFAULT", gm.load(on["mission_id"]).get("pivot_autonomy") is True, on["mission_id"])
    check("V-ARM-NO-PIVOT", not gm.load(off["mission_id"]).get("pivot_autonomy"), off["mission_id"])

    print(f"TOPUP_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


DRILLS = (
    ("T1 trigger ignored", "    if room >= TOPUP_TRIGGER_TOKENS:\n", "    if False:\n", "V-TOPUP-ROOM"),
    ("T2 owner/cost hold ignored", "    if hold and hold.get(\"kind\") not in WAIT_HOLD_KINDS:\n        return False, f\"under",
     "    if False:\n        return False, f\"under", "V-TOPUP-OWNER-HOLD"),
    # Reading unmeasured as ZERO is fail-safe here (huge room, no top-up), so that mutant is equivalent; the harmful
    # direction is unmeasured read as EXHAUSTED, which would spend capital nobody measured.
    ("T3 unmeasured read as exhausted", "    if spent is None:\n        return False, \"spend unmeasurable\", {}\n",
     "    if spent is None:\n        spent = int(rec[\"authority_tokens\"])\n", "V-TOPUP-UNMEASURED"),
    ("T4 left not decremented", "t.update(left=int(t[\"left\"]) - 1, used=n)", "t.update(used=n)", "V-TOPUP-APPLIES"),
    ("T5 pass unwired", "            rows = rows + topup_pass()\n", "            rows = rows\n", "V-TOPUP-WIRED"),
    ("T6 kill switch ignored", "    if not topup_on():\n        return []\n", "", "V-TOPUP-OFF"),
    ("T7 turn not required", "    if not owner_turn:\n        raise MissionError(\"refused: top-ups are capital",
     "    if False:\n        raise MissionError(\"refused: top-ups are capital", "V-TOPUP-SET-NEEDS-TURN"),
    ("T9 owner turn replay resets the grant",
     '    if old_turn.get("uuid") == turn["uuid"] and old_turn.get("session") == turn["session"]:',
     "    if False:", "V-TOPUP-REPLAY-NOOP"),
    ("T8 arm default off", "    if pivot and pivot_autonomy_on():\n", "    if False:\n", "V-ARM-PIVOT-DEFAULT"),
)


def drills() -> int:
    import subprocess
    here = Path(__file__).resolve().parent
    src = (here / "gsd_mission.py").read_text(encoding="utf-8")
    ok = 0
    for name, needle, repl, gate in DRILLS:
        if needle not in src:
            print(f"DRILL-FAIL {name}: needle absent from tools/gsd_mission.py")
            continue
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "gsd_mission.py").write_text(src.replace(needle, repl, 1), encoding="utf-8")
            r = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve())], capture_output=True, text=True,
                               env={**os.environ, "GSD_MISSION_DRILL_DIR": td}, timeout=300)
        red = f"FAIL {gate}" in r.stdout
        print(f"{'DRILL-PASS' if red else 'DRILL-FAIL'} {name}: expected 'FAIL {gate}' -> {'seen' if red else 'NOT seen'}")
        ok += int(red)
    print(f"TOPUP_DRILLS_PASS={ok}/{len(DRILLS)}")
    return 0 if ok == len(DRILLS) else 1


if __name__ == "__main__":
    sys.exit(drills() if "--drills" in sys.argv[1:] else main())
