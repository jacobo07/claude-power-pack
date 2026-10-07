#!/usr/bin/env python3
"""V-CE-T1-WAIT-* gates: obligation C3 part 2 (COMPLETION-PLAN Master Done-Gate) -- WAITING with
zero hot sessions, and stale-pane revalidation. Driven through the REAL owners:
`wake_check.consume` (WAKE_FLAG -> one `wake` event on a gsd_x GoalLog -> receipt),
`rollover.claim` / `_holder_dead` (claim takeover), `modules.lease.LeaseStore` (lease expiry).

a. WAITING zero-hot: a declared goal with no live session (empty sessions dir, no claim). Writing the
   flag + one consume() appends exactly one `wake` event and a receipt while every process launcher
   is replaced by a recorder that must stay at 0 calls. Consuming again (flag retired) and replaying
   the same flag bytes (DUPLICATE) still leave one wake.
b. Control: no flag -> NO_FLAG, zero events, no receipt.
c. Stale pane: a claim whose holder is provably dead is taken over; a live holder's claim is
   refused; a claim whose lease ran out is taken over; an EXPIRED LeaseStore lease is never
   honoured as ACTIVE by check()/renew().
The real WAKE_FLAG.json and wake_receipts/ are fingerprinted and must not move (PP_WAKE_FLAG and
PP_WAKE_RECEIPTS point at a temp dir).

    python tools/test_ce_t1_waiting.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import rollover as ro                               # noqa: E402
import wake_check as wc                             # noqa: E402
from modules.gsd_x.goal import contract as gc       # noqa: E402
from modules.gsd_x.goal import log as gl            # noqa: E402
from modules.lease.store import ACTIVE, EXPIRED, LeaseStore  # noqa: E402

REPO_ID = "3d" * 20
passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"  PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"  FAIL {gate}: {ev}")


class Launcher:
    """Replaces every process-launch entry point; records argv instead of running anything."""
    NAMES = ("run", "Popen", "call", "check_call", "check_output")

    def __init__(self):
        self.calls: list = []
        self.saved: dict = {}

    def _rec(self, *a, **k):
        self.calls.append(a[0] if a else k.get("args"))
        raise RuntimeError("launcher recorder: no process may start here")

    def __enter__(self):
        for n in self.NAMES:
            self.saved[n] = getattr(subprocess, n)
            setattr(subprocess, n, self._rec)
        self.saved["system"] = os.system
        os.system = self._rec
        return self

    def __exit__(self, *exc):
        for n in self.NAMES:
            setattr(subprocess, n, self.saved[n])
        os.system = self.saved["system"]
        return False


def make_goal(base: Path, gid: str) -> gl.GoalLog:
    lg = gl.GoalLog(REPO_ID, gid, base=base)
    gc.declare(lg, "waiting goal %s" % gid, ["the wake is acted on"], [], {"paths": ["."]})
    return lg


def wakes(lg: gl.GoalLog) -> list:
    return [e for e in lg.read() if e.type == "wake"]


def live_fp() -> tuple:
    flag = wc.FLAG.read_bytes() if wc.FLAG.is_file() else None
    rec = sorted(p.name for p in wc.RECEIPTS.iterdir()) if wc.RECEIPTS.is_dir() else None
    return flag, rec


class Clock:
    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t


def main() -> int:
    before = live_fp()
    tmp = Path(tempfile.mkdtemp(prefix="ce_t1_wait_"))
    saved_env = {k: os.environ.get(k) for k in ("PP_WAKE_FLAG", "PP_WAKE_RECEIPTS", "CPP_CLAUDE_SESSIONS_DIR")}
    flag, rdir, sessions = tmp / "WAKE_FLAG.json", tmp / "receipts", tmp / "sessions"
    sessions.mkdir()
    os.environ.update(PP_WAKE_FLAG=str(flag), PP_WAKE_RECEIPTS=str(rdir), CPP_CLAUDE_SESSIONS_DIR=str(sessions))
    try:
        base = tmp / "goals"

        print("C3 control: the launcher recorder can see a launch")
        with Launcher() as probe:
            try:
                subprocess.run(["claude", "--probe"])
            except RuntimeError:
                pass
        check("V-CE-T1-WAIT-RECORDER-LIVE", len(probe.calls) == 1, f"recorded={probe.calls}")

        print("C3 b: no flag -> zero events")
        lc = make_goal(base, "no-flag")
        n0 = len(lc.read())
        with Launcher() as la:
            r = wc.consume(lc)
        check("V-CE-T1-WAIT-NO-FLAG", r["outcome"] == "NO_FLAG" and len(lc.read()) == n0 and not wakes(lc)
              and not rdir.exists() and not la.calls, f"outcome={r['outcome']} events={len(lc.read())}/{n0}")

        print("C3 a: WAITING with zero hot sessions -> one wake, zero model calls")
        lg = make_goal(base, "waiting")
        no_hot = not any(sessions.iterdir()) and ro.read_claim("waiting-goal", tmp / "state") is None
        raw = json.dumps({"wake": True, "reason": "MATERIAL_RISE", "gate_exit": 1, "model_calls": 0,
                          "at": datetime.now(timezone.utc).isoformat()}, indent=1).encode("utf-8")
        flag.write_bytes(raw)
        with Launcher() as la:
            r1 = wc.consume(lg)
        w1 = wakes(lg)
        rec = json.loads(Path(r1["receipt"]).read_text(encoding="utf-8")) if r1.get("receipt") else {}
        check("V-CE-T1-WAIT-ZERO-HOT", no_hot and r1["outcome"] == "MOVED" and len(w1) == 1
              and w1[0].data.get("reason") == "MATERIAL_RISE" and rec.get("event_digest") == w1[0].digest
              and not flag.exists() and la.calls == [],
              f"no_hot={no_hot} outcome={r1['outcome']} wakes={len(w1)} receipt={Path(r1.get('receipt', '')).name} "
              f"launches={len(la.calls)}")
        with Launcher() as la:
            r2 = wc.consume(lg)
            flag.write_bytes(raw)                       # the same flag replayed
            r3 = wc.consume(lg)
        check("V-CE-T1-WAIT-IDEMPOTENT", r2["outcome"] == "NO_FLAG" and r3["outcome"] == "DUPLICATE"
              and len(wakes(lg)) == 1 and la.calls == [],
              f"second={r2['outcome']} replay={r3['outcome']} wakes={len(wakes(lg))} launches={len(la.calls)}")
        try:
            gc.project(lg)
            ok, why = True, "contract.project reads the goal with the wake event"
        except Exception as exc:                        # the owner's projection must tolerate the event
            ok, why = False, f"{type(exc).__name__}: {exc}"
        check("V-CE-T1-WAIT-PROJECT", ok, why)

        print("C3 c: stale-pane revalidation")
        state = tmp / "state"
        dead_host = {"pid": "424242"}
        ro.claim("pane-dead", "pane-A", state, host=dead_host, now=1000.0)
        hd = ro._holder_dead(dead_host, alive=lambda pid: False)
        t = ro.claim("pane-dead", "pane-B", state, host={"pid": "1"}, now=1001.0, alive=lambda pid: False)
        check("V-CE-T1-WAIT-DEAD-HOLDER-TAKEABLE", hd is True and t["claimed"] and t.get("took_over_from") == "pane-A"
              and t.get("generation") == 2 and t.get("takeover_reason") == "holder process is gone",
              f"_holder_dead={hd} claim={t}")
        ro.claim("pane-live", "pane-A", state, host={"pid": "434343"}, now=1000.0)
        hl = ro._holder_dead({"pid": "434343"}, alive=lambda pid: True)
        t = ro.claim("pane-live", "pane-B", state, now=1001.0, alive=lambda pid: True)
        cur = ro.read_claim("pane-live", state)
        check("V-CE-T1-WAIT-LIVE-HOLDER-REFUSED", hl is not True and not t["claimed"] and t["holder"] == "pane-A"
              and cur["claimant"] == "pane-A", f"_holder_dead={hl} claim={t}")
        t = ro.claim("pane-live", "pane-B", state, now=1000.0 + ro.CLAIM_LEASE_S + 1, alive=lambda pid: True)
        check("V-CE-T1-WAIT-CLAIM-LEASE-EXPIRED", t["claimed"] and t.get("took_over_from") == "pane-A"
              and str(t.get("takeover_reason", "")).startswith("lease expired"), f"claim={t}")

        clk = Clock()
        ls = LeaseStore(tmp / "lease", min_ttl_s=1, clock=clk)
        g = ls.acquire(["pane"], "pane-A", 10, "L1")
        d = ls.dispatch("L1", "pane-A", g.fences)
        live = ls.check("pane", g.fences["pane"])
        clk.t += 11
        dead = ls.check("pane", g.fences["pane"])
        renew = ls.renew("L1", "pane-A", g.fences)
        st = ls.snapshot()["leases"]["L1"]["state"]
        take = ls.acquire(["pane"], "pane-B", 10, "L2")
        check("V-CE-T1-WAIT-EXPIRED-NOT-ACTIVE", d.ok and d.state == ACTIVE and live.ok and not dead.ok
              and not renew.ok and st == EXPIRED and take.ok,
              f"before={live.ok} after={dead.ok}/{dead.reason} renew={renew.reason} state={st} next={take.ok}")
    finally:
        for k, v in saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)
    check("V-CE-T1-WAIT-LIVE-UNTOUCHED", live_fp() == before, "real WAKE_FLAG.json + wake_receipts/ unchanged")
    print(f"CE_T1_WAIT_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
