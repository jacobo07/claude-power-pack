#!/usr/bin/env python
"""V-MV2-* gates: capsule-v2 wired into tools/gsd_mission.py (spec vault/specs/mission-capsule-rollover.md, T6).

Drives the REAL supervise() pass with the host, the launcher, the stopper and GSD injected, and the
real adapter + rollover underneath (temp state dirs, a real git repo). Every v2 behaviour has a
control: the same scenario on a legacy record must show none of it, and every refusal has an
admitted twin, so a build that refuses (or rotates) everything cannot pass.

Hermetic (spec I6): every state dir is redirected BEFORE import; rollover.STATE_DIR (frozen at
import) points at a trap that must stay empty.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TMP = Path(tempfile.mkdtemp(prefix="mv2_t_"))
STATE = TMP / "rollover"
TRAP = TMP / "trap-import-time-state"
os.environ["CPP_ROLLOVER_STATE_DIR"] = str(STATE)
os.environ["GSD_LONG_RUN_STATE_DIR"] = str(TMP / "missions")
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(TMP / "missions" / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = str(TMP / "missions")
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(TMP / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(TMP / "projects")
os.environ.pop("CPP_CAPSULE_ROLLOVER", None)
(TMP / "missions" / "sessions").mkdir(parents=True)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import rollover as ro  # noqa: E402
import mission_capsule as mc  # noqa: E402
import gsd_mission as gm  # noqa: E402

ro.STATE_DIR = TRAP
gm.progress_fingerprint = lambda work_dir: None   # unmeasured: the neutral answer (as test_gsd_mission)

passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def git(root, *args):
    subprocess.run([ro._git_exe(), "-C", str(root), *args], check=True, capture_output=True,
                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def make_repo() -> Path:
    repo = TMP / "repo"
    (repo / ".planning").mkdir(parents=True)
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "t@example.invalid")
    git(repo, "config", "user.name", "t")
    (repo / ".planning" / "STATE.md").write_text("# State\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init")
    return repo


REPO = make_repo()
NOW = 1_800_000_000.0
MANAGER = {"state_path": str(REPO / ".planning" / "STATE.md"),
           "recommended_actions": [{"phase": "2", "phase_name": "Wire it", "action": "execute"}],
           "phases": [{"number": "2", "name": "Wire it", "phase_complete": False}]}
CLEAR = {"verdict": "CLEAR", "pending": [], "unconsumed": []}
HOLD = {"verdict": "HOLD", "pending": ["a background child"], "unconsumed": []}
TRANSCRIPT = TMP / "outgoing.jsonl"
TRANSCRIPT.write_text(json.dumps({"type": "assistant", "message": {"content": []}}) + "\n", encoding="utf-8")
gone = lambda pid: False   # noqa: E731
GSD_OK = lambda c, workstream=None: {"outcome": "OK", "reason": "work remains"}  # noqa: E731


def io(children=CLEAR, transcript=True):
    return {"manager": MANAGER, "children": children,
            "find_transcript": (lambda sid: TRANSCRIPT) if transcript else (lambda sid: None)}


class R:
    def __init__(self, out):
        self.stdout, self.stderr, self.returncode = out, "", 0


stops, launches, armed_at_spawn = [], [], []


def stop_run(argv):
    stops.append(argv)
    return R("stopped")


def launch_run(argv, cwd):
    name = argv[argv.index("-n") + 1]
    mid = name.rsplit("-e", 1)[0]
    armed_at_spawn.append(ro.precert_read(mid, STATE))   # spec 3.3: the marker exists BEFORE spawn
    launches.append(argv)
    return R(f"backgrounded · 9e9e9e9e · {name}")


def mission(mid, *, v2=True, epoch=1, state=None, note=None, **extra):
    """A RUNNING mission whose worker <epoch> is owner `s-<mid>`, optionally in HANDOFF with a note."""
    for p in (TMP / "missions").glob(f"gsd-mission-{mid}.json"):
        p.unlink()
    gm.create(str(REPO), "/gsd-autonomous", mission_id=mid, now=NOW, permission_mode="auto",
              rollover_protocol=gm.CAPSULE_V2 if v2 else None)
    owner = {"session_id": f"s-{mid}", "pid": 999, "kind": "background"}
    rec = gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t", now=NOW,
                        state=gm.RUNNING, epoch=epoch, owner=owner, **extra)
    if note is not None:
        rec = gm.transition(mid, expect_epoch=epoch, expect_state=gm.RUNNING, event="t_handoff", now=NOW,
                            state=gm.HANDOFF, note=note,
                            pending={"kind": "handoff", "from": owner["session_id"], "deadline": NOW + 1800})
    if state:
        rec = gm.transition(mid, expect_epoch=epoch, expect_state=rec["state"], event="t_state", now=NOW,
                            state=state)
    return rec


def host(mid, **row):
    base = {"sessionId": f"s-{mid}", "status": "idle", "state": "working", "kind": "background",
            "id": f"s-{mid}"[:8], "pid": 999}
    base.update(row)
    return [{k: v for k, v in base.items() if v is not None}]


def run(sessions, now=NOW, children=CLEAR, transcript=True):
    rows = gm.supervise(now=now, sessions=sessions, gsd_status=GSD_OK, runner=launch_run,
                        stop_runner=stop_run, pid_alive=gone, capsule_io=io(children, transcript))
    return rows


def row_of(rows, mid):
    return next((r for r in rows if r.get("mission_id") == mid), {})


def events(mid):
    return [e.get("event") for e in gm.lr.ledger_events(mid)]


def wipe():
    for p in (TMP / "missions").glob("gsd-mission-*.json"):
        p.unlink()


def main() -> int:
    # --- arm: G11 + field absent on legacy ------------------------------------------------------
    try:
        gm.create(str(REPO), "/gsd-autonomous", mission_id="m-mode", now=NOW,
                  permission_mode="acceptEdits", rollover_protocol=gm.CAPSULE_V2)
        check("V-MV2-ARM-REFUSES-SHELLLESS-MODE", False, "acceptEdits was accepted for capsule-v2")
    except gm.MissionError as exc:
        check("V-MV2-ARM-REFUSES-SHELLLESS-MODE", "permission mode" in str(exc), str(exc))
    try:
        gm.create(str(REPO), "/gsd-autonomous", mission_id="m-proto", now=NOW, rollover_protocol="capsule-v3")
        check("V-MV2-ARM-REFUSES-UNKNOWN-PROTOCOL", False, "capsule-v3 accepted")
    except gm.MissionError as exc:
        check("V-MV2-ARM-REFUSES-UNKNOWN-PROTOCOL", "unknown rollover protocol" in str(exc), str(exc))
    v2rec = gm.create(str(REPO), "/gsd-autonomous", mission_id="m-armv2", now=NOW, permission_mode="auto",
                      rollover_protocol=gm.CAPSULE_V2)
    legrec = gm.create(str(REPO), "/gsd-autonomous", mission_id="m-armleg", now=NOW, permission_mode="auto")
    check("V-MV2-ARM-FIELD-ONLY-WHEN-ASKED",
          v2rec.get("rollover_protocol") == gm.CAPSULE_V2 and "rollover_protocol" not in legrec
          and "rollover_protocol" not in json.loads(gm.mission_path("m-armleg").read_text(encoding="utf-8")),
          f"v2={v2rec.get('rollover_protocol')} legacy keys has={('rollover_protocol' in legrec)}")
    rc = gm._cli(["arm", "--cwd", str(REPO), "--command", "/gsd-autonomous", "--no-launch",
                  "--rollover-protocol", gm.CAPSULE_V2])
    armed = [m for m in gm.all_missions() if m.get("rollover_protocol") == gm.CAPSULE_V2
             and m["mission_id"] not in ("m-armv2",)]
    check("V-MV2-CLI-ARM-FLAG", rc == 0 and len(armed) == 1, f"rc={rc} armed={[m['mission_id'] for m in armed]}")

    # --- argv: G9 MCP strip, legacy untouched --------------------------------------------------
    a2 = gm.worker_argv(v2rec, "/gsd-autonomous")
    al = gm.worker_argv(legrec, "/gsd-autonomous")
    check("V-MV2-ARGV-STRIPS-MCP", "--strict-mcp-config" in a2 and "--strict-mcp-config" not in al,
          f"v2 has={('--strict-mcp-config' in a2)} legacy has={('--strict-mcp-config' in al)}")
    wipe()

    # --- happy rotation: seal -> authorize -> stop -> arm -> spawn -> bind ---------------------
    mission("m-hap", note="phase 2 half done: wire the gate next")
    n_s, n_l = len(stops), len(launches)
    rows = run(host("m-hap"))
    r = row_of(rows, "m-hap")
    rec = gm.load("m-hap")
    key = "mission-m-hap-e1"
    ev = events("m-hap")
    mk = ro.precert_read("m-hap", STATE)
    check("V-MV2-ROTATE-SEALS-AND-AUTHORIZES",
          rec.get("capsule_key") == key and (rec.get("capsule_stop_authorized") or {}).get("origin") == "worker_handoff"
          and "outgoing_stop_authorized" in ev, f"capsule={r.get('capsule')} key={rec.get('capsule_key')}")
    check("V-MV2-AUTHORIZED-BEFORE-STOP-AND-CLAIM",
          "outgoing_stop_authorized" in ev and "launch_claimed" in ev
          and ev.index("outgoing_stop_authorized") < ev.index("launch_claimed") and len(stops) == n_s + 1,
          f"events={ev[-6:]} stops={len(stops) - n_s}")
    spawned_mk = armed_at_spawn[-1] if len(launches) == n_l + 1 else None
    check("V-MV2-MARKER-ARMED-BEFORE-SPAWN",
          spawned_mk is not None and spawned_mk.get("worker") == "m-hap-e2"
          and spawned_mk.get("capsule_key") == key and not spawned_mk.get("certified_at"), str(spawned_mk))
    check("V-MV2-MARKER-BOUND-TO-BG-ID", (mk or {}).get("bg_id") == "9e9e9e9e", str(mk))
    card = launches[-1][launches[-1].index("--append-system-prompt") + 1] if len(launches) == n_l + 1 else ""
    check("V-MV2-CARD-HAS-V2-BLOCK", "CAPSULE-V2 SUCCESSOR" in card and key in card
          and "mission_capsule.py resume --mission m-hap" in card, card[:200])
    check("V-MV2-SUCCESSOR-ARGV-STRIPS-MCP", "--strict-mcp-config" in (launches[-1] if launches else []))

    # ack: the successor's own hook binds its session and starts the certification clock
    succ = "9e9e9e9e-0000-4000-8000-000000000001"
    gm.ack_session(succ, now=NOW + 10)
    rec = gm.load("m-hap")
    mk = ro.precert_read("m-hap", STATE)
    check("V-MV2-ACK-BINDS-AND-CLOCKS", rec.get("capsule_acked_at") == NOW + 10
          and (mk or {}).get("owner_session") == succ, f"acked={rec.get('capsule_acked_at')} mk={mk}")

    # --- uncertified successor: never rotated while alive; BLOCKED past the deadline -----------
    busy = [{"sessionId": succ, "status": "idle", "state": "working", "kind": "background",
             "id": "9e9e9e9e", "pid": 999}]
    n_s, n_l = len(stops), len(launches)
    rows = run(busy, now=NOW + 60)
    r = row_of(rows, "m-hap")
    check("V-MV2-UNCERTIFIED-NOT-ROTATED", "has not certified" in (r.get("held") or "")
          and len(stops) == n_s and len(launches) == n_l, f"{r.get('action')} held={r.get('held')}")
    rows = run(busy, now=NOW + 10 + gm.CAPSULE_CERTIFY_DEADLINE_S + 1)
    rec = gm.load("m-hap")
    check("V-MV2-CERTIFY-DEADLINE-BLOCKS",
          rec["state"] == gm.BLOCKED and (rec.get("capsule_hold") or {}).get("kind") == "resume_not_certified",
          f"{rec['state']} hold={rec.get('capsule_hold')}")
    p = gm.plan_next(rec, NOW + 4000, busy, gone, v2=True)
    check("V-MV2-HOLD-STICKS-OVER-LIVE-OWNER", p["action"] == "none" and "capsule hold" in p["reason"], str(p))
    p_leg = gm.plan_next({**rec, "rollover_protocol": None}, NOW + 4000,
                         [{**busy[0], "status": "busy"}], gone)
    check("V-MV2-HOLD-CONTROL-LEGACY-UNBLOCKS", p_leg["action"] == "unblock", str(p_leg))
    ro.precert_write("m-hap", {"certified_at": NOW + 4100}, STATE)   # the flip rollover.certify_flow makes
    rows = run(busy, now=NOW + 4200)
    rec = gm.load("m-hap")
    check("V-MV2-CERTIFICATION-LIFTS-HOLD", rec["state"] == gm.RUNNING and not rec.get("capsule_hold")
          and row_of(rows, "m-hap").get("action") == "capsule_certified", f"{rec['state']} {rec.get('capsule_hold')}")

    # --- a dead uncertified successor: its replacement inherits the SAME capsule (G6) -----------
    wipe()
    mission("m-inh", epoch=2, capsule_key="mission-m-inh-e1")
    ro.precert_arm("m-inh", {"worker": "m-inh-e2", "epoch": 2, "capsule_key": "mission-m-inh-e1",
                             "cwd": str(REPO), "resume_cmd": "/gsd-autonomous"}, STATE)
    n_l = len(launches)
    rows = run(host("m-inh", state="stopped", status=None))
    mk = ro.precert_read("m-inh", STATE)
    check("V-MV2-DEAD-UNCERTIFIED-INHERITS",
          len(launches) == n_l + 1 and (mk or {}).get("worker") == "m-inh-e3"
          and mk.get("capsule_key") == "mission-m-inh-e1" and "inherited" in (row_of(rows, "m-inh").get("capsule") or ""),
          f"mk={mk} capsule={row_of(rows, 'm-inh').get('capsule')}")

    # --- refusal: nothing stopped; clock; fallback past grace; BLOCKED when that refuses too ---
    wipe()
    mission("m-ref", note="n")
    n_s, n_l = len(stops), len(launches)
    rows = run(host("m-ref"), children=HOLD)
    rec = gm.load("m-ref")
    check("V-MV2-REFUSED-NOTHING-STOPPED",
          len(stops) == n_s and len(launches) == n_l and rec.get("capsule_first_refused_at") == NOW
          and "fallback clock started" in (row_of(rows, "m-ref").get("held") or ""),
          f"stops={len(stops) - n_s} held={row_of(rows, 'm-ref').get('held')}")
    rows = run(host("m-ref"), now=NOW + 600, children=HOLD)
    check("V-MV2-REFUSED-WITHIN-GRACE-HELD", len(stops) == n_s and gm.load("m-ref")["state"] == gm.HANDOFF,
          row_of(rows, "m-ref").get("held") or "")
    rows = run(host("m-ref"), now=NOW + 1800 + 1, children=HOLD)
    rec = gm.load("m-ref")
    check("V-MV2-FALLBACK-IMPOSSIBLE-BLOCKS-NOT-STOPPED",
          rec["state"] == gm.BLOCKED and (rec.get("capsule_hold") or {}).get("kind") == "seal_refused"
          and len(stops) == n_s and len(launches) == n_l, f"{rec['state']} hold={rec.get('capsule_hold')}")

    # control twin: no note -> handoff refused, clock; past grace the degraded fallback seals and stops
    wipe()
    mission("m-fb")
    n_s, n_l = len(stops), len(launches)
    run(host("m-fb"))
    check("V-MV2-NO-NOTE-HANDOFF-REFUSED", len(stops) == n_s and gm.load("m-fb").get("capsule_first_refused_at"))
    run(host("m-fb"), now=NOW + 1800 + 1)
    rec = gm.load("m-fb")
    cap = json.loads(ro.capsule_path("mission-m-fb-e1", STATE).read_text(encoding="utf-8")) \
        if ro.capsule_path("mission-m-fb-e1", STATE).is_file() else {}
    check("V-MV2-FALLBACK-PAST-GRACE-SEALS-DEGRADED",
          (rec.get("capsule_stop_authorized") or {}).get("origin") == "supervisor_fallback" and cap.get("degraded")
          and len(stops) == n_s + 1 and len(launches) == n_l + 1, f"auth={rec.get('capsule_stop_authorized')}")

    # --- dead owner: recovery capsule (G21) --------------------------------------------------------
    wipe()
    mission("m-rec")
    n_l = len(launches)
    run(host("m-rec", state="stopped", status=None), transcript=False)
    rec = gm.load("m-rec")
    check("V-MV2-DEAD-OWNER-RECOVERY", (rec.get("capsule_stop_authorized") or {}).get("origin") == "recovery"
          and len(launches) == n_l + 1, str(rec.get("capsule_stop_authorized")))

    # --- arming failure: no marker, no spawn ------------------------------------------------------
    wipe()
    mission("m-arm", note="n")
    real_arm = mc.arm_successor
    mc.arm_successor = lambda *a, **k: (_ for _ in ()).throw(OSError("disk full"))
    try:
        n_l = len(launches)
        rows = run(host("m-arm"))
    finally:
        mc.arm_successor = real_arm
    check("V-MV2-ARM-FAILURE-NO-SPAWN", len(launches) == n_l and "not armed" in (row_of(rows, "m-arm").get("held") or "")
          and "capsule_arm_failed" in events("m-arm"), row_of(rows, "m-arm").get("held") or "")

    # --- kill switches: a v2 mission rotates the legacy way ---------------------------------------
    for gate, setup, teardown in (
            ("V-MV2-KILL-SWITCH-FILE", lambda: (STATE / "capsule-v2.off").write_text("", encoding="utf-8"),
             lambda: (STATE / "capsule-v2.off").unlink()),
            ("V-MV2-KILL-SWITCH-ENV", lambda: os.environ.__setitem__("CPP_CAPSULE_ROLLOVER", "off"),
             lambda: os.environ.pop("CPP_CAPSULE_ROLLOVER", None))):
        wipe()
        mission("m-ks", note="n")
        STATE.mkdir(parents=True, exist_ok=True)
        setup()
        try:
            n_l = len(launches)
            run(host("m-ks"))
        finally:
            teardown()
        rec = gm.load("m-ks")
        check(gate, len(launches) == n_l + 1 and not rec.get("capsule_key")
              and "outgoing_stop_authorized" not in events("m-ks"), f"key={rec.get('capsule_key')}")

    # --- legacy control: the same happy scenario, none of the v2 effects ---------------------------
    wipe()
    mission("m-leg", v2=False, note="n")
    n_l = len(launches)
    run(host("m-leg"))
    rec = gm.load("m-leg")
    card = launches[-1][launches[-1].index("--append-system-prompt") + 1] if len(launches) == n_l + 1 else ""
    check("V-MV2-LEGACY-CONTROL-UNTOUCHED",
          len(launches) == n_l + 1 and not rec.get("capsule_key") and ro.precert_read("m-leg", STATE) is None
          and "CAPSULE-V2" not in card and "outgoing_stop_authorized" not in events("m-leg"),
          f"key={rec.get('capsule_key')} marker={ro.precert_read('m-leg', STATE)}")

    # --- renewal carries the protocol (G20) --------------------------------------------------------
    wipe()
    rec = mission("m-ren", note="n")
    new = gm.renew_mission({**rec, "state": gm.HALTED}, now=NOW)
    check("V-MV2-RENEW-CARRIES-PROTOCOL", new.get("rollover_protocol") == gm.CAPSULE_V2, str(new.get("rollover_protocol")))

    # --- card: the v2 block survives the byte cap (G22) --------------------------------------------
    big = gm.render_card({**rec, "epoch": 2, "capsule_key": "mission-m-ren-e1", "note": "N" * 9000},
                         {"head": "abc", "dirty": 0, "recent": ["x"] * 5}, "G" * 3000)
    check("V-MV2-CARD-BLOCK-SURVIVES-CAP", "CAPSULE-V2 SUCCESSOR" in big and "[card truncated at cap]" in big
          and big.index("CAPSULE-V2") < big.index("GSD:"), f"{len(big.encode())} bytes")
    nokey = gm.render_card({**rec, "epoch": 1, "note": ""}, None)
    check("V-MV2-CARD-CONTROL-NO-KEY-NO-BLOCK", "CAPSULE-V2" not in nokey)

    # --- review M1: an undecidable v2 record is isolated, fail-closed, and blinds nobody else ----
    wipe()
    mission("m-err", note="n")
    mission("m-oth", v2=False, note="n")
    real_sd = mc.state_dir
    mc.state_dir = lambda explicit=None: (_ for _ in ()).throw(PermissionError("state dir held"))
    n_s, n_l = len(stops), len(launches)
    try:
        rows = run(host("m-err") + host("m-oth"))
    except Exception as exc:  # noqa: BLE001 -- the pre-fix shape: the pass itself dies
        rows = [{"mission_id": "m-err", "error": f"PASS ABORTED {type(exc).__name__}: {exc}"}]
    finally:
        mc.state_dir = real_sd
    r_err, r_oth = row_of(rows, "m-err"), row_of(rows, "m-oth")
    check("V-MV2-UNDECIDABLE-ISOLATED-FAIL-CLOSED",
          "capsule-v2 undecidable" in (r_err.get("error") or "") and gm.load("m-err")["state"] == gm.HANDOFF
          and not any(a[a.index("-n") + 1].startswith("m-err") for a in launches[n_l:])
          and not any("s-m-err"[:8] in " ".join(s) for s in stops[n_s:]),
          f"err={r_err.get('error')} state={gm.load('m-err')['state']}")
    check("V-MV2-UNDECIDABLE-CONTROL-OTHERS-SUPERVISED",
          (r_oth.get("launch") or {}).get("ok") is True, f"other={r_oth.get('action')} launch={r_oth.get('launch')}")

    trap_hits = list(TRAP.rglob("*")) if TRAP.exists() else []
    check("V-MV2-TRAP-UNTOUCHED", not trap_hits, str(trap_hits[:3]))
    print(f"MV2_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
