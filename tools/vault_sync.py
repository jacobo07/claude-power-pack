#!/usr/bin/env python3
"""
Vault Sync — Regenerate INDEX.md and update metadata for the governance vault.

Scans ~/.claude/vault/ for all .md files, rebuilds INDEX.md with wikilinks,
and updates _meta/vault_meta.json with file hashes for change detection.

Usage:
    python vault_sync.py                        # sync default vault
    python vault_sync.py --vault ~/.claude/vault/  # explicit path
    python vault_sync.py --check                # check for changes without syncing
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Descriptions for INDEX.md wikilinks (shared with vault_extractor.py)
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


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_text(encoding="utf-8").encode()).hexdigest()[:12]


def generate_index(vault_path: Path) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    parts = [
        "# Governance Vault",
        f"Generated: {now}",
        "",
        "Navigate via [[wikilinks]]. Load only what's relevant — max 5 pages per task.",
        "",
    ]

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


def build_meta(vault_path: Path) -> dict:
    files = {}
    for md_file in sorted(vault_path.rglob("*.md")):
        if md_file.name == "INDEX.md" or md_file.parent.name == "_meta":
            continue
        rel = str(md_file.relative_to(vault_path))
        files[rel] = hash_file(md_file)

    return {
        "version": "1.0",
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "file_count": len(files),
        "files": files,
    }


def check_changes(vault_path: Path) -> list[str]:
    """Check if vault files changed since last sync."""
    meta_path = vault_path / "_meta" / "vault_meta.json"
    if not meta_path.exists():
        return ["no metadata found — full sync needed"]

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    old_files = meta.get("files", {})
    changes = []

    current_files = {}
    for md_file in sorted(vault_path.rglob("*.md")):
        if md_file.name == "INDEX.md" or md_file.parent.name == "_meta":
            continue
        rel = str(md_file.relative_to(vault_path))
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
    parser = argparse.ArgumentParser(description="Vault Sync — regenerate INDEX.md")
    parser.add_argument("--vault", default="~/.claude/vault/", help="Vault directory")
    parser.add_argument("--check", action="store_true", help="Check for changes without syncing")
    args = parser.parse_args()

    vault_path = Path(args.vault).expanduser()
    sync(vault_path, check_only=args.check)


if __name__ == "__main__":
    main()
