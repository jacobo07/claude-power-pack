"""S4: the receipt-gated succession transaction (econ-succession plan sections 4 and 5).

One OWNER_APPROVED receipt becomes, without the Owner doing anything else: the programme applied, the
predecessor lease closed, the successor lease opened, the predecessor session fenced, a continuation card
written and the successor launched. The transaction is a journalled state machine keyed by the receipt id;
every step is recorded after it takes effect, so a rerun after a crash replays from the journal and each
effect happens once.

Relation to GoalLedger's automatic succession (3c98097b): this EXTENDS it. The lease itself is opened through
`GoalLedger.lease_open` (one CAS, one idempotency key, one envelope check, shared with `_auto_succeed`); this
module never reimplements it. The auto path is the policy path (no receipt, inside an existing programme);
this path is the capital path (a receipt first raises the programme). Both are CAS-guarded on the latest
lease, so they cannot open two successors for one predecessor.

The launcher is injected: `launcher(goal, lease, continuation_path, key) -> {"ok": bool, ...}` and must be
idempotent by `key` (gsd_mission arm is). A crash between the launch and its journal row relaunches with the
same key, which the launcher collapses.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from . import capital_authority as ca

STEPS = ["REVALIDATED", "APPLIED", "PREDECESSOR_CLOSED", "L2_OPENED", "DETACHED", "CONTINUATION", "LAUNCHED",
         "RELEASED"]
LOCK_STALE_S = 300.0


def _journal(root) -> Path:
    return ca.capital_root(root) / "succession.jsonl"


def _rows(root, rid: str) -> list[dict]:
    p = _journal(root)
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("receipt") == rid:
            out.append(r)
    return out


def _append(root, rid: str, goal: str, step: str, **data) -> dict:
    p = _journal(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    row = {"ts": time.time(), "receipt": rid, "goal": goal, "step": step, **data}
    with open(p, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    return row


class _Lock:
    """One runner per receipt. A lock older than LOCK_STALE_S belongs to a dead runner."""

    def __init__(self, root, rid: str):
        self.path = ca.capital_root(root) / "succession" / rid / "run.lock"

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(2):
            try:
                os.close(os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
                return self
            except FileExistsError:
                if time.time() - self.path.stat().st_mtime < LOCK_STALE_S:
                    raise
                self.path.unlink(missing_ok=True)
        raise FileExistsError(str(self.path))

    def __exit__(self, *exc):
        self.path.unlink(missing_ok=True)
        return False


def _fail(root, rid, goal, state, reason, **data) -> dict:
    _append(root, rid, goal, state, reason=reason, **data)
    return {"ok": False, "state": state, "reason": reason, "receipt": rid}


def run(packet_path, goal: str, ledger_factory, launcher, predecessor_sid: str, root=None,
        after_step=None, now: float | None = None) -> dict:
    """Run (or resume) the succession for the receipt on `packet_path`. Idempotent; never raises on a refusal."""
    sha = ca.packet_sha(packet_path)
    rec = next((r for r in ca.receipts(root) if r.get("goal") == goal and r.get("sha") == sha), None)
    if rec is None:
        return {"ok": False, "state": "REJECTED", "receipt": None,
                "reason": f"no OWNER_APPROVED receipt for goal {goal!r} on this packet"}
    rid = rec["id"]
    try:
        with _Lock(root, rid):
            return _run_locked(packet_path, goal, ledger_factory, launcher, predecessor_sid, root, after_step,
                               now, rec, rid, sha)
    except FileExistsError:
        return {"ok": False, "state": "BUSY", "receipt": rid, "reason": "another runner holds this receipt"}


def _run_locked(packet_path, goal, ledger_factory, launcher, predecessor_sid, root, after_step, now, rec, rid, sha):
    rows = _rows(root, rid)
    done = {r["step"]: r for r in rows if r["step"] in STEPS}
    if "RELEASED" in done:
        return {"ok": True, "state": "RELEASED", "receipt": rid, "lease": done["L2_OPENED"].get("lease"),
                "reason": ""}

    def mark(step, **data):
        done[step] = _append(root, rid, goal, step, **data)
        if after_step:
            after_step(step)

    all_rows = ca._rows(root)
    if "REVALIDATED" not in done:
        if any(r.get("goal") == goal and r.get("state") == "REVOKED" for r in all_rows) \
                or ca._finalized(all_rows, sha, goal):
            return _fail(root, rid, goal, "REJECTED", "receipt revoked or packet invalidated")
        mark("REVALIDATED")
    led = ledger_factory(goal)
    if "APPLIED" not in done:
        out = ca.apply_receipt(packet_path, goal, ledger_factory, now=now, root=root)
        if not out.get("ok"):
            return _fail(root, rid, goal, "FAILED_SAFE", f"apply: {out.get('reason')}")
        mark("APPLIED")
    if "PREDECESSOR_CLOSED" not in done:
        pred = led._gfold(led._read())["leases"][-1]["id"]
        led.lease_close(pred, f"succession:{rid}", receipt=rid)
        mark("PREDECESSOR_CLOSED", predecessor=pred)
    pred = done["PREDECESSOR_CLOSED"]["predecessor"]
    if "L2_OPENED" not in done:
        g = led._gfold(led._read())
        cap = int(led._executable(g))
        if cap <= 0:
            return _fail(root, rid, goal, "FAILED_SAFE", f"no executable programme left for a successor ({cap})")
        out = led.lease_open(rid, cap, prev_lease=pred)
        if not out.get("ok"):
            return _fail(root, rid, goal, "FAILED_SAFE", f"lease_open: {out.get('reason')}")
        mark("L2_OPENED", lease=out["lease"], cap=cap)
    lease = done["L2_OPENED"]["lease"]
    if "DETACHED" not in done:
        led.tombstone(predecessor_sid, f"succession:{rid}")
        mark("DETACHED", sid=predecessor_sid)
    cont = ca.capital_root(root) / "succession" / rid / "continuation.json"
    if "CONTINUATION" not in done:
        cont.parent.mkdir(parents=True, exist_ok=True)
        cont.write_text(json.dumps({"goal": goal, "lease": lease, "receipt": rid, "packet_sha": sha,
                                    "predecessor": pred, "predecessor_sid": predecessor_sid,
                                    "ceiling": rec["ceiling"], "scope": rec["scope"],
                                    "excluded": rec["excluded"], "stop_loss": rec["stop_loss"]},
                                   indent=1, sort_keys=True), encoding="utf-8")
        mark("CONTINUATION", path=str(cont))
    if "LAUNCHED" not in done:
        res = launcher(goal, lease, str(cont), rid)
        if not (res or {}).get("ok"):
            return _fail(root, rid, goal, "FAILED_SAFE", f"launch: {(res or {}).get('reason', 'refused')}")
        mark("LAUNCHED")
    mark("RELEASED")
    return {"ok": True, "state": "RELEASED", "receipt": rid, "lease": lease, "reason": ""}
