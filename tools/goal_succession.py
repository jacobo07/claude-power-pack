"""Terminal reconciliation + atomic succession for a dgl goal (W3).

A lease ends in a worker that stopped; this module decides, once and atomically, what happens next.

  reconcile(sid, dead, measured)  TERMINAL_PROVEN only when the caller passes a process-proven `dead` AND a
                                  measured spend: the ledger settles at that value and every hold closes.
                                  Anything else is UNKNOWN_RESERVED: the hold stays reserved, a first-seen
                                  time is journalled, nothing is freed. Unknown is never free.
  sweep_unknown(sid, measured)    after the TTL a held sid converts to SWEPT_MEASURED, and only by a measured
                                  value; a TTL with no measurement keeps the hold.
  succeed(...)                    settle the dead holder -> close the previous lease -> open the successor
                                  (CAS on prev_lease) -> claim the workspace at gen+1. Idempotent by
                                  succession_id, resumable after a crash between sub-steps, and refusals
                                  (UNKNOWN_RESERVED, AUTHORITY_REQUIRED, CAS_LOST, CLAIM_LOST) are returned.

Placed beside the ledger, not inside it: the ledger stays a pure fold of spend, this module owns the
cross-journal order (ledger, then workspace registry) and the per-succession journal
<goal-budget>/<goal>/succession.journal.jsonl (append-only, deduped by key).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from modules.lease.store import Exclusive, fsync_dir  # noqa: E402
from modules.provider_routing.ledger import GoalLedger  # noqa: E402
from modules.provider_routing.workspace_registry import WorkspaceRegistry  # noqa: E402

JOURNAL = "succession.journal.jsonl"
DEFAULT_UNKNOWN_TTL_S = 1800
FAULT_EXIT = 97
UNKNOWN = "UNKNOWN_RESERVED"


def _fault(point: str) -> None:
    """Crash injection for the resume gate: the process dies exactly at `point`, no unwinding."""
    if os.environ.get("GOAL_SUCCESSION_FAULT") == point:
        os._exit(FAULT_EXIT)


def _goal_root() -> Path:
    from mission_spend import goal_root
    return goal_root()


class _Journal:
    def __init__(self, goal_dir: Path):
        goal_dir.mkdir(parents=True, exist_ok=True)
        self.dir = goal_dir
        self.path = goal_dir / JOURNAL
        self._lock = Exclusive(goal_dir / "succession.lock", 10.0)

    def _rows(self) -> list[dict]:
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_bytes().split(b"\n"):
            if line.strip():
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue                       # torn tail: never acked
        return out

    def note(self, op: str, key: str, **data) -> dict:
        """Append (op, key) once; a repeat returns the first row and writes nothing."""
        with self._lock:
            rows = self._rows()
            for r in rows:
                if r["op"] == op and r["key"] == key:
                    return r
            rec = {"seq": len(rows) + 1, "ts": time.time(), "op": op, "key": key, **data}
            with open(self.path, "ab") as fh:
                fh.write(json.dumps(rec, sort_keys=True).encode("utf-8") + b"\n")
                fh.flush()
                os.fsync(fh.fileno())
            fsync_dir(self.dir)
            return rec

    def first(self, op: str, key: str) -> dict | None:
        with self._lock:
            return next((r for r in self._rows() if r["op"] == op and r["key"] == key), None)


def _ledger(root: Path, goal: str) -> GoalLedger:
    return GoalLedger(root / goal, goal)


def reconcile(root, goal: str, sid: str, *, dead: bool, measured: int | None, now: float | None = None,
              ttl: int = DEFAULT_UNKNOWN_TTL_S) -> dict:
    root, now = Path(root), time.time() if now is None else now
    jr = _Journal(root / goal)
    if dead is True and isinstance(measured, int) and not isinstance(measured, bool) and measured >= 0:
        _ledger(root, goal).settle_stopped(sid, measured, "terminal_proven")
        jr.note("terminal", sid, measured=measured)
        return {"state": "TERMINAL_PROVEN", "sid": sid, "measured": measured}
    row = jr.note("unknown", sid, at=now)
    return {"state": UNKNOWN, "sid": sid, "since": row["at"], "ttl": ttl,
            "reason": "no process-proven death with a measured spend: the hold stays reserved"}


def sweep_unknown(root, goal: str, sid: str, *, measured: int | None, now: float | None = None,
                  ttl: int = DEFAULT_UNKNOWN_TTL_S) -> dict:
    """Past the TTL a held sid converts, but only by a measured value; a clock alone frees nothing."""
    root, now = Path(root), time.time() if now is None else now
    jr = _Journal(root / goal)
    row = jr.first("unknown", sid) or jr.note("unknown", sid, at=now)
    if (now - row["at"]) < ttl or measured is None:
        return {"state": UNKNOWN, "sid": sid, "since": row["at"], "ttl": ttl,
                "reason": "inside the TTL or no measured value: the hold stays reserved"}
    booked = int(measured or 0)
    _ledger(root, goal).settle_stopped(sid, booked, "ttl_sweep_measured")
    jr.note("swept", sid, measured=booked)
    return {"state": "SWEPT_MEASURED", "sid": sid, "measured": booked}


# --- succession ---------------------------------------------------------------------------------------

def _refuse(status: str, reason: str, **extra) -> dict:
    return {"ok": False, "status": status, "applied": False, "reason": reason, **extra}


def _lease_status(res: dict) -> str:
    reason = res.get("reason", "")
    if "AUTHORITY_REQUIRED" in reason:
        return "AUTHORITY_REQUIRED"
    return "CAS_LOST" if reason.startswith("CAS") else "REFUSED"


def _step_settle(c: dict) -> dict | None:
    if c["done"] or not c["old_sid"]:
        return None
    rec = reconcile(c["root"], c["goal"], c["old_sid"], dead=c["dead"], measured=c["measured"],
                    now=c["now"], ttl=c["ttl"])
    if rec["state"] == UNKNOWN:
        rec = sweep_unknown(c["root"], c["goal"], c["old_sid"], measured=c["measured"], now=c["now"], ttl=c["ttl"])
    c["reconcile"] = rec
    if rec["state"] == UNKNOWN:
        return _refuse(UNKNOWN, rec["reason"], reconcile=rec)
    c["jr"].note("step", f"{c['succession_id']}:settled", state=rec["state"])
    return None


def _step_close(c: dict) -> dict | None:
    if c["done"]:
        return None
    led, prev = c["led"], c["prev_lease"]
    latest = led.lineage()["leases"][-1]
    if prev != latest["id"]:
        return _refuse("CAS_LOST", f"CAS: {prev} is not the latest lease; {latest['id']} "
                       f"(succession {latest['succession_id']}) won")
    # Check the envelope BEFORE closing: a refused succession leaves the old holder's lease open.
    ps = led.programme_status()
    held = 0 if latest["closed"] else sum(latest["reserves"].values())
    need = c["cap"] + sum(c["reserves"].values())
    if ps["executable"] is None or need > ps["executable"] + held:
        res = led.lease_open(c["succession_id"], c["cap"], prev_lease=prev, reserves=c["reserves"])
        if res["ok"]:
            c["done"] = next(x for x in res["leases"] if x["succession_id"] == c["succession_id"])
            c["applied"] = res["applied"]
            return None
        return _refuse(_lease_status(res), res["reason"], need=res.get("need"), executable=res.get("executable"))
    led.lease_close(prev, "succeeded", c["succession_id"])
    c["jr"].note("step", f"{c['succession_id']}:closed", lease=prev)
    _fault("after_close")
    return None


def _step_open(c: dict) -> dict | None:
    if c["done"]:
        return None
    res = c["led"].lease_open(c["succession_id"], c["cap"], prev_lease=c["prev_lease"], reserves=c["reserves"])
    if not res["ok"]:
        return _refuse(_lease_status(res), res["reason"], need=res.get("need"), executable=res.get("executable"))
    c["lease"], c["applied"] = res["lease"], c["applied"] or res["applied"]
    c["jr"].note("step", f"{c['succession_id']}:opened", lease=c["lease"])
    _fault("after_open")
    return None


def _step_claim(c: dict) -> dict | None:
    lease = c["lease"] or c["predicted"]
    res = c["reg"].claim(c["workspace"], c["goal"], lease, c["expect_gen"], holder_sid=c["new_sid"])
    if not res["ok"]:
        return _refuse("CLAIM_LOST", res["reason"], lease=lease, winner=res.get("winner"))
    c["gen"], c["applied"] = res["gen"], c["applied"] or res["applied"]
    c["jr"].note("step", f"{c['succession_id']}:claimed", lease=lease, gen=res["gen"], holder_sid=c["new_sid"])
    return None


STEPS = ("settle", "close", "open", "claim")
HANDLERS = {"settle": _step_settle, "close": _step_close, "open": _step_open, "claim": _step_claim}


def succeed(goal: str, succession_id: str, prev_lease: str, cap: int, reserves: dict | None, workspace: str,
            expect_gen: int, new_sid: str, *, root=None, old_sid: str | None = None, dead: bool = False,
            measured: int | None = None, now: float | None = None, ttl: int = DEFAULT_UNKNOWN_TTL_S) -> dict:
    root = Path(root) if root else _goal_root()
    led = _ledger(root, goal)
    leases = led.lineage()["leases"]
    done = next((x for x in leases if x["succession_id"] == succession_id), None)
    c = {"root": root, "goal": goal, "succession_id": succession_id, "prev_lease": prev_lease, "cap": cap,
         "reserves": dict(reserves or {}), "workspace": workspace, "expect_gen": expect_gen, "new_sid": new_sid,
         "old_sid": old_sid, "dead": dead, "measured": measured, "now": time.time() if now is None else now,
         "ttl": ttl, "led": led, "reg": WorkspaceRegistry(root), "jr": _Journal(root / goal), "done": done,
         "lease": done["id"] if done else None, "predicted": f"L{len(leases) + 1}", "applied": False,
         "gen": None, "reconcile": None}
    for step in STEPS:
        refusal = HANDLERS[step](c)
        if refusal:
            return refusal
    c["jr"].note("done", succession_id, lease=c["lease"], gen=c["gen"])
    return {"ok": True, "status": "SUCCEEDED", "applied": c["applied"], "lease": c["lease"], "gen": c["gen"],
            "reconcile": c["reconcile"], "reason": ""}


# --- CLI ----------------------------------------------------------------------------------------------

def _parse_reserves(items: list[str]) -> dict:
    out = {}
    for it in items or []:
        k, _, v = it.partition("=")
        out[k] = int(v)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="goal_succession")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("succeed")
    s.add_argument("--goal", required=True)
    s.add_argument("--succession-id", required=True)
    s.add_argument("--prev-lease", required=True)
    s.add_argument("--cap", type=int, required=True)
    s.add_argument("--reserve", action="append", default=[])
    s.add_argument("--workspace", required=True)
    s.add_argument("--expect-gen", type=int, required=True)
    s.add_argument("--new-sid", required=True)
    s.add_argument("--old-sid")
    s.add_argument("--dead", action="store_true")
    s.add_argument("--measured", type=int)
    s.add_argument("--ttl", type=int, default=DEFAULT_UNKNOWN_TTL_S)
    r = sub.add_parser("reconcile")
    r.add_argument("--goal", required=True)
    r.add_argument("--sid", required=True)
    r.add_argument("--dead", action="store_true")
    r.add_argument("--measured", type=int)
    r.add_argument("--ttl", type=int, default=DEFAULT_UNKNOWN_TTL_S)
    a = ap.parse_args(argv)
    if a.cmd == "succeed":
        out = succeed(a.goal, a.succession_id, a.prev_lease, a.cap, _parse_reserves(a.reserve), a.workspace,
                      a.expect_gen, a.new_sid, old_sid=a.old_sid, dead=a.dead, measured=a.measured, ttl=a.ttl)
        print(json.dumps(out, sort_keys=True))
        return 0 if out["ok"] else 3
    out = reconcile(_goal_root(), a.goal, a.sid, dead=a.dead, measured=a.measured, ttl=a.ttl)
    print(json.dumps(out, sort_keys=True))
    return 0 if out["state"] == "TERMINAL_PROVEN" else 3


if __name__ == "__main__":
    sys.exit(main())
