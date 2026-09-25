"""One account-wide spend ledger: reserve before the effect, commit or release after.

Replaces "count today's rows, then append one" (providers/claude.py, codex.py),
which is a check-then-act race across hosts and panes -- the LiteLLM budget-race
class (#36926 false BudgetExceeded under load, #39150 spend charged to the wrong
window by COMMIT order, #27639 reservations never released). Clean-room: concepts only.

Invariants:
  - reserve() is atomic under the home's exclusive section and counts committed AND
    outstanding reservations against the cap;
  - the window a reservation belongs to is fixed when it is RESERVED, never when it
    commits (a spend at 23:59:59.9 that commits at 00:00:01 belongs to the old day);
  - a reservation neither committed nor released within `leak_after_s` becomes
    LEAKED, which still COUNTS as spent (conservative) and is reported;
  - replaying a reserve with the same id returns the original answer;
  - every record is fsynced before the call returns.
"""
from __future__ import annotations

import json
import os
import socket
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from modules.lease.store import Exclusive, fs_refusal, filesystem_type, fsync_dir

RESERVED, COMMITTED, RELEASED, LEAKED = "RESERVED", "COMMITTED", "RELEASED", "LEAKED"
JOURNAL = "spend.journal.jsonl"


class LedgerError(Exception):
    pass


@dataclass(frozen=True)
class Answer:
    ok: bool
    reason: str = ""
    window: str = ""
    used: int = 0
    cap: int = 0


def utc_day(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")


class SpendLedger:
    def __init__(self, root, *, caps: dict, leak_after_s: float, clock=time.time,
                 window=utc_day, host: str | None = None):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        why = fs_refusal(filesystem_type(self.root))
        if why:
            raise LedgerError(f"{self.root}: {why}")
        for k, v in caps.items():
            if not isinstance(v, int) or v < 0:
                raise LedgerError(f"cap for {k!r} must be a non-negative int, got {v!r}")
        if not (leak_after_s and leak_after_s > 0):
            raise LedgerError("leak_after_s must be positive")
        self.caps, self.leak_after_s, self.clock, self.window = dict(caps), leak_after_s, clock, window
        self.host = host or socket.gethostname()
        self.journal = self.root / JOURNAL
        self._lock = Exclusive(self.root / "spend.lock", 10.0)

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
                raise LedgerError(f"{self.journal}: seq gap at {rec.get('seq')}")
            out.append(rec)
        return out

    def _append(self, recs: list[dict], rec: dict) -> None:
        rec = {"seq": len(recs) + 1, "ts": self.clock(), "host": self.host, **rec}
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

    def _fold(self, recs: list[dict]) -> dict:
        res = {}
        for r in recs:
            if r["op"] == "reserve":
                res[r["id"]] = {**r, "state": RESERVED}
            elif r["op"] in ("commit", "release", "leak"):
                res[r["id"]]["state"] = {"commit": COMMITTED, "release": RELEASED,
                                         "leak": LEAKED}[r["op"]]
        return res

    def _sweep_leaks(self, recs: list[dict]) -> dict:
        now = self.clock()
        for rid, r in self._fold(recs).items():
            if r["state"] == RESERVED and now - r["ts"] > self.leak_after_s:
                self._append(recs, {"op": "leak", "id": rid})
        return self._fold(recs)

    @staticmethod
    def _used(res: dict, provider: str, window: str) -> int:
        return sum(r["amount"] for r in res.values() if r["provider"] == provider
                   and r["window"] == window and r["state"] in (RESERVED, COMMITTED, LEAKED))

    def reserve(self, rid: str, provider: str, amount: int = 1) -> Answer:
        if provider not in self.caps:
            return Answer(False, f"no cap configured for {provider!r}")
        if not isinstance(amount, int) or amount <= 0:
            return Answer(False, "amount must be a positive int")
        with self._lock:
            recs = self._read()
            res = self._sweep_leaks(recs)
            if rid in res:
                r = res[rid]
                same = r["provider"] == provider and r["amount"] == amount
                return Answer(same and r["state"] in (RESERVED, COMMITTED),
                              "" if same else "reservation id reused for a different request",
                              r["window"], self._used(res, provider, r["window"]), self.caps[provider])
            window = self.window(self.clock())     # fixed NOW, at reservation time
            used, cap = self._used(res, provider, window), self.caps[provider]
            if used + amount > cap:
                return Answer(False, "budget_spent", window, used, cap)
            self._append(recs, {"op": "reserve", "id": rid, "provider": provider,
                                "amount": amount, "window": window})
            return Answer(True, "", window, used + amount, cap)

    def _finish(self, op: str, rid: str) -> Answer:
        with self._lock:
            recs = self._read()
            res = self._sweep_leaks(recs)
            r = res.get(rid)
            if r is None:
                return Answer(False, "unknown reservation")
            if r["state"] != RESERVED:
                return Answer(r["state"] == {"commit": COMMITTED, "release": RELEASED}[op],
                              f"already {r['state']}", r["window"])
            self._append(recs, {"op": op, "id": rid})
            return Answer(True, "", r["window"])

    def commit(self, rid: str) -> Answer:
        return self._finish("commit", rid)

    def release(self, rid: str) -> Answer:
        """The effect never happened (refused before spawn): give the unit back."""
        return self._finish("release", rid)

    def state(self) -> dict:
        with self._lock:
            return self._fold(self._read())
