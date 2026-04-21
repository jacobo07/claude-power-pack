"""
Sleepless QA — CLI entrypoint.

Usage:
    python -m sleepless_qa heartbeat
    python -m sleepless_qa run <repo-path> <action-script.yml> [--runtime-class auto|web|minecraft|python_daemon|cli] [--retry-budget N]
    python -m sleepless_qa show <run-id>
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from . import STATE_DIR_DEFAULT
from .dumpers.base import ActionScript
from .healer.orchestrator import run as orchestrator_run


def _load_config() -> dict[str, Any]:
    """Load config.json if present, otherwise return sensible defaults."""
    candidates = [
        Path(__file__).resolve().parent / "config.json",
        Path(__file__).resolve().parent / "config.example.json",
    ]
    for p in candidates:
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                logging.warning("Failed to parse %s: %s", p, exc)
    return {}


def _load_action_script(path: Path) -> ActionScript:
    """Load a YAML action script into an ActionScript model."""
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PyYAML not installed. pip install PyYAML") from exc
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Action script {path} did not parse to a dict")
    return ActionScript(**data)


def _cmd_heartbeat(_args: argparse.Namespace) -> int:
    from .heartbeat import run_heartbeat
    verdict = run_heartbeat()
    print(verdict.to_json())
    return 0 if verdict.status == "alive" else 1


def _cmd_run(args: argparse.Namespace) -> int:
    repo_path = Path(args.repo).resolve()
    action_path = Path(args.action).resolve()
    if not repo_path.exists():
        print(f"ERROR: repo not found: {repo_path}", file=sys.stderr)
        return 2
    if not action_path.exists():
        print(f"ERROR: action script not found: {action_path}", file=sys.stderr)
        return 2

    action = _load_action_script(action_path)
    config = _load_config()
    max_retry = int(
        args.retry_budget
        or os.environ.get("MAX_RETRY_BUDGET")
        or config.get("max_retry_budget", 3)
    )

    result = orchestrator_run(
        repo_path=repo_path,
        action=action,
        config=config,
        runtime_class=args.runtime_class,
        max_retry_budget=max_retry,
    )

    print(json.dumps({
        "run_id": result.run_id,
        "status": result.final_verdict.status.value,
        "confidence": result.final_verdict.confidence,
        "reason": result.final_verdict.reason,
        "attempts": result.attempts,
        "terminated_because": result.terminated_because,
        "heal_commits": result.heal_commits,
        "verdict_json_path": str(STATE_DIR_DEFAULT / "runs" / result.run_id / "verdict.json"),
    }, indent=2))

    return 0 if result.final_verdict.status.value == "PASS" else 1


def _cmd_show(args: argparse.Namespace) -> int:
    run_id = args.run_id
    verdict_path = STATE_DIR_DEFAULT / "runs" / run_id / "verdict.json"
    jsonl_path = STATE_DIR_DEFAULT / "runs" / run_id / "run.jsonl"
    if not verdict_path.exists():
        print(f"No verdict.json at {verdict_path}", file=sys.stderr)
        return 2
    print("=== verdict.json ===")
    print(verdict_path.read_text(encoding="utf-8"))
    if jsonl_path.exists():
        print("\n=== run.jsonl (last 20 events) ===")
        lines = jsonl_path.read_text(encoding="utf-8").splitlines()
        for line in lines[-20:]:
            print(line)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sleepless_qa",
        description="Sleepless QA — empirical verification pipeline (Ley 25 enforcer)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("heartbeat", help="Self-test: verify Claude Vision is alive")

    run_p = sub.add_parser("run", help="Run QA against a repo")
    run_p.add_argument("repo", help="Path to target repo")
    run_p.add_argument("action", help="Path to YAML action script")
    run_p.add_argument(
        "--runtime-class",
        default="auto",
        choices=["auto", "web", "minecraft", "python_daemon", "cli"],
    )
    run_p.add_argument("--retry-budget", type=int, default=None)

    show_p = sub.add_parser("show", help="Show a past run's verdict + log")
    show_p.add_argument("run_id")

    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=os.environ.get("SLEEPLESS_QA_LOG", "INFO"),
        format="%(asctime)s [sleepless_qa] %(levelname)s: %(message)s",
    )
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd == "heartbeat":
        return _cmd_heartbeat(args)
    if args.cmd == "run":
        return _cmd_run(args)
    if args.cmd == "show":
        return _cmd_show(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
