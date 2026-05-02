#!/usr/bin/env python
"""Skill semantic heat-map indexer (BL-0016 / MC-SYS-27).

Scans ~/.claude/skills/**/SKILL.md and ~/.claude/plugins/**/skills/**/SKILL.md,
extracts YAML frontmatter (name, description), tokenizes description into
keywords, emits compact JSON to vault/skills_heat_map.json.

Purpose: PreToolUse hooks can read the heat-map (single small JSON) instead of
re-globbing the skills tree on every tool call. Future hooks can rank-inject
skill suggestions as additionalContext via cosine-similarity-on-keywords or
TF-IDF without ever invoking an embedding model.

Output schema (vault/skills_heat_map.json):
  {
    "generated_iso": "...",
    "total": int,
    "schema_version": 1,
    "skills": {
      "<skill-id>": {
        "description": str,
        "keywords": [str, ...],   // deduped, lowercased, length>=3, stop-words removed
        "file_path": str,
        "size_bytes": int,
        "mtime": float
      }
    }
  }

CLI:
  python tools/skill_heat_map_indexer.py            # scan + write + summary
  python tools/skill_heat_map_indexer.py --dry-run  # scan + summary only, no write
  python tools/skill_heat_map_indexer.py --query "<word>"  # rank-search and print top 10
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path.home() / ".claude"
SKILL_GLOBS = [
    ROOT / "skills",
    ROOT / "plugins",
]
OUT_PATH = ROOT / "skills" / "claude-power-pack" / "vault" / "skills_heat_map.json"
ATOMIC_WRITE_DIR = ROOT / "skills" / "claude-power-pack" / "lib"

STOP_WORDS = {
    "the", "and", "for", "use", "this", "that", "with", "your", "you",
    "are", "from", "have", "any", "all", "can", "into", "about", "when",
    "what", "which", "will", "should", "must", "also", "etc", "such",
    "based", "using", "via", "per", "but", "not", "out", "see", "may",
    "skill", "tool", "tools", "agent", "agents", "claude",
}
KEYWORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_-]{2,}")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _parse_frontmatter(text: str) -> dict[str, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fm = m.group(1)
    out: dict[str, str] = {}
    current_key: str | None = None
    for line in fm.split("\n"):
        if not line.strip():
            continue
        if line[:1] in (" ", "\t") and current_key:
            out[current_key] = (out.get(current_key, "") + " " + line.strip()).strip()
            continue
        if ":" in line:
            k, _, v = line.partition(":")
            current_key = k.strip()
            out[current_key] = v.strip().strip('"').strip("'")
    return out


def _keywords(description: str) -> list[str]:
    hits = KEYWORD_RE.findall(description.lower())
    seen: dict[str, int] = {}
    for w in hits:
        if w in STOP_WORDS or len(w) < 3:
            continue
        seen[w] = seen.get(w, 0) + 1
    return [w for w, _ in sorted(seen.items(), key=lambda kv: (-kv[1], kv[0]))]


def _skill_id_for(path: Path) -> str:
    parts = path.parts
    if "plugins" in parts:
        i = parts.index("plugins")
        if len(parts) >= i + 4 and parts[i + 2] == "skills":
            return f"{parts[i + 1]}:{parts[i + 3]}"
        if len(parts) >= i + 3:
            return f"{parts[i + 1]}:{parts[i + 2]}"
    if "skills" in parts:
        i = parts.index("skills")
        if len(parts) >= i + 2:
            return parts[i + 1]
    return path.parent.name


def discover() -> list[Path]:
    found: list[Path] = []
    for root in SKILL_GLOBS:
        if not root.exists():
            continue
        for p in root.rglob("SKILL.md"):
            try:
                if p.is_file():
                    found.append(p)
            except OSError:
                continue
    return found


def build_index(paths: list[Path]) -> dict:
    skills: dict[str, dict] = {}
    for p in paths:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        fm = _parse_frontmatter(text)
        if not fm:
            continue
        sid = fm.get("name") or _skill_id_for(p)
        sid = _skill_id_for(p) if "/" in sid or "\\" in sid else sid
        description = fm.get("description") or ""
        try:
            stat = p.stat()
            size = stat.st_size
            mtime = stat.st_mtime
        except OSError:
            size = 0
            mtime = 0.0
        skills[sid] = {
            "description": description,
            "keywords": _keywords(description),
            "file_path": str(p),
            "size_bytes": size,
            "mtime": mtime,
        }
    return {
        "generated_iso": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "total": len(skills),
        "schema_version": 1,
        "skills": skills,
    }


def write_index(index: dict, out_path: Path) -> None:
    sys.path.insert(0, str(ATOMIC_WRITE_DIR))
    try:
        import atomic_write  # type: ignore
        atomic_write.atomic_write_json(out_path, index, indent=2)
    finally:
        try:
            sys.path.remove(str(ATOMIC_WRITE_DIR))
        except ValueError:
            pass


def query(index: dict, term: str, limit: int = 10) -> list[tuple[str, int]]:
    term = term.lower().strip()
    if not term:
        return []
    scored: list[tuple[str, int]] = []
    for sid, entry in index["skills"].items():
        kws = entry["keywords"]
        score = 0
        for w in term.split():
            if w in kws:
                score += 5
            elif any(w in k or k in w for k in kws):
                score += 1
            if w in entry["description"].lower():
                score += 2
        if score:
            scored.append((sid, score))
    scored.sort(key=lambda kv: (-kv[1], kv[0]))
    return scored[:limit]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--query", type=str, default=None)
    ap.add_argument("--out", type=str, default=str(OUT_PATH))
    args = ap.parse_args()

    paths = discover()
    index = build_index(paths)

    if args.query is not None:
        hits = query(index, args.query)
        print(f"Query: {args.query!r} — top {len(hits)} of {index['total']} skills")
        for sid, score in hits:
            print(f"  [{score:>3}] {sid}")
        return 0

    out_path = Path(args.out)
    if not args.dry_run:
        write_index(index, out_path)

    avg_kw = (sum(len(s["keywords"]) for s in index["skills"].values()) / max(index["total"], 1))
    print(f"skill heat-map: {index['total']} skills indexed, avg {avg_kw:.1f} keywords/skill")
    print(f"  output: {out_path}{' (dry-run)' if args.dry_run else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
