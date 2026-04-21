#!/usr/bin/env python3
"""
Obsidian Enrich — Add inline [[wikilinks]] to knowledge vault body text.

One-time enrichment script. Converts plain-text references (Ley XX, Mistake #XX,
Quality Gate, Supremacy Mode, etc.) into Obsidian wikilinks with display aliases.

Usage:
    python obsidian_enrich.py                          # dry-run (default)
    python obsidian_enrich.py --apply                  # apply changes
    python obsidian_enrich.py --vault ~/.claude/knowledge_vault/  # custom path
"""

import argparse
import io
import re
import sys
from pathlib import Path

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DEFAULT_VAULT = Path.home() / ".claude" / "knowledge_vault"

# Mapping: regex pattern -> replacement wikilink
# Order matters: more specific patterns first
LINK_RULES = [
    # Leyes — core (24-29)
    (r'(?<!\[\[)(?<!"\[\[)\b(Ley(?:es)?\s+2[4-9])\b(?!\]\])', r'[[core/leyes-core|\1]]'),
    # Leyes — domain (31, 34-38)
    (r'(?<!\[\[)(?<!"\[\[)\b(Ley(?:es)?\s+3[1-8])\b(?!\]\])', r'[[domain/leyes-domain|\1]]'),
    # Mistakes #1-27 -> global
    (r'(?<!\[\[)(?<!"\[\[)\b(Mistake\s+#(?:[1-9]|1\d|2[0-7]))\b(?!\]\])', r'[[core/mistakes-global|\1]]'),
    # Mistakes #28-38 -> extended
    (r'(?<!\[\[)(?<!"\[\[)\b(Mistake\s+#(?:2[8-9]|3\d))\b(?!\]\])', r'[[core/mistakes-extended|\1]]'),
    # Mistakes #39+ (bukkit/minecraft range) -> bukkit-mistakes
    (r'(?<!\[\[)(?<!"\[\[)\b(Mistake\s+#(?:[4-9]\d|[1-9]\d{2}))\b(?!\]\])', r'[[minecraft/bukkit-mistakes|\1]]'),
    # Quality Gate(s)
    (r'(?<!\[\[)(?<!"\[\[)\b(Quality\s+Gate(?:s)?(?:\s+\d+)?)\b(?!\]\])', r'[[core/quality-gates|\1]]'),
    # Supremacy Mode
    (r'(?<!\[\[)(?<!"\[\[)\b(Supremacy\s+Mode)\b(?!\]\])', r'[[governance/supremacy-mode|\1]]'),
    (r'(?<!\[\[)(?<!"\[\[)\b(SUPREMACY\s+MODE)\b(?!\]\])', r'[[governance/supremacy-mode|\1]]'),
    # Anti-Monolith / ANTI-MONOLITH
    (r'(?<!\[\[)(?<!"\[\[)\b(ANTI-MONOLITH)\b(?!\]\])', r'[[execution/anti-monolith|\1]]'),
    (r'(?<!\[\[)(?<!"\[\[)\b(Anti-Monolith)\b(?!\]\])', r'[[execution/anti-monolith|\1]]'),
    # Intent-Lock / INTENT-LOCK
    (r'(?<!\[\[)(?<!"\[\[)\b(INTENT-LOCK)\b(?!\]\])', r'[[execution/intent-lock|\1]]'),
    (r'(?<!\[\[)(?<!"\[\[)\b(Intent-Lock)\b(?!\]\])', r'[[execution/intent-lock|\1]]'),
    # Scaffold Illusion (common reference)
    (r'(?<!\[\[)(?<!"\[\[)\b(Scaffold\s+Illusion)\b(?!\]\])', r'[[core/mistakes-global|\1]]'),
    # DNA-036
    (r'(?<!\[\[)(?<!"\[\[)\b(DNA-036)\b(?!\]\])', r'[[governance/omni-iterator|\1]]'),
    # DNA-300
    (r'(?<!\[\[)(?<!"\[\[)\b(DNA-300)\b(?!\]\])', r'[[governance/dna-300-context-anchor|\1]]'),
]


def is_frontmatter(lines: list[str], idx: int) -> bool:
    """Check if line index is inside YAML frontmatter (between --- delimiters)."""
    if not lines or lines[0].strip() != "---":
        return False
    in_fm = False
    for i, line in enumerate(lines):
        if i == 0 and line.strip() == "---":
            in_fm = True
            continue
        if in_fm and line.strip() == "---":
            return idx <= i
    return False


def is_code_block(lines: list[str], idx: int) -> bool:
    """Check if line index is inside a fenced code block."""
    in_code = False
    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            in_code = not in_code
        if i == idx:
            return in_code
    return False


def get_self_target(filepath: Path, vault_root: Path) -> str:
    """Get the wikilink target that would point to this file (for self-link prevention)."""
    rel = filepath.relative_to(vault_root)
    return str(rel.with_suffix("")).replace("\\", "/")


def enrich_file(filepath: Path, vault_root: Path, dry_run: bool = True) -> list[str]:
    """Add wikilinks to a single file. Returns list of changes made."""
    content = filepath.read_text(encoding="utf-8")
    lines = content.split("\n")
    changes = []
    self_target = get_self_target(filepath, vault_root)

    # Filter out rules that would create self-links
    active_rules = [
        (pat, repl) for pat, repl in LINK_RULES
        if self_target not in repl
    ]

    new_lines = []
    for idx, line in enumerate(lines):
        if is_frontmatter(lines, idx) or is_code_block(lines, idx):
            new_lines.append(line)
            continue

        # Skip lines that are already wikilinks in see_also
        if line.strip().startswith('- "[['):
            new_lines.append(line)
            continue

        original = line
        for pattern, replacement in active_rules:
            line = re.sub(pattern, replacement, line)

        if line != original:
            changes.append(f"  L{idx+1}: {original.strip()}")
            changes.append(f"     -> {line.strip()}")

        new_lines.append(line)

    if changes and not dry_run:
        filepath.write_text("\n".join(new_lines), encoding="utf-8")

    return changes


def main():
    parser = argparse.ArgumentParser(description="Add inline wikilinks to knowledge vault")
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT, help="Vault root path")
    parser.add_argument("--apply", action="store_true", help="Apply changes (default is dry-run)")
    args = parser.parse_args()

    if not args.vault.exists():
        print(f"ERROR: Vault not found at {args.vault}")
        sys.exit(1)

    mode = "APPLYING" if args.apply else "DRY-RUN"
    print(f"=== Obsidian Enrich ({mode}) ===")
    print(f"Vault: {args.vault}\n")

    total_changes = 0
    md_files = sorted(args.vault.rglob("*.md"))

    for filepath in md_files:
        # Skip .obsidian/, .backups/, INDEX.md
        rel = filepath.relative_to(args.vault)
        if str(rel).startswith((".obsidian", ".backups", "_meta")):
            continue
        if filepath.name == "INDEX.md":
            continue

        changes = enrich_file(filepath, args.vault, dry_run=not args.apply)
        if changes:
            print(f"{'MODIFIED' if args.apply else 'WOULD MODIFY'}: {rel}")
            for c in changes:
                print(c)
            print()
            total_changes += len(changes) // 2

    print(f"--- {total_changes} substitutions {'applied' if args.apply else 'found (dry-run)'} ---")
    if not args.apply and total_changes > 0:
        print("Run with --apply to write changes.")


if __name__ == "__main__":
    main()
