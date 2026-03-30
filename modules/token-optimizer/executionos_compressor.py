#!/usr/bin/env python3
"""ExecutionOS Compressor - Parses markdown prompts, scores sections by universality tier, compresses filler."""

import argparse
import re
import sys
from pathlib import Path


TIER_KEYWORDS = {
    "core": {
        "keywords": ["always", "never", "must", "every session", "mandatory", "required", "all projects", "global"],
        "weight": 1.0,
    },
    "standard": {
        "keywords": ["implement", "test", "build", "create", "write", "function", "module", "component"],
        "weight": 0.7,
    },
    "deep": {
        "keywords": ["architecture", "migration", "refactor", "redesign", "schema", "infrastructure", "overhaul"],
        "weight": 0.4,
    },
    "forensic": {
        "keywords": ["deploy", "production", "incident", "rollback", "hotfix", "outage", "postmortem", "debug"],
        "weight": 0.2,
    },
}

FILLER_PATTERNS = [
    r"^\s*$",
    r"^<!--.*-->$",
    r"^---+$",
    r"^\s*#\s*$",
]

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
]


def parse_sections(text: str) -> list[dict]:
    """Split markdown into sections by ## headers."""
    sections = []
    current_title = "(Preamble)"
    current_lines: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^##\s+(.+)$", line)
        if match:
            if current_lines or current_title == "(Preamble)":
                sections.append({"title": current_title, "lines": current_lines})
            current_title = match.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)
    sections.append({"title": current_title, "lines": current_lines})
    return sections


def score_section(section: dict) -> tuple[str, float]:
    """Score a section for universality. Returns (tier_name, score)."""
    text_lower = "\n".join(section["lines"]).lower()
    best_tier = "standard"
    best_score = 0.0
    for tier_name, tier_info in TIER_KEYWORDS.items():
        hits = sum(1 for kw in tier_info["keywords"] if kw in text_lower)
        if hits > 0:
            score = min(1.0, (hits / len(tier_info["keywords"])) * tier_info["weight"] * 2)
            if score > best_score:
                best_score = score
                best_tier = tier_name
    if best_score == 0.0:
        best_score = 0.5
    return best_tier, round(best_score, 2)


def compress_lines(lines: list[str]) -> list[str]:
    """Remove filler lines and excess whitespace."""
    result = []
    prev_blank = False
    for line in lines:
        is_filler = any(re.match(pat, line) for pat in FILLER_PATTERNS)
        is_blank = line.strip() == ""
        if is_blank:
            if not prev_blank:
                result.append("")
            prev_blank = True
            continue
        prev_blank = False
        if is_filler:
            continue
        compressed = line
        for phrase in FILLER_PHRASES:
            compressed = re.sub(re.escape(phrase), "", compressed, flags=re.IGNORECASE)
        compressed = re.sub(r"  +", " ", compressed)
        result.append(compressed)
    return result


def estimate_tokens(text: str) -> int:
    words = len(text.split())
    return int(words * 1.33)


def main():
    parser = argparse.ArgumentParser(description="ExecutionOS Compressor - Score and compress markdown prompt files")
    parser.add_argument("input", type=str, help="Path to markdown prompt file")
    parser.add_argument("--compress", action="store_true", help="Output compressed version to stdout")
    args = parser.parse_args()

    path = Path(args.input)
    if not path.exists():
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(1)

    text = path.read_text(encoding="utf-8")
    original_tokens = estimate_tokens(text)
    sections = parse_sections(text)

    tier_buckets: dict[str, list[dict]] = {"core": [], "standard": [], "deep": [], "forensic": []}
    total_compressed_tokens = 0

    for section in sections:
        tier, score = score_section(section)
        compressed = compress_lines(section["lines"])
        orig_tokens = estimate_tokens("\n".join(section["lines"]))
        comp_tokens = estimate_tokens("\n".join(compressed))
        total_compressed_tokens += comp_tokens
        tier_buckets[tier].append({
            "title": section["title"],
            "score": score,
            "original_lines": len(section["lines"]),
            "compressed_lines": len(compressed),
            "original_tokens": orig_tokens,
            "compressed_tokens": comp_tokens,
            "compressed_content": compressed,
        })

    print("=" * 70)
    print("EXECUTIONOS COMPRESSOR REPORT")
    print("=" * 70)
    print(f"File: {path}")
    print(f"Original tokens (est): {original_tokens:,}")
    print(f"Compressed tokens (est): {total_compressed_tokens:,}")
    savings = original_tokens - total_compressed_tokens
    pct = (savings / original_tokens * 100) if original_tokens > 0 else 0
    print(f"Savings: {savings:,} tokens ({pct:.1f}%)")
    print()

    for tier_name in ["core", "standard", "deep", "forensic"]:
        items = tier_buckets[tier_name]
        if not items:
            continue
        tier_tokens = sum(i["original_tokens"] for i in items)
        print(f"--- {tier_name.upper()} TIER ({len(items)} sections, {tier_tokens:,} tokens) ---")
        for item in items:
            saved = item["original_tokens"] - item["compressed_tokens"]
            print(f"  [{item['score']:.2f}] {item['title']}")
            print(f"         {item['original_lines']} -> {item['compressed_lines']} lines, "
                  f"{item['original_tokens']} -> {item['compressed_tokens']} tokens (saved {saved})")
        print()

    if args.compress:
        print("=" * 70)
        print("COMPRESSED OUTPUT")
        print("=" * 70)
        for section in sections:
            tier, _ = score_section(section)
            compressed = compress_lines(section["lines"])
            if section["title"] != "(Preamble)":
                print(f"\n## {section['title']}")
            print("\n".join(compressed))


if __name__ == "__main__":
    main()
