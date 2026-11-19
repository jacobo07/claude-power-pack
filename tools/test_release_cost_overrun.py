#!/usr/bin/env python
"""V-RCO-* gates: release_owner_hold refuses to lift a COST hold under a ceiling already crossed (W0 2026-11-19).

Origin: SkyParty C5 (m-a8f0221b1acc) was released right after `budget` refused the raise, so a worker ran
against an authority its spend had already passed. Hermetic, like test_gsd_mission_owner_hold.py: state goes to
a temp dir BEFORE import and spend is injected. Every refusal has a paired control, so a release that refuses
everything (or nothing) cannot go green.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="gsd-release-overrun-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ.pop("CPP_MISSION_RENEW", None)
os.environ["CPP_MISSION_RECOVERY"] = "off"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_mission as gm  # noqa: E402
import mission_spend as ms  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None
NOW = 1_800_000_000.0
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def held(mid: str, kind: str, authority: int) -> None:
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW, authority_tokens=authority)
    gm.set_owner_hold(mid, "cost breaker (mission authority): test" if kind == "cost" else "owner pause: test",
                      now=NOW, kind=kind if kind == "cost" else None)


def release(mid: str, spent, **kw):
    real = ms.processed_tokens
    ms.processed_tokens = lambda rec, *a, **k: spent
    try:
        return gm.release_owner_hold(mid, now=NOW + 60, **kw), None
    except gm.MissionError as e:
        return None, str(e)
    finally:
        ms.processed_tokens = real


held("m-rco000000001", "cost", 2_000_000)
_, err = release("m-rco000000001", 4_500_000)
check("V-RCO-REFUSE-CROSSED", err is not None and "not above live spend" in err, err or "released")

held("m-rco000000002", "cost", 8_000_000)
out, err = release("m-rco000000002", 4_500_000)
check("V-RCO-CONTROL-ROOM-RELEASES", err is None and out and not out.get("owner_hold"), err or "")

held("m-rco000000003", "cost", 2_000_000)
out, err = release("m-rco000000003", 4_500_000, allow_overrun=True)
check("V-RCO-ALLOW-OVERRUN-RELEASES", err is None and out and not out.get("owner_hold"), err or "")

held("m-rco000000004", "cost", 2_000_000)
out, err = release("m-rco000000004", None)
check("V-RCO-UNMEASURED-NOT-REFUSED", err is None and out is not None, err or "")

held("m-rco000000005", "owner", 2_000_000)
out, err = release("m-rco000000005", 4_500_000)
check("V-RCO-NON-COST-HOLD-UNTOUCHED", err is None and out is not None, err or "")

print(f"RELEASE_COST_OVERRUN_PASS={passes}/{passes + fails}  threshold=5/5")
sys.exit(0 if fails == 0 and passes == 5 else 1)
