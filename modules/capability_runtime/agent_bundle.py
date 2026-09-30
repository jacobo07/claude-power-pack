#!/usr/bin/env python3
"""agent_bundle.py -- validate and persist a specialist's proof bundle.

Spec: vault/specs/agent-capability-virtualization.md (S2). Contract text:
vault/capability_runtime/agent_primitives/proof-bundle-v1.md.

What crosses the agent boundary is a small, typed bundle, not a transcript. The
specialist's full trajectory stays in its own subagent transcript; the parent
keeps the bundle, which carries pointers (`path:line`) instead of copied text.

Verdicts (never a silent pass):
  VALID      well-formed, from this compilation, read the current state
  STALE      well-formed, but computed against a repo state that has moved
  INVALID    malformed, or claims evidence it does not cite, or from another spec
  MISSING    no fenced json block in the reply at all

  python -m modules.capability_runtime.agent_bundle accept <reply.txt> --spec <id> [--state <sha>]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.capability_runtime import agent_spec as A  # noqa: E402

STORE = Path.home() / ".claude" / "state" / "agent_bundles"
STATUSES = {"OBSERVED", "PROVEN", "INFERRED", "UNKNOWN", "CONFLICTING"}
SEVERITIES = {"critical", "high", "medium", "low", "info"}
REQUIRED = ("bundle", "spec", "spec_hash", "state_version", "summary", "claims",
            "counterevidence", "unknowns", "recommendation")
_FENCE = re.compile(r"```json\s*\n(.*?)\n```", re.S)
_CITE = re.compile(r"\S+:\d+")
SUMMARY_MAX = 600


def extract(reply: str) -> dict | None:
    blocks = _FENCE.findall(reply or "")
    if not blocks:
        return None
    try:
        obj = json.loads(blocks[-1])
    except json.JSONDecodeError:
        return {"__unparseable__": True}
    return obj if isinstance(obj, dict) else {"__unparseable__": True}


def validate(reply: str, spec: "A.AgentSpec", current_state: str) -> dict:
    b = extract(reply)
    if b is None:
        return {"verdict": "MISSING", "reasons": ["no fenced json block"]}
    if b.get("__unparseable__"):
        return {"verdict": "INVALID", "reasons": ["json block does not parse to an object"]}
    reasons = [f"missing field {k}" for k in REQUIRED if k not in b]
    if b.get("bundle") != "proof-bundle/v1":
        reasons.append(f"bundle={b.get('bundle')!r}")
    if b.get("spec") != f"{spec.id}@{spec.contract.version}":
        reasons.append(f"spec {b.get('spec')!r} is not {spec.id}@{spec.contract.version}")
    if b.get("spec_hash") != spec.spec_hash():
        reasons.append("spec_hash does not match this compilation")
    if not isinstance(b.get("summary", ""), str) or len(b.get("summary", "")) > SUMMARY_MAX:
        reasons.append("summary missing or longer than 600 chars")
    claims = b.get("claims")
    if not isinstance(claims, list):
        reasons.append("claims is not a list")
        claims = []
    for c in claims:
        cid = c.get("id", "?") if isinstance(c, dict) else "?"
        if not isinstance(c, dict):
            reasons.append("a claim is not an object")
            continue
        if c.get("status") not in STATUSES:
            reasons.append(f"{cid}: status {c.get('status')!r}")
        if c.get("severity", "info") not in SEVERITIES:
            reasons.append(f"{cid}: severity {c.get('severity')!r}")
        ev = c.get("evidence") or []
        if c.get("status") in ("OBSERVED", "PROVEN") and not any(_CITE.search(str(e)) for e in ev):
            reasons.append(f"{cid}: {c.get('status')} without a path:line citation")
    if reasons:
        return {"verdict": "INVALID", "reasons": reasons, "bundle": b}
    sv = b.get("state_version")
    if sv not in ("none",) and current_state not in ("none",) and sv != current_state:
        return {"verdict": "STALE", "reasons": [f"read {sv[:12]}, repo is now {current_state[:12]}"], "bundle": b}
    return {"verdict": "VALID", "reasons": [], "bundle": b}


def accept(reply: str, spec_id: str, current_state: str | None = None, store: Path | None = None) -> dict:
    spec = A.load(spec_id)
    cur = current_state if current_state is not None else A.current_state_version()
    res = validate(reply, spec, cur)
    if res["verdict"] in ("VALID", "STALE"):
        root = (store or STORE) / spec_id
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{res['verdict'].lower()}.json"
        path.write_text(json.dumps({"verdict": res["verdict"], "reasons": res["reasons"],
                                    **res["bundle"]}, indent=1), encoding="utf-8")
        res["stored"] = str(path)
    return res


def compact(res: dict) -> str:
    """The one line the parent keeps: verdict, size, where the rest lives."""
    b = res.get("bundle") or {}
    n = len(b.get("claims") or [])
    tail = f" -> {res['stored']}" if res.get("stored") else ""
    why = f" ({'; '.join(res['reasons'][:3])})" if res["reasons"] else ""
    return f"BUNDLE {res['verdict']} claims={n}{why} :: {str(b.get('summary', ''))[:200]}{tail}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="agent_bundle")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("accept"); a.add_argument("reply"); a.add_argument("--spec", required=True)
    a.add_argument("--state")
    args = ap.parse_args(argv)
    try:
        res = accept(Path(args.reply).read_text(encoding="utf-8"), args.spec, args.state)
    except A.AgentSpecError as e:
        print(f"AGENTSPEC_ERROR {e.code} {e}", file=sys.stderr)
        return 2
    print(compact(res))
    return 0 if res["verdict"] == "VALID" else 1


if __name__ == "__main__":
    sys.exit(main())
