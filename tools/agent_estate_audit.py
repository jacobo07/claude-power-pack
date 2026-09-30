#!/usr/bin/env python3
"""agent_estate_audit -- measure the agent estate a parent session pays for.

Spec: vault/specs/agent-capability-virtualization.md, slice S0.

Claude Code lists every agent file it finds (global ~/.claude/agents plus the
project's .claude/agents) in the parent's Agent tool: name + description + tool
list per agent. Bodies load only at dispatch. So the parent's discovery tax is
the listing, and it grows with the number of RESIDENT agent names.

This tool reports, from the files on disk:
  * every agent per surface (repo agents/, agent-packs/*, global), with sizes;
  * name collisions inside one surface (runtime lists the name once and
    dispatches one body -- measured 2026-09-30: the `<name>.md` file won over
    `<name>.compact.md`; filename-match vs sort order is UNDETERMINED);
  * repo agents that no install surface carries (undispatchable);
  * doctrine duplicated across agent bodies (8-word shingles shared by >= 2
    distinct agents), with a per-agent duplicated-byte share;
  * the resident listing bytes a surface costs the parent.

  python tools/agent_estate_audit.py                 summary to stdout
  python tools/agent_estate_audit.py --write         also write vault/audits/agent_estate/
  python tools/agent_estate_audit.py --roots a b     audit arbitrary agent dirs (tests)

Exit 0 always on a completed audit; 2 when no surface could be read (a failed
look is reported as a failure, never as an empty estate).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GLOBAL_AGENTS = Path.home() / ".claude" / "agents"
SHINGLE = 8

_FM = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n", re.S)


def _field(fm: str, key: str) -> str | None:
    m = re.search(rf"^{key}:\s*(.*?)(?=^[\w-]+:|\Z)", fm, re.S | re.M)
    return m.group(1).strip() if m else None


def parse_agent(path: Path) -> dict | None:
    """One agent file -> record, or None when it declares no name (not an agent)."""
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    m = _FM.match(text)
    if not m:
        return None
    fm, body = m.group(1), text[m.end():]
    name = _field(fm, "name")
    if not name:
        return None
    desc = _field(fm, "description") or ""
    tools = _field(fm, "tools")
    return {
        "name": name,
        "file": str(path),
        "bytes": len(text.encode()),
        "desc_bytes": len(desc.encode()),
        "tools": [t.strip() for t in tools.split(",")] if tools else None,
        "model": _field(fm, "model"),
        "body_bytes": len(body.encode()),
        "sha": hashlib.sha256(text.encode()).hexdigest()[:12],
        "listing_bytes": len(name.encode()) + len(desc.encode()) + len((tools or "*").encode()),
        "_body": body,
    }


def read_surface(root: Path) -> list[dict] | None:
    """All agents under one dir; None when the dir cannot be read at all."""
    if not root.is_dir():
        return None
    out = []
    for p in sorted(root.glob("*.md")):
        rec = parse_agent(p)
        if rec:
            out.append(rec)
    return out


def surfaces() -> dict[str, Path]:
    s = {"repo": ROOT / "agents", "global": GLOBAL_AGENTS}
    packs = ROOT / "agent-packs"
    if packs.is_dir():
        for d in sorted(packs.iterdir()):
            if d.is_dir():
                s[f"pack:{d.name}"] = d
    return s


def collisions(agents: list[dict]) -> dict[str, list[str]]:
    by = defaultdict(list)
    for a in agents:
        by[a["name"]].append(Path(a["file"]).name)
    return {n: f for n, f in by.items() if len(f) > 1}


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def duplication(agents: list[dict]) -> dict:
    """Shingles shared by >= 2 distinct agent NAMES (twins of one name do not count)."""
    owners: dict[tuple, set] = defaultdict(set)
    per: dict[str, set] = {}
    for a in agents:
        w = _words(a["_body"])
        sh = {tuple(w[i:i + SHINGLE]) for i in range(max(0, len(w) - SHINGLE + 1))}
        per.setdefault(a["name"], set()).update(sh)
    for name, sh in per.items():
        for s in sh:
            owners[s].add(name)
    shared = {s for s, o in owners.items() if len(o) > 1}
    share = {n: (round(len(sh & shared) / len(sh), 3) if sh else 0.0) for n, sh in per.items()}
    pairs = defaultdict(int)
    for s in shared:
        o = sorted(owners[s])
        for i in range(len(o)):
            for j in range(i + 1, len(o)):
                pairs[(o[i], o[j])] += 1
    top = sorted(pairs.items(), key=lambda kv: -kv[1])[:10]
    return {"shared_shingles": len(shared),
            "per_agent_shared_share": dict(sorted(share.items(), key=lambda kv: -kv[1])),
            "top_pairs": [{"a": a, "b": b, "shared_shingles": n} for (a, b), n in top]}


def audit(roots: dict[str, Path]) -> dict:
    report: dict = {"surfaces": {}, "unreadable": []}
    loaded: dict[str, list[dict]] = {}
    for label, root in roots.items():
        agents = read_surface(root)
        if agents is None:
            report["unreadable"].append(label)
            continue
        loaded[label] = agents
        unique = {a["name"]: a for a in agents}
        report["surfaces"][label] = {
            "root": str(root),
            "files": len(agents),
            "unique_names": len(unique),
            "total_bytes": sum(a["bytes"] for a in agents),
            # the runtime lists a colliding name once (measured), so residency is per unique name
            "resident_listing_bytes": sum(a["listing_bytes"] for a in unique.values()),
            "collisions": collisions(agents),
            "agents": [{k: v for k, v in a.items() if k != "_body"} for a in agents],
        }
    if "repo" in loaded:
        installed = set()
        for label, agents in loaded.items():
            if label != "repo":
                installed |= {a["name"] for a in agents}
        report["dormant_repo_agents"] = sorted({a["name"] for a in loaded["repo"] if a["name"] not in installed})
    everything = [a for agents in loaded.values() for a in agents]
    # one body per name for duplication: prefer the file the runtime dispatches (<name>.md)
    chosen: dict[str, dict] = {}
    for a in everything:
        cur = chosen.get(a["name"])
        if cur is None or Path(a["file"]).name == f"{a['name']}.md":
            chosen[a["name"]] = a
    report["duplication"] = duplication(list(chosen.values()))
    return report


def render_md(r: dict) -> str:
    lines = ["# Agent estate (generated by tools/agent_estate_audit.py -- do not hand-edit)", ""]
    lines.append("| surface | files | unique names | total bytes | resident listing bytes | collisions |")
    lines.append("|---|---|---|---|---|---|")
    for label, s in r["surfaces"].items():
        lines.append(f"| {label} | {s['files']} | {s['unique_names']} | {s['total_bytes']} | "
                     f"{s['resident_listing_bytes']} | {len(s['collisions'])} |")
    if r["unreadable"]:
        lines += ["", f"UNREADABLE surfaces (not empty -- unknown): {', '.join(r['unreadable'])}"]
    lines += ["", f"Dormant repo agents (no install surface): {', '.join(r.get('dormant_repo_agents', [])) or 'none'}", ""]
    for label, s in r["surfaces"].items():
        lines += [f"## {label}", "", "| name | file | bytes | desc | tools | model |", "|---|---|---|---|---|---|"]
        for a in sorted(s["agents"], key=lambda a: a["name"]):
            tools = ", ".join(a["tools"]) if a["tools"] else "(inherits all)"
            lines.append(f"| {a['name']} | {Path(a['file']).name} | {a['bytes']} | {a['desc_bytes']} | {tools} | {a['model'] or ''} |")
        lines.append("")
    d = r["duplication"]
    lines += ["## Duplicated doctrine", "", f"8-word shingles shared by >= 2 agents: {d['shared_shingles']}", ""]
    for p in d["top_pairs"]:
        lines.append(f"- {p['a']} / {p['b']}: {p['shared_shingles']}")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--roots", nargs="*")
    args = ap.parse_args(argv)
    roots = {f"root{i}": Path(p) for i, p in enumerate(args.roots)} if args.roots else surfaces()
    r = audit(roots)
    if not r["surfaces"]:
        print(f"AGENT_ESTATE=UNREADABLE {r['unreadable']}")
        return 2
    for label, s in r["surfaces"].items():
        print(f"[{label}] files={s['files']} unique={s['unique_names']} bytes={s['total_bytes']} "
              f"resident_listing={s['resident_listing_bytes']} collisions={len(s['collisions'])}")
    if "dormant_repo_agents" in r:
        print(f"dormant_repo_agents={len(r['dormant_repo_agents'])} {r['dormant_repo_agents']}")
    d = r["duplication"]
    print(f"shared_shingles={d['shared_shingles']} top_pair={d['top_pairs'][:1]}")
    if args.write:
        out = ROOT / "vault" / "audits" / "agent_estate"
        out.mkdir(parents=True, exist_ok=True)
        (out / "estate.json").write_text(json.dumps(r, indent=1), encoding="utf-8")
        (out / "INDEX.generated.md").write_text(render_md(r), encoding="utf-8")
        print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
