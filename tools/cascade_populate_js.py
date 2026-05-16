#!/usr/bin/env python3
"""cascade_populate_js.py — JavaScript cascade populator (MC-OVO-107).

Walks .js / .mjs / .cjs files in a project, parses each via esprima
(pure-Python AST), and emits ovo-cascade-graph-v2 nodes + edges.

Per the v11500 Reality Shield: regex shortcuts for structural logic
are PROHIBITED. Anything we can't resolve through the AST gets
recorded as ANALYSIS_STALEMATE — never silently dropped, never
synthesized.

Usage:
  python tools/cascade_populate_js.py --project .             # stdout
  python tools/cascade_populate_js.py --project . --write     # merge into vault/audits/cascade_graph.json
  python tools/cascade_populate_js.py --project . --json      # JSON to stdout

Exit codes: 0 ok (even with stalemates), 2 argv error, 3 io error.

Schema: vault/forensic/CASCADE_POPULATOR_SCHEMA.md
Consumer: vault/forensic/CGAR_SCHEMA.md → forensic_probes.cgar_check
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

try:
    import esprima
except ImportError:
    print("cascade_populate_js.py: esprima not installed. "
          "Run: python -m pip install --user esprima", file=sys.stderr)
    sys.exit(3)

POPULATOR_TAG = "cascade_populate_js"
GRAPH_PATH = "vault/audits/cascade_graph.json"
JS_EXTS = (".js", ".mjs", ".cjs")
SKIP_DIRS = {
    "node_modules", ".git", "dist", "build", "out", ".next",
    "coverage", "_audit_cache", "snapshots", ".venv", "venv",
}
TRANSITIVE_HOPS = 2


# ---------------------------------------------------------------------------
# AST walking
# ---------------------------------------------------------------------------

def _walk_files(project: Path) -> list[Path]:
    out: list[Path] = []
    for p in project.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix not in JS_EXTS:
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        out.append(p)
    return out


def _node_iter(node):
    """Yield every dict-like AST node depth-first."""
    if isinstance(node, list):
        for item in node:
            yield from _node_iter(item)
        return
    if not hasattr(node, "type"):
        return
    yield node
    # Walk all attributes that look like child nodes.
    for attr in dir(node):
        if attr.startswith("_") or attr == "type" or attr == "loc" or attr == "range":
            continue
        try:
            child = getattr(node, attr)
        except Exception:
            continue
        if hasattr(child, "type") or isinstance(child, list):
            yield from _node_iter(child)


def _resolve_local_path(from_file: Path, raw: str, project: Path) -> str | None:
    """Resolve a relative require/import string to a project-relative path.

    Returns the rel path string (with forward slashes) if the target file
    exists under the project. Returns None for non-relative imports
    (npm packages, absolute paths) or unresolvable targets.
    """
    if not raw or not (raw.startswith("./") or raw.startswith("../")):
        return None
    base = from_file.parent
    target = (base / raw).resolve()
    # Try as-is, then with each extension, then with /index.<ext>.
    candidates = [target]
    if target.suffix == "":
        for ext in JS_EXTS:
            candidates.append(target.with_suffix(ext))
        for ext in JS_EXTS:
            candidates.append(target / f"index{ext}")
    for c in candidates:
        try:
            if c.is_file():
                rel = c.resolve().relative_to(project.resolve())
                return str(rel).replace("\\", "/")
        except (ValueError, OSError):
            continue
    return None


def _extract_from_ast(tree, file_rel: str, file_abs: Path, project: Path):
    """Extract requires, imports, defs, calls. Returns (edges, defs)."""
    edges: list[dict] = []
    defs: list[dict] = []
    for n in _node_iter(tree):
        t = n.type

        # CommonJS require()
        if t == "CallExpression":
            callee = n.callee
            if callee and callee.type == "Identifier" and callee.name == "require":
                if n.arguments and n.arguments[0].type == "Literal":
                    raw = n.arguments[0].value
                    resolved = _resolve_local_path(file_abs, raw, project) if isinstance(raw, str) else None
                    edges.append({
                        "from": file_rel,
                        "to": resolved or f"<external:{raw}>",
                        "type": "consumed_by",
                        "_populator": POPULATOR_TAG,
                        **({"unresolved": True, "reason": f"non-local require({raw!r})"}
                           if resolved is None else {}),
                    })
            elif callee and callee.type == "Identifier":
                # Generic call: attribute as invocation evidence (function-level
                # blast radius will be aggregated at module level for v1).
                # We don't emit per-call edges to keep the graph readable.
                pass

        # ES6 import
        elif t == "ImportDeclaration":
            raw = n.source.value if n.source and n.source.type == "Literal" else None
            resolved = _resolve_local_path(file_abs, raw, project) if isinstance(raw, str) else None
            edges.append({
                "from": file_rel,
                "to": resolved or f"<external:{raw}>",
                "type": "consumed_by",
                "_populator": POPULATOR_TAG,
                **({"unresolved": True, "reason": f"non-local import({raw!r})"}
                   if resolved is None else {}),
            })

        # Function / class definitions (just collect names; per-function
        # nodes would explode the graph for large files — keep at module
        # granularity for v1 and surface the count via metadata).
        elif t in ("FunctionDeclaration", "ClassDeclaration"):
            if n.id and n.id.name:
                defs.append({"name": n.id.name, "kind": t})

    return edges, defs


# ---------------------------------------------------------------------------
# Populator core
# ---------------------------------------------------------------------------

def populate(project: Path) -> dict:
    project = project.resolve()
    files = _walk_files(project)

    nodes: dict[str, dict] = {}
    all_edges: list[dict] = []
    stalemates: list[dict] = []

    for fp in files:
        rel = str(fp.relative_to(project)).replace("\\", "/")
        try:
            src = fp.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as exc:
            stalemates.append({
                "file": rel, "reason": f"read failed: {exc}",
                "_populator": POPULATOR_TAG,
            })
            continue
        # esprima rejects shebang lines (`#!/usr/bin/env node`) — strip
        # the first line if it's a shebang. Otherwise every CLI tool in
        # the project would stalemate, defeating the populator.
        if src.startswith("#!"):
            nl = src.find("\n")
            src = src[nl + 1:] if nl != -1 else ""
        # Try ESM first (handles import statements). Fallback to script mode.
        tree = None
        last_err = None
        for parse_fn in (esprima.parseModule, esprima.parseScript):
            try:
                tree = parse_fn(src, {"tolerant": False})
                break
            except Exception as exc:
                last_err = exc
        if tree is None:
            stalemates.append({
                "file": rel,
                "reason": f"esprima parse error: {type(last_err).__name__}: {last_err}",
                "_populator": POPULATOR_TAG,
            })
            continue
        edges, defs = _extract_from_ast(tree, rel, fp, project)
        nodes[rel] = {
            "id": rel,
            "kind": "module",
            "definitions": defs,
            "_populator": POPULATOR_TAG,
        }
        all_edges.extend(edges)

    # Compute blast radius from edges.
    inbound: dict[str, list[str]] = {n: [] for n in nodes}
    for e in all_edges:
        if e["to"] in inbound:
            inbound[e["to"]].append(e["from"])
    for nid, node in nodes.items():
        direct = list(set(inbound[nid]))
        # Transitive: BFS up to TRANSITIVE_HOPS.
        seen = set(direct)
        frontier = list(direct)
        for _hop in range(TRANSITIVE_HOPS - 1):
            next_frontier = []
            for caller in frontier:
                for c2 in inbound.get(caller, []):
                    if c2 not in seen:
                        seen.add(c2)
                        next_frontier.append(c2)
            frontier = next_frontier
        node["blast_radius"] = {
            "direct_callers": len(direct),
            "transitive_callers": len(seen),
            "downstream_systems": [],
        }

    return {
        "schema": "ovo-cascade-graph-v2",
        "generated_at": _dt.datetime.now(_dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project": project.name,
        "nodes": list(nodes.values()),
        "edges": all_edges,
        "_stalemates": stalemates,
    }


# ---------------------------------------------------------------------------
# Merge into existing graph (preserve v1 legacy + other populators' nodes)
# ---------------------------------------------------------------------------

def merge_write(project: Path, fresh: dict) -> None:
    out = project / GRAPH_PATH
    existing: dict = {}
    if out.exists():
        try:
            existing = json.loads(out.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}

    legacy = existing.get("_legacy_v1", {
        "classes": [], "event_to_listeners": {}, "event_to_publishers": {}
    })

    # Filter out nodes/edges/stalemates owned by THIS populator from existing,
    # then add the fresh ones. This way other populators (TS, Py, Java) can
    # write to the same graph without stomping each other.
    keep_nodes = [n for n in existing.get("nodes", [])
                  if n.get("_populator") != POPULATOR_TAG]
    keep_edges = [e for e in existing.get("edges", [])
                  if e.get("_populator") != POPULATOR_TAG]
    keep_stale = [s for s in existing.get("_stalemates", [])
                  if s.get("_populator") != POPULATOR_TAG]

    merged = {
        "schema": "ovo-cascade-graph-v2",
        "generated_at": fresh["generated_at"],
        "project": fresh["project"],
        "nodes": keep_nodes + fresh["nodes"],
        "edges": keep_edges + fresh["edges"],
        "_stalemates": keep_stale + fresh["_stalemates"],
        "_legacy_v1": legacy,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def render_human(graph: dict) -> str:
    lines = [
        f"Cascade Populator (JS) — {graph['project']}",
        f"Generated: {graph['generated_at']}",
        f"Nodes:      {len(graph['nodes'])}",
        f"Edges:      {len(graph['edges'])}",
        f"Stalemates: {len(graph['_stalemates'])}",
    ]
    if graph["nodes"]:
        lines.append("")
        lines.append("Top by blast_radius (transitive_callers):")
        ranked = sorted(graph["nodes"],
                        key=lambda n: -(n.get("blast_radius") or {}).get("transitive_callers", 0))
        for n in ranked[:10]:
            br = n.get("blast_radius", {})
            lines.append(f"  {n['id']}: direct={br.get('direct_callers',0)} "
                         f"transitive={br.get('transitive_callers',0)} "
                         f"defs={len(n.get('definitions', []))}")
    if graph["_stalemates"]:
        lines.append("")
        lines.append("ANALYSIS_STALEMATE entries:")
        for s in graph["_stalemates"][:5]:
            lines.append(f"  {s['file']}: {s['reason'][:120]}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="JavaScript cascade populator (esprima AST)"
    )
    parser.add_argument("--project", type=Path, default=Path("."),
                        help="Project root (default: cwd)")
    parser.add_argument("--write", action="store_true",
                        help="Merge result into vault/audits/cascade_graph.json")
    parser.add_argument("--json", action="store_true",
                        help="Emit JSON instead of human text")
    args = parser.parse_args(argv[1:])

    project = args.project.resolve()
    if not project.exists() or not project.is_dir():
        print(f"cascade_populate_js.py: project not a directory: {project}",
              file=sys.stderr)
        return 2

    graph = populate(project)
    if args.write:
        try:
            merge_write(project, graph)
        except OSError as exc:
            print(f"cascade_populate_js.py: write failed: {exc}", file=sys.stderr)
            return 3
        print(f"[cascade_populate_js] merged into {GRAPH_PATH} "
              f"(nodes={len(graph['nodes'])}, edges={len(graph['edges'])}, "
              f"stalemates={len(graph['_stalemates'])})")
    elif args.json:
        print(json.dumps(graph, indent=2, ensure_ascii=False))
    else:
        print(render_human(graph))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
