#!/usr/bin/env python3
"""Wait for a mission below the model boundary (spec law 6): zero model calls, one poll loop.

    mission_wait.py --mission M [--timeout S] [--guard-renewals] [--poll S] [--out FILE]

Polls the mission record every 20 s and exits on COMPLETED / HALTED / BLOCKED, an owner hold, or a
worker that is gone while the packet's done_gate passes. With --guard-renewals every record renewed
from M is held and its worker stopped (a finished packet must not be re-run by a renewal). Prints the
measured spend, the state and the last ledger rows, and writes the same as JSON next to the record
(`gsd-mission-wait-<M>.json`, or --out). Runnable detached: `nohup python3 tools/mission_wait.py ... &`.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gsd_long_run as lr  # noqa: E402
import gsd_mission as gm  # noqa: E402
import mission_spend as ms  # noqa: E402

POLL_S = 20
TIMEOUT_S = 6 * 3600


def _stop(rec: dict, stop_runner) -> bool:
    sid = ((rec.get("owner") or {}).get("session_id") or (rec.get("pending") or {}).get("bg_id") or "")
    if not sid:
        return False
    run = stop_runner or (lambda a: subprocess.run(a, capture_output=True, timeout=120))
    try:
        run([os.environ.get("CPP_CLAUDE_EXE") or "claude", "stop", sid])
        return True
    except Exception:  # noqa: BLE001 -- the hold already stands; the stop is best effort and ledgered below
        return False


def guard_renewals(mission_id: str, seen: set, *, stop_runner=None) -> list[str]:
    """Hold and stop every record renewed from `mission_id` (transitively); returns the ids newly guarded."""
    guarded = []
    parents = {mission_id}
    changed = True
    while changed:
        changed = False
        for rec in gm.all_missions():
            if rec.get("renewed_from") in parents and rec["mission_id"] not in parents:
                parents.add(rec["mission_id"])
                changed = True
    for mid in sorted(parents - {mission_id}):
        rec = gm.load(mid)
        if rec is None or mid in seen:
            continue
        seen.add(mid)
        if rec["state"] not in gm.TERMINAL and not rec.get("owner_hold"):
            gm.set_owner_hold(mid, f"mission_wait: renewal of {mission_id} guarded")
        stopped = _stop(rec, stop_runner) if rec["state"] not in gm.TERMINAL else False
        lr.ledger_append(mid, "renewal_guarded", mission_id=mid, renewed_from=mission_id, stopped=stopped)
        guarded.append(mid)
    return guarded


def check(mission_id: str, now: float, *, pid_alive=None, gate_runner=None) -> tuple[str | None, dict | None]:
    """The reason to stop waiting, or None. `gate` carries the packet gate result when it decided."""
    rec = gm.load(mission_id)
    if rec is None:
        return "MISSING", None
    if rec["state"] in (gm.COMPLETED, gm.HALTED):
        return rec["state"], None
    if rec["state"] == gm.BLOCKED:
        return "BLOCKED", None
    if rec.get("owner_hold"):
        return "OWNER_HOLD", None
    owner = rec.get("owner") or {}
    alive = (pid_alive or lr._pid_alive)(owner.get("pid")) if owner.get("pid") else None
    if alive is False and rec["state"] in (gm.RUNNING, gm.LAUNCHING):
        gate = gm.packet_gate_passed(rec, now, gate_runner=gate_runner)
        if gate:
            return "WORKER_GONE_GATE_PASSED", gate
    return None, None


def report(mission_id: str, reason: str, gate: dict | None, guarded: list[str], measure=None) -> dict:
    rec = gm.load(mission_id) or {}
    try:
        spent = (measure or ms.processed_tokens)(rec) if rec else None
    except Exception:  # noqa: BLE001 -- unmeasurable is None, never zero
        spent = None
    rows = [{k: e.get(k) for k in ("event", "epoch", "reason", "gate", "why") if e.get(k) is not None}
            for e in lr.ledger_events(mission_id)[-8:]]
    return {"mission": mission_id, "reason": reason, "state": rec.get("state"), "epoch": rec.get("epoch"),
            "processed_tokens": spent, "token_estimate": rec.get("token_estimate"), "gate": gate,
            "guarded_renewals": guarded, "last_ledger": rows, "at": time.time()}


def wait(mission_id: str, *, timeout: float = TIMEOUT_S, poll: float = POLL_S, guard: bool = False,
         pid_alive=None, gate_runner=None, stop_runner=None, measure=None, sleep=time.sleep,
         clock=time.time) -> dict:
    deadline = clock() + timeout
    seen: set = set()
    guarded: list[str] = []
    while True:
        if guard:
            guarded += guard_renewals(mission_id, seen, stop_runner=stop_runner)
        reason, gate = check(mission_id, clock(), pid_alive=pid_alive, gate_runner=gate_runner)
        if reason:
            return report(mission_id, reason, gate, guarded, measure)
        if clock() >= deadline:
            return report(mission_id, "TIMEOUT", None, guarded, measure)
        sleep(poll)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--mission", required=True)
    ap.add_argument("--timeout", type=float, default=TIMEOUT_S)
    ap.add_argument("--poll", type=float, default=POLL_S)
    ap.add_argument("--guard-renewals", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    res = wait(a.mission, timeout=a.timeout, poll=a.poll, guard=a.guard_renewals)
    out = Path(a.out) if a.out else gm.mission_path(a.mission).with_name(f"gsd-mission-wait-{a.mission}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))
    print(f"RESULT {out}")
    return 0 if res["reason"] in ("COMPLETED", "WORKER_GONE_GATE_PASSED") else 1


if __name__ == "__main__":
    sys.exit(main())
