#!/usr/bin/env python
"""V-BURN-HOLD-* gates for BAMR P5 (vault/specs/budget-aware-mission-recovery.md): the burn-optimisation hold at
supersede time. Owner 2026-11-20: trigger = supersede, N = 50M tokens with no tree change, release = a cited fix.

Hermetic: state goes to a temp dir BEFORE import; the mission repo is a real temp git repo so the commit checks
run against git, not a stub. Every refusal has a paired control, so a module that refuses (or admits) everything
cannot go green.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="gsd-mission-burn-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["CPP_MISSION_ACCOUNT_ADMISSION"] = "off"  # account quota: covered by test_mission_account_admission
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ.pop("CPP_MISSION_BURN_HOLD", None)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_mission as gm  # noqa: E402

LIVE = {"fp": "fp-origin"}
gm.progress_fingerprint = lambda work_dir: LIVE["fp"]

REPO = Path(TMP) / "repo"
REPO.mkdir()
GIT = gm.resolve_exe("git") or "git"
passes = fails = 0
N = gm.BURN_HOLD_TOKENS


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def git(*args, when: float | None = None) -> str:
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@t")
    if when is not None:
        env["GIT_COMMITTER_DATE"] = env["GIT_AUTHOR_DATE"] = f"{int(when)} +0000"
    return subprocess.run([GIT, "-C", str(REPO), *args], capture_output=True, text=True, env=env,
                          check=True).stdout.strip()


def commit(msg: str, when: float) -> str:
    (REPO / "f.txt").write_text(msg, encoding="utf-8")
    git("add", "f.txt")
    git("commit", "-q", "-m", msg, when=when)
    return git("rev-parse", "HEAD")


def arm(ws, **kw):
    return gm.arm(str(REPO), f"/gsd-autonomous --ws {ws}", launch=False, **kw)["mission"]


def burned(ws, *, tokens=None, stamp=None, fp="fp-origin", measured=True):
    """A live attempt of goal `ws` with recorded spend and progress, as the supervisor leaves it."""
    rec = arm(ws)
    fields = {"progress_origin": "fp-origin", "progress": {"fp": fp, "stalls": 3, "measured": measured}}
    if tokens is not None:
        fields["cost_mark"] = {"fp": fp, "tokens": tokens, "at": time.time()}
    if stamp is not None:
        fields["spend_stamp"] = {"tokens": stamp, "at": time.time()}
    return gm.transition(rec["mission_id"], expect_epoch=rec["epoch"], expect_state=rec["state"],
                         event="t_burn", **fields)


def supersede(ws, old):
    return arm(ws, supersedes=old["mission_id"], authority="Owner 'y' 2026-11-20 (test)")


def refused(fn, needle):
    try:
        fn()
    except gm.MissionError as exc:
        return needle in str(exc), str(exc)[:160]
    return False, "admitted"


def events(mid, name):
    return sum(1 for e in gm.lr.ledger_events(mid) if e.get("event") == name)


def main() -> int:
    git("init", "-q")
    commit("base", time.time() - 7200)
    LIVE["fp"] = "fp-origin"

    # Threshold, both poles.
    under = burned("ws-under", tokens=N - 1)
    s = supersede("ws-under", under)
    check("V-BURN-HOLD-UNDER-N-SUPERSEDES", s.get("supersedes") == under["mission_id"]
          and gm.load(under["mission_id"])["state"] == gm.HALTED)
    at_n = burned("ws-at", tokens=N)
    ok, ev = refused(lambda: supersede("ws-at", at_n), "BURN_OPTIMIZATION_REQUIRED")
    check("V-BURN-HOLD-AT-N-REFUSED", ok, ev)
    held = gm.load(at_n["mission_id"])
    check("V-BURN-HOLD-SETS-KIND", (held.get("owner_hold") or {}).get("kind") == gm.BURN_HOLD_KIND
          and held["state"] not in gm.TERMINAL and (held["owner_hold"].get("burn") or {}).get("tokens") == N,
          str(held.get("owner_hold"))[:160])

    # Spend is the larger recorded figure (spend_stamp beside cost_mark).
    st = burned("ws-stamp", tokens=1_000, stamp=N + 5)
    ok, ev = refused(lambda: supersede("ws-stamp", st), "BURN_OPTIMIZATION_REQUIRED")
    check("V-BURN-HOLD-READS-SPEND-STAMP", ok, ev)

    # Tree change, every pole.
    ch = burned("ws-changed", tokens=N * 3, fp="fp-moved")
    check("V-BURN-HOLD-CHANGED-TREE-SUPERSEDES", supersede("ws-changed", ch).get("supersedes") == ch["mission_id"])
    lv = burned("ws-live", tokens=N * 3)
    LIVE["fp"] = "fp-live-moved"
    check("V-BURN-HOLD-LIVE-CHANGE-SUPERSEDES", supersede("ws-live", lv).get("supersedes") == lv["mission_id"])
    LIVE["fp"] = None
    lv2 = burned("ws-live-unread", tokens=N * 3)
    ok, ev = refused(lambda: supersede("ws-live-unread", lv2), "BURN_OPTIMIZATION_REQUIRED")
    check("V-BURN-HOLD-UNREADABLE-LIVE-KEEPS-RECORDED", ok, ev)
    LIVE["fp"] = "fp-origin"

    # Unknown is recorded, never zero and never a hold.
    unk = burned("ws-unk-tok")
    check("V-BURN-HOLD-UNKNOWN-SPEND-SUPERSEDES", supersede("ws-unk-tok", unk).get("supersedes") == unk["mission_id"]
          and events(unk["mission_id"], "burn_check_unknown") == 1)
    unm = burned("ws-unk-tree", tokens=N * 3, measured=False)
    check("V-BURN-HOLD-UNKNOWN-TREE-SUPERSEDES", supersede("ws-unk-tree", unm).get("supersedes") == unm["mission_id"]
          and events(unm["mission_id"], "burn_check_unknown") == 1)

    # A held goal: plain arm refused, a second supersede refused until cited.
    ok, ev = refused(lambda: arm("ws-at"), "goal held")
    check("V-BURN-HOLD-PLAIN-ARM-REFUSED", ok, ev)
    ok, ev = refused(lambda: supersede("ws-at", gm.load(at_n["mission_id"])), "burn-cite")
    check("V-BURN-HOLD-UNCITED-SUPERSEDE-REFUSED", ok, ev)

    # Citation: fake commit, a fix older than the hold, a mission without a burn hold -- all refused.
    mid = at_n["mission_id"]
    ok, ev = refused(lambda: gm.burn_cite(mid, "cache the plan graph", "deadbeef" * 5), "not a commit")
    check("V-BURN-CITE-FAKE-COMMIT-REFUSED", ok, ev)
    old_fix = commit("old fix", time.time() - 3600)
    ok, ev = refused(lambda: gm.burn_cite(mid, "cache the plan graph", old_fix), "predates")
    check("V-BURN-CITE-PREDATING-COMMIT-REFUSED", ok, ev)
    other = arm("ws-free")
    ok, ev = refused(lambda: gm.burn_cite(other["mission_id"], "x", old_fix), "no burn-optimisation hold")
    check("V-BURN-CITE-NO-HOLD-REFUSED", ok, ev)
    ok, ev = refused(lambda: supersede("ws-at", gm.load(mid)), "burn-cite")
    check("V-BURN-HOLD-REFUSED-CITATIONS-DO-NOT-RELEASE", ok, ev)

    # A valid citation releases it at the next supersede, and only then.
    fix = commit("real fix", time.time() + 60)
    row = gm.burn_cite(mid, "relay card carries the plan verdict; no re-read per epoch", fix)
    check("V-BURN-CITE-RECORDED", row["commit"] == fix and (gm.load(mid).get("owner_hold") or {}).get("kind")
          == gm.BURN_HOLD_KIND, "hold stands until the supersede consumes it")
    succ = supersede("ws-at", gm.load(mid))
    old = gm.load(mid)
    check("V-BURN-HOLD-CITED-SUPERSEDE-RELEASES", succ.get("supersedes") == mid and old["state"] == gm.HALTED
          and not old.get("owner_hold") and events(mid, "burn_hold_released_by_citation") == 1,
          f"{old['state']} hold={old.get('owner_hold')}")

    # Review MEDIUM-1: a bound attempt is re-checked on its execution root, not on cwd.
    wt = Path(TMP) / "wt-bound"
    wt.mkdir()
    gm.progress_fingerprint = lambda work_dir: "fp-origin" if Path(work_dir) == wt else "fp-main-checkout"
    try:
        bd = burned("ws-bound", tokens=N * 2)
        bd = gm.transition(bd["mission_id"], expect_epoch=bd["epoch"], expect_state=bd["state"], event="t_bind",
                           binding={"root": str(wt), "gen": 1})
        ok, ev = refused(lambda: supersede("ws-bound", bd), "BURN_OPTIMIZATION_REQUIRED")
        check("V-BURN-HOLD-BOUND-ROOT-MEASURED", ok, ev)
    finally:
        gm.progress_fingerprint = lambda work_dir: LIVE["fp"]

    # Review MEDIUM-2: a hold this feature does not own is kept; the burn marker rides beside it.
    ch_ = burned("ws-costheld", tokens=N * 2)
    gm.set_owner_hold(ch_["mission_id"], "MISSION COST HOLD: test", kind="cost")
    ok, ev = refused(lambda: supersede("ws-costheld", gm.load(ch_["mission_id"])), "BURN_OPTIMIZATION_REQUIRED")
    kept = gm.load(ch_["mission_id"])
    check("V-BURN-HOLD-KEEPS-FOREIGN-HOLD", ok and (kept.get("owner_hold") or {}).get("kind") == "cost"
          and (kept.get("burn_hold") or {}).get("burn", {}).get("tokens") == N * 2,
          f"{ev} hold={(kept.get('owner_hold') or {}).get('kind')}")
    ok, ev = refused(lambda: supersede("ws-costheld", gm.load(ch_["mission_id"])), "burn-cite")
    check("V-BURN-HOLD-FOREIGN-HOLD-UNCITED-REFUSED", ok, ev)
    fix2 = commit("fix two", time.time() + 120)
    gm.burn_cite(ch_["mission_id"], "bounded the retry", fix2)
    s2 = supersede("ws-costheld", gm.load(ch_["mission_id"]))
    o2 = gm.load(ch_["mission_id"])
    check("V-BURN-HOLD-FOREIGN-HOLD-CITED-SUPERSEDES", s2.get("supersedes") == ch_["mission_id"]
          and o2["state"] == gm.HALTED and not o2.get("burn_hold")
          and (o2.get("burn_cited") or {}).get("commit") == fix2, str(o2.get("burn_cited")))

    # Review LOW-3: only a hex sha is a citation (no ref names, no option injection).
    oc = burned("ws-refs", tokens=N * 2)
    refused(lambda: supersede("ws-refs", oc), "BURN_OPTIMIZATION_REQUIRED")
    commit("after hold", time.time() + 180)
    for bad, gate in (("HEAD", "V-BURN-CITE-REF-NAME-REFUSED"), ("--output=x", "V-BURN-CITE-OPTION-REFUSED")):
        ok, ev = refused(lambda b=bad: gm.burn_cite(oc["mission_id"], "x", b), "hex sha")
        check(gate, ok, ev)
    check("V-BURN-CITE-NO-OPTION-SIDE-EFFECT", not any(Path(p).name.startswith("x") for p in os.listdir(REPO)))

    # Review LOW-4: a cited supersede whose create() fails leaves the hold standing (consumed atomically).
    gm.burn_cite(oc["mission_id"], "x", git("rev-parse", "HEAD"))
    real_create = gm.create

    def boom(*a, **k):
        raise OSError("disk full (test)")
    gm.create = boom
    try:
        try:
            supersede("ws-refs", gm.load(oc["mission_id"]))
        except OSError:
            pass
    finally:
        gm.create = real_create
    after = gm.load(oc["mission_id"])
    check("V-BURN-HOLD-SURVIVES-FAILED-CREATE", bool(after.get("burn_hold")) and after["state"] not in gm.TERMINAL
          and (after.get("owner_hold") or {}).get("kind") == gm.BURN_HOLD_KIND, str(after.get("owner_hold"))[:120])
    check("V-BURN-HOLD-RETRY-AFTER-FAILED-CREATE",
          supersede("ws-refs", gm.load(oc["mission_id"])).get("supersedes") == oc["mission_id"])

    # Kill switch, with its control above (V-BURN-HOLD-AT-N-REFUSED).
    os.environ["CPP_MISSION_BURN_HOLD"] = "off"
    try:
        off = burned("ws-off", tokens=N * 3)
        check("V-BURN-HOLD-KILL-SWITCH", supersede("ws-off", off).get("supersedes") == off["mission_id"])
    finally:
        os.environ.pop("CPP_MISSION_BURN_HOLD", None)

    print(f"\n{passes} passed, {fails} failed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
