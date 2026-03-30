#!/usr/bin/env python3
"""
ExecutionOS Migration Tool

Parses a full ExecutionOS markdown file, classifies sections into
depth tiers using keyword heuristics, and prints a migration report.

Usage:
    python migrate.py <path-to-executionos.md> [--verify]
"""

import argparse
import re
import sys
from pathlib import Path

# Keyword heuristics for tier classification
TIER_KEYWORDS = {
    "LIGHT": [
        "run context", "constitution", "core", "adaptive depth",
        "token efficiency", "question gate", "loader",
    ],
    "STANDARD": [
        "phase 0", "phase 1", "phase 2", "phase 3", "phase 4",
        "phase 5", "phase 6", "phase 7", "phase 8", "phase 9", "phase 10",
        "input", "intent", "sources", "route", "discover",
        "plan", "scaffold", "implement", "integrate", "test", "review",
    ],
    "DEEP": [
        "phase 11", "phase 12", "phase 13", "phase 14", "phase 15",
        "validate", "security", "performance", "documentation", "governance",
        "overlay", "domain", "minecraft", "python", "typescript", "seo",
        "product", "live-ops",
    ],
    "FORENSIC": [
        "phase 16", "phase 17", "phase 18", "phase 19", "phase 20",
        "artifact", "reflect", "feedback loop", "handoff", "close",
        "runtime artifact", "session summary", "deviation log",
    ],
}


def parse_sections(text: str) -> list[dict]:
    """Split markdown into sections by ## headers."""
    sections = []
    current = None
    for line in text.splitlines():
        match = re.match(r"^##\s+(.+)$", line)
        if match:
            if current:
                sections.append(current)
            current = {"title": match.group(1), "lines": []}
        elif current is not None:
            current["lines"].append(line)
    if current:
        sections.append(current)
    return sections


def classify_section(section: dict) -> str:
    """Classify a section into a depth tier using keyword matching."""
    text = (section["title"] + " " + " ".join(section["lines"])).lower()
    scores = {}
    for tier, keywords in TIER_KEYWORDS.items():
        scores[tier] = sum(1 for kw in keywords if kw in text)
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "UNCLASSIFIED"
    return best


def classify_to_file(tier: str) -> str:
    """Map tier to target file in executionos-lite structure."""
    mapping = {
        "LIGHT": "core.md",
        "STANDARD": "phases/phases-0-4.md or phases/phases-5-10.md",
        "DEEP": "phases/phases-11-15.md or overlays/*.md",
        "FORENSIC": "phases/phases-16-20.md or artifacts.md",
        "UNCLASSIFIED": "(manual review needed)",
    }
    return mapping.get(tier, "(unknown)")


def run_migration(path: Path, verify: bool = False) -> int:
    """Parse file, classify sections, print report."""
    if not path.exists():
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        return 1

    text = path.read_text(encoding="utf-8")
    sections = parse_sections(text)

    if not sections:
        print("WARNING: No ## sections found in file.", file=sys.stderr)
        return 1

    # Classification report
    tier_counts = {"LIGHT": 0, "STANDARD": 0, "DEEP": 0, "FORENSIC": 0, "UNCLASSIFIED": 0}
    results = []

    for section in sections:
        tier = classify_section(section)
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        line_count = len([l for l in section["lines"] if l.strip()])
        results.append({
            "title": section["title"],
            "tier": tier,
            "target": classify_to_file(tier),
            "lines": line_count,
        })

    # Print report
    print("=" * 70)
    print("ExecutionOS Migration Report")
    print(f"Source: {path}")
    print(f"Sections found: {len(sections)}")
    print("=" * 70)
    print()
    print(f"{'Section':<40} {'Tier':<15} {'Lines':>5}")
    print("-" * 62)
    for r in results:
        print(f"{r['title'][:39]:<40} {r['tier']:<15} {r['lines']:>5}")
    print("-" * 62)
    print()

    # Tier summary
    print("Tier Distribution:")
    for tier, count in tier_counts.items():
        if count > 0:
            print(f"  {tier:<15} {count} section(s)")
    print()

    # Target file mapping
    print("Target File Mapping:")
    for r in results:
        print(f"  {r['title'][:45]:<47} -> {r['target']}")
    print()

    # Unclassified warnings
    unclassified = [r for r in results if r["tier"] == "UNCLASSIFIED"]
    if unclassified:
        print(f"WARNING: {len(unclassified)} section(s) could not be classified:")
        for r in unclassified:
            print(f"  - {r['title']}")
        print("  These sections require manual review and placement.")
        print()

    # Verify mode: check that lite files exist
    if verify:
        print("Verification Mode:")
        lite_dir = Path(__file__).parent
        expected = [
            "core.md",
            "phases/phases-0-4.md",
            "phases/phases-5-10.md",
            "phases/phases-11-15.md",
            "phases/phases-16-20.md",
            "artifacts.md",
        ]
        overlay_dir = lite_dir / "overlays"
        all_ok = True
        for f in expected:
            fp = lite_dir / f
            status = "FOUND" if fp.exists() else "MISSING"
            if status == "MISSING":
                all_ok = False
            print(f"  [{status}] {f}")
        if overlay_dir.exists():
            overlays = list(overlay_dir.glob("*.md"))
            print(f"  [{'FOUND' if overlays else 'EMPTY'}] overlays/ ({len(overlays)} files)")
            if not overlays:
                all_ok = False
        else:
            print("  [MISSING] overlays/")
            all_ok = False
        print()
        print(f"Verification: {'PASSED' if all_ok else 'FAILED'}")
        return 0 if all_ok else 1

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Migrate a full ExecutionOS markdown file to the lite modular structure."
    )
    parser.add_argument("path", type=Path, help="Path to the ExecutionOS markdown file")
    parser.add_argument("--verify", action="store_true", help="Verify lite module files exist")
    args = parser.parse_args()
    sys.exit(run_migration(args.path, args.verify))


if __name__ == "__main__":
    main()
