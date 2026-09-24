#!/usr/bin/env python3
"""Intents, information gain, escalations and leases.

INTENTS (F9). The attempt id is written to `intents.jsonl` BEFORE the provider
is asked to do anything. Recovery can then tell "we never meant to" (no intent:
provably not started) from "we meant to and do not know if it happened" (intent,
no handle: UNCERTAIN, reconciled against the provider's own record).

GAIN (F10). Gain is a change in what the ENGINE says about the goal between two
readings: obligation dispositions and their verdicts, the judge's verdict, and
the set of failure signatures. Commits, receipts and tree moves are not in the
snapshot at all, so a provider that only produces those cannot manufacture it.

LEASES (F14). A lease names a resource, a holder, a heartbeat and a TTL. An
expired lease is reclaimable; a live one held by someone else is refused.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import uuid
from pathlib import Path

from .. import contract as gc
from .. import convergence as cv
from .. import epoch as ep
from . import store

# Escalation ladder, in order (spec: Stagnation).
ESCALATION_LADDER = ("RCA_MISSION", "PROVIDER_CHANGE", "SUBGOAL", "DECISION_PACKET")

LEASE_HELD = "LEASE_HELD"
LEASE_UNREADABLE = "LEASE_UNREADABLE"
LEASE_RACE = "LEASE_RACE"


# --- intents -------------------------------------------------------------------

class IntentLedger:
    def __init__(self, path: Path):
        self.path = Path(path)

    def record(self, attempt_id: str, mission_id: str, goal: str, repo: str,
               provider: str, spec: dict) -> dict:
        body = {"attempt_id": attempt_id, "mission": mission_id, "goal": goal, "repo": repo,
                "provider": provider, "ts": time.time(),
                "spec_digest": hashlib.sha256(json.dumps(spec, sort_keys=True, default=str)
                                              .encode("utf-8")).hexdigest()[:24]}
        store.append_jsonl(self.path, body)
        return body

    def has(self, attempt_id: str) -> bool:
        records, _torn = store.read_jsonl(self.path)
        return any(r.get("attempt_id") == attempt_id for r in records)


# --- gain ------------------------------------------------------------------------

def goal_snapshot(state: gc.GoalState, judge: dict | None) -> dict:
    """What the engine says about the goal: the only inputs gain may move on."""
    conv = cv.project_convergence(state)
    obligations = {o.identifier: [o.disposition, (o.verdict or {}).get("exit_status")]
                   for o in conv.obligations.values()}
    sigs = set()
    for ev in state.events:
        if ev.type == ep.RECEIPT:
            for f in (ev.data.get("receipt") or {}).get("failures") or []:
                sigs.add(str(f.get("signature", "")))
    for fid, f in conv.failures.items():
        sigs.add(f"recorded:{fid}:{f.get('disposition')}")
    return {"obligations": obligations,
            "judge": (judge or {}).get("verdict"),
            "failure_signatures": sorted(sigs)}


def snapshot_digest(snap: dict) -> str:
    return hashlib.sha256(json.dumps(snap, sort_keys=True).encode("utf-8")).hexdigest()[:24]


class GainLedger:
    def __init__(self, path: Path):
        self.path = Path(path)

    def last(self, goal_key: str) -> dict | None:
        records, _torn = store.read_jsonl(self.path)
        mine = [r for r in records if r.get("goal") == goal_key]
        return mine[-1] if mine else None

    def last_gain_ts(self) -> float | None:
        records, _torn = store.read_jsonl(self.path)
        ts = [r["ts"] for r in records if r.get("gain")]
        return max(ts) if ts else None

    def record(self, goal_key: str, cycle: int, snap: dict, active: bool,
               now: float | None = None) -> dict:
        """One verdict per goal per cycle. `active` = the goal had work in motion
        this cycle; only an active no-gain cycle counts towards stagnation."""
        prev = self.last(goal_key)
        digest = snapshot_digest(snap)
        if prev is None:
            gain, reason = False, "baseline: first reading of this goal"
            streak = 0
        else:
            gain = prev.get("digest") != digest
            reason = _describe_change(prev.get("snapshot") or {}, snap) if gain else "no change"
            streak = 0 if gain else int(prev.get("no_gain_streak", 0)) + (1 if active else 0)
        body = {"goal": goal_key, "cycle": cycle, "ts": now if now is not None else time.time(),
                "gain": gain, "reason": reason, "active": bool(active), "digest": digest,
                "no_gain_streak": streak, "snapshot": snap}
        store.append_jsonl(self.path, body)
        return body


def _describe_change(old: dict, new: dict) -> str:
    parts = []
    oo, no = old.get("obligations") or {}, new.get("obligations") or {}
    for k in sorted(set(oo) | set(no)):
        if oo.get(k) != no.get(k):
            parts.append(f"{k}: {oo.get(k)} -> {no.get(k)}")
    if old.get("judge") != new.get("judge"):
        parts.append(f"judge: {old.get('judge')} -> {new.get('judge')}")
    if old.get("failure_signatures") != new.get("failure_signatures"):
        parts.append("failure signature set changed")
    return "; ".join(parts) or "snapshot changed"


class EscalationLedger:
    def __init__(self, path: Path):
        self.path = Path(path)

    def next_step(self, goal_key: str) -> str:
        records, _torn = store.read_jsonl(self.path)
        n = sum(1 for r in records if r.get("goal") == goal_key)
        return ESCALATION_LADDER[min(n, len(ESCALATION_LADDER) - 1)]

    def record(self, goal_key: str, reason: str) -> dict:
        body = {"goal": goal_key, "step": self.next_step(goal_key), "reason": reason,
                "ts": time.time()}
        store.append_jsonl(self.path, body)
        return body


# --- leases ----------------------------------------------------------------------

class LeaseRefused(Exception):
    def __init__(self, reason: str, detail: str):
        super().__init__(f"{reason}: {detail}")
        self.reason, self.detail = reason, detail


def _safe(resource: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", resource)[:120]


class Leases:
    def __init__(self, directory: Path, clock=time.time):
        self.dir = Path(directory)
        self.clock = clock

    def path(self, resource: str) -> Path:
        return self.dir / f"{_safe(resource)}.json"

    def _create(self, resource: str, holder: str, ttl_s: float) -> bool:
        self.dir.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(str(self.path(resource)), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError:
            return False
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"resource": resource, "holder": holder,
                                 "heartbeat_ts": self.clock(), "ttl_s": float(ttl_s)}))
            fh.flush()
            os.fsync(fh.fileno())
        return True

    def acquire(self, resource: str, holder: str, ttl_s: float) -> dict:
        """Acquire or renew. Returns {"acquired", "renewed", "reclaimed"}."""
        if self._create(resource, holder, ttl_s):
            return {"acquired": True, "renewed": False, "reclaimed": None}
        p = self.path(resource)
        try:
            cur = store.read_json(p)
        except FileNotFoundError:
            if self._create(resource, holder, ttl_s):
                return {"acquired": True, "renewed": False, "reclaimed": None}
            raise LeaseRefused(LEASE_RACE, f"{resource} changed hands during acquisition")
        except store.StateUnreadable as exc:
            raise LeaseRefused(LEASE_UNREADABLE, str(exc))
        if cur.get("holder") == holder:
            store.atomic_write_json(p, {**cur, "heartbeat_ts": self.clock(),
                                        "ttl_s": float(ttl_s)})
            return {"acquired": True, "renewed": True, "reclaimed": None}
        age = self.clock() - float(cur.get("heartbeat_ts", 0))
        if age <= float(cur.get("ttl_s", 0)):
            raise LeaseRefused(LEASE_HELD, f"{resource} held by {cur.get('holder')} "
                                           f"(heartbeat {age:.0f}s ago, ttl {cur.get('ttl_s')}s)")
        aside = self.dir / f".expired-{uuid.uuid4().hex}"
        try:
            os.rename(p, aside)
        except FileNotFoundError:
            raise LeaseRefused(LEASE_RACE, f"{resource} was reclaimed by someone else")
        if not self._create(resource, holder, ttl_s):
            raise LeaseRefused(LEASE_RACE, f"{resource} was taken after the reclaim")
        return {"acquired": True, "renewed": False,
                "reclaimed": {**cur, "expired_by_s": round(age - float(cur.get("ttl_s", 0)), 1)}}

    def release(self, resource: str, holder: str) -> bool:
        p = self.path(resource)
        try:
            cur = store.read_json(p)
        except FileNotFoundError:
            return False
        if cur.get("holder") != holder:
            return False
        os.unlink(p)
        return True

    def held_by(self, holder: str) -> list[str]:
        out = []
        if not self.dir.is_dir():
            return out
        for p in self.dir.glob("*.json"):
            try:
                cur = store.read_json(p)
            except (FileNotFoundError, store.StateUnreadable):
                continue
            if cur.get("holder") == holder:
                out.append(cur.get("resource", p.stem))
        return out
