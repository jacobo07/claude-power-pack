"""V-OBD: an Owner wait is typed, quantified, queued without grace, visible, and cleared on release.

Red pole: the pre-fix _amr_boundary wrote "spent None of ceiling None", no queue row, and the digest hid a
fresh row for 24 h. Green pole: a typed CAPITAL_EXHAUSTED wait with real figures reaches the next SessionStart.
Run: python tools/test_owner_boundary_delivery.py   (exit 0 = all gates pass)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="obd-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["CLAUDE_CONFIG_DIR"] = str(Path(TMP) / "cc")
QDIR = str(Path(TMP) / "queue")
os.environ["PP_OWNER_QUEUE_STATE_DIR"] = QDIR
for k in ("CPP_MISSION_RECOVERY", "CPP_ROUTE_ADMISSION", "CPP_CCR_ADMISSION", "CPP_COG_ADMISSION"):
    os.environ.pop(k, None)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import gsd_mission as gm  # noqa: E402
import mission_recovery as mr  # noqa: E402
from modules.owner_queue import owner_queue as oq  # noqa: E402

NOW = 1_800_000_000.0
BREAKER = "cost breaker: processed 156,097,796 >= authority 155,000,000 minus 1,000,000 closeout reserve"
passes = fails = 0


def check(gate: str, cond: bool, ev: str = "") -> None:
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}"[:200])
    else:
        fails += 1
        print(f"FAIL {gate} {ev}"[:300])


def main() -> int:
    # --- classifier + figures (pure) ---------------------------------------------------------------------
    check("V-OBD-TYPE-CAPITAL", gm.owner_wait_type("no materially different strategy", BREAKER) == "CAPITAL_EXHAUSTED")
    check("V-OBD-TYPE-SECURITY", gm.owner_wait_type("workspace trust dialog not accepted") == "SECURITY_BOUNDARY")
    check("V-OBD-TYPE-UNKNOWN-CONTROL", gm.owner_wait_type("something nobody classified") == "UNKNOWN")
    figs = gm.owner_wait_figures(BREAKER, {"spent": None, "ceiling": None})
    check("V-OBD-FIGURES-FROM-HOLD", figs == {"spent": 156097796, "ceiling": 155000000}, str(figs))
    check("V-OBD-FIGURES-ABSENT-NOT-ZERO", gm.owner_wait_figures("no numbers here", {}) == {})

    # --- queue: urgent row skips the grace window; a normal fresh row does not ---------------------------
    fresh = datetime(2027, 1, 15, 8, 0, tzinfo=timezone.utc)
    oq.append("normal", "cmd-a", state_dir=QDIR, now=fresh)
    oq.append("urgent", "cmd-b", state_dir=QDIR, now=fresh, urgent=True)
    dig = oq.sessionstart_digest(QDIR, now=fresh) or ""
    check("V-OBD-QUEUE-URGENT-NO-GRACE", "urgent" in dig and "normal" not in dig, dig[:160])

    # --- end to end: a budget-exhausted mission parks as a typed, queued, visible wait -------------------
    wd = Path(TMP) / "wt"
    wd.mkdir()
    git = gm.resolve_exe("git")
    subprocess.run([git, "-C", str(wd), "init", "-q"], check=True)
    mid = "m-obd000000001"
    gm.create(str(wd), "/gsd-autonomous --ws obd", mission_id=mid, workstream="obd", now=NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW, state=gm.RUNNING, epoch=2,
                  max_hours=100.0)
    gm.set_owner_hold(mid, BREAKER, now=NOW, kind="cost")
    rec = gm.load(mid)
    gm._amr_boundary(rec, {"boundary": "no materially different strategy known for UNCLASSIFIED", "unit": None,
                           "failure": None}, NOW + 5, rec.get("owner_hold"))
    after = gm.load(mid)
    wait = (after.get("owner_hold") or {}).get("wait") or {}
    check("V-OBD-HOLD-TYPED", wait.get("type") == "CAPITAL_EXHAUSTED" and wait.get("figures", {}).get("spent") == 156097796,
          str(wait)[:200])
    pkt = Path(wait.get("packet", "x")).read_text(encoding="utf-8") if wait.get("packet") else ""
    check("V-OBD-PACKET-REAL-FIGURES", "156,097,796" in pkt and "None" not in pkt and "WAIT TYPE: CAPITAL_EXHAUSTED" in pkt,
          pkt[:200])
    row = {r["id"]: r for r in oq.load(QDIR)}.get(f"q-wait-{mid}")
    check("V-OBD-QUEUED-URGENT", bool(row) and row["urgent"] and row["status"] == "pending", str(row)[:200])
    same_minute = oq.sessionstart_digest(QDIR) or ""
    check("V-OBD-VISIBLE-NEXT-SESSIONSTART", mid in same_minute and "CAPITAL_EXHAUSTED" in same_minute, same_minute[:200])
    topo = gm.topology(mid) if hasattr(gm, "topology") else {}
    check("V-OBD-NOT-RUNNING-LABEL", mr.goal_liveness(after) == "WAITING_OWNER", mr.goal_liveness(after))
    pending_json = json.loads((Path(QDIR) / "OWNER_QUEUE.pending.json").read_text(encoding="utf-8"))
    check("V-OBD-HUB-SEES-URGENT-FLAG", any(r.get("urgent") is True for r in pending_json), "pending.json carries urgent")

    # --- release clears the row (no stale urgent noise forever) -----------------------------------------
    gm.release_owner_hold(mid, now=NOW + 60)
    row2 = {r["id"]: r for r in oq.load(QDIR)}.get(f"q-wait-{mid}")
    check("V-OBD-RELEASE-CLEARS-ROW", row2 is not None and row2["status"] == "done", str(row2)[:120])
    check("V-OBD-UNKNOWN-IS-NOT-LIVENESS-INCIDENT-CONTROL", mr.goal_liveness({"state": "RUNNING", "owner_hold": {
        "reason": "x", "recovery": {"state": mr.OWNER_BOUNDARY}}}) == "OWNER_BOUNDARY",
        "a boundary with no typed wait keeps the legacy label (control)")

    print(f"OBD_PASS={passes}/{passes + fails}  threshold=all")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
