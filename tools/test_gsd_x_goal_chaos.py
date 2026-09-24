#!/usr/bin/env python3
"""Chaos: break the goal spine twelve ways and require it to stay honest (C14).

Every case here is a failure this design claims to survive. None is reasoned
about: each one is caused, and the system's own answer is read back. The two
that matter most are the ones that could fake success -- a queue with nothing
in it, and a coordinator that died mid-decision.

    python tools/test_gsd_x_goal_chaos.py
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

from modules.gsd_x.goal import contract as gc       # noqa: E402
from modules.gsd_x.goal import convergence as cv    # noqa: E402
from modules.gsd_x.goal import epoch as ep          # noqa: E402
from modules.gsd_x.goal import git_state as gs      # noqa: E402
from modules.gsd_x.goal import log as gl            # noqa: E402
from modules.gsd_x.goal import reconcile as rc      # noqa: E402
from modules.gsd_x.goal.providers.gate import GateProvider   # noqa: E402
from modules.gsd_x.mission import closure as mcl    # noqa: E402

GIT = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"   # PATH first: GEX44 (Linux) runs these
CLI = ROOT / "tools" / "gsd_x_goal.py"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
       "PYTHONIOENCODING": "utf-8"}
REPO_ID = "c0" * 20
SCOPE = "sc"

SLOW_GATE = "import time\nprint('working')\ntime.sleep(120)\n"
OK_GATE = "import sys\nprint('2 passed')\nsys.exit(0)\n"


def make_repo(body=OK_GATE) -> Path:
    d = Path(tempfile.mkdtemp(prefix="gsdx_chaos_repo_"))
    subprocess.run([GIT, "init", "-q", str(d)], check=True, env=ENV)
    (d / "gate.py").write_text(body, encoding="utf-8")
    (d / "slow.py").write_text(SLOW_GATE, encoding="utf-8")
    subprocess.run([GIT, "-C", str(d), "add", "."], check=True, env=ENV)
    subprocess.run([GIT, "-C", str(d), "commit", "-qm", "seed"], check=True, env=ENV)
    return d


def goal(base: Path, gid: str, repo: Path, *, obligations=True, satisfy_all=False,
         harvest_open=False):
    lg = gl.GoalLog(REPO_ID, gid, base=base)
    gc.declare(lg, f"chaos {gid}", ["it works"], [], {"paths": ["."]})
    for plane in cv.PLANES:
        s = gc.project(lg)
        cv.set_plane(lg, s, plane, plane in cv.ALWAYS, "" if plane in cv.ALWAYS
                     else "not claimed", "t")
    if obligations:
        pin = gs.file_pin(repo, ["gate.py"])
        for plane in (cv.OUTCOME, cv.EVIDENCE, cv.REGRESSION, cv.UCR_CIF_LEARNING):
            cv.accept_obligation(lg, gc.project(lg), f"ob-{plane.lower()}", plane, "do it",
                                 f'"{sys.executable}" gate.py', pin, "t")
        if satisfy_all or harvest_open:
            tree = gs.tree_id(repo, ["."])
            targets = list(cv.project_convergence(gc.project(lg)).obligations)
            if harvest_open:            # everything but the learning plane
                targets = [t for t in targets if "ucr" not in t]
            for oid in targets:
                s = gc.project(lg)
                cv.satisfy(lg, s, oid, mcl.Verdict("gate.py", 0, "ok", tree, s.revision,
                                                   "unit", pin), "t")
    return lg


def ctx(lg, repo, **kw):
    s = gc.project(lg)
    return rc.Context(state=s, tree_hash=kw.pop("tree", gs.tree_id(repo, ["."])),
                      scope_hash=SCOPE, providers=kw.pop("providers", ("gate", "codex")),
                      now=kw.pop("now", 1000.0), **kw)


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []

    def ok(g, ev):
        passes.append(g)
        print(f"  PASS {g}: {ev}")

    def bad(g, why):
        fails.append(g)
        print(f"  FAIL {g}: {why}")

    def check(g, cond, ev, why):
        (ok if cond else bad)(g, ev if cond else why)

    base = Path(tempfile.mkdtemp(prefix="gsdx_chaos_goals_"))
    repo = make_repo()

    # 1. coordinator killed between deciding and appending
    lg = goal(base, "c-1", repo)
    d1 = rc.decide(ctx(lg, repo))
    d2 = rc.decide(ctx(lg, repo))        # nothing was appended: re-derive
    check("V-CHAOS-1-DECISION-REDERIVED",
          d1.kind == d2.kind and d1.info_key == d2.info_key,
          "a decision lost before it was appended is simply re-derived", f"{d1} vs {d2}")

    # 2. two coordinators race for the same sequence number
    lg2 = goal(base, "c-2", repo)
    s2 = gc.project(lg2)
    ep.begin(lg2, s2, "gate", {}, "k-a", "initial", "w1")
    try:
        ep.begin(lg2, s2, "gate", {}, "k-b", "initial", "w2")   # same stale state
        bad("V-CHAOS-2-CAS", "both coordinators wrote a decision")
    except gl.LostRace:
        ok("V-CHAOS-2-CAS", "the second coordinator loses the sequence and must re-derive")

    # 3. an epoch that outlives its bound is cancelled and ends EXPIRED
    runs = Path(tempfile.mkdtemp(prefix="gsdx_chaos_runs_"))
    prov = GateProvider(runs, wall_bound_s=0.5)
    lg3 = goal(base, "c-3", repo)
    s3 = gc.project(lg3)
    e3 = ep.begin(lg3, s3, "gate", {}, "k3", "initial", "t")
    h3 = prov.dispatch({"epoch_id": e3.epoch_id, "revision": s3.revision, "root": str(repo),
                        "identity": e3.identity, "scope_paths": ["."],
                        "gate": {"id": "slow", "command": [sys.executable, "slow.py"],
                                 "class": "unit", "files": ["slow.py"]}})
    ep.mark_running(lg3, gc.project(lg3), e3.epoch_id, h3, "t")
    time.sleep(1.0)
    obs3 = prov.observe(h3)
    prov.cancel(h3)
    ep.end(lg3, gc.project(lg3), e3.epoch_id, ep.EXPIRED, "over its wall bound", "t")
    check("V-CHAOS-3-WALL-BOUND",
          "wall bound" in obs3.detail
          and ep.project_epochs(gc.project(lg3))[e3.epoch_id].outcome == ep.EXPIRED,
          "an epoch past its bound is visible as such and ends EXPIRED", f"{obs3}")

    # 4. the provider will not start: the epoch stays open until it is resolved
    lg4 = goal(base, "c-4", repo)
    s4 = gc.project(lg4)
    e4 = ep.begin(lg4, s4, "gate", {}, "k4", "initial", "t")
    check("V-CHAOS-4-OPEN-UNTIL-RESOLVED",
          ep.open_epochs(gc.project(lg4)) == [e4.epoch_id],
          "an epoch whose dispatch never happened stays open and blocks closure",
          "the unresolved epoch vanished")

    class Gone:
        name, wall_bound_s = "gone", 1.0
        def dispatch(self, spec): raise ep.EpochError("provider unavailable")
        def observe(self, handle): return ep.Observation(ep.OBS_UNKNOWN)
        def harvest(self, handle, spec): return ep.Receipt("", self.name, "")
        def cancel(self, handle): pass
        def probe(self, identity): return None

    res4 = ep.recover(lg4, gc.project(lg4), Gone(), e4.epoch_id, "t")
    check("V-CHAOS-4-RECOVERS-LOST", res4 == ep.LOST
          and ep.open_epochs(gc.project(lg4)) == [],
          "with no run behind it the epoch resolves LOST and stops blocking", res4)

    # 5. the goal's meaning changes while an epoch is in flight
    lg5 = goal(base, "c-5", repo)
    s5 = gc.project(lg5)
    e5 = ep.begin(lg5, s5, "gate", {}, "k5", "initial", "t")
    ep.mark_running(lg5, gc.project(lg5), e5.epoch_id, {"pid": 1}, "t")
    s5b = gc.project(lg5)
    s5b = gc.revise(lg5, s5b.last_seq + 1, s5b.intent, s5b.acceptance + ["and fast"],
                    s5b.constraints, s5b.scope)
    stale = ep.Receipt(e5.epoch_id, "gate", s5b.revision)      # about the NEW revision
    try:
        ep.ingest_receipt(lg5, gc.project(lg5), stale, "t")
        bad("V-CHAOS-5-REVISION-MOVED", "a receipt for another revision was ingested")
    except ep.EpochError:
        ok("V-CHAOS-5-REVISION-MOVED",
           "an epoch aimed at the old revision cannot bank work against the new one")

    # 6 + 7. duplicate and replayed receipts
    lg6 = goal(base, "c-6", repo)
    s6 = gc.project(lg6)
    e6 = ep.begin(lg6, s6, "gate", {}, "k6", "initial", "t")
    r6 = ep.Receipt(e6.epoch_id, "gate", s6.revision, commits=["abc"])
    ep.ingest_receipt(lg6, gc.project(lg6), r6, "t")
    try:
        ep.ingest_receipt(lg6, gc.project(lg6), r6, "t")
        bad("V-CHAOS-6-DUPLICATE-RECEIPT", "the same receipt was banked twice")
    except ep.EpochError:
        ok("V-CHAOS-6-DUPLICATE-RECEIPT", "a duplicate receipt is refused")
    ep.end(lg6, gc.project(lg6), e6.epoch_id, ep.COMPLETED, "done", "t")
    try:
        ep.ingest_receipt(lg6, gc.project(lg6), r6, "t")
        bad("V-CHAOS-7-REPLAY", "a receipt was replayed after the epoch ended")
    except ep.EpochError:
        ok("V-CHAOS-7-REPLAY", "replaying a receipt after the epoch ended is refused")

    # 8. the budget runs out with the goal open
    d8 = rc.decide(ctx(lg, repo, budget={"max_epochs": 0, "max_hours": 1,
                                         "started_at": 0.0}, now=99999.0))
    check("V-CHAOS-8-BUDGET", d8.kind == rc.ESCALATE and "budget" in d8.reason,
          "a spent budget escalates with the gaps attached, and does not converge", d8.reason)

    # 9. nothing is running and the goal is not converged
    d9 = rc.decide(ctx(lg, repo, providers=()))
    check("V-CHAOS-9-EMPTY-QUEUE", d9.kind == rc.ESCALATE and d9.kind != rc.CONVERGED,
          "an empty queue with open gaps escalates; there is no path to CONVERGED",
          rc.render(d9))

    # 10. the provider says DONE and the goal is still open
    lg10 = goal(base, "c-10", repo)
    s10 = gc.project(lg10)
    e10 = ep.begin(lg10, s10, "gate", {}, "k10", "initial", "t")
    ep.mark_running(lg10, gc.project(lg10), e10.epoch_id, {"pid": 1}, "t")
    ep.end(lg10, gc.project(lg10), e10.epoch_id, ep.COMPLETED, "exit 0", "t")
    c10 = cv.goal_closure(gc.project(lg10), gs.tree_id(repo, ["."]))
    check("V-CHAOS-10-DONE-IS-NOT-CONVERGED", not c10.may_close,
          "an epoch reporting COMPLETED leaves the goal blocked on its obligations",
          f"closure said may_close with blocking={c10.blocking}")

    # 11. every implementation obligation is proven and the harvest is still open
    lg11 = goal(base, "c-11", repo, harvest_open=True)
    c11 = cv.goal_closure(gc.project(lg11), gs.tree_id(repo, ["."]))
    check("V-CHAOS-11-HARVEST-OPEN",
          not c11.may_close and any("UCR_CIF_LEARNING" in b or "ucr" in b
                                    for b in c11.blocking),
          "implementation complete with the learning plane open does not close",
          f"blocking={c11.blocking}")

    # 12. cold birth: the host store is destroyed and restored from a checkpoint
    goals_env = Path(tempfile.mkdtemp(prefix="gsdx_chaos_cold_"))
    env = {**ENV, "GSDX_GOALS_ROOT": str(goals_env)}
    G = ["--goal", "g-cold", "--root", str(repo)]

    def cli(*a):
        return subprocess.run([sys.executable, str(CLI), *a], capture_output=True,
                              text=True, env=env, timeout=300)

    cli("declare", *G, "--intent", "survive a cold birth", "--scope-path", ".")
    for plane in ("OUTCOME", "EVIDENCE", "FAILURE", "REGRESSION", "UCR_CIF_LEARNING"):
        cli("plane", *G, "--plane", plane)
    cli("oblige", *G, "--id", "ob-1", "--plane", "OUTCOME", "--text", "x",
        "--gate", f'"{sys.executable}" gate.py', "--gate-file", "gate.py")
    export = Path(tempfile.mkdtemp(prefix="gsdx_chaos_exp_")) / "cold.json"
    cli("export", *G, "--to", str(export))
    before = cli("status", *G, "--json").stdout
    store = gl.GoalLog(gl.repo_id(repo), "g-cold", base=goals_env).dir
    for f in store.iterdir():
        f.unlink()
    gone = cli("status", *G, "--json")
    check("V-CHAOS-12-DESTROYED-IS-NOT-EMPTY", gone.returncode == 2,
          "a destroyed store refuses rather than reporting a goal with no history",
          f"rc={gone.returncode} {gone.stdout[:160]}")
    cli("restore", *G, "--from", str(export))
    after = cli("status", *G, "--json").stdout
    check("V-CHAOS-12-COLD-BIRTH",
          json.loads(before)["revision"] == json.loads(after)["revision"]
          and json.loads(before)["blocking"] == json.loads(after)["blocking"],
          "the goal is reconstructed from its checkpoint with the same revision and gaps",
          f"before={before[:120]} after={after[:120]}")

    # 13. a fresh PROCESS reaches the same decision from durable state alone
    first = cli("reconcile", *G).stdout.strip().splitlines()[0]
    second = subprocess.run([sys.executable, str(CLI), "reconcile", *G],
                            capture_output=True, text=True, env=env,
                            timeout=300).stdout.strip().splitlines()[0]
    check("V-CHAOS-13-RESTART-SAME-DECISION", first == second and first.startswith("NEXT_EPOCH"),
          f"a new process re-reads the store and decides the same thing ({first[:60]})",
          f"{first!r} vs {second!r}")

    total = len(passes) + len(fails)
    print(f"\nGSDX_GOAL_CHAOS_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
