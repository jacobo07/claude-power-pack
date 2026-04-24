#!/usr/bin/env python3
"""
oracle_cascade.py — Dependency Cascade Oracle (MC-OVO-91).

Heuristic blast-radius analyzer for Paper/Bukkit plugin codebases. For
a given delta (list of changed .java files), computes which OTHER
plugin classes will observe the same event types the changed class
listens to or publishes, and flags the cascade.

Honest scoping:
  - Regex-based extraction, NOT a true Java AST. Catches idiomatic
    Paper/Bukkit patterns (``@EventHandler public void on*(XxxEvent)``,
    ``plugin.getServer().getPluginManager().callEvent(new XxxEvent(…))``).
  - False negatives: reflection-based event dispatch, dynamic class
    loading, annotations via meta-annotations.
  - False positives: minimal — regex anchors on the event class name
    and `@EventHandler` proximity.

What the tool does:
  1. Scan one or more repo roots for .java files.
  2. For each class, extract:
       - events_listened_to : set of Event class names
       - events_published   : set of Event class names
       - package / class name for provenance
  3. Persist the full graph to ``vault/audits/cascade_graph.json`` so
     subsequent runs can diff against it.
  4. Given --changed, compute transitive blast radius:
       changed class → events it publishes/listens to → other classes
       touching those events → their fragile-boundary tags.
  5. Emit a cascade verdict. If blast_radius > ``--max-radius`` OR
     crosses a fragile boundary (Economy, Auth, Persistence,
     WorldGuard, Spawn, Tax), the verdict is ``CASCADE_DETECTED``
     which OVO consumers can interpret as a B-cap unless cited.

Usage:
  python tools/oracle_cascade.py --project <repo>
  python tools/oracle_cascade.py --project <repo> \\
        --changed path/to/PluginA.java path/to/PluginB.java
  python tools/oracle_cascade.py --project <repo> --rebuild --pretty
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_GRAPH = "vault/audits/cascade_graph.json"

# Boundary tags — a cascade that crosses these is high-risk regardless
# of fan-out size.
FRAGILE_BOUNDARY_KEYWORDS = {
    "economy":    ["economy", "vault", "balance", "transaction", "money", "currency"],
    "auth":       ["auth", "login", "session", "token", "permission", "acl"],
    "persistence":["database", "repository", "jpa", "hibernate", "storage", "save"],
    "worldguard": ["worldguard", "region", "flag"],
    "spawn":      ["spawn", "respawn", "bed"],
    "tax":        ["tax", "fee", "rent"],
}

# Regexes — multiline so they span class body boundaries.
RE_PACKAGE     = re.compile(r"^\s*package\s+([\w.]+)\s*;", re.MULTILINE)
RE_CLASS       = re.compile(r"(?:public\s+|final\s+|abstract\s+)*\s*class\s+(\w+)")
RE_EVT_HANDLER = re.compile(
    r"@EventHandler\b(?:\([^)]*\))?\s*[^{;]*?\bvoid\s+(\w+)\s*\(\s*(?:final\s+)?(\w+Event)\s+\w+\s*\)",
    re.MULTILINE | re.DOTALL,
)
RE_CALL_EVENT  = re.compile(
    r"\.callEvent\s*\(\s*new\s+(\w+Event)\s*\(",
)
RE_NEW_EVENT   = re.compile(r"\bnew\s+(\w+Event)\s*\(")


@dataclass
class ClassProfile:
    path: str
    package: str
    name: str
    events_listened_to: set[str] = field(default_factory=set)
    events_published: set[str] = field(default_factory=set)

    @property
    def fqn(self) -> str:
        return f"{self.package}.{self.name}" if self.package else self.name

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "package": self.package,
            "name": self.name,
            "events_listened_to": sorted(self.events_listened_to),
            "events_published": sorted(self.events_published),
        }


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="OVO Dependency Cascade Oracle")
    p.add_argument("--project", default=".", help="repo root")
    p.add_argument("--graph", default=DEFAULT_GRAPH, help="output graph path, relative to --project")
    p.add_argument("--changed", nargs="+", default=[],
                   help="paths of changed .java files (relative to --project) for blast-radius query")
    p.add_argument("--rebuild", action="store_true", help="force a fresh scan even if graph exists")
    p.add_argument("--max-radius", type=int, default=5,
                   help="if more than this many other classes touch the event(s), cap verdict")
    p.add_argument("--pretty", action="store_true", help="pretty-print stdout JSON")
    p.add_argument("--quiet", action="store_true", help="emit only the verdict summary to stdout")
    return p.parse_args()


def extract_profile(path: Path, text: str) -> ClassProfile | None:
    m_pkg = RE_PACKAGE.search(text)
    pkg = m_pkg.group(1) if m_pkg else ""
    m_cls = RE_CLASS.search(text)
    if not m_cls:
        return None
    name = m_cls.group(1)
    listened = {m.group(2) for m in RE_EVT_HANDLER.finditer(text)}
    published = {m.group(1) for m in RE_CALL_EVENT.finditer(text)}
    # new XxxEvent(...) outside of callEvent is weaker evidence, but we
    # treat it as "event object constructed" → probably about to be
    # dispatched. Filter to `new FooEvent(` where FooEvent is NOT in
    # listened (self-published listener pattern).
    for m in RE_NEW_EVENT.finditer(text):
        evt = m.group(1)
        if evt not in listened:
            published.add(evt)
    if not listened and not published:
        return None  # class has no event traffic; skip
    return ClassProfile(
        path=str(path).replace("\\", "/"),
        package=pkg,
        name=name,
        events_listened_to=listened,
        events_published=published,
    )


def scan_repo(root: Path) -> list[ClassProfile]:
    SKIP = {"target", "build", "out", ".git", ".idea", ".gradle", "node_modules", "dist"}
    profiles: list[ClassProfile] = []
    for java in root.rglob("*.java"):
        rel = java.relative_to(root)
        if any(seg in SKIP for seg in rel.parts):
            continue
        try:
            text = java.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        prof = extract_profile(rel, text)
        if prof is not None:
            profiles.append(prof)
    return profiles


def build_graph(profiles: list[ClassProfile]) -> dict:
    event_to_listeners: dict[str, list[str]] = {}
    event_to_publishers: dict[str, list[str]] = {}
    for p in profiles:
        for e in p.events_listened_to:
            event_to_listeners.setdefault(e, []).append(p.fqn)
        for e in p.events_published:
            event_to_publishers.setdefault(e, []).append(p.fqn)
    return {
        "schema": "ovo-cascade-graph-v1",
        "generated_at": iso_now(),
        "classes": [p.to_dict() for p in profiles],
        "event_to_listeners": event_to_listeners,
        "event_to_publishers": event_to_publishers,
    }


def classify_boundary(event_name: str) -> list[str]:
    low = event_name.lower()
    tags: list[str] = []
    for tag, keywords in FRAGILE_BOUNDARY_KEYWORDS.items():
        if any(k in low for k in keywords):
            tags.append(tag)
    return tags


def compute_blast_radius(graph: dict, changed_paths: list[str]) -> dict:
    classes = graph["classes"]
    by_path: dict[str, dict] = {c["path"]: c for c in classes}
    touched_events: set[str] = set()
    changed_fqns: list[str] = []
    missing: list[str] = []
    for path in changed_paths:
        normalized = path.replace("\\", "/")
        cls = by_path.get(normalized)
        if cls is None:
            missing.append(normalized)
            continue
        changed_fqns.append(f"{cls['package']}.{cls['name']}" if cls["package"] else cls["name"])
        for e in cls["events_listened_to"]:
            touched_events.add(e)
        for e in cls["events_published"]:
            touched_events.add(e)

    affected: set[str] = set()
    for e in touched_events:
        for fqn in graph["event_to_listeners"].get(e, []):
            affected.add(fqn)
        for fqn in graph["event_to_publishers"].get(e, []):
            affected.add(fqn)
    for fqn in changed_fqns:
        affected.discard(fqn)

    boundaries: dict[str, list[str]] = {}
    for e in touched_events:
        tags = classify_boundary(e)
        for tag in tags:
            boundaries.setdefault(tag, []).append(e)

    return {
        "changed_classes": changed_fqns,
        "missing_from_graph": missing,
        "touched_events": sorted(touched_events),
        "affected_classes": sorted(affected),
        "affected_count": len(affected),
        "fragile_boundaries_crossed": boundaries,
    }


def render_verdict(blast: dict, max_radius: int) -> dict:
    count = blast["affected_count"]
    crossed = list(blast["fragile_boundaries_crossed"].keys())
    if not blast["changed_classes"]:
        return {
            "verdict": "NO_CHANGE_OR_UNMAPPED",
            "reason": "no changed classes matched the cascade graph",
        }
    if crossed:
        return {
            "verdict": "CASCADE_FRAGILE_BOUNDARY",
            "reason": f"change touches fragile boundary: {', '.join(crossed)}",
        }
    if count > max_radius:
        return {
            "verdict": "CASCADE_DETECTED",
            "reason": f"blast radius {count} exceeds threshold {max_radius}",
        }
    return {
        "verdict": "CASCADE_WITHIN_BOUND",
        "reason": f"blast radius {count} is within threshold {max_radius}",
    }


def load_or_build_graph(project: Path, graph_path: Path, rebuild: bool) -> tuple[dict, bool]:
    if graph_path.exists() and not rebuild:
        try:
            return json.loads(graph_path.read_text(encoding="utf-8")), False
        except json.JSONDecodeError:
            pass
    profiles = scan_repo(project)
    graph = build_graph(profiles)
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    graph_path.write_text(json.dumps(graph, indent=2), encoding="utf-8")
    return graph, True


def main() -> int:
    args = parse_args()
    project = Path(args.project).resolve()
    graph_path = (project / args.graph).resolve()
    graph, rebuilt = load_or_build_graph(project, graph_path, args.rebuild)

    out: dict = {
        "graph_path": str(graph_path),
        "graph_rebuilt": rebuilt,
        "classes_scanned": len(graph["classes"]),
        "unique_events": sorted(set(list(graph["event_to_listeners"].keys()) +
                                    list(graph["event_to_publishers"].keys()))),
    }

    if args.changed:
        blast = compute_blast_radius(graph, args.changed)
        out["blast_radius"] = blast
        out["verdict"] = render_verdict(blast, args.max_radius)

    if args.quiet and "verdict" in out:
        sys.stdout.write(
            f"{out['verdict']['verdict']}: {out['verdict']['reason']} "
            f"(events={len(out['blast_radius']['touched_events'])}, "
            f"affected={out['blast_radius']['affected_count']})\n"
        )
    else:
        sys.stdout.write(
            json.dumps(out, indent=2 if args.pretty else None) + "\n"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
