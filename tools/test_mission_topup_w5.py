#!/usr/bin/env python
"""V-W5-* gates: mission-capital W5 (spec vault/specs/mission-capital-state.md "W5").

WAITING_PROVIDER separation (a provider hold at a capital boundary grants, resumes and pings nothing, and the first
pass after its reset acts), the ledger metrics and the historical census. Hermetic like test_mission_topup_w3.py:
state in a temp dir, spend and governor injected, the provider hold injected at gsd_mission.provider_hold (the one
seam provider_of reads), progress judged on real throw-away git repos. Every refusal pole has a control.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="mission-topup-w5-")
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
           "CPP_CAPITAL_STATE", "CPP_PROGRESS_RECEIPTS", "CPP_TOPUP_PROVIDER", "CPP_AUTHORITY_RECEIPT"):
    os.environ.pop(_k, None)
TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import gsd_mission as gm  # noqa: E402
import mission_topup as mt  # noqa: E402
import account_governor as _ag  # noqa: E402
import mission_spend as _ms  # noqa: E402

_ag.DEFAULT_STATE = os.path.join(TMP, "governor")
_ag.check = lambda state_dir, action: (0, "ALLOW", "test governor", {})
SPEND: dict = {}
_ms.processed_tokens = lambda rec, *a, **k: SPEND.get(rec.get("mission_id"))
PROVIDER: dict = {}
gm.provider_hold = lambda rec, now: PROVIDER.get(rec.get("mission_id"))   # the seam provider_of reads

passes = fails = 0
GIT = gm.resolve_exe("git") or "git"
TRIP = "cost breaker (mission authority): processed 119,000,000 >= authority 120,000,000 minus closeout reserve"
SENT: list = []


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


class env:
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


def git(repo, *args):
    subprocess.run([GIT, "-C", str(repo), *args], check=True, capture_output=True)


def commit(repo, rel, text):
    p = Path(repo) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", f"edit {rel}")


def mission(name, spend):
    """A live mission on its own git repo, authority 120M, 3 x 40M top-ups, `spend` processed."""
    repo = Path(TMP) / name
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "t@t")
    git(repo, "config", "user.name", "t")
    commit(repo, "README.md", "x")
    mid = f"m-{name}"
    SPEND[mid] = 1_000_000
    gm.create(str(repo), "/gsd-autonomous", mission_id=mid)
    mt.budget(mid, "120M", 3, "40M", reason="w5 test")
    SPEND[mid] = spend
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="test_running", state=gm.RUNNING, epoch=0)
    return mid, str(repo)


def parked(name, spend=119_000_000):
    """A mission parked on its authority trip, with progress since the budget (a poller pass would grant)."""
    m, r = mission(name, spend)
    commit(r, "src/a.ts", "1")
    with env(CPP_TOPUP_EVENT="off"):
        gm.set_owner_hold(m, TRIP, kind="cost")
    return m, r


def rows(mid, event):
    return [e for e in gm.lr.ledger_events(mid) if e.get("event") == event]


def real_decide(mid, text, decision_id=None):
    return gm.deliver_decision(mid, text, decision_id=decision_id, wake=False)


def sweep(mid, now=None, **kw):
    return mt.sweep_one(mid, now=now, decide_fn=real_decide, sender=lambda t: SENT.append(t) or "sent", **kw)


def provider_gates():
    t0 = time.time()
    until = t0 + 600
    m, _ = parked("wait")
    PROVIDER[m] = {"class": "quota", "until": until, "reason": "You've hit your limit - resets 11pm"}
    sent0 = len(SENT)
    r1 = sweep(m, now=t0)
    pol = mt.load_policy(m)
    check("V-W5-WAITING-PROVIDER-NO-GRANT",
          r1["action"] == "none" and r1.get("waiting_provider") and r1.get("capital_state") == "WAITING_PROVIDER"
          and not pol.get("grants") and gm.load(m).get("owner_hold") and len(SENT) == sent0
          and not rows(m, "authority_auto_topup_refused") and r1.get("wake_at") == until,
          f"{r1['action']} {r1.get('capital_state')} why={str(r1.get('why'))[:80]}")
    r2 = sweep(m, now=t0 + 60)
    check("V-W5-ROW-ON-CHANGE", r2.get("waiting_provider") and len(rows(m, "capital_waiting_provider")) == 1,
          f"rows={len(rows(m, 'capital_waiting_provider'))}")
    r3 = sweep(m, now=until + 5)     # the provider's reset has passed: provider_of reads no live hold
    rec = gm.load(m)
    cl = rows(m, "capital_provider_cleared")
    check("V-W5-WAKE-ON-RESET", r3["action"] == "grant" and rec["authority_tokens"] == 160_000_000
          and not rec.get("owner_hold") and len(cl) == 1 and cl[0]["waited_s"] == round(until + 5 - t0)
          and cl[0]["late_s"] == 5 and "waiting_provider" not in mt.load_policy(m),
          f"{r3['action']} auth={rec['authority_tokens']} cleared={cl[:1]}")
    PROVIDER.pop(m, None)

    c, _ = parked("nowait")
    rc = sweep(c, now=t0)
    check("V-W5-CONTROL-NO-PROVIDER", rc["action"] == "grant" and gm.load(c)["authority_tokens"] == 160_000_000
          and not rows(c, "capital_waiting_provider"), f"{rc['action']}")

    k, _ = parked("killsw")
    PROVIDER[k] = {"class": "quota", "until": until, "reason": "limit"}
    with env(CPP_TOPUP_PROVIDER="off"):
        rk = sweep(k, now=t0)
    check("V-W5-KILL-SWITCH", rk["action"] == "grant" and not rows(k, "capital_waiting_provider"), rk["action"])
    PROVIDER.pop(k, None)

    q, _ = parked("quar")
    PROVIDER[q] = {"class": "auth", "until": None, "reason": "QUARANTINE (credentials)", "quarantine": True}
    rq = sweep(q, now=t0)
    check("V-W5-QUARANTINE", rq.get("waiting_provider") and rq.get("wake_at") is None and "re-login" in rq["why"]
          and not mt.load_policy(q).get("grants") and len(SENT) == sent0, rq.get("why"))
    PROVIDER.pop(q, None)

    # a grant already WRITTEN (its effect died) waits too, and is resumed exactly once after the reset
    w, _ = parked("written")
    real_complete = mt._complete

    def dies(*a, **k):
        raise RuntimeError("killed between the grant row and its effect")
    mt._complete = dies
    try:
        sweep(w, now=t0)
    except RuntimeError:
        pass
    finally:
        mt._complete = real_complete
    g_before = len(mt.load_policy(w)["grants"])
    PROVIDER[w] = {"class": "quota", "until": until, "reason": "limit"}
    rw1 = sweep(w, now=t0 + 1)
    PROVIDER.pop(w, None)
    rw2 = sweep(w, now=until + 1)
    rec = gm.load(w)
    check("V-W5-WRITTEN-GRANT-WAITS", g_before == 1 and rw1["action"] == "none" and rw1.get("waiting_provider")
          and rw2["action"] == "resume" and len(mt.load_policy(w)["grants"]) == 1
          and rec["authority_tokens"] == 160_000_000 and not rec.get("owner_hold"),
          f"before={g_before} {rw1['action']} -> {rw2['action']} auth={rec['authority_tokens']}")

    # review L1: top-ups exhausted at the renew zone is the Owner's boundary even under a quarantine (no reset time)
    x, _ = parked("exhausted")
    quar = {"class": "auth", "until": None, "reason": "QUARANTINE", "quarantine": True}
    rec_x, pol_x = gm.load(x), mt.load_policy(x)
    spent_pol = dict(pol_x, grants=[{"n": i, "to": 0, "hold_set_at": i} for i in (1, 2, 3)])
    cs_x = mt.capital_state(rec_x, spent_pol, 119_000_000, t0, provider=quar)
    cs_xc = mt.capital_state(rec_x, pol_x, 119_000_000, t0, provider=quar)
    check("V-W5-OWNER-BOUNDARY-NOT-HIDDEN", cs_x["state"] == "EXHAUSTED_OWNER" and cs_x.get("dim") == "authority"
          and cs_xc["state"] == "WAITING_PROVIDER", f"{cs_x['state']} / control {cs_xc['state']}")

    # hours exhausted wins over a provider wait: that boundary is the Owner's either way
    h, _ = parked("hours")
    PROVIDER[h] = {"class": "quota", "until": until, "reason": "limit"}
    late = float(gm.load(h)["created_at"]) + 3600 * float(gm.load(h).get("max_hours") or gm.lr.DEFAULT_MAX_HOURS) + 1
    cs = mt.capital_state(gm.load(h), mt.load_policy(h), 119_000_000, late,
                          provider=mt.provider_of(gm.load(h), late) or PROVIDER[h])
    check("V-W5-HOURS-WINS", cs["state"] == "EXHAUSTED_OWNER" and cs.get("dim") == "hours", cs["state"])
    PROVIDER.pop(h, None)

    # predictive PRESSURE waits; control without the provider stays PRESSURE
    p, _ = mission("pressure", 100_000_000)
    rec, pol = gm.load(p), mt.load_policy(p)
    cs_wait = mt.capital_state(rec, pol, 100_000_000, t0, provider={"class": "quota", "until": until, "reason": "x"})
    cs_ctrl = mt.capital_state(rec, pol, 100_000_000, t0)
    check("V-W5-PREDICTIVE-WAITS", cs_wait["state"] == "WAITING_PROVIDER" and cs_ctrl["state"] == "PRESSURE",
          f"{cs_wait['state']} / control {cs_ctrl['state']}")
    # a provider hold on a HEALTHY mission is gsd_mission's business, never a capital state
    hm, _ = mission("healthy", 10_000_000)
    cs_h = mt.capital_state(gm.load(hm), mt.load_policy(hm), 10_000_000, t0,
                            provider={"class": "quota", "until": until, "reason": "x"})
    check("V-W5-HEALTHY-UNTOUCHED", cs_h["state"] == "HEALTHY", cs_h["state"])
    return m


def ev(t, event, **kw):
    return {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(t)), "event": event, **kw}


def metrics_gates(waited_mid):
    base = 1_790_000_000
    events = [
        ev(base, "owner_hold_set", reason="owner hold: cost breaker (mission authority): processed ..."),
        ev(base + 300, "authority_auto_topup", predictive=False),
        ev(base + 310, "owner_hold_released"),
        ev(base + 1000, "mission_blocked", reason="OWNER_BOUNDARY (AUTHORITY): raise authority"),
        ev(base + 1100, "authority_auto_topup_refused", why="ceiling reached (255,000,000); beyond it is the Owner's"),
        ev(base + 1200, "authority_set", reason="authority: owner", receipt={"provenance": "portable_receipt"}),
        ev(base + 1300, "mission_unblocked"),
        ev(base + 2000, "authority_auto_topup", predictive=True),
        ev(base + 3000, "owner_hold_set", reason="owner hold: cost breaker (mission authority): again"),
        ev(base + 3100, "authority_auto_topup_refused", why="progress unmeasured: root unreadable"),
    ]
    mx = mt.capital_metrics("m-synthetic", now=base + 4000, events=events)
    check("V-W5-METRICS", mx["parks"] == 3 and mx["open_parks"] == 1 and mx["authorized_capital_stall_s"] == 310
          and mx["owner_boundary_s"] == 300 and mx["open_s"] == 1000 and mx["renewal_latency_s"]["p50"] == 300
          and mx["owner_interrupts"]["legitimate"] == 1 and mx["owner_interrupts"]["review"] == [
              "progress unmeasured: root unreadable"] and mx["grants"] == 2 and mx["predictive_rate"] == 0.5,
          json.dumps({k: mx[k] for k in ("parks", "authorized_capital_stall_s", "owner_boundary_s", "open_s")}))
    # control: a park ended by the top-up's OWN authority_set (provenance topup_policy) is auto, not the Owner's
    ctrl = mt.capital_metrics("m-synthetic", now=base + 500, events=[
        ev(base, "owner_hold_set", reason="owner hold: cost breaker (mission authority): x"),
        ev(base + 100, "authority_set", reason="authority: auto top-up 1", receipt={"provenance": "topup_policy"}),
        ev(base + 101, "authority_auto_topup", predictive=False),
        ev(base + 102, "owner_hold_released")])
    check("V-W5-METRICS-CONTROL-TOPUP-SET", ctrl["authorized_capital_stall_s"] == 102 and ctrl["owner_boundary_s"] == 0,
          json.dumps({k: ctrl[k] for k in ("authorized_capital_stall_s", "owner_boundary_s")}))
    # review L2: a 600 s provider wait inside an auto-renewed 700 s park is the provider's, not the runtime's stall
    pw = mt.capital_metrics("m-synthetic", now=base + 1000, events=[
        ev(base, "owner_hold_set", reason="owner hold: cost breaker (mission authority): x"),
        ev(base + 650, "capital_provider_cleared", waited_s=600),
        ev(base + 690, "authority_auto_topup", predictive=False),
        ev(base + 700, "owner_hold_released")])
    check("V-W5-METRICS-PROVIDER-SPLIT", pw["authorized_capital_stall_s"] == 100
          and pw["provider_wait_in_parks_s"] == 600, json.dumps({k: pw[k] for k in (
              "authorized_capital_stall_s", "provider_wait_in_parks_s")}))
    # regression, the GEX44 m-76e04d86896d shape: a BLOCKED ask answered by the Owner's hand raise (worded "Owner-approved
    # top-up 1 of 2"), the turn continued with NO mission_unblocked row, then a second trip later
    inc = mt.capital_metrics("m-synthetic", now=base + 50_000, events=[
        ev(base, "mission_blocked", state="BLOCKED", reason="OWNER_BOUNDARY (AUTHORITY): raise authority: ..."),
        ev(base + 29_583, "authority_set", state="BLOCKED",
           reason="authority: {'authority_tokens': 215000000} (Owner-approved top-up 1 of 2 (40M) from '+90 M ...')"),
        ev(base + 29_631, "turn_continued", state="LAUNCHING", reason="owner decision D2"),
        ev(base + 32_668, "owner_hold_set", state="RUNNING",
           reason="owner hold: cost breaker (mission authority): processed 214,056,797 >= authority 215,000,000"),
        ev(base + 41_015, "authority_auto_topup", predictive=False),
        ev(base + 41_016, "owner_hold_released", state="RUNNING")])
    lp = inc["last_parks"]
    check("V-W5-METRICS-INCIDENT-SHAPE", inc["parks"] == 2 and lp[0]["by"] == "owner" and lp[0]["s"] == 29_631
          and lp[1]["by"] == "auto" and lp[1]["s"] == 41_016 - 32_668 and inc["owner_boundary_s"] == 29_631,
          json.dumps(lp))
    real = mt.capital_metrics(waited_mid)
    check("V-W5-METRICS-REAL", real["parks"] >= 1 and real["provider_waits"]["n"] == 1 and real["grants"] == 1
          and real["open_parks"] == 0, json.dumps(real)[:200])
    cen = mt.census()
    ids = {t["mission"] for t in cen["top_stalls"]}
    check("V-W5-CENSUS", cen["with_capital_parks"] >= 5 and waited_mid in ids and
          cen["totals"]["grants"] >= 4 and cen["missions"] >= cen["with_capital_parks"],
          json.dumps({k: cen[k] for k in ("missions", "with_capital_parks")}) + " " + json.dumps(cen["totals"]))
    out = subprocess.run([sys.executable, str(TOOLS / "mission_topup.py"), "status", "--mission", waited_mid],
                         capture_output=True, text=True, env=os.environ.copy())
    try:
        js = json.loads(out.stdout)
    except ValueError:
        js = {}
    check("V-W5-STATUS-CLI", out.returncode == 0 and {"policy", "capital", "metrics"} <= set(js)
          and js["metrics"]["provider_waits"]["n"] == 1, (out.stderr or out.stdout)[:200])


if __name__ == "__main__":
    t0 = time.time()
    waited = None
    for group in (provider_gates, metrics_gates):
        try:
            waited = group(waited) if group is metrics_gates else group()
        except Exception as exc:  # noqa: BLE001 -- a crashed group is a failed gate, named
            import traceback
            traceback.print_exc()
            check(f"V-W5-GROUP-{group.__name__}", False, f"{type(exc).__name__}: {exc}")
    print(f"W5_PASS={passes}/{passes + fails} secs={time.time() - t0:.1f}")
    sys.exit(0 if fails == 0 else 1)
