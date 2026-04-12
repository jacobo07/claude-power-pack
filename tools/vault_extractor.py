#!/usr/bin/env python3
"""
Vault Extractor — Splits a monolithic CLAUDE.md into an Obsidian-compatible vault.

Parses ## sections, categorizes them by domain, writes individual .md files
with [[wikilinks]], and generates an INDEX.md for token-efficient navigation.

Usage:
    python vault_extractor.py extract ~/.claude/CLAUDE.md --vault ~/.claude/vault/
    python vault_extractor.py verify ~/.claude/CLAUDE.md --vault ~/.claude/vault/
    python vault_extractor.py index --vault ~/.claude/vault/
"""

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ── Section categorization map ──────────────────────────────────────────────
# Maps regex patterns (matched against section titles) to (subdir, filename).
# Order matters: first match wins.
CATEGORY_MAP = [
    # Setup & Integration
    (r"Global Alignment Ledger|CARL Integration|First-Time.*Setup", "setup", "gal-integration.md"),
    (r"ExecutionOS Lite", "setup", "executionos-tiers.md"),
    (r"Governance Overlay", "setup", "governance-overlay.md"),
    (r"Shared Repo Anti-Overlap", "setup", "shared-repo.md"),
    # Stacks
    (r"KobiiAI Stack", "stacks", "kobiiAI-stack.md"),
    (r"SaaS Launch", "stacks", "saas-doctrine.md"),
    (r"AKOS Knowledge|ChatGPT Vision|DNA Flywheel", "stacks", "knowledge-tools.md"),
    # Protocols
    (r"USAP", "protocols", "usap.md"),
    (r"Intent Compiler", "protocols", "intent-compiler.md"),
    (r"Token Efficiency", "protocols", "token-efficiency.md"),
    (r"Session Logging", "protocols", "session-logging.md"),
    (r"ONE-SHOT SUPREMACY", "protocols", "supremacy-mode.md"),
    (r"Universal Completeness", "protocols", "supremacy-mode.md"),  # merged with supremacy
    # Leyes
    (r"Ley 24", "leyes", "ley-24-anti-hallucination.md"),
    (r"Ley 25", "leyes", "ley-25-empirical-evidence.md"),
    (r"Ley 26", "leyes", "ley-26-zero-shot-veto.md"),
    (r"Ley 27", "leyes", "ley-27-auto-heal.md"),
    (r"Ley 28|Ley 29", "leyes", "ley-28-29-autonomy.md"),
    (r"Ley 31", "leyes", "ley-31-domain-seal.md"),
    (r"Ley 34", "leyes", "ley-34-visual-sovereignty.md"),
    (r"Ley 35", "leyes", "ley-35-effort-parity.md"),
    (r"Ley 36", "leyes", "ley-36-retention-curve.md"),
    (r"Ley 37", "leyes", "ley-37-open-loop.md"),
    (r"Ley 38", "leyes", "ley-38-sensory-floor.md"),
    # Mistakes
    (r"Claude Code Mistakes.*check before", "mistakes", "mistakes-01-27.md"),
    (r"Claude Code Mistakes.*additions", "mistakes", "mistakes-28-38.md"),
    # Gates
    (r"Completion Quality Gates", "gates", "completion-gates.md"),
]

# Descriptions for INDEX.md wikilinks
FILE_DESCRIPTIONS = {
    "gal-integration.md": "GAL, CARL, first-time project bootstrap",
    "executionos-tiers.md": "LIGHT/STANDARD/DEEP/FORENSIC tier classification",
    "governance-overlay.md": "Auto-activation rules for dev skills",
    "shared-repo.md": "Anti-overlap protocol for shared repos",
    "kobiiAI-stack.md": "Frontend (frozen TS/Next) + Backend (Elixir/OTP)",
    "saas-doctrine.md": "14-phase SaaS Launch, stack definition",
    "knowledge-tools.md": "AKOS injection, ChatGPT Vision, DNA Flywheel",
    "usap.md": "Universal Skill Activation Protocol — mandatory skills",
    "intent-compiler.md": "7-step decompose protocol for code tasks",
    "token-efficiency.md": "Token budget rules, tool hierarchy",
    "session-logging.md": "Session file format and tracking",
    "supremacy-mode.md": "3 gates (Feel Codex, Adversarial, Voice) + Level 10 standard",
    "ley-24-anti-hallucination.md": "El Veto de la Realidad — no technical optimism",
    "ley-25-empirical-evidence.md": "DONE = Sleepless QA PASS, not logic",
    "ley-26-zero-shot-veto.md": "Plan required before execution (>1 file)",
    "ley-27-auto-heal.md": "Every feature born with .yml test twin",
    "ley-28-29-autonomy.md": "Agent executes own commands, never outsources",
    "ley-31-domain-seal.md": "Domain code never imports cross-domain",
    "ley-34-visual-sovereignty.md": "Visual quality gate before publish",
    "ley-35-effort-parity.md": "Every feature generates a communication asset",
    "ley-36-retention-curve.md": ">60% retention to second 20, drivers required",
    "ley-37-open-loop.md": ">=2 open loops per short <60s",
    "ley-38-sensory-floor.md": ">=3 sensory layers per second of content",
    "mistakes-01-27.md": "Universal mistakes #1-27 (Building Without Wiring → Overblocking)",
    "mistakes-28-38.md": "Domain mistakes #28-38 (Feel Codex → Mono-Layer Boredom)",
    "completion-gates.md": "7 mandatory gates: tsc, lint, build, tests, schema, scaffold, evidence",
}


@dataclass
class Section:
    """A parsed ## section from CLAUDE.md."""
    title: str
    content: str  # full text including the ## header line
    line_start: int
    line_end: int
    category: Optional[str] = None  # subdir name
    filename: Optional[str] = None  # target filename


def parse_sections(text: str) -> list[Section]:
    """Split CLAUDE.md into sections by ## headers."""
    lines = text.split("\n")
    sections: list[Section] = []
    current_title = ""
    current_lines: list[str] = []
    current_start = 0

    for i, line in enumerate(lines):
        if line.startswith("## ") and i > 0:
            # Close previous section
            if current_lines:
                content = "\n".join(current_lines).strip()
                if content:
                    sections.append(Section(
                        title=current_title,
                        content=content,
                        line_start=current_start,
                        line_end=i - 1,
                    ))
            current_title = line[3:].strip()
            current_lines = [line]
            current_start = i
        else:
            current_lines.append(line)

    # Last section
    if current_lines:
        content = "\n".join(current_lines).strip()
        if content:
            sections.append(Section(
                title=current_title,
                content=content,
                line_start=current_start,
                line_end=len(lines) - 1,
            ))

    return sections


def categorize_sections(sections: list[Section]) -> list[Section]:
    """Assign category (subdir) and filename to each section."""
    for section in sections:
        matched = False
        for pattern, category, filename in CATEGORY_MAP:
            if re.search(pattern, section.title, re.IGNORECASE):
                section.category = category
                section.filename = filename
                matched = True
                break
        if not matched:
            # Uncategorized sections go to setup/ as catch-all
            safe_name = re.sub(r"[^\w\s-]", "", section.title.lower())
            safe_name = re.sub(r"\s+", "-", safe_name.strip())[:40]
            section.category = "uncategorized"
            section.filename = f"{safe_name}.md"
    return sections


def add_wikilinks(content: str, all_filenames: set[str]) -> str:
    """Add [[wikilinks]] to cross-references between vault files."""
    # Link Ley references → their vault files
    def link_ley(m):
        num = m.group(1)
        for fn in all_filenames:
            if f"ley-{num}" in fn or f"ley-{num}-" in fn:
                name = fn.replace(".md", "")
                return f"[[{name}|Ley {num}]]"
        return m.group(0)

    content = re.sub(r"Ley (\d+)", link_ley, content)

    # Link Mistake references
    def link_mistake(m):
        num = int(m.group(1))
        if num <= 27:
            return f"[[mistakes-01-27|Mistake #{num}]]"
        else:
            return f"[[mistakes-28-38|Mistake #{num}]]"

    content = re.sub(r"Mistake #(\d+)", link_mistake, content)

    # Link Gate references
    content = re.sub(r"Gate (\d)", r"[[completion-gates|Gate \1]]", content)

    return content


def write_vault(sections: list[Section], vault_path: Path) -> dict[str, str]:
    """Write categorized sections to vault files. Returns {filepath: content} map."""
    written: dict[str, str] = {}

    # Group sections by target file (some sections merge into one file)
    file_groups: dict[str, list[Section]] = {}
    for s in sections:
        if s.filename is None:
            continue
        key = f"{s.category}/{s.filename}"
        file_groups.setdefault(key, []).append(s)

    all_filenames = {s.filename for s in sections if s.filename}

    for rel_path, group in file_groups.items():
        subdir, filename = rel_path.split("/", 1)
        dir_path = vault_path / subdir
        dir_path.mkdir(parents=True, exist_ok=True)

        # Merge sections destined for the same file
        merged_content = "\n\n".join(s.content for s in group)
        merged_content = add_wikilinks(merged_content, all_filenames)

        # Add frontmatter
        primary_title = group[0].title or filename.replace(".md", "").replace("-", " ").title()
        desc = FILE_DESCRIPTIONS.get(filename, primary_title)
        frontmatter = f"---\ntitle: \"{primary_title}\"\ndescription: \"{desc}\"\nsource: CLAUDE.md lines {group[0].line_start}-{group[-1].line_end}\n---\n\n"

        full_content = frontmatter + merged_content + "\n"
        file_path = dir_path / filename
        file_path.write_text(full_content, encoding="utf-8")
        written[str(file_path.relative_to(vault_path))] = full_content

    return written


def generate_index(vault_path: Path, source_path: Optional[str] = None) -> str:
    """Generate INDEX.md with wikilinks to all vault files."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    parts = [
        "# Governance Vault",
        f"Generated: {now}" + (f" | Source: `{source_path}`" if source_path else ""),
        "",
        "Navigate via [[wikilinks]]. Load only what's relevant — max 5 pages per task.",
        "",
    ]

    # Scan vault subdirs
    subdirs = sorted(set(
        p.parent.name for p in vault_path.rglob("*.md")
        if p.name != "INDEX.md" and not p.parent.name.startswith("_")
    ))

    for subdir in subdirs:
        parts.append(f"## {subdir.title()}")
        subdir_path = vault_path / subdir
        if not subdir_path.is_dir():
            continue
        for md_file in sorted(subdir_path.glob("*.md")):
            name = md_file.stem
            desc = FILE_DESCRIPTIONS.get(md_file.name, name.replace("-", " ").title())
            parts.append(f"- [[{name}]] — {desc}")
        parts.append("")

    return "\n".join(parts)


def write_meta(vault_path: Path, source_text: str, written_files: dict[str, str]):
    """Write vault metadata for sync tracking."""
    meta_dir = vault_path / "_meta"
    meta_dir.mkdir(parents=True, exist_ok=True)

    source_hash = hashlib.sha256(source_text.encode()).hexdigest()
    vault_hash = hashlib.sha256(
        "".join(sorted(written_files.values())).encode()
    ).hexdigest()

    meta = {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_hash": source_hash,
        "vault_hash": vault_hash,
        "file_count": len(written_files),
        "files": {k: hashlib.sha256(v.encode()).hexdigest()[:12] for k, v in written_files.items()},
    }

    (meta_dir / "vault_meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )


def verify_completeness(source_path: Path, vault_path: Path) -> tuple[bool, str]:
    """Verify 0% content loss by comparing normalized text."""
    source_text = source_path.read_text(encoding="utf-8")

    # Extract just the section content (skip frontmatter comment line)
    source_lines = source_text.strip().split("\n")
    if source_lines and source_lines[0].startswith("<!--"):
        source_lines = source_lines[1:]
    # Skip the top-level # header
    if source_lines and source_lines[0].startswith("# "):
        source_lines = source_lines[1:]

    # Normalize: strip whitespace, remove empty lines, lowercase for comparison
    def normalize(text: str) -> list[str]:
        lines = text.split("\n")
        result = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            # Skip frontmatter
            if stripped == "---" or stripped.startswith("title:") or stripped.startswith("description:") or stripped.startswith("source:"):
                continue
            result.append(stripped)
        return result

    source_normalized = normalize("\n".join(source_lines))

    # Collect all vault content
    vault_content = []
    for md_file in sorted(vault_path.rglob("*.md")):
        if md_file.name == "INDEX.md":
            continue
        if md_file.parent.name == "_meta":
            continue
        vault_content.append(md_file.read_text(encoding="utf-8"))
    vault_normalized = normalize("\n".join(vault_content))

    # Compare: check that every source line appears in vault
    # (vault may have extra lines from wikilink substitutions)
    source_set = set(source_normalized)
    vault_text_joined = "\n".join(vault_normalized)

    missing = []
    for line in source_normalized:
        # Check exact match or wikilink-substituted match
        if line not in vault_normalized:
            # Check if it's a wikilink substitution (e.g., "Ley 24" → "[[ley-24...|Ley 24]]")
            plain_line = re.sub(r"\[\[[^\]]*\|([^\]]*)\]\]", r"\1", vault_text_joined)
            if line not in plain_line.split("\n"):
                missing.append(line)

    if missing:
        report = f"FAIL: {len(missing)} lines missing from vault:\n"
        for m in missing[:10]:
            report += f"  - {m[:80]}...\n" if len(m) > 80 else f"  - {m}\n"
        if len(missing) > 10:
            report += f"  ... and {len(missing) - 10} more\n"
        return False, report

    coverage = len(source_set)
    return True, f"PASS: {coverage} unique source lines verified in vault. 0% loss."


def cmd_extract(args):
    """Extract CLAUDE.md into vault."""
    source_path = Path(args.source).expanduser()
    vault_path = Path(args.vault).expanduser()

    if not source_path.exists():
        print(f"ERROR: Source file not found: {source_path}", file=sys.stderr)
        sys.exit(1)

    source_text = source_path.read_text(encoding="utf-8")
    print(f"Source: {source_path} ({len(source_text.split(chr(10)))} lines, {len(source_text)} chars)")

    # Parse and categorize
    sections = parse_sections(source_text)
    sections = categorize_sections(sections)

    print(f"Parsed: {len(sections)} sections")
    for s in sections:
        cat = f"{s.category}/{s.filename}" if s.category else "UNCATEGORIZED"
        print(f"  [{cat}] {s.title} (lines {s.line_start}-{s.line_end})")

    # Write vault
    vault_path.mkdir(parents=True, exist_ok=True)
    written = write_vault(sections, vault_path)
    print(f"\nWritten: {len(written)} files to {vault_path}")

    # Generate INDEX.md
    index_content = generate_index(vault_path, str(source_path))
    (vault_path / "INDEX.md").write_text(index_content, encoding="utf-8")
    index_tokens = len(index_content.split()) * 1.3  # rough token estimate
    print(f"INDEX.md: ~{int(index_tokens)} tokens")

    # Write metadata
    write_meta(vault_path, source_text, written)

    # Auto-verify
    passed, report = verify_completeness(source_path, vault_path)
    print(f"\nVerification: {report}")

    if not passed:
        sys.exit(1)

    print(f"\nVault ready at: {vault_path}")
    print(f"Read ~/.claude/vault/INDEX.md to navigate.")


def cmd_verify(args):
    """Verify vault completeness against source."""
    source_path = Path(args.source).expanduser()
    vault_path = Path(args.vault).expanduser()

    if not source_path.exists():
        print(f"ERROR: Source not found: {source_path}", file=sys.stderr)
        sys.exit(1)
    if not vault_path.exists():
        print(f"ERROR: Vault not found: {vault_path}", file=sys.stderr)
        sys.exit(1)

    passed, report = verify_completeness(source_path, vault_path)
    print(report)
    sys.exit(0 if passed else 1)


def cmd_index(args):
    """Regenerate INDEX.md from existing vault."""
    vault_path = Path(args.vault).expanduser()
    if not vault_path.exists():
        print(f"ERROR: Vault not found: {vault_path}", file=sys.stderr)
        sys.exit(1)

    index_content = generate_index(vault_path)
    (vault_path / "INDEX.md").write_text(index_content, encoding="utf-8")
    print(f"INDEX.md regenerated at {vault_path / 'INDEX.md'}")


def main():
    parser = argparse.ArgumentParser(
        description="Vault Extractor — Split CLAUDE.md into Obsidian vault"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # extract
    p_extract = sub.add_parser("extract", help="Extract CLAUDE.md into vault files")
    p_extract.add_argument("source", help="Path to CLAUDE.md")
    p_extract.add_argument("--vault", default="~/.claude/vault/", help="Vault output directory")
    p_extract.set_defaults(func=cmd_extract)

    # verify
    p_verify = sub.add_parser("verify", help="Verify vault completeness")
    p_verify.add_argument("source", help="Path to original CLAUDE.md")
    p_verify.add_argument("--vault", default="~/.claude/vault/", help="Vault directory")
    p_verify.set_defaults(func=cmd_verify)

    # index
    p_index = sub.add_parser("index", help="Regenerate INDEX.md")
    p_index.add_argument("--vault", default="~/.claude/vault/", help="Vault directory")
    p_index.set_defaults(func=cmd_index)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
