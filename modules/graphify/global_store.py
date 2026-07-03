#!/usr/bin/env python3
"""
GK-10 — Global Cross-Repo Knowledge Store.

One knowledge store that serves every repo. kobi_graphify + graphify_knowledge
(GK-03/04) produce a repo's local nodes; this layer keeps them CENTRAL (under
~/.claude/state/graphify/) so:
  - external repos are never polluted with generated _knowledge_graph/ dirs;
  - already-open sessions in any repo can query the graph by reading one file,
    no restart required (the data is on disk, GK-00);
  - cross-repo-valuable knowledge (UKDL, decisions, contracts, datasets, seals,
    traps) is PROMOTED to a global layer so learning in one repo reaches all
    (the reuse dividend, GK-10).

Storage (same on-disk-JSON pattern as findings_bus / repo_brain):
  ~/.claude/state/graphify/graphify_global.json   — repo registry + promoted global nodes
  ~/.claude/state/graphify/repos/<repo_id>.json   — full per-repo knowledge cache

Merge protocol (GK-10 / GK-02): promoted nodes dedup by canonical node_id and
UNION their origins with provenance — never a directional overwrite (HR-006).
Fail-open: a write failure under ~/.claude/state degrades to a returned error
dict; it never raises into a caller (a store that blocks work is worse than a
stale store).
"""

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Reach tools/ for the GK-03/04 grapher, regardless of CWD.
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "tools"))
import graphify_knowledge as gk  # noqa: E402

SCHEMA_VERSION = 1

# GK-10 promotion set: node types whose value is transportable across repos.
PROMOTABLE = {"hard_rule", "scs_seal", "decision", "contract", "dataset", "trap"}


def state_dir() -> Path:
    # GRAPHIFY_STATE_DIR redirects the whole store (tests set it to a tmp dir so
    # they never touch the real ~/.claude/state — hermetic, no global writes).
    override = os.environ.get("GRAPHIFY_STATE_DIR")
    if override:
        return Path(override)
    return Path(os.path.expanduser("~")) / ".claude" / "state" / "graphify"


def _global_file() -> Path:
    return state_dir() / "graphify_global.json"


def _repos_dir() -> Path:
    return state_dir() / "repos"


def repo_id(repo_path) -> str:
    """Stable, filesystem-safe id for a repo path (case-normalised)."""
    norm = str(Path(repo_path).resolve()).replace("\\", "/").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", Path(norm).name).strip("-") or "repo"
    digest = hashlib.sha256(norm.encode("utf-8")).hexdigest()[:10]
    return f"{slug}-{digest}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dirs() -> bool:
    try:
        _repos_dir().mkdir(parents=True, exist_ok=True)
        return True
    except OSError:
        return False


def load_global() -> dict:
    path = _global_file()
    if not path.exists():
        return {"schema_version": SCHEMA_VERSION, "updated_at": None,
                "repos": {}, "global_nodes": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"schema_version": SCHEMA_VERSION, "updated_at": None,
                "repos": {}, "global_nodes": {}}


def _save_global(data: dict) -> dict:
    data["updated_at"] = _now()
    try:
        _global_file().write_text(json.dumps(data, indent=2), encoding="utf-8")
        return {"ok": True}
    except OSError as e:
        return {"ok": False, "error": f"global store write denied: {e}"}


def _save_repo_cache(rid: str, payload: dict) -> bool:
    try:
        (_repos_dir() / f"{rid}.json").write_text(
            json.dumps(payload, separators=(",", ":")), encoding="utf-8")
        return True
    except OSError:
        return False


def load_repo_cache(rid: str) -> dict:
    path = _repos_dir() / f"{rid}.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _promote(glob_nodes: dict, node: dict, rid: str, repo_path: str) -> None:
    """Merge a promotable node into the global layer by canonical id, unioning
    origins with provenance (GK-10 union-with-provenance — never clobber)."""
    nid = node["node_id"]
    entry = glob_nodes.get(nid)
    origin = {"repo_id": rid, "repo_path": repo_path, "file": node.get("file_path", "")}
    if entry is None:
        glob_nodes[nid] = {
            "node_id": nid, "name": node.get("name", ""),
            "node_type": node.get("node_type", ""),
            "summary": node.get("summary", ""),
            "edges": node.get("edges", []),
            "trust": "confirmed" if node.get("node_type") in ("hard_rule", "scs_seal") else "inferred",
            "origins": [origin],
        }
    else:
        # Union origins; preserve a differing summary as a provenance note
        # rather than overwriting (contradictions are preserved, GK-10).
        if origin not in entry["origins"]:
            entry["origins"].append(origin)
        new_sum = node.get("summary", "")
        if new_sum and new_sum != entry.get("summary", ""):
            entry.setdefault("alt_summaries", [])
            if new_sum not in entry["alt_summaries"]:
                entry["alt_summaries"].append(new_sum)


# A governance identity token — the mark of a genuinely cross-repo artifact.
_GOV_ID = re.compile(r"\b(CO-\d|PM-\d|GK-\d|HR-[A-Z0-9]|BL-\d|SCS ?C\d|T-[A-Z])", re.IGNORECASE)


def _is_promotable(nd: dict) -> bool:
    """GK-10 signal gate: promote a node to the global layer only when it is a
    genuine cross-repo asset. hard_rule / scs_seal qualify by definition; the
    other promotable types must carry a governance-ID token OR at least one
    OBSERVED typed edge (a real, declared relationship) — never a bare file that
    merely matched a promotable type. Prevents global-layer pollution."""
    ntype = nd.get("node_type")
    if ntype not in PROMOTABLE:
        return False
    if ntype in ("hard_rule", "scs_seal"):
        return True
    blob = f"{nd.get('node_id', '')} {nd.get('name', '')} {nd.get('summary', '')}"
    if _GOV_ID.search(blob):
        return True
    return any(e.get("confidence") == "observed" for e in nd.get("edges", []))


def index_repo(repo_path, quiet: bool = True) -> dict:
    """Index one repo's knowledge nodes into the central store and promote the
    transportable ones to the global layer. Runs with NO Claude Code active in
    the target repo — it is a pure filesystem pass. Returns a stats dict."""
    rp = Path(repo_path)
    if not rp.is_dir():
        return {"ok": False, "repo": str(repo_path), "error": "path not found"}

    if not _ensure_dirs():
        return {"ok": False, "repo": str(repo_path), "error": "cannot create state dir"}

    rid = repo_id(rp)
    knodes = gk.build_nodes(rp, quiet=quiet)
    node_dicts = [gk._node_to_dict(n) for n in knodes]

    type_counts: dict = {t: 0 for t in gk.NODE_TYPES}
    for nd in node_dicts:
        type_counts[nd["node_type"]] = type_counts.get(nd["node_type"], 0) + 1

    _save_repo_cache(rid, {
        "repo_id": rid, "repo_path": str(rp.resolve()),
        "indexed_at": _now(), "node_types": type_counts, "nodes": node_dicts,
    })

    data = load_global()
    glob_nodes = data.setdefault("global_nodes", {})
    promoted = 0
    for nd in node_dicts:
        if _is_promotable(nd):
            _promote(glob_nodes, nd, rid, str(rp.resolve()))
            promoted += 1

    data.setdefault("repos", {})[rid] = {
        "path": str(rp.resolve()), "indexed_at": _now(),
        "node_count": len(node_dicts), "node_types": type_counts,
    }
    save_res = _save_global(data)

    return {"ok": save_res.get("ok", False), "repo": str(rp.resolve()),
            "repo_id": rid, "nodes": len(node_dicts), "promoted": promoted,
            "types_present": [t for t, c in type_counts.items() if c],
            "error": save_res.get("error")}


def index_all(repo_paths, quiet: bool = True) -> list:
    return [index_repo(p, quiet=quiet) for p in repo_paths]


def query_global(node_type: str = None, edge_type: str = None,
                 name: str = None, cross_repo_only: bool = False) -> list:
    """Query the promoted global layer, plus per-repo caches unless
    cross_repo_only. Returns matching node records with their origin repos."""
    data = load_global()
    results: list = []

    for nid, entry in data.get("global_nodes", {}).items():
        if node_type and entry.get("node_type") != node_type:
            continue
        if name and name.lower() not in (entry.get("name", "").lower() + " " + nid.lower()):
            continue
        if edge_type and not any(e.get("type") == edge_type for e in entry.get("edges", [])):
            continue
        results.append({"scope": "global", "node_id": nid,
                        "node_type": entry.get("node_type"),
                        "name": entry.get("name"),
                        "origins": [o["repo_id"] for o in entry.get("origins", [])],
                        "summary": entry.get("summary", "")})

    if not cross_repo_only:
        for rid in data.get("repos", {}):
            cache = load_repo_cache(rid)
            for nd in cache.get("nodes", []):
                if node_type and nd.get("node_type") != node_type:
                    continue
                if name and name.lower() not in (nd.get("name", "").lower() + " " + nd.get("node_id", "").lower()):
                    continue
                if edge_type and not any(e.get("type") == edge_type for e in nd.get("edges", [])):
                    continue
                results.append({"scope": rid, "node_id": nd.get("node_id"),
                                "node_type": nd.get("node_type"),
                                "name": nd.get("name"), "origins": [rid],
                                "summary": nd.get("summary", "")})
    return results


def summary() -> dict:
    data = load_global()
    return {
        "repos": {rid: r.get("node_count", 0) for rid, r in data.get("repos", {}).items()},
        "global_nodes": len(data.get("global_nodes", {})),
        "updated_at": data.get("updated_at"),
        "store_path": str(_global_file()),
    }
