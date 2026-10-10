"""Authority capsules: an Owner approval compiled into durable, scoped, revocable authority.

Spec: ~/.claude/plans/owner-interface-compiler-v1.md (oic-v1, S1). EXTENDS autonomy_gate: the
CPP_AUTONOMY_AUTHORIZED env list stays a ceiling of action KINDS; a capsule is what can actually
authorize a concrete effect, and only one that names it.

A capsule binds an approval to what it was given for:
  programme / goal       what the work is
  plan {path, sha256}    the exact plan version; an edited plan invalidates the capsule
  level 1-3              L4 (new irreversible / high blast radius) and L5 (credentials, legal,
                         money, physical presence) are never grantable here
  effects / denied       named effects only; no wildcard; denied wins
  targets                key -> value (or list) every request must match, e.g. pr=545, head_sha=...
  conditions             fact names that must be True at check time, e.g. ci_green
  delegation_depth       how many times it may be narrowed for a child; a child can never widen
  expires_at             hard expiry (epoch seconds)

Ledger: append-only JSONL (grant / revoke rows); the latest row per id wins. Every check() verdict is
also written to the autonomy-decisions log, so any effect can answer "which approval allowed this".
Missing anything is a NO: no capsule, a missing fact, an unreadable plan, an unknown effect.

    python -m modules.autonomy_gate.capsules list
    python -m modules.autonomy_gate.capsules check --effect pr.merge --target pr=545 --fact ci_green=true
    python -m modules.autonomy_gate.capsules revoke <id|all> --by owner --reason "..."
exit 0 = allowed, 10 = not allowed, 2 = usage error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

MAX_LEVEL = 3
_REQUIRED = ("programme", "level", "effects", "expires_at", "provenance")


def ledger_path() -> Path:
    base = os.environ.get("CPP_AUTHORITY_DIR") or str(Path.home() / ".claude" / "state" / "authority")
    return Path(base) / "capsules.jsonl"


def _append(row: dict) -> None:
    p = ledger_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _rows() -> list[dict]:
    p = ledger_path()
    if not p.is_file():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except ValueError:
                continue    # a torn line is skipped, never read as a grant
    return out


def load() -> dict[str, dict]:
    """Current capsules by id; a revoke row marks its target (or every capsule, for "all")."""
    caps: dict[str, dict] = {}
    for r in _rows():
        if r.get("op") == "grant" and r.get("id"):
            caps[r["id"]] = dict(r["capsule"], id=r["id"], revoked=None)
        elif r.get("op") == "revoke":
            tgt = r.get("id")
            for cid, c in caps.items():
                if tgt in ("all", cid) and c["revoked"] is None:
                    c["revoked"] = {"at": r.get("at"), "by": r.get("by"), "reason": r.get("reason")}
    # A revoked ancestor revokes every descendant, at any depth.
    for c in caps.values():
        seen, p = set(), c.get("parent")
        while p and p not in seen and c["revoked"] is None:
            seen.add(p)
            anc = caps.get(p)
            if anc is None:
                break
            if anc["revoked"]:
                c["revoked"] = dict(anc["revoked"], inherited_from=p)
            p = anc.get("parent")
    return caps


def _sha256_file(path: str) -> str | None:
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def _validate(c: dict) -> None:
    missing = [k for k in _REQUIRED if c.get(k) in (None, "", [])]
    if missing:
        raise ValueError(f"capsule missing {missing}")
    if not isinstance(c["level"], int) or not 1 <= c["level"] <= MAX_LEVEL:
        raise ValueError(f"level {c['level']!r} is not grantable here (1..{MAX_LEVEL}); L4/L5 stay with the Owner")
    if any(e in ("*", "all", "any") for e in c["effects"]):
        raise ValueError("wildcard effects are not grantable")
    if int(c.get("delegation_depth", 0)) < 0:
        raise ValueError("negative delegation depth")
    plan = c.get("plan")
    if plan and not (plan.get("path") and plan.get("sha256")):
        raise ValueError("a plan binding needs both path and sha256")


def grant(capsule: dict, *, now: float | None = None) -> str:
    c = dict(capsule)
    c.setdefault("granted_at", now or time.time())
    c.setdefault("denied", [])
    c.setdefault("targets", {})
    c.setdefault("conditions", [])
    c.setdefault("delegation_depth", 0)
    _validate(c)
    cid = c.get("id") or "cap-" + hashlib.sha256(json.dumps(c, sort_keys=True).encode()).hexdigest()[:12]
    c.pop("id", None)
    if cid in load():
        return cid          # idempotent: the same grant twice is one capsule
    _append({"op": "grant", "id": cid, "at": c["granted_at"], "capsule": c})
    return cid


def revoke(cid: str, *, by: str, reason: str, now: float | None = None) -> None:
    _append({"op": "revoke", "id": cid, "by": by, "reason": reason, "at": now or time.time()})


def _subset(child_v, parent_v) -> bool:
    cv = child_v if isinstance(child_v, list) else [child_v]
    pv = parent_v if isinstance(parent_v, list) else [parent_v]
    return all(v in pv for v in cv)


def derive(parent_id: str, child: dict, *, now: float | None = None) -> str:
    """A child capsule: a subset of its parent, one delegation level down. Raises if it would widen."""
    p = load().get(parent_id)
    if not p:
        raise ValueError(f"no capsule {parent_id}")
    if p["revoked"]:
        raise ValueError(f"{parent_id} is revoked")
    if int(p.get("delegation_depth", 0)) < 1:
        raise ValueError(f"{parent_id} may not be delegated")
    c = dict(child)
    c.setdefault("programme", p["programme"])
    c.setdefault("goal", p.get("goal"))
    c.setdefault("plan", p.get("plan"))
    c.setdefault("provenance", {"derived_from": parent_id, **(p.get("provenance") or {})})
    c.setdefault("expires_at", p["expires_at"])
    c.setdefault("level", p["level"])
    c["denied"] = sorted(set(c.get("denied", [])) | set(p.get("denied", [])))
    c["conditions"] = sorted(set(c.get("conditions", [])) | set(p.get("conditions", [])))
    c["parent"] = parent_id
    c["delegation_depth"] = min(int(c.get("delegation_depth", 0)), int(p["delegation_depth"]) - 1)
    widened = [e for e in c.get("effects", []) if e not in p["effects"]]
    if widened:
        raise ValueError(f"child widens effects {widened}")
    if c["level"] > p["level"] or c["expires_at"] > p["expires_at"]:
        raise ValueError("child widens level or expiry")
    for k, pv in (p.get("targets") or {}).items():
        if k not in (c.get("targets") or {}):
            c.setdefault("targets", {})[k] = pv
        elif not _subset(c["targets"][k], pv):
            raise ValueError(f"child widens target {k}")
    if c.get("plan") != p.get("plan"):
        raise ValueError("child must keep its parent's plan binding")
    return grant(c, now=now)


def check(effect: str, *, target: dict | None = None, facts: dict | None = None,
          now: float | None = None, record_source: str | None = "capsules.check") -> dict:
    """Is there a live capsule that authorizes exactly this effect on this target, now?"""
    now = now or time.time()
    target, facts = target or {}, facts or {}
    reasons = []
    try:
        caps = load()
    except Exception as exc:  # noqa: BLE001 -- FAIL CLOSED
        return _verdict(False, None, [f"ledger unreadable ({exc.__class__.__name__})"], effect, record_source)
    for cid, c in caps.items():
        why = _mismatch(c, effect, target, facts, now)
        if not why:
            return _verdict(True, cid, [], effect, record_source)
        reasons.append(f"{cid}: {why}")
    return _verdict(False, None, reasons or ["no capsule"], effect, record_source)


def _mismatch(c: dict, effect: str, target: dict, facts: dict, now: float) -> str | None:
    if c.get("revoked"):
        return "revoked"
    if now >= float(c["expires_at"]):
        return "expired"
    if effect in c.get("denied", []):
        return f"{effect} is denied"
    if effect not in c["effects"]:
        return f"{effect} not granted"
    for k, want in (c.get("targets") or {}).items():
        have = target.get(k)
        if have is None:
            return f"target {k} not given"      # missing is not a match
        if not _subset(have, want):
            return f"target {k}={have!r} not in {want!r}"
    for cond in c.get("conditions", []):
        if facts.get(cond) is not True:
            return f"condition {cond} not true ({facts.get(cond)!r})"
    plan = c.get("plan")
    if plan and _sha256_file(plan["path"]) != plan["sha256"]:
        return "plan changed or unreadable since approval"
    return None


def _verdict(ok: bool, cid, reasons, effect, source) -> dict:
    v = {"allowed": ok, "capsule": cid, "effect": effect, "why": reasons}
    if source:
        try:
            from modules.autonomy_gate.gate import record, AGENT, OWNER
            record({"owner": AGENT if ok else OWNER, "category": "capsule",
                    "why": f"{'allowed by ' + cid if ok else 'no capsule'}: {effect}"},
                   f"effect {effect}", source=source)
        except Exception:  # noqa: BLE001 -- the audit row is best-effort; the verdict is not
            pass
    return v


def _kv(items) -> dict:
    out = {}
    for it in items or []:
        k, _, v = it.partition("=")
        out[k] = {"true": True, "false": False}.get(v.lower(), v)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="capsules")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    g = sub.add_parser("grant")
    g.add_argument("--file", required=True)
    ck = sub.add_parser("check")
    ck.add_argument("--effect", required=True)
    ck.add_argument("--target", nargs="*")
    ck.add_argument("--fact", nargs="*")
    rv = sub.add_parser("revoke")
    rv.add_argument("id")
    rv.add_argument("--by", required=True)
    rv.add_argument("--reason", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "list":
        for cid, c in load().items():
            state = "REVOKED" if c["revoked"] else ("EXPIRED" if time.time() >= c["expires_at"] else "LIVE")
            print(f"{cid} {state} L{c['level']} {c['programme']} effects={c['effects']} targets={c.get('targets')}")
        return 0
    if a.cmd == "grant":
        print(grant(json.loads(Path(a.file).read_text(encoding="utf-8"))))
        return 0
    if a.cmd == "revoke":
        revoke(a.id, by=a.by, reason=a.reason)
        print(f"revoked {a.id}")
        return 0
    v = check(a.effect, target=_kv(a.target), facts=_kv(a.fact))
    print(json.dumps(v, ensure_ascii=False))
    return 0 if v["allowed"] else 10


if __name__ == "__main__":
    sys.exit(main())
