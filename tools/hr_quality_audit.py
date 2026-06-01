#!/usr/bin/env python3
"""Hard rule quality audit -- BL-DATASET-BUILD M11.

Audits installed HRs in CLAUDE.md. Each HR is scored on field
completeness; rules scoring below ORPHAN_THRESHOLD are flagged.
Exit 0 always (advisory). Use --strict to fail when orphans exist.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.hard_rules.writer import list_hard_rules

# Score weights per required field.
WEIGHT_PER_FIELD = 25
REQUIRED_FIELDS = ("title", "trigger", "stop", "evidence")
# Total = len(REQUIRED_FIELDS) * WEIGHT_PER_FIELD = 100 max.
PERFECT_SCORE = len(REQUIRED_FIELDS) * WEIGHT_PER_FIELD

# Rules below this score are flagged orphan.
ORPHAN_THRESHOLD = 50


def _score_rule(rule: dict) -> tuple[int, list[str]]:
    score = 0
    missing: list[str] = []
    for f in REQUIRED_FIELDS:
        v = (rule.get(f) or "").strip()
        if v and v != "-":
            score += WEIGHT_PER_FIELD
        else:
            missing.append(f)
    return score, missing


def audit() -> list[dict]:
    rules = list_hard_rules()
    report: list[dict] = []
    for r in rules:
        score, missing = _score_rule(r)
        report.append({
            "id": r.get("id"),
            "score": score,
            "title": r.get("title", ""),
            "missing": missing,
            "orphan": score < ORPHAN_THRESHOLD,
        })
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if any orphan rules detected")
    args = ap.parse_args(argv)

    report = audit()
    total = len(report)
    print(f"=== HR quality audit ({total} rules, "
          f"max score {PERFECT_SCORE}) ===")
    for r in report:
        tag = "ORPHAN" if r["orphan"] else "ok    "
        title = (r["title"] or "")[:60]
        print(
            f"  [{tag}]  {r['id']:<22s}  score={r['score']:3d}  "
            f"missing={r['missing']}  {title}"
        )

    orphans = [r for r in report if r["orphan"]]
    print(
        f"\nTotal: {total} rules. "
        f"{len(orphans)} orphan(s) (score < {ORPHAN_THRESHOLD})."
    )
    if args.strict and orphans:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
