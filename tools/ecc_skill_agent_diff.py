#!/usr/bin/env python3
"""ecc_skill_agent_diff.py -- selective-absorption diff for ECC skills + agents.

ECC ships 261 skills + 64 agents. PP / the environment already has its own
(~88 skills in ~/.claude/skills, ~39 agents in ~/.claude/agents, + PP's bundled
agents). Cloning all 325 ECC items would be redundant and violates adapt-not-copy.

This computes the NET-NEW set: ECC items whose normalized name has no equivalent
already present. Name normalization strips a leading `pp-`/`ecc-`, lowercases,
and removes non-alphanumerics so `code-reviewer` == `pp-code-reviewer`. The
output is a review list (net-new candidates with their descriptions) + the
overlap list (skipped, with the reason "already present").

  python tools/ecc_skill_agent_diff.py --ecc <ECC root> [--json out.json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HOME = Path.home()
PP_ROOT = Path(__file__).resolve().parents[1]


def _norm(name: str) -> str:
    n = name.strip().lower()
    n = re.sub(r"^(pp|ecc)[-_]", "", n)
    return re.sub(r"[^a-z0-9]", "", n)


def _frontmatter(text: str) -> dict:
    """Minimal YAML-frontmatter parse: name + first-line description."""
    out: dict = {}
    if not text.startswith("---"):
        return out
    end = text.find("\n---", 3)
    block = text[3:end] if end != -1 else ""
    for key in ("name", "description"):
        m = re.search(rf"^{key}:\s*(.+)$", block, re.MULTILINE)
        if m:
            out[key] = m.group(1).strip().strip('"\'')
    return out


def _existing_names() -> set[str]:
    names: set[str] = set()
    # global skills: dir name + frontmatter name
    sk = HOME / ".claude" / "skills"
    if sk.is_dir():
        for d in sk.iterdir():
            if d.is_dir():
                names.add(_norm(d.name))
                f = d / "SKILL.md"
                if f.is_file():
                    fm = _frontmatter(f.read_text(encoding="utf-8", errors="replace"))
                    if fm.get("name"):
                        names.add(_norm(fm["name"]))
    # global agents + PP bundled agents
    for adir in (HOME / ".claude" / "agents", PP_ROOT / "agents"):
        if adir.is_dir():
            for f in adir.glob("*.md"):
                names.add(_norm(f.stem))
                fm = _frontmatter(f.read_text(encoding="utf-8", errors="replace"))
                if fm.get("name"):
                    names.add(_norm(fm["name"]))
    names.discard("")
    return names


def _ecc_items(ecc_root: Path) -> tuple[list[dict], list[dict]]:
    skills, agents = [], []
    for f in sorted((ecc_root / "skills").rglob("SKILL.md")):
        fm = _frontmatter(f.read_text(encoding="utf-8", errors="replace"))
        name = fm.get("name") or f.parent.name
        skills.append({"name": name, "desc": (fm.get("description") or "")[:140]})
    for f in sorted((ecc_root / "agents").glob("*.md")):
        fm = _frontmatter(f.read_text(encoding="utf-8", errors="replace"))
        name = fm.get("name") or f.stem
        agents.append({"name": name, "desc": (fm.get("description") or "")[:140]})
    return skills, agents


def diff(ecc_root: Path) -> dict:
    existing = _existing_names()
    skills, agents = _ecc_items(ecc_root)

    def split(items):
        new, overlap = [], []
        for it in items:
            (overlap if _norm(it["name"]) in existing else new).append(it)
        return new, overlap

    sk_new, sk_ov = split(skills)
    ag_new, ag_ov = split(agents)
    return {
        "existing_count": len(existing),
        "skills": {"total": len(skills), "new": sk_new, "overlap": sk_ov},
        "agents": {"total": len(agents), "new": ag_new, "overlap": ag_ov},
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--ecc", required=True)
    ap.add_argument("--json", default=None)
    args = ap.parse_args(argv)

    ecc_root = Path(args.ecc)
    if not ecc_root.is_dir():
        print(f"[ERROR] not a dir: {ecc_root}")
        return 1

    r = diff(ecc_root)
    if args.json:
        Path(args.json).write_text(json.dumps(r, indent=2), encoding="utf-8")

    print(f"existing names indexed: {r['existing_count']}")
    print(f"SKILLS: {r['skills']['total']} total -> "
          f"{len(r['skills']['new'])} NET-NEW, {len(r['skills']['overlap'])} overlap")
    print(f"AGENTS: {r['agents']['total']} total -> "
          f"{len(r['agents']['new'])} NET-NEW, {len(r['agents']['overlap'])} overlap")
    print("\n--- NET-NEW AGENTS ---")
    for a in r["agents"]["new"]:
        print(f"  [A] {a['name']}: {a['desc']}")
    print("\n--- NET-NEW SKILLS ---")
    for s in r["skills"]["new"]:
        print(f"  [S] {s['name']}: {s['desc']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
