#!/usr/bin/env python
"""V-TOPUP-* gates for tools/mission_topup.py (spec vault/specs/mission-auto-topup.md).

Hermetic: state goes to a temp dir before import; progress is judged on a real throw-away git repo; the worker
wake and the notification are injected. Every refusal has a paired control that grants.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="mission-topup-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_RESOURCE_ADMISSION"] = "off"
os.environ["CPP_MISSION_ACCOUNT_ADMISSION"] = "off"  # account quota: covered by test_mission_account_admission
os.environ.pop("CPP_MISSION_AUTO_TOPUP", None)
# These gates pin the POLLER (sweep_one called by hand after each write). With the W3 event path on, the write itself
# renews in-process and the poller finds nothing left to judge; W3 behaviour is gated in test_mission_topup_w3.py.
os.environ["CPP_TOPUP_EVENT"] = "off"
os.environ["CPP_TOPUP_PREDICTIVE"] = "off"
os.environ.pop("TELEGRAM_BOT_TOKEN", None)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_mission as gm  # noqa: E402
import mission_topup as mt  # noqa: E402
import account_governor as _ag  # noqa: E402

# Hermetic governor (mission-capital W0): sweep_one asks account_governor.check(DEFAULT_STATE) -- the REAL
# ~/.claude/state -- so the live weekly figure (88% on 2026-11-23) turned 9 gates red. The verdict is injected;
# V-TOPUP-GOVERNOR-REFUSE drives the refusal pole.
GOV = {"code": 0, "verdict": "ALLOW", "why": "test governor", "calls": 0}
_ag.DEFAULT_STATE = os.path.join(TMP, "governor")


def _fake_gov_check(state_dir, action):
    GOV["calls"] += 1
    assert state_dir == _ag.DEFAULT_STATE and action == "topup", (state_dir, action)
    return GOV["code"], GOV["verdict"], GOV["why"], {}


_ag.check = _fake_gov_check

# Hermetic spend (mission-capital W1): capital_state reads mission_spend.processed_tokens, which finds no
# transcripts here and answers None (UNKNOWN: never grants). Injected like GOV: SPEND[mid] when set (None drives the
# UNKNOWN pole), else the spend measured at the mission's last trip() (the trip line authority - closeout reserve at
# that moment: what a mission-authority trip means), else that line for the current authority. A grant raises the
# authority, not the spend, so the release that follows sees real headroom, as live.
import mission_spend as _ms  # noqa: E402
SPEND: dict = {}
AT_TRIP: dict = {}


def _trip_line(rec):
    return max(0, int(rec.get("authority_tokens") or 0) - _ms.closeout_reserve(rec))


def _fake_processed(rec, *a, **k):
    mid = rec.get("mission_id")
    if mid in SPEND:
        return SPEND[mid]
    return AT_TRIP.get(mid, _trip_line(rec))


_ms.processed_tokens = _fake_processed

passes = fails = 0
NOW = 1_800_000_000.0
TRIP = "cost breaker (mission authority): processed 119,000,000 >= authority 120,000,000 minus closeout reserve"


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


GIT = gm.resolve_exe("git") or "git"


def git(repo, *args):
    subprocess.run([GIT, "-C", repo, *args], check=True, capture_output=True)


def new_repo(name):
    repo = Path(TMP) / name
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "t@t")
    git(repo, "config", "user.name", "t")
    commit(repo, "README.md", "x")
    return str(repo)


def commit(repo, rel, text):
    p = Path(repo) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", f"edit {rel}")


woken = []


def decide(mid, text, decision_id=None):
    woken.append((mid, decision_id, text))
    return {"woke": True}


sent = []


def sender(text):
    sent.append(text)
    return "sent"


def mission(name, hold_reason=TRIP, kind="cost"):
    repo = new_repo(name)
    mid = f"m-{name}"
    gm.create(repo, "/gsd-autonomous", mission_id=mid, now=NOW)
    mt.budget(mid, "120M", 3, "40M", reason="test", now=NOW)
    return mid, repo


def trip(mid, reason=TRIP, kind="cost", at=None):
    AT_TRIP[mid] = _trip_line(gm.load(mid))   # the breaker trips when spend reaches the line
    gm.set_owner_hold(mid, reason, now=at or NOW + len(woken) + len(sent) + 10, kind=kind)


def _judge_pre_w0(rec, pol, prog):
    """Control for H6: mission_topup.judge exactly as it was before mission-capital W0 (verbatim copy)."""
    if rec is None or rec.get("state") in gm.TERMINAL:
        return {"action": "none", "why": "mission gone or terminal"}
    if not mt.is_authority_trip(rec):
        return {"action": "none", "why": "no mission-authority cost hold"}
    hold_at = (rec.get("owner_hold") or {}).get("set_at")
    grants = pol.get("grants") or []
    if grants and grants[-1].get("hold_set_at") == hold_at:
        return {"action": "resume", "why": "grant already written for this hold"}
    if len(grants) >= int(pol["max_topups"]):
        return {"action": "refuse", "why": f"top-ups exhausted ({len(grants)}/{pol['max_topups']})"}
    if pol.get("ceiling") and int(rec.get("authority_tokens") or 0) >= int(pol["ceiling"]):
        return {"action": "refuse", "why": f"ceiling reached ({int(pol['ceiling']):,}); beyond it is the Owner's"}
    if not prog.get("measured"):
        return {"action": "refuse", "why": f"progress unmeasured: {prog.get('why')}"}
    if not prog.get("progress"):
        return {"action": "refuse", "why": "no progress"}
    return {"action": "grant", "why": f"{prog['commits']} commit(s) touching {prog['paths']} path(s)"}


def main() -> int:
    # parse
    check("V-TOPUP-PARSE", mt.parse_tokens("40M") == 40_000_000 and mt.parse_tokens("1.5m") == 1_500_000
          and mt.parse_tokens("800K") == 800_000, "40M/1.5m/800K")
    try:
        mt.parse_tokens("lots")
        check("V-TOPUP-PARSE-REFUSE", False, "accepted 'lots'")
    except ValueError:
        check("V-TOPUP-PARSE-REFUSE", True)

    # governor refusal pole: progress + authority trip, but the account governor refuses -> no grant, no wake,
    # the hold stays; the same mission then grants once the governor allows (paired control)
    gm_mid, gm_repo = mission("govrefuse")
    commit(gm_repo, "src/g.ts", "g")
    trip(gm_mid)
    GOV.update(code=3, verdict="REFUSE", why="topup refused: weekly lower bound 88.0% >= 85% (test)")
    n_woken, calls0 = len(woken), GOV["calls"]
    r = mt.sweep_one(gm_mid, now=NOW + 50, decide_fn=decide, sender=sender)
    grec = gm.load(gm_mid)
    check("V-TOPUP-GOVERNOR-REFUSE", r["action"] == "refuse" and "88.0%" in r["why"] and grec.get("owner_hold")
          and grec.get("authority_tokens") == 120_000_000 and len(woken) == n_woken
          and not (mt.load_policy(gm_mid).get("grants")) and GOV["calls"] == calls0 + 1, r["why"])
    GOV.update(code=0, verdict="ALLOW", why="test governor")
    r = mt.sweep_one(gm_mid, now=NOW + 60, decide_fn=decide, sender=sender)
    check("V-TOPUP-GOVERNOR-ALLOW-CONTROL", r["action"] == "grant"
          and gm.load(gm_mid).get("authority_tokens") == 160_000_000, r["why"])
    sent.clear()

    # budget sets the Owner authority and the policy
    mid, repo = mission("grant")
    rec = gm.load(mid)
    pol = mt.load_policy(mid)
    check("V-TOPUP-BUDGET", rec.get("authority_tokens") == 120_000_000 and pol["max_topups"] == 3
          and pol["step"] == 40_000_000 and pol["last_head"], f"auth={rec.get('authority_tokens')}")

    # control: progress since base -> grant, release, wake
    commit(repo, "src/a.ts", "a")
    trip(mid)
    r = mt.sweep_one(mid, now=NOW + 100, decide_fn=decide, sender=sender)
    rec = gm.load(mid)
    check("V-TOPUP-GRANT", r["action"] == "grant" and rec.get("authority_tokens") == 160_000_000
          and not rec.get("owner_hold") and woken and woken[-1][1] == "TOPUP1", f"{r} auth={rec.get('authority_tokens')}")

    # refusal: tripped again with no commit since the grant -> held, notified once
    trip(mid)
    n_woken = len(woken)
    r = mt.sweep_one(mid, now=NOW + 200, decide_fn=decide, sender=sender)
    rec = gm.load(mid)
    check("V-TOPUP-NO-PROGRESS", r["action"] == "refuse" and rec.get("owner_hold")
          and rec.get("authority_tokens") == 160_000_000 and len(woken) == n_woken and len(sent) == 1, r["why"])
    mt.sweep_one(mid, now=NOW + 300, decide_fn=decide, sender=sender)
    check("V-TOPUP-NOTIFY-ONCE", len(sent) == 1, f"sent={len(sent)}")

    # refusal: bookkeeping-only commit is not progress
    commit(repo, ".planning/STATE.md", "moved")
    r = mt.sweep_one(mid, now=NOW + 400, decide_fn=decide, sender=sender)
    check("V-TOPUP-BOOKKEEPING", r["action"] == "refuse" and gm.load(mid).get("owner_hold"), r["why"])

    # control for the same hold: real work now -> grant 2
    commit(repo, "src/b.ts", "b")
    r = mt.sweep_one(mid, now=NOW + 500, decide_fn=decide, sender=sender)
    check("V-TOPUP-GRANT-2", r["action"] == "grant" and gm.load(mid).get("authority_tokens") == 200_000_000, r["why"])

    # exhaustion: grant 3, then a 4th trip with progress is refused
    commit(repo, "src/c.ts", "c")
    trip(mid)
    mt.sweep_one(mid, now=NOW + 600, decide_fn=decide, sender=sender)
    commit(repo, "src/d.ts", "d")
    trip(mid)
    r = mt.sweep_one(mid, now=NOW + 700, decide_fn=decide, sender=sender)
    check("V-TOPUP-EXHAUSTED", r["action"] == "refuse" and "exhausted" in r["why"]
          and gm.load(mid).get("authority_tokens") == 240_000_000, r["why"])

    # holds this module does not own are untouched, even with progress
    for gate, reason, kind in (
            ("V-TOPUP-IGNORE-DEFAULT-CEILING", "cost breaker: processed 17,058,129 > default policy ceiling", "cost"),
            ("V-TOPUP-IGNORE-STALL", "cost breaker: 9,000,000 processed since the work tree last changed", "cost"),
            ("V-TOPUP-IGNORE-OWNER-PAUSE", TRIP, "owner_stop")):
        m2, repo2 = mission(gate.lower().replace("_", "-")[8:])
        commit(repo2, "src/x.ts", "x")
        trip(m2, reason, kind)
        r = mt.sweep_one(m2, now=NOW + 800, decide_fn=decide, sender=sender)
        check(gate, r["action"] == "none" and gm.load(m2).get("owner_hold")
              and gm.load(m2).get("authority_tokens") == 120_000_000, r["why"])

    # no double grant: a pass that died after writing the grant is completed, never re-granted
    m3, repo3 = mission("crash")
    commit(repo3, "src/y.ts", "y")
    trip(m3)
    real_complete = mt._complete
    mt._complete = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("died mid-effect"))
    try:
        mt.sweep_one(m3, now=NOW + 900, decide_fn=decide, sender=sender)
    except RuntimeError:
        pass
    mt._complete = real_complete
    commit(repo3, "src/y2.ts", "work landed between the dead pass and the next one")
    r = mt.sweep_one(m3, now=NOW + 950, decide_fn=decide, sender=sender)
    pol3 = mt.load_policy(m3)
    check("V-TOPUP-NO-DOUBLE-GRANT", r["action"] == "resume" and len(pol3["grants"]) == 1
          and gm.load(m3).get("authority_tokens") == 160_000_000 and not gm.load(m3).get("owner_hold"), r["why"])

    # kill switch
    m4, repo4 = mission("kill")
    commit(repo4, "src/z.ts", "z")
    trip(m4)
    os.environ["CPP_MISSION_AUTO_TOPUP"] = "off"
    res = mt.sweep(now=NOW + 1000, decide_fn=decide, sender=sender)
    os.environ.pop("CPP_MISSION_AUTO_TOPUP")
    check("V-TOPUP-KILL-SWITCH", res[0]["why"] == "CPP_MISSION_AUTO_TOPUP=off" and gm.load(m4).get("owner_hold"))
    res = mt.sweep(now=NOW + 1100, decide_fn=decide, sender=sender)
    check("V-TOPUP-KILL-SWITCH-CONTROL", any(x.get("mission") == m4 and x["action"] == "grant" for x in res),
          str([x.get("action") for x in res]))

    # no channel: refusal says so instead of pretending (a test run never toasts: the state dir is redirected)
    check("V-TOPUP-NO-CHANNEL", mt.notify("x") == "no channel configured")
    # spec mission-unattended-continuity B: no Telegram -> the Windows toast; switch off -> no channel again
    shown = []
    got = mt.notify("hola", toaster=lambda t: shown.append(t) or "toast shown")
    check("V-TOPUP-TOAST-FALLBACK", got == "toast shown" and shown == ["hola"], f"{got} {shown}")
    saved_sd = os.environ.pop("GSD_LONG_RUN_STATE_DIR")
    try:
        os.environ["CPP_MISSION_NOTIFY_TOAST"] = "off"
        off = mt.toast_enabled()
        os.environ.pop("CPP_MISSION_NOTIFY_TOAST")
        on = mt.toast_enabled()
    finally:
        os.environ["GSD_LONG_RUN_STATE_DIR"] = saved_sd
    check("V-TOPUP-TOAST-SWITCH", off is False and on is (os.name == "nt") and mt.toast_enabled() is False,
          f"off={off} live={on} test-run={mt.toast_enabled()}")
    os.environ["TELEGRAM_BOT_TOKEN"], os.environ["TELEGRAM_CHAT_ID"] = "t", "c"
    try:
        tel = mt.notify("x", sender=lambda t: "telegram 200", toaster=lambda t: "toast shown")
    finally:
        os.environ.pop("TELEGRAM_BOT_TOKEN"), os.environ.pop("TELEGRAM_CHAT_ID")
    check("V-TOPUP-TELEGRAM-FIRST", tel == "telegram 200", tel)

    # suggest: open phases x rate
    sr = Path(TMP) / "sugg"
    (sr / ".planning").mkdir(parents=True)
    (sr / ".planning" / "ROADMAP.md").write_text(
        "- [x] **Phase 5: drift**\n- [ ] **Phase 6: history**\n- [ ] **Phase 7: quality**\n- [ ] Phase 8: crc\n",
        encoding="utf-8")
    s = mt.suggest(str(sr))
    check("V-TOPUP-SUGGEST", s["phases"] == 3 and s["authority"] == 120_000_000, str(s))
    s2 = mt.suggest(str(Path(TMP) / "nowhere"))
    check("V-TOPUP-SUGGEST-NO-ROADMAP", s2["phases"] == 3 and "assumed" in s2["basis"], s2["basis"])

    # addendum 2026-11-16: ceiling by default, commits-gated; 3x since Owner 2026-11-21 "x3" (was 2x)
    def bare(name, auth=None):
        repo = new_repo(name)
        mid = f"m-{name}"
        gm.create(repo, "/gsd-autonomous", mission_id=mid, now=NOW)
        if auth:
            gm.set_authority(mid, tokens=auth, now=NOW, reason="test")
        return mid, repo

    m5, _ = bare("derived")
    p5 = mt.budget(m5, "100M", None, "40M", reason="test", now=NOW)
    check("V-TOPUP-CEILING-DERIVED", p5["ceiling"] == 300_000_000 and p5["max_topups"] == 5
          and p5["step"] == 40_000_000, f"ceiling={p5['ceiling']} topups={p5['max_topups']}")
    t10 = mt.default_terms(10_000_000)
    check("V-TOPUP-CEILING-3X", t10["ceiling"] == 30_000_000, str(t10))

    m6, repo6 = bare("clip")
    mt.budget(m6, "100M", 5, "40M", reason="test", now=NOW, ceiling="150M")
    commit(repo6, "src/c1.ts", "1")
    trip(m6)
    mt.sweep_one(m6, now=NOW + 1200, decide_fn=decide, sender=sender)
    commit(repo6, "src/c2.ts", "2")
    trip(m6)
    r = mt.sweep_one(m6, now=NOW + 1300, decide_fn=decide, sender=sender)
    check("V-TOPUP-CEILING-CLIP", r["action"] == "grant" and gm.load(m6).get("authority_tokens") == 150_000_000,
          f"{r['action']} auth={gm.load(m6).get('authority_tokens')}")
    commit(repo6, "src/c3.ts", "3")
    trip(m6)
    r = mt.sweep_one(m6, now=NOW + 1400, decide_fn=decide, sender=sender)
    check("V-TOPUP-CEILING-REFUSE", r["action"] == "refuse" and "ceiling" in r["why"]
          and gm.load(m6).get("authority_tokens") == 150_000_000 and gm.load(m6).get("owner_hold"), r["why"])

    m7, repo7 = bare("adopt", auth=50_000_000)
    gm.bind_mission(m7, repo7, now=NOW)   # what arm/AMCR records: the root and its head at that moment
    commit(repo7, "src/w.ts", "work since arm")
    trip(m7)
    res = mt.sweep(now=NOW + 1500, decide_fn=decide, sender=sender)
    p7 = mt.load_policy(m7) or {}
    check("V-TOPUP-DEFAULT-ADOPT", p7.get("default") and p7.get("ceiling") == 150_000_000
          and gm.load(m7).get("authority_tokens") == 90_000_000 and not gm.load(m7).get("owner_hold"),
          f"policy={ {k: p7.get(k) for k in ('ceiling', 'step', 'max_topups', 'last_head')} } "
          f"res={[x for x in res if x.get('mission') == m7]}")

    m8, repo8 = bare("adopt-off", auth=50_000_000)
    commit(repo8, "src/w.ts", "work")
    trip(m8)
    os.environ["CPP_MISSION_TOPUP_DEFAULT"] = "off"
    mt.sweep(now=NOW + 1600, decide_fn=decide, sender=sender)
    os.environ.pop("CPP_MISSION_TOPUP_DEFAULT")
    check("V-TOPUP-DEFAULT-OFF", mt.load_policy(m8) is None and gm.load(m8).get("owner_hold")
          and gm.load(m8).get("authority_tokens") == 50_000_000, "kill switch kept it parked, no policy")

    # H6 (mission-capital W0), the live shape of GEX44 m-76e04d86896d 2026-11-23 09:40Z: one grant under the first
    # policy, then the Owner re-budgets to authority 215M, 1 top-up of 40M, ceiling 255M. The old grant must not
    # count against the new envelope, and the next decision id must be TOPUP2 (TOPUP1 was already delivered).
    import copy
    ma, ra = mission("epoch")
    commit(ra, "src/e1.ts", "1")
    trip(ma, at=NOW + 2000)
    mt.sweep_one(ma, now=NOW + 2010, decide_fn=decide, sender=sender)
    pre = copy.deepcopy(mt.load_policy(ma))
    mt.budget(ma, "215M", 1, "40M", reason="Owner re-budget", now=NOW + 2020, ceiling="255M")
    pa = mt.load_policy(ma)
    check("V-TOPUP-EPOCH-BUDGET", pa.get("policy_epoch") == 1 and pa.get("grants") == []
          and [g["n"] for g in pa.get("prior_grants") or []] == [1] and pa["ceiling"] == 255_000_000,
          f"epoch={pa.get('policy_epoch')} prior={len(pa.get('prior_grants') or [])} grants={len(pa['grants'])}")
    commit(ra, "src/e2.ts", "2")
    trip(ma, at=NOW + 2100)
    rec_a = gm.load(ma)
    prog_a = mt.progress_since(ra, pa["last_head"])
    # (d) control: the pre-W0 judge, copied verbatim, on the policy the pre-W0 budget() left (old grant kept).
    old_shape = {**pre, **{k: pa[k] for k in ("authority", "max_topups", "step", "ceiling", "last_head")}}
    old_v = _judge_pre_w0(rec_a, old_shape, prog_a)
    check("V-TOPUP-EPOCH-CONTROL-PRE-W0", old_v["action"] == "refuse" and "exhausted (1/1)" in old_v["why"],
          f"pre-W0 judge: {old_v}")
    check("V-TOPUP-EPOCH-CEILING-BOUND", mt.judge(rec_a, old_shape, prog_a)["action"] == "grant",
          "same old-shape policy: the ceiling bounds the envelope, not the grant count")
    r = mt.sweep_one(ma, now=NOW + 2110, decide_fn=decide, sender=sender)
    pa = mt.load_policy(ma)
    check("V-TOPUP-EPOCH-GRANT", r["action"] == "grant" and pa["grants"][-1]["n"] == 2
          and pa["grants"][-1]["epoch"] == 1 and woken[-1][1] == "TOPUP2"
          and gm.load(ma).get("authority_tokens") == 255_000_000 and not gm.load(ma).get("owner_hold"),
          f"{r} n={pa['grants'][-1]['n']} id={woken[-1][1]} auth={gm.load(ma).get('authority_tokens')}")
    # (b) ceiling reached: authority == ceiling, real progress -> refuse, still parked
    commit(ra, "src/e3.ts", "3")
    trip(ma, at=NOW + 2200)
    r = mt.sweep_one(ma, now=NOW + 2210, decide_fn=decide, sender=sender)
    check("V-TOPUP-EPOCH-CEILING-REACHED", r["action"] == "refuse" and "ceiling reached" in r["why"]
          and gm.load(ma).get("authority_tokens") == 255_000_000 and gm.load(ma).get("owner_hold"), r["why"])

    # (c) a policy file written before W0 (no policy_epoch / prior_grants, no ceiling) behaves as before
    for gate, n_old, want in (("V-TOPUP-OLD-SCHEMA-EXHAUSTED", 2, "refuse"), ("V-TOPUP-OLD-SCHEMA-GRANT", 1, "grant")):
        mo, ro = bare(gate.lower()[8:], auth=160_000_000)
        mt.save_policy({"schema": mt.SCHEMA, "mission_id": mo, "authority": 120_000_000, "max_topups": 2,
                        "step": 40_000_000, "ceiling": None, "set_at": NOW, "reason": "pre-W0 file",
                        "last_head": mt.head_of(ro),
                        "grants": [{"n": i + 1, "hold_set_at": NOW - 100 + i, "from": 0, "to": 0}
                                   for i in range(n_old)]})
        commit(ro, "src/o.ts", "o")
        trip(mo, at=NOW + 2300)
        r = mt.sweep_one(mo, now=NOW + 2310, decide_fn=decide, sender=sender)
        po = mt.load_policy(mo)
        ok = r["action"] == want and "policy_epoch" not in po and "prior_grants" not in po
        if want == "refuse":
            ok = ok and "exhausted (2/2)" in r["why"]
        else:
            ok = ok and po["grants"][-1]["n"] == 2 and woken[-1][1] == "TOPUP2"
        check(gate, ok, f"{r['action']}: {r['why']}")
    po = mt.budget(mo, "200M", 1, "40M", reason="re-budget an old file", now=NOW + 2400)
    check("V-TOPUP-OLD-SCHEMA-REBUDGET", po["policy_epoch"] == 1 and po["grants"] == []
          and [g["n"] for g in po["prior_grants"]] == [1, 2], f"epoch={po['policy_epoch']}")

    # W2 (was V-TOPUP-WORKTREE-PROGRESS, 8c059095): a plain local branch that no session of the mission named is not
    # the mission's work, however new. The executor-worktree case it stood for is V-W2-CHILD-WORKTREE (w2_gates).
    m9, repo9 = mission("wtbranch")
    git(repo9, "checkout", "-q", "-b", "worktree-agent-x")
    commit(repo9, "tools/bench.py", "a branch nobody in this mission named")
    git(repo9, "checkout", "-q", "-")
    trip(m9)
    r = mt.sweep_one(m9, now=NOW + 1700, decide_fn=decide, sender=sender)
    check("V-W2-UNRELATED-BRANCH-NOT-PROGRESS", r["action"] == "refuse" and "0 progress receipt" in r["why"]
          and gm.load(m9).get("authority_tokens") == 120_000_000, r["why"])
    os.environ["CPP_PROGRESS_RECEIPTS"] = "off"
    try:   # kill-switch control: the any-branch reading of 8c059095 grants on the same fixture
        r = mt.sweep_one(m9, now=NOW + 1710, decide_fn=decide, sender=sender, dry_run=True)
    finally:
        os.environ.pop("CPP_PROGRESS_RECEIPTS", None)
    check("V-W2-KILL-SWITCH-ANY-BRANCH", r["action"] == "grant", r["why"])
    try:   # revert control: the module at HEAD before W2 (2483d9e6 line) grants on it too
        r = _module_at(PRE_W2, "w2rev").sweep_one(m9, now=NOW + 1720, decide_fn=decide, sender=sender, dry_run=True)
        check("V-W2-REVERT-CONTROL", r["action"] == "grant", r["why"])
    except subprocess.CalledProcessError as exc:
        check("V-W2-REVERT-CONTROL", False, f"git show HEAD failed: {exc}")
    # a branch that already existed at budget time is not new work, even unmerged
    repo10 = new_repo("oldbranch")
    git(repo10, "checkout", "-q", "-b", "old-unrelated")
    commit(repo10, "src/old.ts", "old")
    git(repo10, "checkout", "-q", "-")
    m10 = "m-oldbranch"
    gm.create(repo10, "/gsd-autonomous", mission_id=m10, now=NOW)
    mt.budget(m10, "120M", 3, "40M", reason="test", now=NOW)
    trip(m10)
    r = mt.sweep_one(m10, now=NOW + 1900, decide_fn=decide, sender=sender)
    check("V-TOPUP-OLD-BRANCH-NOT-PROGRESS", r["action"] == "refuse" and gm.load(m10).get("owner_hold"), r["why"])

    # park 2: the worker itself stopped to ask for authority -> BLOCKED, no owner hold
    ASK = "OWNER_BOUNDARY (AUTHORITY): authority room too small for 04-03; host needs: more tokens"

    def block(name, reason=ASK):
        m, repo = mission(name)
        commit(repo, "src/p.ts", "work")
        rec = gm.load(m)
        gm.block_mission(rec, expect_epoch=rec["epoch"], expect_state=rec["state"], now=NOW + 50, reason=reason)
        return m, repo

    real_spent = mt._spent
    try:
        mt._spent = lambda rec: 117_000_000
        m11, _ = block("ablock")
        n_w = len(woken)
        r = mt.sweep_one(m11, now=NOW + 2000, decide_fn=decide, sender=sender)
        rec = gm.load(m11)
        check("V-TOPUP-AUTHORITY-BLOCK", r["action"] == "grant" and rec.get("authority_tokens") == 160_000_000
              and rec.get("state") == gm.RUNNING and len(woken) == n_w + 1 and woken[-1][1] == "TOPUP1",
              f"{r} state={rec.get('state')}")
        # the reason on the record is overwritten later while BLOCKED; the blocker keeps the ask
        m12, _ = block("ablock-overwritten")
        rec = gm.load(m12)
        gm.transition(m12, expect_epoch=rec["epoch"], expect_state=gm.BLOCKED, event="cost_mark", now=NOW + 60,
                      reason="progress fingerprint moved at 171,949,354 processed")
        r = mt.sweep_one(m12, now=NOW + 2100, decide_fn=decide, sender=sender)
        check("V-TOPUP-AUTHORITY-BLOCK-REASON-OVERWRITTEN", r["action"] == "grant", r["why"])
        mt._spent = lambda rec: 10_000_000
        m13, _ = block("ablock-room")
        r = mt.sweep_one(m13, now=NOW + 2200, decide_fn=decide, sender=sender)
        check("V-TOPUP-AUTHORITY-BLOCK-ROOM-LEFT", r["action"] == "refuse" and "unspent" in r["why"]
              and gm.load(m13).get("state") == gm.BLOCKED and gm.load(m13).get("authority_tokens") == 120_000_000,
              r["why"])
        mt._spent = lambda rec: None
        m14, _ = block("ablock-unmeasured")
        r = mt.sweep_one(m14, now=NOW + 2300, decide_fn=decide, sender=sender)
        check("V-TOPUP-AUTHORITY-BLOCK-UNMEASURED", r["action"] == "refuse" and "unmeasured" in r["why"], r["why"])
        mt._spent = lambda rec: 117_000_000
        m15, _ = block("other-block", "OWNER_BOUNDARY (PRODUCT_SCOPE): keep the photo on the end card?")
        r = mt.sweep_one(m15, now=NOW + 2400, decide_fn=decide, sender=sender)
        check("V-TOPUP-OTHER-BLOCK-IGNORED", r["action"] == "none" and gm.load(m15).get("state") == gm.BLOCKED
              and gm.load(m15).get("authority_tokens") == 120_000_000, r["why"])
    finally:
        mt._spent = real_spent

    w1_gates()
    w2_gates()
    print(f"TOPUP_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


def _old_module():
    """mission_topup.py exactly as at 8c452fac (W0), loaded from git into a temp module: the revert control."""
    import importlib.util
    src = subprocess.run([GIT, "-C", str(Path(__file__).resolve().parent), "show", "8c452fac:tools/mission_topup.py"],
                         capture_output=True, text=True, encoding="utf-8", check=True).stdout
    p = Path(TMP) / "oldmod" / "mission_topup_8c452fac.py"
    p.parent.mkdir(exist_ok=True)
    p.write_text(src, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("mission_topup_8c452fac", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _module_at(rev, tag):
    """tools/mission_topup.py as at git `rev`, loaded into a temp module (a revert control)."""
    import importlib.util
    src = subprocess.run([GIT, "-C", str(Path(__file__).resolve().parent), "show", f"{rev}:tools/mission_topup.py"],
                         capture_output=True, text=True, encoding="utf-8", check=True).stdout
    p = Path(TMP) / "oldmod" / f"mission_topup_{tag}.py"
    p.parent.mkdir(exist_ok=True)
    p.write_text(src, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(f"mission_topup_{tag}", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PRE_W2 = "2483d9e6"   # the merge of both lines, live on GEX44 as 90c6f26f: any-branch progress


def _iso(at):
    import datetime as _dt
    return _dt.datetime.fromtimestamp(at, _dt.timezone.utc).isoformat(timespec="seconds")


def _ledger_row(mid, event, at, **fields):
    """A ledger row stamped at fixture time `at` (ledger_append stamps wall time, which is before NOW)."""
    import json
    p = gm.lr.ledger_path()
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"ts": _iso(at), "session_id": mid, "event": event, "mission_id": mid, **fields}) + "\n")


def _session(sid, rows, subagents=None, at=None):
    """A fixture transcript projects/w2/<sid>.jsonl (+ subagents/<name>.jsonl), mtimes set to fixture time."""
    import json
    d = Path(TMP) / "projects" / "w2"
    d.mkdir(parents=True, exist_ok=True)
    files = {d / f"{sid}.jsonl": rows}
    for name, srows in (subagents or {}).items():
        files[d / sid / "subagents" / f"{name}.jsonl"] = srows
    for f, rs in files.items():
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("".join(json.dumps(r) + "\n" for r in rs), encoding="utf-8")
        if at is not None:
            os.utime(f, (at, at))


def _write_use(path, at):
    return {"type": "assistant", "timestamp": _iso(at), "cwd": "x",
            "message": {"content": [{"type": "tool_use", "name": "Write", "input": {"file_path": path}}]}}


def w2_gates():
    """The four mandatory W2 regressions (unrelated branch -, child worktree +, non-commit receipt +, planning-only
    commit -), each with its opposite pole on the same fixture."""
    # V-W2-CHILD-WORKTREE (+): a subagent isolation worktree of the mission's acked worker holds the only commit
    mc, rc_ = mission("w2child")
    wt = str(Path(rc_) / ".claude" / "worktrees" / "agent-a1")
    git(rc_, "worktree", "add", "-q", "-b", "worktree-agent-a1", wt)
    commit(wt, "src/child.py", "child work, unmerged")
    trip(mc, at=NOW + 4000)
    r = mt.sweep_one(mc, now=NOW + 4010, decide_fn=decide, sender=sender)
    check("V-W2-CHILD-WORKTREE-UNNAMED", r["action"] == "refuse", r["why"])   # pole: no session named it yet
    sid = "11111111-w2child"
    _ledger_row(mc, "worker_acked", NOW + 5, worker=sid)
    _session(sid, [{"type": "user", "timestamp": _iso(NOW + 5), "cwd": rc_}],
             {"agent-a1": [{"type": "user", "timestamp": _iso(NOW + 200), "cwd": wt, "isSidechain": True}]},
             at=NOW + 200)
    r = mt.sweep_one(mc, now=NOW + 4030, decide_fn=decide, sender=sender)
    check("V-W2-CHILD-WORKTREE", r["action"] == "grant" and "1 commit(s)" in r["why"]
          and gm.load(mc).get("authority_tokens") == 160_000_000, r["why"])
    trip(mc, at=NOW + 4040)
    r = mt.sweep_one(mc, now=NOW + 4050, decide_fn=decide, sender=sender)
    check("V-W2-CHILD-NO-RECOUNT", r["action"] == "refuse" and "no progress" in r["why"], r["why"])

    # V-W2-FOREIGN-WORKTREE (-): a NEW worktree another session (not acked by this mission) wrote in and committed
    mf, rf = mission("w2foreign")
    fwt = str(Path(rf).parent / "w2foreign-other-wt")
    git(rf, "worktree", "add", "-q", "-b", "other-pane", fwt)
    commit(fwt, "src/other.py", "another pane's work")
    _session("22222222-foreign", [_write_use(str(Path(fwt) / "src" / "other.py"), NOW + 300)], at=NOW + 300)
    trip(mf, at=NOW + 4100)
    r = mt.sweep_one(mf, now=NOW + 4110, decide_fn=decide, sender=sender)
    check("V-W2-FOREIGN-WORKTREE-NOT-PROGRESS", r["action"] == "refuse" and gm.load(mf).get("authority_tokens")
          == 120_000_000, r["why"])
    _ledger_row(mf, "worker_acked", NOW + 6, worker="22222222-foreign")   # pole: the same session, now the mission's
    r = mt.sweep_one(mf, now=NOW + 4120, decide_fn=decide, sender=sender, dry_run=True)
    check("V-W2-OWN-WRITE-WORKTREE", r["action"] == "grant", r["why"])

    # V-W2-RECEIPT (+): no commit at all; a GOOD_PROGRESS breaker receipt after the last grant is progress. Before it,
    # a receipt older than the grant, a ZERO_PROGRESS receipt and a hand-closed obligation (self-report) are not.
    mr, _ = mission("w2rcpt")
    _ledger_row(mr, "breaker_receipt", NOW - 10, classification="GOOD_PROGRESS", action="mark")
    _ledger_row(mr, "breaker_receipt", NOW + 150, classification="ZERO_PROGRESS_CONFIRMED", action="trip")
    _ledger_row(mr, "obligation_set", NOW + 160, reason="obligation x -> COMPLETED")
    trip(mr, at=NOW + 4200)
    r = mt.sweep_one(mr, now=NOW + 4210, decide_fn=decide, sender=sender)
    check("V-W2-RECEIPT-STALE-OR-SELF-REPORT", r["action"] == "refuse" and "0 progress receipt" in r["why"], r["why"])
    _ledger_row(mr, "breaker_receipt", NOW + 170, classification="GOOD_PROGRESS", action="mark")
    r = mt.sweep_one(mr, now=NOW + 4220, decide_fn=decide, sender=sender)
    check("V-W2-RECEIPT", r["action"] == "grant" and "1 progress receipt(s)" in r["why"]
          and gm.load(mr).get("authority_tokens") == 160_000_000, r["why"])
    trip(mr, at=NOW + 4240)
    r = mt.sweep_one(mr, now=NOW + 4250, decide_fn=decide, sender=sender)
    check("V-W2-RECEIPT-NO-RECOUNT", r["action"] == "refuse", r["why"])   # the receipt predates the grant now

    # V-W2-PLANNING-ONLY (-): a commit touching only .planning/ is bookkeeping; pole: a code commit grants
    mp, rp = mission("w2plan")
    commit(rp, ".planning/STATE.md", "state")
    trip(mp, at=NOW + 4300)
    r = mt.sweep_one(mp, now=NOW + 4310, decide_fn=decide, sender=sender)
    check("V-W2-PLANNING-ONLY-NOT-PROGRESS", r["action"] == "refuse" and "1 commit(s), 0 non-bookkeeping" in r["why"],
          r["why"])
    commit(rp, "src/p.ts", "code")
    r = mt.sweep_one(mp, now=NOW + 4320, decide_fn=decide, sender=sender)
    check("V-W2-PLANNING-CONTROL", r["action"] == "grant", r["why"])

    # V-W2-NOT-READ-OFF-BOUNDARY: a mission at no capital boundary is not measured at all (the sweep visits 69)
    mn, _ = mission("w2idle")
    calls = []
    real = mt.progress_receipts
    mt.progress_receipts = lambda *a, **k: calls.append(1) or real(*a, **k)
    try:
        r = mt.sweep_one(mn, now=NOW + 4400, decide_fn=decide, sender=sender)
    finally:
        mt.progress_receipts = real
    check("V-W2-NOT-READ-OFF-BOUNDARY", r["action"] == "none" and not calls, r["why"])


def _block(mid, reason, at):
    rec = gm.load(mid)
    return gm.block_mission(rec, expect_epoch=rec["epoch"], expect_state=rec["state"], now=at, reason=reason)


def _real_decide(mid, text, decision_id=None):
    """The real durable decision (replay of the same id+text is a no-op), without waking a host."""
    return gm.deliver_decision(mid, text, decision_id=decision_id, wake=False, now=NOW)


def _decisions(mid, prefix):
    return [d["id"] for d in (gm.load(mid).get("decisions") or []) if d["id"].startswith(prefix)]


def w1_gates():
    old = _old_module()
    cap_reason = "OWNER_BOUNDARY (AUTHORITY): raise authority: 119,000,000 of 120,000,000 processed; host needs: more"

    # V-CAP-BLOCKED-RENEWS (H1, 8h13m): BLOCKED, no hold, blocker CAPITAL_EXHAUSTED on the record -> grant + decision
    mb_, rb = mission("blkcap")
    SPEND[mb_] = 119_000_000
    commit(rb, "src/b1.ts", "1")
    _block(mb_, cap_reason, NOW + 3000)
    rec = gm.load(mb_)
    blk_key = f"blocked:e{rec['epoch']}:{NOW + 3000}"   # the 8c059095/b2af3eb0 key form (live grants stay valid)
    prog = mt.progress_since(rb, mt.load_policy(mb_)["last_head"])
    old_v = old.judge(rec, mt.load_policy(mb_), prog)
    r = mt.sweep_one(mb_, now=NOW + 3010, decide_fn=_real_decide, sender=sender)
    rec = gm.load(mb_)
    check("V-CAP-BLOCKED-RENEWS", r["action"] == "grant" and r.get("capital_state") == "RENEW_ELIGIBLE"
          and rec.get("authority_tokens") == 160_000_000 and _decisions(mb_, "TOPUP") == ["TOPUP1"]
          and (rec.get("blocker") or {}).get("class") == "CAPITAL_EXHAUSTED" and rec["state"] == gm.RUNNING
          and mt.load_policy(mb_)["grants"][-1]["hold_set_at"] == blk_key,
          f"{r['action']} {r.get('capital_state')} auth={rec.get('authority_tokens')} state={rec['state']} "
          f"key={mt.load_policy(mb_)['grants'][-1]['hold_set_at']}")
    check("V-CAP-BLOCKED-RENEWS-FAILS-AT-8c452fac", old_v["action"] == "none", f"8c452fac judge: {old_v}")
    r2 = mt.sweep_one(mb_, now=NOW + 3020, decide_fn=_real_decide, sender=sender)
    check("V-CAP-BLOCKED-EXACTLY-ONCE", r2["action"] == "none" and len(mt.load_policy(mb_)["grants"]) == 1
          and _decisions(mb_, "TOPUP") == ["TOPUP1"] and gm.load(mb_).get("authority_tokens") == 160_000_000,
          f"pass2={r2['action']} grants={len(mt.load_policy(mb_)['grants'])} decisions={_decisions(mb_, 'TOPUP')}")
    # crash after the grant was written, before the raise: the same BLOCKED occurrence -> resume, never a 2nd grant
    mx, rx = mission("blkcrash")
    SPEND[mx] = 119_000_000
    commit(rx, "src/x1.ts", "1")
    _block(mx, cap_reason, NOW + 3000)
    real_set = gm.set_authority
    gm.set_authority = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("died before the raise"))
    try:
        mt.sweep_one(mx, now=NOW + 3010, decide_fn=_real_decide, sender=sender)
    except RuntimeError:
        pass
    gm.set_authority = real_set
    r3 = mt.sweep_one(mx, now=NOW + 3020, decide_fn=_real_decide, sender=sender)
    check("V-CAP-BLOCKED-CRASH-RESUMES", r3["action"] == "resume" and len(mt.load_policy(mx)["grants"]) == 1
          and _decisions(mx, "TOPUP") == ["TOPUP1"] and gm.load(mx)["state"] == gm.RUNNING
          and gm.load(mx).get("authority_tokens") == 160_000_000, f"{r3['action']} state={gm.load(mx)['state']}")
    # a worker ask with a step unspent: answered by a resume only when the Owner raised authority after the block
    mz, rz = mission("blkstale")
    SPEND[mz] = 119_000_000
    _block(mz, cap_reason, NOW + 3000)
    gm.set_authority(mz, tokens=200_000_000, now=NOW + 3005, reason="Owner raise after the ask (test)")
    r4 = mt.sweep_one(mz, now=NOW + 3010, decide_fn=_real_decide, sender=sender)
    check("V-CAP-BLOCKED-STALE-ASK-RESUMES", r4["action"] == "release" and r4.get("capital_state") == "RESUME_ONLY"
          and _decisions(mz, "RESUME") == ["RESUME1"] and gm.load(mz)["state"] == gm.RUNNING
          and not mt.load_policy(mz).get("grants"), f"{r4['action']} {r4.get('capital_state')}: {r4['why']}")
    # control: the same BLOCKED shape on another blocker class is left alone
    mc, rcc = mission("blkother")
    SPEND[mc] = 119_000_000
    commit(rcc, "src/o1.ts", "1")
    _block(mc, "OWNER_BOUNDARY (PRODUCT): choose the landing headline; host needs: a product decision", NOW + 3000)
    r = mt.sweep_one(mc, now=NOW + 3010, decide_fn=_real_decide, sender=sender)
    rec = gm.load(mc)
    check("V-CAP-BLOCKED-RENEWS-CONTROL", r["action"] == "none" and rec["state"] == gm.BLOCKED
          and rec.get("authority_tokens") == 120_000_000 and not _decisions(mc, "TOPUP")
          and (rec.get("blocker") or {}).get("class") != "CAPITAL_EXHAUSTED",
          f"{r['action']} class={(rec.get('blocker') or {}).get('class')}")

    # V-CAP-STALE-HOLD-RESUME (m-396659f48a16): hold stays after the Owner raised authority -> release, no grant
    ms_, rs = mission("stale")
    SPEND[ms_] = 119_000_000
    trip(ms_, at=NOW + 3100)
    gm.set_authority(ms_, tokens=200_000_000, now=NOW + 3110, reason="Owner raise (test)")
    r = mt.sweep_one(ms_, now=NOW + 3120, decide_fn=_real_decide, sender=sender)
    p = mt.load_policy(ms_)
    rec = gm.load(ms_)
    r2 = mt.sweep_one(ms_, now=NOW + 3130, decide_fn=_real_decide, sender=sender)
    check("V-CAP-STALE-HOLD-RESUME", r["action"] == "release" and r.get("capital_state") == "RESUME_ONLY"
          and not p.get("grants") and rec.get("authority_tokens") == 200_000_000 and not rec.get("owner_hold")
          and _decisions(ms_, "RESUME") == ["RESUME1"] and len(p.get("resumes") or []) == 1
          and p["resumes"][0]["key"] == NOW + 3100 and r2["action"] == "none",
          f"{r['action']} {r.get('capital_state')} grants={len(p.get('grants') or [])} hold={rec.get('owner_hold')}")
    mn, rn = mission("stale-ctl")       # control: same hold, NO headroom (spent at the trip line) -> stays
    trip(mn, at=NOW + 3100)
    r = mt.sweep_one(mn, now=NOW + 3120, decide_fn=_real_decide, sender=sender)
    check("V-CAP-STALE-HOLD-RESUME-CONTROL", r["action"] == "refuse" and r.get("capital_state") == "RENEW_ELIGIBLE"
          and gm.load(mn).get("owner_hold") and not _decisions(mn, "RESUME"), f"{r['action']}: {r['why']}")

    # V-CAP-HOURS-EXHAUSTED (H8): deadline passed -> refuse, notify names --extend-hours; control before it grants
    mh, rh = mission("hours")
    commit(rh, "src/h.ts", "h")
    trip(mh, at=NOW + 86_000)
    n_sent = len(sent)
    r = mt.sweep_one(mh, now=NOW + 24 * 3600 + 10, decide_fn=decide, sender=sender)
    msg = sent[-1] if len(sent) > n_sent else ""
    check("V-CAP-HOURS-EXHAUSTED", r["action"] == "refuse" and "hours exhausted" in r["why"]
          and "--extend-hours" in msg and "--tokens" not in msg and gm.load(mh).get("authority_tokens") == 120_000_000
          and gm.load(mh).get("owner_hold"), f"{r['why']} | {msg[-90:]}")
    r = mt.sweep_one(mh, now=NOW + 24 * 3600 - 100, decide_fn=decide, sender=sender)
    check("V-CAP-HOURS-EXHAUSTED-CONTROL", r["action"] == "grant", f"before the deadline: {r['action']} {r['why']}")

    # V-CAP-CYCLES-NOT-REFUSED: cycles spent is recorded, not refused (the runtime renews a cycle-capped halt)
    my, ry = mission("cycles")
    rec = gm.load(my)
    gm.transition(my, expect_epoch=rec["epoch"], expect_state=rec["state"], event="test_iterations", iterations=12)
    commit(ry, "src/y.ts", "y")
    trip(my, at=NOW + 3200)
    cs = mt.capital_state(gm.load(my), mt.load_policy(my), 119_000_000, NOW + 3210)
    r = mt.sweep_one(my, now=NOW + 3210, decide_fn=decide, sender=sender)
    check("V-CAP-CYCLES-NOT-REFUSED", r["action"] == "grant" and cs["dims"]["cycles_exhausted"]
          and cs["dims"]["cycles_used"] == 12 and cs["state"] == "RENEW_ELIGIBLE", f"{r['action']} dims={cs['dims']}")

    # V-CAP-UNKNOWN-SPENT: unmeasured spend never grants and is never zero; control: measured -> grant
    mu, ru = mission("unknown")
    SPEND[mu] = None
    commit(ru, "src/u.ts", "u")
    trip(mu, at=NOW + 3300)
    r = mt.sweep_one(mu, now=NOW + 3310, decide_fn=decide, sender=sender)
    check("V-CAP-UNKNOWN-SPENT", r["action"] == "refuse" and r.get("capital_state") == "UNKNOWN"
          and "unmeasured" in r["why"] and gm.load(mu).get("authority_tokens") == 120_000_000
          and gm.load(mu).get("owner_hold") and not mt.load_policy(mu).get("grants"), r["why"])
    del SPEND[mu]
    r = mt.sweep_one(mu, now=NOW + 3320, decide_fn=decide, sender=sender)
    check("V-CAP-UNKNOWN-SPENT-CONTROL", r["action"] == "grant", f"measured: {r['action']}")

    # V-CAP-TERMINAL: HALTED by _dead_worker_authority_guard -> TERMINAL, nothing grants
    guard = ("cost breaker (mission authority): CAPITAL_EXHAUSTED: 900,000 left of 120,000,000 authority, below the "
             "1,176,471 a minimum successor lease needs")
    mtm, rt = mission("terminal")
    commit(rt, "src/t.ts", "t")
    trip(mtm, reason=guard, at=NOW + 3400)
    rec = gm.load(mtm)
    gm.transition(mtm, expect_epoch=rec["epoch"], expect_state=rec["state"], event="mission_halted",
                  state=gm.HALTED, reason=guard)
    r = mt.sweep_one(mtm, now=NOW + 3410, decide_fn=decide, sender=sender)
    cs = mt.capital_state(gm.load(mtm), mt.load_policy(mtm), 119_000_000, NOW + 3410)
    check("V-CAP-TERMINAL", r["action"] == "none" and cs["state"] == "TERMINAL" and not mt.load_policy(mtm).get(
        "grants") and gm.load(mtm).get("authority_tokens") == 120_000_000, f"{r['action']} {cs['state']}")
    mg, rg = mission("guardpark")        # control: the same guard reason on a live park is case 1 -> grant
    commit(rg, "src/g.ts", "g")
    trip(mg, reason=guard, at=NOW + 3400)
    r = mt.sweep_one(mg, now=NOW + 3410, decide_fn=decide, sender=sender)
    check("V-CAP-TERMINAL-CONTROL", r["action"] == "grant", f"live guard park: {r['action']} {r['why']}")

    # V-CAP-KILL-SWITCH: CPP_CAPITAL_STATE=off -> judge() equals the 8c452fac judge on every shape
    shapes = []
    for m_ in (mb_, mc, ms_, mn, mh, mtm, mg, my):
        rec_ = gm.load(m_)
        pol_ = mt.load_policy(m_)
        for pg in ({"measured": True, "progress": True, "commits": 2, "paths": 1, "head": "x"},
                   {"measured": True, "progress": False, "commits": 0, "paths": 0}, {"measured": False, "why": "w"}):
            shapes.append((rec_, pol_, pg))
    shapes.append((None, {"max_topups": 1}, {"measured": False}))
    # the record as it stood at the block (the grant has since unblocked it to RUNNING)
    blocked_shape = dict(gm.load(mb_), authority_tokens=120_000_000, state=gm.BLOCKED)
    pol_b = {**mt.load_policy(mb_), "grants": []}
    os.environ["CPP_CAPITAL_STATE"] = "off"
    try:
        same = all(mt.judge(*s) == old.judge(*s) for s in shapes)
        off_blocked = mt.judge(blocked_shape, pol_b, shapes[0][2])
    finally:
        os.environ.pop("CPP_CAPITAL_STATE")
    on_blocked = mt.judge(blocked_shape, pol_b, shapes[0][2], spent=119_000_000, now=NOW + 3500)
    check("V-CAP-KILL-SWITCH", same and off_blocked["action"] == "none" and on_blocked["action"] == "grant",
          f"{len(shapes)} shapes equal={same}; BLOCKED off={off_blocked['action']} on={on_blocked['action']}")

    # V-CAP-REBUDGET-HALF-GRANT: a written grant whose raise never landed is VOIDED (ledger row), then the epoch opens
    mv, rv = mission("halfgrant")
    commit(rv, "src/v.ts", "v")
    trip(mv, at=NOW + 3600)
    real_set = gm.set_authority
    gm.set_authority = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("died before the raise"))
    try:
        mt.sweep_one(mv, now=NOW + 3610, decide_fn=decide, sender=sender)
    except RuntimeError:
        pass
    gm.set_authority = real_set
    half = mt.load_policy(mv)["grants"][-1]
    pv = mt.budget(mv, "200M", 1, "40M", reason="Owner re-budget", now=NOW + 3620, ceiling="240M")
    rows = "".join(f.read_text(encoding="utf-8", errors="replace") for f in Path(TMP).rglob("*.jsonl"))
    r = mt.sweep_one(mv, now=NOW + 3630, decide_fn=decide, sender=sender)
    check("V-CAP-REBUDGET-HALF-GRANT", half["to"] == 160_000_000 and (pv["prior_grants"][-1].get("voided") or {})
          .get("why", "").startswith("re-budget to 200,000,000") and "authority_topup_voided" in rows
          and pv["grants"] == [] and gm.load(mv).get("authority_tokens") == 200_000_000 and r["action"] != "resume",
          f"voided={pv['prior_grants'][-1].get('voided')} next={r['action']}")
    mw, rw = mission("fullgrant")        # control: an APPLIED grant is not voided by a re-budget
    commit(rw, "src/w.ts", "w")
    trip(mw, at=NOW + 3600)
    mt.sweep_one(mw, now=NOW + 3610, decide_fn=decide, sender=sender)
    pw = mt.budget(mw, "200M", 1, "40M", reason="Owner re-budget", now=NOW + 3620, ceiling="240M")
    check("V-CAP-REBUDGET-HALF-GRANT-CONTROL", pw["prior_grants"][-1]["to"] == 160_000_000
          and "voided" not in pw["prior_grants"][-1], str(pw["prior_grants"][-1].get("voided")))


if __name__ == "__main__":
    sys.exit(main())
