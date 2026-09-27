#!/usr/bin/env python3
"""Startup-prefix inventory: what instruction text every session in a cwd loads.

The observed side (tools/tis_observed.py) measures how big the startup prefix
is -- median ~169k tokens on this repo, re-read on every call. This module
measures what it is made of, from the files on disk, so a relocation proposal
can name the bytes it would move.

APERTURE -- stated because silence here is not evidence:
  counted   CLAUDE.md chain (global + every ancestor of cwd, deduped), rules
            (~/.claude/rules and <cwd>/.claude/rules; `paths:`-scoped files
            reported apart), this project's auto-memory MEMORY.md, and the
            name+description of user-level skills, agents and commands.
  NOT       the harness system prompt, tool schemas (incl. MCP), plugin
            skills/agents (which of them are enabled is not resolved here),
            hook-injected context. The residual against an observed
            first-call context is theirs, not "unexplained waste".
Tokens are an ESTIMATE (bytes / 3.8); no tokenizer is available offline.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

HOME_CLAUDE = Path.home() / ".claude"
BYTES_PER_TOKEN_EST = 3.8
# Projects whose names a rule's text can carry; a tag is a MENTION, not ownership.
KNOWN_PROJECTS = ("Orca X", "CommonWealth", "TUA-X", "CavEX", "KobiiCraft",
                  "KobiiSports", "Jacobo", "Power Pack", "GEX44", "ABSW2")


def _est(nbytes: int) -> int:
    return round(nbytes / BYTES_PER_TOKEN_EST)


def frontmatter(text: str) -> dict:
    """Minimal YAML-frontmatter reader: top-level `key: value` pairs, with a
    folded continuation for indented lines. Enough for name/description/paths."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    out: dict = {}
    key = None
    for line in text[3:end].splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            key = m.group(1)
            out[key] = m.group(2).strip()
        elif key and line.startswith((" ", "\t")):
            out[key] = (out[key] + " " + line.strip()).strip()
    return out


def claude_md_chain(cwd: Path, home_claude: Path = HOME_CLAUDE,
                    stop_at: Optional[Path] = None) -> list[Path]:
    """Global CLAUDE.md plus every ancestor's, up to the filesystem root as the
    harness does. `stop_at` bounds the walk for hermetic tests only: an
    unbounded walk from a temp dir found the real ~/CLAUDE.md (2026-09-27)."""
    dirs = [cwd, *cwd.parents]
    if stop_at is not None:
        dirs = [d for d in dirs if d == stop_at or stop_at in d.parents]
    seen, out = set(), []
    for p in [home_claude / "CLAUDE.md"] + [d / "CLAUDE.md" for d in dirs]:
        try:
            rp = p.resolve()
        except OSError:
            continue
        if p.is_file() and rp not in seen:
            seen.add(rp)
            out.append(p)
    return out


def _mentions(text: str) -> dict:
    return {n: text.count(n) for n in KNOWN_PROJECTS if n in text}


def inventory(cwd: Path, home_claude: Path = HOME_CLAUDE,
              memory_file: Optional[Path] = None,
              stop_at: Optional[Path] = None) -> dict:
    rows = []

    def add(kind, path, nbytes, **extra):
        rows.append(dict(kind=kind, path=str(path), bytes=nbytes,
                         tokens_est=_est(nbytes), **extra))

    for p in claude_md_chain(cwd, home_claude, stop_at):
        add("claude_md", p, p.stat().st_size)
    for root in (home_claude / "rules", cwd / ".claude" / "rules"):
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*.md")):
            text = p.read_text(encoding="utf-8-sig", errors="replace")
            scoped = bool(frontmatter(text).get("paths"))
            add("rule_scoped" if scoped else "rule", p, len(text.encode("utf-8")),
                mentions=_mentions(text))
    if memory_file is not None and memory_file.is_file():
        add("memory_index", memory_file, memory_file.stat().st_size)
    for kind, pattern, root in (("skill_listing", "*/SKILL.md", home_claude / "skills"),
                                ("agent_listing", "*.md", home_claude / "agents"),
                                ("command_listing", "*.md", home_claude / "commands")):
        if not root.is_dir():
            continue
        for p in sorted(root.glob(pattern)):
            fm = frontmatter(p.read_text(encoding="utf-8-sig", errors="replace"))
            listed = (fm.get("name") or p.stem) + " " + fm.get("description", "")
            add(kind, p, len(listed.encode("utf-8")))

    by_kind: dict = {}
    for r in rows:
        k = by_kind.setdefault(r["kind"], {"files": 0, "bytes": 0})
        k["files"] += 1
        k["bytes"] += r["bytes"]
    for k in by_kind.values():
        k["tokens_est"] = _est(k["bytes"])
    unconditional = sum(v["bytes"] for k, v in by_kind.items() if k != "rule_scoped")
    return {"cwd": str(cwd), "source": "files", "tokens": "ESTIMATE bytes/3.8",
            "by_kind": by_kind,
            "unconditional_bytes": unconditional,
            "unconditional_tokens_est": _est(unconditional),
            "not_counted": ["harness system prompt", "tool schemas incl. MCP",
                            "plugin skills/agents", "hook-injected context"],
            "rows": rows}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cwd", default=".")
    ap.add_argument("--top", type=int, default=15, help="largest rows to print")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    cwd = Path(args.cwd).resolve()
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
    import tis_observed  # single owner of the transcript-dir key
    mem = HOME_CLAUDE / "projects" / tis_observed.project_key(cwd) / "memory" / "MEMORY.md"
    inv = inventory(cwd, memory_file=mem)
    if args.json:
        print(json.dumps(inv, indent=2))
        return 0
    print(f"startup prefix inventory for {cwd} (tokens = ESTIMATE bytes/3.8)")
    for kind, v in sorted(inv["by_kind"].items(), key=lambda kv: -kv[1]["bytes"]):
        print(f"  {kind:16s} files={v['files']:4d}  bytes={v['bytes']:9d}  ~tok={v['tokens_est']:7d}")
    print(f"  UNCONDITIONAL    ~tok={inv['unconditional_tokens_est']}  "
          f"(not counted: {', '.join(inv['not_counted'])})")
    print(f"largest {args.top}:")
    for r in sorted(inv["rows"], key=lambda r: -r["bytes"])[:args.top]:
        m = r.get("mentions")
        print(f"  {r['tokens_est']:7d}  {r['kind']:14s} {Path(r['path']).name}"
              + (f"  mentions={m}" if m else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
