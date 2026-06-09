#!/usr/bin/env python3
"""ADS Stop-chain runner (D4).

Invoked by hooks/hook-dispatcher.js CHAIN_MAP['Stop-chain'] as a child
process: it receives the Stop event JSON on stdin, reads `cwd`, diffs the
repo's working tree, and writes/refreshes docs for each significant
module change. It NEVER stages or commits (audit gap #8) and ALWAYS exits
0 -- any error is swallowed so it can never block the Stop chain
(fail-open, audit gap #2 partner). MINOR/DELETED changes are silent.

Kill switch (audit gap #1): a `docs/.ads-disabled` file in the repo turns
ADS off for that repo. Default is ON (Owner Q5).

stdlib-only. Standalone: also runnable as `python ads_sync.py --repo <p>`.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

LOG = Path.home() / ".claude" / "logs" / "ads-sync.log"
KILL_SWITCH = "docs/.ads-disabled"


def _now() -> str:
    override = os.environ.get("CLAUDE_ADS_NOW")
    if override:
        return override
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _log(msg: str) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(f"{_now()} {msg}\n")
    except OSError:
        pass


def _read_cwd_from_stdin() -> str | None:
    try:
        raw = sys.stdin.read()
    except Exception:
        return None
    if not raw:
        return None
    raw = raw.lstrip("﻿").strip()       # BOM-defensive (PS pipe)
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return None
    cwd = data.get("cwd") or data.get("working_directory")
    return cwd if isinstance(cwd, str) else None


def sync(repo: str | Path) -> dict:
    """Run detection + generation for one repo. Returns a summary dict."""
    from modules.ads.detector import ChangeType, detect_changes
    from modules.ads.doc_generator import write_docs
    from modules.ads.doc_updater import update_docs

    repo = Path(repo).resolve()
    summary = {"repo": str(repo), "created": [], "updated": [], "skipped": []}

    if (repo / KILL_SWITCH).exists():
        summary["disabled"] = True
        return summary

    now = _now()
    for change in detect_changes(repo):
        if change.change_type == ChangeType.CREATED:
            write_docs(change.key, repo, now, change.is_package)
            summary["created"].append(change.key)
        elif change.change_type == ChangeType.UPDATED:
            update_docs(change.key, repo, change, now, change.is_package)
            summary["updated"].append(change.key)
        else:                                 # MINOR / DELETED -> silence
            summary["skipped"].append(change.key)
    return summary


def main(argv: list[str] | None = None) -> int:
    try:
        ap = argparse.ArgumentParser(description="ADS Stop-chain runner")
        ap.add_argument("--repo", default=None,
                        help="repo root (default: cwd from stdin Stop JSON)")
        args = ap.parse_args(argv)

        repo = args.repo or _read_cwd_from_stdin()
        if not repo:
            return 0
        summary = sync(repo)
        if summary.get("created") or summary.get("updated"):
            _log(f"synced {summary['repo']}: "
                 f"+{len(summary['created'])} created, "
                 f"{len(summary['updated'])} updated "
                 f"{summary['created']}{summary['updated']}")
        # stdout JSON is harmless on Stop (no additionalContext accepted);
        # useful for --repo manual runs.
        if args.repo:
            print(json.dumps(summary, indent=2))
    except Exception as exc:                  # fail-open: never block Stop
        _log(f"ERROR (swallowed): {type(exc).__name__}: {exc}")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
