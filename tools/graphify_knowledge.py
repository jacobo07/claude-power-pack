#!/usr/bin/env python3
"""
graphify_knowledge — GK-03/GK-04 knowledge-node + typed-edge extension for kobi_graphify.

kobi_graphify.py compiles SOURCE CODE (module/class/function nodes, untyped wikilinks).
This companion widens the graph to the full ontology GK-03 names — dataset, hard_rule (UKDL),
trap, decision, contract, scs_seal, test, session, system, doc — and gives edges the TYPE,
EVIDENCE and CONFIDENCE that GK-04 requires (the ~18 typed relations, not one untyped wikilink).

It writes into the SAME `_knowledge_graph/` vault kobi_graphify produces (subtree `knowledge/`)
plus a `_meta/knowledge_nodes.json` cache with per-node freshness hashes — so the two graphers
populate one navigable vault. "Extender kobi_graphify.py, no reimplementar el grafo."

Usage:
    python graphify_knowledge.py build  --project /path/to/repo [--quiet]
    python graphify_knowledge.py query  --project /path/to/repo --type dataset
    python graphify_knowledge.py query  --project /path/to/repo --edge extends
    python graphify_knowledge.py stats  --project /path/to/repo

Pure stdlib, sha256-reproducible, Windows-safe. No third-party deps.
"""

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

# Reuse the parent's proven primitives (same tools/ dir).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from kobi_graphify import VAULT_DIR, META_DIR, safe_filename, file_hash  # type: ignore
except Exception:  # pragma: no cover - fallback keeps the companion standalone
    VAULT_DIR = "_knowledge_graph"
    META_DIR = "_meta"

    def safe_filename(name: str) -> str:
        name = name.replace("/", "--").replace("\\", "--")
        name = re.sub(r'[<>:"|?*]', "", name)
        return name.strip(". ")

    def file_hash(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

KNOWLEDGE_CACHE = "knowledge_nodes.json"
KNOWLEDGE_INDEX = "KNOWLEDGE_INDEX.md"

# GK-03 non-code node types (module/class/function come from kobi_graphify itself).
NODE_TYPES = (
    "dataset", "hard_rule", "trap", "decision", "contract",
    "scs_seal", "test", "session", "system", "doc",
)

# GK-04 typed edge vocabulary. Every edge carries type + evidence + confidence.
EDGE_TYPES = (
    "depends-on", "governed-by", "extends", "produces", "consumes",
    "reuses", "supersedes", "contradicts", "validates", "related-to",
)

# Directories never worth graphing as knowledge (generated / vendored / noise).
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
    ".next", "target", VAULT_DIR, "_audit_cache", "handoffs", "research",
    "test-results", "test-failures", "ceps", "sleepy", "token_logs",
    "telemetry", "monitor", ".pytest_cache", ".mypy_cache",
}
MAX_MD_BYTES = 512 * 1024


@dataclass
class Edge:
    """A GK-04 typed relationship: first-class, evidenced, confidence-graded."""
    type: str            # one of EDGE_TYPES
    target: str          # target node_id (or raw identity when unresolved)
    evidence: str        # file:line or the literal line that proved it
    confidence: str      # observed | inferred


@dataclass
class KNode:
    """A GK-03 knowledge node addressed by a stable coordinate (node_id)."""
    node_id: str
    name: str
    node_type: str
    file_path: str
    summary: str = ""
    edges: list = field(default_factory=list)   # list[Edge]
    anchor: str = ""                              # sha256 of source file (freshness)
    trust: str = "confirmed"                      # confirmed | inferred | stale
    extra: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Typed-edge extraction from markdown conventions
# ---------------------------------------------------------------------------

_RE_PARENT = re.compile(r"[Pp]arents?:\s*\*{0,2}([^\n<|]+)", re.MULTILINE)
_RE_EXTEND = re.compile(r"\bEXTEND(?:S|ING)?\b[:\s]+\*{0,2}([A-Za-z0-9_.\- /+]+)")
_RE_SEAL = re.compile(r"[Ss]ealed under\s+(SCS\s*C?\d+)")
_RE_SUPERSEDE = re.compile(r"\b(?:supersedes|replaces|superseded by)\b[:\s]+([A-Za-z0-9_.\- ]+)", re.IGNORECASE)
_RE_GOVERN = re.compile(r"\bgoverned[- ]by\b[:\s]+([A-Za-z0-9_.\- ]+)", re.IGNORECASE)
_RE_VALIDATE = re.compile(r"\bvalidated[- ]by\b[:\s]+([A-Za-z0-9_.\- ]+)", re.IGNORECASE)
_RE_SYSREF = re.compile(r"\b(CO-\d{2}|PM-\d{2}|GK-\d{2}|HR-[A-Z0-9\-]+|SCS\s*C\d+)\b")


def _clean(token: str) -> str:
    return token.strip().strip("*.`,;").strip()


def extract_edges(text: str, self_id: str) -> list:
    """Extract GK-04 typed edges from PP markdown conventions.

    Observed edges = an explicit declaration line (Parent:/EXTEND/Sealed under).
    Inferred edges = a loose in-prose system reference (CO-0N / PM-0N / GK-0N)."""
    edges: list = []
    seen = set()

    def add(etype: str, raw_target: str, evidence: str, confidence: str):
        for piece in re.split(r"[+,/]| and ", raw_target):
            t = _clean(piece)
            if not t or len(t) > 80:
                continue
            key = (etype, t.lower())
            if key in seen or t.lower() in self_id.lower():
                continue
            seen.add(key)
            edges.append(Edge(type=etype, target=t, evidence=evidence[:160], confidence=confidence))

    for m in _RE_PARENT.finditer(text):
        add("governed-by", m.group(1), _clean(m.group(0)), "observed")
    for m in _RE_EXTEND.finditer(text):
        add("extends", m.group(1), _clean(m.group(0)), "observed")
    for m in _RE_SEAL.finditer(text):
        add("validates", m.group(1).replace(" ", ""), _clean(m.group(0)), "observed")
    for m in _RE_SUPERSEDE.finditer(text):
        add("supersedes", m.group(1), _clean(m.group(0)), "observed")
    for m in _RE_GOVERN.finditer(text):
        add("governed-by", m.group(1), _clean(m.group(0)), "observed")
    for m in _RE_VALIDATE.finditer(text):
        add("validates", m.group(1), _clean(m.group(0)), "observed")

    # Inferred: any in-prose system/rule reference not already an observed edge.
    for m in _RE_SYSREF.finditer(text):
        ref = m.group(1).replace(" ", "")
        add("related-to", ref, "in-prose reference", "inferred")

    return edges


def _summary_of(text: str) -> str:
    """First blockquote line or first heading's following sentence, capped."""
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("> "):
            return s[2:].strip()[:200]
    for line in text.splitlines():
        s = line.strip()
        if s and not s.startswith("#") and not s.startswith("---"):
            return s[:200]
    return ""


# ---------------------------------------------------------------------------
# Knowledge discovery + node construction
# ---------------------------------------------------------------------------

_RE_HR_BLOCK = re.compile(r"^#{1,4}\s+(HR-[A-Z0-9\-]+)[^\n]*", re.MULTILINE)
_RE_TRAP_BLOCK = re.compile(r"^#{1,4}\s+(T-[A-Z0-9\-]+)[^\n]*", re.MULTILINE)
_RE_SCS = re.compile(r"\bSCS\s*(C\d+)\b")


def _rel(p: Path, root: Path) -> str:
    try:
        return str(p.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


def _classify(rel: str) -> str:
    """Map a repo-relative markdown path to a GK-03 node type by PP convention."""
    low = rel.lower()
    base = os.path.basename(low)
    if "hard_rules" in low or base.startswith("hr-") or "ukdl" in low:
        return "hard_rule"
    if "_scs_c" in base or base.startswith("scs") or "seal" in base:
        return "scs_seal"
    if "/lessons/" in "/" + low or "trap" in base or "never_again" in low:
        return "trap"
    if "/decisions/" in "/" + low or "decision" in base:
        return "decision"
    if "contract" in base or "/specs/" in "/" + low:
        return "contract"
    if "/sessions/" in "/" + low or base.startswith("session_"):
        return "session"
    # 'dataset' is reserved for genuine architecture datasets — files that live
    # under a knowledge_base/ or datasets/ tree. A bare `_NN_` in a filename
    # (report_01_, 2026_07_) is NOT a dataset; it falls through to 'doc' so the
    # global layer is not polluted with per-repo report noise (GK-10 over-promotion).
    if "/knowledge_base/" in "/" + low or "/datasets/" in "/" + low:
        return "dataset"
    return "doc"


def _iter_files(root: Path):
    for dpath, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for name in files:
            yield Path(dpath) / name


def build_nodes(project_dir: Path, quiet: bool = False) -> list:
    """Discover knowledge resources in a repo and build GK-03 nodes with GK-04 edges."""
    nodes: list = []
    seen_ids: set = set()

    def log(m):
        if not quiet:
            print(m, file=sys.stderr)

    def push(n: KNode):
        if n.node_id in seen_ids:
            return
        seen_ids.add(n.node_id)
        nodes.append(n)

    for fp in _iter_files(project_dir):
        suffix = fp.suffix.lower()
        rel = _rel(fp, project_dir)

        # --- test nodes (code, but a knowledge type): validates edges by name ---
        if suffix == ".py" and re.match(r"test_", fp.name):
            subject = re.sub(r"^test_|\.py$", "", fp.name)
            nid = f"test/{safe_filename(subject)}"
            push(KNode(nid, fp.stem, "test", rel,
                       summary=f"Test suite for {subject}",
                       anchor=file_hash(fp),
                       edges=[Edge("validates", subject, f"{rel} (name)", "inferred")]))
            continue

        if suffix != ".md":
            continue
        try:
            if fp.stat().st_size > MAX_MD_BYTES or fp.stat().st_size == 0:
                continue
            text = fp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        ntype = _classify(rel)
        anchor = file_hash(fp)

        # Hard-rule / trap blocks: one node per rule/trap inside the file.
        hr_hits = _RE_HR_BLOCK.findall(text)
        trap_hits = _RE_TRAP_BLOCK.findall(text)
        if ntype == "hard_rule" and hr_hits:
            for hr in dict.fromkeys(hr_hits):
                push(KNode(f"hard_rule/{safe_filename(hr)}", hr, "hard_rule", rel,
                           summary=f"Hard Rule {hr}", anchor=anchor,
                           edges=[Edge("governed-by", "UKDL", rel, "observed")]))
        for tr in dict.fromkeys(trap_hits):
            push(KNode(f"trap/{safe_filename(tr)}", tr, "trap", rel,
                       summary=f"Trap {tr}", anchor=anchor))

        # The file itself as a node of its classified type.
        stem = fp.stem
        nid = f"{ntype}/{safe_filename(stem)}"
        edges = extract_edges(text, nid)
        for seal in dict.fromkeys(_RE_SCS.findall(text)):
            edges.append(Edge("validates", seal, f"{rel} SCS ref", "observed"))
        push(KNode(nid, stem, ntype, rel, summary=_summary_of(text),
                   edges=edges, anchor=anchor))

    # System nodes: top-level module dirs become 'system' coordinates.
    modules_dir = project_dir / "modules"
    if modules_dir.is_dir():
        for sub in sorted(modules_dir.iterdir()):
            if sub.is_dir() and sub.name not in SKIP_DIRS and not sub.name.startswith("."):
                push(KNode(f"system/{safe_filename(sub.name)}", sub.name, "system",
                           _rel(sub, project_dir), summary=f"Subsystem: {sub.name}"))

    log(f"[graphify-knowledge] {len(nodes)} knowledge nodes across {len(NODE_TYPES)} types")
    return nodes


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def _edge_to_dict(e) -> dict:
    return asdict(e) if isinstance(e, Edge) else dict(e)


def _node_to_dict(n: KNode) -> dict:
    d = asdict(n)
    d["edges"] = [_edge_to_dict(e) for e in n.edges]
    return d


def write_knowledge(project_dir: Path, nodes: list, quiet: bool = False) -> dict:
    vault = project_dir / VAULT_DIR
    kdir = vault / "knowledge"
    mdir = vault / META_DIR
    for d in (kdir, mdir):
        d.mkdir(parents=True, exist_ok=True)

    # Per-node markdown (navigable) + one JSON cache (queryable).
    for n in nodes:
        node_path = kdir / f"{safe_filename(n.node_id)}.md"
        lines = ["---", f"type: {n.node_type}", f"name: {n.name}",
                 f"file: {n.file_path}", f"trust: {n.trust}", "---", "",
                 f"# {n.name}"]
        if n.summary:
            lines += [f"> {n.summary}", ""]
        if n.edges:
            lines.append("## Edges")
            for e in n.edges:
                ed = _edge_to_dict(e)
                lines.append(f"- **{ed['type']}** -> [[{ed['target']}]] "
                             f"({ed['confidence']}; {ed['evidence']})")
            lines.append("")
        node_path.write_text("\n".join(lines), encoding="utf-8")

    cache = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_dir": str(project_dir),
        "node_types": {t: sum(1 for n in nodes if n.node_type == t) for t in NODE_TYPES},
        "edge_types": {t: sum(1 for n in nodes for e in n.edges
                              if _edge_to_dict(e)["type"] == t) for t in EDGE_TYPES},
        "nodes": [_node_to_dict(n) for n in nodes],
    }
    (mdir / KNOWLEDGE_CACHE).write_text(json.dumps(cache, indent=2), encoding="utf-8")

    # Compact per-type index.
    idx = [f"# Knowledge Graph (GK-03/04): {project_dir.name}",
           f"Nodes: {len(nodes)} | Types: {sum(1 for v in cache['node_types'].values() if v)}", ""]
    for t in NODE_TYPES:
        members = [n for n in nodes if n.node_type == t]
        if members:
            idx.append(f"## {t} ({len(members)})")
            for n in members[:25]:
                idx.append(f"- [[knowledge/{safe_filename(n.node_id)}|{n.name}]] "
                           f"— {len(n.edges)} edges")
            if len(members) > 25:
                idx.append(f"- _...and {len(members) - 25} more_")
            idx.append("")
    (kdir / KNOWLEDGE_INDEX).write_text("\n".join(idx), encoding="utf-8")

    if not quiet:
        print(f"[graphify-knowledge] wrote {len(nodes)} nodes -> {kdir}", file=sys.stderr)
    return cache


def load_cache(project_dir: Path) -> dict:
    path = project_dir / VAULT_DIR / META_DIR / KNOWLEDGE_CACHE
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def query_by_type(project_dir: Path, node_type: str) -> list:
    return [n for n in load_cache(project_dir).get("nodes", []) if n.get("node_type") == node_type]


def query_by_edge(project_dir: Path, edge_type: str) -> list:
    out = []
    for n in load_cache(project_dir).get("nodes", []):
        for e in n.get("edges", []):
            if e.get("type") == edge_type:
                out.append({"from": n["node_id"], "to": e["target"],
                            "confidence": e["confidence"], "evidence": e["evidence"]})
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="GK-03/04 knowledge-node + typed-edge grapher")
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="index a repo's knowledge nodes + typed edges")
    b.add_argument("--project", "-p", required=True)
    b.add_argument("--quiet", "-q", action="store_true")

    q = sub.add_parser("query", help="query the knowledge graph by node type or edge type")
    q.add_argument("--project", "-p", required=True)
    q.add_argument("--type", "-t", default=None)
    q.add_argument("--edge", "-e", default=None)

    s = sub.add_parser("stats", help="show node/edge type counts")
    s.add_argument("--project", "-p", required=True)

    args = ap.parse_args()
    project = Path(args.project).resolve()

    if args.cmd == "build":
        nodes = build_nodes(project, quiet=args.quiet)
        cache = write_knowledge(project, nodes, quiet=args.quiet)
        present = [t for t, c in cache["node_types"].items() if c]
        print(json.dumps({"nodes": len(nodes), "types_present": present,
                          "node_types": cache["node_types"],
                          "edge_types": cache["edge_types"]}, indent=2))
        return 0

    if args.cmd == "query":
        if args.edge:
            res = query_by_edge(project, args.edge)
        elif args.type:
            res = query_by_type(project, args.type)
        else:
            print("give --type or --edge", file=sys.stderr)
            return 2
        print(json.dumps({"count": len(res), "results": res[:50]}, indent=2))
        return 0

    if args.cmd == "stats":
        cache = load_cache(project)
        if not cache:
            print("no knowledge graph — run build first", file=sys.stderr)
            return 1
        print(json.dumps({"node_types": cache.get("node_types"),
                          "edge_types": cache.get("edge_types"),
                          "generated_at": cache.get("generated_at")}, indent=2))
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
