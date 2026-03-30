#!/usr/bin/env python3
"""
Claude Power Pack — Cross-Repo Dispatcher (Part O)

Dispatches claude CLI to a target repository with a prompt file.
Finds repos by name, cds into them, and runs claude -p with the prompt
so the target project's CLAUDE.md context is loaded automatically.

Usage:
    claude-dispatch <repo-name> <prompt-file>
    claude-dispatch --rebuild-index
    claude-dispatch --list
    claude-dispatch <repo-name> <prompt-file> --repo-path /exact/path
    claude-dispatch <repo-name> <prompt-file> --dry-run
"""

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = MODULE_DIR / "config.json"
REPO_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")
MAX_PROMPT_SIZE = 1_048_576  # 1 MB

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [dispatcher] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

DEFAULTS = {
    "search_dirs": ["~/projects", "~/repos", "~/code", "~/dev", "~/Desktop"],
    "search_depth": 3,
    "index_path": "~/.claude/dispatcher/repo-index.json",
    "claude_args": [],
    "match_strategy": "basename",
}

# Windows-specific extra search dirs
WINDOWS_EXTRA_DIRS = ["~/source/repos", "~/Documents"]


def load_config() -> dict:
    """Load config.json from module directory, merged with defaults."""
    config = dict(DEFAULTS)
    if CONFIG_PATH.exists():
        try:
            user_config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            config.update(user_config)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load config.json, using defaults: %s", exc)

    if sys.platform == "win32":
        for d in WINDOWS_EXTRA_DIRS:
            if d not in config["search_dirs"]:
                config["search_dirs"].append(d)

    return config


def expand_path(p: str) -> Path:
    """Expand ~ and resolve a path string."""
    return Path(os.path.expanduser(p)).resolve()


def load_index(index_path: Path) -> dict:
    """Read the JSON repo index. Returns {name: [absolute_paths]}."""
    if not index_path.exists():
        return {}
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Index corrupted, will rebuild: %s", exc)
        try:
            index_path.unlink()
        except OSError:
            pass
    return {}


def save_index(index_path: Path, index: dict) -> None:
    """Write the JSON index atomically (write to tmp, then rename)."""
    index_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=str(index_path.parent), suffix=".tmp"
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
        # On Windows, target must not exist for rename
        if index_path.exists():
            index_path.unlink()
        Path(tmp_path).rename(index_path)
    except OSError:
        # Fallback: direct write
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        index_path.write_text(
            json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8"
        )


def scan_directories(search_dirs: list, max_depth: int) -> dict:
    """Scan directories for git repos up to max_depth. Returns {name: [paths]}."""
    index = {}

    def _scan(directory: Path, depth: int):
        if depth > max_depth:
            return
        try:
            with os.scandir(directory) as entries:
                has_git = False
                subdirs = []
                for entry in entries:
                    if entry.name == ".git" and entry.is_dir(follow_symlinks=False):
                        has_git = True
                    elif entry.is_dir(follow_symlinks=False) and not entry.name.startswith("."):
                        subdirs.append(entry.path)

                if has_git:
                    name = directory.name
                    abs_path = str(directory)
                    if name not in index:
                        index[name] = []
                    if abs_path not in index[name]:
                        index[name].append(abs_path)

                for subdir in subdirs:
                    _scan(Path(subdir), depth + 1)
        except (PermissionError, OSError):
            pass

    for search_dir in search_dirs:
        expanded = expand_path(search_dir)
        if expanded.is_dir():
            logger.info("Scanning %s ...", expanded)
            _scan(expanded, 1)
        else:
            logger.debug("Skipping non-existent dir: %s", search_dir)

    return index


def resolve_repo(name: str, config: dict) -> Path:
    """Look up repo by name. Falls back to live scan if not in index."""
    index_path = expand_path(config["index_path"])
    index = load_index(index_path)

    if name in index:
        paths = index[name]
        # Verify at least one path still has .git
        valid = [p for p in paths if (Path(p) / ".git").is_dir()]
        if len(valid) == 1:
            return Path(valid[0])
        if len(valid) > 1:
            print(f"\nMultiple repos match '{name}':", file=sys.stderr)
            for p in valid:
                print(f"  - {p}", file=sys.stderr)
            print(
                f"\nRe-run with --repo-path <exact-path> to disambiguate.",
                file=sys.stderr,
            )
            sys.exit(2)
        # All cached paths invalid — remove stale entry, trigger rescan
        del index[name]
        save_index(index_path, index)

    # Live scan
    logger.info("Repo '%s' not in index, scanning directories...", name)
    fresh = scan_directories(config["search_dirs"], config["search_depth"])
    # Merge fresh into index
    for k, v in fresh.items():
        index[k] = v
    save_index(index_path, index)

    if name not in index or not index[name]:
        dirs_str = ", ".join(config["search_dirs"])
        print(
            f"Repo '{name}' not found. Searched: {dirs_str}\n"
            f"Run with --rebuild-index to refresh, or use --repo-path.",
            file=sys.stderr,
        )
        sys.exit(1)

    paths = index[name]
    if len(paths) == 1:
        return Path(paths[0])

    print(f"\nMultiple repos match '{name}':", file=sys.stderr)
    for p in paths:
        print(f"  - {p}", file=sys.stderr)
    print(
        f"\nRe-run with --repo-path <exact-path> to disambiguate.",
        file=sys.stderr,
    )
    sys.exit(2)


def validate_repo_name(name: str) -> str:
    """Validate repo name against allowed pattern."""
    name = name.strip()
    if not name:
        print("Error: repo name cannot be empty.", file=sys.stderr)
        sys.exit(4)
    if not REPO_NAME_PATTERN.match(name):
        print(
            f"Error: invalid repo name '{name}'. "
            f"Only alphanumeric, dots, hyphens, and underscores allowed.",
            file=sys.stderr,
        )
        sys.exit(4)
    return name


def validate_prompt_file(path_str: str) -> Path:
    """Validate prompt file exists, is readable, and not too large."""
    prompt_path = Path(path_str).resolve()
    if not prompt_path.is_file():
        print(f"Prompt file not found: {prompt_path}", file=sys.stderr)
        sys.exit(4)
    size = prompt_path.stat().st_size
    if size > MAX_PROMPT_SIZE:
        print(
            f"Prompt file too large ({size} bytes, max {MAX_PROMPT_SIZE}).",
            file=sys.stderr,
        )
        sys.exit(4)
    # Check for binary content
    sample = prompt_path.read_bytes()[:8192]
    if b"\x00" in sample:
        print("Prompt file appears to be binary. Only text files accepted.", file=sys.stderr)
        sys.exit(4)
    return prompt_path


def dispatch(repo_path: Path, prompt_file: Path, extra_args: list, dry_run: bool = False) -> int:
    """Read prompt file and invoke claude -p in the target repo directory."""
    claude_bin = shutil.which("claude")
    if not claude_bin:
        print(
            "Error: 'claude' CLI not found in PATH.\n"
            "Install from: https://docs.anthropic.com/en/docs/claude-code",
            file=sys.stderr,
        )
        sys.exit(3)

    prompt_content = prompt_file.read_text(encoding="utf-8").strip()
    if not prompt_content:
        logger.warning("Prompt file is empty, proceeding anyway.")

    cmd = [claude_bin, "-p", prompt_content] + extra_args

    if dry_run:
        print(f"[DRY RUN] Would execute in: {repo_path}")
        print(f"[DRY RUN] Command: claude -p \"<prompt from {prompt_file.name}>\" {' '.join(extra_args)}".rstrip())
        print(f"[DRY RUN] Prompt content ({len(prompt_content)} chars):")
        preview = prompt_content[:200]
        if len(prompt_content) > 200:
            preview += "..."
        print(f"  {preview}")
        return 0

    logger.info("Dispatching to: %s", repo_path)
    logger.info("Prompt file: %s (%d chars)", prompt_file.name, len(prompt_content))

    result = subprocess.run(cmd, cwd=str(repo_path))
    return result.returncode


def cmd_rebuild_index(config: dict) -> None:
    """Force rebuild the repo index."""
    index_path = expand_path(config["index_path"])
    logger.info("Rebuilding repo index...")
    index = scan_directories(config["search_dirs"], config["search_depth"])
    save_index(index_path, index)
    total_repos = sum(len(v) for v in index.values())
    print(f"Index rebuilt: {len(index)} unique names, {total_repos} total paths.")
    print(f"Saved to: {index_path}")


def cmd_list_repos(config: dict) -> None:
    """List all indexed repositories."""
    index_path = expand_path(config["index_path"])
    index = load_index(index_path)
    if not index:
        print("No repos indexed. Run with --rebuild-index first.")
        return
    print(f"Indexed repositories ({len(index)} names):\n")
    for name in sorted(index.keys()):
        paths = index[name]
        if len(paths) == 1:
            print(f"  {name:40s} {paths[0]}")
        else:
            print(f"  {name:40s} ({len(paths)} locations)")
            for p in paths:
                print(f"    {'':40s} {p}")


def main():
    parser = argparse.ArgumentParser(
        prog="claude-dispatch",
        description="Dispatch claude CLI to any repository with a prompt file.",
    )
    parser.add_argument("repo_name", nargs="?", help="Name of the target repository")
    parser.add_argument("prompt_file", nargs="?", help="Path to the prompt file")
    parser.add_argument("--rebuild-index", action="store_true", help="Force rebuild the repo index")
    parser.add_argument("--list", action="store_true", dest="list_repos", help="List all indexed repos")
    parser.add_argument("--repo-path", type=str, help="Use exact path instead of searching")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be executed")
    parser.add_argument("--config", type=str, help="Path to alternative config file")

    args = parser.parse_args()
    config = load_config()

    if args.config:
        alt_config_path = Path(args.config).resolve()
        if alt_config_path.exists():
            try:
                user_config = json.loads(alt_config_path.read_text(encoding="utf-8"))
                config.update(user_config)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Failed to load alt config: %s", exc)

    if args.rebuild_index:
        cmd_rebuild_index(config)
        return

    if args.list_repos:
        cmd_list_repos(config)
        return

    if not args.repo_name or not args.prompt_file:
        parser.print_help()
        sys.exit(1)

    repo_name = validate_repo_name(args.repo_name)
    prompt_file = validate_prompt_file(args.prompt_file)

    if args.repo_path:
        repo_path = Path(args.repo_path).resolve()
        if not repo_path.is_dir():
            print(f"Error: --repo-path '{repo_path}' is not a directory.", file=sys.stderr)
            sys.exit(1)
    else:
        repo_path = resolve_repo(repo_name, config)

    exit_code = dispatch(repo_path, prompt_file, config.get("claude_args", []), args.dry_run)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
