"""Decision Plane: an Owner decision is a durable, self-contained contract, not chat and not STATE.md prose.

Spec: vault/plans/decision-plane-master-plan-2026-10-17.md (covers: decision-plane, owner-decision).

One append-only JSONL per mission under the long-run state dir. A Decision Object names its question, its evidence
(with a fingerprint), its orthogonal dimensions and its options. An option is SELECTABLE only when applying it needs
no further parameter: every dimension has a value and every amount carries its unit. Selecting yields a typed,
hashed Receipt; a replay is a no-op, a changed fingerprint invalidates the decision, an unknown id is a hard
failure (DanglingDecision), never a fallback to prose.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_long_run as lr  # noqa: E402

CLASSES = ("CAPITAL", "SCOPE", "PRODUCT", "SECURITY", "IRREVERSIBLE", "EXTERNAL", "RISK")
OPEN, READY, RESOLVED, SUPERSEDED, INVALIDATED = "OPEN", "READY_FOR_OWNER", "RESOLVED", "SUPERSEDED", "INVALIDATED"
_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,23}$")
_WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*")
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
DIM_KINDS = ("capital", "enum")


class DecisionError(Exception):
    pass


class DanglingDecision(DecisionError):
    """A decision id with no durable contract. Never recovered from prose or a remote grep."""


def _canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def fingerprint(evidence: dict) -> str:
    return hashlib.sha256(_canon(evidence).encode("utf-8")).hexdigest()[:16]


def store_path(mission_id: str) -> Path:
    if not _ID.match(mission_id or ""):
        raise DecisionError(f"invalid mission id: {mission_id!r}")
    return lr.state_dir() / f"decisions-{mission_id}.jsonl"


def _append(mission_id: str, row: dict) -> None:
    p = store_path(mission_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(_canon(row) + "\n")


def _rows(mission_id: str) -> list[dict]:
    p = store_path(mission_id)
    if not p.exists():
        return []
    out = []
    for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                out.append(json.loads(line))
            except ValueError as e:   # an unreadable store is not an empty one
                raise DecisionError(f"{p.name}:{n} unreadable: {e}") from e
    return out


def _fold(mission_id: str) -> dict[str, dict]:
    """Current state of every decision: the created object plus the events applied to it, in order."""
    cur: dict[str, dict] = {}
    for r in _rows(mission_id):
        ev, did = r.get("ev"), r.get("id")
        if ev == "created":
            cur[did] = {**r["object"], "status": r["object"].get("status", OPEN)}
        elif did in cur and ev == "resolved":
            cur[did].update(status=RESOLVED, receipt=r["receipt"])
        elif did in cur and ev == "invalidated":
            cur[did].update(status=INVALIDATED, invalidated_reason=r.get("reason"))
        elif did in cur and ev == "superseded":
            cur[did].update(status=SUPERSEDED, superseded_by=r.get("by"))
    return cur


def get(mission_id: str, decision_id: str) -> dict:
    d = _fold(mission_id).get(decision_id)
    if d is None:
        raise DanglingDecision(f"decision {decision_id} has no durable contract on {mission_id}")
    return d


def _option_problems(dec: dict, opt: dict) -> list[str]:
    bad = []
    tok = opt.get("token")
    if not isinstance(tok, str) or not _TOKEN.match(tok):
        bad.append(f"option token {tok!r} is not a short token")
    params = opt.get("params") or {}
    for dim in dec.get("dimensions", []):
        name, kind = dim["name"], dim["kind"]
        v = params.get(name)
        if v is None or v == "":
            bad.append(f"option {tok}: dimension {name} has no value")
        elif kind == "capital":
            if not (isinstance(v, dict) and isinstance(v.get("ceiling"), int) and v["ceiling"] > 0 and v.get("unit")):
                bad.append(f"option {tok}: capital {name} needs an integer ceiling > 0 and a unit")
        elif kind == "enum" and "allowed" in dim and v not in dim["allowed"]:
            bad.append(f"option {tok}: {name}={v!r} outside {dim['allowed']}")
    for extra in params:
        if extra not in {d["name"] for d in dec.get("dimensions", [])}:
            bad.append(f"option {tok}: parameter {extra} is not a declared dimension")
    return bad


def closure_gate(dec: dict) -> list[str]:
    """Empty list = every option is executable as presented. Anything else may not be shown to the Owner."""
    bad = []
    if dec.get("class") not in CLASSES:
        bad.append(f"unknown class {dec.get('class')!r}")
    dims = dec.get("dimensions") or []
    if not dims:
        bad.append("no dimensions declared")
    for d in dims:
        if d.get("kind") not in DIM_KINDS:
            bad.append(f"dimension {d.get('name')}: unknown kind {d.get('kind')!r}")
    opts = dec.get("options") or []
    if len(opts) < 1:
        bad.append("no options")
    toks = [o.get("token") for o in opts]
    if len(set(toks)) != len(toks):
        bad.append("duplicate option tokens")
    for o in opts:
        bad += _option_problems(dec, o)
    rec = (dec.get("recommendation") or {}).get("token")
    if rec is not None and rec not in toks:
        bad.append(f"recommendation {rec} is not an option")
    if not dec.get("evidence"):
        bad.append("no evidence handles")
    if not dec.get("consumers"):
        bad.append("no consumer mission")
    return bad


def create(mission_id: str, spec: dict, now: float | None = None) -> dict:
    """Persist a Decision Object. READY_FOR_OWNER only if the Closure Gate passes; otherwise OPEN and not surfaceable."""
    did = spec.get("id")
    if not isinstance(did, str) or not _ID.match(did):
        raise DecisionError(f"invalid decision id: {did!r}")
    if did in _fold(mission_id):
        raise DecisionError(f"decision {did} already exists on {mission_id}")
    obj = {k: spec.get(k) for k in ("id", "class", "question", "dimensions", "options", "recommendation",
                                    "consumers", "wake_policy", "invalidators")}
    obj["mission"] = mission_id
    obj["evidence"] = dict(spec.get("evidence") or {})
    obj["fingerprint"] = fingerprint(obj["evidence"])
    obj["created_at"] = time.time() if now is None else now
    obj["problems"] = closure_gate(obj)
    obj["status"] = READY if not obj["problems"] else OPEN
    _append(mission_id, {"ev": "created", "id": did, "object": obj})
    return obj


def surface(mission_id: str, decision_id: str) -> dict:
    """What the Owner is shown. Refuses an incomplete decision (the Closure Gate is the only door)."""
    d = get(mission_id, decision_id)
    if d["status"] != READY:
        raise DecisionError(f"{decision_id} is {d['status']}; it cannot be shown"
                            + (f": {d['problems']}" if d.get("problems") else ""))
    return {"id": d["id"], "question": d["question"], "options": d["options"], "recommendation": d["recommendation"],
            "valid_tokens": [o["token"] for o in d["options"]]}


def parse_choice(dec: dict, text: str) -> tuple[str | None, list[str]]:
    """Providerless mapping of short Owner input to ONE option token. (token, valid_tokens); token None = ambiguous."""
    valid = [o["token"] for o in dec["options"]]
    low = {t.lower(): t for t in valid}
    hits = {low[w.lower()] for w in _WORD.findall(text or "") if w.lower() in low}
    return (next(iter(hits)) if len(hits) == 1 else None), valid


def _receipt_sha(body: dict) -> str:
    return hashlib.sha256(_canon(body).encode("utf-8")).hexdigest()[:16]


def resolve(mission_id: str, decision_id: str, owner_text: str, evidence_now: dict | None = None,
            now: float | None = None) -> dict:
    """Owner selection -> typed Receipt. Idempotent; a stale decision is invalidated, never applied."""
    d = get(mission_id, decision_id)
    token, valid = parse_choice(d, owner_text)
    if d["status"] == RESOLVED:
        if token is not None and token == d["receipt"]["token"]:
            return {"receipt": d["receipt"], "recorded": False}
        raise DecisionError(f"{decision_id} is already resolved as {d['receipt']['token']}")
    if d["status"] != READY:
        raise DecisionError(f"{decision_id} is {d['status']}; it cannot be resolved")
    if token is None:
        raise DecisionError(f"ambiguous or empty selection; valid tokens: {valid}")
    if evidence_now is not None and fingerprint(evidence_now) != d["fingerprint"]:
        _append(mission_id, {"ev": "invalidated", "id": decision_id, "reason": "evidence fingerprint changed"})
        raise DecisionError(f"{decision_id} invalidated: evidence changed since the packet was compiled")
    opt = next(o for o in d["options"] if o["token"] == token)
    body = {"decision": decision_id, "mission": mission_id, "token": token, "params": opt["params"],
            "evidence_fp": d["fingerprint"], "consumers": d["consumers"]}
    receipt = {**body, "at": time.time() if now is None else now, "sha": _receipt_sha(body)}
    _append(mission_id, {"ev": "resolved", "id": decision_id, "receipt": receipt})
    return {"receipt": receipt, "recorded": True}


def invalidate(mission_id: str, decision_id: str, reason: str) -> None:
    get(mission_id, decision_id)
    _append(mission_id, {"ev": "invalidated", "id": decision_id, "reason": reason})


def supersede(mission_id: str, old_id: str, new_id: str) -> None:
    get(mission_id, old_id)
    get(mission_id, new_id)
    _append(mission_id, {"ev": "superseded", "id": old_id, "by": new_id})


def unresolved(mission_id: str) -> list[str]:
    """Decisions that still block their consumers (a WAITING mission wakes when this empties)."""
    return [i for i, d in _fold(mission_id).items() if d["status"] in (OPEN, READY)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="decision_plane")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create")
    c.add_argument("--mission", required=True)
    c.add_argument("--file", required=True, help="JSON decision spec")
    s = sub.add_parser("show")
    s.add_argument("--mission", required=True)
    s.add_argument("--decision", required=True)
    r = sub.add_parser("resolve")
    r.add_argument("--mission", required=True)
    r.add_argument("--decision", required=True)
    r.add_argument("--choice", required=True, help="the Owner's short input")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "create":
            o = create(a.mission, json.loads(Path(a.file).read_text(encoding="utf-8")))
            print(f"DECISION {o['id']} status={o['status']} problems={o['problems']}")
            return 0 if o["status"] == READY else 3
        if a.cmd == "show":
            print(json.dumps(surface(a.mission, a.decision), indent=2))
            return 0
        out = resolve(a.mission, a.decision, a.choice)
        print(f"RESOLVED {a.decision} token={out['receipt']['token']} sha={out['receipt']['sha']} "
              f"recorded={out['recorded']}")
        return 0
    except DecisionError as e:
        print(f"DECISION REFUSED: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
