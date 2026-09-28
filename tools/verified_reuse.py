"""Verified Reuse (T8 item 30, genesis-verified-reuse -> EXTEND _audit_cache).

A read-only batch draft that was validated once may be handed back instead of dispatching a
reviewer again -- but only as a DRAFT. The vendored module does the binding through the one
bridge: objective, contract, source SHA-256s, worker route, role, policies, freshness window
and the tree root (so a different worktree never reuses another's draft) all enter one
fingerprint, and every persisted byte is re-read and re-hashed at the moment of reuse.

What this wrapper adds:
  * persistence under `<root>/_audit_cache/reuse/` (gitignored, owned by tools/audit_cache.py's
    cache dir), content-addressed so an input file cannot be edited in place;
  * the role and policy the fingerprint binds are the task's OWN task_contract text and the
    batch output bounds -- change either and the fingerprint changes;
  * a ledger of hits and misses with what the hit actually avoided: one reviewer dispatch and
    the measured source characters it would have been sent. Never tokens or dollars -- those
    were not measured (the vendored result says tokensSaved: null, and so do we).

A hit is `accepted: false, needsFreshReview: true` by construction. It can never satisfy the
review gate: tools/evidence_bundle.py demands a reply that echoes a one-time review ticket
issued for the current bytes, and a reused draft carries no ticket.

    python tools/verified_reuse.py stats [--root .]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from modules.external_assimilation import node_bridge as nb  # noqa: E402

STORE_REL = Path("_audit_cache") / "reuse"
TTL_MS = 24 * 60 * 60 * 1000
HIT, MISS, ADMITTED, REFUSED, UNJUDGED = "HIT", "MISS", "ADMITTED", "REFUSED", "UNJUDGED"


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def store(root: str | Path) -> Path:
    return Path(root) / STORE_REL


def _put(root: Path, kind: str, data: bytes) -> dict:
    """Content-addressed file under the store; returns a root-relative proof."""
    digest = _sha(data)
    rel = STORE_REL / kind / f"{digest}.txt"
    p = root / rel
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return {"path": rel.as_posix(), "sha256": digest}


def request_for(root: str | Path, task: dict, bounds: dict) -> dict:
    """The exact inputs a batch draft was produced from, as the vendored request."""
    root = Path(root)
    sources = []
    for rel in task["sourcePaths"]:
        sources.append({"path": Path(rel).as_posix(), "sha256": _sha((root / rel).read_bytes())})
    contract = task["contract"]
    role = _put(root, "role", json.dumps(contract, sort_keys=True).encode("utf-8"))
    policy = _put(root, "policy", json.dumps({"operation": "read-only-draft", "outputBounds": bounds,
                                              "acceptance": "draft only; fresh review required"},
                                             sort_keys=True).encode("utf-8"))
    worker = task["worker"]
    return {"objective": task["task"],
            "contract": {"acceptance": contract.get("acceptance") or [], "id": task["id"]},
            "sources": sources,
            "worker": {"provider": worker["route"], "model": worker["requestedModel"],
                       "config": worker.get("config") or {}},
            "role": role, "policies": [policy], "outputSchema": {"type": "object"},
            "operation": "read-only-draft", "dependencyMode": "static",
            "freshness": {"ttlMs": TTL_MS}, "context": {"selectors": task.get("selectors") or []}}


def _index_path(root: Path) -> Path:
    return store(root) / "index.json"


def _load_index(root: Path) -> dict:
    try:
        return json.loads(_index_path(root).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _log(root: Path, row: dict) -> None:
    p = store(root) / "ledger.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    row = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), **row}
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")


def admit(root: str | Path, task: dict, bounds: dict, draft: dict, plan_id: str, worker_id: str) -> tuple[str, dict]:
    """Persist a VALIDATED batch draft so a later identical task may be handed it back."""
    root = Path(root)
    req = request_for(root, task, bounds)
    fp = nb.call("verifiedReuse", "buildFingerprint", [{"root": str(root), "request": req}], timeout=60)
    if not fp.ok or not (fp.value or {}).get("ok"):
        return UNJUDGED, {"reason": fp.error or (fp.value or {}).get("reason")}
    fingerprint = fp.value["fingerprint"]
    output = _put(root, "output", json.dumps(draft, sort_keys=True).encode("utf-8"))
    now = datetime.now(timezone.utc)

    def js_utc(d: datetime) -> str:
        # The vendored module accepts only JavaScript's canonical toISOString() shape
        # (millisecond precision, "Z"); Python's isoformat() is refused as non-canonical.
        return d.strftime("%Y-%m-%dT%H:%M:%S.") + f"{d.microsecond // 1000:03d}Z"

    receipt_body = {"schema": "genesis-readonly-draft-v1", "status": "draft", "operation": "read-only-draft",
                    "fingerprint": fingerprint, "planId": plan_id[:160], "taskId": task["id"][:160],
                    "workerId": worker_id[:160], "worker": req["worker"], "output": output,
                    "createdAt": js_utc(now - timedelta(seconds=1)),
                    "expiresAt": js_utc(now + timedelta(milliseconds=TTL_MS - 2000))}
    receipt = _put(root, "receipt", json.dumps(receipt_body, sort_keys=True).encode("utf-8"))
    r = nb.call("verifiedReuse", "admitCandidate",
                [{"root": str(root), "request": req, "output": output, "receipt": receipt,
                  "now": int(time.time() * 1000)}], timeout=60)
    if not r.ok:
        return UNJUDGED, {"reason": f"bridge {r.outcome}: {r.error}"}
    v = r.value or {}
    if not v.get("ok"):
        return REFUSED, {"reason": v.get("reason")}
    idx = _load_index(root)
    idx[fingerprint] = v["record"]
    _index_path(root).write_text(json.dumps(idx, indent=1), encoding="utf-8")
    _log(root, {"event": "admitted", "fingerprint": fingerprint, "task": task["id"], "plan": plan_id})
    return ADMITTED, {"fingerprint": fingerprint}


def lookup(root: str | Path, task: dict, bounds: dict, plan_id: str | None = None) -> tuple[str, dict]:
    """HIT hands back the prior draft (never accepted); MISS says why; UNJUDGED = could not ask."""
    root = Path(root)
    try:
        req = request_for(root, task, bounds)
    except OSError as exc:
        return MISS, {"reason": f"source unreadable: {exc}"}
    fp = nb.call("verifiedReuse", "buildFingerprint", [{"root": str(root), "request": req}], timeout=60)
    if not fp.ok:
        return UNJUDGED, {"reason": f"bridge {fp.outcome}: {fp.error}"}
    if not (fp.value or {}).get("ok"):
        return MISS, {"reason": (fp.value or {}).get("reason")}
    fingerprint = fp.value["fingerprint"]
    record = _load_index(root).get(fingerprint)
    if record is None:
        _log(root, {"event": "miss", "task": task["id"], "reason": "no admitted draft for these exact inputs"})
        return MISS, {"reason": "no admitted draft for these exact inputs", "fingerprint": fingerprint}
    target = {"planId": (plan_id or f"lookup-{uuid.uuid4().hex[:12]}")[:160], "taskId": task["id"][:160]}
    r = nb.call("verifiedReuse", "decideReuse",
                [{"root": str(root), "request": req, "record": record, "target": target,
                  "now": int(time.time() * 1000)}], timeout=60)
    if not r.ok:
        return UNJUDGED, {"reason": f"bridge {r.outcome}: {r.error}"}
    v = r.value or {}
    if not v.get("hit"):
        _log(root, {"event": "miss", "task": task["id"], "reason": v.get("reason")})
        return MISS, {"reason": v.get("reason"), "fingerprint": fingerprint}
    if v.get("accepted") is not False or v.get("needsFreshReview") is not True:
        # The vendored contract is that a hit is never an approval. If that ever changes upstream,
        # refuse rather than pass an approval through a cache.
        return REFUSED, {"reason": "reuse result claimed acceptance; a cache cannot approve"}
    chars = sum((root / p).stat().st_size for p in task["sourcePaths"])
    _log(root, {"event": "hit", "task": task["id"], "fingerprint": fingerprint,
                "avoided": {"reviewer_dispatches": 1, "source_chars": chars}})
    return HIT, {"draft": json.loads(v["text"]), "accepted": False, "needsFreshReview": True,
                 "sourceTask": v["sourceTask"], "fingerprint": fingerprint,
                 "avoided": {"reviewer_dispatches": 1, "source_chars": chars}}


def stats(root: str | Path) -> dict:
    p = store(root) / "ledger.jsonl"
    rows = []
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
    hits = [r for r in rows if r.get("event") == "hit"]
    return {"admitted": sum(1 for r in rows if r.get("event") == "admitted"),
            "hits": len(hits), "misses": sum(1 for r in rows if r.get("event") == "miss"),
            "reviewer_dispatches_avoided": sum(r["avoided"]["reviewer_dispatches"] for r in hits),
            "source_chars_avoided": sum(r["avoided"]["source_chars"] for r in hits),
            "tokens_saved": None, "cost_saved": None}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Verified reuse of read-only batch drafts")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("stats")
    s.add_argument("--root", default=os.getcwd())
    a = ap.parse_args(argv)
    print(json.dumps(stats(a.root), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
