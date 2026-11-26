#!/usr/bin/env python
"""V-W3-* gates: mission-capital W3 (spec vault/specs/mission-capital-state.md "W3").

Predictive renewal (H4), the in-process capital event path (H5) and exactly-once under races: poller vs event,
worker block vs poller, manual Owner raise vs a half-written auto grant, a process killed mid-grant, and N
concurrent passes. Hermetic like test_mission_topup.py: state in a temp dir, spend and governor injected, progress
judged on real throw-away git repos, every event driven through the real gsd_mission write that raises it.
Each refusal pole has a control; the race has a revert control (2455e994, pre-W3) that double-grants.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="mission-topup-w3-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_WORK_CLASS_PROFILE_DIR"] = str(Path(TMP) / "wcp")
os.environ["CPP_RESOURCE_ADMISSION"] = "off"
os.environ["CPP_MISSION_ACCOUNT_ADMISSION"] = "off"
os.environ["CPP_MISSION_NOTIFY_TOAST"] = "off"
for _k in ("CPP_MISSION_AUTO_TOPUP", "TELEGRAM_BOT_TOKEN", "CPP_TOPUP_EVENT", "CPP_TOPUP_PREDICTIVE",
           "CPP_CAPITAL_STATE", "CPP_PROGRESS_RECEIPTS"):
    os.environ.pop(_k, None)
TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import gsd_mission as gm  # noqa: E402
import mission_topup as mt  # noqa: E402
import account_governor as _ag  # noqa: E402
import mission_spend as _ms  # noqa: E402

GOV_DIR = os.path.join(TMP, "governor")
_ag.DEFAULT_STATE = GOV_DIR
_ag.check = lambda state_dir, action: (0, "ALLOW", "test governor", {})
SPEND: dict = {}
_ms.processed_tokens = lambda rec, *a, **k: SPEND.get(rec.get("mission_id"))

passes = fails = 0
GIT = gm.resolve_exe("git") or "git"
TRIP = "cost breaker (mission authority): processed 119,000,000 >= authority 120,000,000 minus closeout reserve"
ASK = "OWNER_BOUNDARY (AUTHORITY): raise authority: 119,000,000 of 120,000,000 processed; host needs: more"


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def git(repo, *args):
    subprocess.run([GIT, "-C", str(repo), *args], check=True, capture_output=True)


def commit(repo, rel, text):
    p = Path(repo) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", f"edit {rel}")


class env:
    """Set env vars for a block, restore after (the switches are read on every call)."""

    def __init__(self, **kv):
        self.kv, self.old = kv, {}

    def __enter__(self):
        for k, v in self.kv.items():
            self.old[k] = os.environ.get(k)
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def __exit__(self, *exc):
        for k, v in self.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def mission(name, spend, running=True, epoch=0, policy=True):
    """A live mission on its own git repo, authority 120M, 3 x 40M top-ups, `spend` processed."""
    repo = Path(TMP) / name
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "t@t")
    git(repo, "config", "user.name", "t")
    commit(repo, "README.md", "x")
    mid = f"m-{name}"
    SPEND[mid] = 1_000_000   # budgeted at arm, before the spend: set_authority refuses a ceiling already overrun
    gm.create(str(repo), "/gsd-autonomous", mission_id=mid)
    if policy:
        mt.budget(mid, "120M", 3, "40M", reason="w3 test")
    else:
        gm.set_authority(mid, tokens="120M", reason="w3 test (no policy)")
    SPEND[mid] = spend
    if running:
        gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="test_running", state=gm.RUNNING,
                      epoch=epoch)
    return mid, str(repo)


def rows(mid, event, **match):
    return [e for e in gm.lr.ledger_events(mid)
            if e.get("event") == event and all(e.get(k) == v for k, v in match.items())]


def decisions(mid, prefix):
    return [d["id"] for d in (gm.load(mid).get("decisions") or []) if d["id"].startswith(prefix)]


def real_decide(mid, text, decision_id=None):
    return gm.deliver_decision(mid, text, decision_id=decision_id, wake=False)


def hold(mid, reason=TRIP):
    """A mission-authority cost hold set with the event path OFF (the state a poller pass finds)."""
    with env(CPP_TOPUP_EVENT="off"):
        gm.set_owner_hold(mid, reason, kind="cost")


def predictive_gates():
    # V-W3-PREDICTIVE-GRANT (H4): running, headroom 19M < next lease (policy step 40M), commits -> grant BEFORE park
    m, r = mission("pred", 100_000_000)
    commit(r, "src/a.ts", "1")
    res = mt.sweep_one(m, decide_fn=real_decide, predictive=True)
    rec, pol = gm.load(m), mt.load_policy(m)
    g = (pol.get("grants") or [{}])[-1]
    check("V-W3-PREDICTIVE-GRANT", res["action"] == "grant" and res.get("predictive") and
          rec["authority_tokens"] == 160_000_000 and rec["state"] == gm.RUNNING and not rec.get("owner_hold")
          and str(g.get("hold_set_at")).startswith("pressure:e0:a120000000") and decisions(m, "") == []
          and rows(m, "authority_auto_topup", predictive=True),
          f"{res['action']} auth={rec['authority_tokens']} key={g.get('hold_set_at')} why={res.get('why')}")
    # exactly once: the raise moved the authority (new key), and no progress since this grant -> none
    res2 = mt.sweep_one(m, decide_fn=real_decide, predictive=True)
    check("V-W3-PREDICTIVE-EXACTLY-ONCE", res2["action"] == "none" and len(mt.load_policy(m)["grants"]) == 1
          and gm.load(m)["authority_tokens"] == 160_000_000, f"{res2['action']} {res2.get('why')}")

    # controls: healthy headroom / no progress / switch off / ceiling reached / held -- none, and nobody is told
    m, r = mission("predhealthy", 10_000_000)
    commit(r, "src/a.ts", "1")
    res = mt.sweep_one(m, decide_fn=real_decide, predictive=True)
    check("V-W3-PREDICTIVE-HEALTHY-NONE", res["action"] == "none" and res.get("capital_state") == "HEALTHY"
          and gm.load(m)["authority_tokens"] == 120_000_000, f"{res['action']} {res.get('capital_state')}")
    m, r = mission("prednoprog", 100_000_000)
    res = mt.sweep_one(m, decide_fn=real_decide, predictive=True)
    check("V-W3-PREDICTIVE-NO-PROGRESS-NONE", res["action"] == "none" and "no progress" in res["why"]
          and not rows(m, "authority_auto_topup_refused") and gm.load(m)["authority_tokens"] == 120_000_000,
          res.get("why"))
    m, r = mission("predoff", 100_000_000)
    commit(r, "src/a.ts", "1")
    with env(CPP_TOPUP_PREDICTIVE="off"):
        res = mt.sweep_one(m, decide_fn=real_decide)
    check("V-W3-PREDICTIVE-KILL-SWITCH", res["action"] == "none" and gm.load(m)["authority_tokens"] == 120_000_000,
          res.get("why"))
    m, r = mission("predceil", 100_000_000)
    mt.budget(m, "120M", None, "40M", ceiling="120M", reason="ceiling = authority")
    commit(r, "src/a.ts", "1")
    res = mt.sweep_one(m, decide_fn=real_decide, predictive=True)
    check("V-W3-PREDICTIVE-CEILING-NONE", res["action"] == "none" and "ceiling" in res["why"], res.get("why"))
    m, r = mission("predlease", 60_000_000)
    commit(r, "src/a.ts", "1")
    # next lease = the work class's settled p80 (here one 70M sample), not the step: headroom 59M is PRESSURE
    import work_class_profile as wcp
    wcp.main(["settle", "--class", "W3_CLASS", "--unit", "u1", "--processed", "70000000", "--calls", "300",
              "--avg-ctx", "200000", "--max-ctx", "300000", "--attempts", "1", "--attempts-failed", "0",
              "--cause", "w3 test sample"])
    gm.transition(m, expect_epoch=0, expect_state=gm.RUNNING, event="test_class", work_class="W3_CLASS")
    lease = mt.next_lease(gm.load(m), mt.load_policy(m))
    res = mt.sweep_one(m, decide_fn=real_decide, predictive=True)
    check("V-W3-PREDICTIVE-LEASE-FORECAST", lease[0] == 70_000_000 and "W3_CLASS" in lease[1] and res["action"] == "grant",
          f"lease={lease} {res['action']} {res.get('why')}")
    m2, r2 = mission("predleasectl", 60_000_000)
    commit(r2, "src/a.ts", "1")
    res = mt.sweep_one(m2, decide_fn=real_decide, predictive=True)
    check("V-W3-PREDICTIVE-LEASE-STEP-CONTROL", res["action"] == "none" and res.get("capital_state") == "HEALTHY",
          f"step lease 40M vs headroom 59M: {res['action']} {res.get('capital_state')}")

    # V-W3-FORECAST-EVENT: the real forecast_invalidated write (H4 00:31Z) tops up in the same call
    m, r = mission("predfc", 100_000_000)
    commit(r, "src/a.ts", "1")
    rec = gm.load(m)
    gm._recompile_forecast(rec, time.time(), {"spent": 100_000_000, "estimate": 50_000_000,
                                               "authority": 120_000_000, "ratio": 0.9})
    rec = gm.load(m)
    check("V-W3-FORECAST-EVENT", rec["authority_tokens"] == 160_000_000 and
          rows(m, "capital_event", cause="forecast_invalidated", action="grant"),
          f"auth={rec['authority_tokens']} events={[e.get('cause') for e in rows(m, 'capital_event')]}")
    m, r = mission("predfcoff", 100_000_000)
    commit(r, "src/a.ts", "1")
    with env(CPP_TOPUP_EVENT="off"):
        gm._recompile_forecast(gm.load(m), time.time(), {"spent": 100_000_000, "estimate": 50_000_000,
                                                          "authority": 120_000_000, "ratio": 0.9})
    check("V-W3-FORECAST-EVENT-KILL-SWITCH", gm.load(m)["authority_tokens"] == 120_000_000
          and not rows(m, "capital_event"), f"auth={gm.load(m)['authority_tokens']}")

    # V-W3-PRE-LAUNCH-EVENT: launch_worker asks for a predictive top-up before a relaunch claims its epoch
    m, r = mission("predlaunch", 100_000_000, epoch=1)
    commit(r, "src/a.ts", "1")
    seen = []
    real_ev = mt.on_capital_event

    def spy(mid, cause, **k):
        seen.append(cause)
        return real_ev(mid, cause, **k)

    def no_launch(*a, **k):
        raise RuntimeError("w3 test: no worker is launched")

    mt.on_capital_event = spy
    try:
        try:
            gm.launch_worker(m, expect_epoch=1, expect_state=gm.RUNNING, reason="w3 relaunch", runner=no_launch,
                             spawner=no_launch)
        except Exception as exc:  # noqa: BLE001 -- only the pre-claim top-up is under test
            launch_exc = type(exc).__name__
        else:
            launch_exc = None
    finally:
        mt.on_capital_event = real_ev
    check("V-W3-PRE-LAUNCH-EVENT", "pre_launch" in seen and gm.load(m)["authority_tokens"] == 160_000_000,
          f"seen={seen} auth={gm.load(m)['authority_tokens']} launch={launch_exc}")


def event_gates():
    # V-W3-EVENT-COST-HOLD (H5): the breaker's own hold renews in the same call -- no poller pass
    m, r = mission("evhold", 119_000_000)
    commit(r, "src/a.ts", "1")
    out = gm.set_owner_hold(m, TRIP, kind="cost")
    rec = gm.load(m)
    check("V-W3-EVENT-COST-HOLD", not rec.get("owner_hold") and rec["authority_tokens"] == 160_000_000
          and decisions(m, "TOPUP") == ["TOPUP1"] and (rec.get("pending_wake") or {}).get("decision_id") == "TOPUP1"
          and out.get("seq") == rec.get("seq") and rows(m, "capital_event", cause="cost_hold", action="grant"),
          f"hold={bool(rec.get('owner_hold'))} auth={rec['authority_tokens']} wake={rec.get('pending_wake')}")
    # the grant's own set_authority / release / decide were not re-dispatched as events (reentrancy)
    check("V-W3-EVENT-NO-REENTRY", [e.get("cause") for e in rows(m, "capital_event")] == ["cost_hold"]
          and len(mt.load_policy(m)["grants"]) == 1 and len(rows(m, "authority_auto_topup")) == 1,
          f"events={[e.get('cause') for e in rows(m, 'capital_event')]}")
    m, r = mission("evholdoff", 119_000_000)
    commit(r, "src/a.ts", "1")
    with env(CPP_TOPUP_EVENT="off"):
        gm.set_owner_hold(m, TRIP, kind="cost")
    check("V-W3-EVENT-KILL-SWITCH", bool(gm.load(m).get("owner_hold")) and gm.load(m)["authority_tokens"] == 120_000_000,
          "hold stands until the poller")
    m, r = mission("evnopol", 119_000_000, policy=False)
    commit(r, "src/a.ts", "1")
    gm.set_owner_hold(m, TRIP, kind="cost")
    check("V-W3-EVENT-NO-POLICY-NOOP", bool(gm.load(m).get("owner_hold")) and not rows(m, "capital_event")
          and not rows(m, "capital_event_error"), "no policy: one stat, nothing acts")
    # an event fault never fails the write that raised it
    m, r = mission("everr", 119_000_000)
    real_sweep = mt.sweep_one

    def boom(*a, **k):
        raise RuntimeError("w3 injected fault")

    mt.sweep_one = boom
    try:
        held = gm.set_owner_hold(m, TRIP, kind="cost")
    finally:
        mt.sweep_one = real_sweep
    check("V-W3-EVENT-FAULT-ISOLATED", bool(held.get("owner_hold")) and rows(m, "capital_event_error", cause="cost_hold"),
          f"held={bool(held.get('owner_hold'))}")

    # V-W3-EVENT-BLOCKED (H1+H5): the worker's own BLOCKED/CAPITAL_EXHAUSTED renews in the same call
    m, r = mission("evblk", 119_000_000, epoch=1)
    commit(r, "src/a.ts", "1")
    rec = gm.load(m)
    gm.block_mission(rec, expect_epoch=rec["epoch"], expect_state=gm.RUNNING, reason=ASK)
    rec = gm.load(m)
    check("V-W3-EVENT-BLOCKED", rec["state"] == gm.RUNNING and rec["authority_tokens"] == 160_000_000
          and decisions(m, "TOPUP") == ["TOPUP1"] and rows(m, "capital_event", cause="blocked", action="grant"),
          f"state={rec['state']} auth={rec['authority_tokens']}")
    m, r = mission("evblkoff", 119_000_000, epoch=1)
    commit(r, "src/a.ts", "1")
    rec = gm.load(m)
    with env(CPP_TOPUP_EVENT="off"):
        gm.block_mission(rec, expect_epoch=rec["epoch"], expect_state=gm.RUNNING, reason=ASK)
    check("V-W3-EVENT-BLOCKED-CONTROL", gm.load(m)["state"] == gm.BLOCKED, gm.load(m)["state"])

    # V-W3-EVENT-AUTHORITY-SET: an Owner raise over a parked mission releases it at once (RESUME_ONLY), no grant
    m, r = mission("evauth", 119_000_000)
    hold(m)
    gm.set_authority(m, tokens="200M", reason="Owner raise (w3 test)")
    rec = gm.load(m)
    check("V-W3-EVENT-AUTHORITY-SET", not rec.get("owner_hold") and rec["authority_tokens"] == 200_000_000
          and decisions(m, "RESUME") == ["RESUME1"] and not mt.load_policy(m).get("grants"),
          f"hold={bool(rec.get('owner_hold'))} resumes={decisions(m, 'RESUME')}")
    # V-W3-BUDGET-EVENT: a re-budget is judged once its policy is whole (never mid-write), then releases the park
    m, r = mission("evbudget", 119_000_000)
    hold(m)
    pol = mt.budget(m, "200M", 3, "40M", reason="Owner re-budget (w3 test)")
    rec = gm.load(m)
    check("V-W3-BUDGET-EVENT", pol["policy_epoch"] == 1 and not rec.get("owner_hold")
          and [e.get("cause") for e in rows(m, "capital_event")] == ["budget"]
          and mt.load_policy(m)["resumes"][-1]["authority"] == 200_000_000,
          f"epoch={pol['policy_epoch']} events={[e.get('cause') for e in rows(m, 'capital_event')]}")


def _slow_progress(module, delays):
    """Wrap module.progress_receipts so thread i sleeps delays[i] inside the read (judged, not yet written)."""
    real = module.progress_receipts
    tl = threading.local()

    def slow(rec, pol):
        out = real(rec, pol)
        time.sleep(getattr(tl, "delay", 0))
        return out

    module.progress_receipts = slow
    return real, tl


def _race(module, mid, delays, decide_fn):
    real, tl = _slow_progress(module, delays)
    barrier = threading.Barrier(len(delays))
    results = [None] * len(delays)

    def run(i):
        tl.delay = delays[i]
        barrier.wait()
        try:
            results[i] = module.sweep_one(mid, decide_fn=decide_fn, sender=lambda t: "sent")
        except Exception as exc:  # noqa: BLE001 -- recorded as the thread's result
            results[i] = {"action": "error", "why": f"{type(exc).__name__}: {exc}"}

    ts = [threading.Thread(target=run, args=(i,)) for i in range(len(delays))]
    for t in ts:
        t.start()
    for t in ts:
        t.join(120)
    module.progress_receipts = real
    return results


def race_gates():
    # V-W3-RACE-CONCURRENT-EXACTLY-ONCE: 4 passes (poller, event, manual, recovery) judge one hold at once
    m, r = mission("race4", 119_000_000)
    commit(r, "src/a.ts", "1")
    hold(m)
    res = _race(mt, m, [0.4, 0.4, 0.4, 0.4], real_decide)
    acts = sorted(x["action"] for x in res)
    check("V-W3-RACE-CONCURRENT-EXACTLY-ONCE", acts.count("grant") == 1 and "error" not in acts
          and len(rows(m, "authority_auto_topup")) == 1 and gm.load(m)["authority_tokens"] == 160_000_000
          and decisions(m, "TOPUP") == ["TOPUP1"], f"{acts} auth={gm.load(m)['authority_tokens']}")

    # revert control: 2455e994 (W2, no lock, no seq check) on the same race writes two grants
    old = _module_at("2455e994")
    m, r = mission("raceold", 119_000_000)
    commit(r, "src/a.ts", "1")
    hold(m)
    with env(CPP_TOPUP_EVENT="off"):
        res = _race(old, m, [0.4, 0.4], real_decide)
    # Pre-W3, uncoordinated passes break exactly-once in one of two ways depending on timing (both measured on this
    # host): two grant rows for one hold, or the second pass dies mid-effect on the record the first one moved.
    # The W3 gate above shows neither, so the control accepts either and names which one happened.
    n_old = len(rows(m, "authority_auto_topup"))
    errs = [x["why"][:80] for x in res if x["action"] == "error"]
    check("V-W3-RACE-REVERT-CONTROL-2455e994", n_old == 2 or bool(errs),
          f"pre-W3: grant rows={n_old} crashed passes={errs} actions={[x['action'] for x in res]}")

    # mutant: the lock removed -- the seq check alone refuses the stale second judgement
    import contextlib
    m, r = mission("racemut", 119_000_000)
    commit(r, "src/a.ts", "1")
    hold(m)
    real_lock = mt._topup_lock
    mt._topup_lock = lambda mid, t: contextlib.nullcontext()
    try:
        res = _race(mt, m, [0.2, 1.5], real_decide)
    finally:
        mt._topup_lock = real_lock
    check("V-W3-RACE-LOCK-MUTANT-SEQ-HOLDS", len(rows(m, "authority_auto_topup")) == 1
          and any(x.get("cas_moved") for x in res) and rows(m, "authority_topup_cas_moved"),
          f"{[(x['action'], x.get('cas_moved')) for x in res]}")

    # V-W3-CAS-MOVED: the record moves while progress is read -> no entry written; the next pass grants
    m, r = mission("racecas", 119_000_000)
    commit(r, "src/a.ts", "1")
    hold(m)
    real = mt.progress_receipts

    def moving(rec, pol):
        cur = gm.load(rec["mission_id"])
        gm.transition(rec["mission_id"], expect_epoch=cur["epoch"], expect_state=cur["state"], event="test_move")
        return real(rec, pol)

    mt.progress_receipts = moving
    try:
        res = mt.sweep_one(m, decide_fn=real_decide)
    finally:
        mt.progress_receipts = real
    check("V-W3-CAS-MOVED", res["action"] == "none" and res.get("cas_moved") and not mt.load_policy(m).get("grants")
          and gm.load(m)["authority_tokens"] == 120_000_000, res.get("why"))
    res = mt.sweep_one(m, decide_fn=real_decide)
    check("V-W3-CAS-MOVED-CONTROL", res["action"] == "grant" and gm.load(m)["authority_tokens"] == 160_000_000,
          res.get("why"))

    # V-W3-RACE-EVENT-BUSY: an event that meets a pass in flight defers (recorded), the holder judges it
    m, r = mission("racebusy", 119_000_000)
    commit(r, "src/a.ts", "1")
    hold(m)
    real_wait = mt.EVENT_LOCK_S
    mt.EVENT_LOCK_S = 0.3
    try:
        with mt._topup_lock(m, 1):
            out = []
            t = threading.Thread(target=lambda: out.append(mt.on_capital_event(m, "cost_hold")))
            t.start()
            t.join(30)
    finally:
        mt.EVENT_LOCK_S = real_wait
    res = mt.sweep_one(m, decide_fn=real_decide)
    check("V-W3-RACE-EVENT-BUSY", out and out[0].get("busy") and rows(m, "capital_event_deferred")
          and res["action"] == "grant" and len(rows(m, "authority_auto_topup")) == 1,
          f"event={out and out[0].get('why')} then poller={res['action']}")

    # V-W3-RACE-WORKER-BLOCK-VS-POLLER: the worker blocks itself while a poller loops -> one grant, RUNNING
    m, r = mission("raceblk", 119_000_000, epoch=1)
    commit(r, "src/a.ts", "1")
    stop = threading.Event()
    polled = []

    def poller():
        while not stop.is_set():
            polled.append(mt.sweep_one(m, decide_fn=real_decide)["action"])
            time.sleep(0.01)

    t = threading.Thread(target=poller)
    t.start()
    time.sleep(0.1)
    rec = gm.load(m)
    gm.block_mission(rec, expect_epoch=rec["epoch"], expect_state=gm.RUNNING, reason=ASK)
    time.sleep(0.5)
    stop.set()
    t.join(60)
    rec = gm.load(m)
    # Two legal orders (both measured: Windows saw the first, GEX44 the second). Block first: one boundary grant
    # (TOPUP1). Poller first: one predictive grant, then the worker's stale ask is answered by RESUME1. Either way
    # ONE grant, RUNNING, and the Owner is not told the mission is parked.
    boundary_first = decisions(m, "TOPUP") == ["TOPUP1"] and decisions(m, "RESUME") == []
    predictive_first = decisions(m, "TOPUP") == [] and decisions(m, "RESUME") == ["RESUME1"]
    check("V-W3-RACE-WORKER-BLOCK-VS-POLLER", len(rows(m, "authority_auto_topup")) == 1 and rec["state"] == gm.RUNNING
          and rec["authority_tokens"] == 160_000_000 and (boundary_first or predictive_first)
          and not rows(m, "authority_auto_topup_refused"),
          f"grants={len(rows(m, 'authority_auto_topup'))} state={rec['state']} polls={len(polled)} "
          f"order={'boundary' if boundary_first else 'predictive' if predictive_first else 'NEITHER'}")

    # V-W3-PREDICTIVE-THEN-ASK (the GEX44 order, made deterministic): a predictive grant, then the worker -- never
    # told of it -- asks for authority. The ask is stale: RESUME_ONLY, RUNNING, no refusal, no Owner notice.
    m, r = mission("predask", 119_000_000, epoch=1)
    commit(r, "src/a.ts", "1")
    g = mt.sweep_one(m, decide_fn=real_decide, predictive=True)
    rec = gm.load(m)
    gm.block_mission(rec, expect_epoch=rec["epoch"], expect_state=gm.RUNNING, reason=ASK)
    rec = gm.load(m)
    check("V-W3-PREDICTIVE-THEN-ASK", g["action"] == "grant" and rec["state"] == gm.RUNNING
          and decisions(m, "RESUME") == ["RESUME1"] and not rows(m, "authority_auto_topup_refused")
          and len(mt.load_policy(m)["grants"]) == 1,
          f"grant={g['action']} state={rec['state']} resume={decisions(m, 'RESUME')} "
          f"refused={len(rows(m, 'authority_auto_topup_refused'))}")
    # control: the same ask with room left and NO predictive raise in this epoch stays the Owner's (W1 rule)
    m, r = mission("predaskctl", 70_000_000, epoch=1)
    commit(r, "src/a.ts", "1")
    rec = gm.load(m)
    gm.block_mission(rec, expect_epoch=rec["epoch"], expect_state=gm.RUNNING, reason=ASK)
    rec = gm.load(m)
    check("V-W3-PREDICTIVE-THEN-ASK-CONTROL", rec["state"] == gm.BLOCKED and decisions(m, "RESUME") == []
          and rows(m, "authority_auto_topup_refused"), f"state={rec['state']}")

    # V-W3-MANUAL-VS-AUTO: a grant written, its effect crashed; the Owner then raises by hand above it. The
    # Owner's raise stands (never lowered, never +step on top), the grant completes once, TOPUP1 once.
    m, r = mission("racemanual", 119_000_000)
    commit(r, "src/a.ts", "1")
    hold(m)
    real_sa = gm.set_authority

    def crash(*a, **k):
        raise RuntimeError("w3 injected crash after the grant was written")

    gm.set_authority = crash
    try:
        try:
            mt.sweep_one(m, decide_fn=real_decide)
        except RuntimeError:
            pass
    finally:
        gm.set_authority = real_sa
    half = mt.load_policy(m)["grants"]
    gm.set_authority(m, tokens="170M", reason="Owner raise by hand (w3 test)")
    rec = gm.load(m)
    check("V-W3-MANUAL-VS-AUTO", len(half) == 1 and rec["authority_tokens"] == 170_000_000 and not rec.get("owner_hold")
          and decisions(m, "TOPUP") == ["TOPUP1"] and len(mt.load_policy(m)["grants"]) == 1
          and rows(m, "capital_event", cause="authority_set", action="resume"),
          f"auth={rec['authority_tokens']} grants={len(mt.load_policy(m)['grants'])} topup={decisions(m, 'TOPUP')}")

    # V-W3-CRASH-KILLED-MID-GRANT: a real process dies (os._exit) after writing the grant, before its effect.
    # The kernel lock dies with it; the poller (recovery) completes that grant once.
    m, r = mission("racekill", 119_000_000)
    commit(r, "src/a.ts", "1")
    hold(m)
    child = Path(TMP) / "w3_child.py"
    child.write_text(
        "import json, os, sys\n"
        f"sys.path.insert(0, {str(TOOLS)!r})\n"
        "import gsd_mission as gm, mission_topup as mt, account_governor as ag, mission_spend as ms\n"
        f"ag.DEFAULT_STATE = {GOV_DIR!r}\n"
        "ag.check = lambda s, a: (0, 'ALLOW', 'test governor', {})\n"
        "spend = json.loads(os.environ['W3_SPEND'])\n"
        "ms.processed_tokens = lambda rec, *a, **k: spend.get(rec.get('mission_id'))\n"
        "gm.set_authority = lambda *a, **k: os._exit(9)\n"
        "mt.sweep_one(sys.argv[1], decide_fn=mt._decide_deferred)\n"
        "sys.exit(0)\n", encoding="utf-8")
    import json
    cp = subprocess.run([sys.executable, "-I", str(child), m], capture_output=True, text=True, timeout=120,
                        env={**os.environ, "W3_SPEND": json.dumps(SPEND)})
    written = mt.load_policy(m).get("grants") or []
    free = True
    try:
        with mt._topup_lock(m, 1):
            pass
    except gm.MissionError:
        free = False
    res = mt.sweep_one(m, decide_fn=real_decide)
    rec = gm.load(m)
    check("V-W3-CRASH-KILLED-MID-GRANT", cp.returncode == 9 and len(written) == 1 and free and res["action"] == "resume"
          and rec["authority_tokens"] == 160_000_000 and not rec.get("owner_hold")
          and decisions(m, "TOPUP") == ["TOPUP1"] and len(mt.load_policy(m)["grants"]) == 1,
          f"rc={cp.returncode} written={len(written)} lock_free={free} then={res['action']} "
          f"auth={rec['authority_tokens']} err={cp.stderr.strip()[-200:]}")


def review_gates():
    """Gates for the W3 review findings (vault/audits/mission-capital-W3-review.md)."""
    import work_class_profile as wcp
    wcp.main(["settle", "--class", "W3_BIG", "--unit", "u1", "--processed", "120000000", "--calls", "300",
              "--avg-ctx", "200000", "--max-ctx", "300000", "--attempts", "1", "--attempts-failed", "0",
              "--cause", "w3 review sample"])
    # MEDIUM-2: next lease 120M > headroom + step, so PRESSURE persists after a grant. A second commit must NOT buy a
    # second predictive step until the first step is spent.
    m, r = mission("oneahead", 100_000_000)
    gm.transition(m, expect_epoch=0, expect_state=gm.RUNNING, event="test_class", work_class="W3_BIG")
    commit(r, "src/a.ts", "1")
    first = mt.sweep_one(m, decide_fn=real_decide, predictive=True)
    commit(r, "src/b.ts", "2")
    second = mt.sweep_one(m, decide_fn=real_decide, predictive=True)
    check("V-W3-PREDICTIVE-ONE-AHEAD", first["action"] == "grant" and second["action"] == "none"
          and "one step ahead" in second["why"] and len(mt.load_policy(m)["grants"]) == 1
          and gm.load(m)["authority_tokens"] == 160_000_000, f"{first['action']} then {second.get('why')}")
    SPEND[m] = 140_000_000   # the first step (40M) is spent
    commit(r, "src/c.ts", "3")
    third = mt.sweep_one(m, decide_fn=real_decide, predictive=True)
    check("V-W3-PREDICTIVE-ONE-AHEAD-SPENT-CONTROL", third["action"] == "grant"
          and gm.load(m)["authority_tokens"] == 200_000_000, f"{third['action']} {third.get('why')}")

    # LOW-3: a predictive grant dies before its raise, then the mission parks: the park completes THAT grant (no n+1)
    m, r = mission("predcrashpark", 100_000_000)
    commit(r, "src/a.ts", "1")
    real_sa = gm.set_authority

    def crash(*a, **k):
        raise RuntimeError("w3 injected crash after the predictive grant was written")

    gm.set_authority = crash
    try:
        try:
            mt.sweep_one(m, decide_fn=real_decide, predictive=True)
        except RuntimeError:
            pass
    finally:
        gm.set_authority = real_sa
    SPEND[m] = 119_000_000
    hold(m)
    p1 = mt.sweep_one(m, decide_fn=real_decide)
    p2 = mt.sweep_one(m, decide_fn=real_decide)
    rec, pol = gm.load(m), mt.load_policy(m)
    check("V-W3-PREDICTIVE-CRASH-THEN-PARK", p1["action"] == "resume" and p2["action"] == "release"
          and len(pol["grants"]) == 1 and rec["authority_tokens"] == 160_000_000 and not rec.get("owner_hold")
          and decisions(m, "TOPUP") == [] and decisions(m, "RESUME") == ["RESUME1"],
          f"{p1['action']} -> {p2['action']} grants={len(pol['grants'])} auth={rec['authority_tokens']}")

    # pre_launch is predictive-only: it never runs the boundary judge on a parked record. Control: its own event does.
    m, r = mission("prelaunchblk", 119_000_000, epoch=1)
    commit(r, "src/a.ts", "1")
    rec = gm.load(m)
    with env(CPP_TOPUP_EVENT="off"):
        gm.block_mission(rec, expect_epoch=rec["epoch"], expect_state=gm.RUNNING, reason=ASK)
    pl = mt.on_capital_event(m, "pre_launch")
    st = gm.load(m)["state"]
    ctl = mt.on_capital_event(m, "blocked")
    check("V-W3-PRE-LAUNCH-PREDICTIVE-ONLY", pl["action"] == "none" and st == gm.BLOCKED
          and ctl["action"] == "grant" and gm.load(m)["state"] == gm.RUNNING,
          f"pre_launch={pl['action']} state={st}; blocked event={ctl['action']}")

    # LOW-2: an Owner raise (below the grant's `to`) lands between the grant's write and its raise. The Owner's
    # figure stands, the grant is voided, and the stale park is released at that figure (RESUME_ONLY), no top-up.
    m, r = mission("raisecas", 119_000_000)
    commit(r, "src/a.ts", "1")
    hold(m)
    fired = []

    def owner_first(mid, *a, **k):
        if not fired:
            fired.append(1)
            real_sa(mid, tokens="150M", reason="Owner raise mid-grant (w3 test)")
        return real_sa(mid, *a, **k)

    gm.set_authority = owner_first
    try:
        try:
            p1 = mt.sweep_one(m, decide_fn=real_decide)["action"]
        except gm.CasConflict:
            p1 = "CasConflict"
    finally:
        gm.set_authority = real_sa
    p2 = mt.sweep_one(m, decide_fn=real_decide)
    p3 = mt.sweep_one(m, decide_fn=real_decide)
    rec, pol = gm.load(m), mt.load_policy(m)
    check("V-W3-OWNER-RAISE-MID-GRANT", p1 == "CasConflict" and rec["authority_tokens"] == 150_000_000
          and pol["grants"][-1].get("voided") and not rec.get("owner_hold") and decisions(m, "TOPUP") == []
          and rows(m, "authority_topup_voided"),
          f"p1={p1} p2={p2['action']}:{p2.get('result')} p3={p3['action']} auth={rec['authority_tokens']} "
          f"hold={bool(rec.get('owner_hold'))} topup={decisions(m, 'TOPUP')}")


def main_gates():
    """Review MEDIUM-1: the poller runs `mission_topup.py sweep` as __main__. A grant's own set_authority raises
    the authority_set event; if `import mission_topup` loads a second module copy, its reentrancy depth is 0 and
    the event waits EVENT_LOCK_S on the lock its own pass holds, then writes a false capital_event_deferred row.
    Driven for real: a child process runs the file as __main__ (runpy), governor and spend injected first."""
    import json
    m, r = mission("mainsweep", 119_000_000)
    commit(r, "src/a.ts", "1")
    hold(m)
    child = Path(TMP) / "w3_main_child.py"
    child.write_text(
        "import json, os, runpy, sys\n"
        f"sys.path.insert(0, {str(TOOLS)!r})\n"
        "import account_governor as ag, mission_spend as ms\n"
        f"ag.DEFAULT_STATE = {GOV_DIR!r}\n"
        "ag.check = lambda s, a: (0, 'ALLOW', 'test governor', {})\n"
        "spend = json.loads(os.environ['W3_SPEND'])\n"
        "ms.processed_tokens = lambda rec, *a, **k: spend.get(rec.get('mission_id'))\n"
        f"sys.argv = [{str(TOOLS / 'mission_topup.py')!r}, 'sweep']\n"
        f"runpy.run_path({str(TOOLS / 'mission_topup.py')!r}, run_name='__main__')\n", encoding="utf-8")
    t0 = time.time()
    cp = subprocess.run([sys.executable, "-I", str(child)], capture_output=True, text=True, timeout=180,
                        env={**os.environ, "W3_SPEND": json.dumps(SPEND)})
    wall = time.time() - t0
    rec = gm.load(m)
    check("V-W3-MAIN-NO-SELF-DEFER", cp.returncode == 0 and rec["authority_tokens"] == 160_000_000
          and not rows(m, "capital_event_deferred") and wall < mt.EVENT_LOCK_S,
          f"rc={cp.returncode} wall={wall:.1f}s auth={rec['authority_tokens']} "
          f"deferred={len(rows(m, 'capital_event_deferred'))} err={cp.stderr.strip()[-200:]}")


def _module_at(rev, tag=None):
    import importlib.util
    src = subprocess.run([GIT, "-C", str(TOOLS), "show", f"{rev}:tools/mission_topup.py"],
                         capture_output=True, text=True, encoding="utf-8", check=True).stdout
    p = Path(TMP) / "oldmod" / f"mission_topup_{tag or rev}.py"
    p.parent.mkdir(exist_ok=True)
    p.write_text(src, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(f"mission_topup_{tag or rev}", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    for fn in (main_gates, predictive_gates, event_gates, race_gates, review_gates):   # main first: its sweep sees one policy
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 -- a crashed group is a failure, never a silent pass
            import traceback
            traceback.print_exc()
            check(f"V-W3-GROUP-{fn.__name__}", False, f"{type(exc).__name__}: {exc}")
    print(f"W3_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
