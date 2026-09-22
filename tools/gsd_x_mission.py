#!/usr/bin/env python3
"""Mission Intelligence CLI -- derive, inspect, gate, close.

    python tools/gsd_x_mission.py derive   <mission-root>
    python tools/gsd_x_mission.py contract <mission-root>
    python tools/gsd_x_mission.py closure  <mission-root> [--backlog-empty]
    python tools/gsd_x_mission.py check    <mission-root> [--raw]

`check` is the GSD seam. It is registered by
capabilities/cpp-gsd-x-mission/capability.json as a `ship:pre` gate whose
`check.predicate` (kind `command-exit-zero`) runs `check <PHASE_DIR>
--exit-code`; GSD reads the exit code (gate-predicate-evaluator.cjs). Without
--exit-code it emits the `{block, message}` envelope for the prose `kind:"gate"`
seam instead. GSD keeps the lifecycle; this only answers.

WHAT IS PROVEN, AND WHERE IT STOPS (2026-09-22). Through GSD's real capability
registry, its activation resolver and its `check predicate` CLI: open
obligations block naming them, a passing gate verdict clears them, narrative
and failing verdicts do not, and the hook renders only in a project whose
config sets `gsd_x_mission.enabled`. NOT proven: a live `/gsd:ship` run
dispatching it -- that workflow is driven by an agent reading markdown and
cannot be invoked from a tool call. See
vault/lessons/gsd-x-predicate-seam-measurements.md.

FACTS come from `FACTS.json` in the mission root when it is present (declared,
schema `gsdx-facts/1`, modules/gsd_x/mission/structured_facts.py) and from the
prose adapter over INTENT.txt + README.md otherwise. `derive` reports which.
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
from modules.gsd_x.mission import structured_facts as sf  # noqa: E402

INTENT_FILE = "INTENT.txt"
REALITY_FILE = "README.md"


def _read(root: Path, name: str) -> str:
    p = root / name
    return p.read_text(encoding="utf-8-sig") if p.is_file() else ""


def _derive(root: Path) -> tuple[list, list, str]:
    """Derive from FACTS.json when present, otherwise from prose.

    A FACTS.json that cannot be trusted raises StructuredFactsError rather than
    falling back to prose: a mission that declared its facts and got them wrong
    must not be silently re-read through the very vocabulary it was written to
    escape."""
    intent = _read(root, INTENT_FILE)
    reality = _read(root, REALITY_FILE)
    source = sf.source_of(root)
    if source == sf.SOURCE:
        cands, facts = ob.derive_from_facts(sf.load(sf.facts_path(root)), intent, reality)
    else:
        cands, facts = ob.derive(intent, reality)
    return [ob.judge(c) for c in cands], facts, source


def cmd_derive(args) -> int:
    root = Path(args.root).resolve()
    try:
        judged, facts, source = _derive(root)
    except sf.StructuredFactsError as exc:
        print(f"REFUSED  : {exc}")
        return 2
    print(f"source   : {source}")
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
    try:
        path = st.save(root, merged)
    except st.GoalBound as exc:
        print(f"REFUSED  : {exc}")
        return 2
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
    # A root bound to a goal has its obligations in the goal log. A closure
    # computed from this per-root file would be a second, disagreeing answer.
    st.refuse_if_bound(root)
    obs = st.load(root)
    contract = mc.project(root, intent=_read(root, INTENT_FILE).strip() or None,
                          obligations=obs)
    return cl.project_closure(contract, obs, backlog_empty, pr), obs


def cmd_closure(args) -> int:
    root = Path(args.root).resolve()
    try:
        receipt, _ = _closure(root, args.backlog_empty, args.production_reality)
    except st.GoalBound as exc:
        print(f"REFUSED  : {exc}")
        return 2
    print(receipt.render())
    return 0 if receipt.may_close else 1


def _goal_gate_payload(root: Path, bound: dict) -> dict:
    """The same gate answer, computed from the goal that owns this root.

    Imported here rather than at module import time: the mission path must keep
    working in a tree where the goal package is absent, and a gate that fails to
    import is a gate that blocks every wave.
    """
    from modules.gsd_x.goal import contract as gcon
    from modules.gsd_x.goal import convergence as gconv
    from modules.gsd_x.goal import epoch as gep
    from modules.gsd_x.goal import git_state as ggit
    from modules.gsd_x.goal import log as glog

    lg = glog.GoalLog(bound["repo"], bound["goal_id"])
    state = gcon.project(lg)
    paths = state.scope.get("paths") or ["."]
    closure = gconv.goal_closure(state, ggit.tree_id(root, paths), gep.open_epochs(state))
    conv = gconv.project_convergence(state)
    open_ids = [o.identifier for o in conv.obligations.values()
                if o.disposition in (gconv.ACCEPTED, gconv.CANDIDATE, gconv.STALE)]
    return {
        "block": bool(open_ids),
        "message": ("; ".join(closure.blocking) if open_ids
                    else "no goal obligation is open"),
        "capId": "gsd-x-goal-obligations",
        "goal_id": bound["goal_id"],
        "revision": state.revision,
        "open_obligations": open_ids,
        "closure_blocking": list(closure.blocking),
    }


def cmd_check(args) -> int:
    """The GSD gate, for either of the two seams GSD actually offers.

    WITHOUT --exit-code: emits {block, message} and exits 0. This is the
    prose-dispatched `kind:"gate"` envelope; the dispatcher reads the fields,
    and a non-zero exit would be read as the CHECK having failed (its `onError`
    path), which is a different thing from a gate that blocked.

    WITH --exit-code: the same computation, reported as an exit code, for
    `check.predicate` + `command-exit-zero` -- the only seam that both runs a
    third party's own command AND may set `blocking: true`."""
    # A root that does not exist is UNREADABLE INPUT, never "nothing is open".
    # `${PHASE_DIR}` is interpolated by the host and an absent value becomes the
    # empty string (gate-predicate-evaluator.cjs `interpolate`, undefined => ''),
    # which resolves to the process cwd -- a directory with no obligations, so
    # the gate would report a clean pass on a MISCONFIGURED path. Measured: a
    # nonexistent root exited 0. That is the fail-open shape this whole gate
    # exists to prevent, so it is refused before anything is computed.
    if not str(args.root).strip() or not Path(args.root).is_dir():
        print(json.dumps({"error": f"UNREADABLE_INPUT: no such mission root: "
                                   f"{args.root!r}"}))
        return 2 if args.exit_code else 1
    root = Path(args.root).resolve()
    # A root bound to a goal has its obligations in the goal log. Failing closed
    # here would block every wave in that project; asking the WRONG store would
    # pass them. So the gate asks the goal, which is the owner.
    try:
        bound = st.bound_goal(root)
    except st.GoalBound as exc:
        print(json.dumps({"error": f"GoalBound: {exc}"}))
        return 2 if args.exit_code else 1
    if bound:
        try:
            payload = _goal_gate_payload(root, bound)
        except Exception as exc:                      # noqa: BLE001 -- boundary
            print(json.dumps({"error": f"{exc.__class__.__name__}: {exc}"}))
            return 2 if args.exit_code else 1
        print(json.dumps(payload, ensure_ascii=False)
              if args.raw else json.dumps(payload, indent=2, ensure_ascii=False))
        if not args.exit_code:
            return 0
        return 1 if payload["open_obligations"] else 0
    try:
        receipt, obs = _closure(root, args.backlog_empty, args.production_reality)
    except Exception as exc:                          # noqa: BLE001 -- boundary
        # An error here is the CHECK failing, not the mission passing. Say so in
        # the envelope so `onError` routes it rather than it reading as a pass.
        print(json.dumps({"error": f"{exc.__class__.__name__}: {exc}"}))
        return 2 if args.exit_code else 1
    open_ids = [o.identifier for o in obs if o.is_open]
    # `block` names the SAME condition the exit code names. It used to carry
    # `receipt.blocking`, which is wider (it includes "explicit backlog is not
    # empty"), so the two seams would have disagreed about the same phase: the
    # prose envelope blocking while the predicate passed. One computation, one
    # answer, whichever seam is reading. `receipt.blocking` is still reported,
    # under its own key, because it is genuine information about the mission --
    # it is simply not what a WAVE gate decides on.
    payload = {
        "block": bool(open_ids),
        "message": ("; ".join(receipt.blocking) if open_ids
                    else "no derived obligation is open"),
        "capId": "gsd-x-mission-obligations",
        "open_obligations": open_ids,
        "closure_blocking": list(receipt.blocking),
    }
    print(json.dumps(payload, ensure_ascii=False)
          if args.raw else json.dumps(payload, indent=2, ensure_ascii=False))
    if not args.exit_code:
        return 0
    # --exit-code is the GSD `check.predicate` / `command-exit-zero` seam, which
    # reads the EXIT CODE and nothing else (gate-predicate-evaluator.cjs:86-100:
    # `exitCode === 0` -> block:false, anything else -> block:true, with the
    # stdout tail as the gate message). The default path must keep returning 0,
    # because the OTHER seam -- the prose-dispatched `kind:"gate"` envelope --
    # reads these fields and treats a non-zero exit as the check having failed.
    # Two seams, two contracts, one computation; only the exit code differs.
    #
    # TWO values were within reach here and only one covers the effect.
    #
    # `closure` answers "may this mission close?" -- DENIED for a phase carrying
    # no obligations at all (measured: every section printed "(none)" and it
    # still exited 1). Wired to a wave gate it blocks every wave in every
    # project on the host.
    #
    # `receipt.blocking` is narrower and still too wide: it also carries
    # "explicit backlog is not empty", a mission-CLOSURE condition. Measured on
    # a mission root with nothing derived, `receipt.blocking` was non-empty
    # while `open_obligations` was []. Wiring the exit code to it made the GREEN
    # pole fail -- a wave with no obligations blocked anyway -- which is the
    # same defect as `closure`, one level in and harder to see.
    #
    # The effect this gate authorises is "hold the wave because a derived
    # obligation is still open". The field that covers exactly that effect is
    # the open set, so that is what decides the exit code.
    #
    # 1 = an obligation is open (the gate blocks on a real verdict).
    # 2 = the check itself could not run (the gate also blocks, fail-closed,
    #     but the envelope carries "error" rather than "block" so a human can
    #     tell a refusal from a breakage).
    return 1 if payload["open_obligations"] else 0


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
        # Defined on every subparser so `args.exit_code` always resolves; only
        # `check` gives it meaning. Default False keeps every existing caller's
        # exit code exactly as it was.
        p.add_argument("--exit-code", action="store_true")
        p.set_defaults(fn=fn)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
