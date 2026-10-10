"""Workspace lease registry (dgl W2): who may spend from a workspace, fenced by generation.

A workspace (normalised cwd root) has at most one holder {goal, lease, gen, holder_sid}. The journal
`workspace.journal.jsonl` is append-only, one Exclusive lock, seq + fsync, the same idiom as GoalLedger.
It lives in the goal-budget root, NOT in a goal dir: one-holder-per-workspace needs a single journal
that every goal's claim contends on.

  claim(ws, goal, lease, expect_gen)  CAS on the generation; gen+1, holder replaced; a stale gen is
                                      refused naming the winner; idempotent by (ws, goal, lease, gen).
  holder / holder_for_cwd             read-only. Entering a directory observes, never binds or claims.
  authority / settle                  a lower gen, another goal/lease, or a closed lease is FENCED: the
                                      spend is still booked (settle_stopped), only the authority is revoked.
"""
from __future__ import annotations

import json
import os
import socket
import time
from pathlib import Path

from modules.lease.store import Exclusive, fsync_dir

JOURNAL = "workspace.journal.jsonl"


class RegistryError(Exception):
    pass


def norm(path: str) -> str:
    return os.path.normcase(os.path.abspath(path)).rstrip("\\/")


class WorkspaceRegistry:
    def __init__(self, root, *, clock=time.time):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.clock = clock
        self.journal = self.root / JOURNAL
        self._lock = Exclusive(self.root / "workspace.lock", 10.0)

    def _read(self) -> list[dict]:
        if not self.journal.exists():
            return []
        out = []
        for line in self.journal.read_bytes().split(b"\n"):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue                           # torn tail: never acked
            if rec.get("seq") != len(out) + 1:
                raise RegistryError(f"{self.journal}: seq gap at {rec.get('seq')}")
            out.append(rec)
        return out

    def _append(self, recs: list[dict], rec: dict) -> None:
        rec = {"seq": len(recs) + 1, "ts": self.clock(), "host": socket.gethostname(), **rec}
        prefix = b""
        if self.journal.exists() and self.journal.stat().st_size:
            with open(self.journal, "rb") as fh:
                fh.seek(-1, os.SEEK_END)
                prefix = b"" if fh.read(1) == b"\n" else b"\n"
        with open(self.journal, "ab") as fh:
            fh.write(prefix + json.dumps(rec, sort_keys=True).encode("utf-8") + b"\n")
            fh.flush()
            os.fsync(fh.fileno())
        fsync_dir(self.root)
        recs.append(rec)

    @staticmethod
    def _fold(recs: list[dict]) -> dict:
        cur: dict = {}
        for r in recs:
            if r["op"] == "claim":
                cur[r["workspace"]] = {k: r[k] for k in ("workspace", "goal", "lease", "gen", "holder_sid", "ts")}
        return cur

    def holder(self, workspace: str) -> dict | None:
        with self._lock:
            return self._fold(self._read()).get(norm(workspace))

    def holder_for_cwd(self, cwd: str | None) -> dict | None:
        """Read-only: the holder of the deepest claimed workspace containing `cwd`."""
        if not cwd or not self.journal.exists():
            return None
        c = norm(cwd)
        with self._lock:
            held = self._fold(self._read())
        hits = [h for ws, h in held.items() if c == ws or c.startswith(ws + os.sep)]
        return max(hits, key=lambda h: len(h["workspace"])) if hits else None

    def has_claims(self) -> bool:
        return self.journal.exists() and self.journal.stat().st_size > 0

    def claim(self, workspace: str, goal: str, lease: str, expect_gen: int, holder_sid: str = "") -> dict:
        if not (workspace and goal and lease) or not isinstance(expect_gen, int) or expect_gen < 0:
            raise RegistryError("claim needs a workspace, goal, lease and an int expect_gen >= 0")
        ws = norm(workspace)
        with self._lock:
            recs = self._read()
            cur = self._fold(recs).get(ws)
            gen = cur["gen"] if cur else 0
            if cur and gen == expect_gen + 1 and (cur["goal"], cur["lease"]) == (goal, lease):
                return {"ok": True, "applied": False, "gen": gen, "holder": cur, "reason": ""}
            if gen != expect_gen:
                return {"ok": False, "applied": False, "gen": gen, "winner": cur,
                        "reason": f"CAS: expected gen {expect_gen}, workspace is at gen {gen}, held by "
                                  f"{cur['goal'] if cur else 'nobody'} ({cur['lease'] if cur else '-'})"}
            self._append(recs, {"op": "claim", "workspace": ws, "goal": goal, "lease": lease,
                                "gen": gen + 1, "holder_sid": holder_sid})
            return {"ok": True, "applied": True, "gen": gen + 1, "holder": self._fold(recs)[ws], "reason": ""}

    def authority(self, workspace: str, goal: str, lease: str, gen: int, *, ledger=None) -> dict:
        cur = self.holder(workspace)
        if cur is None:
            return {"ok": False, "fenced": False, "reason": "no holder: the workspace was never claimed"}
        if gen != cur["gen"] or (cur["goal"], cur["lease"]) != (goal, lease):
            return {"ok": False, "fenced": True,
                    "reason": f"fenced: gen {gen} ({goal}/{lease}) is not the holder's gen {cur['gen']} "
                              f"({cur['goal']}/{cur['lease']})"}
        if ledger is not None:
            ls = next((x for x in ledger.lineage()["leases"] if x["id"] == lease), None)
            if ls is None or ls["closed"]:
                return {"ok": False, "fenced": True,
                        "reason": f"fenced: lease {lease} is {'unknown' if ls is None else 'closed'}"}
        return {"ok": True, "fenced": False, "reason": ""}

    def settle(self, ledger, workspace: str, goal: str, lease_id: str, *, gen: int, sid: str,
               measured: int, lease: int, per_call: int = 0) -> dict:
        """Renew under authority; without it, journal `fenced` and book the spend all the same."""
        a = self.authority(workspace, goal, lease_id, gen, ledger=ledger)
        if a["ok"]:
            out = ledger.renew(sid, measured, lease, per_call)
            return {**out, "fenced": False}
        if a["fenced"]:
            with self._lock:
                recs = self._read()
                self._append(recs, {"op": "fenced", "workspace": norm(workspace), "goal": goal, "lease": lease_id,
                                    "gen": gen, "sid": sid, "measured": measured, "reason": a["reason"]})
        out = ledger.settle_stopped(sid, measured, a["reason"])
        return {**out, "ok": False, "fenced": a["fenced"], "reason": a["reason"]}
