#!/usr/bin/env python
"""V-ENVREQ-* gates: a launch with no token_estimate AND no wu_packet is refused (enforce) or ledgered
as would-refuse (shadow) unless the record carries an Owner waiver; a refusal no sweep can cure parks the
mission BLOCKED once instead of being retried every pass (tools/gsd_mission.py launch_worker /
envelope_missing / uncurable_launch_refusal / park_uncurable_launch / unpark_cured_launch / supervise).

Origin: cep-gen3 T1 (vault/plans/cep-gen3-universal-economy-2026-10-07.md). Recon-factory ran 15 missions
with token_estimate None on all (1.18 G processed); admission ran only `if rec.get("wu_packet")`. The first
gen3 arming was refused 86 times over 8 h, once per pass, for an admission nobody had recorded.

Hermetic like test_gsd_mission_admission.py: state in a temp dir BEFORE import, an injected runner, no real
worker. Every refuse pole has an admit control, so a gate that refuses or admits everything cannot go green.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

TMP = tempfile.mkdtemp(prefix="gsd-mission-envreq-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
for var in ("CPP_MISSION_RENEW", "CPP_ROUTE_ADMISSION", "CPP_MISSION_ENVELOPE_REQUIRED"):
    os.environ.pop(var, None)
os.environ["CPP_CLAUDE_EXE"] = "__no_such_claude_in_tests__"
sys.path.insert(0, str(Path(__file__).resolve().parent))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
import gsd_mission as gm  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None

passes = fails = 0
NOW = 1_800_000_000.0
calls: list = []


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def runner(argv, cwd):
    calls.append(argv)
    return SimpleNamespace(stdout=f"backgrounded · c0ffee{len(calls):02x} · {argv[3]}", stderr="", returncode=0)


def prepared(mid: str) -> dict:
    return gm.create(TMP, "/gsd-autonomous --ws wsx", mission_id=mid, now=NOW)


def launch(mid: str) -> dict:
    cur = gm.load(mid)
    return gm.launch_worker(mid, expect_epoch=cur["epoch"], expect_state=cur["state"], reason="t",
                            runner=runner, now=NOW)


def events(mid: str, name: str) -> list:
    return [e for e in gm.lr.ledger_events(mid) if e.get("event") == name]


def main() -> int:
    # 1. enforce: no estimate, no packet, no waiver -> refused BEFORE the claim, row written
    os.environ["CPP_MISSION_ENVELOPE_REQUIRED"] = "enforce"
    prepared("m-bare")
    n = len(calls)
    res = launch("m-bare")
    check("V-ENVREQ-ENFORCE-REFUSES", res["ok"] is False and len(calls) == n and gm.load("m-bare")["epoch"] == 0
          and "no envelope" in res["why"], res.get("why", "")[:80])
    check("V-ENVREQ-REFUSAL-LEDGERED", len(events("m-bare", "launch_refused_no_envelope")) == 1)

    # 2. enforce admit poles: estimate / packet / waiver each launch
    prepared("m-est")
    gm.set_envelope("m-est", token_estimate="4M", now=NOW)
    check("V-ENVREQ-ADMIT-ESTIMATE", launch("m-est")["ok"] is True)
    prepared("m-pkt")
    pkt = Path(TMP) / "WU.md"
    pkt.write_text("# WU\n", encoding="utf-8")
    gm.set_envelope("m-pkt", wu_packet=str(pkt), now=NOW)
    ok_before = gm.envelope_missing(gm.load("m-pkt"))
    # a packet is admitted by envelope_missing; route admission (not this gate) then judges it
    check("V-ENVREQ-PACKET-NOT-MISSING", ok_before is False)
    prepared("m-waive")
    gm.set_envelope("m-waive", waiver_reason="Owner y 2026-10-07: one-off probe, no breaker wanted", now=NOW)
    check("V-ENVREQ-ADMIT-WAIVER", launch("m-waive")["ok"] is True
          and gm.load("m-waive")["envelope_waiver"]["reason"].startswith("Owner y"))
    try:
        gm.set_envelope("m-waive", waiver_reason="   ", now=NOW)
        blank_refused = False
    except gm.MissionError:
        blank_refused = True
    check("V-ENVREQ-BLANK-WAIVER-REFUSED", blank_refused)

    # 3. shadow (default): the row is written and the launch proceeds
    os.environ.pop("CPP_MISSION_ENVELOPE_REQUIRED")
    prepared("m-shadow")
    res = launch("m-shadow")
    check("V-ENVREQ-SHADOW-LAUNCHES", res["ok"] is True and len(events("m-shadow", "would_refuse_no_envelope")) == 1
          and not events("m-shadow", "launch_refused_no_envelope"))
    prepared("m-shadow-ok")
    gm.set_envelope("m-shadow-ok", token_estimate="4M", now=NOW)
    launch("m-shadow-ok")
    check("V-ENVREQ-SHADOW-CONTROL-SILENT", not events("m-shadow-ok", "would_refuse_no_envelope"))
    os.environ["CPP_MISSION_ENVELOPE_REQUIRED"] = "off"
    prepared("m-off")
    check("V-ENVREQ-OFF-SILENT", launch("m-off")["ok"] is True and not events("m-off", "would_refuse_no_envelope"))
    os.environ["CPP_MISSION_ENVELOPE_REQUIRED"] = "bogus"
    check("V-ENVREQ-UNKNOWN-MODE-IS-SHADOW", gm.envelope_required_mode() == "shadow")

    # 4. an uncurable refusal parks ONCE (BLOCKED), is not retried, and un-parks when cured
    os.environ["CPP_MISSION_ENVELOPE_REQUIRED"] = "enforce"
    prepared("m-park")
    sup = dict(now=NOW, sessions=[], runner=runner, gsd_status=lambda *a, **k: {"outcome": "OK"})
    row1 = next((r for r in gm.supervise(**sup) if r["mission_id"] == "m-park"), {})
    rec = gm.load("m-park")
    check("V-ENVREQ-PARKED-ONCE", rec["state"] == gm.BLOCKED and rec.get("launch_hold") and row1.get("parked"),
          f"{rec['state']} {row1.get('parked', '')[:60]}")
    gm.supervise(**{**sup, "now": NOW + 300})
    gm.supervise(**{**sup, "now": NOW + 600})
    check("V-ENVREQ-NOT-RETRIED", len(events("m-park", "launch_refused_no_envelope")) == 1,
          str(len(events("m-park", "launch_refused_no_envelope"))))
    gm.set_envelope("m-park", token_estimate="4M", now=NOW + 700)
    gm.supervise(**{**sup, "now": NOW + 900})
    cured = gm.load("m-park")
    check("V-ENVREQ-UNPARKED-WHEN-CURED", not cured.get("launch_hold") and cured["state"] != gm.BLOCKED
          and events("m-park", "launch_unparked"), cured["state"])

    # 5. a packet with no recorded admission is also parked once (the 86-row failure shape)
    prepared("m-unadm")
    gm.set_envelope("m-unadm", wu_packet=str(pkt), now=NOW)
    gm.supervise(**sup)
    gm.supervise(**{**sup, "now": NOW + 300})
    check("V-ENVREQ-UNADMITTED-PARKED-ONCE", gm.load("m-unadm")["state"] == gm.BLOCKED
          and len(events("m-unadm", "launch_refused_admission")) == 1)

    # 6. CLI waiver flag
    prepared("m-cli")
    rc = gm._cli(["envelope", "--mission", "m-cli", "--waiver-reason", "Owner waiver for the CLI pole"])
    check("V-ENVREQ-CLI-WAIVER", rc == 0 and gm.envelope_missing(gm.load("m-cli")) is False)

    print(f"ENVREQ_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
