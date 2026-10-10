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


# --- Goal scope (A1 incident 2026-10-07, vault/specs/goal-budget-admission.md) ----------------------
# A1's cap was a number read AFTER the spend. A goal ledger holds one goal's cap and every settlement
# as journal state, so admission and the post-hoc check read the same thing. Two ops are added; the
# base fold ignores both, so a SpendLedger reading this journal is unaffected:
#   cap     {value, source}            -- the cap is folded, never taken from a constructor argument;
#   settle  {sid, measured, closes}    -- `measured` is the sid's CUMULATIVE processed tokens; the
#                                         booked amount is the highest one seen (a watermark), so a
#                                         replayed or duplicated settle books nothing twice.
# used = sum(watermarks) + open reservations (RESERVED or LEAKED, not closed by a settle of their sid).
GOAL_WINDOW = "goal"
SETTLED = "SETTLED"
DEFAULT_GOAL_LEAK_S = 6 * 3600


class GoalLedger(SpendLedger):
    def __init__(self, root, goal: str, *, leak_after_s: float = DEFAULT_GOAL_LEAK_S,
                 clock=time.time, host: str | None = None):
        super().__init__(root, caps={}, leak_after_s=leak_after_s, clock=clock,
                         window=lambda ts: GOAL_WINDOW, host=host)
        self.goal = goal

    def _gfold(self, recs: list[dict]) -> dict:
        cap, source, marks, res, seqs, pre = None, None, {}, {}, {}, {}
        # Lease epochs (dgl W1b). With no programme / lease_open row there is one implicit lease L1 whose
        # cap is the goal cap, and cap / used below come out exactly as before.
        leases = [{"id": "L1", "cap": None, "closed": False, "reason": None, "succession_id": None,
                   "reserves": {}, "settled": 0}]
        programme, programme_source, authority, opened = None, None, [], set()
        for r in recs:
            op = r["op"]
            cur = leases[-1]
            if op == "prebind":
                # PRE_BINDING_PROGRAM_CAPEX: history of a session from before it was bound. Watermarked
                # per sid, reported, and NEVER part of `used`.
                pre[r["sid"]] = max(pre.get(r["sid"], 0), int(r["measured"]))
            elif op == "cap":
                if r.get("lease") not in (None, cur["id"]) or cur["closed"] and r.get("lease"):
                    continue                              # a closed lease's cap is immutable
                cap, source = r["value"], r.get("source")
                cur["cap"] = cap
            elif op == "programme":
                programme, programme_source = int(r["value"]), r.get("source")
            elif op == "lease_open":
                if r["succession_id"] in opened:
                    continue
                opened.add(r["succession_id"])
                cur["closed"], cur["reason"] = True, cur["reason"] or "succeeded"
                leases.append({"id": f"L{len(leases) + 1}", "cap": int(r["cap"]), "closed": False,
                               "reason": None, "succession_id": r["succession_id"],
                               "reserves": dict(r.get("reserves") or {}), "settled": 0})
                cap, source = int(r["cap"]), f"lease_open {r['succession_id']}"
            elif op == "lease_close":
                for ls in leases:
                    if ls["id"] == r["lease"] and not ls["closed"]:
                        ls["closed"], ls["reason"], ls["receipt"] = True, r.get("reason"), r.get("receipt")
            elif op == "authority_required":
                authority.append({k: r.get(k) for k in ("succession_id", "need", "executable")})
            elif op == "reserve":
                res[r["id"]] = {**r, "state": RESERVED, "lease": cur["id"]}
                seqs[r["sid"]] = seqs.get(r["sid"], 0) + 1
            elif op == "leak":
                if res.get(r["id"], {}).get("state") == RESERVED:
                    res[r["id"]]["state"] = LEAKED
            elif op == "correct":
                marks[r["sid"]] = int(r["measured"])       # may LOWER; later settles watermark from here
            elif op == "settle":
                new = max(marks.get(r["sid"], 0), int(r["measured"]))
                cur["settled"] += new - marks.get(r["sid"], 0)
                marks[r["sid"]] = new
                for rid in r.get("closes", []):
                    if rid in res:
                        res[rid]["state"] = SETTLED
        for r in res.values():
            r["hold"] = r["amount"] if r["state"] in (RESERVED, LEAKED) else 0
            if r["hold"] and r.get("kind") == "agent":
                # A child's spend lands in its parent sid's measured total, so an open agent hold
                # shrinks by what that sid has settled since the spawn: neither counted twice nor
                # released by the parent's next renew (review M1, 31f1e714).
                r["hold"] = max(0, r["amount"] - max(0, marks.get(r["sid"], 0) - int(r.get("base", 0))))
        open_ = sum(r["hold"] for r in res.values())
        used = total = sum(marks.values()) + open_
        for ls in leases:
            ls["used"] = ls["settled"] + sum(r["hold"] for r in res.values() if r["lease"] == ls["id"])
        if len(leases) > 1:
            used = leases[-1]["used"]                    # admission reads the CURRENT lease
        return {"goal": self.goal, "cap": cap, "source": source, "marks": marks, "res": res,
                "seqs": seqs, "open": open_, "used": used, "total_used": total,
                "prebind": pre, "PRE_BINDING_PROGRAM_CAPEX": sum(pre.values()),
                "leases": leases, "programme": programme, "programme_source": programme_source,
                "authority": authority, "opened": opened,
                "status": "AUTHORITY_REQUIRED" if any(a["succession_id"] not in opened for a in authority) else "OK"}

    def prebind(self, sid: str, measured: int) -> dict:
        """Book a session's pre-binding history as program capex, never as goal spend."""
        if not isinstance(measured, int) or measured < 0:
            raise LedgerError("measured must be an int >= 0")
        with self._lock:
            recs = self._read()
            g = self._gfold(recs)
            if measured > g["prebind"].get(sid, 0):
                self._append(recs, {"op": "prebind", "sid": sid, "measured": measured})
                g = self._gfold(recs)
            return self._summary(g, ok=True, reason="", PRE_BINDING_PROGRAM_CAPEX=g["PRE_BINDING_PROGRAM_CAPEX"])

    def _sweep_leaks(self, recs: list[dict]) -> dict:
        now = self.clock()
        for rid, r in self._gfold(recs)["res"].items():
            if r["state"] == RESERVED and now - r["ts"] > self.leak_after_s:
                self._append(recs, {"op": "leak", "id": rid})   # still counts; reported, not dropped
        return self._gfold(recs)

    def reserve(self, rid, provider, amount=1):
        raise LedgerError("a goal ledger reserves through renew() / spawn(), never reserve()")

    @staticmethod
    def _summary(g: dict, **extra) -> dict:
        return {"goal": g["goal"], "cap": g["cap"], "used": g["used"], "open": g["open"],
                "settled": sum(g["marks"].values()),
                "remaining": None if g["cap"] is None else g["cap"] - g["used"], **extra}

    @staticmethod
    def approval_token(approval_id: str) -> str:
        return f"approval:{approval_id}"

    def declare_cap(self, value: int, source: str, *, inside_agent: bool = False,
                    approval_id: str | None = None, lease: str | None = None) -> dict:
        """Initial cap and lowering are always admitted. A raise is refused unless the caller holds the
        Owner's authority (`inside_agent=False`), and refused once used >= cap: raising a crossed cap
        makes the limit retrospective. A cap for a lease that is closed (or not the current one) is
        refused for everyone, the Owner included."""
        if not isinstance(value, int) or value <= 0:
            raise LedgerError("cap must be a positive int")
        with self._lock:
            recs = self._read()
            if lease is not None:
                cur = self._gfold(recs)["leases"][-1]
                if cur["closed"] or cur["id"] != lease:
                    return {"ok": False, "goal": self.goal, "reason": f"lease {lease} is closed "
                            f"(current is {cur['id']}): a closed lease's cap is immutable"}
            if approval_id:
                tok = self.approval_token(approval_id)
                if any(r.get("op") == "cap" and tok in str(r.get("source") or "") for r in recs):
                    return self._summary(self._gfold(recs), ok=True, applied=False,
                                         reason=f"approval {approval_id} already consumed")
                if tok not in source:
                    source = f"{source} {tok}"
            g = self._sweep_leaks(recs)
            cur = g["cap"]
            if cur is not None and value > cur:
                if inside_agent:
                    return self._summary(g, ok=False, reason="a cap raise needs the Owner's interactive "
                                         "confirmation (goal-declare --owner on a terminal)")
                if g["used"] >= cur:
                    return self._summary(g, ok=False, reason=f"CONTAINED: used {g['used']:,} >= cap {cur:,}; "
                                         "a crossed cap is never raised -- declare a new goal id")
            if cur != value:
                self._append(recs, {"op": "cap", "value": value, "source": source,
                                    **({"lease": lease} if lease else {})})
            return self._summary(self._gfold(recs), ok=True, reason="")

    # --- Lease epochs (dgl W1b): a goal is a programme of leases; a lease is a disposable cap --------
    RESERVE_KEYS = ("proof", "closeout", "recovery")

    @staticmethod
    def _lineage_view(g: dict) -> dict:
        leases = [{k: v for k, v in ls.items() if k != "settled"} for ls in g["leases"]]
        return {"goal": g["goal"], "ok": True, "cap": g["cap"], "used": g["used"], "total_used": g["total_used"],
                "settled": sum(g["marks"].values()), "open": g["open"], "programme": g["programme"],
                "programme_source": g["programme_source"], "status": g["status"], "leases": leases,
                "authority_required": g["authority"]}

    def lineage(self) -> dict:
        """Read-only: folds the journal and appends nothing (status() sweeps leaks, this never does)."""
        with self._lock:
            return self._lineage_view(self._gfold(self._read()))

    def programme_status(self) -> dict:
        with self._lock:
            g = self._gfold(self._read())
        other = sum(sum(ls["reserves"].values()) for ls in g["leases"] if not ls["closed"])
        settled = sum(g["marks"].values())
        ex = None if g["programme"] is None else g["programme"] - settled - g["open"] - other
        return {"goal": g["goal"], "ok": True, "programme": g["programme"], "source": g["programme_source"],
                "settled": settled, "open": g["open"], "open_lease_reserves": other, "executable": ex,
                "lease": g["leases"][-1]["id"], "status": g["status"]}

    def set_programme(self, value: int, source: str, *, inside_agent: bool = False) -> dict:
        """The programme envelope. Same Owner rule as declare_cap: first value and lowering are admitted,
        a raise needs the Owner (`inside_agent=False`)."""
        if not isinstance(value, int) or value <= 0:
            raise LedgerError("programme must be a positive int")
        with self._lock:
            recs = self._read()
            cur = self._gfold(recs)["programme"]
            if cur is not None and value > cur and inside_agent:
                return {"ok": False, "goal": self.goal, "programme": cur,
                        "reason": "a programme raise needs the Owner's interactive confirmation (--owner)"}
            if cur != value:
                self._append(recs, {"op": "programme", "value": value, "source": source})
            return {"ok": True, "goal": self.goal, "programme": value, "reason": ""}

    def lease_open(self, succession_id: str, cap: int, *, prev_lease: str | None = None,
                   reserves: dict | None = None) -> dict:
        """Open the successor lease. Idempotent by `succession_id`; compare-and-swap on `prev_lease`
        (must be the latest lease); the envelope must hold cap + reserves, else exactly one
        authority_required row is journalled for the succession and the status is AUTHORITY_REQUIRED."""
        reserves = {k: int(v) for k, v in (reserves or {}).items()}
        if not succession_id or not isinstance(cap, int) or cap <= 0 or set(reserves) - set(self.RESERVE_KEYS) \
                or any(v < 0 for v in reserves.values()):
            raise LedgerError("lease_open needs a succession id, a positive int cap and reserves "
                              f"{self.RESERVE_KEYS} >= 0")
        with self._lock:
            recs = self._read()
            g = self._sweep_leaks(recs)
            done = next((ls for ls in g["leases"] if ls["succession_id"] == succession_id), None)
            if done:
                return {**self._lineage_view(g), "ok": True, "applied": False, "lease": done["id"], "reason": ""}
            latest = g["leases"][-1]
            if prev_lease is not None and prev_lease != latest["id"]:
                return {**self._lineage_view(g), "ok": False, "lease": latest["id"],
                        "reason": f"CAS: {prev_lease} is not the latest lease; {latest['id']} "
                                  f"(succession {latest['succession_id']}) won"}
            if g["programme"] is None:
                return {**self._lineage_view(g), "ok": False,
                        "reason": "UNKNOWN: no programme envelope declared; unknown headroom is not free"}
            need = cap + sum(reserves.values())
            other = sum(sum(ls["reserves"].values()) for ls in g["leases"]
                        if not ls["closed"] and ls is not latest)
            executable = g["programme"] - sum(g["marks"].values()) - g["open"] - other
            if need > executable:
                if succession_id not in {a["succession_id"] for a in g["authority"]}:
                    self._append(recs, {"op": "authority_required", "succession_id": succession_id,
                                        "need": need, "executable": executable})
                g = self._gfold(recs)
                return {**self._lineage_view(g), "ok": False, "need": need, "executable": executable,
                        "reason": f"AUTHORITY_REQUIRED: need {need:,} > executable {executable:,}"}
            self._append(recs, {"op": "lease_open", "lease": f"L{len(g['leases']) + 1}", "cap": cap,
                                "succession_id": succession_id, "prev_lease": latest["id"],
                                "reserves": reserves})
            g = self._gfold(recs)
            return {**self._lineage_view(g), "ok": True, "applied": True, "lease": g["leases"][-1]["id"],
                    "need": need, "executable": executable, "reason": ""}

    def lease_close(self, lease: str, reason: str, receipt: str = "") -> dict:
        with self._lock:
            recs = self._read()
            g = self._gfold(recs)
            ls = next((x for x in g["leases"] if x["id"] == lease), None)
            if ls is None:
                return {"ok": False, "goal": self.goal, "reason": f"unknown lease {lease}"}
            if not ls["closed"]:
                self._append(recs, {"op": "lease_close", "lease": lease, "reason": reason, "receipt": receipt})
            return {**self._lineage_view(self._gfold(recs)), "ok": True, "reason": ""}

    @staticmethod
    def _headroom(g: dict, exclude: str | None = None) -> int:
        """One final reply per live pane: a deny stops tool calls, not the model request that answers
        it (canary #2, 2026-10-07: 195,084 of a 207,358 overshoot). A live pane is a sid with an open
        LEASE; its `per_call` is the size of that reply."""
        return sum(int(r.get("per_call") or 0) for r in g["res"].values()
                   if r["hold"] and r.get("kind") == "lease" and r["sid"] != exclude)

    def renew(self, sid: str, measured: int, lease: int, per_call: int = 0) -> dict:
        """Settle `sid` at its cumulative `measured`, close its open LEASES and any agent hold the
        settled spend has used up, reserve the next lease (at most `lease`, at most what remains).
        At most one open lease per sid afterwards; an agent hold survives until its spend arrives.
        With `per_call` > 0, what remains is net of every live pane's final reply, this one's too:
        refused unless one more call AND its reply fit, and a refusal books this pane's reply as a
        `final` hold so no other pane can spend it."""
        if not isinstance(measured, int) or measured < 0 or not isinstance(lease, int) or lease <= 0 \
                or not isinstance(per_call, int) or per_call < 0:
            raise LedgerError("measured must be an int >= 0, lease a positive int, per_call an int >= 0")
        with self._lock:
            recs = self._read()
            g = self._sweep_leaks(recs)
            if g["cap"] is None:
                return self._summary(g, ok=False, reason="no cap declared for this goal")
            mark = max(g["marks"].get(sid, 0), measured)
            closes = sorted(rid for rid, r in g["res"].items()
                            if r["sid"] == sid and r["state"] in (RESERVED, LEAKED)
                            and (r.get("kind") == "lease"
                                 or r.get("kind") == "agent" and mark - int(r.get("base", 0)) >= r["amount"]
                                 or r.get("kind") == "final" and mark > int(r.get("base", 0))))
            if closes or measured > g["marks"].get(sid, 0):
                self._append(recs, {"op": "settle", "sid": sid, "measured": measured, "closes": closes})
                g = self._gfold(recs)
            room = g["cap"] - g["used"] - self._headroom(g, exclude=sid) - per_call
            if room < max(per_call, 1):
                if per_call and not any(r["hold"] and r["sid"] == sid and r.get("kind") == "final"
                                        for r in g["res"].values()):
                    self._append(recs, {"op": "reserve", "id": f"{self.goal}:{sid}:{g['seqs'].get(sid, 0) + 1}",
                                        "sid": sid, "kind": "final", "provider": self.goal, "amount": per_call,
                                        "window": GOAL_WINDOW, "base": measured, "per_call": per_call})
                    g = self._gfold(recs)
                return self._summary(g, ok=False, reason=(
                    f"budget_spent: used {g['used']:,} of cap {g['cap']:,}; after one final reply per live "
                    f"pane, {max(room, 0):,} is left, less than one call ({max(per_call, 1):,})"))
            seq = g["seqs"].get(sid, 0) + 1
            rid, amount = f"{self.goal}:{sid}:{seq}", min(lease, room)
            self._append(recs, {"op": "reserve", "id": rid, "sid": sid, "kind": "lease", "provider": self.goal,
                                "amount": amount, "window": GOAL_WINDOW, "base": measured, "per_call": per_call})
            return self._summary(self._gfold(recs), ok=True, reason="",
                                 lease={"id": rid, "amount": amount, "base": measured})

    def settle_stopped(self, sid: str, measured: int, reason: str) -> dict:
        """A stopped worker: settle `sid` at `measured` and close EVERY open hold of it (lease, agent,
        final). Never reserves. A second call books nothing new."""
        if not isinstance(measured, int) or measured < 0:
            raise LedgerError("measured must be an int >= 0")
        with self._lock:
            recs = self._read()
            g = self._sweep_leaks(recs)
            closes = sorted(rid for rid, r in g["res"].items()
                            if r["sid"] == sid and r["state"] in (RESERVED, LEAKED))
            if closes or measured > g["marks"].get(sid, 0):
                self._append(recs, {"op": "settle", "sid": sid, "measured": measured, "closes": closes,
                                    "stopped": True, "reason": reason})
                g = self._gfold(recs)
            return self._summary(g, ok=True, reason="", closed=closes)

    def correct(self, sid: str, measured: int, reason: str, authority: str) -> dict:
        """Owner correction of a misattributed mark (may lower it). Journalled, never silent."""
        if not isinstance(measured, int) or measured < 0 or not reason or not authority:
            raise LedgerError("correct needs measured int >= 0, a reason and an authority")
        with self._lock:
            recs = self._read()
            g = self._sweep_leaks(recs)
            self._append(recs, {"op": "correct", "sid": sid, "measured": measured,
                                "reason": reason, "authority": authority,
                                "previous": g["marks"].get(sid, 0)})
            return self._summary(self._gfold(recs), ok=True, reason="")

    def spawn(self, sid: str, estimate: int, base: int = 0) -> dict:
        """Admit a child (Agent / worker) only if its estimate fits what remains. `base` is the parent
        sid's measured total at launch; the hold shrinks as settled spend passes it (see _gfold)."""
        if not isinstance(estimate, int) or estimate <= 0 or not isinstance(base, int) or base < 0:
            raise LedgerError("estimate must be a positive int and base an int >= 0")
        with self._lock:
            recs = self._read()
            g = self._sweep_leaks(recs)
            if g["cap"] is None:
                return self._summary(g, ok=False, reason="no cap declared for this goal")
            remaining = g["cap"] - g["used"] - self._headroom(g)   # a child never takes a pane's last reply
            if estimate > remaining:
                return self._summary(g, ok=False, reason=f"spawn estimate {estimate:,} > remaining {remaining:,} "
                                     "(net of one final reply per live pane)")
            rid = f"{self.goal}:{sid}:{g['seqs'].get(sid, 0) + 1}"
            self._append(recs, {"op": "reserve", "id": rid, "sid": sid, "kind": "agent", "provider": self.goal,
                                "amount": estimate, "window": GOAL_WINDOW, "base": base})
            return self._summary(self._gfold(recs), ok=True, reason="", reservation=rid)

    def status(self) -> dict:
        with self._lock:
            return self._summary(self._sweep_leaks(self._read()), ok=True, reason="")
