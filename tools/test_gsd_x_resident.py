#!/usr/bin/env python3
"""V-gates for the GOAL RESIDENT (vault/specs/gdd-resident-driver.md, Proof).

Every property is driven at both poles: the refusal AND the control where the
same machinery admits, so a resident that refused everything could not pass.
Providers are fakes that implement the engine's provider contract; goal stores
and resident state live in temp dirs (GSDX_GOALS_ROOT / explicit state dirs), so
no real state is touched. Cases that need POSIX process groups, /proc or start
times print UNJUDGED on a host without them -- never PASS.

    python tools/test_gsd_x_resident.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.gsd_x.goal import authority as au      # noqa: E402
from modules.gsd_x.goal import contract as gc       # noqa: E402
from modules.gsd_x.goal import convergence as cv    # noqa: E402
from modules.gsd_x.goal import epoch as ep          # noqa: E402
from modules.gsd_x.goal import git_state as gs      # noqa: E402
from modules.gsd_x.goal import log as gl            # noqa: E402
from modules.gsd_x.goal import sweep as sw          # noqa: E402
from modules.gsd_x.goal.resident import (control, cycle, health, ledgers,   # noqa: E402
                                         missions as ms, procs, store)

GIT = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t", "PYTHONIOENCODING": "utf-8"}
REPO_ID = "7e" * 20
POSIX = procs.ProcInfo().available()
AUTH_ENV = (au.ENV_ANCHOR, au.ENV_FOUNDER_KEY, au.ENV_JUDGE_KEY)


# --- fixtures -----------------------------------------------------------------------

def git(repo: Path, *args: str) -> None:
    subprocess.run([GIT, "-C", str(repo), *args], check=True, env=ENV, capture_output=True)


def make_repo() -> Path:
    d = Path(tempfile.mkdtemp(prefix="gsdx_res_repo_"))
    subprocess.run([GIT, "init", "-q", str(d)], check=True, env=ENV)
    (d / "gate.py").write_text("import sys\nprint('1 passed')\nsys.exit(0)\n", encoding="utf-8")
    git(d, "add", ".")
    git(d, "commit", "-qm", "seed")
    return d


def make_goal(base: Path, gid: str, repo: Path, autonomous: bool = True) -> gl.GoalLog:
    lg = gl.GoalLog(REPO_ID, gid, base=base)
    gc.declare(lg, f"resident {gid}", ["the gate passes"], [], {"paths": ["."]})
    for plane in cv.PLANES:
        s = gc.project(lg)
        cv.set_plane(lg, s, plane, plane in cv.ALWAYS,
                     "" if plane in cv.ALWAYS else "not claimed", "t")
    cv.accept_obligation(lg, gc.project(lg), "ob-outcome", cv.OUTCOME, "prove it",
                         f'"{sys.executable}" gate.py', gs.file_pin(repo, ["gate.py"]), "t")
    if autonomous:
        sw.set_autonomous(lg, gc.project(lg), True, "test", "owner")
    return lg


def green_record(signed_with=None) -> None:
    payload = {"head": gs.head(ROOT), "green": True,
               "suites": {s: {"ok": True} for s in sw.REQUIRED_SUITES}}
    if signed_with is not None:
        payload = au.sign_licence(payload, signed_with)
    rec = sw.record_path()
    rec.parent.mkdir(parents=True, exist_ok=True)
    rec.write_text(json.dumps(payload), encoding="utf-8")


class FakeGate:
    """Implements the engine provider contract. Its `started` set is the
    provider's own durable record of attempt ids (what `probe` consults)."""
    name = "gate"
    wall_bound_s = 60.0

    def __init__(self, mode: str = "close", intents_path: Path | None = None,
                 cancel_error: str = "", probe_error: str = ""):
        self.mode = mode
        self.intents_path = intents_path
        self.cancel_error, self.probe_error = cancel_error, probe_error
        self.dispatched: list = []
        self.cancelled: list = []
        self.started: set = set()
        self.intent_seen_at_dispatch: list = []

    def dispatch(self, spec: dict) -> dict:
        token = spec["identity"]["run_token"]
        if self.intents_path is not None:
            recs, _ = store.read_jsonl(self.intents_path)
            self.intent_seen_at_dispatch.append(any(r.get("attempt_id") == token for r in recs))
        self.started.add(token)
        self.dispatched.append(spec["epoch_id"])
        root = Path(spec["root"])
        if self.mode == "noise":
            n = len(self.dispatched)
            (root / f"noise-{n}.txt").write_text(f"noise {n} {token}\n", encoding="utf-8")
            git(root, "add", ".")
            git(root, "commit", "-qm", f"noise {n}")
        return {"pid": None, "pgid": None, "token": token, "root": str(root),
                "head_before": gs.head(root)}

    def observe(self, handle: dict) -> ep.Observation:
        forced = handle.get("obs")
        if forced == "lost":
            return ep.Observation(ep.OBS_LOST, ep.LOST, "fake: gone")
        if forced == "running" or self.mode == "hang":
            return ep.Observation(ep.OBS_RUNNING, "", "fake: in flight")
        return ep.Observation(ep.OBS_ENDED, ep.COMPLETED, "fake: exit 0")

    def harvest(self, handle: dict, spec: dict) -> ep.Receipt:
        root = Path(spec["root"])
        paths = spec.get("scope_paths") or ["."]
        head = gs.head(root)
        verdicts = []
        if self.mode == "close":
            g = spec["gate"]
            verdicts.append({"gate": g["id"], "exit_status": 0, "observed": "1 passed",
                             "tree_hash": gs.tree_id(root, paths), "revision": spec["revision"],
                             "gate_class": g["class"],
                             "gate_pin": [list(p) for p in gs.file_pin(root, g["files"])]})
        return ep.Receipt(spec["epoch_id"], self.name, spec["revision"],
                          head_before=handle.get("head_before", ""), head_after=head,
                          commits=[head] if self.mode == "noise" else [], verdicts=verdicts,
                          narrative="fake")

    def cancel(self, handle: dict) -> None:
        if self.cancel_error:
            raise RuntimeError(self.cancel_error)
        self.cancelled.append(handle.get("token"))

    def probe(self, identity: dict) -> dict | None:
        if self.probe_error:
            raise RuntimeError(self.probe_error)
        tok = identity.get("run_token", "")
        return {"pid": None, "token": tok} if tok in self.started else None


class FakeInfo(procs.ProcInfo):
    """A process table the test controls: {pid: start_time}, {pgid: [pids]}."""

    def __init__(self, table=None, groups=None, observable=True):
        super().__init__()
        self.table, self.groups, self.observable = dict(table or {}), dict(groups or {}), observable

    def available(self) -> bool:
        return self.observable

    def exists(self, pid):
        return (int(pid) in self.table) if self.observable else None

    def start_time(self, pid):
        return self.table.get(int(pid)) if (self.observable and pid is not None) else None

    def pgid_members(self, pgid):
        if not self.observable or pgid is None:
            return None
        return list(self.groups.get(int(pgid), []))


def new_state() -> Path:
    return Path(tempfile.mkdtemp(prefix="gsdx_res_state_"))


def resident(goals, prov, state=None, fault=None, info=None, **cfg) -> cycle.Resident:
    conf = cycle.Config(cancel_grace_s=0.0, **cfg)
    r = cycle.Resident(ROOT, {"gate": prov}, goals=goals, state_dir=state or new_state(),
                       config=conf, info=info or FakeInfo({os.getpid(): 1}), fault=fault)
    r.start()
    return r


# --- the suite --------------------------------------------------------------------

def main() -> int:
    passes: list = []
    fails: list = []
    unjudged: list = []

    def ok(g, ev):
        passes.append(g)
        print(f"  PASS {g}: {ev}")

    def bad(g, why):
        fails.append(g)
        print(f"  FAIL {g}: {why}")

    def check(g, cond, ev, why):
        (ok if cond else bad)(g, ev if cond else why)

    def unj(g, why):
        unjudged.append(g)
        print(f"  UNJUDGED {g}: {why}")

    for k in AUTH_ENV:
        os.environ.pop(k, None)
    goals_root = Path(tempfile.mkdtemp(prefix="gsdx_res_goals_")) / "goals"
    goals_root.mkdir(parents=True)
    os.environ["GSDX_GOALS_ROOT"] = str(goals_root)
    green_record()

    # --- lock ------------------------------------------------------------------------
    sd = new_state()
    me = os.getpid()
    info = FakeInfo({me: 100})
    a = procs.InstanceLock(sd / "lock", info)
    a.acquire()
    try:
        procs.InstanceLock(sd / "lock", info).acquire()
        bad("V-RES-LOCK-REFUSES-LIVE", "a second instance took a live lock")
    except procs.LockRefused as exc:
        check("V-RES-LOCK-REFUSES-LIVE", exc.reason == procs.LOCK_HELD_ALIVE,
              f"a live holder is refused ({exc.reason})", f"wrong reason {exc.reason}")
    a.release()

    def foreign_lock(pid, start):
        d = new_state()
        (d / "lock").write_text(json.dumps({"pid": pid, "start_time": start, "token": "x"}),
                                encoding="utf-8")
        return d / "lock"

    got = procs.InstanceLock(foreign_lock(424242, 5), FakeInfo({me: 100})).acquire()
    check("V-RES-LOCK-RECLAIMS-ABSENT-PID",
          got["reclaimed"] and "absent" in got["reclaimed"]["evidence"],
          f"a lock whose pid is absent is reclaimed on that evidence ({got['reclaimed']})",
          f"{got}")
    got = procs.InstanceLock(foreign_lock(424242, 5), FakeInfo({me: 100, 424242: 7})).acquire()
    check("V-RES-REUSED-PID-NOT-ALIVE",
          got["reclaimed"] and "reused" in got["reclaimed"]["evidence"],
          "same pid, different start time: a different process, so the lock is stale",
          f"{got}")
    try:
        procs.InstanceLock(foreign_lock(424242, 5), FakeInfo({me: 100, 424242: 5})).acquire()
        bad("V-RES-SAME-START-IS-ALIVE", "a lock with matching pid+start time was reclaimed")
    except procs.LockRefused as exc:
        check("V-RES-SAME-START-IS-ALIVE", exc.reason == procs.LOCK_HELD_ALIVE,
              "control: matching pid + start time is ALIVE and refused", exc.reason)
    try:
        procs.InstanceLock(foreign_lock(424242, 5), FakeInfo(observable=False)).acquire()
        bad("V-RES-UNKNOWN-NEVER-DEAD", "a lock was reclaimed with no evidence")
    except procs.LockRefused as exc:
        check("V-RES-UNKNOWN-NEVER-DEAD", exc.reason == procs.LOCK_HELD_UNKNOWN,
              "no process table (the Windows case): UNKNOWN, refused, not reclaimed", exc.reason)
    real = procs.ProcInfo()
    if POSIX:
        st = real.start_time(me)
        v1, _ = procs.liveness(me, st, real)
        v2, why2 = procs.liveness(me, (st or 0) + 1, real)
        check("V-RES-REUSED-PID-REAL-PROC", v1 == procs.ALIVE and v2 == procs.DEAD,
              f"/proc: own start time ALIVE, a different one DEAD ({why2})", f"{v1} {v2}")
    else:
        v, why = procs.liveness(me, None, real)
        check("V-RES-WINDOWS-LIVENESS-UNKNOWN", v == procs.UNKNOWN and real.start_time(me) is None,
              f"no /proc: start time None and liveness UNKNOWN ({why})", f"{v}")
        unj("V-RES-REUSED-PID-REAL-PROC", "no /proc on this host")

    # --- missions: legal transitions and CAS ----------------------------------------------
    mstore = ms.MissionStore(new_state() / "missions")
    m = mstore.create("m1", ms.ADMITTED, provider="gate")
    try:
        mstore.update("m1", m["version"], ms.HARVESTED)
        bad("V-RES-ILLEGAL-TRANSITION-RAISES", "ADMITTED -> HARVESTED was written")
    except ms.IllegalTransition as exc:
        ok("V-RES-ILLEGAL-TRANSITION-RAISES", f"refused: {exc}")
    m2 = mstore.update("m1", m["version"], ms.DISPATCHED)
    check("V-RES-LEGAL-TRANSITION", m2["state"] == ms.DISPATCHED and m2["version"] == 2,
          "control: ADMITTED -> DISPATCHED is written and versioned", f"{m2}")
    try:
        mstore.update("m1", m["version"], ms.RUNNING)
        bad("V-RES-MISSION-CAS", "a write from a stale version landed")
    except ms.MissionConflict:
        ok("V-RES-MISSION-CAS", "a write computed on version 1 is refused at version 2")

    # --- intent before dispatch -------------------------------------------------------------
    repo = make_repo()
    lg = make_goal(goals_root, "g-intent", repo)
    st_dir = new_state()
    prov = FakeGate("hang", intents_path=st_dir / "intents.jsonl")
    r = resident([(lg, repo)], prov, state=st_dir)
    r.once()
    r.close()
    check("V-RES-INTENT-BEFORE-DISPATCH",
          prov.intent_seen_at_dispatch == [True],
          "the attempt id was durable in intents.jsonl when the provider was called",
          f"{prov.intent_seen_at_dispatch}")

    # --- crash between intent and dispatch -----------------------------------------------
    def crash_at(point):
        def hook(p, **ctx):
            if p == point:
                raise cycle.SimulatedCrash(point)
        return hook

    repo = make_repo()
    lg = make_goal(goals_root, "g-crash-intent", repo)
    st_dir = new_state()
    prov = FakeGate("close")
    r1 = resident([(lg, repo)], prov, state=st_dir, fault=crash_at("after_intent"))
    try:
        r1.once()
        bad("V-RES-CRASH-INJECTED", "the fault hook did not fire")
    except cycle.SimulatedCrash:
        hb = store.read_json(st_dir / "heartbeat.json")
        check("V-RES-CRASH-HEARTBEAT-FAILED", hb["health"] == health.FAILED,
              "the crashed cycle's heartbeat says FAILED", f"{hb['health']}")
    r1.close()                                     # the process died
    r2 = resident([(lg, repo)], prov, state=st_dir)
    rows = {row["mission"]: row for row in r2.last_census}
    check("V-RES-CRASH-AFTER-INTENT-UNCERTAIN",
          len(rows) == 1 and list(rows.values())[0]["classification"] == control.UNCERTAIN,
          f"intent recorded, no handle -> UNCERTAIN, reconciled via probe "
          f"({list(rows.values())[0]['action'] if rows else ''})", f"{rows}")
    r2.once()
    r2.once()
    r2.close()
    eps = ep.project_epochs(gc.project(lg))
    check("V-RES-CRASH-AFTER-INTENT-NO-DISPATCH",
          prov.dispatched == [] and all(e.outcome == ep.LOST for e in eps.values()),
          "nothing was dispatched then or after recovery; the epoch ended LOST and the "
          "engine's info key refuses a blind retry", f"dispatched={prov.dispatched} "
          f"epochs={[(e.state, e.outcome) for e in eps.values()]}")

    repo = make_repo()
    lg = make_goal(goals_root, "g-crash-dispatch", repo)
    st_dir = new_state()
    prov = FakeGate("hang")
    r1 = resident([(lg, repo)], prov, state=st_dir, fault=crash_at("after_dispatch"))
    try:
        r1.once()
    except cycle.SimulatedCrash:
        pass                                        # the injected crash; asserted below
    r1.close()
    r2 = resident([(lg, repo)], prov, state=st_dir)
    row = r2.last_census[0] if r2.last_census else {}
    r2.once()
    r2.once()
    mid = row.get("mission", "")
    mrec = r2.missions.get(mid) or {}
    r2.close()
    check("V-RES-CRASH-AFTER-DISPATCH-ADOPTED",
          row.get("classification") == control.UNCERTAIN and "ADOPTED" in row.get("action", "")
          and len(prov.dispatched) == 1 and mrec.get("state") == ms.RUNNING,
          "the run the provider records is adopted, never dispatched a second time",
          f"row={row} dispatched={prov.dispatched} mission={mrec.get('state')}")

    # --- census classes -----------------------------------------------------------------
    sdc = new_state()
    cstore = ms.MissionStore(sdc / "missions")
    cint = ledgers.IntentLedger(sdc / "intents.jsonl")
    cprov = FakeGate("close")
    cinfo = FakeInfo({me: 1}, groups={4242: [], 4343: [55]})

    def running(mid, **handle):
        cstore.create(mid, ms.ADMITTED, provider="gate", attempt_id=mid,
                      identity={"run_token": mid})
        cint.record(mid, mid, "g", REPO_ID, "gate", {})
        cstore.advance(mid, ms.DISPATCHED, handle={"token": mid, **handle},
                       pgid=handle.get("pgid"))
        cstore.advance(mid, ms.RUNNING)

    running("c-done")
    running("c-lost-dead", obs="lost", pgid=4242)
    running("c-lost-orphans", obs="lost", pgid=4343)
    cstore.create("c-no-intent", ms.ADMITTED, provider="gate", attempt_id="c-no-intent",
                  identity={"run_token": "c-no-intent"})
    cstore.create("c-intent", ms.ADMITTED, provider="gate", attempt_id="c-intent",
                  identity={"run_token": "c-intent"})
    cint.record("c-intent", "c-intent", "g", REPO_ID, "gate", {})
    got = {row["mission"]: row["classification"]
           for row in control.census(cstore, {"gate": cprov}, cint, cinfo)}
    want = {"c-done": control.DONE, "c-lost-dead": control.INCOMPLETE,
            "c-lost-orphans": control.UNCERTAIN, "c-no-intent": control.INCOMPLETE,
            "c-intent": control.UNCERTAIN}
    check("V-RES-CENSUS-CLASSES", got == want,
          f"DONE / INCOMPLETE (no intent; lost+empty pgid) / UNCERTAIN (intent w/o handle; "
          f"lost with live pgid) -- {got}", f"got {got}, want {want}")
    check("V-RES-CENSUS-NO-DISPATCH", cprov.dispatched == [],
          "the census classified and reconciled; it dispatched nothing", f"{cprov.dispatched}")

    # --- STOP honoured mid-cycle ----------------------------------------------------------
    def two_goals(tag):
        ra, rb = make_repo(), make_repo()
        return [(make_goal(goals_root, f"g-{tag}-a", ra), ra),
                (make_goal(goals_root, f"g-{tag}-b", rb), rb)]

    goals = two_goals("stop")
    st_dir = new_state()

    def stop_after_first(point, **ctx):
        if point == "after_goal" and ctx.get("goal") == "g-stop-a":
            (st_dir / "STOP").write_text("{}", encoding="utf-8")

    prov = FakeGate("hang")
    r = resident(goals, prov, state=st_dir, fault=stop_after_first)
    rep = r.once()
    a_m = [x for x in r.missions.all() if x.get("goal_id") == "g-stop-a"]
    r.close()
    a_eps = ep.project_epochs(gc.project(goals[0][0]))
    check("V-RES-STOP-MID-CYCLE",
          rep.stopped and len(prov.dispatched) == 1
          and not ep.project_epochs(gc.project(goals[1][0])),
          "STOP written mid-cycle: the second goal was never touched",
          f"stopped={rep.stopped} dispatched={prov.dispatched}")
    check("V-RES-STOP-CANCELS-OWNED",
          len(prov.cancelled) == 1 and a_m and a_m[0]["state"] == ms.CANCELLED
          and all(e.outcome == ep.CANCELLED for e in a_eps.values()),
          "the owned mission was cancelled by handle and its epoch ended CANCELLED via the engine",
          f"cancelled={prov.cancelled} missions={[x['state'] for x in a_m]}")
    goals = two_goals("nostop")
    prov = FakeGate("hang")
    r = resident(goals, prov)
    rep = r.once()
    r.close()
    check("V-RES-NO-STOP-CONTROL", not rep.stopped and len(prov.dispatched) == 2,
          "control: without STOP both goals are driven in the cycle", f"{prov.dispatched}")

    # --- stagnation ---------------------------------------------------------------------
    repo = make_repo()
    lg = make_goal(goals_root, "g-noise", repo)
    prov = FakeGate("noise")
    k = 2
    r = resident([(lg, repo)], prov, stall_k=k)
    seen, reached = [], None
    for i in range(2 * k + 2):
        rep = r.once()
        seen.append(rep.health)
        if rep.health == health.STALLED:
            reached = i + 1
            break
    esc, _ = store.read_jsonl(r.sd.escalations)
    r.close()
    check("V-RES-NOISE-STALLS",
          reached is not None and health.HEALTHY not in seen and len(prov.dispatched) >= 2
          and esc and esc[0]["step"] == ledgers.ESCALATION_LADDER[0],
          f"commits + receipts + tree moves without gain: STALLED at cycle {reached} (K={k}), "
          f"escalation {esc[0]['step'] if esc else None}", f"health={seen} esc={esc}")
    repo = make_repo()
    lg = make_goal(goals_root, "g-closer", repo)
    prov = FakeGate("close")
    r = resident([(lg, repo)], prov, stall_k=k)
    seen = [r.once().health for _ in range(k + 2)]
    gains, _ = store.read_jsonl(r.sd.gain)
    r.close()
    check("V-RES-CLOSER-HEALTHY",
          seen[-1] == health.HEALTHY and health.STALLED not in seen
          and any(g["gain"] and "ob-outcome" in g["reason"] for g in gains),
          f"control: closing an obligation is gain and keeps HEALTHY ({seen})",
          f"health={seen} gains={[g['reason'] for g in gains]}")

    # --- health is computed -----------------------------------------------------------------
    now = 10_000.0
    f_run = health.HealthFacts(admitted=1, running_missions=2, last_gain_ts=None)
    f_old = health.HealthFacts(admitted=1, running_missions=2, last_gain_ts=now - 7200)
    f_new = health.HealthFacts(admitted=1, running_missions=2, last_gain_ts=now - 60)
    f_idle = health.HealthFacts(admitted=1, last_gain_ts=None)
    hs = [health.compute(f, now, 3600)[0] for f in (f_run, f_old, f_new, f_idle)]
    check("V-RES-NEVER-HEALTHY-WITHOUT-GAIN",
          hs == [health.RUNNING, health.RUNNING, health.HEALTHY, health.STALLED],
          f"no gain -> RUNNING, gain outside window -> RUNNING, gain inside -> HEALTHY, "
          f"alive with nothing moving -> STALLED ({hs})", f"{hs}")

    # --- leases -------------------------------------------------------------------------------
    clock = [1000.0]
    L = ledgers.Leases(new_state() / "leases", clock=lambda: clock[0])
    L.acquire("goal:x", "holder-A", ttl_s=60)
    try:
        L.acquire("goal:x", "holder-B", ttl_s=60)
        bad("V-RES-LIVE-LEASE-RESPECTED", "a live lease was taken by another holder")
    except ledgers.LeaseRefused as exc:
        check("V-RES-LIVE-LEASE-RESPECTED", exc.reason == ledgers.LEASE_HELD,
              f"a live lease is refused ({exc.detail})", exc.reason)
    clock[0] += 61
    got = L.acquire("goal:x", "holder-B", ttl_s=60)
    check("V-RES-EXPIRED-LEASE-RECLAIMED",
          got["reclaimed"] and got["reclaimed"]["holder"] == "holder-A",
          f"an expired lease is reclaimed and the reclaim records whose it was", f"{got}")

    # --- cancel by handle + orphan census --------------------------------------------------
    base = {"id": "k1", "provider": "gate", "handle": {"token": "t"}, "pgid": 77}
    res = control.cancel_by_handle(base, FakeGate(), FakeInfo(groups={77: []}), grace_s=0)
    check("V-RES-CANCEL-CLEAN", res["clean"] and res["orphan_census"]["status"] == control.CLEAN,
          "control: provider cancel ok and an empty process group -> clean, census recorded",
          f"{res}")
    res = control.cancel_by_handle(base, FakeGate(), FakeInfo(groups={77: [901]}), grace_s=0)
    check("V-RES-CANCEL-RECORDS-ORPHANS",
          not res["clean"] and res["orphan_census"]["pids"] == [901] and res["failures"],
          f"orphans in the pgid are recorded and make the cancel not clean ({res['failures']})",
          f"{res}")
    unit = {**base, "scope_unit": "gsdx-ep.scope", "claude_bg_id": "bg1"}
    calls = []

    def failing_runner(argv, timeout=60.0):
        calls.append(argv)
        return (1, "Unit gsdx-ep.scope not loaded.") if argv[0] == "systemctl" else (0, "")

    res = control.cancel_by_handle(unit, FakeGate(cancel_error="boom"),
                                   FakeInfo(groups={77: []}), runner=failing_runner, grace_s=0)
    steps = {s["step"]: s["ok"] for s in res["steps"]}
    check("V-RES-FAILED-STOP-RECORDED",
          not res["clean"] and steps == {"provider_cancel": False, "unit_stop": False,
                                         "claude_stop": True}
          and any("boom" in f for f in res["failures"])
          and ["claude", "stop", "bg1"] in calls,
          f"a raising provider cancel and a failing unit stop are recorded, not swallowed "
          f"({res['failures']})", f"{res}")
    # Through the resident: a failed stop leaves the mission UNCERTAIN and blocks the goal.
    repo = make_repo()
    lg = make_goal(goals_root, "g-badcancel", repo)
    st_dir = new_state()
    prov = FakeGate("hang", cancel_error="kill refused")
    r = resident([(lg, repo)], prov, state=st_dir)
    r.once()
    (st_dir / "STOP").write_text("{}", encoding="utf-8")
    rep = r.once()
    mm = r.missions.all()
    r.close()
    check("V-RES-FAILED-STOP-UNCERTAIN",
          rep.stopped and mm and mm[0]["state"] == ms.UNCERTAIN
          and "kill refused" in json.dumps(mm[0].get("cancel")),
          "a failed stop on STOP is recorded on the mission, which becomes UNCERTAIN",
          f"{[x['state'] for x in mm]}")
    if POSIX:
        proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"],
                                start_new_session=True)
        time.sleep(0.3)
        before = control.orphan_census(proc.pid, real)
        mission = {"id": "real", "provider": "none", "handle": None, "pgid": proc.pid}
        os.killpg(proc.pid, 9)
        proc.wait(timeout=10)
        after = control.orphan_census(proc.pid, real)
        check("V-RES-ORPHAN-CENSUS-REAL-PGID",
              before["status"] == control.ORPHANS and proc.pid in before["pids"]
              and after["status"] == control.CLEAN and mission["pgid"] == proc.pid,
              f"/proc scan sees the live group ({before['pids']}) and not the killed one",
              f"before={before} after={after}")
    else:
        oc = control.orphan_census(me, real)
        check("V-RES-ORPHAN-CENSUS-UNJUDGED-HERE", oc["status"] == control.UNJUDGED,
              "without /proc the orphan census says UNJUDGED, never CLEAN", f"{oc}")
        unj("V-RES-ORPHAN-CENSUS-REAL-PGID", "no /proc process groups on this host")

    # --- admission: paused, ungoverned, unverifiable -------------------------------------------
    repo = make_repo()
    lg = make_goal(goals_root, "g-paused", repo)
    lg.append(gc.project(lg).last_seq + 1, gc.PAUSED, {"reason": "t"}, "founder")
    prov = FakeGate("hang")
    r = resident([(lg, repo)], prov)
    rep = r.once()
    check("V-RES-PAUSED-NOT-ADMITTED",
          prov.dispatched == [] and any("PAUSED" in s for s in rep.skipped),
          "a paused goal is not admitted", f"{rep.skipped} {prov.dispatched}")
    lg.append(gc.project(lg).last_seq + 1, gc.RESUMED, {"reason": "t"}, "founder")
    rep = r.once()
    r.close()
    check("V-RES-RESUMED-ADMITTED", len(prov.dispatched) == 1,
          "control: after RESUMED the same goal is admitted and dispatched", f"{rep.skipped}")

    repo = make_repo()
    lg = make_goal(goals_root, "g-bad-anchor", repo)
    os.environ[au.ENV_ANCHOR] = str(goals_root / "no-such-anchor.json")
    prov = FakeGate("hang")
    r = resident([(lg, repo)], prov)
    rep = r.once()
    r.close()
    check("V-RES-UNVERIFIABLE-ADMITS-NOTHING",
          prov.dispatched == [] and rep.health == health.WAITING_FOR_AUTHORITY
          and "AUTHORITY_UNVERIFIABLE" in rep.health_reason and "UNVERIFIABLE" in
          au.describe(au.load_anchor()) and au.describe(au.load_anchor()) in rep.health_reason,
          f"an unusable anchor is never read as ABSENT: {rep.health} ({rep.health_reason[:90]})",
          f"{rep.health}: {rep.health_reason} dispatched={prov.dispatched}")
    os.environ.pop(au.ENV_ANCHOR, None)
    prov = FakeGate("hang")
    r = resident([(lg, repo)], prov)
    rep = r.once()
    r.close()
    check("V-RES-ABSENT-LEGACY-ADMISSION", len(prov.dispatched) == 1,
          "control: with no anchor (ABSENT) the same unsigned goal is admitted as before",
          f"{rep.health}: {rep.skipped}")

    keys = Path(tempfile.mkdtemp(prefix="gsdx_res_keys_"))
    try:
        f_id, f_entry = au.generate_keypair(keys / "founder.pem", au.FOUNDER)
        j_id, j_entry = au.generate_keypair(keys / "judge.pem", au.JUDGE)
    except au.AuthorityError as exc:
        f_entry = None
        unj("V-RES-UNGOVERNED-NOT-ADMITTED", f"no signing available here: {exc}")
    if f_entry is not None:
        repo = make_repo()
        lg = make_goal(goals_root, "g-ungoverned", repo)       # declared unsigned (ABSENT)
        (keys / "anchor.json").write_text(json.dumps({**f_entry, **j_entry}), encoding="utf-8")
        os.environ[au.ENV_ANCHOR] = str(keys / "anchor.json")
        os.environ[au.ENV_FOUNDER_KEY] = str(keys / "founder.pem")
        os.environ[au.ENV_JUDGE_KEY] = str(keys / "judge.pem")
        green_record(signed_with=au.load_anchor())
        prov = FakeGate("hang")
        r = resident([(lg, repo)], prov)
        rep = r.once()
        check("V-RES-UNGOVERNED-NOT-ADMITTED",
              prov.dispatched == [] and any("UNGOVERNED" in s for s in rep.skipped),
              f"under anchor {au.load_anchor().mode} an unsigned goal is refused",
              f"{rep.skipped} {prov.dispatched}")
        reviewed = gc.project(lg).events[-1].digest       # what the Founder reviewed
        gc.adopt(lg, "founder", reviewed, "test adoption")
        rep = r.once()
        r.close()
        check("V-RES-GOVERNED-ADMITTED", len(prov.dispatched) == 1,
              "control: once adopted with the founder key the same goal is admitted",
              f"{rep.skipped} {rep.notes}")
        for k_ in AUTH_ENV:
            os.environ.pop(k_, None)
        green_record()

    # --- heartbeat + entrance -----------------------------------------------------------------
    import importlib
    cli = importlib.import_module("tools.gsd_x_resident")
    st_dir = new_state()
    repo = make_repo()
    lg = make_goal(goals_root, "g-hb", repo)
    r = resident([(lg, repo)], FakeGate("hang"), state=st_dir)
    r.once()
    r.close()
    hb = store.read_json(st_dir / "heartbeat.json")
    need = {"generation", "pid", "host", "health", "current", "mission", "provider",
            "last_progress_ts", "last_evidence_ts", "budget", "blockers"}
    check("V-RES-HEARTBEAT-FIELDS", need <= set(hb) and hb["generation"] == 1,
          f"heartbeat carries {sorted(need)}", f"missing {need - set(hb)}")
    rc_stop = cli.main(["stop", "--state", str(st_dir)])
    rc_status = cli.main(["status", "--json", "--state", str(st_dir)])
    check("V-RES-CLI-STOP-STATUS", rc_stop == 0 and (st_dir / "STOP").is_file()
          and rc_status in (0, 1),
          "`stop` writes the STOP file and `status --json` reads the heartbeat",
          f"stop={rc_stop} status={rc_status}")
    rc_run_stopped = cli.main(["run", "--state", str(st_dir)])           # STOP still pending
    ctl_dir = new_state()
    rc_run_bound = cli.main(["run", "--max-cycles", "0", "--state", str(ctl_dir)])
    check("V-RES-RUN-STOP-EXIT", rc_run_stopped == cli.STOPPED_EXIT and rc_run_bound == 0,
          f"`run` that honours STOP exits {cli.STOPPED_EXIT} (the unit's RestartPreventExitStatus); "
          "control: a run that reaches its wake bound exits 0 and is restarted",
          f"stopped={rc_run_stopped} bound={rc_run_bound}")

    total = len(passes) + len(fails)
    print(f"\nUNJUDGED ({len(unjudged)}): {unjudged}")
    print(f"GSDX_RESIDENT_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
