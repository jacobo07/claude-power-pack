#!/usr/bin/env python3
"""Phase 5 / 05-04 + 05-05: `review.received` and reviewer concurrency (D17).

A review receipt (genesis-review-v1, written by tools/evidence_bundle.py) becomes one goal event, or is refused
with a reason. Many reviewers may report at once: each attempt re-projects the log, a lost CAS race is retried
at most three times, and the ticket nonce is the idempotency key. Hermetic: temp HOME, temp goals root, temp
git repo for the evidence root.

Summary line: GSDX_REVIEW_PASS=n/m  threshold=n/m
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

_TMP_HOME = Path(tempfile.mkdtemp(prefix="rev-home-"))
_TMP_GOALS = Path(tempfile.mkdtemp(prefix="rev-goals-")) / "goals"
os.environ["HOME"] = str(_TMP_HOME)
os.environ["USERPROFILE"] = str(_TMP_HOME)
os.environ["GSDX_GOALS_ROOT"] = str(_TMP_GOALS)
os.environ.pop("GSDX_GOAL_EPOCH", None)

from modules.gsd_x.goal import contract as gc            # noqa: E402
from modules.gsd_x.goal import git_state as gs           # noqa: E402
from modules.gsd_x.goal import log as gl                 # noqa: E402
from modules.gsd_x.goal import proof as pf               # noqa: E402
import evidence_bundle as eb                             # noqa: E402

try:
    from modules.gsd_x.goal import review as rv          # noqa: E402
except ImportError:
    rv = None

REVIEWER = {"agent": "pp-code-reviewer", "model": "claude-sonnet-5", "effort": "default"}
OK_REPLY = "```json\n{\"findings\": []}\n```"
passes = 0
fails = 0


def check(gate: str, cond: bool, ev: str = "") -> None:
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}".rstrip())
    else:
        fails += 1
        print(f"FAIL {gate} {ev}".rstrip())


def run_gate(gate: str, fn) -> None:
    try:
        cond, ev = fn()
    except Exception as exc:  # noqa: BLE001 -- a raise is a FAIL line, the summary always prints
        check(gate, False, f"raised {type(exc).__name__}: {exc}")
        return
    check(gate, bool(cond), ev)


def need():
    return None if rv is not None else (False, "RED-first: modules.gsd_x.goal.review absent")


def _git(repo: Path, *args: str) -> None:
    rc_, out = gs._git(repo, *args)         # the goal package's own git resolution (git is not on PATH here)
    if rc_ != 0:
        raise RuntimeError(f"git {args[0]} failed: {out}")


class Rig:
    """A git repo as the evidence root, one declared goal, and a way to mint review receipts."""

    def __init__(self, name: str):
        self.root = Path(tempfile.mkdtemp(prefix="rev-repo-"))
        (self.root / "art.py").write_text("x = 1\n", encoding="utf-8", newline="\n")
        for a in (("init", "-q"), ("config", "user.name", "t"), ("config", "user.email", "t@t"),
                  ("config", "core.autocrlf", "false"), ("add", "-A"), ("commit", "-q", "-m", "base")):
            _git(self.root, *a)
        self.goal = name
        self.log = gl.GoalLog(gl.repo_id(self.root), name)
        gc.declare(self.log, "Review intake", ["reviewed"], [], {"paths": ["."]}, actor="founder")

    def receipt(self, task: str, reviewer: dict = REVIEWER, echo: bool = True) -> tuple[str, str]:
        _, nonce = eb.ticket(self.root, "plan", task, ["art.py"])
        reply = (eb.ticket_line(nonce) + "\n" if echo else "") + OK_REPLY
        rel, _ = eb.write_review(self.root, "plan", task, reply, reviewer, ["art.py"], [])
        return rel, nonce

    def receive(self, task: str, worker: str = "worker-7", **kw) -> dict:
        rel, nonce = self.receipt(task, **kw)
        return rv.receive(gl.GoalLog(gl.repo_id(self.root), self.goal), self.root, rel, nonce,
                          "claim-" + task, "snap:" + "1" * 40, worker, "reviewer")

    def received(self) -> list:
        return pf.project_proofs(gc.project(gl.GoalLog(gl.repo_id(self.root), self.goal))).received

    def close(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)


def gate_hermetic():
    return (Path.home() == _TMP_HOME and Path(os.environ["GSDX_GOALS_ROOT"]) == _TMP_GOALS,
            f"home={_TMP_HOME.name}")


def gate_recorded():
    n = need()
    if n:
        return n
    r = Rig("rev-ok")
    try:
        out = r.receive("t1")
        got = r.received()
        return (out["status"] == rv.RECORDED and len(got) == 1 and got[0]["data"]["ticket"]
                and got[0]["data"]["reviewer"]["agent"] == "pp-code-reviewer", f"{out} events={len(got)}")
    finally:
        r.close()


def gate_stale():
    n = need()
    if n:
        return n
    r = Rig("rev-stale")
    try:
        rel, nonce = r.receipt("t1")
        (r.root / "art.py").write_text("x = 2  # moved after the review\n", encoding="utf-8")
        out = rv.receive(gl.GoalLog(gl.repo_id(r.root), r.goal), r.root, rel, nonce, "c", "snap:" + "1" * 40,
                         "worker-7")
        return out["status"] == rv.REFUSED and "stale" in out["reason"] and not r.received(), out["reason"]
    finally:
        r.close()


def gate_reviewer_is_worker():
    n = need()
    if n:
        return n
    r = Rig("rev-self")
    try:
        out = r.receive("t1", worker="pp-code-reviewer")
        return out["status"] == rv.REFUSED and "worker" in out["reason"] and not r.received(), out["reason"]
    finally:
        r.close()


def gate_unbound_refused():
    n = need()
    if n:
        return n
    r = Rig("rev-unbound")
    try:
        out = r.receive("t1", echo=False)
        return out["status"] == rv.REFUSED and not r.received(), out["reason"]
    finally:
        r.close()


def gate_log_readable():
    n = need()
    if n:
        return n
    r = Rig("rev-read")
    try:
        r.receive("t1")
        s = gc.project(gl.GoalLog(gl.repo_id(r.root), r.goal))
        types = [e.type for e in s.events]
        return types[-1] == "review.received" and "review.received" in pf.NEW_TYPES, types[-2:]
    finally:
        r.close()


def gate_cli_round_trip():
    r = Rig("rev-cli")
    try:
        rel, nonce = r.receipt("t1")
        p = subprocess.run([sys.executable, str(ROOT / "tools" / "gsd_x_goal.py"), "review", "--goal", r.goal,
                            "--root", str(r.root), "--receipt", rel, "--ticket", nonce, "--claim-id", "c1",
                            "--candidate", "snap:" + "1" * 40, "--worker", "worker-7"],
                           capture_output=True, text=True, env=os.environ.copy(), timeout=120)
        out = json.loads(p.stdout) if p.stdout.strip().startswith("{") else {}
        return p.returncode == 0 and out.get("status") == "RECORDED" and len(r.received()) == 1, \
            f"rc={p.returncode} {out or p.stderr[-120:]}"
    finally:
        r.close()


def _threads(fns):
    out = [None] * len(fns)

    def run(i):
        try:
            out[i] = fns[i]()
        except Exception as exc:  # noqa: BLE001 -- recorded as the thread's result
            out[i] = {"status": "RAISED", "reason": f"{type(exc).__name__}: {exc}"}
    ts = [threading.Thread(target=run, args=(i,)) for i in range(len(fns))]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    return out


def gate_concurrent_all_land():
    n = need()
    if n:
        return n
    r = Rig("rev-conc")
    try:
        recs = [r.receipt(f"t{i}") for i in range(3)]
        outs = _threads([lambda rel=rel, nonce=nonce, i=i: rv.receive(
            gl.GoalLog(gl.repo_id(r.root), r.goal), r.root, rel, nonce, f"c{i}", "snap:" + "1" * 40,
            "worker-7") for i, (rel, nonce) in enumerate(recs)])
        got = r.received()
        seqs = sorted(e["seq"] for e in got)
        return (all(o["status"] == rv.RECORDED for o in outs) and len(got) == 3
                and seqs == list(range(seqs[0], seqs[0] + 3)),
                f"statuses={[o['status'] for o in outs]} attempts={[o.get('attempts') for o in outs]} seqs={seqs}")
    finally:
        r.close()


def gate_dup_ticket():
    n = need()
    if n:
        return n
    r = Rig("rev-dup")
    try:
        rel, nonce = r.receipt("t1")

        def go():
            return rv.receive(gl.GoalLog(gl.repo_id(r.root), r.goal), r.root, rel, nonce, "c", "snap:" + "1" * 40,
                              "worker-7")
        first = go()
        second = go()
        outs = _threads([go, go, go])
        got = r.received()
        return (first["status"] == rv.RECORDED and second["status"] == rv.DUPLICATE and len(got) == 1
                and all(o["status"] == rv.DUPLICATE for o in outs),
                f"first={first['status']} second={second['status']} later={[o['status'] for o in outs]} events={len(got)}")
    finally:
        r.close()


class AlwaysLost:
    """A log whose every append loses the race: the retry bound is observable and nothing is written."""

    def __init__(self, real):
        self.real, self.calls = real, 0

    def append(self, *a, **k):
        self.calls += 1
        raise gl.LostRace("synthetic: another writer always wins")

    def __getattr__(self, name):
        return getattr(self.real, name)


def gate_retry_bounded():
    n = need()
    if n:
        return n
    r = Rig("rev-bound")
    try:
        rel, nonce = r.receipt("t1")
        lost = AlwaysLost(gl.GoalLog(gl.repo_id(r.root), r.goal))
        out = rv.receive(lost, r.root, rel, nonce, "c", "snap:" + "1" * 40, "worker-7")
        return (out["status"] == rv.CONTENDED and lost.calls == rv.MAX_ATTEMPTS == 3 and not r.received(),
                f"{out['status']} append_calls={lost.calls}")
    finally:
        r.close()


def gate_cross_client():
    n = need()
    if n:
        return n
    r = Rig("rev-cross")
    try:
        rel_a, nonce_a = r.receipt("ta")
        rel_b, nonce_b = r.receipt("tb")
        procs = []

        def cli():
            p = subprocess.run([sys.executable, str(ROOT / "tools" / "gsd_x_goal.py"), "review", "--goal", r.goal,
                                "--root", str(r.root), "--receipt", rel_b, "--ticket", nonce_b, "--claim-id", "cb",
                                "--candidate", "snap:" + "1" * 40, "--worker", "worker-7"],
                               capture_output=True, text=True, env=os.environ.copy(), timeout=120)
            procs.append(p.returncode)
            return {"status": "RECORDED" if p.returncode == 0 else "CLI-FAILED", "reason": p.stderr[-100:]}

        def lib():
            return rv.receive(gl.GoalLog(gl.repo_id(r.root), r.goal), r.root, rel_a, nonce_a, "ca",
                              "snap:" + "1" * 40, "worker-7")
        outs = _threads([cli, lib])
        tickets = sorted(e["data"]["ticket"] for e in r.received())
        return (all(o["status"] == "RECORDED" for o in outs) and tickets == sorted([nonce_a, nonce_b]),
                f"statuses={[o['status'] for o in outs]} cli_rc={procs} events={len(tickets)}")
    finally:
        r.close()


def gate_distinct_nonces():
    r = Rig("rev-nonce")
    try:
        nonces = [r.receipt(f"t{i}")[1] for i in range(6)]
        return len(set(nonces)) == 6 and all(len(x) == 24 for x in nonces), f"{len(set(nonces))}/6 distinct"
    finally:
        r.close()


def main() -> int:
    for gate, fn in (("V-REV-HERMETIC-HOME", gate_hermetic),
                     ("V-REV-RECORDED", gate_recorded),
                     ("V-REV-STALE-REFUSED", gate_stale),
                     ("V-REV-REVIEWER-IS-WORKER-REFUSED", gate_reviewer_is_worker),
                     ("V-REV-UNBOUND-REFUSED", gate_unbound_refused),
                     ("V-REV-LOG-READABLE", gate_log_readable),
                     ("V-REV-CLI-ROUND-TRIP", gate_cli_round_trip),
                     ("V-REV-CONCURRENT-ALL-LAND", gate_concurrent_all_land),
                     ("V-REV-DUP-TICKET-IDEMPOTENT", gate_dup_ticket),
                     ("V-REV-RETRY-BOUNDED", gate_retry_bounded),
                     ("V-REV-CROSS-CLIENT", gate_cross_client),
                     ("V-REV-DISTINCT-NONCES", gate_distinct_nonces)):
        run_gate(gate, fn)
    total = passes + fails
    print(f"GSDX_REVIEW_PASS={passes}/{total}  threshold=12/12")
    return 0 if fails == 0 and passes == 12 else 1


if __name__ == "__main__":
    sys.exit(main())
