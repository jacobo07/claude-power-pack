#!/usr/bin/env python3
"""Prompt Pattern Optimizer - Find repeated 4-grams across CLAUDE.md files to identify token waste."""

import argparse
import os
import re
import sys
from collections import Counter, defaultdict
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


def extract_ngrams(text: str, n: int = 4) -> list[str]:
    """Extract n-grams from text."""
    words = re.findall(r"[a-zA-Z0-9_-]+", text.lower())
    if len(words) < n:
        return []
    return [" ".join(words[i:i + n]) for i in range(len(words) - n + 1)]


def estimate_tokens(text: str) -> int:
    return int(len(text.split()) * 1.33)


def main():
    home = Path.home()
    default_scan = str(home / "Desktop" / "Cursor Projects")

    parser = argparse.ArgumentParser(description="Prompt Pattern Optimizer - Find repeated patterns across CLAUDE.md files")
    parser.add_argument("--scan-dir", type=str, default=default_scan, help=f"Directory to scan (default: {default_scan})")
    parser.add_argument("--min-projects", type=int, default=2, help="Minimum projects a pattern must appear in (default: 2)")
    parser.add_argument("--ngram-size", type=int, default=4, help="N-gram size (default: 4)")
    parser.add_argument("--top", type=int, default=30, help="Number of top patterns to show (default: 30)")
    args = parser.parse_args()

    files = find_claude_md_files(args.scan_dir)
    if not files:
        print("No CLAUDE.md files found.")
        sys.exit(0)

    print("=" * 70)
    print("PROMPT PATTERN OPTIMIZER")
    print("=" * 70)
    print(f"Scan directory: {args.scan_dir}")
    print(f"N-gram size: {args.ngram_size}")
    print(f"Min projects: {args.min_projects}")
    print(f"Files found: {len(files)}")
    print()

    # Extract ngrams per project
    project_ngrams: dict[str, Counter] = {}
    ngram_to_projects: dict[str, set[str]] = defaultdict(set)

    for fp in files:
        project_name = fp.parent.name
        text = fp.read_text(encoding="utf-8", errors="replace")
        ngrams = extract_ngrams(text, args.ngram_size)
        counter = Counter(ngrams)
        project_ngrams[project_name] = counter

        for ng in set(ngrams):
            ngram_to_projects[ng].add(project_name)

    # Filter to patterns in min_projects+ projects
    shared_patterns: list[tuple[str, int, int]] = []  # (pattern, project_count, total_occurrences)
    for ng, projects in ngram_to_projects.items():
        if len(projects) >= args.min_projects:
            total_occ = sum(project_ngrams[p].get(ng, 0) for p in projects)
            shared_patterns.append((ng, len(projects), total_occ))

    # Sort by total occurrences * project count (impact score)
    shared_patterns.sort(key=lambda x: x[1] * x[2], reverse=True)

    if not shared_patterns:
        print(f"No patterns found appearing in {args.min_projects}+ projects.")
        sys.exit(0)

    # Deduplicate overlapping patterns (keep the higher-scoring one)
    seen_words: set[str] = set()
    deduplicated: list[tuple[str, int, int]] = []
    for pattern, proj_count, total_occ in shared_patterns:
        words = set(pattern.split())
        # If more than half the words overlap with already-shown patterns, skip
        overlap = len(words & seen_words)
        if overlap > len(words) * 0.5 and len(deduplicated) > 5:
            continue
        deduplicated.append((pattern, proj_count, total_occ))
        seen_words.update(words)
        if len(deduplicated) >= args.top:
            break

    total_wasted_tokens = 0

    print(f"--- TOP {len(deduplicated)} SHARED PATTERNS ---")
    print()
    for i, (pattern, proj_count, total_occ) in enumerate(deduplicated, 1):
        # Each duplicate occurrence beyond the first is waste
        wasted_occ = total_occ - 1  # keep one, rest are waste
        wasted_tokens = int(wasted_occ * args.ngram_size * 1.33)
        total_wasted_tokens += wasted_tokens
        projects = sorted(ngram_to_projects[pattern])

        print(f"  {i:>2}. \"{pattern}\"")
        print(f"      Projects: {proj_count} | Occurrences: {total_occ} | Wasted: ~{wasted_tokens} tokens")
        print(f"      In: {', '.join(projects[:5])}{' ...' if len(projects) > 5 else ''}")
        print()

    print("-" * 70)
    print(f"Shared patterns: {len(shared_patterns)} total, {len(deduplicated)} shown")
    print(f"Estimated wasted tokens from duplication: {total_wasted_tokens:,}")
    print()
    print("RECOMMENDATIONS:")
    print("  1. Move shared patterns to ~/.claude/CLAUDE.md (loaded for all projects)")
    print("  2. Remove duplicated instructions from per-project CLAUDE.md files")
    print("  3. Use references (@file) instead of copying instructions")
    if total_wasted_tokens > 500:
        print(f"  4. Potential savings: ~{total_wasted_tokens:,} tokens per session")


if __name__ == "__main__":
    main()
