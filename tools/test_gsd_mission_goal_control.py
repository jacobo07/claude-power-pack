#!/usr/bin/env python
"""V-GGMC-* gates for goal-governed mission control (spec vault/specs/goal-governed-mission-control.md).

Hermetic, like test_gsd_mission_owner_hold.py: state goes to a temp dir BEFORE import. Every refusal has a
paired control, so a module that refuses (or renews) everything cannot go green.

Mutation drill: GSD_MISSION_DRILL_DIR names a directory holding a mutated copy of gsd_mission.py; it is
imported instead of the real module, so the live file (loaded by the running supervisor) is never edited.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="gsd-mission-goal-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ.pop("CPP_MISSION_RENEW", None)
os.environ.pop("CPP_MISSION_BOUNDED_RENEWAL", None)
sys.path.insert(0, str(Path(__file__).resolve().parent))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
import gsd_mission as gm  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None

passes = fails = 0
NOW = 1_800_000_000.0
BUDGET_HALT = "owner BLOCKED and budget: older than 1.0 h"


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def _halted(mid: str, *, epoch: int, **fields) -> dict:
    """A HALTED record as the supervisor leaves it after a budget halt."""
    gm.create(TMP, "/gsd-autonomous --ws ws-a", mission_id=mid, now=NOW)
    return gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW,
                         state=gm.HALTED, epoch=epoch, reason=BUDGET_HALT, **fields)


def _ledger(mid: str, event: str) -> int:
    return sum(1 for e in gm.lr.ledger_events(mid) if e.get("event") == event)


def main() -> int:
    pkt = Path(TMP) / "wu.md"
    pkt.write_text("work unit\n", encoding="utf-8")
    wu = {"path": str(pkt), "sha256": "x", "bytes": 10, "set_at": NOW}

    # C1: a renewal keeps the route; never the admission.
    src = _halted("m-bound", epoch=1, token_estimate=3_500_000, note="CLOSEOUT_PLAN_v3 envelope",
                  wu_packet=wu, wu_packet_epoch=1, admission={"verdict": "ADMISSIBLE", "consumed_epoch": 1})
    check("V-GGMC-CONTROL-SOURCE-HAS-ROUTE", src.get("token_estimate") and src.get("wu_packet"))
    new = gm.renew_mission(src, now=NOW)
    check("V-GGMC-RENEWAL-CARRIES-ESTIMATE", new.get("token_estimate") == 3_500_000, str(new.get("token_estimate")))
    check("V-GGMC-RENEWAL-CARRIES-PACKET", (new.get("wu_packet") or {}).get("path") == str(pkt)
          and new.get("wu_packet_epoch") == 0, f"{new.get('wu_packet')} e{new.get('wu_packet_epoch')}")
    check("V-GGMC-RENEWAL-CARRIES-NOTE", new.get("note") == "CLOSEOUT_PLAN_v3 envelope", repr(new.get("note")))
    check("V-GGMC-RENEWAL-NEVER-CARRIES-ADMISSION", not new.get("admission"), str(new.get("admission")))
    check("V-GGMC-BOUNDED-NO-SHADOW-ROW", _ledger("m-bound", "renewal_unbounded_shadow") == 0)

    # C2: unbounded renewal -- shadow ledgers and renews; enforce refuses; bounded control renews in both.
    unb = _halted("m-unb", epoch=1)
    check("V-GGMC-SHADOW-RENEWS-UNBOUNDED", gm.renewal_refusal(unb, BUDGET_HALT, "OK") is None)
    gm.renew_mission(unb, now=NOW)
    check("V-GGMC-SHADOW-LEDGERS-UNBOUNDED", _ledger("m-unb", "renewal_unbounded_shadow") == 1)
    os.environ["CPP_MISSION_BOUNDED_RENEWAL"] = "enforce"
    try:
        why = gm.renewal_refusal(unb, BUDGET_HALT, "OK")
        check("V-GGMC-ENFORCE-REFUSES-UNBOUNDED", bool(why) and "unbounded" in why, str(why))
        check("V-GGMC-ENFORCE-CONTROL-BOUNDED-RENEWS", gm.renewal_refusal(src, BUDGET_HALT, "OK") is None)
    finally:
        os.environ["CPP_MISSION_BOUNDED_RENEWAL"] = "off"
    try:
        check("V-GGMC-OFF-RENEWS-UNBOUNDED", gm.renewal_refusal(unb, BUDGET_HALT, "OK") is None)
    finally:
        os.environ.pop("CPP_MISSION_BOUNDED_RENEWAL", None)

    # C3: a never-launched attempt does not renew; a launched one does (control above: m-unb, epoch 1).
    never = _halted("m-never", epoch=0, token_estimate=1_000_000)
    why = gm.renewal_refusal(never, BUDGET_HALT, "OK")
    check("V-GGMC-NEVER-LAUNCHED-REFUSED", bool(why) and "never launched" in why, str(why))
    check("V-GGMC-NEVER-LAUNCHED-CONTROL", gm.renewal_refusal({**never, "epoch": 1}, BUDGET_HALT, "OK") is None)

    # C4: the Goal is the authority; a new mission id is not.
    def arm(ws, **kw):
        return gm.arm(TMP, f"/gsd-autonomous --ws {ws}", launch=False, now=NOW, **kw)["mission"]

    def refused(fn, needle):
        try:
            fn()
        except gm.MissionError as exc:
            return needle in str(exc)
        return False

    first = arm("ws-g")
    check("V-GGMC-GOAL-BOUND", (first.get("goal") or {}).get("workstream") == "ws-g", str(first.get("goal")))
    check("V-GGMC-SINGLEFLIGHT-REFUSED", refused(lambda: arm("ws-g"), "singleflight"))
    check("V-GGMC-SINGLEFLIGHT-CONTROL-OTHER-GOAL", arm("ws-h")["state"] == gm.PREPARED)
    other_repo = Path(TMP) / "other-repo"
    other_repo.mkdir()
    check("V-GGMC-SINGLEFLIGHT-CONTROL-OTHER-REPO",
          gm.arm(str(other_repo), "/gsd-autonomous --ws ws-g", launch=False, now=NOW)["mission"]["state"] == gm.PREPARED)

    gm.set_owner_hold(first["mission_id"], "Owner park", now=NOW)
    check("V-GGMC-GOAL-HOLD-REFUSES-NEW-ID", refused(lambda: arm("ws-g"), "goal held"))
    check("V-GGMC-GOAL-HOLD-COVERS-UNITS", refused(lambda: arm("ws-g", parallel_unit="u9"), "goal held"))
    check("V-GGMC-SUPERSEDE-NEEDS-AUTHORITY",
          refused(lambda: arm("ws-g", supersedes=first["mission_id"]), "--authority"))
    succ = arm("ws-g", supersedes=first["mission_id"], authority="Owner 'y' 2026-10-06, plan v3")
    old = gm.load(first["mission_id"])
    check("V-GGMC-SUPERSEDE-WITH-AUTHORITY", succ.get("supersedes") == first["mission_id"]
          and "Owner" in (succ.get("authority") or "") and old["state"] == gm.HALTED
          and succ["mission_id"] in (old.get("reason") or ""), f"{old['state']} {old.get('reason')}")
    check("V-GGMC-SUPERSEDE-FOREIGN-GOAL-REFUSED",
          refused(lambda: arm("ws-h", supersedes=succ["mission_id"], authority="Owner"), "not an attempt of this goal"))

    u1 = arm("ws-p", parallel_unit="u1")
    check("V-GGMC-PARALLEL-DISTINCT-UNIT-ALLOWED", arm("ws-p", parallel_unit="u2")["state"] == gm.PREPARED)
    check("V-GGMC-PARALLEL-SAME-UNIT-REFUSED", refused(lambda: arm("ws-p", parallel_unit="u1"), "singleflight"))
    check("V-GGMC-PARALLEL-UNNAMED-REFUSED", refused(lambda: arm("ws-p"), "singleflight"))

    # Renewal obeys the Goal: a halted attempt of ws-p does not renew beside a live sibling unit.
    halted = gm.transition(u1["mission_id"], expect_epoch=0, expect_state=gm.PREPARED, event="t_halt", now=NOW,
                           state=gm.HALTED, epoch=1, reason=BUDGET_HALT, token_estimate=1_000_000)
    halted = {**halted, "goal": {**halted["goal"], "unit": "u2"}}   # same unit as the live u2 sibling
    why = gm._renewal_why_not(halted, BUDGET_HALT, {"outcome": "OK"}, TMP, fingerprint=lambda w: None)
    check("V-GGMC-RENEWAL-OBEYS-SINGLEFLIGHT", bool(why) and "singleflight" in why, str(why))
    lone = gm.transition(gm.arm(TMP, "/gsd-autonomous --ws ws-lone", launch=False, now=NOW)["mission"]["mission_id"],
                         expect_epoch=0, expect_state=gm.PREPARED, event="t_halt", now=NOW, state=gm.HALTED,
                         epoch=1, reason=BUDGET_HALT, token_estimate=1_000_000)
    check("V-GGMC-RENEWAL-CONTROL-LONE-GOAL",
          gm._renewal_why_not(lone, BUDGET_HALT, {"outcome": "OK"}, TMP, fingerprint=lambda w: None) is None)

    print(f"GOAL_CONTROL_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
