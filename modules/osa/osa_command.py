"""OSA CLI entry point: /osa --audit / --status / --budget / --force.

Exposes:
  --audit               run dispatcher.should_activate(), print decision.
  --audit --project X   override project resolution.
  --status              print throttle.status() + last 5 NEVER_AGAIN.
  --budget              print throttle.status() only.
  --never-again --top N print top-N recurring NEVER_AGAIN entries.
  --never-again --query PATTERN substring search.
  --force               bypass triggers (still respects throttle).

V1 contract: this command DECIDES, LOGS, and PRINTS. It does NOT
spawn `claude -p`. Spawning autonomous claude calls consumes
programmatic credit -- that is an explicit Owner action via the
agent file itself (`~/.claude/agents/omni-singularity.md`).

Sealed 2026-05-28.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[2]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.osa import dispatcher, never_again, throttle  # noqa: E402


def _cmd_status(args: argparse.Namespace) -> int:
    out = {
        "throttle": throttle.status(),
        "project_resolved": dispatcher._resolve_project(),
        "session_minutes": dispatcher._session_minutes(),
        "top_recurring": [asdict(e) for e in never_again.top_recurring(5)],
    }
    print(json.dumps(out, indent=2, default=str))
    return 0


def _cmd_budget(args: argparse.Namespace) -> int:
    print(json.dumps(throttle.status(), indent=2, default=str))
    return 0


def _cmd_never_again(args: argparse.Namespace) -> int:
    if args.query:
        rows = never_again.query(args.query)
    else:
        rows = never_again.top_recurring(args.top or 5)
    print(json.dumps([asdict(r) for r in rows], indent=2, default=str))
    return 0


def _cmd_audit(args: argparse.Namespace) -> int:
    """V1: DECIDE + LOG. Does NOT spawn claude -p."""
    result = dispatcher.run_if_warranted(
        project=args.project, force=bool(args.force))
    print(json.dumps(result, indent=2, default=str))
    return 0 if result.get("status") != "blocked" else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="osa", description="Omni-Singularity Agent CLI")
    ap.add_argument("--audit", action="store_true",
                    help="Run dispatcher decision and print")
    ap.add_argument("--status", action="store_true",
                    help="Print throttle status + top NEVER_AGAIN")
    ap.add_argument("--budget", action="store_true",
                    help="Print throttle status only")
    ap.add_argument("--never-again", action="store_true",
                    help="Query NEVER_AGAIN log")
    ap.add_argument("--top", type=int, default=5,
                    help="With --never-again: top N entries")
    ap.add_argument("--query", default=None,
                    help="With --never-again: substring search")
    ap.add_argument("--force", action="store_true",
                    help="With --audit: bypass triggers (respects budget)")
    ap.add_argument("--project", default=None,
                    help="Override project name resolution")
    args = ap.parse_args(argv)

    selected = sum(int(x) for x in [
        args.audit, args.status, args.budget, args.never_again])
    if selected == 0:
        # default: --status
        return _cmd_status(args)
    if selected > 1:
        print(
            "ERROR: --audit / --status / --budget / --never-again are "
            "mutually exclusive", file=sys.stderr)
        return 2
    if args.audit:
        return _cmd_audit(args)
    if args.status:
        return _cmd_status(args)
    if args.budget:
        return _cmd_budget(args)
    if args.never_again:
        return _cmd_never_again(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
