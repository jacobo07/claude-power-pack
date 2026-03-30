#!/usr/bin/env python3
"""Cross-Project Dedup - Find duplicate rules across CLAUDE.md files in multiple projects."""

import argparse
import difflib
import os
import re
import sys
from pathlib import Path


def find_claude_md_files(scan_dir: str) -> list[Path]:
    """Find all CLAUDE.md files under scan_dir."""
    files = []
    scan = Path(scan_dir)
    if not scan.exists():
        return files
    for root, dirs, filenames in os.walk(scan):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", ".next", "dist"}]
        for f in filenames:
            if f == "CLAUDE.md":
                files.append(Path(root) / f)
    return files


def extract_rules(text: str) -> list[str]:
    """Extract rule-like lines: bullets, numbered items, imperative sentences."""
    rules = []
    for line in text.splitlines():
        stripped = line.strip()
        # Bullet points
        if re.match(r"^[-*+]\s+.{10,}", stripped):
            rules.append(stripped)
        # Numbered items
        elif re.match(r"^\d+\.\s+.{10,}", stripped):
            rules.append(stripped)
        # Bold directives
        elif re.match(r"^\*\*.+\*\*", stripped) and len(stripped) > 15:
            rules.append(stripped)
    return rules


def normalize(text: str) -> str:
    """Normalize text for comparison."""
    t = text.lower()
    t = re.sub(r"^[-*+]\s+", "", t)
    t = re.sub(r"^\d+\.\s+", "", t)
    t = re.sub(r"\*\*", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def estimate_tokens(text: str) -> int:
    return int(len(text.split()) * 1.33)


def main():
    home = Path.home()
    default_scan = str(home / "Desktop" / "Cursor Projects")

    parser = argparse.ArgumentParser(description="Cross-Project Dedup - Find duplicate rules across CLAUDE.md files")
    parser.add_argument("--scan-dir", type=str, default=default_scan, help=f"Directory to scan (default: {default_scan})")
    parser.add_argument("--threshold", type=float, default=0.8, help="Similarity threshold 0.0-1.0 (default: 0.8)")
    args = parser.parse_args()

    files = find_claude_md_files(args.scan_dir)
    if len(files) < 2:
        print(f"Need at least 2 CLAUDE.md files for comparison. Found: {len(files)}")
        sys.exit(0)

    # Extract rules per project
    project_rules: dict[str, list[tuple[str, str]]] = {}  # project_name -> [(original, normalized)]
    for fp in files:
        project_name = fp.parent.name
        text = fp.read_text(encoding="utf-8", errors="replace")
        rules = extract_rules(text)
        project_rules[project_name] = [(r, normalize(r)) for r in rules]

    print("=" * 70)
    print("CROSS-PROJECT DEDUP REPORT")
    print("=" * 70)
    print(f"Scan directory: {args.scan_dir}")
    print(f"Similarity threshold: {args.threshold}")
    print(f"Projects scanned: {len(files)}")
    for name, rules in sorted(project_rules.items()):
        print(f"  {name}: {len(rules)} rules")
    print()

    # Compare all pairs
    exact_dupes: list[dict] = []
    near_dupes: list[dict] = []
    seen_pairs: set[tuple[str, str]] = set()

    projects = sorted(project_rules.keys())
    for i, proj_a in enumerate(projects):
        for proj_b in projects[i + 1:]:
            for orig_a, norm_a in project_rules[proj_a]:
                for orig_b, norm_b in project_rules[proj_b]:
                    pair_key = (min(norm_a, norm_b), max(norm_a, norm_b))
                    if pair_key in seen_pairs:
                        continue

                    if norm_a == norm_b:
                        seen_pairs.add(pair_key)
                        exact_dupes.append({
                            "project_a": proj_a,
                            "project_b": proj_b,
                            "rule_a": orig_a,
                            "rule_b": orig_b,
                            "similarity": 1.0,
                        })
                    else:
                        ratio = difflib.SequenceMatcher(None, norm_a, norm_b).ratio()
                        if ratio >= args.threshold:
                            seen_pairs.add(pair_key)
                            near_dupes.append({
                                "project_a": proj_a,
                                "project_b": proj_b,
                                "rule_a": orig_a,
                                "rule_b": orig_b,
                                "similarity": round(ratio, 3),
                            })

    # Sort near dupes by similarity descending
    near_dupes.sort(key=lambda x: x["similarity"], reverse=True)

    total_wasted_tokens = 0

    if exact_dupes:
        print(f"--- EXACT DUPLICATES ({len(exact_dupes)}) ---")
        for d in exact_dupes:
            tokens = estimate_tokens(d["rule_a"])
            total_wasted_tokens += tokens
            print(f"  [{d['project_a']}] <-> [{d['project_b']}] ({tokens} tokens wasted)")
            rule_preview = d["rule_a"][:100] + ("..." if len(d["rule_a"]) > 100 else "")
            print(f"    {rule_preview}")
            print()
    else:
        print("No exact duplicates found.")
        print()

    if near_dupes:
        print(f"--- NEAR DUPLICATES ({len(near_dupes)}) ---")
        for d in near_dupes[:30]:  # cap display
            tokens = estimate_tokens(d["rule_a"])
            total_wasted_tokens += tokens
            print(f"  [{d['similarity']:.1%}] [{d['project_a']}] <-> [{d['project_b']}] (~{tokens} tokens)")
            preview_a = d["rule_a"][:80] + ("..." if len(d["rule_a"]) > 80 else "")
            preview_b = d["rule_b"][:80] + ("..." if len(d["rule_b"]) > 80 else "")
            print(f"    A: {preview_a}")
            print(f"    B: {preview_b}")
            print()
    else:
        print("No near duplicates found.")
        print()

    print("-" * 70)
    print(f"Total duplicates: {len(exact_dupes)} exact + {len(near_dupes)} near")
    print(f"Estimated wasted tokens: {total_wasted_tokens:,}")
    print()
    if total_wasted_tokens > 0:
        print("RECOMMENDATION: Move shared rules to ~/.claude/CLAUDE.md (global config)")
        print("and remove from per-project CLAUDE.md files.")


if __name__ == "__main__":
    main()
