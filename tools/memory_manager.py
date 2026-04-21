#!/usr/bin/env python3
"""
Memory Manager — Hot/Cold context splitter for session handoff files.

Moves completed phases from handoff files to cold storage,
keeping only active context to reduce token consumption.

Usage:
    python memory_manager.py                    # process default handoff
    python memory_manager.py --dry-run          # show what would move, change nothing
    python memory_manager.py --file path.md     # process a specific file
"""

import argparse
import os
import re
from datetime import datetime
from pathlib import Path

DEFAULT_HANDOFF = os.path.expanduser(
    "~/.claude/projects/C--Users-kobig--claude-skills-claude-power-pack"
    "/memory/project_session_handoff.md"
)
COLD_STORAGE_DIR = os.path.expanduser(
    "~/.claude/projects/C--Users-kobig--claude-skills-claude-power-pack"
    "/memory/cold_storage"
)

COMPLETED_PATTERNS = [
    r"(?i)\b(COMPLETED|DONE|VERIFIED|SHIPPED|MERGED|CLOSED)\b",
]

# Sections to ALWAYS keep in hot storage (never archive)
HOT_SECTIONS = [
    "what needs to happen next",
    "key infrastructure state",
    "how to apply",
]


def estimate_tokens(text: str) -> int:
    """Rough token estimate: words * 1.3"""
    return int(len(text.split()) * 1.3)


def parse_sections(content: str) -> list[dict]:
    """Split markdown into sections by ## headers."""
    sections = []
    current = {"header": "(preamble)", "content": "", "level": 0}

    for line in content.split("\n"):
        header_match = re.match(r"^(#{1,3})\s+(.+)", line)
        if header_match:
            if current["content"].strip() or current["header"] != "(preamble)":
                sections.append(current)
            current = {
                "header": header_match.group(2).strip(),
                "content": line + "\n",
                "level": len(header_match.group(1)),
            }
        else:
            current["content"] += line + "\n"

    if current["content"].strip():
        sections.append(current)

    return sections


def is_completed(section: dict) -> bool:
    """Check if a section contains completion markers."""
    for pattern in COMPLETED_PATTERNS:
        if re.search(pattern, section["content"]):
            return True
    return False


def is_hot(section: dict) -> bool:
    """Check if a section must stay in hot storage."""
    header_lower = section["header"].lower()
    for hot_keyword in HOT_SECTIONS:
        if hot_keyword in header_lower:
            return True
    # Frontmatter (preamble with ---) always stays hot
    if section["header"] == "(preamble)" and "---" in section["content"]:
        return True
    return False


def process_handoff(filepath: str, dry_run: bool = False) -> dict:
    """Process a handoff file, splitting hot/cold sections."""
    path = Path(filepath)
    if not path.exists():
        print(f"File not found: {filepath}")
        return {"error": "file_not_found"}

    content = path.read_text(encoding="utf-8")
    tokens_before = estimate_tokens(content)
    sections = parse_sections(content)

    hot_sections = []
    cold_sections = []

    for section in sections:
        if is_hot(section):
            hot_sections.append(section)
        elif is_completed(section):
            cold_sections.append(section)
        else:
            hot_sections.append(section)

    # Report
    print(f"\n{'=' * 50}")
    print(f"MEMORY MANAGER — Context Diet Report")
    print(f"{'=' * 50}")
    print(f"File: {filepath}")
    print(f"Tokens before: {tokens_before}")
    print(f"Total sections: {len(sections)}")
    print(f"  Hot (keep): {len(hot_sections)}")
    print(f"  Cold (archive): {len(cold_sections)}")

    if cold_sections:
        print(f"\nSections to archive:")
        for s in cold_sections:
            print(f"  - {s['header']} ({estimate_tokens(s['content'])} tokens)")

        cold_content = "\n".join(s["content"] for s in cold_sections)
        tokens_after = estimate_tokens(
            "\n".join(s["content"] for s in hot_sections)
        )
        savings = tokens_before - tokens_after
        print(f"\nTokens after: {tokens_after}")
        print(f"Savings: {savings} tokens ({savings * 100 // tokens_before}%)")

        if not dry_run:
            # Write cold storage
            cold_dir = Path(COLD_STORAGE_DIR)
            cold_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d")
            cold_path = cold_dir / f"handoff_archive_{timestamp}.md"
            cold_path.write_text(
                f"# Archived Sections — {timestamp}\n\n{cold_content}",
                encoding="utf-8",
            )
            print(f"Cold storage: {cold_path}")

            # Rewrite hot file
            hot_content = "\n".join(s["content"] for s in hot_sections)
            path.write_text(hot_content, encoding="utf-8")
            print(f"Hot file rewritten: {filepath}")
        else:
            print(f"\n[DRY RUN] No files modified.")
    else:
        print(f"\nNo completed sections found. File is already lean.")
        print(f"Current size: {tokens_before} tokens — no action needed.")

    return {
        "tokens_before": tokens_before,
        "sections_total": len(sections),
        "sections_cold": len(cold_sections),
        "sections_hot": len(hot_sections),
    }


def main():
    parser = argparse.ArgumentParser(description="Memory Manager — Hot/Cold context splitter")
    parser.add_argument("--file", default=DEFAULT_HANDOFF, help="Handoff file to process")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without modifying files")
    args = parser.parse_args()

    process_handoff(args.file, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
