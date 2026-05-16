r"""
skills_index_merge.py - merge local + plugin + GitHub + mydeepchat skills.

Inputs:
  vault/skills_index.json                  local catalog (~/.claude/skills bare-name scan)
  vault/audits/plugin_skills_raw.jsonl     plugin harvest (plugin_skill_scanner.py output)
  vault/audits/gh_skills_raw.jsonl         GitHub harvest (gh_skill_scanner.py output)
  vault/audits/mydeepchat_skills_raw.jsonl mydeepchat harvest

Output:
  vault/skills_index_unified.json      merged catalog with origin field per entry

Priority on name collision (highest first wins; lower-priority entries logged
to collisions[] for visibility but not used for lookup):
  1. local        — installed under ~/.claude/skills/, source of truth
  2. plugin       — installed Claude plugins (namespaced as <plugin>:<skill>)
  3. github       — harvested from public GitHub
  4. mydeepchat   — harvested from mydeepchat catalog

Plugin skill names are pre-namespaced (e.g. "superpowers:systematic-debugging")
so they almost never collide with bare-name local skills. The 4-source merge
captures the full installed surface that the harness exposes to Claude.

Bug history: pre-2026-04-30 the merger was 3-source (local + gh + mdc) and
silently lost every plugin-installed skill (~76+ namespaced ids visible in
the harness reminder). MC-SA-02 restores them.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCAL_INDEX = REPO_ROOT / "vault" / "skills_index.json"
PLUGIN_RAW = REPO_ROOT / "vault" / "audits" / "plugin_skills_raw.jsonl"
GH_RAW = REPO_ROOT / "vault" / "audits" / "gh_skills_raw.jsonl"
MDC_RAW = REPO_ROOT / "vault" / "audits" / "mydeepchat_skills_raw.jsonl"
UNIFIED_OUT = REPO_ROOT / "vault" / "skills_index_unified.json"


def load_local() -> dict[str, dict]:
    """Read local skills_index.json and flatten to {name: {origin:'local', ...}}."""
    if not LOCAL_INDEX.is_file():
        return {}
    raw = json.loads(LOCAL_INDEX.read_text(encoding="utf-8"))
    flat: dict[str, dict] = {}
    for category, names in (raw.get("categories") or {}).items():
        for n in names:
            if n not in flat:
                flat[n] = {"name": n, "categories": [category]}
            elif category not in flat[n]["categories"]:
                flat[n]["categories"].append(category)
    return flat


def load_plugins() -> list[dict]:
    """Read plugin_skills_raw.jsonl produced by plugin_skill_scanner.py."""
    out: list[dict] = []
    if not PLUGIN_RAW.is_file():
        return out
    with PLUGIN_RAW.open("r", encoding="utf-8") as h:
        for line in h:
            if not line.strip():
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not e.get("name"):
                continue
            out.append(e)
    return out


def load_gh() -> list[dict]:
    """Read gh_skills_raw.jsonl, drop _error/None-named entries."""
    out: list[dict] = []
    if not GH_RAW.is_file():
        return out
    for line in GH_RAW.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "_error" in e or not e.get("name"):
            continue
        out.append(e)
    return out


def load_mydeepchat() -> list[dict]:
    """Read mydeepchat_skills_raw.jsonl. Drop entries without a name."""
    out: list[dict] = []
    if not MDC_RAW.is_file():
        return out
    with MDC_RAW.open("r", encoding="utf-8") as h:
        for line in h:
            if not line.strip():
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not e.get("name"):
                continue
            out.append(e)
    return out


def atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as h:
            json.dump(payload, h, indent=2, sort_keys=False, ensure_ascii=False)
            h.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="skills_index_merge")
    parser.add_argument("--out", default=str(UNIFIED_OUT))
    args = parser.parse_args(argv)

    local = load_local()
    plug = load_plugins()
    gh = load_gh()
    mdc = load_mydeepchat()

    by_name: dict[str, dict] = {}
    collisions: list[dict] = []

    # Priority: local > plugin > github > mydeepchat (local wins on every collision)
    for name, entry in local.items():
        by_name[name] = {"name": name, "origin": "local", "local": entry}

    for e in plug:
        name = e["name"]
        if name in by_name:
            collisions.append({
                "name": name,
                "kept": by_name[name]["origin"],
                "dropped_source": "plugin",
                "dropped_plugin": e.get("plugin"),
                "dropped_version": e.get("plugin_version"),
            })
            continue
        by_name[name] = {
            "name": name,
            "origin": "plugin",
            "plugin": {
                "plugin": e.get("plugin"),
                "skill": e.get("skill"),
                "version": e.get("plugin_version"),
                "marketplace": e.get("marketplace"),
                "description": e.get("description"),
                "skill_path": e.get("skill_path"),
                "scope": e.get("scope"),
            },
        }

    for e in gh:
        name = e["name"]
        if name in by_name:
            collisions.append({"name": name, "kept": by_name[name]["origin"], "dropped_source": "github", "dropped_repo": e["repo"]})
            continue
        by_name[name] = {
            "name": name,
            "origin": "github",
            "github": {
                "repo": e["repo"],
                "path": e["path"],
                "sha": e.get("sha"),
                "raw_url": e["raw_url"],
                "html_url": e.get("html_url"),
            },
        }

    for e in mdc:
        name = e["name"]
        if name in by_name:
            collisions.append({"name": name, "kept": by_name[name]["origin"], "dropped_source": "mydeepchat", "dropped_author": e.get("author")})
            continue
        by_name[name] = {
            "name": name,
            "origin": "mydeepchat",
            "mydeepchat": {
                "id": e.get("id"),
                "slug": e.get("slug"),
                "description": e.get("description"),
                "author": e.get("author"),
                "github_url": e.get("github_url"),
                "has_prompt": bool(e.get("prompt")),
            },
        }

    payload = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "totals": {
            "local": len(local),
            "plugin_harvested": len(plug),
            "gh_harvested": len(gh),
            "mydeepchat_harvested": len(mdc),
            "merged": len(by_name),
            "collisions": len(collisions),
        },
        "by_name": by_name,
        "collisions": collisions,
    }
    atomic_write_json(Path(args.out), payload)

    print(json.dumps(payload["totals"], indent=2))
    print(f"unified -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
