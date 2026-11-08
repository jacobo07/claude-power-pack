#!/usr/bin/env python
"""V-CCRADMIT-* gates: the CCR pre-launch cost contract inside gsd_mission.admit_route (WU-W1).
Hermetic: state and PGO dir are temp dirs set BEFORE import."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="mission-ccr-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_CCR_PGO_DIR"] = str(Path(TMP) / "pgo")
os.environ.pop("CPP_CCR_ADMISSION", None)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_mission as gm  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None
NOW = 1_800_000_000.0
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
    else:
        fails += 1
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def q(v):
    return {"p50": v, "p80": v}


def pgo(cls, floor, slope, calls):
    d = Path(TMP) / "pgo"
    d.mkdir(exist_ok=True)
    (d / f"{cls}.json").write_text(json.dumps({"cls": cls, "n": 5, "calls": q(calls), "floor": q(floor),
                                               "slope": q(slope), "step": {"p50": 1, "p95": 2, "n": 5}}),
                                   encoding="utf-8")


PKT = Path(TMP) / "WU-X.md"
PKT.write_text("# WU-X small unit\nDo it.\n", encoding="utf-8")
ROUTE = Path(TMP) / "route.json"
ROUTE.write_text('{"envelope": {"target": 3500000, "warn": 4500000, "stop": 5500000, "calls": 25}, '
                 '"workers": [{"name": "w", "profile": "top-level-worker", "calls": 25, "packet": 4000}]}',
                 encoding="utf-8")


def mission(mid, cls=None):
    gm.create(TMP, "/gsd-autonomous --ws wsx", mission_id=mid, now=NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW,
                  state=gm.RUNNING, epoch=1, cost_mark={"fp": "abc", "tokens": 5})
    gm.set_envelope(mid, wu_packet=str(PKT), ccr_class=cls, now=NOW) if cls else gm.set_envelope(
        mid, wu_packet=str(PKT), now=NOW)


def admit(mid):
    return gm.admit_route(mid, str(ROUTE), now=NOW, measure=lambda r: None)["admission"]


def main() -> int:
    mission("m-none")
    a = admit("m-none")
    check("V-CCRADMIT-NO-CLASS-UNFORECAST", a["ccr_contract"]["verdict"] == "UNFORECAST"
          and a["verdict"] in gm.LAUNCHABLE_VERDICTS, str(a["verdict"]))

    mission("m-nofile", "ghost")
    a = admit("m-nofile")
    check("V-CCRADMIT-NO-PGO-FILE-UNFORECAST", a["ccr_contract"]["verdict"] == "UNFORECAST"
          and a["verdict"] in gm.LAUNCHABLE_VERDICTS)

    pgo("big", 200_000, 5_000, 25)          # 5.0M + 1.5M = 6.5M > 5.5M
    mission("m-obs", "big")
    a = admit("m-obs")
    check("V-CCRADMIT-OBSERVE-RECORDS-ADMITS", a["ccr_contract"]["verdict"] == "SPLIT"
          and a["verdict"] in gm.LAUNCHABLE_VERDICTS, str(a["ccr_contract"].get("forecast")))

    os.environ["CPP_CCR_ADMISSION"] = "enforce"
    mission("m-enf", "big")
    a = admit("m-enf")
    check("V-CCRADMIT-ENFORCE-SPLIT-REFUSED", a["verdict"] not in gm.LAUNCHABLE_VERDICTS
          and "ccr_contract:SPLIT" in a["reasons"] and gm.admission_refusal(gm.load("m-enf")) is not None,
          str(a["verdict"]))

    pgo("small", 10_000, 100, 25)
    mission("m-ok", "small")
    a = admit("m-ok")
    check("V-CCRADMIT-ENFORCE-ADMIT-ADMITTED", a["ccr_contract"]["verdict"] == "ADMIT"
          and a["verdict"] in gm.LAUNCHABLE_VERDICTS, str(a["ccr_contract"]["verdict"]))
    os.environ.pop("CPP_CCR_ADMISSION")
    print(f"{passes} passed, {fails} failed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
