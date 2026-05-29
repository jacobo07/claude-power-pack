#!/usr/bin/env python3
"""Bug -> Hard Rule converter (CLI).

Reads UKDL + session_lessons + never_again_log.jsonl, surfaces
CRITICAL or recurrence>=3 bug candidates (Decision A3), and writes
approved ones to CLAUDE.md + vault/hard_rules/HARD_RULES.md.

Subcommands:
  --scan         List qualifying bug candidates without changes.
  --propose      Render proposed hard-rule blocks to a draft file
                 under vault/hard_rules/proposals_<ts>.md.
  --retroactive  Auto-install every CRITICAL candidate that is not
                 yet present (idempotent).
  --install ID*  Install one or more PROPOSED-NNN draft rules from
                 the latest proposals file.
  --list         List the hard rules currently installed.

Sealed BL-HARDRULE-001 (2026-05-29).
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.hard_rules.extractor import (
    BugCandidate,
    load_candidates,
    propose_hard_rule,
)
from modules.hard_rules.writer import (
    DEFAULT_ARCHIVE,
    DEFAULT_CLAUDE_MD,
    append_hard_rule,
    get_current_rules,
    list_hard_rules,
)

PROPOSALS_DIR = PP_ROOT / "vault" / "hard_rules"


def cmd_scan() -> int:
    candidates = load_candidates()
    print(f"=== BUG CANDIDATES qualifying for hard rule "
          f"({len(candidates)}) ===")
    for i, c in enumerate(candidates):
        print(f"\n[{i}] [{c.severity}] r={c.recurrence}x  "
              f"src={c.source}")
        print(f"    issue : {c.issue[:120]}")
        print(f"    fix   : {c.fix[:120]}")
    return 0


def cmd_propose() -> int:
    candidates = load_candidates()
    if not candidates:
        print("No candidates qualify under Decision A3 (CRITICAL "
              "or recurrence>=3). Nothing to propose.")
        return 0
    PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
    iso = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    draft = PROPOSALS_DIR / f"proposals_{iso}.md"
    parts: list[str] = [
        f"# Proposed Hard Rules ({iso}, Decision A3)\n",
        "",
        f"{len(candidates)} candidates from "
        "UKDL + session_lessons + never_again_log.\n",
        "",
        "Review each block; install with:\n",
        "  python tools/bug_to_hardrule.py --install PROPOSED-001 ...\n",
        "",
        "---",
        "",
    ]
    for i, c in enumerate(candidates):
        proposed_id = f"PROPOSED-{i+1:03d}"
        block = propose_hard_rule(c, proposed_id)
        parts.append(block)
        parts.append("---")
        parts.append("")
    draft.write_text("\n".join(parts), encoding="utf-8")
    print(f"[OK] {len(candidates)} proposals written to {draft}")
    print("Review them, then install with:")
    print("  python tools/bug_to_hardrule.py --install PROPOSED-001 "
          "PROPOSED-002 ...")
    return 0


def cmd_retroactive(force_recurrence: bool = True) -> int:
    candidates = load_candidates()
    critical = [c for c in candidates if c.severity == "CRITICAL"]
    if force_recurrence:
        recur = [c for c in candidates
                 if c.severity != "CRITICAL" and c.recurrence >= 3]
        candidates = critical + recur
    else:
        candidates = critical
    if not candidates:
        print("No CRITICAL candidates to install. Nothing to do.")
        return 0
    print(f"Installing {len(candidates)} hard rule(s) "
          f"({len(critical)} CRITICAL + "
          f"{len(candidates)-len(critical)} recurrence>=3)...")
    installed: list[tuple[str, str]] = []
    skipped: list[tuple[str, str]] = []
    for c in candidates:
        rule_text = propose_hard_rule(c, "HR-NEXT")
        before = set(get_current_rules())
        rid = append_hard_rule(rule_text)
        after = set(get_current_rules())
        if rid in before:
            skipped.append((rid, c.issue[:80]))
        else:
            installed.append((rid, c.issue[:80]))
    print()
    print("=" * 60)
    print(f"INSTALLED ({len(installed)}):")
    for rid, issue in installed:
        print(f"  {rid}: {issue}")
    if skipped:
        print(f"\nALREADY PRESENT ({len(skipped)}):")
        for rid, issue in skipped:
            print(f"  {rid}: {issue}")
    print()
    print(f"CLAUDE.md  : {DEFAULT_CLAUDE_MD}")
    print(f"Archive    : {DEFAULT_ARCHIVE}")
    print("Hard rules are now active in CLAUDE.md.")
    return 0


def cmd_install(ids: list[str]) -> int:
    if not ids:
        print("[FAIL] --install requires at least one PROPOSED-NNN id",
              file=sys.stderr)
        return 2
    proposals = sorted(PROPOSALS_DIR.glob("proposals_*.md"),
                       key=lambda p: p.stat().st_mtime, reverse=True)
    if not proposals:
        print("[FAIL] no proposals file under vault/hard_rules/ -- "
              "run --propose first.", file=sys.stderr)
        return 3
    draft = proposals[0]
    body = draft.read_text(encoding="utf-8-sig")
    installed: list[str] = []
    for pid in ids:
        block = _slice_block(body, pid)
        if not block:
            print(f"[skip] {pid} not found in {draft.name}")
            continue
        rule_text = block.replace(pid, "HR-NEXT")
        rid = append_hard_rule(rule_text)
        installed.append(rid)
    print()
    print(f"Installed: {installed}")
    print(f"CLAUDE.md  : {DEFAULT_CLAUDE_MD}")
    print(f"Archive    : {DEFAULT_ARCHIVE}")
    return 0 if installed else 4


def _slice_block(body: str, proposed_id: str) -> str:
    import re
    pat = re.compile(
        rf"###\s+{re.escape(proposed_id)}\s+--[\s\S]*?(?=\n---|\Z)",
        re.MULTILINE,
    )
    m = pat.search(body)
    return m.group(0) if m else ""


def cmd_list() -> int:
    rules = list_hard_rules()
    if not rules:
        print("No hard rules installed.")
        print(f"CLAUDE.md path checked: {DEFAULT_CLAUDE_MD}")
        print("Install with: python tools/bug_to_hardrule.py "
              "--retroactive")
        return 0
    print(f"=== INSTALLED HARD RULES ({len(rules)}) ===")
    for r in rules:
        print(f"\n{r['id']} -- {r['title']}")
        print(f"  TRIGGER : {r['trigger']}")
        print(f"  STOP    : {r['stop']}")
        print(f"  EVIDENCE: {r['evidence']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Bug -> Hard Rule converter. Reads UKDL + "
            "session_lessons + never_again_log, surfaces qualifying "
            "candidates (CRITICAL or recurrence>=3), and writes "
            "approved rules to CLAUDE.md + the canonical archive."))
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--scan", action="store_true")
    group.add_argument("--propose", action="store_true")
    group.add_argument("--retroactive", action="store_true")
    group.add_argument("--install", nargs="+", metavar="PROPOSED-ID")
    group.add_argument("--list", action="store_true")
    args = parser.parse_args(argv)
    if args.scan:
        return cmd_scan()
    if args.propose:
        return cmd_propose()
    if args.retroactive:
        return cmd_retroactive()
    if args.install:
        return cmd_install(list(args.install))
    if args.list:
        return cmd_list()
    return cmd_scan()


if __name__ == "__main__":
    raise SystemExit(main())
