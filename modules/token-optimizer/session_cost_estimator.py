#!/usr/bin/env python3
"""Session Cost Estimator - Estimate token overhead per session based on tier and project config."""

import argparse
import json
import os
import sys
from pathlib import Path


# Base token costs per tier (estimated system prompt + reasoning overhead)
TIER_BASE_COSTS = {
    1: {"name": "Light", "base_tokens": 500, "description": "Simple Q&A, quick edits"},
    2: {"name": "Standard", "base_tokens": 2000, "description": "Feature implementation, debugging"},
    3: {"name": "Deep", "base_tokens": 5000, "description": "Architecture, multi-file refactoring"},
    4: {"name": "Forensic", "base_tokens": 10000, "description": "Complex debugging, system analysis"},
    5: {"name": "Full Context", "base_tokens": 20000, "description": "Complete codebase reasoning"},
}

# Per-source overhead multipliers
OVERHEAD_SOURCES = {
    "claude_md_global": {"label": "Global CLAUDE.md", "multiplier": 1.0},
    "claude_md_project": {"label": "Project CLAUDE.md", "multiplier": 1.0},
    "memory_files": {"label": "Memory files", "multiplier": 0.8},
    "plugins": {"label": "Plugins (per plugin)", "multiplier": 500},
    "mcp_servers": {"label": "MCP servers (per server)", "multiplier": 300},
    "governance": {"label": "Governance docs", "multiplier": 0.5},
}


def count_words(filepath: Path) -> int:
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
        return len(text.split())
    except Exception:
        return 0


def estimate_tokens(words: int) -> int:
    return int(words * 1.33)


def find_memory_files(project_dir: Path) -> list[Path]:
    """Find memory files in project."""
    memory_dirs = [
        project_dir / "memory",
        project_dir / ".claude" / "memory",
    ]
    # Also check user-level project memory
    home = Path.home()
    project_id = project_dir.name
    memory_dirs.append(home / ".claude" / "projects" / project_id / "memory")

    files = []
    for d in memory_dirs:
        if d.exists():
            for f in d.rglob("*.md"):
                files.append(f)
    return files


def load_settings() -> dict:
    settings_path = Path.home() / ".claude" / "settings.json"
    try:
        return json.loads(settings_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def count_governance_docs(project_dir: Path) -> tuple[int, int]:
    """Count governance docs and their total words."""
    gov_dir = project_dir / "governance"
    if not gov_dir.exists():
        return 0, 0
    count = 0
    words = 0
    for f in gov_dir.rglob("*.md"):
        count += 1
        words += count_words(f)
    return count, words


def main():
    parser = argparse.ArgumentParser(description="Session Cost Estimator - Estimate token overhead per session")
    parser.add_argument("--tier", type=int, default=2, choices=[1, 2, 3, 4, 5],
                        help="Execution tier 1-5 (default: 2)")
    parser.add_argument("--project-dir", type=str, default=".",
                        help="Project directory (default: current)")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    home = Path.home()
    tier = TIER_BASE_COSTS[args.tier]

    print("=" * 70)
    print("SESSION COST ESTIMATOR")
    print("=" * 70)
    print(f"Project: {project_dir}")
    print(f"Tier: {args.tier} ({tier['name']}) - {tier['description']}")
    print()

    breakdown: list[tuple[str, int]] = []

    # Base cost
    breakdown.append(("Base tier cost", tier["base_tokens"]))

    # Global CLAUDE.md
    global_claude = home / ".claude" / "CLAUDE.md"
    if global_claude.exists():
        words = count_words(global_claude)
        tokens = estimate_tokens(words)
        breakdown.append((f"Global CLAUDE.md ({words} words)", tokens))
    else:
        breakdown.append(("Global CLAUDE.md (not found)", 0))

    # Project CLAUDE.md
    project_claude = project_dir / "CLAUDE.md"
    if project_claude.exists():
        words = count_words(project_claude)
        tokens = estimate_tokens(words)
        breakdown.append((f"Project CLAUDE.md ({words} words)", tokens))
    else:
        breakdown.append(("Project CLAUDE.md (not found)", 0))

    # Memory files
    memory_files = find_memory_files(project_dir)
    if memory_files:
        total_words = sum(count_words(f) for f in memory_files)
        tokens = int(estimate_tokens(total_words) * 0.8)  # 80% load factor
        breakdown.append((f"Memory files ({len(memory_files)} files, {total_words} words)", tokens))
    else:
        breakdown.append(("Memory files (none)", 0))

    # Settings / plugins
    settings = load_settings()
    plugins = settings.get("enabledPlugins", settings.get("enabled_plugins", []))
    plugin_tokens = len(plugins) * 500
    breakdown.append((f"Plugins ({len(plugins)} enabled)", plugin_tokens))

    # MCP servers
    mcp_config_paths = [
        home / ".claude" / "mcp.json",
        project_dir / ".claude" / "mcp.json",
    ]
    mcp_count = 0
    for mcp_path in mcp_config_paths:
        if mcp_path.exists():
            try:
                mcp_data = json.loads(mcp_path.read_text(encoding="utf-8"))
                servers = mcp_data.get("mcpServers", mcp_data.get("servers", {}))
                mcp_count += len(servers)
            except Exception:
                pass
    mcp_tokens = mcp_count * 300
    breakdown.append((f"MCP servers ({mcp_count} servers)", mcp_tokens))

    # Governance docs
    gov_count, gov_words = count_governance_docs(project_dir)
    if gov_count > 0:
        gov_tokens = int(estimate_tokens(gov_words) * 0.5)  # 50% - not all loaded every session
        breakdown.append((f"Governance docs ({gov_count} files, {gov_words} words)", gov_tokens))
    else:
        breakdown.append(("Governance docs (none)", 0))

    # Planning files
    planning_dir = project_dir / ".planning"
    planning_tokens = 0
    if planning_dir.exists():
        planning_words = 0
        planning_count = 0
        for f in planning_dir.rglob("*.md"):
            planning_count += 1
            planning_words += count_words(f)
        planning_tokens = int(estimate_tokens(planning_words) * 0.3)  # 30% - selectively loaded
        breakdown.append((f"Planning files ({planning_count} files)", planning_tokens))

    # Print breakdown
    print("--- TOKEN BREAKDOWN ---")
    print()
    total = 0
    for label, tokens in breakdown:
        total += tokens
        bar = "#" * min(50, tokens // 200) if tokens > 0 else ""
        print(f"  {tokens:>7,} | {label}")
        if bar:
            print(f"          | {bar}")
    print()
    print("-" * 70)
    print(f"  TOTAL: {total:,} estimated tokens per session start")
    print()

    # Cost estimates (rough, based on public pricing)
    # Claude Opus ~$15/M input, Sonnet ~$3/M input, Haiku ~$0.25/M input
    opus_cost = total / 1_000_000 * 15
    sonnet_cost = total / 1_000_000 * 3
    haiku_cost = total / 1_000_000 * 0.25

    print("--- ESTIMATED OVERHEAD COST (input only, per session) ---")
    print(f"  Opus:   ${opus_cost:.4f}")
    print(f"  Sonnet: ${sonnet_cost:.4f}")
    print(f"  Haiku:  ${haiku_cost:.5f}")
    print()

    # Recommendations
    if total > 15000:
        print("WARNING: High overhead detected. Recommendations:")
        for label, tokens in breakdown:
            if tokens > 3000 and "Base" not in label:
                print(f"  - Reduce {label} (currently {tokens:,} tokens)")
    elif total > 8000:
        print("NOTE: Moderate overhead. Consider trimming largest sources above.")
    else:
        print("OK: Token overhead is within reasonable bounds.")


if __name__ == "__main__":
    main()
