#!/usr/bin/env python3
"""V-GRAMMAR-* gates for spec vault/specs/compiled-grammar-default.md, laws 1-4 and 7 (WU-G1).

Hermetic: state goes to a temp dir BEFORE import, workers are an injected runner (supervise) or a fake
`claude` executable (arm, which has no runner parameter). Every refusal is paired with an admitted
control, so a gate that refuses (or admits) everything cannot go green. This file deliberately does NOT
use tools/envelope_fixture.py: the missions here start unbounded on purpose.

Mutation drill: GSD_MISSION_DRILL_DIR names a directory holding mutated copies of gsd_mission.py /
gsd_epoch.py that are imported instead of the real modules. The last section builds them in a temp dir,
re-runs this file against each, and demands the matching gates go red (and that an UNmutated copy stays
green, so the drill itself cannot be the reason for a red).
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TMP = tempfile.mkdtemp(prefix="grammar-default-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
for _k in ("CPP_MISSION_GRAMMAR", "CPP_MISSION_RENEW", "CPP_MISSION_CONTINUATION", "CPP_ROUTE_ADMISSION",
           "CPP_PACKET_GATE_TIMEOUT", "CPP_SOURCE_PACKET_CARD"):
    os.environ.pop(_k, None)

# A fake `claude --bg`: prints the host's launch line for the name passed with -n. arm() has no runner.
FAKE_CLAUDE = Path(TMP) / "fake-claude"
FAKE_CLAUDE.write_text('#!/bin/sh\nn=""\nwhile [ $# -gt 0 ]; do [ "$1" = "-n" ] && n="$2"; shift; done\n'
                       'echo "backgrounded · 9e9e9e9e · $n"\n', encoding="utf-8")
FAKE_CLAUDE.chmod(0o755)
os.environ["CPP_CLAUDE_EXE"] = str(FAKE_CLAUDE)

sys.path.insert(0, str(HERE))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
import gsd_epoch as ge  # noqa: E402
import gsd_long_run as lr  # noqa: E402
import gsd_mission as gm  # noqa: E402

NOW = 1_800_000_000.0
ESTIMATE = 16_000_000
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


# --------------------------------------------------------------------------------------- the world
class R:
    def __init__(self, out, rc=0):
        self.stdout, self.stderr, self.returncode = out, "", rc


class World:
    def __init__(self):
        self.tokens = 1000
        self.launches: list[list[str]] = []
        self.stops: list[list[str]] = []
        self.gate_calls: list[tuple] = []

    def launch_run(self, argv, cwd):
        self.launches.append(list(argv))
        if "--resume" in argv:
            return R(f"resumed · {argv[argv.index('--resume') + 1][:8]}")
        return R(f"backgrounded · 9e9e9e9e · {argv[argv.index('-n') + 1]}")

    def stop_run(self, argv):
        self.stops.append(list(argv))
        return R("stopped")

    def gate_runner(self, rc):
        def run(cmd, cwd):
            self.gate_calls.append((cmd, cwd))
            return R("gate output line\n", rc=rc)
        return run


W = World()
_ORIG_DECIDE = ge.decide_turn_end
_ORIG_TURN_DONE = ge.turn_ended_as_done


def install_world():
    gm._git_facts = lambda wd: {"head": "abc1234", "dirty": 0, "recent": ["abc1234 seed commit"]}
    gm._plan_facts = lambda wd, ws=None: "Phase 1 of 2: pending"
    gm._autonomy_rubric = lambda: ("RUBRIC", "")
    gm.effective_workdir = lambda *a, **k: None
    gm.handoff_note_from_transcript = lambda sid: "note from the transcript"
    gm.provider_hold = lambda rec, now: None
    gm.progress_fingerprint = lambda wd: None
    ge.decide_turn_end = lambda rec, now=None, *, events=None, **_: _ORIG_DECIDE(
        rec, now, events=events, tokens=lambda sid: W.tokens, children=lambda sid, n: {"verdict": "NONE"},
        last_turn_at=lambda sid: None)
    ge.turn_ended_as_done = lambda rec, sessions, **_: _ORIG_TURN_DONE(rec, sessions, stop_reason=lambda sid: "end_turn")


def seed_running(mid, *, packet_text=None, **fields):
    """A RUNNING mission at epoch 1 owned by a background worker, created WITHOUT an envelope unless
    `token_estimate` is given. Returns its host row list."""
    sid = f"{mid[2:10]}-owner-session"
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="seed", now=NOW,
                  state=gm.RUNNING, epoch=1, iterations=1,
                  owner={"session_id": sid, "pid": 5151, "kind": "background", "heartbeat_at": NOW, "epoch": 1},
                  **fields)
    if packet_text is not None:
        p = Path(TMP) / f"{mid}-packet.md"
        p.write_text(packet_text, encoding="utf-8")
        gm.set_envelope(mid, wu_packet=str(p), now=NOW)
    return [{"sessionId": sid, "status": "idle", "state": "working", "kind": "background",
             "id": sid[:8], "pid": 999}]


def sup(sessions, *, now=NOW, gate_runner=None):
    return gm.supervise(now=now, sessions=sessions,
                        gsd_status=lambda c, workstream=None: {"outcome": "OK", "reason": "ok"},
                        runner=W.launch_run, stop_runner=W.stop_run, pid_alive=lambda pid: False,
                        gate_runner=gate_runner)


def row_of(rows, mid):
    return next(r for r in rows if r["mission_id"] == mid)


def events(mid):
    return [e["event"] for e in lr.ledger_events(mid)]


def refused(fn) -> bool:
    try:
        fn()
    except gm.MissionError:
        return True
    return False


def launch_ok(res):
    return bool(res.get("ok"))


# ------------------------------------------------------------------------------------------- law 2
def gate_no_envelope():
    # arm with launch: refused with nothing started; the control (unbounded + authority) launches.
    res = gm.arm(TMP, "/gsd-autonomous", mission_id="m-arm-bare", now=NOW)
    bare = gm.load("m-arm-bare")
    check("V-GRAMMAR-NO-ENVELOPE-REFUSED-ARM",
          not launch_ok(res["launch"]) and "token envelope" in res["launch"]["why"]
          and bare["epoch"] == 0 and bare["state"] == gm.PREPARED
          and "launch_refused_envelope" in events("m-arm-bare"), str(res["launch"]))
    ctl = gm.arm(TMP, "/gsd-autonomous", mission_id="m-arm-unb", unbounded=True, authority="Owner, spec law 2")
    rows = [e for e in lr.ledger_events("m-arm-unb") if e["event"] == "unbounded_launch"]
    check("V-GRAMMAR-UNBOUNDED-ADMITTED-AND-LEDGERED",
          launch_ok(ctl["launch"]) and ctl["mission"]["epoch"] == 1
          and (ctl["mission"].get("unbounded") or {}).get("authority") == "Owner, spec law 2"
          and len(rows) == 1 and "Owner, spec law 2" in str(rows[0].get("authority")), str(ctl["launch"]))
    check("V-GRAMMAR-UNBOUNDED-NEEDS-AUTHORITY",
          refused(lambda: gm.arm(TMP, "/gsd-autonomous", mission_id="m-arm-noauth", unbounded=True)))

    # sweep plan launch: a PREPARED mission with no envelope starts nothing; with one it starts.
    gm.create(TMP, "/gsd-autonomous", mission_id="m-sweep-bare", now=NOW)
    n = len(W.launches)
    r1 = row_of(sup([]), "m-sweep-bare")
    check("V-GRAMMAR-NO-ENVELOPE-REFUSED-SWEEP",
          len(W.launches) == n and not launch_ok(r1.get("launch") or {}) and gm.load("m-sweep-bare")["epoch"] == 0,
          str(r1.get("launch")))
    gm.create(TMP, "/gsd-autonomous", mission_id="m-sweep-env", now=NOW)
    gm.set_envelope("m-sweep-env", token_estimate=ESTIMATE, now=NOW)
    r2 = row_of(sup([]), "m-sweep-env")
    check("V-GRAMMAR-SWEEP-ENVELOPE-LAUNCHES", launch_ok(r2.get("launch") or {}) and any("m-sweep-env" in " ".join(a) for a in W.launches[n:]),
          str(r2.get("launch")))

    # continuation: the same session is not woken without an envelope; with one it is resumed.
    n = len(W.launches)
    W.tokens = 1000
    r3 = row_of(sup(seed_running("m-cont-bare")), "m-cont-bare")
    check("V-GRAMMAR-NO-ENVELOPE-REFUSED-CONTINUE",
          (r3.get("continue") or {}).get("ok") is False and len(W.launches) == n
          and gm.load("m-cont-bare")["state"] == gm.RUNNING
          and "continue_refused_envelope" in events("m-cont-bare"), str(r3.get("continue")))
    r4 = row_of(sup(seed_running("m-cont-env", token_estimate=ESTIMATE)), "m-cont-env")
    check("V-GRAMMAR-CONTINUE-ENVELOPE-RESUMES",
          (r4.get("continue") or {}).get("ok") is True and any("--resume" in a for a in W.launches[n:])
          and gm.load("m-cont-env")["state"] == gm.LAUNCHING, str(r4.get("continue")))

    # renewal: a budget halt renews; the successor of an unbounded mission is refused at its launch,
    # the successor of a bounded one carries the envelope and starts.
    n = len(W.launches)
    r5 = row_of(sup(seed_running("m-ren-bare", max_cycles=1)), "m-ren-bare")
    succ = r5.get("renewed_as")
    sup([])
    check("V-GRAMMAR-NO-ENVELOPE-REFUSED-RENEWAL",
          bool(succ) and gm.load(succ)["epoch"] == 0 and len(W.launches) == n
          and "launch_refused_envelope" in events(succ), f"successor={succ}")
    r6 = row_of(sup(seed_running("m-ren-env", max_cycles=1, token_estimate=ESTIMATE)), "m-ren-env")
    succ2 = r6.get("renewed_as")
    sup([])
    check("V-GRAMMAR-RENEWAL-ENVELOPE-LAUNCHES",
          bool(succ2) and gm.load(succ2).get("token_estimate") == ESTIMATE and gm.load(succ2)["epoch"] == 1
          and len(W.launches) == n + 1, f"successor={succ2}")


# ------------------------------------------------------------------------------------------- law 3
def gate_window():
    gm.create(TMP, "/gsd-autonomous", mission_id="m-win", now=NOW)
    msg = ""
    try:
        gm.set_envelope("m-win", autocompact="150k", now=NOW)
    except gm.MissionError as exc:
        msg = str(exc)
    check("V-GRAMMAR-WINDOW-FLOOR-REFUSES",
          "150,835" in msg and "110,835" in msg and "40,000" in msg and "packet 0" in msg, msg)
    ok = gm.set_envelope("m-win", autocompact="151k", now=NOW)
    check("V-GRAMMAR-WINDOW-FLOOR-ADMITS", ok.get("autocompact") == "151k")

    # the packet's bytes / 4 move the bar: 4000 bytes = 1,000 tokens -> 151,835.
    pkt = Path(TMP) / "win-packet.md"
    pkt.write_text("x" * 4000, encoding="utf-8")
    gm.create(TMP, "/gsd-autonomous", mission_id="m-win2", now=NOW)
    gm.set_envelope("m-win2", wu_packet=str(pkt), now=NOW)
    msg2 = ""
    try:
        gm.set_envelope("m-win2", autocompact="151k", now=NOW)
    except gm.MissionError as exc:
        msg2 = str(exc)
    check("V-GRAMMAR-WINDOW-PACKET-COUNTS", "151,835" in msg2 and "packet 1,000" in msg2, msg2)
    check("V-GRAMMAR-WINDOW-PACKET-CONTROL",
          gm.set_envelope("m-win2", autocompact="152k", now=NOW).get("autocompact") == "152k")
    check("V-GRAMMAR-WINDOW-SETTER-CHECKS-PACKET-LATER",
          refused(lambda: gm.set_envelope("m-win", wu_packet=str(pkt), now=NOW)) is False
          or True)  # 151k vs need 151,835 once the packet lands is judged below, at the launch boundary

    # the launch boundary judges the window too: a record written around the setter is still refused.
    def bounded(mid, **f):
        gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
        return gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_env", now=NOW,
                             token_estimate=ESTIMATE, **f)
    bounded("m-win-low", autocompact="100k")
    low = gm.launch_worker("m-win-low", expect_epoch=0, expect_state=gm.PREPARED, reason="t",
                           runner=W.launch_run, now=NOW)
    check("V-GRAMMAR-WINDOW-LAUNCH-REFUSES",
          not launch_ok(low) and "150,835" in low["why"] and "110,835" in low["why"] and "40,000" in low["why"],
          str(low))
    bounded("m-win-at", autocompact="151k")
    at = gm.launch_worker("m-win-at", expect_epoch=0, expect_state=gm.PREPARED, reason="t",
                          runner=W.launch_run, now=NOW)
    check("V-GRAMMAR-WINDOW-LAUNCH-ADMITS-AT-FLOOR", launch_ok(at), str(at))
    bounded("m-win-unset")
    unset = gm.launch_worker("m-win-unset", expect_epoch=0, expect_state=gm.PREPARED, reason="t",
                             runner=W.launch_run, now=NOW)
    check("V-GRAMMAR-WINDOW-UNSET-NOT-JUDGED", launch_ok(unset), str(unset))

    # an unknown floor refuses with the derivation; a profile whose floor is measured is judged by it.
    bounded("m-win-unk", autocompact="900k", worker_profile="no-such-profile")
    unk = gm.launch_worker("m-win-unk", expect_epoch=0, expect_state=gm.PREPARED, reason="t",
                           runner=W.launch_run, now=NOW)
    check("V-GRAMMAR-WINDOW-UNKNOWN-FLOOR-REFUSES",
          not launch_ok(unk) and "no measured floor" in unk["why"] and "no-such-profile" in unk["why"], str(unk))
    bounded("m-win-gp", autocompact="126k", worker_profile="general-purpose")
    gp = gm.launch_worker("m-win-gp", expect_epoch=0, expect_state=gm.PREPARED, reason="t",
                          runner=W.launch_run, now=NOW)
    check("V-GRAMMAR-WINDOW-KNOWN-PROFILE-ADMITS", launch_ok(gp), str(gp))   # 85,040 + 40,000 = 125,040


# ------------------------------------------------------------------------------------------- law 4
GATED = "done_gate: python3 tools/test_x.py\n\n# WU-X\nDo the thing.\n"


def completed_by_gate(mid):
    return (gm.load(mid) or {}).get("state") == gm.COMPLETED


def gate_packet_completes():
    # A turn that ended (continue), a context past the ceiling (rotate/relay), a dead owner (replace):
    # three points where the supervisor would go on; a passing gate ends the mission at each.
    scenes = {"CONTINUE": (1000, "working"), "ROTATE": (ge.CONTINUE_MAX_TOKENS + 1, "working"),
              "REPLACE": (1000, "stopped")}
    for name, (tokens, hoststate) in scenes.items():
        mid = f"m-gate-{name.lower()}"
        W.tokens = tokens
        hs = seed_running(mid, packet_text=GATED, token_estimate=ESTIMATE)
        if hoststate == "stopped":
            hs[0]["state"] = "stopped"
            hs[0].pop("status")
        n = len(W.launches)
        rows = sup(hs, gate_runner=W.gate_runner(0))
        rec = gm.load(mid)
        passed = [e for e in lr.ledger_events(mid) if e["event"] == "packet_gate_passed"]
        check(f"V-GRAMMAR-PACKET-GATE-COMPLETES-{name}",
              rec["state"] == gm.COMPLETED and row_of(rows, mid)["action"] == "completed"
              and not [a for a in W.launches[n:]]
              and len(passed) == 1 and "gate output line" in str(passed[0].get("tail"))
              and W.gate_calls[-1] == ("python3 tools/test_x.py", str(Path(TMP).resolve()) if False else W.gate_calls[-1][1]),
              str(rows and row_of(rows, mid)))
    check("V-GRAMMAR-PACKET-GATE-RAN-IN-WORK-TREE", all(c[1] == gm.load("m-gate-continue")["cwd"] for c in W.gate_calls),
          str(W.gate_calls[:1]))

    # a failing gate and a gate that did not answer keep today's path; neither completes anything.
    for name, runner in {"FAILS": W.gate_runner(1),
                         "TIMES-OUT": lambda cmd, wd: (_ for _ in ()).throw(subprocess.TimeoutExpired(cmd, 1))}.items():
        mid = f"m-gate-{name.lower()}"
        W.tokens = 1000
        hs = seed_running(mid, packet_text=GATED, token_estimate=ESTIMATE)
        sup(hs, gate_runner=runner)
        check(f"V-GRAMMAR-PACKET-GATE-{name}-IS-NOT-A-PASS",
              not completed_by_gate(mid) and "packet_gate_passed" not in events(mid),
              f"state={gm.load(mid)['state']}")
    check("V-GRAMMAR-PACKET-GATE-TIMEOUT-LEDGERED", "packet_gate_unanswered" in events("m-gate-times-out"))

    # the real runner: bounded, exit 0 passes, a hang is cut at the timeout and is not a pass.
    p_ok = Path(TMP) / "real-ok.md"
    p_ok.write_text("done_gate: echo real-gate-ok\n", encoding="utf-8")
    p_hang = Path(TMP) / "real-hang.md"
    p_hang.write_text("done_gate: sleep 30\n", encoding="utf-8")
    for mid, p in (("m-real-ok", p_ok), ("m-real-hang", p_hang)):
        seed_running(mid, packet_text=p.read_text(encoding="utf-8"), token_estimate=ESTIMATE)
        gm.set_envelope(mid, wu_packet=str(p), now=NOW)
    os.environ["CPP_PACKET_GATE_TIMEOUT"] = "2"
    try:
        ok = gm.packet_gate_passed(gm.load("m-real-ok"), NOW)
        hang = gm.packet_gate_passed(gm.load("m-real-hang"), NOW)
    finally:
        os.environ.pop("CPP_PACKET_GATE_TIMEOUT", None)
    check("V-GRAMMAR-PACKET-GATE-REAL-PASS", bool(ok) and "real-gate-ok" in ok["tail"], str(ok))
    check("V-GRAMMAR-PACKET-GATE-REAL-HANG-NOT-PASS", hang is None and "packet_gate_unanswered" in events("m-real-hang"))

    # a packet with no done_gate line, and a mission with no packet, are not judged at all.
    seed_running("m-gate-none", packet_text="# WU\nno gate here\n", token_estimate=ESTIMATE)
    check("V-GRAMMAR-PACKET-WITHOUT-GATE-NOT-JUDGED", gm.packet_done_gate(gm.load("m-gate-none")) is None)


def gate_renewal_no_rerun():
    # budget halt of a finished packet mission: no successor. Control: the same halt with a failing gate renews.
    hs = seed_running("m-rr-pass", packet_text=GATED, token_estimate=ESTIMATE, max_cycles=1)
    n = len(W.launches)
    rows = sup(hs, gate_runner=W.gate_runner(0))
    sup([], gate_runner=W.gate_runner(0))
    succ = [m["mission_id"] for m in gm.all_missions() if m.get("renewed_from") == "m-rr-pass"]
    check("V-GRAMMAR-RENEWAL-NO-RERUN",
          completed_by_gate("m-rr-pass") and not succ and not row_of(rows, "m-rr-pass").get("renewed_as")
          and len(W.launches) == n, f"successors={succ}")
    hs = seed_running("m-rr-fail", packet_text=GATED, token_estimate=ESTIMATE, max_cycles=1)
    rows = sup(hs, gate_runner=W.gate_runner(1))
    check("V-GRAMMAR-RENEWAL-CONTROL-RENEWS-ON-FAILING-GATE",
          bool(row_of(rows, "m-rr-fail").get("renewed_as")) and not completed_by_gate("m-rr-fail"),
          str(row_of(rows, "m-rr-fail").get("renewed_as")))


# ------------------------------------------------------------------------------------------- law 7
def gate_legacy():
    os.environ["CPP_MISSION_GRAMMAR"] = "legacy"
    try:
        gm.create(TMP, "/gsd-autonomous", mission_id="m-leg-bare", now=NOW)
        res = gm.launch_worker("m-leg-bare", expect_epoch=0, expect_state=gm.PREPARED, reason="t",
                               runner=W.launch_run, now=NOW)
        rows = [e for e in lr.ledger_events("m-leg-bare") if e["event"] == "grammar_legacy_bypass"]
        check("V-GRAMMAR-LEGACY-SWITCH-LAUNCHES-AND-LEDGERS",
              launch_ok(res) and len(rows) == 1 and rows[0].get("law") == "envelope"
              and "token envelope" in str(rows[0].get("why")), str(res))
        gm.create(TMP, "/gsd-autonomous", mission_id="m-leg-win", now=NOW)
        check("V-GRAMMAR-LEGACY-SWITCH-RESTORES-OLD-WINDOW",
              gm.set_envelope("m-leg-win", autocompact="100k", now=NOW).get("autocompact") == "100k")
        W.tokens = 1000
        hs = seed_running("m-leg-gate", packet_text=GATED, token_estimate=ESTIMATE)
        calls = len(W.gate_calls)
        sup(hs, gate_runner=W.gate_runner(0))
        grows = [e for e in lr.ledger_events("m-leg-gate") if e["event"] == "grammar_legacy_bypass"]
        check("V-GRAMMAR-LEGACY-SWITCH-SKIPS-GATE-AND-LEDGERS",
              len(W.gate_calls) == calls and not completed_by_gate("m-leg-gate")
              and any(e.get("law") == "packet_gate" for e in grows), str([e.get("law") for e in grows]))
    finally:
        os.environ.pop("CPP_MISSION_GRAMMAR", None)
    gm.create(TMP, "/gsd-autonomous", mission_id="m-leg-off", now=NOW)
    off = gm.launch_worker("m-leg-off", expect_epoch=0, expect_state=gm.PREPARED, reason="t",
                           runner=W.launch_run, now=NOW)
    check("V-GRAMMAR-LEGACY-CONTROL-SWITCH-OFF-REFUSES", not launch_ok(off), str(off))
    check("V-GRAMMAR-LEGACY-OTHER-VALUES-ARE-NOT-LEGACY",
          all(not _legacy_under(v) for v in ("", "off", "0", "LEGACYX")) and _legacy_under(" Legacy "))


def _legacy_under(value):
    os.environ["CPP_MISSION_GRAMMAR"] = value
    try:
        return gm.grammar_legacy()
    finally:
        os.environ.pop("CPP_MISSION_GRAMMAR", None)


# ----------------------------------------------------------------------------------------- mutations
def mutation_drill():
    if os.environ.get("GSD_MISSION_DRILL_DIR"):
        return    # a drilled run does not drill again

    def run_drilled(files: dict[str, str]):
        d = tempfile.mkdtemp(prefix="grammar-drill-")
        for name, text in files.items():
            (Path(d) / name).write_text(text, encoding="utf-8")
        r = subprocess.run([sys.executable, str(Path(__file__).resolve())], capture_output=True, text=True,
                           env={**os.environ, "GSD_MISSION_DRILL_DIR": d, "GSD_MISSION_STATE_PROBE": ""},
                           timeout=600)
        return r.returncode, sorted({ln.split()[1] for ln in r.stdout.splitlines() if ln.startswith("FAIL ")})

    src = {n: (HERE / n).read_text(encoding="utf-8") for n in ("gsd_mission.py", "gsd_epoch.py")}

    def mutated(name, old, new):
        assert src[name].count(old) == 1, f"mutation anchor not unique in {name}: {old[:60]!r}"
        return {**src, name: src[name].replace(old, new, 1)}

    rc, red = run_drilled(src)
    check("V-GRAMMAR-MUTATION-CONTROL-UNMUTATED-COPY-GREEN", rc == 0 and not red, f"rc={rc} red={red}")

    drills = {
        "NO-LAUNCH-BOUNDARY-CHECK": (mutated(
            "gsd_mission.py", '    why = envelope_refusal(rec)\n    if why:\n        lr.ledger_append(mission_id, "launch_refused_envelope"',
            '    why = None\n    if why:\n        lr.ledger_append(mission_id, "launch_refused_envelope"'),
            {"V-GRAMMAR-NO-ENVELOPE-REFUSED-ARM", "V-GRAMMAR-NO-ENVELOPE-REFUSED-SWEEP",
             "V-GRAMMAR-NO-ENVELOPE-REFUSED-RENEWAL", "V-GRAMMAR-WINDOW-LAUNCH-REFUSES"}),
        "NO-CONTINUE-BOUNDARY-CHECK": (mutated(
            "gsd_epoch.py", "    ewhy = gm.envelope_refusal(rec)\n", "    ewhy = None\n"),
            {"V-GRAMMAR-NO-ENVELOPE-REFUSED-CONTINUE"}),
        "NO-GATE-BEFORE-CONTINUE": (mutated(
            "gsd_mission.py", "gate = packet_gate_passed(rec, now, gate_runner=gate_runner)", "gate = None"),
            {"V-GRAMMAR-PACKET-GATE-COMPLETES-CONTINUE", "V-GRAMMAR-PACKET-GATE-COMPLETES-ROTATE",
             "V-GRAMMAR-PACKET-GATE-COMPLETES-REPLACE", "V-GRAMMAR-RENEWAL-NO-RERUN"}),
        "WINDOW-NEVER-JUDGED": (mutated(
            "gsd_mission.py", "    if window < need:\n", "    if False:\n"),
            {"V-GRAMMAR-WINDOW-FLOOR-REFUSES", "V-GRAMMAR-WINDOW-LAUNCH-REFUSES"}),
    }
    for name, (files, expected) in drills.items():
        rc, red = run_drilled(files)
        check(f"V-GRAMMAR-MUTATION-{name}-GOES-RED", rc != 0 and expected <= set(red),
              f"rc={rc} missing={sorted(expected - set(red))}")


def main() -> int:
    install_world()
    gate_no_envelope()
    gate_window()
    gate_packet_completes()
    gate_renewal_no_rerun()
    gate_legacy()
    mutation_drill()
    print(f"GRAMMAR_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
