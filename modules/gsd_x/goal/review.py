"""Reviewer verdict intake as a goal event (spec S7, D17): `review.received`.

An independent review is a CLAIM about bytes a reviewer read. This module turns a review receipt
(`genesis-review-v1`, written by tools/evidence_bundle.py::write_review) into one event on the goal log, and
refuses to when the receipt cannot be trusted:

  * the receipt's verdict is not `pass` (an unbound, tampered or non-APPROVE review is not received);
  * the reviewer is the worker (a builder never certifies its own work);
  * the reviewed bytes are not today's bytes (a stale review is a review of something else).

Concurrency: many reviewers may report at once. Every attempt re-projects the log and appends at the next
sequence; a lost race is retried, at most `MAX_ATTEMPTS` times, then reported as contended -- never dropped
silently. The ticket nonce is the idempotency key: the same ticket received twice records once.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from . import proof as pf
from .contract import project
from .log import GoalLog, GoalLogError, LostRace

MAX_ATTEMPTS = 3
RECORDED, DUPLICATE, REFUSED, CONTENDED = "RECORDED", "DUPLICATE", "REFUSED", "CONTENDED"
SCHEMA = "genesis-review-v1"


def _refuse(reason: str, status: str = REFUSED) -> dict:
    return {"status": status, "reason": reason}


def _stale(root: Path, artifacts: list) -> str:
    for a in artifacts:
        try:
            now = hashlib.sha256((root / a["path"]).read_bytes()).hexdigest()
        except (OSError, KeyError, TypeError):
            return f"{a.get('path') if isinstance(a, dict) else '?'} is unreadable now"
        if now != a.get("sha256"):
            return f"{a['path']} is not the reviewed bytes any more"
    return ""


def receive(log: GoalLog, root: Path, receipt_path: str, ticket: str, claim_id: str,
            candidate: str, worker: str, actor: str = "reviewer") -> dict:
    """Record one review as `review.received`, or say why not. Never raises on a refusal."""
    root = Path(root)
    try:
        receipt = json.loads((root / receipt_path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        return _refuse(f"review receipt unreadable: {exc.__class__.__name__}")
    if not isinstance(receipt, dict) or receipt.get("schema") != SCHEMA:
        return _refuse("not a genesis-review-v1 receipt")
    if receipt.get("verdict") != "pass":
        return _refuse(f"the review did not pass: {(receipt.get('intake') or {}).get('reason', 'no reason')}")
    reviewer = receipt.get("reviewer") or {}
    if not worker or reviewer.get("agent") == worker:
        return _refuse("the reviewer is the worker (or the worker is unnamed): a builder cannot certify its own work")
    why = _stale(root, receipt.get("artifacts") or [])
    if why:
        return _refuse(f"stale review: {why}")
    if not ticket:
        return _refuse("no ticket: nothing identifies which dispatch this review answers")
    data = {"v": pf.SUPPORTED_V, "claim_id": claim_id, "candidate": candidate, "ticket": ticket,
            "reviewer": {k: reviewer.get(k) for k in ("agent", "model", "effort")},
            "worker": worker, "artifacts": receipt.get("artifacts") or []}
    for attempt in range(1, MAX_ATTEMPTS + 1):
        state = project(log)
        if any(e["data"].get("ticket") == ticket for e in pf.project_proofs(state).received):
            return {"status": DUPLICATE, "reason": "this ticket was already received", "attempts": attempt}
        try:
            pf.append_pcc(log, state, pf.RECEIVED, data, actor)
        except LostRace:
            continue                      # another writer took that sequence: re-project and try again
        except (GoalLogError, pf.ProofRefused) as exc:
            return _refuse(f"{exc.__class__.__name__}: {exc}")
        return {"status": RECORDED, "reason": "review recorded", "attempts": attempt}
    return _refuse(f"the log stayed contended for {MAX_ATTEMPTS} attempts; nothing was recorded", CONTENDED)
