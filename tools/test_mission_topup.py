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
os.environ.pop("CPP_MISSION_AUTO_TOPUP", None)
os.environ.pop("TELEGRAM_BOT_TOKEN", None)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_mission as gm  # noqa: E402
import mission_topup as mt  # noqa: E402

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
    gm.set_owner_hold(mid, reason, now=at or NOW + len(woken) + len(sent) + 10, kind=kind)


def main() -> int:
    # parse
    check("V-TOPUP-PARSE", mt.parse_tokens("40M") == 40_000_000 and mt.parse_tokens("1.5m") == 1_500_000
          and mt.parse_tokens("800K") == 800_000, "40M/1.5m/800K")
    try:
        mt.parse_tokens("lots")
        check("V-TOPUP-PARSE-REFUSE", False, "accepted 'lots'")
    except ValueError:
        check("V-TOPUP-PARSE-REFUSE", True)

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

    # no channel: refusal says so instead of pretending
    check("V-TOPUP-NO-CHANNEL", mt.notify("x") == "no channel configured")

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

    print(f"TOPUP_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
