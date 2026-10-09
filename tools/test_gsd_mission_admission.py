#!/usr/bin/env python
"""V-ADM-* gates: a compiled work unit launches only through route admission, and the admitted
envelope becomes the worker's session envelope (tools/gsd_mission.py admit_route / launch_worker /
ack_session / adopt_launched; tools/route_admission.py).

Origin: Live QA W0 (m-8bbdf725cd52, 2026-10-05) launched a heavy GSD topology into a 4M envelope and
spent 53.7M before the cost breaker held it. Every refusal here has a launching control, so a gate
that refuses (or admits) everything cannot go green.

Hermetic like test_gsd_mission_envelope.py: state in a temp dir BEFORE import, an injected runner,
no real worker. Mutation drill: GSD_MISSION_DRILL_DIR holding a mutated gsd_mission.py.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

TMP = tempfile.mkdtemp(prefix="gsd-mission-admission-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ.pop("CPP_MISSION_RENEW", None)
os.environ.pop("CPP_ROUTE_ADMISSION", None)
os.environ["CPP_CLAUDE_EXE"] = "__no_such_claude_in_tests__"
sys.path.insert(0, str(Path(__file__).resolve().parent))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
import gsd_mission as gm  # noqa: E402
import mission_spend as ms  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None
FLOORS = str(Path(__file__).resolve().parent.parent / "vault" / "config" / "route-floors.json")

passes = fails = 0
NOW = 1_800_000_000.0
ENV = {"target": 3_500_000, "warn": 4_500_000, "stop": 5_500_000, "calls": 25}
THIN = {"envelope": ENV, "workers": [{"name": "w0r", "profile": "top-level-worker", "calls": 25, "packet": 4000}]}
HEAVY = {"envelope": ENV, "workers": [
    {"name": "orch", "profile": "top-level-worker", "calls": 40, "packet": 5000},
    *({"name": f"exec-{i}", "profile": "gsd-executor", "calls": 20, "packet": 20000} for i in range(3))]}


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def refused(fn) -> bool:
    try:
        fn()
    except gm.MissionError:
        return True
    return False


calls: list = []


def runner(argv, cwd):
    calls.append(argv)   # a distinct bg id per launch: an ack must find exactly ONE launching mission
    return SimpleNamespace(stdout=f"backgrounded · c0ffee{len(calls):02x} · {argv[3]}", stderr="", returncode=0)


def worker_sid(mid: str) -> str:
    return gm.load(mid)["pending"]["bg_id"] + "-0000-4000-8000-000000000000"


def write(name: str, obj) -> str:
    p = Path(TMP) / name
    p.write_text(obj if isinstance(obj, str) else json.dumps(obj), encoding="utf-8")
    return str(p)


def mission(mid: str, packet: bool = True) -> dict:
    gm.create(TMP, "/gsd-autonomous --ws wsx", mission_id=mid, now=NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW,
                  state=gm.RUNNING, epoch=1)
    if packet:
        gm.set_envelope(mid, wu_packet=write(f"{mid}-WU.md", f"# WU {mid}\n"), now=NOW)
    return gm.load(mid)


def launch(mid: str) -> dict:
    cur = gm.load(mid)
    return gm.launch_worker(mid, expect_epoch=cur["epoch"], expect_state=cur["state"], reason="t",
                            runner=runner, now=NOW)


def admit(mid: str, route_name: str, route=THIN, measure=lambda r: None) -> dict:
    return gm.admit_route(mid, write(route_name, route), floors_path=FLOORS, now=NOW, measure=measure)


def refused_launch(mid: str) -> tuple[bool, str]:
    n, before = len(calls), gm.load(mid)["epoch"]
    res = launch(mid)
    ok = res["ok"] is False and len(calls) == n and gm.load(mid)["epoch"] == before
    return ok, res.get("why", "")


def main() -> int:
    # 0. worker_argv: slim-t2 is a print-mode launch carrying the breaker; the default stays `--bg`
    base = {"mission_id": "m-slim", "epoch": 1, "card": "KERNEL", "model": "sonnet"}
    t2 = gm.worker_argv({**base, "worker_profile": "slim-t2"}, "do it")
    t1 = gm.worker_argv({**base, "worker_profile": "slim-t1"}, "do it")
    dflt = gm.worker_argv(dict(base), "do it")
    check("V-ADM-SLIM-T2-ARGV", "-p" in t2 and "--bg" not in t2 and "--no-session-persistence" not in t2
          and any(a.startswith("--settings=") and a.endswith("slim-critical-settings.json") for a in t2)
          and f"--tools={','.join(gm.SLIM_DEFAULT_TOOLS)}" in t2 and ("PowerShell" in gm.SLIM_DEFAULT_TOOLS) == (os.name == "nt") and "--system-prompt=KERNEL" in t2 and t2[-1] == "do it", str(t2))
    check("V-ADM-SLIM-T1-ARGV", "-p" in t1 and "--bg" not in t1 and "--no-session-persistence" in t1
          and not any(a.startswith("--settings=") for a in t1))
    check("V-ADM-DEFAULT-ARGV-UNCHANGED", dflt[1] == "--bg" and "-p" not in dflt
          and not any(a.startswith("--settings=") for a in dflt) and "--autocompact" in dflt and dflt[-1] == "do it", str(dflt))
    t2p = gm.worker_argv({**base, "worker_profile": "slim-t2", "permission_mode": "auto",
                          "allowed_tools": ["Bash(git commit:*)"]}, "do it")
    check("V-ADM-SLIM-PERMISSIONS", "--permission-mode=acceptEdits" in t2 and "--permission-mode=auto" in t2p
          and "--allowedTools=Edit(.planning/**)" in t2 and "--allowedTools=Bash(git commit:*)" in t2p
          and not any(a in ("--allowedTools", "--permission-mode") for a in t2p) and t2p[-1] == "do it", str(t2p))
    check("V-ADM-SLIM-FROM-ADMISSION", gm.slim_profile({"admission": {"workers": [{"profile": "slim-t2"}]}}) == "slim-t2"
          and gm.slim_profile({"admission": {"workers": [{"profile": "top-level-worker"}]}}) is None)

    # 1. an unadmitted packet refuses BEFORE the claim; the refusal is on the ledger
    mission("m-un")
    ok, why = refused_launch("m-un")
    check("V-ADM-UNADMITTED-REFUSED", ok and "not admitted" in why, why)
    check("V-ADM-REFUSAL-LEDGERED", any(e.get("event") == "launch_refused_admission" for e in gm.lr.ledger_events("m-un")))

    # 2. heavy route recorded as RECOMPILE and refused; thin route ADMISSIBLE launches (control)
    mission("m-heavy")
    h = admit("m-heavy", "heavy.json", HEAVY)["admission"]
    ok, why = refused_launch("m-heavy")
    check("V-ADM-HEAVY-RECORDED-AND-REFUSED", h["verdict"] == "RECOMPILE" and ok, f"{h['verdict']}: {why}")
    mission("m-thin")
    t = admit("m-thin", "thin.json")["admission"]
    res = launch("m-thin")
    check("V-ADM-THIN-LAUNCHES", t["verdict"] == "ADMISSIBLE" and res.get("ok") is True, str(res))

    # 3. the admission is bound to the packet and the route file
    mission("m-pkt")
    admit("m-pkt", "pkt-route.json")
    write("m-pkt-WU.md", "# WU m-pkt EDITED\n")
    ok, why = refused_launch("m-pkt")
    check("V-ADM-PACKET-CHANGE-REFUSED", ok and "packet changed" in why, why)
    admit("m-pkt", "pkt-route.json")
    check("V-ADM-READMIT-LAUNCHES", launch("m-pkt").get("ok") is True)
    mission("m-route")
    admit("m-route", "route-r.json")
    write("route-r.json", {**THIN, "workers": [{**THIN["workers"][0], "calls": 24}]})
    ok, why = refused_launch("m-route")
    check("V-ADM-ROUTE-CHANGE-REFUSED", ok and "route file" in why, why)

    # 4. a mission without a packet (the GSD resume route) is not judged here (control)
    mission("m-gsd", packet=False)
    check("V-ADM-NO-PACKET-NOT-JUDGED", launch("m-gsd").get("ok") is True)

    # 5. kill switch: launches, and the bypass is on the ledger
    mission("m-kill")
    os.environ["CPP_ROUTE_ADMISSION"] = "off"
    try:
        res = launch("m-kill")
    finally:
        os.environ.pop("CPP_ROUTE_ADMISSION", None)
    check("V-ADM-KILL-SWITCH", res.get("ok") is True
          and any(e.get("event") == "admission_bypassed" for e in gm.lr.ledger_events("m-kill")), str(res))

    # 6. DEFER from the breaker's own numbers: 2 x 2M estimate - 3M attributed spend = 1M left
    mission("m-defer")
    gm.set_envelope("m-defer", token_estimate="2M", now=NOW)
    d = admit("m-defer", "defer.json", measure=lambda r: 3_000_000)["admission"]
    ok, _ = refused_launch("m-defer")
    check("V-ADM-DEFER-FROM-BREAKER", d["verdict"] == "DEFER" and d["remaining"] == 1_000_000 and ok, str(d["reasons"]))
    d2 = admit("m-defer", "defer.json", measure=lambda r: 100_000)["admission"]
    check("V-ADM-DEFER-CONTROL", d2["verdict"] == "ADMISSIBLE", f"remaining {d2['remaining']:,}")

    # 7. refusals of admit itself write nothing
    mission("m-nopkt", packet=False)
    seq = gm.load("m-nopkt")["seq"]
    check("V-ADM-ADMIT-NEEDS-PACKET", refused(lambda: admit("m-nopkt", "x.json")) and gm.load("m-nopkt")["seq"] == seq)
    seq = gm.load("m-thin")["seq"]
    check("V-ADM-MALFORMED-ROUTE-REFUSED",
          refused(lambda: gm.admit_route("m-thin", write("bad.json", "{not json"), floors_path=FLOORS, now=NOW))
          and refused(lambda: admit("m-thin", "bad2.json", {"envelope": ENV, "workers": []}))
          and gm.load("m-thin")["seq"] == seq)

    # 8. the worker's ack declares the admitted envelope as its SESSION envelope
    sid = worker_sid("m-thin")
    acked = gm.ack_session(sid, pid=1, now=NOW + 5)   # m-thin is LAUNCHING with its own bg_id
    bp = ms.budget_path(sid)
    budget = json.loads(bp.read_text(encoding="utf-8")) if bp.is_file() else {}
    check("V-ADM-ACK-DECLARES-ENVELOPE", acked and acked["mission_id"] == "m-thin"
          and (budget.get("target"), budget.get("stop"), budget.get("calls_estimate")) == (3_500_000, 5_500_000, 25),
          str(budget))
    check("V-ADM-ENVELOPE-LEDGERED", any(e.get("event") == "worker_envelope_declared" and e.get("worker") == sid
                                         for e in gm.lr.ledger_events("m-thin")))
    gsd_sid = worker_sid("m-gsd")
    gacked = gm.ack_session(gsd_sid, pid=2, now=NOW + 5)          # m-gsd: no packet, no admission
    check("V-ADM-NO-ADMISSION-NO-ENVELOPE", gacked and gacked["mission_id"] == "m-gsd"
          and not ms.budget_path(gsd_sid).exists())

    # 9. adoption (the worker's own ack never arrived) declares it too
    mission("m-adopt")
    admit("m-adopt", "adopt.json")
    launch("m-adopt")
    asid = worker_sid("m-adopt")
    gm.adopt_launched(gm.load("m-adopt"), {"sessionId": asid, "pid": 3}, now=NOW + 6)
    check("V-ADM-ADOPT-DECLARES-ENVELOPE", ms.budget_path(asid).is_file())
    # Replay of m-8bbdf725cd52 epoch 2 (2026-10-06): a record whose resume command does not start with
    # '/' makes _arm_worker_marker raise during adoption; the envelope must already be declared.
    mission("m-adopt-raise")
    cur = gm.load("m-adopt-raise")
    gm.transition("m-adopt-raise", expect_epoch=cur["epoch"], expect_state=cur["state"], event="t_shape", now=NOW,
                  resume_command="MISSION: InfinityOps Sidecar Live QA (record shape seen in production)")
    admit("m-adopt-raise", "adopt-raise.json")
    launch("m-adopt-raise")
    rsid = worker_sid("m-adopt-raise")
    raised = None
    try:
        gm.adopt_launched(gm.load("m-adopt-raise"), {"sessionId": rsid, "pid": 4}, now=NOW + 7)
    except Exception as exc:  # noqa: BLE001 -- the replay expects the marker to raise
        raised = type(exc).__name__
    check("V-ADM-ADOPT-ENVELOPE-SURVIVES-MARKER-ERROR", ms.budget_path(rsid).is_file(),
          f"marker raised {raised}; envelope declared {ms.budget_path(rsid).is_file()}")

    # 9b. review F3: one admission pays for ONE launch; the successor re-admits (remaining re-measured)
    thin_rec = gm.load("m-thin")
    check("V-ADM-LAUNCH-CONSUMES", (thin_rec.get("admission") or {}).get("consumed_epoch") == 2,
          str((thin_rec.get("admission") or {}).get("consumed_epoch")))
    ok, why = refused_launch("m-thin")
    check("V-ADM-SECOND-LAUNCH-REFUSED", ok and "used by epoch 2" in why, why)
    check("V-ADM-CONTINUATION-NOT-CONSUMED", gm.admission_refusal(gm.load("m-thin"), for_launch=False) is None,
          "the session that admission launched may continue")
    re = admit("m-thin", "thin-again.json", measure=lambda r: None)["admission"]
    check("V-ADM-READMIT-AFTER-USE-LAUNCHES", re.get("consumed_epoch") is None and launch("m-thin").get("ok") is True)
    mission("m-unused")
    admit("m-unused", "unused.json")
    gm.transition("m-unused", expect_epoch=1, expect_state=gm.RUNNING, event="t_fail", now=NOW)
    n = len(calls)
    failing = lambda argv, cwd: (calls.append(argv), SimpleNamespace(stdout="", stderr="refused", returncode=1))[1]
    cur = gm.load("m-unused")
    gm.launch_worker("m-unused", expect_epoch=cur["epoch"], expect_state=cur["state"], reason="t", runner=failing, now=NOW)
    check("V-ADM-FAILED-LAUNCH-KEEPS-ADMISSION", len(calls) == n + 1
          and (gm.load("m-unused").get("admission") or {}).get("consumed_epoch") is None,
          "a launch the host refused started nothing and does not use the admission up")

    # 9c. slim launch: pre-generated session id, budget file before the process, detached spawn, completion
    SLIM = {"envelope": {"target": 200_000, "warn": 250_000, "stop": 300_000, "calls": 10},
            "workers": [{"name": "s0", "profile": "slim-t2", "calls": 3, "packet": 500}]}
    mission("m-slimlaunch")
    sa = admit("m-slimlaunch", "slim-route.json", SLIM)
    check("V-ADM-WORKER-PROFILE-RECORDED", sa.get("worker_profile") == "slim-t2" and sa["admission"]["verdict"] == "ADMISSIBLE"
          and sa["admission"]["workers"][0]["profile"] == "slim-t2", str(sa.get("worker_profile")))
    seen: dict = {}

    def spawner(argv, cwd, out_path, err_path):
        sid = next(a.split("=", 1)[1] for a in argv if a.startswith("--session-id="))
        bf = ms.budget_path(sid)
        seen.update(argv=argv, sid=sid, cwd=cwd, out=out_path, err=err_path,
                    budget=json.loads(bf.read_text(encoding="utf-8")) if bf.exists() else None)
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)   # what the real spawner does
        return 4242

    def no_bg(argv, cwd):
        raise AssertionError("slim launch must not use the --bg runner")

    cur = gm.load("m-slimlaunch")
    sres = gm.launch_worker("m-slimlaunch", expect_epoch=cur["epoch"], expect_state=cur["state"], reason="t",
                            runner=no_bg, spawner=spawner, now=NOW)
    srec = gm.load("m-slimlaunch")
    check("V-ADM-SLIM-BINDS-OWN-SID", sres.get("ok") is True and sres["bg_id"] == seen["sid"]
          and srec["state"] == gm.RUNNING and srec["owner"]["session_id"] == seen["sid"]
          and srec["owner"]["kind"] == "slim" and srec["owner"]["pid"] == 4242 and "--bg" not in seen["argv"]
          and "-p" in seen["argv"] and seen["argv"][-1] == gm.launch_prompt(cur), str(sres))
    check("V-ADM-SLIM-BUDGET-BEFORE-SPAWN", seen["budget"] is not None and seen["budget"]["stop"] == 300_000
          and seen["budget"]["target"] == 200_000 and seen["budget"]["calls_estimate"] == 10, str(seen["budget"]))
    check("V-ADM-SLIM-ADMISSION-CONSUMED", srec["admission"].get("consumed_epoch") == srec["epoch"])
    check("V-ADM-SLIM-DEFAULT-BG-UNCHANGED", gm.worker_argv(dict(base), "do it", session_id="x") == dflt)
    owner = srec["owner"]
    alive, dead = (lambda p: True), (lambda p: False)
    p_run = gm.plan_next(srec, NOW + 60, [], alive)
    check("V-ADM-SLIM-RUNNING-NOT-FINISHED", p_run["action"] == "none" and "running" in p_run["reason"], str(p_run))
    p_dead = gm.plan_next(srec, NOW + 60, [], dead)
    check("V-ADM-SLIM-EXIT-NO-JSON-HALTS", p_dead["action"] == "halt" and "no result JSON" in p_dead["reason"], str(p_dead))
    Path(owner["out_path"]).write_text(json.dumps(
        {"type": "result", "is_error": False, "result": "done", "session_id": owner["session_id"],
         "usage": {"input_tokens": 2, "cache_read_input_tokens": 10, "output_tokens": 5},
         "permission_denials": [{"tool_name": "Read"}]}), encoding="utf-8")
    p_fin = gm.plan_next(srec, NOW + 60, [], alive)
    check("V-ADM-SLIM-JSON-MEANS-FINISHED", p_fin["action"] == "slim_finished" and p_fin["slim"]["tokens"] == 17
          and p_fin["slim"]["denials"] == 1 and p_fin["slim"]["session_id"] == owner["session_id"], str(p_fin))
    write("m-slimlaunch-WU-receipt.md", "# receipt\nStatus: DONE\n")
    rows = gm.supervise(now=NOW + 60, sessions=[], pid_alive=dead)
    done = gm.load("m-slimlaunch")
    check("V-ADM-SLIM-SUPERVISE-COMPLETES", done["state"] == gm.COMPLETED and done["slim_result"]["result"] == "done",
          f"{done['state']} {[r for r in rows if r['mission_id'] == 'm-slimlaunch']}")
    # A worker the breaker stopped exits cleanly (is_error=false); the guard's state file decides.
    def finish_slim(mid, route_file, state):
        mission(mid)
        admit(mid, route_file, SLIM)
        cur = gm.load(mid)
        gm.launch_worker(mid, expect_epoch=cur["epoch"], expect_state=cur["state"], reason="t",
                         runner=no_bg, spawner=spawner, now=NOW)
        own = gm.load(mid)["owner"]
        Path(own["out_path"]).write_text(json.dumps(
            {"type": "result", "is_error": False, "result": "stopped by budget" if state["closeout"] else "done",
             "session_id": own["session_id"], "usage": {"output_tokens": 5}, "permission_denials": []}),
            encoding="utf-8")
        sp = ms.budget_path(own["session_id"])
        sp.with_name(f"session-budget-{own['session_id']}.state.json").write_text(json.dumps(state), encoding="utf-8")
        if not state["closeout"]:
            write(f"{mid}-WU-receipt.md", "# receipt\nStatus: DONE\n")
        gm.supervise(now=NOW + 60, sessions=[], pid_alive=dead)
        return gm.load(mid)

    trip = finish_slim("m-slimtrip", "slim-route-t.json", {"ids": [], "tokens": 350_000, "calls": 3, "closeout": 1})
    check("V-ADM-SLIM-TRIPPED-HALTS-NOT-COMPLETES", trip["state"] == gm.HALTED
          and "breaker tripped" in (trip.get("reason") or "")
          and (trip["slim_result"].get("tripped") or "").startswith("breaker tripped"), f"{trip['state']} {trip.get('reason')}")
    ok = finish_slim("m-slimok", "slim-route-o.json", {"ids": [], "tokens": 120_000, "calls": 3, "closeout": 0})
    check("V-ADM-SLIM-UNTRIPPED-STATE-COMPLETES", ok["state"] == gm.COMPLETED and ok["slim_result"].get("tripped") is None,
          f"{ok['state']} {ok.get('reason')}")
    # Epoch 4 of m-8bbdf725cd52 (2026-10-06) was spawned in the main checkout (`cwd`) instead of its
    # worktree (`work_dir`). The worker must start where the work lives; no work_dir keeps `cwd`.
    check("V-ADM-SLIM-NO-WORKDIR-SPAWNS-IN-CWD", Path(seen["cwd"]) == Path(srec["cwd"]), f"{seen['cwd']} vs {srec['cwd']}")
    wt = Path(TMP) / "wt-slim"
    wt.mkdir(exist_ok=True)
    mission("m-slimwd")
    cur = gm.load("m-slimwd")
    gm.transition("m-slimwd", expect_epoch=cur["epoch"], expect_state=cur["state"], event="t_wd", now=NOW, work_dir=str(wt))
    admit("m-slimwd", "slim-route-w.json", SLIM)
    cur = gm.load("m-slimwd")
    gm.launch_worker("m-slimwd", expect_epoch=cur["epoch"], expect_state=cur["state"], reason="t",
                     runner=no_bg, spawner=spawner, now=NOW)
    check("V-ADM-SLIM-SPAWNS-IN-WORK-DIR", Path(seen["cwd"]) == wt, f"spawned in {seen['cwd']}, work_dir {wt}")
    mission("m-slimfail")
    admit("m-slimfail", "slim-route-f.json", SLIM)
    cur = gm.load("m-slimfail")
    gm.launch_worker("m-slimfail", expect_epoch=cur["epoch"], expect_state=cur["state"], reason="t", runner=no_bg,
                     spawner=lambda *a: (_ for _ in ()).throw(OSError("no exe")), now=NOW)
    check("V-ADM-SLIM-SPAWN-FAILURE-LEDGERED", gm.load("m-slimfail")["state"] == gm.LAUNCHING and any(
        e.get("event") == "launch_failed" for e in gm.lr.ledger_events("m-slimfail")))

    # 10. CLI: admitted exit 0, rejected exit 3
    mission("m-cli")
    rc_ok = gm._cli(["admit", "--mission", "m-cli", "--route", write("cli-thin.json", THIN), "--floors", FLOORS])
    rc_no = gm._cli(["admit", "--mission", "m-cli", "--route", write("cli-heavy.json", HEAVY), "--floors", FLOORS])
    check("V-ADM-CLI", (rc_ok, rc_no) == (0, 3), f"{rc_ok} {rc_no}")

    print(f"ADM_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
