#!/usr/bin/env python
"""V-PARK-* gates (ASC-02): `gsd_mission status` must not label a parked mission RUNNING.

Hermetic (temp state dir before import). Both poles: a held mission shows PARKED, a live
unheld mission still shows its raw state, `state` itself is unchanged for existing consumers.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="gsd-mission-park-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_MISSION_RECOVERY"] = "off"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_mission as gm  # noqa: E402

NOW = 1_800_000_000.0
FAILS = []


def check(name, cond, ev=""):
    print(("PASS " if cond else "FAIL ") + name + (f" {ev}" if not cond else ""))
    if not cond:
        FAILS.append(name)


def mk(mid, state):
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    owner = {"session_id": f"{mid}-w", "pid": 4242, "proc_start": None, "heartbeat_at": NOW,
             "epoch": 1, "kind": "background"}
    return gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t", now=NOW,
                         state=state, epoch=1, max_hours=1.0, owner=owner)


run = mk("m-live", gm.RUNNING)
held = gm.set_owner_hold(mk("m-held", gm.RUNNING)["mission_id"], "cost hold test", now=NOW, kind="cost")

# pure function, both poles
check("held RUNNING displays PARKED", hasattr(gm, "display_state") and gm.display_state(held).startswith("PARKED"),
      str(getattr(gm, "display_state", lambda r: "NO display_state")(held)))
check("unheld RUNNING still displays RUNNING (control)", hasattr(gm, "display_state")
      and gm.display_state(run) == "RUNNING")
check("held keeps raw state RUNNING (consumers unchanged)", held["state"] == gm.RUNNING)

# through the real CLI path
buf = io.StringIO()
with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
    rc = gm._cli(["status"])
rows = {r["mission_id"]: r for r in json.loads(buf.getvalue())}
check("CLI rc 0", rc == 0)
check("CLI row: held mission display_state PARKED", str(rows.get("m-held", {}).get("display_state", "")).startswith("PARKED"),
      str(rows.get("m-held", {}).get("display_state")))
check("CLI row: live mission display_state RUNNING", rows.get("m-live", {}).get("display_state") == "RUNNING")
check("CLI row: state field unchanged", rows["m-held"]["state"] == "RUNNING")
print("V-PARK", "FAIL" if FAILS else "PASS", FAILS or "")
sys.exit(1 if FAILS else 0)
