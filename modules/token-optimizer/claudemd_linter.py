#!/usr/bin/env python3
"""CLAUDE.md Linter - Find, measure, and optionally compress CLAUDE.md files across projects."""

import argparse
import os
import re
import sys
from pathlib import Path


FILLER_PHRASES = [
    "please note that",
    "it is important to",
    "make sure to",
    "keep in mind that",
    "note that",
    "remember that",
    "be sure to",
    "as mentioned above",
    "as previously stated",
    "in order to",
    "for the purpose of",
    "at this point in time",
    "it should be noted that",
    "as a result of",
    "due to the fact that",
    "with regard to",
    "in the event that",
    "on the other hand",
    "at the end of the day",
    "for all intents and purposes",
    "needless to say",
    "it goes without saying",
    "the fact of the matter is",
    "as a matter of fact",
]

META_COMMENTARY_PATTERNS = [
    r"^\s*<!--.*-->\s*$",
    r"^\s*\[//\]:.*$",
    r"^\s*>\s*Note:?\s*This (file|document|section)",
    r"^\s*>\s*TODO:?\s",
    r"^\s*>\s*FIXME:?\s",
]


def find_claude_md_files(scan_dir: str, global_file: str | None = None) -> list[Path]:
    """Find all CLAUDE.md files under scan_dir and optionally include global."""
    files = []
    if global_file:
        gp = Path(global_file)
        if gp.exists():
            files.append(gp)
    scan = Path(scan_dir)
    if scan.exists():
        for root, dirs, filenames in os.walk(scan):
            dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", ".next", "dist"}]
            for f in filenames:
                if f == "CLAUDE.md":
                    files.append(Path(root) / f)
    return files


def count_words(text: str) -> int:
    return len(text.split())


def estimate_tokens(word_count: int) -> int:
    return int(word_count * 1.33)


def compress_text(text: str) -> str:
    """Remove filler phrases, meta-commentary, collapse whitespace."""
    lines = text.splitlines()
    result = []
    prev_blank = False

    for line in lines:
        # Remove meta-commentary
        if any(re.match(pat, line) for pat in META_COMMENTARY_PATTERNS):
            continue

        # Remove filler phrases
        compressed = line
        for phrase in FILLER_PHRASES:
            compressed = re.sub(re.escape(phrase), "", compressed, flags=re.IGNORECASE)

        # Collapse multiple spaces
        compressed = re.sub(r"  +", " ", compressed)
        compressed = compressed.rstrip()

        is_blank = compressed.strip() == ""
        if is_blank:
            if not prev_blank:
                result.append("")
            prev_blank = True
        else:
            prev_blank = False
            result.append(compressed)

    # Strip trailing blank lines
    while result and result[-1].strip() == "":
        result.pop()

    return "\n".join(result) + "\n"


def main():
    home = Path.home()
    default_scan = str(home / "Desktop" / "Cursor Projects")
    default_global = str(home / ".claude" / "CLAUDE.md")

    parser = argparse.ArgumentParser(description="CLAUDE.md Linter - Find and measure CLAUDE.md files")
    parser.add_argument("--scan-dir", type=str, default=default_scan, help=f"Directory to scan (default: {default_scan})")
    parser.add_argument("--global-file", type=str, default=default_global, help="Path to global CLAUDE.md")
    parser.add_argument("--max-words", type=int, default=1500, help="Max word count before flagging (default: 1500)")
    parser.add_argument("--fix", action="store_true", help="Compress files in-place")
    args = parser.parse_args()

    files = find_claude_md_files(args.scan_dir, args.global_file)

    if not files:
        print("No CLAUDE.md files found.")
        sys.exit(0)

    print("=" * 70)
    print("CLAUDE.MD LINTER REPORT")
    print("=" * 70)
    print(f"Scan directory: {args.scan_dir}")
    print(f"Max words: {args.max_words}")
    print(f"Files found: {len(files)}")
    print()

    total_words = 0
    total_tokens = 0
    flagged = 0
    fixed = 0

    for fp in sorted(files):
        text = fp.read_text(encoding="utf-8", errors="replace")
        words = count_words(text)
        tokens = estimate_tokens(words)
        total_words += words
        total_tokens += tokens
        over = words > args.max_words
        if over:
            flagged += 1

        status = "OVER" if over else "OK"
        marker = "!!!" if over else "   "
        print(f"{marker} [{status:>4}] {words:>5} words ({tokens:>6} tokens) {fp}")

        if over and args.fix:
            compressed = compress_text(text)
            new_words = count_words(compressed)
            new_tokens = estimate_tokens(new_words)
            saved_words = words - new_words
            if saved_words > 0:
                fp.write_text(compressed, encoding="utf-8")
                fixed += 1
                print(f"         FIXED: {words} -> {new_words} words (saved {saved_words} words, "
                      f"{estimate_tokens(saved_words)} tokens)")
            else:
                print(f"         No filler found to remove.")

    print()
    print("-" * 70)
    print(f"Total: {total_words:,} words ({total_tokens:,} est. tokens) across {len(files)} files")
    print(f"Flagged: {flagged} files over {args.max_words} word limit")
    if args.fix:
        print(f"Fixed: {fixed} files compressed")

    if flagged > 0 and not args.fix:
        print()
        print("Run with --fix to auto-compress flagged files.")


if __name__ == "__main__":
    main()
