#!/usr/bin/env python3
"""Measure the command-tool denominator from session transcripts.

`PR-PRECISION-BEFORE-COVERAGE-001` requires an instrument's coverage to be
bounded against a denominator the instrument does not produce. It was
stated as 75.5% and recorded only in prose -- a rule demanding a
reproducible denominator whose own number could not be reproduced. This is
the instrument that produces it.

Counts `"name":"<Tool>"` occurrences across the session transcripts under
~/.claude/projects. Substring counting, not JSON parsing: the corpus is
~2 GB and the exact figure does not need per-record fidelity, only a
denominator whose ORDER and RATIO are trustworthy, not a per-record census.

Measured 2026-08-27, PowerShell's share of command-tool traffic:

    this tool, --since 2026-08-16 (98 transcripts) ......... 75.4%
    this tool, full corpus (765 transcripts) .............. 82.2%
    an independent count, full corpus, other method ....... 72.1%

The three disagree by up to ten points and agree unanimously on the only
thing the coverage judgement rests on: PowerShell carries the large
majority of command traffic here, so a `Bash`-only matcher observes the
minority. Quote the range, not a decimal. The methodological gap between
the second and third figures is unresolved, and is stated rather than
averaged away.

    python tools/measure_command_surface.py                # all transcripts
    python tools/measure_command_surface.py --since 2026-08-16
    python tools/measure_command_surface.py --json

Exit 0 always: this reports, it does not gate. What it feeds is a judgement
about whether a producer's registration covers its subject, and that
judgement belongs to capture_liveness.
"""
from __future__ import annotations

import argparse
import collections
import datetime
import glob
import json
import os
import sys

TOOLS = ("Bash", "PowerShell", "Read", "Edit", "Write", "Grep", "Glob",
         "Task", "WebFetch", "NotebookEdit", "Monitor", "MultiEdit")
COMMAND_TOOLS = ("Bash", "PowerShell")
CHUNK = 1 << 23
OVERLAP = 64          # longest pattern is far shorter; guards a split token


def transcripts(since: str | None) -> list[str]:
    root = os.path.expanduser("~/.claude/projects")
    found = glob.glob(os.path.join(root, "*", "*.jsonl"))
    if not since:
        return found
    cutoff = datetime.datetime.strptime(since, "%Y-%m-%d").timestamp()
    return [f for f in found if os.path.getmtime(f) >= cutoff]


def count(paths: list[str]) -> tuple[collections.Counter, int]:
    # Both serialisations are counted, though on this corpus it changes
    # almost nothing (+3 of 28,483). The spaced spelling was a HYPOTHESIS
    # for why an independent count of the full corpus reported a higher
    # Bash total than this one; the hypothesis is wrong, and the difference
    # remains methodological rather than a spelling gap. Recorded here
    # because a disproved guess left in a comment reads as a finding.
    needles = {t: (f'"name":"{t}"'.encode(), f'"name": "{t}"'.encode())
               for t in TOOLS}
    tally: collections.Counter = collections.Counter()
    total_bytes = 0
    for path in paths:
        try:
            with open(path, "rb") as handle:
                tail = b""
                while True:
                    chunk = handle.read(CHUNK)
                    if not chunk:
                        break
                    total_bytes += len(chunk)
                    buf = tail + chunk
                    for tool, spellings in needles.items():
                        for needle in spellings:
                            tally[tool] += buf.count(needle)
                    tail = buf[-OVERLAP:]
        except OSError:
            continue
    return tally, total_bytes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--since", help="only transcripts modified on/after "
                                    "YYYY-MM-DD")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    paths = transcripts(args.since)
    if not paths:
        print("no transcripts found", file=sys.stderr)
        return 0
    tally, nbytes = count(paths)

    commands = sum(tally[t] for t in COMMAND_TOOLS)
    report = {
        "transcripts": len(paths),
        "bytes": nbytes,
        "since": args.since,
        "by_tool": dict(tally.most_common()),
        "command_tool_total": commands,
        "command_share": {
            t: round(tally[t] * 100.0 / commands, 1) if commands else None
            for t in COMMAND_TOOLS},
    }
    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print(f"transcripts {len(paths)}   {nbytes / 1e6:.0f} MB"
          + (f"   since {args.since}" if args.since else ""))
    total = sum(tally.values()) or 1
    print(f"\n{'tool':<14}{'calls':>9}{'share':>9}")
    for tool, n in tally.most_common():
        if n:
            print(f"{tool:<14}{n:>9}{n * 100.0 / total:>8.1f}%")
    print(f"\ncommand tools: {commands}")
    for tool in COMMAND_TOOLS:
        share = tally[tool] * 100.0 / commands if commands else 0
        print(f"  {tool:<12}{tally[tool]:>9}{share:>8.1f}% of command traffic")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
