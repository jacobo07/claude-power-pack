"""Owner decisions with a Proof of Human Necessity (oic-v1 S2, amendment M6).

Lives beside owner_queue (the HR-001 residual register) but in its OWN log,
~/.claude/state/OWNER_DECISIONS.jsonl, so machine-raised decisions never flood the SessionStart digest.

An Owner interruption costs attention, context reconstruction and a blocked critical path, so a
component may raise one only with a proof that nothing else can answer it:

  requested_decision        what the Owner is asked, in one line
  human_authority           capital | credential | legal | physical_presence | preference |
                            irreversible | new_scope      (anything else is refused)
  why_not_authority         why no authority grant covers it (checked here when `effect` is given:
                            a covered effect is refused as REDUNDANT_OWNER_PROMPT)
  why_not_machinery         why deterministic machinery cannot resolve it
  why_not_event_wait        why waiting for an event (CI, a reset, a deploy) does not resolve it
  why_not_independent_work  why the work cannot continue elsewhere first
  blocks                    the dependency closure this decision blocks, and nothing more

A refused ask never reaches the Owner; it is an incident (MISSING_PROOF,
MECHANICAL_OWNER_ESCALATION, REDUNDANT_OWNER_PROMPT) in owner-interface-incidents.jsonl.

Dedup: the decision id derives from a semantic `key`, so the same question raised by several workers or
panes is ONE decision; later askers are subscribers and read the same answer.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

HUMAN_AUTHORITY = {"capital", "credential", "legal", "physical_presence", "preference",
                   "irreversible", "new_scope"}
PROOF_FIELDS = ("requested_decision", "human_authority", "why_not_authority", "why_not_machinery",
                "why_not_event_wait", "why_not_independent_work", "blocks")


def _dir(state_dir=None) -> Path:
    return Path(state_dir or os.environ.get("CPP_OWNER_DECISIONS_DIR") or Path.home() / ".claude" / "state")


def _log(state_dir=None) -> Path:
    return _dir(state_dir) / "OWNER_DECISIONS.jsonl"


def _append(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _events(state_dir=None) -> list[dict]:
    p = _log(state_dir)
    if not p.is_file():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            continue   # a torn line is skipped; it can neither queue nor answer a decision
    return out


def incident(kind: str, detail: dict, *, state_dir=None, now=None) -> None:
    _append(_dir(state_dir) / "owner-interface-incidents.jsonl",
            {"ts": now or time.time(), "kind": kind, **detail})


def decision_id(key: str) -> str:
    return "qd-" + hashlib.sha256(("decision\x00" + key).encode("utf-8")).hexdigest()[:10]


def load(state_dir=None) -> dict[str, dict]:
    """Decisions by id: packet, status (pending|answered|withdrawn), answer, subscribers."""
    out: dict[str, dict] = {}
    for ev in _events(state_dir):
        rid, op = ev.get("id"), ev.get("op")
        if op == "ask" and (rid not in out or out[rid]["status"] == "withdrawn"):
            out[rid] = {"id": rid, "packet": ev.get("packet"), "status": "pending", "answer": None,
                        "subscribers": [ev.get("packet", {}).get("asker")], "asked_at": ev.get("at")}
        elif rid in out and op == "subscribe":
            out[rid]["subscribers"].append(ev.get("asker"))
        elif rid in out and op == "answer":
            out[rid].update(status="answered", answer=ev.get("answer"), by=ev.get("by"), answered_at=ev.get("at"))
        elif rid in out and op == "withdraw":
            out[rid].update(status="withdrawn", why=ev.get("why"))
    return out


def ask(key: str, proof: dict, *, asker: str, effect: str | None = None, target: dict | None = None,
        facts: dict | None = None, options: list[str] | None = None, safe_default: str = "",
        state_dir=None, now=None) -> dict:
    """Queue ONE Owner decision, subscribe to an identical pending one, or refuse."""
    now = now or time.time()
    missing = [f for f in PROOF_FIELDS if not str(proof.get(f) or "").strip()]
    if missing:
        incident("MISSING_PROOF", {"key": key, "asker": asker, "missing": missing}, state_dir=state_dir, now=now)
        return {"status": "refused", "incident": "MISSING_PROOF", "missing": missing}
    if proof["human_authority"] not in HUMAN_AUTHORITY:
        incident("MECHANICAL_OWNER_ESCALATION",
                 {"key": key, "asker": asker, "claimed": proof["human_authority"]}, state_dir=state_dir, now=now)
        return {"status": "refused", "incident": "MECHANICAL_OWNER_ESCALATION"}
    if effect:
        from modules.autonomy_gate import grants
        v = grants.check(effect, target=target, facts=facts, record_source=f"decisions.ask:{asker}")
        if v["allowed"]:
            incident("REDUNDANT_OWNER_PROMPT",
                     {"key": key, "asker": asker, "grant": v["grant"], "effect": effect}, state_dir=state_dir, now=now)
            return {"status": "refused", "incident": "REDUNDANT_OWNER_PROMPT", "grant": v["grant"]}
    rid = decision_id(key)
    cur = load(state_dir).get(rid)
    if cur and cur["status"] == "pending":
        _append(_log(state_dir), {"op": "subscribe", "id": rid, "asker": asker, "at": now})
        return {"status": "subscribed", "id": rid}
    if cur and cur["status"] == "answered":
        return {"status": "answered", "id": rid, "answer": cur["answer"]}   # decision cache: reuse
    packet = {"key": key, "proof": proof, "options": options or [], "safe_default": safe_default,
              "effect": effect, "target": target, "asker": asker}
    _append(_log(state_dir), {"op": "ask", "id": rid, "at": now, "packet": packet})
    return {"status": "queued", "id": rid}


def decide(key: str, answer: str, *, by: str = "owner", state_dir=None, now=None) -> bool:
    rid = decision_id(key)
    if rid not in load(state_dir):
        return False
    _append(_log(state_dir), {"op": "answer", "id": rid, "answer": answer, "by": by, "at": now or time.time()})
    return True


def withdraw(key: str, why: str, *, state_dir=None, now=None) -> bool:
    """An invalidator fired (the question no longer applies): the cached answer must not be reused."""
    rid = decision_id(key)
    if rid not in load(state_dir):
        return False
    _append(_log(state_dir), {"op": "withdraw", "id": rid, "why": why, "at": now or time.time()})
    return True


def pending(state_dir=None) -> list[dict]:
    return [d for d in load(state_dir).values() if d["status"] == "pending"]


def blocked(work_item: str, state_dir=None) -> list[str]:
    """Pending decisions whose declared closure names this work item; anything else keeps running."""
    return [d["id"] for d in pending(state_dir)
            if work_item in [s.strip() for s in str(d["packet"]["proof"]["blocks"]).split(",")]]
