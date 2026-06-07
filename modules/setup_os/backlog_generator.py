#!/usr/bin/env python3
"""Setup Backlog Generator -- CPP Setup OS Pillar 5 (build-everything B2).

Bridges the ROI analyzer (Pillar 2) into the existing backlog_autopilot
engine: scan -> ROI recommendations -> BacklogItems with done-gates ->
what_now() picks the next action. Pure composition of two existing
modules (SCS C28: no duplication of either scoring engine).

stdlib-only.
"""
from __future__ import annotations

from dataclasses import dataclass

from modules.backlog_autopilot import BacklogItem, WhatNowResult, what_now

from .roi_analyzer import Recommendation, analyze
from .scanner import scan

# roi impact label -> backlog impact label (secret recs become Critical).
_IMPACT_MAP = {"High": "High", "Medium": "Medium", "Low": "Low"}

# Per-category done-gate text -- the empirical proof the item is done.
_DONE_GATE = {
    "secret": "secret firewall scan returns 0 CRITICAL hits on the repo",
    "docs": "the file exists, is non-empty, and is referenced by onboarding",
    "command": "the test harness runs and reports >=1 happy + 1 edge case",
    "ci": "the CI workflow runs test+lint on push and goes green",
    "hook": "the hook fires on the matched tool event and is observed acting",
    "mcp": "the MCP responds within its permission boundary in a dry-run",
    "skill": "the skill activates on a matching prompt and improves output",
}


@dataclass
class SetupBacklogEntry:
    item: BacklogItem
    done_gate: str
    roi: float


def _priority(rec: Recommendation) -> int:
    if rec.category == "secret":
        return 0                      # P0: firewall first
    if rec.roi_score >= 2.0:
        return 1
    if rec.roi_score >= 1.0:
        return 2
    return 3


def _to_item(rec: Recommendation) -> BacklogItem:
    impact = "Critical" if rec.category == "secret" else _IMPACT_MAP.get(
        rec.impact, "Medium")
    effort = rec.effort if rec.effort in ("S", "M", "L", "XL") else "M"
    return BacklogItem(id=rec.id, title=rec.title, priority=_priority(rec),
                       effort=effort, impact=impact)


def generate_backlog(path: str | None = None) -> list[SetupBacklogEntry]:
    """Scan -> ROI -> backlog entries (each with a done-gate), ROI-ordered."""
    recs = analyze(scan(path))
    entries = [
        SetupBacklogEntry(
            item=_to_item(r),
            done_gate=_DONE_GATE.get(r.category,
                                     "the recommendation is applied and "
                                     "validated against its rationale"),
            roi=r.roi_score)
        for r in recs
    ]
    # Already ROI-ordered by analyze(); keep secret-first, ROI desc.
    return entries


def recommend(path: str | None = None) -> WhatNowResult:
    """The single next action from the generated backlog (what_now)."""
    return what_now([e.item for e in generate_backlog(path)])


def render(entries: list[SetupBacklogEntry]) -> str:
    lines = [f"Setup backlog: {len(entries)} item(s) (ROI-ordered)\n"]
    for i, e in enumerate(entries, 1):
        lines.append(
            f"{i}. [P{e.item.priority}] {e.item.title} "
            f"(impact={e.item.impact}, effort={e.item.effort}, ROI={e.roi})\n"
            f"   done-gate: {e.done_gate}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Setup Backlog Generator")
    ap.add_argument("--path", default=".")
    args = ap.parse_args(argv)
    entries = generate_backlog(args.path)
    print(render(entries))
    rec = recommend(args.path)
    print(f"\nNext action: {rec.recommended.title if rec.recommended else 'none'}"
          f"  ({rec.reasoning})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
