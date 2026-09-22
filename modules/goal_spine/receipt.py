#!/usr/bin/env python3
"""Receipts -- what a provider returns, and the only way it can move an obligation.

A receipt is a CLAIM from a provider (Claude via /cpp-gsd-long, Codex, a
deterministic verifier). It moves nothing by itself. Ingestion checks that the
claim is about this Goal, this revision, an epoch that actually started, an
obligation that epoch was scoped to, and a verdict from the gate that
obligation names -- and then hands it to GSD X's own `closure.satisfy`, which
refuses an executor narrative, a failed gate, a STALE or CANDIDATE obligation.

GATE IDENTITY IS ENFORCED HERE, NOT IN GSD X. `closure.evaluate_transition`
checks that a verdict passed; it does not check that it came from the gate the
obligation names, because in GSD X `done_gate` is prose describing a gate (its
own suite satisfies done_gate="a real gate" with a "pytest" verdict). Changing
that would rewrite another programme's contract for one caller. So the spine's
obligations name an exact gate, and a verdict from any other gate is refused at
this boundary before closure is asked. Recorded as finding B12 for GSD X.

IDEMPOTENT BY RECEIPT ID. A receipt's id is a hash of its content, so a provider
that re-delivers after a crash, or a reconciler that retries after an uncertain
completion, produces a DUPLICATE and changes nothing (Part VIII benchmark B: no
duplicate side effects).

RESIDUAL RISK, stated not hidden: GSD X's obligation store has no version
counter, so two ingests for the same Goal running concurrently could lose one
update. Ingestion is designed to run inside a reconciler tick, which holds the
Goal's version lock; the obligation list is re-read immediately before it is
written to keep the window narrow. It is narrowed, not closed.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from modules.gsd_x.mission import closure as gsdx_closure
from modules.gsd_x.mission import store as gsdx_store

from . import epoch as ep_
from . import goal as gl
from . import store as gs

APPLIED = "APPLIED"
REFUSED = "REFUSED"
DUPLICATE = "DUPLICATE"


@dataclass(frozen=True)
class Receipt:
    epoch_id: str
    goal_id: str
    goal_revision: int
    obligation_id: str
    provider: str
    gate: str = ""               # the gate that ran; "" means none did
    exit_status: int = -1
    observed: str = ""
    narrative: str = ""          # the provider's own account -- input, never authority

    @property
    def receipt_id(self) -> str:
        canon = json.dumps(asdict(self), sort_keys=True, ensure_ascii=False)
        return "r-" + hashlib.sha256(canon.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class IngestResult:
    outcome: str
    reason: str
    receipt_id: str


def _ledger_path(receipt_id: str) -> Path:
    return gs.state_dir() / "receipts" / f"{receipt_id}.json"


def _record(r: Receipt, result: IngestResult) -> None:
    p = _ledger_path(r.receipt_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps({"receipt": asdict(r), "outcome": result.outcome,
                               "reason": result.reason, "at": gl.now_iso()},
                              indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(p)


def _refuse(r: Receipt, reason: str) -> IngestResult:
    res = IngestResult(REFUSED, reason, r.receipt_id)
    _record(r, res)
    return res


def ingest(goal: gl.Goal, r: Receipt) -> IngestResult:
    if _ledger_path(r.receipt_id).is_file():
        return IngestResult(DUPLICATE, "this exact receipt was already ingested", r.receipt_id)
    if r.goal_id != goal.goal_id:
        return _refuse(r, f"receipt is for {r.goal_id}, not {goal.goal_id}")
    if r.goal_revision != goal.revision:
        return _refuse(r, f"receipt serves revision {r.goal_revision}; the Goal is at "
                          f"{goal.revision} -- its target moved")
    try:
        epoch = ep_.load(r.epoch_id)
    except FileNotFoundError:
        return _refuse(r, f"no epoch {r.epoch_id}")
    if epoch.goal_id != goal.goal_id or epoch.goal_revision != goal.revision:
        return _refuse(r, f"epoch {r.epoch_id} serves {epoch.goal_id} rev {epoch.goal_revision}")
    if epoch.provider != r.provider:
        return _refuse(r, f"epoch {r.epoch_id} was given to {epoch.provider}, "
                          f"not {r.provider}")
    if epoch.state not in (ep_.STARTED, ep_.COMPLETED):
        return _refuse(r, f"epoch {r.epoch_id} is {epoch.state}; an epoch that never "
                          "started produced no evidence")
    if r.obligation_id not in epoch.scope:
        return _refuse(r, f"{r.obligation_id} is outside epoch {r.epoch_id}'s scope "
                          f"{epoch.scope}")

    root = Path(goal.root)
    obligations = gsdx_store.load(root, namespace=goal.goal_id)
    target = next((o for o in obligations if o.identifier == r.obligation_id), None)
    if target is None:
        return _refuse(r, f"{r.obligation_id} is not in the Goal's obligation store")
    if r.gate and r.gate != target.done_gate:
        return _refuse(r, f"{r.obligation_id} is proven only by {target.done_gate!r}; "
                          f"a verdict from {r.gate!r} is evidence about something else")

    verdict = (gsdx_closure.Verdict(r.gate, r.exit_status, r.observed) if r.gate else None)
    updated, transition = gsdx_closure.satisfy(target, verdict, r.narrative or None)
    if not transition.allowed:
        return _refuse(r, f"GSD X closure {transition.outcome}: {transition.reason}")

    # Re-read immediately before writing: narrows the lost-update window to the
    # write itself (see RESIDUAL RISK above).
    current = gsdx_store.load(root, namespace=goal.goal_id)
    merged = [updated if o.identifier == r.obligation_id else o for o in current]
    gsdx_store.save(root, merged, namespace=goal.goal_id)
    result = IngestResult(APPLIED, transition.reason, r.receipt_id)
    _record(r, result)
    return result
