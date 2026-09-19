#!/usr/bin/env python3
"""Mission Intelligence CLI -- derive, inspect, gate, close.

    python tools/gsd_x_mission.py derive   <mission-root>
    python tools/gsd_x_mission.py contract <mission-root>
    python tools/gsd_x_mission.py closure  <mission-root> [--backlog-empty]
    python tools/gsd_x_mission.py check    <mission-root> [--raw]

`check` is the GSD seam. GSD's capability-hook dispatcher evaluates a
`kind: "gate"` entry and reads two fields off the result -- `block` (boolean) and
`message` -- and when the hook is registered `blocking: true`, a `block: true`
halts wave completion (gsd-core/references/loop-hook-dispatch.md, and
workflows/execute-phase/steps/wave-post-gate-hooks.md). This command emits
exactly that envelope. GSD keeps the lifecycle; this only answers.

REGISTRATION IS UNVERIFIED, and that is stated rather than implied. The DISPATCH
contract above was read from GSD Core's own reference documents and is what this
output is shaped to. The MANIFEST format by which a capability registers a hook
at a point was not found on this host -- the only capability manifests present
are Power Pack's own Capability Runtime contracts, which are a different noun --
so this gate is proven to produce the envelope GSD consumes and is NOT proven to
be reachable from a GSD run. Production Reality is graded accordingly.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.gsd_x.mission import closure as cl          # noqa: E402
from modules.gsd_x.mission import contract as mc         # noqa: E402
from modules.gsd_x.mission import obligation as ob       # noqa: E402
from modules.gsd_x.mission import store as st            # noqa: E402

INTENT_FILE = "INTENT.txt"
REALITY_FILE = "README.md"


def _read(root: Path, name: str) -> str:
    p = root / name
    return p.read_text(encoding="utf-8-sig") if p.is_file() else ""


def _derive(root: Path) -> tuple[list, list]:
    intent = _read(root, INTENT_FILE)
    reality = _read(root, REALITY_FILE)
    cands, facts = ob.derive(intent, reality)
    return [ob.judge(c) for c in cands], facts


def cmd_derive(args) -> int:
    root = Path(args.root).resolve()
    judged, facts = _derive(root)
    existing = {o.identifier: o for o in st.load(root)}
    # An obligation already dispositioned by a human is not re-decided by a
    # re-run: re-derivation refreshes what is DERIVABLE, never what was DECIDED.
    for o in judged:
        prev = existing.get(o.identifier)
        if prev is not None and prev.disposition not in (ob.CANDIDATE, ob.ACCEPTED):
            o.disposition = prev.disposition
            o.disposition_reason = prev.disposition_reason
            o.revisit_when = prev.revisit_when
        elif prev is not None and prev.disposition == ob.SATISFIED:
            o.disposition = prev.disposition
    merged = list(judged)
    for ident, prev in existing.items():
        if ident not in {o.identifier for o in judged}:
            merged.append(ob.invalidate_if_parent_gone(prev, facts))
    path = st.save(root, merged)
    print(f"facts    : {len(facts)}")
    for f in facts:
        print(f"  {f.name:28} [{f.source}] {f.matched[:64]!r}")
    print(f"\nderived  : {len(judged)}")
    for o in merged:
        print(f"  {o.identifier}  {o.operator:30} {o.disposition}")
    print(f"\nstored   : {path}")
    return 0


def cmd_contract(args) -> int:
    root = Path(args.root).resolve()
    obs = st.load(root)
    contract = mc.project(root, intent=_read(root, INTENT_FILE).strip() or None,
                          obligations=obs)
    if args.raw:
        print(json.dumps(contract.to_dict(), indent=2, ensure_ascii=False))
        return 0
    print(f"mission: {contract.mission_id}\n")
    for f in contract.fields:
        v = f.value
        s = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
        print(f"  {f.name:22} [{f.kind:9}] {f.owner}")
        print(f"  {'':22}  {str(s)[:120]}")
    stored = [f.name for f in contract.by_kind(mc.STORED)]
    print(f"\nSTORED (owned here, nowhere else): {stored}")
    return 0


def _closure(root: Path, backlog_empty: bool, pr: str):
    obs = st.load(root)
    contract = mc.project(root, intent=_read(root, INTENT_FILE).strip() or None,
                          obligations=obs)
    return cl.project_closure(contract, obs, backlog_empty, pr), obs


def cmd_closure(args) -> int:
    root = Path(args.root).resolve()
    receipt, _ = _closure(root, args.backlog_empty, args.production_reality)
    print(receipt.render())
    return 0 if receipt.may_close else 1


def cmd_check(args) -> int:
    """The GSD gate. Emits {block, message} and exits 0 -- the dispatcher reads
    the fields, and a non-zero exit would be read as the CHECK having failed
    (its `onError` path), which is a different thing from a gate that blocked."""
    root = Path(args.root).resolve()
    try:
        receipt, obs = _closure(root, args.backlog_empty, args.production_reality)
    except Exception as exc:                          # noqa: BLE001 -- boundary
        # An error here is the CHECK failing, not the mission passing. Say so in
        # the envelope so `onError` routes it rather than it reading as a pass.
        print(json.dumps({"error": f"{exc.__class__.__name__}: {exc}"}))
        return 1
    blocked = receipt.blocking
    payload = {
        "block": bool(blocked),
        "message": ("; ".join(blocked) if blocked
                    else "no derived obligation is open"),
        "capId": "gsd-x-mission-obligations",
        "open_obligations": [o.identifier for o in obs if o.is_open],
    }
    print(json.dumps(payload, ensure_ascii=False)
          if args.raw else json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("derive", cmd_derive), ("contract", cmd_contract),
                     ("closure", cmd_closure), ("check", cmd_check)):
        p = sub.add_parser(name)
        p.add_argument("root")
        p.add_argument("--raw", action="store_true")
        p.add_argument("--backlog-empty", action="store_true")
        p.add_argument("--production-reality", default="UNPROVEN")
        p.set_defaults(fn=fn)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
