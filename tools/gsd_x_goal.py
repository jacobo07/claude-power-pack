#!/usr/bin/env python3
"""The goal spine's entrance: declare a goal, see why it has not converged, act.

    python tools/gsd_x_goal.py declare  --goal <id> --root <repo> --intent "..." \
                                        [--acceptance ...] [--constraint ...] [--scope-path ...]
    python tools/gsd_x_goal.py plane    --goal <id> --root <repo> --plane REALITY \
                                        --not-applicable --reason "..."
    python tools/gsd_x_goal.py oblige   --goal <id> --root <repo> --id ob-1 --plane OUTCOME \
                                        --text "..." --gate "python tools/x.py" --gate-file tools/x.py
    python tools/gsd_x_goal.py record-gates --goal <id> --root <repo>
    python tools/gsd_x_goal.py sweep    --goal <id> --root <repo> [--dry-run]
    python tools/gsd_x_goal.py retire   --goal <id> --root <repo> --id ob-1 \
                                        --disposition REJECTED --reason "..."
    python tools/gsd_x_goal.py disposition-failure --goal <id> --root <repo> --id f-1 \
                                        --disposition fixed --reason "..."
    python tools/gsd_x_goal.py bind     --goal <id> --root <repo>
    python tools/gsd_x_goal.py status   --goal <id> --root <repo> [--json]
    python tools/gsd_x_goal.py explain  --goal <id> --root <repo>
    python tools/gsd_x_goal.py reconcile --goal <id> --root <repo> [--apply] [--provider ...]
    python tools/gsd_x_goal.py judge    --goal <id> --root <repo> --worktree <path>
    python tools/gsd_x_goal.py export   --goal <id> --root <repo> --to <file>
    python tools/gsd_x_goal.py restore  --goal <id> --root <repo> --from <file>

Exit codes describe the ANSWER, not the process: 0 the command did what it says,
1 the goal is not converged / the closure is blocked / the judge refused, 2 the
command could not run. A reader must be able to tell "this goal is not done"
from "this tool broke".
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.gsd_x.goal import brief as br              # noqa: E402
from modules.gsd_x.goal import contract as gc           # noqa: E402
from modules.gsd_x.goal import convergence as cv        # noqa: E402
from modules.gsd_x.goal import epoch as ep              # noqa: E402
from modules.gsd_x.goal import git_state as gs          # noqa: E402
from modules.gsd_x.goal import judge as jd              # noqa: E402
from modules.gsd_x.goal import log as gl                # noqa: E402
from modules.gsd_x.goal import reconcile as rc          # noqa: E402
from modules.gsd_x.goal.providers.gate import GateProvider        # noqa: E402
from modules.gsd_x.mission import store as st           # noqa: E402

COULD_NOT_RUN = 2


def _log(args) -> gl.GoalLog:
    return gl.GoalLog(gl.repo_id(Path(args.root)), args.goal)


def _state(args) -> gc.GoalState:
    return gc.project(_log(args))


def _tree(state: gc.GoalState, root: Path) -> str:
    return gs.tree_id(root, state.scope.get("paths") or ["."])


def cmd_declare(args) -> int:
    lg = _log(args)
    intent = args.intent
    if args.intent_file:
        intent = Path(args.intent_file).read_text(encoding="utf-8-sig")
    s = gc.declare(lg, intent, args.acceptance, args.constraint,
                   {"paths": args.scope_path or []}, args.actor)
    print(f"declared {s.goal_id} @ revision {s.revision}")
    print(f"store: {lg.dir}")
    return 0


def cmd_plane(args) -> int:
    lg = _log(args)
    applicable = not args.not_applicable
    cv.set_plane(lg, gc.project(lg), args.plane, applicable, args.reason or "", args.actor)
    print(f"{args.plane}: {'applies' if applicable else 'NOT APPLICABLE -- ' + args.reason}")
    return 0


def cmd_oblige(args) -> int:
    lg = _log(args)
    # New obligations pin eol-invariantly (UWCP S1-9): the judge may run on a
    # Linux node against a checkout made on Windows.
    pin = gs.file_pin(Path(args.root), args.gate_file, gs.BLOB)
    cv.accept_obligation(lg, gc.project(lg), args.id, args.plane, args.text, args.gate,
                         pin, args.actor, gate_class=args.gate_class)
    print(f"accepted {args.id} ({args.plane}); proven by {args.gate!r} "
          f"({args.gate_class or 'unstated'} gate)")
    for rel, digest in pin:
        print(f"  pinned {rel} {digest[:16]}...")
    return 0


def cmd_retire(args) -> int:
    """Retire an obligation that will not be proven, with a reason.

    Reachable from here because a writer only an ad-hoc script can call is a
    capability the tool does not have. The refusals live in `convergence`, not
    in this argument parser: SATISFIED is not offered as a choice AND would be
    refused if it were.
    """
    lg = _log(args)
    cv.disposition_obligation(lg, gc.project(lg), args.id, args.disposition,
                              args.reason, args.actor)
    print(f"retired {args.id} as {args.disposition}: {args.reason}")
    s = gc.project(lg)
    closure = cv.goal_closure(s, _tree(s, Path(args.root)), ep.open_epochs(s))
    still = [b for b in closure.blocking if args.id in b or "retired unproven" in b]
    for b in still:
        print(f"  still blocking: {b}")
    return 0


def cmd_dispose_failure(args) -> int:
    lg = _log(args)
    cv.disposition_failure(lg, gc.project(lg), args.id, args.disposition,
                           args.reason, args.actor)
    print(f"failure {args.id}: {args.disposition} -- {args.reason}")
    return 0


def cmd_bind(args) -> int:
    lg = _log(args)
    gc.project(lg)                       # refuses if the goal is not declared
    p = st.bind(Path(args.root), lg.repo, args.goal)
    print(f"bound {args.root} to goal {args.goal}: {p}")
    print("this root's obligations and intent now live in the goal log, and the per-root "
          "mission store refuses writes")
    return 0


def cmd_status(args) -> int:
    s = _state(args)
    root = Path(args.root)
    tree = _tree(s, root)
    closure = cv.goal_closure(s, tree, ep.open_epochs(s))
    conv = cv.project_convergence(s)
    eps = ep.project_epochs(s)
    if args.json:
        print(json.dumps({"goal": s.goal_id, "revision": s.revision, "tree": tree,
                          "may_close": closure.may_close, "blocking": closure.blocking,
                          "planes": {k: v[0] for k, v in closure.planes.items()},
                          "epochs": {k: {"state": e.state, "outcome": e.outcome,
                                         "provider": e.provider} for k, e in eps.items()},
                          "last_seq": s.last_seq}, indent=2))
        return 0 if closure.may_close else 1
    print(f"goal     : {s.goal_id}")
    print(f"revision : {s.revision}  (events: {s.last_seq})")
    print(f"tree     : {tree}")
    print(f"intent   : {s.intent[:100]}")
    print("planes   :")
    for plane, (state, reason) in closure.planes.items():
        print(f"  {plane:18} {state}{(' -- ' + reason) if reason else ''}")
    print("obligations:")
    for o in conv.obligations.values():
        print(f"  {o.identifier:22} {o.plane:16} {o.disposition}")
    if eps:
        print("epochs   :")
        for e in eps.values():
            print(f"  {e.epoch_id:18} {e.provider:18} {e.state} {e.outcome}")
    print(f"\nCLOSURE  : {'CLEAR (a judge must still certify)' if closure.may_close else 'BLOCKED'}")
    for b in closure.blocking:
        print(f"  - {b}")
    return 0 if closure.may_close else 1


def cmd_record_gates(args) -> int:
    """Run the suites autonomy depends on, here, now, and record what they said.

    The sweep refuses to act until this record is green AT THE CURRENT COMMIT of
    the engine, so this is not a formality: it is the thing that makes a green
    recorded for other code stop authorising this code.
    """
    from modules.gsd_x.goal import sweep as sw
    rec = sw.record_gates(ROOT)
    for suite, r in rec["suites"].items():
        print(f"  {'OK  ' if r['ok'] else 'FAIL'} {suite}: {r['detail']}")
    print(f"\nrecorded at {rec['head'][:12]} -> {'GREEN' if rec['green'] else 'NOT GREEN'}")
    print(f"record: {sw.record_path()}")
    return 0 if rec["green"] else 1


def cmd_sweep(args) -> int:
    """One unattended pass over this goal -- the entrance a scheduler calls.

    Until this existed the sweep was reachable only from its own test suite,
    which is a capability the product did not have. It prints what it did and
    nothing when it did nothing, because a scheduler that speaks every five
    minutes is one nobody reads.
    """
    from modules.gsd_x.goal import sweep as sw
    lg = _log(args)
    report = sw.sweep(ROOT, [(lg, Path(args.root))], dry_run=args.dry_run,
                      actor=args.actor)
    if report.refused:
        print(f"REFUSED: {report.refused}")
        return 1
    for line in report.skipped:
        print(f"  skipped {line}")
    out = report.render()
    print(out if out else "(nothing to do)")
    return 0


def cmd_explain(args) -> int:
    s = _state(args)
    root = Path(args.root)
    closure = cv.goal_closure(s, _tree(s, root), ep.open_epochs(s))
    print(br.compile_brief(s, closure.blocking, str(root), args.task or
                           "Explain what remains.", s.authority))
    return 0 if closure.may_close else 1


def _context(args, s: gc.GoalState, providers, observations=None) -> rc.Context:
    import time
    root = Path(args.root)
    tree = _tree(s, root)
    if observations is None:
        # Observe what is actually running. Without this, every command that
        # reads a decision answered "could not observe it" about a gate this
        # same tool had started -- and an unreadable observation is never an
        # ending, so the CLI reported WAIT forever and could make no progress.
        prov = GateProvider(Path(args.run_dir) if getattr(args, "run_dir", None)
                            else Path(_log(args).dir) / "runs")
        observations = {e.epoch_id: prov.observe(e.handle)
                        for e in ep.project_epochs(s).values()
                        if e.state == "running" and e.provider == "gate" and e.handle}
    return rc.Context(state=s, tree_hash=tree,
                      scope_hash=ep.scope_hash(root, s.scope.get("paths") or ["."]),
                      observations=observations or {}, now=time.time(),
                      budget=s.budget, providers=tuple(providers),
                      # Without this the judge's receipt is written and never read,
                      # and CONVERGED is unreachable by anything but a test.
                      judge=jd.current(s, tree, s.revision),
                      blocked_on=args.blocked_on or "")


def cmd_reconcile(args) -> int:
    s = _state(args)
    providers = args.provider or ["gate"]
    d = rc.decide(_context(args, s, providers))
    print(rc.render(d))
    if not args.apply:
        print("\n(decision only; pass --apply to act on it)")
        return 0 if d.kind in (rc.CONVERGED, rc.WAIT) else 1
    if d.kind not in (rc.NEXT_EPOCH, rc.RECOVER, rc.HARVEST):
        print(f"\nnothing to apply: {d.kind} is not an action")
        return 0 if d.kind in (rc.CONVERGED, rc.WAIT) else 1
    if d.kind == rc.NEXT_EPOCH and d.provider != "gate":
        # Only the deterministic provider is wired into --apply here. Work
        # providers spend an account or a session and are dispatched
        # deliberately, not as a side effect of a status command.
        print(f"\n{d.provider} epochs are dispatched explicitly, not from reconcile --apply")
        return 1
    # One pass of THE driver, not a second copy of it. This used to dispatch a
    # gate with its own inline code and then had no way to observe or harvest
    # one: an operator could start a gate from the CLI and nothing in the CLI
    # could ever finish it, so the epoch stayed `running` forever. It also built
    # its epoch record without the gate spec -- the exact defect already fixed in
    # the sweep, surviving here because the logic had been written twice.
    from modules.gsd_x.goal import sweep as sw
    run_dir = Path(args.run_dir) if args.run_dir else Path(_log(args).dir) / "runs"
    acted = sw.sweep_goal(_log(args), Path(args.root), providers=tuple(providers),
                          run_dir=run_dir, actor=args.actor)
    print()
    for line in acted:
        print(line)
    return 0


def cmd_judge(args) -> int:
    s = _state(args)
    worktree = Path(args.worktree or args.root)
    receipt = jd.judge(s, _tree(s, Path(args.root)), worktree,
                       s.scope.get("paths") or ["."])
    print(json.dumps(receipt.to_dict(), indent=2))
    if args.record:
        # Every verdict, not only PASS: a refusal is a fact about the goal, and
        # the reconciler has a branch for it that nothing could otherwise reach.
        jd.record(_log(args), s, receipt, args.actor)
        print(f"\nrecorded the judge receipt ({receipt.verdict}) on the goal log")
    return 0 if receipt.verdict == jd.PASS else 1


def cmd_export(args) -> int:
    """A checkpoint for cold birth: the events, as they are, labelled derived."""
    lg = _log(args)
    events = [e.to_dict() for e in lg.read()]
    payload = {"kind": "gsd-x goal export (DERIVED -- the host store is the owner)",
               "repo": lg.repo, "goal_id": lg.goal_id, "events": events}
    Path(args.to).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                             encoding="utf-8")
    print(f"exported {len(events)} events to {args.to}")
    return 0


def cmd_restore(args) -> int:
    """Refuse to regress a store. An export older than what is here would replay
    stale sequence numbers over live ones."""
    lg = _log(args)
    payload = json.loads(Path(getattr(args, "from")).read_text(encoding="utf-8-sig"))
    incoming = payload.get("events") or []
    existing = lg.read()
    if len(incoming) < len(existing):
        print(f"REFUSED: the export has {len(incoming)} events, the store has "
              f"{len(existing)}; restoring would lose what is here")
        return COULD_NOT_RUN
    for i, ev in enumerate(existing):
        if incoming[i].get("digest") != ev.digest:
            print(f"REFUSED: the export diverges from this store at seq {ev.seq}")
            return COULD_NOT_RUN
    written = 0
    for raw in incoming[len(existing):]:
        lg.publish(raw)
        written += 1
    print(f"restored {written} event(s); the store now holds {len(lg.read())}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--goal", required=True)
        p.add_argument("--root", required=True)
        p.add_argument("--actor", default="owner")
        return p

    d = common(sub.add_parser("declare"))
    d.add_argument("--intent", default="")
    d.add_argument("--intent-file")
    d.add_argument("--acceptance", action="append", default=[])
    d.add_argument("--constraint", action="append", default=[])
    d.add_argument("--scope-path", action="append", default=[])
    d.set_defaults(fn=cmd_declare)

    p = common(sub.add_parser("plane"))
    p.add_argument("--plane", required=True, choices=cv.PLANES)
    p.add_argument("--not-applicable", action="store_true")
    p.add_argument("--reason", default="")
    p.set_defaults(fn=cmd_plane)

    o = common(sub.add_parser("oblige"))
    o.add_argument("--id", required=True)
    o.add_argument("--plane", required=True, choices=cv.PLANES)
    o.add_argument("--text", required=True)
    o.add_argument("--gate", required=True)
    o.add_argument("--gate-file", action="append", required=True)
    o.add_argument("--gate-class", default="", choices=("",) + cv.GATE_CLASSES,
                   help="what kind of observation the gate makes. REALITY obligations "
                        "must declare in_game or live; it is never inferred from the plane")
    o.set_defaults(fn=cmd_oblige)

    common(sub.add_parser("record-gates")).set_defaults(fn=cmd_record_gates)

    sw_p = common(sub.add_parser("sweep"))
    sw_p.add_argument("--dry-run", action="store_true")
    sw_p.set_defaults(fn=cmd_sweep)

    rt = common(sub.add_parser("retire"))
    rt.add_argument("--id", required=True)
    rt.add_argument("--disposition", required=True,
                    choices=sorted(cv.DECLARABLE_DISPOSITIONS))
    rt.add_argument("--reason", required=True)
    rt.set_defaults(fn=cmd_retire)

    df = common(sub.add_parser("disposition-failure"))
    df.add_argument("--id", required=True)
    df.add_argument("--disposition", required=True,
                    choices=sorted(cv.FAILURE_DISPOSITIONS))
    df.add_argument("--reason", required=True)
    df.set_defaults(fn=cmd_dispose_failure)

    common(sub.add_parser("bind")).set_defaults(fn=cmd_bind)

    s = common(sub.add_parser("status"))
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_status)

    e = common(sub.add_parser("explain"))
    e.add_argument("--task", default="")
    e.set_defaults(fn=cmd_explain)

    r = common(sub.add_parser("reconcile"))
    r.add_argument("--apply", action="store_true")
    r.add_argument("--provider", action="append", default=[])
    r.add_argument("--run-dir")
    # --gate-class is gone: the driver derives the class from the obligation's
    # PLANE (in_game for REALITY, unit otherwise), and a flag that cannot change
    # what is dispatched is worse than no flag.
    r.add_argument("--retired-gate-class", default="unit", help=argparse.SUPPRESS,
                   choices=("unit", "integration",
                                                            "in_game", "live"))
    r.add_argument("--blocked-on", default="")
    r.set_defaults(fn=cmd_reconcile)

    j = common(sub.add_parser("judge"))
    j.add_argument("--worktree")
    j.add_argument("--record", action="store_true")
    j.set_defaults(fn=cmd_judge)

    x = common(sub.add_parser("export"))
    x.add_argument("--to", required=True)
    x.set_defaults(fn=cmd_export)

    rs = common(sub.add_parser("restore"))
    rs.add_argument("--from", required=True, dest="from")
    rs.set_defaults(fn=cmd_restore)

    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except (gl.GoalLogError, FileNotFoundError, ValueError) as exc:
        # The COMMAND could not run. Distinct from a goal that is not converged,
        # which is exit 1 with a verdict.
        print(f"REFUSED: {exc.__class__.__name__}: {exc}")
        return COULD_NOT_RUN


if __name__ == "__main__":
    sys.exit(main())
