#!/usr/bin/env python3
"""Knowledge Vault Indexer (MC-KNB-01)

Scans ~/.claude/knowledge_vault/ and builds a token-cheap JSON index that the
Sleepy Knowledge router uses to retrieve only the relevant fragment for a
given task — instead of loading every .md into the system prompt.

Output: ~/.claude/knowledge_vault/_index/vault_index.json

Index entry per file:
  {
    "path":        relative path under knowledge_vault/
    "category":    top-level dir (core, governance, execution, etc.)
    "title":       first H1 or filename-derived
    "size_bytes":  file size
    "headings":    list of H2/H3 (the addressable subsections)
    "triggers":    keywords from frontmatter + filename + headings,
                   used by the Sleepy router for intent matching
    "summary":     first ~280 chars of body (after frontmatter)
    "mtime":       last modified (RFC3339 UTC)
  }

The index is the ONLY thing the system prompt should ever see. Bodies are
fetched on-demand by sleepy_load(category, file) calls.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

VAULT = Path.home() / ".claude" / "knowledge_vault"
INDEX_DIR = VAULT / "_index"
OUT = INDEX_DIR / "vault_index.json"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
HEADING_RE = re.compile(r"^(#{2,3})\s+(.+)$", re.MULTILINE)
WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_-]{2,}")

# Common stop-words we don't want as triggers
STOP = {
    "the", "and", "for", "with", "this", "that", "from", "into", "your", "have",
    "must", "are", "not", "but", "you", "all", "can", "use", "when", "before",
    "after", "any", "should", "every", "than", "what", "which", "more", "very",
    "off", "set", "get", "see", "via", "per", "ref", "ext", "etc", "via",
}


def extract_triggers(text: str, max_n: int = 25) -> list[str]:
    counts: dict[str, int] = {}
    for w in WORD_RE.findall(text.lower()):
        if w in STOP:
            continue
        counts[w] = counts.get(w, 0) + 1
    return [w for w, _ in sorted(counts.items(), key=lambda x: -x[1])[:max_n]]


def index_file(path: Path) -> dict:
    rel = path.relative_to(VAULT)
    parts = rel.parts
    category = parts[0] if len(parts) > 1 else "_root"
    raw = path.read_text(encoding="utf-8", errors="replace")

    fm_meta = {}
    body = raw
    fm = FRONTMATTER_RE.match(raw)
    if fm:
        body = raw[fm.end():]
        for line in fm.group(1).split("\n"):
            if ":" in line:
                k, _, v = line.partition(":")
                fm_meta[k.strip()] = v.strip().strip("'\"")

    title = fm_meta.get("title") or fm_meta.get("name")
    if not title:
        m = H1_RE.search(body)
        title = m.group(1).strip() if m else path.stem

    headings = [h.strip() for _, h in HEADING_RE.findall(body)][:15]
    summary = re.sub(r"\s+", " ", body.strip())[:280]

    triggers_src = " ".join([title or "", " ".join(headings), fm_meta.get("description", ""), str(rel)])
    triggers = extract_triggers(triggers_src.lower(), 25)

    st = path.stat()
    return {
        "path": str(rel).replace("\\", "/"),
        "category": category,
        "title": title or "",
        "description": fm_meta.get("description", ""),
        "size_bytes": st.st_size,
        "headings": headings,
        "triggers": triggers,
        "summary": summary,
        "mtime": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
    }


def main() -> int:
    if not VAULT.exists():
        print(f"ERROR: {VAULT} does not exist")
        return 1
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    entries: list[dict] = []
    for p in sorted(VAULT.rglob("*.md")):
        # Skip backups and the index itself
        if "_index" in p.parts or ".backups" in p.parts:
            continue
        try:
            entries.append(index_file(p))
        except Exception as e:
            print(f"WARN: failed to index {p}: {e}")

    by_category: dict[str, list[str]] = {}
    by_trigger: dict[str, list[str]] = {}
    for e in entries:
        by_category.setdefault(e["category"], []).append(e["path"])
        for t in e["triggers"]:
            by_trigger.setdefault(t, []).append(e["path"])
    # Cap trigger lists at 8 (avoid bloat for common terms)
    by_trigger = {t: v[:8] for t, v in by_trigger.items() if len(v) >= 1}

    index = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "vault_root": str(VAULT).replace("\\", "/"),
        "totals": {
            "files": len(entries),
            "categories": len(by_category),
            "triggers": len(by_trigger),
            "summary_only_bytes": sum(len(e["summary"]) for e in entries),
            "full_vault_bytes": sum(e["size_bytes"] for e in entries),
        },
        "by_category": {k: sorted(v) for k, v in sorted(by_category.items())},
        "by_trigger": dict(sorted(by_trigger.items())),
        "files": entries,
    }

    OUT.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"WROTE: {OUT}")
    print(f"files indexed:    {len(entries)}")
    print(f"categories:       {len(by_category)}")
    print(f"unique triggers:  {len(by_trigger)}")
    print(f"summary bytes:    {index['totals']['summary_only_bytes']:,} (what router sees)")
    print(f"full vault bytes: {index['totals']['full_vault_bytes']:,} (what was loaded before)")
    ratio = index['totals']['full_vault_bytes'] / max(1, index['totals']['summary_only_bytes'])
    print(f"compression:      {ratio:.1f}x  (router reads ~{ratio:.0f}x less than full-vault load)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
