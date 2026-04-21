#!/usr/bin/env python3
"""
Vault Sync — Regenerate INDEX.md, validate wikilinks, and track changes.

Scans ~/.claude/knowledge_vault/ for all .md files, rebuilds INDEX.md with
Obsidian-compatible wikilinks, and updates _meta/vault_meta.json for change detection.

Usage:
    python vault_sync.py                                          # sync default vault
    python vault_sync.py --vault ~/.claude/knowledge_vault/       # explicit path
    python vault_sync.py --check                                  # check for changes
    python vault_sync.py --validate                               # validate wikilinks + frontmatter
"""

import argparse
import hashlib
import io
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DEFAULT_VAULT = "~/.claude/knowledge_vault/"

# Tier display order and labels for INDEX.md
TIER_ORDER = ["core", "governance", "execution", "minecraft", "stacks", "domain"]
TIER_LABELS = {
    "core": "Core (always-load on STANDARD+)",
    "governance": "Governance (load on STANDARD+)",
    "execution": "Execution (load on STANDARD+)",
    "minecraft": "Minecraft (load when working on KobiiCraft plugins)",
    "stacks": "Stacks (load when domain matches)",
    "domain": "Domain (rarely-needed, load on explicit trigger)",
}


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_text(encoding="utf-8").encode()).hexdigest()[:12]


def extract_frontmatter(path: Path) -> dict:
    """Extract YAML frontmatter as a simple dict (no PyYAML dependency)."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("---", 3)
    if end == -1:
        return {}
    fm_text = text[3:end].strip()
    result = {}
    for line in fm_text.split("\n"):
        if ":" in line and not line.startswith(" ") and not line.startswith("-"):
            key, _, val = line.partition(":")
            val = val.strip().strip('"').strip("'")
            result[key.strip()] = val
    return result


def get_content_files(vault_path: Path) -> list[Path]:
    """Get all content .md files (excluding meta, obsidian, backups, INDEX)."""
    files = []
    for md_file in sorted(vault_path.rglob("*.md")):
        rel = str(md_file.relative_to(vault_path)).replace("\\", "/")
        if rel.startswith((".obsidian", ".backups", "_meta")) or "/_details/" in rel or "\\_details\\" in rel:
            continue
        if md_file.name == "INDEX.md":
            continue
        files.append(md_file)
    return files


def generate_index(vault_path: Path) -> str:
    """Generate INDEX.md with Obsidian wikilinks and tier groupings."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    parts = [
        "---",
        'title: "Knowledge Vault \u2014 Master Index"',
        'version: "2.0"',
        'created: "2026-04-12"',
        f'updated: "{now}"',
        "---",
        "",
        "# Knowledge Vault \u2014 Master Index",
        "",
    ]

    # Group files by subdirectory
    groups: dict[str, list[Path]] = {}
    for md_file in get_content_files(vault_path):
        subdir = md_file.parent.name
        groups.setdefault(subdir, []).append(md_file)

    for tier in TIER_ORDER:
        if tier not in groups:
            continue
        label = TIER_LABELS.get(tier, tier.title())
        parts.append(f"## {label}")
        for md_file in sorted(groups[tier]):
            fm = extract_frontmatter(md_file)
            title = fm.get("title", md_file.stem.replace("-", " ").title())
            rel_stem = f"{tier}/{md_file.stem}"
            parts.append(f"- [[{rel_stem}]] \u2014 {title}")
        parts.append("")

    # Any unlisted subdirs
    for subdir in sorted(groups.keys()):
        if subdir in TIER_ORDER:
            continue
        parts.append(f"## {subdir.title()}")
        for md_file in sorted(groups[subdir]):
            fm = extract_frontmatter(md_file)
            title = fm.get("title", md_file.stem.replace("-", " ").title())
            rel_stem = f"{subdir}/{md_file.stem}"
            parts.append(f"- [[{rel_stem}]] \u2014 {title}")
        parts.append("")

    return "\n".join(parts)


def build_meta(vault_path: Path) -> dict:
    files = {}
    for md_file in get_content_files(vault_path):
        rel = str(md_file.relative_to(vault_path)).replace("\\", "/")
        files[rel] = hash_file(md_file)

    return {
        "version": "2.0",
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "file_count": len(files),
        "files": files,
    }


def check_changes(vault_path: Path) -> list[str]:
    """Check if vault files changed since last sync."""
    meta_path = vault_path / "_meta" / "vault_meta.json"
    if not meta_path.exists():
        return ["no metadata found \u2014 full sync needed"]

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    old_files = meta.get("files", {})
    changes = []

    current_files = {}
    for md_file in get_content_files(vault_path):
        rel = str(md_file.relative_to(vault_path)).replace("\\", "/")
        current_files[rel] = hash_file(md_file)

    for rel, h in current_files.items():
        if rel not in old_files:
            changes.append(f"NEW: {rel}")
        elif old_files[rel] != h:
            changes.append(f"CHANGED: {rel}")

    for rel in old_files:
        if rel not in current_files:
            changes.append(f"DELETED: {rel}")

    return changes


def validate(vault_path: Path) -> int:
    """Validate vault: frontmatter, wikilinks, orphans. Returns error count."""
    errors = 0
    all_stems = set()
    referenced_stems = set()
    content_files = get_content_files(vault_path)

    # Build set of valid targets
    for md_file in content_files:
        rel = md_file.relative_to(vault_path)
        stem = str(rel.with_suffix("")).replace("\\", "/")
        all_stems.add(stem)

    print(f"=== Vault Validation ===")
    print(f"Vault: {vault_path}")
    print(f"Files: {len(content_files)}\n")

    for md_file in content_files:
        rel = str(md_file.relative_to(vault_path)).replace("\\", "/")
        text = md_file.read_text(encoding="utf-8")

        # Check frontmatter exists
        if not text.startswith("---"):
            print(f"ERROR [{rel}]: Missing YAML frontmatter")
            errors += 1
            continue

        fm = extract_frontmatter(md_file)
        if not fm.get("title"):
            print(f"ERROR [{rel}]: Missing 'title' in frontmatter")
            errors += 1
        if not fm.get("tier"):
            print(f"ERROR [{rel}]: Missing 'tier' in frontmatter")
            errors += 1

        # Check all wikilinks resolve
        wikilinks = re.findall(r'\[\[([^\]|]+?)(?:\|[^\]]+?)?\]\]', text)
        for link in wikilinks:
            link_clean = link.strip()
            referenced_stems.add(link_clean)
            if link_clean not in all_stems:
                print(f"WARN  [{rel}]: Broken wikilink [[{link_clean}]]")
                errors += 1

    # Check for orphans (files not referenced by any other file)
    orphans = all_stems - referenced_stems
    if orphans:
        print(f"\nOrphan files (not referenced by any wikilink):")
        for o in sorted(orphans):
            print(f"  {o}")

    # Size warnings (Token Shield — DNA-3000)
    total_bytes = 0
    oversized = []
    for md_file in content_files:
        size = md_file.stat().st_size
        total_bytes += size
        rel = str(md_file.relative_to(vault_path)).replace("\\", "/")
        if size > 5000:
            oversized.append((rel, size))

    if oversized:
        print(f"\nSize warnings (>5KB per file):")
        for rel, size in sorted(oversized, key=lambda x: -x[1]):
            print(f"  WARN: {rel} = {size:,} bytes ({size // 1000}KB)")

    if total_bytes > 60000:
        print(f"\nWARN: Total vault size = {total_bytes:,} bytes (~{total_bytes // 1000}KB). Target: <60KB.")
    else:
        print(f"\nVault size: {total_bytes:,} bytes (~{total_bytes // 1000}KB) \u2014 within 60KB budget.")

    # Check _details/ consistency
    for subdir in vault_path.iterdir():
        if not subdir.is_dir():
            continue
        details_dir = subdir / "_details"
        if details_dir.exists():
            for detail_file in details_dir.glob("*.md"):
                # Check parent exists (e.g., _details/foo-verbose.md should have ../foo.md or similar)
                stem = detail_file.stem.replace("-verbose", "")
                parent_candidates = list(subdir.glob(f"{stem}*.md"))
                if not parent_candidates:
                    print(f"  WARN: {detail_file.relative_to(vault_path)} has no parent file in {subdir.name}/")

    # Summary
    wikilink_count = 0
    for md_file in content_files:
        text = md_file.read_text(encoding="utf-8")
        wikilink_count += len(re.findall(r'\[\[', text))

    print(f"\n--- Validation complete ---")
    print(f"Files: {len(content_files)} | Wikilinks: {wikilink_count} | Errors: {errors}")
    if errors == 0:
        print("STATUS: PASS")
    else:
        print(f"STATUS: FAIL ({errors} errors)")

    return errors


def sync(vault_path: Path, check_only: bool = False):
    if not vault_path.exists():
        print(f"ERROR: Vault not found: {vault_path}", file=sys.stderr)
        sys.exit(1)

    changes = check_changes(vault_path)

    if check_only:
        if changes:
            print(f"Changes detected ({len(changes)}):")
            for c in changes:
                print(f"  {c}")
        else:
            print("No changes detected. Vault is in sync.")
        sys.exit(0)

    # Regenerate INDEX.md
    index_content = generate_index(vault_path)
    (vault_path / "INDEX.md").write_text(index_content, encoding="utf-8")

    # Update metadata
    meta = build_meta(vault_path)
    meta_dir = vault_path / "_meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    (meta_dir / "vault_meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )

    file_count = meta["file_count"]
    index_tokens = int(len(index_content.split()) * 1.3)
    print(f"Vault synced: {file_count} files, INDEX.md ~{index_tokens} tokens")
    if changes:
        print(f"Changes applied ({len(changes)}):")
        for c in changes:
            print(f"  {c}")
    else:
        print("No file changes (INDEX.md regenerated).")


def main():
    parser = argparse.ArgumentParser(description="Vault Sync \u2014 regenerate INDEX.md + validate")
    parser.add_argument("--vault", default=DEFAULT_VAULT, help="Vault directory")
    parser.add_argument("--check", action="store_true", help="Check for changes without syncing")
    parser.add_argument("--validate", action="store_true", help="Validate frontmatter + wikilinks")
    args = parser.parse_args()

    vault_path = Path(args.vault).expanduser()

    if args.validate:
        errors = validate(vault_path)
        sys.exit(1 if errors > 0 else 0)

    sync(vault_path, check_only=args.check)


if __name__ == "__main__":
    main()
