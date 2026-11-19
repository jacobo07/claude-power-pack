#!/usr/bin/env python
"""V-SLIM-* gates for the W0 slim worker (2026-11-19, SkyParty evidence-pyramid W0).

Two behaviours:
  P1 `envelope --worker-profile slim-t1|slim-t2|none` stores rec["worker_profile"] (src "owner"), which
     slim_profile() reads, so an ordinary mission reaches the `claude -p` slim launch with no compiled packet.
  P2 _declare_worker_envelope: a mission with no admitted packet but an Owner authority gets a session
     envelope from that authority (stop = authority - closeout reserve).
Measured why: on GEX44 a --bg worker cost ~192-216K per call; the slim drill (authority 400K) stopped at
405,980 processed, overrun 5,980 (pass bar 50K).

Hermetic like test_gsd_mission_envelope.py: state in a temp dir BEFORE import; mission_spend.declare and the
ledger are captured, never written to the real state. Every positive gate has a paired control.
"""
from __future__ import annotations

import io
import os
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="mission-slim-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ.pop("CPP_MISSION_RENEW", None)
sys.path.insert(0, str(Path(__file__).resolve().parent))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
import gsd_mission as gm  # noqa: E402
import mission_spend as ms  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None

passes = fails = 0
NOW = 1_800_000_000.0
DECLARED: list[tuple] = []
EVENTS: list[tuple] = []


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def _running(mid: str) -> dict:
    gm.create(TMP, "/gsd-autonomous --ws wsx", mission_id=mid, now=NOW)
    return gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW,
                         state=gm.RUNNING, epoch=1, cost_mark={"fp": "abc", "tokens": 5})


def main() -> int:
    ms.declare = lambda sid, target, warn, stop: DECLARED.append((sid, target, warn, stop))
    real_append = gm.lr.ledger_append
    gm.lr.ledger_append = lambda mid, event, **kw: EVENTS.append((mid, event, kw))
    try:
        # P1: the CLI flag stores the profile; slim_profile() reads it; "none" clears it.
        _running("m-slim")
        with redirect_stdout(io.StringIO()) as out:
            rc = gm._cli(["envelope", "--mission", "m-slim", "--token-estimate", "400K",
                          "--worker-profile", "slim-t2"])
        rec = gm.load("m-slim")
        check("V-SLIM-PROFILE-SET", rc == 0 and rec.get("worker_profile") == "slim-t2"
              and rec.get("worker_profile_src") == "owner" and gm.slim_profile(rec) == "slim-t2",
              f"rc={rc} prof={rec.get('worker_profile')} out={out.getvalue().strip()[:80]}")
        with redirect_stdout(io.StringIO()):
            rc = gm._cli(["envelope", "--mission", "m-slim", "--worker-profile", "none"])
        rec = gm.load("m-slim")
        check("V-SLIM-PROFILE-CLEAR", rc == 0 and rec.get("worker_profile") is None
              and gm.slim_profile(rec) is None, f"prof={rec.get('worker_profile')}")
        # control: an envelope call without the flag leaves the profile untouched.
        with redirect_stdout(io.StringIO()):
            gm._cli(["envelope", "--mission", "m-slim", "--worker-profile", "slim-t1"])
            gm._cli(["envelope", "--mission", "m-slim", "--token-estimate", "500K"])
        check("V-SLIM-PROFILE-STICKY", gm.load("m-slim").get("worker_profile") == "slim-t1")

        # P2: authority, no packet -> session envelope stop = authority - closeout reserve.
        rec = {"mission_id": "m-a", "authority_tokens": 400_000}
        gm._declare_worker_envelope(rec, "sid-a")
        reserve = ms.closeout_reserve(rec)
        check("V-SLIM-ENVELOPE-FROM-AUTHORITY",
              DECLARED[-1:] == [("sid-a", int((400_000 - reserve) * 0.8), int((400_000 - reserve) * 0.9),
                                 400_000 - reserve)] and reserve == 20_000
              and EVENTS[-1][1] == "worker_envelope_declared",
              f"declared={DECLARED[-1:]} reserve={reserve}")
        # controls: no sid, no authority -> nothing declared, nothing recorded.
        n_d, n_e = len(DECLARED), len(EVENTS)
        gm._declare_worker_envelope({"mission_id": "m-b", "authority_tokens": 400_000}, None)
        gm._declare_worker_envelope({"mission_id": "m-c"}, "sid-c")
        check("V-SLIM-ENVELOPE-NEEDS-SID-AND-AUTHORITY", len(DECLARED) == n_d and len(EVENTS) == n_e,
              f"declared+={len(DECLARED) - n_d} events+={len(EVENTS) - n_e}")
        # an authority the closeout reserve swallows is refused LOUDLY, never declared.
        gm._declare_worker_envelope({"mission_id": "m-d", "authority_tokens": 100_000,
                                     "closeout_tokens": 100_000}, "sid-d")
        check("V-SLIM-ENVELOPE-NO-ROOM-RECORDED", len(DECLARED) == n_d
              and EVENTS[-1][1] == "worker_envelope_failed", f"last={EVENTS[-1][1]}")
        # control: an admitted packet still takes the admission path, not the authority path.
        n_e = len(EVENTS)
        gm._declare_worker_envelope({"mission_id": "m-e", "authority_tokens": 400_000,
                                     "wu_packet": {"path": "x"}, "admission": {"verdict": "REFUSED"}}, "sid-e")
        check("V-SLIM-PACKET-PATH-UNCHANGED", len(EVENTS) == n_e and len(DECLARED) == n_d,
              f"events+={len(EVENTS) - n_e}")
    finally:
        gm.lr.ledger_append = real_append
    print(f"\n{passes} passed, {fails} failed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
