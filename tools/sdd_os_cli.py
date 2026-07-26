#!/usr/bin/env python3
"""SDD-OS command surface -- classify / spec / scaffold / drift / rollout.

Backs the /cpp-sdd-os command and drives the multi-repo rollout (S1-E).
Every subcommand is cwd-relative and works in any repo (E11).

    python tools/sdd_os_cli.py classify "add a billing endpoint"
    python tools/sdd_os_cli.py spec     "add a billing endpoint" [--repo P]
    python tools/sdd_os_cli.py scaffold [--repo P] [--dry-run]
    python tools/sdd_os_cli.py drift    [--repo P]
    python tools/sdd_os_cli.py status   [--repo P]
    python tools/sdd_os_cli.py rollout  --repos-file F [--dry-run]

Exit codes: 0 clean, 1 action required (drift found / spec missing), 2 usage.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.sdd_os.pre_exec_gate import (  # noqa: E402
    TIER_LABEL, enforce, evaluate,
)
from modules.sdd_os.scaffold import (  # noqa: E402
    check_drift, is_scaffolded, profile_repo, scaffold,
)
from modules.sdd_os.spec_binding import find_bound_spec  # noqa: E402


def _repo(args) -> Path:
    return Path(args.repo).resolve() if args.repo else Path.cwd()


def cmd_classify(args) -> int:
    root = _repo(args)
    d = evaluate(args.task, root)
    print(f"Tier {d.tier} -- {d.tier_label}")
    print(f"  repo    : {root}")
    print(f"  action  : {d.action}")
    print(f"  binding : {d.binding.reason}")
    if d.binding.bound:
        print(f"  spec    : {d.binding.spec_path}")
        print(f"  matched : {list(d.binding.matched)}")
    print()
    print(d.directive)
    return 0 if d.action == "proceed" else 1


def cmd_spec(args) -> int:
    root = _repo(args)
    d = enforce(args.task, root, auto_generate=True)
    print(f"Tier {d.tier} -- {d.tier_label} | action={d.action}")
    if d.spec_written:
        print(f"  written : {d.spec_path}")
    elif d.spec_path and d.spec_path.exists():
        print(f"  exists  : {d.spec_path} (left untouched)")
    print()
    print(d.directive)
    return 0


def cmd_scaffold(args) -> int:
    root = _repo(args)
    r = scaffold(root, dry_run=args.dry_run)
    verb = "would create" if args.dry_run else "created"
    print(f"{root}")
    print(f"  stack        : {r.profile.stack}")
    print(f"  source files : {r.profile.source_files}")
    print(f"  baseline tier: {r.profile.default_tier}")
    print(f"  specs        : {r.profile.existing_specs} "
          f"({r.profile.declared_specs} declare covers)")
    for p in r.created:
        print(f"  {verb:12} : {p.name}")
    for p in r.skipped:
        print(f"  {'preserved':12} : {p.name}")
    return 0


def cmd_drift(args) -> int:
    root = _repo(args)
    reports = check_drift(root)
    if not reports:
        print(f"{root}: no spec declares `covers` -- nothing to check.")
        print("  Run `scaffold`, or add a `covers:` header to an existing spec.")
        return 1
    stale = [r for r in reports if r.drifted]
    for r in reports:
        mark = "STALE" if r.drifted else "ok   "
        print(f"  [{mark}] {r.spec_path.name}: {r.reason}")
    print(f"\n{len(stale)}/{len(reports)} spec(s) stale.")
    return 1 if stale else 0


def cmd_status(args) -> int:
    root = _repo(args)
    p = profile_repo(root)
    print(f"{root}")
    print(f"  scaffolded    : {is_scaffolded(root)}")
    print(f"  stack         : {p.stack}")
    print(f"  baseline tier : {p.default_tier}")
    print(f"  spec files    : {p.existing_specs}")
    print(f"  declaring     : {p.declared_specs}")
    if p.existing_specs and not p.declared_specs:
        print("  NOTE: spec-shaped files exist but none declares `covers`,")
        print("        so none can bind to a task. This is the RC-2 state.")
    return 0 if p.declared_specs or not p.existing_specs else 1


def cmd_rollout(args) -> int:
    """Scaffold many repos in one pass. Non-destructive everywhere."""
    listing = Path(args.repos_file)
    if not listing.is_file():
        print(f"repos file not found: {listing}", file=sys.stderr)
        return 2
    repos = [
        Path(line.strip()) for line in
        listing.read_text(encoding="utf-8-sig").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    done = skipped = missing = 0
    for repo in repos:
        if not repo.is_dir():
            print(f"  MISSING   {repo}")
            missing += 1
            continue
        r = scaffold(repo, dry_run=args.dry_run)
        created = [p.name for p in r.created]
        if created:
            done += 1
            print(f"  {'DRY ' if args.dry_run else 'DONE'}      {repo.name}: "
                  f"{', '.join(created)} (tier {r.profile.default_tier}, "
                  f"{r.profile.existing_specs} specs)")
        else:
            skipped += 1
            print(f"  PRESENT   {repo.name}: already scaffolded")
    print(f"\n{done} scaffolded, {skipped} already present, {missing} missing.")
    return 0 if missing == 0 else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="sdd_os_cli", description=__doc__)
    ap.add_argument("--repo", help="target repo (default: cwd)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("classify", help="tier + spec binding for a task")
    p.add_argument("task")
    p.set_defaults(fn=cmd_classify)

    p = sub.add_parser("spec", help="generate the tier-appropriate spec")
    p.add_argument("task")
    p.set_defaults(fn=cmd_spec)

    p = sub.add_parser("scaffold", help="create the SDD-OS substrate")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_scaffold)

    p = sub.add_parser("drift", help="report specs older than the code")
    p.set_defaults(fn=cmd_drift)

    p = sub.add_parser("status", help="SDD-OS adoption state of a repo")
    p.set_defaults(fn=cmd_status)

    p = sub.add_parser("rollout", help="scaffold many repos")
    p.add_argument("--repos-file", required=True)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_rollout)

    args = ap.parse_args(argv)
    return int(args.fn(args))


if __name__ == "__main__":
    raise SystemExit(main())
