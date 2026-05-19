#!/usr/bin/env python3
"""inventory_loose.py — Classify loose ~/.claude agents+commands.

Walks the live `~/.claude/agents/` and `~/.claude/commands/` trees and
tags every `.md` entry with one of:

  pp-original        : basename + sha256 match a file in this repo
                       (agents/ or commands/) -> shipped by PP, the
                       installer should diff-copy this on install
  pp-original-drift  : same basename in PP repo, content differs ->
                       requires Owner decision before the installer
                       overwrites (drift is real and must surface)
  3rd-party-plugin   : lives in a known plugin namespace subdir
                       (carl/, bmad/, gsd/, code-review/, superpowers/)
                       OR carries a known-plugin filename prefix
                       (gsd-*, rtk-* in agents/) — plugin author owns
                       it, NOT a PP component
  user-personal      : anything else — host-specific, do NOT redistribute

Output: `tools/_inventory/agents.json` + `tools/_inventory/commands.json`,
schema `{generated, count, items: [{name, path, source, tag, sha256,
pp_match?, drift_detail?}]}`. JSON-validated.

A known-basename alias map handles the one tracked rename in this repo
(`cpp-resume-sovereign.md` ↔ `resume-sovereign.md`), so a rename does
not get mis-tagged as user-personal just because basenames diverge.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
PP_ROOT = HOME / ".claude" / "skills" / "claude-power-pack"
PP_AGENTS = PP_ROOT / "agents"
PP_COMMANDS = PP_ROOT / "commands"
LOOSE_AGENTS = HOME / ".claude" / "agents"
LOOSE_COMMANDS = HOME / ".claude" / "commands"
OUT_DIR = PP_ROOT / "tools" / "_inventory"

# Cross-tree basename aliases (PP repo basename ↔ global basename).
# Sourced from `tools/verify_global_mirrors.py :: PAIRS` where a rename
# is tracked; never invented.
ALIASES = {
    # global basename -> PP-repo basename
    "cpp-resume-sovereign.md": "resume-sovereign.md",
}

# Plugin-namespace markers. A loose path containing one of these as a
# subdir component is owned by that plugin, not PP.
PLUGIN_DIRS = {"carl", "bmad", "gsd", "code-review", "superpowers",
               "claude-api", "bmad-method"}

# Plugin-naming prefixes inside the FLAT loose agents/ dir.
PLUGIN_AGENT_PREFIXES = ("gsd-", "rtk-", "bmad-")


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _path_components(p: Path, root: Path) -> list[str]:
    try:
        rel = p.relative_to(root)
    except ValueError:
        return []
    return list(rel.parts)


def _is_plugin(loose_path: Path, root: Path) -> str | None:
    """Return the plugin marker that owns this file, else None."""
    parts = _path_components(loose_path, root)
    # Subdir-based: any path component is a known plugin dir.
    for c in parts:
        if c in PLUGIN_DIRS:
            return c
    # Flat-dir prefix-based (agents/).
    name = loose_path.name
    for pref in PLUGIN_AGENT_PREFIXES:
        if name.startswith(pref):
            return pref.rstrip("-")
    return None


def classify(loose_path: Path, loose_root: Path, pp_dir: Path) -> dict:
    name = loose_path.name
    sha = _sha256(loose_path)
    item: dict = {
        "name": str(loose_path.relative_to(loose_root)).replace("\\", "/"),
        "path": str(loose_path).replace("\\", "/"),
        "sha256": sha,
    }

    # 1) Plugin check first — subdirs (carl/, bmad/, gsd/) take precedence
    #    over basename matches in case of accidental collision.
    plugin = _is_plugin(loose_path, loose_root)
    if plugin is not None:
        item["source"] = f"plugin:{plugin}"
        item["tag"] = "3rd-party-plugin"
        return item

    # 2) PP-original lookup (with alias for tracked renames).
    pp_basename = ALIASES.get(name, name)
    pp_candidate = pp_dir / pp_basename
    if pp_candidate.is_file():
        pp_sha = _sha256(pp_candidate)
        item["pp_match"] = {"pp_path": str(pp_candidate).replace("\\", "/"),
                            "pp_sha256": pp_sha,
                            "renamed_from": name if pp_basename != name
                                            else None}
        if pp_sha == sha:
            item["source"] = "pp-repo"
            item["tag"] = "pp-original"
        else:
            item["source"] = "pp-repo"
            item["tag"] = "pp-original-drift"
            item["drift_detail"] = ("basename matches PP, content differs; "
                                    "Owner decision required before "
                                    "installer overwrites")
        return item

    # 3) Fallback — host-personal.
    item["source"] = "host"
    item["tag"] = "user-personal"
    return item


def walk_tree(loose_root: Path, pp_dir: Path) -> list[dict]:
    if not loose_root.is_dir():
        return []
    items: list[dict] = []
    for dirpath, _dirnames, filenames in os.walk(loose_root):
        for fn in filenames:
            if not fn.endswith(".md"):
                continue
            p = Path(dirpath) / fn
            items.append(classify(p, loose_root, pp_dir))
    items.sort(key=lambda d: d["name"])
    return items


def _validate_json(payload: dict) -> bool:
    try:
        json.loads(json.dumps(payload))
    except Exception:
        return False
    return True


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    agent_items = walk_tree(LOOSE_AGENTS, PP_AGENTS)
    cmd_items = walk_tree(LOOSE_COMMANDS, PP_COMMANDS)

    agents_payload = {
        "generated": now,
        "count": len(agent_items),
        "loose_root": str(LOOSE_AGENTS).replace("\\", "/"),
        "pp_root": str(PP_AGENTS).replace("\\", "/"),
        "items": agent_items,
    }
    cmds_payload = {
        "generated": now,
        "count": len(cmd_items),
        "loose_root": str(LOOSE_COMMANDS).replace("\\", "/"),
        "pp_root": str(PP_COMMANDS).replace("\\", "/"),
        "items": cmd_items,
    }

    if not (_validate_json(agents_payload) and _validate_json(cmds_payload)):
        print("inventory_loose: JSON validation failed", file=sys.stderr)
        return 2

    (OUT_DIR / "agents.json").write_text(
        json.dumps(agents_payload, indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / "commands.json").write_text(
        json.dumps(cmds_payload, indent=2) + "\n", encoding="utf-8")

    # Summary breakdown to stdout (for the installer + human review).
    def _bucket(items: list[dict]) -> dict:
        b: dict[str, int] = {}
        for it in items:
            b[it["tag"]] = b.get(it["tag"], 0) + 1
        return b

    print(f"=== inventory_loose ({now}) ===")
    print(f"agents.json : {len(agent_items)} entries")
    for tag, n in sorted(_bucket(agent_items).items()):
        print(f"  - {tag}: {n}")
    print(f"commands.json: {len(cmd_items)} entries")
    for tag, n in sorted(_bucket(cmd_items).items()):
        print(f"  - {tag}: {n}")
    print(f"written: {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
