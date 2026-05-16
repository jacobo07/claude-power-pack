r"""
plugin_skill_scanner.py - harvest namespaced skills from installed Claude plugins.

Discovers the gap caught on 2026-04-30 in MC-SA-02: the merger only looked at
local (~/.claude/skills/), GitHub harvest, and mydeepchat. Plugin-installed
skills (superpowers:*, bmad:*, gsd:*, carl:*, frontend-design:*, etc.) live
under ~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/skills/<skill>/SKILL.md
and were invisible to the unified index.

Topology:
  installed_plugins.json -> per plugin -> [{ installPath, version, scope, ... }]
  installPath/.claude-plugin/plugin.json -> { name, version, ... }
  installPath/skills/<skill_name>/SKILL.md (YAML frontmatter: name, description)

Namespace convention: <plugin_name>:<skill_name> matches what the harness
exposes to Claude in the deferred-skills system reminder list.

Output: vault/audits/plugin_skills_raw.jsonl
        vault/audits/plugin_skills_summary.json

Each jsonl line:
  {
    "name": "superpowers:systematic-debugging",
    "plugin": "superpowers",
    "skill": "systematic-debugging",
    "plugin_version": "5.0.7",
    "marketplace": "claude-plugins-official",
    "description": "Use when encountering...",
    "skill_path": "C:/Users/kobig/.claude/plugins/cache/.../skills/.../SKILL.md",
    "install_path": "C:/Users/kobig/.claude/plugins/cache/...",
    "scope": "user"
  }
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_OUT = REPO_ROOT / "vault" / "audits" / "plugin_skills_raw.jsonl"
SUMMARY_OUT = REPO_ROOT / "vault" / "audits" / "plugin_skills_summary.json"

PLUGINS_HOME = Path(os.path.expanduser("~/.claude/plugins"))
INSTALLED_MANIFEST = PLUGINS_HOME / "installed_plugins.json"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(text: str) -> dict[str, str]:
    """Extract minimal YAML frontmatter — only top-level key: value pairs."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    block = m.group(1)
    out: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t")):
            continue
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def resolve_plugin_root(install_path: str) -> Path | None:
    """installed_plugins.json paths use Windows backslashes; normalise."""
    if not install_path:
        return None
    p = Path(install_path.replace("\\", "/"))
    return p if p.is_dir() else None


def derive_marketplace(plugin_id: str) -> str:
    """plugin_id format is <plugin>@<marketplace>; extract marketplace."""
    if "@" in plugin_id:
        return plugin_id.split("@", 1)[1]
    return "unknown"


def scan_plugin(plugin_id: str, install: dict) -> list[dict]:
    """Walk one plugin's skills/ tree; emit one record per SKILL.md."""
    root = resolve_plugin_root(install.get("installPath", ""))
    if root is None:
        return []
    manifest_path = root / ".claude-plugin" / "plugin.json"
    plugin_name = plugin_id.split("@", 1)[0]
    plugin_version = install.get("version", "unknown")
    if manifest_path.is_file():
        try:
            mf = json.loads(manifest_path.read_text(encoding="utf-8"))
            plugin_name = mf.get("name", plugin_name)
            plugin_version = mf.get("version", plugin_version)
        except (json.JSONDecodeError, OSError):
            pass

    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        return []

    marketplace = derive_marketplace(plugin_id)
    out: list[dict] = []
    for child in sorted(skills_dir.iterdir()):
        if not child.is_dir():
            continue
        skill_md = child / "SKILL.md"
        if not skill_md.is_file():
            continue
        try:
            text = skill_md.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        fm = parse_frontmatter(text)
        skill_name = fm.get("name") or child.name
        out.append({
            "name": f"{plugin_name}:{skill_name}",
            "plugin": plugin_name,
            "skill": skill_name,
            "plugin_version": plugin_version,
            "marketplace": marketplace,
            "description": fm.get("description", ""),
            "skill_path": str(skill_md).replace("\\", "/"),
            "install_path": str(root).replace("\\", "/"),
            "scope": install.get("scope", "user"),
        })
    return out


def atomic_write(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as h:
            h.writelines(lines)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as h:
            json.dump(payload, h, indent=2, ensure_ascii=False)
            h.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="plugin_skill_scanner")
    parser.add_argument("--out", default=str(RAW_OUT))
    parser.add_argument("--summary", default=str(SUMMARY_OUT))
    args = parser.parse_args(argv)

    if not INSTALLED_MANIFEST.is_file():
        print(f"installed_plugins.json not found at {INSTALLED_MANIFEST}", file=sys.stderr)
        return 2

    try:
        manifest = json.loads(INSTALLED_MANIFEST.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"failed to read installed_plugins.json: {e}", file=sys.stderr)
        return 2

    plugins = manifest.get("plugins", {})
    all_records: list[dict] = []
    per_plugin: dict[str, int] = {}
    no_skills: list[str] = []

    for plugin_id, installs in plugins.items():
        if not isinstance(installs, list) or not installs:
            continue
        recs = scan_plugin(plugin_id, installs[0])
        if not recs:
            no_skills.append(plugin_id)
            continue
        per_plugin[plugin_id] = len(recs)
        all_records.extend(recs)

    lines = [json.dumps(r, ensure_ascii=False) + "\n" for r in all_records]
    atomic_write(Path(args.out), lines)

    summary = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "plugins_scanned": len(plugins),
        "plugins_with_skills": len(per_plugin),
        "plugins_without_skills": no_skills,
        "total_skills": len(all_records),
        "per_plugin": per_plugin,
    }
    atomic_write_json(Path(args.summary), summary)

    print(json.dumps({"plugins_scanned": len(plugins), "plugins_with_skills": len(per_plugin), "total_skills": len(all_records)}, indent=2))
    print(f"raw -> {args.out}")
    print(f"summary -> {args.summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
