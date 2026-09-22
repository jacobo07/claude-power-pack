"""prose_authority.py -- a representation-neutral declaration channel (W11).

`ownership_evidence.build_structural_index` returns four channels. Two of them
can promote a candidate and both are unreachable for an owner whose authority is
written in prose: `_DECL_RX` carries `.js` and `.ts` only, and a document cannot
be imported. `.md` is scanned, so a prose artifact contributes a bag of words and
a filename, and then stops. That is the mechanism behind `governance-overlay`
holding 13.7 % of its term-pairs structurally against a 21.0 % corpus average,
and it is a property of the extractor rather than of the owner.

The repair is NOT "read Markdown headings". Measured on the estate, 1,061
markdown files carry headings, and a family that credited them would credit every
README. Neither half of the pair below is authority on its own:

    CONSUMER EDGE      something outside the artifact resolves a path to THAT
                       artifact and acts on it
    DECLARATION SURFACE the artifact's structured surface -- headings, governance
                       rule ids, `covers:` keys -- never its prose body

Composed, they are the prose analogue of what a code owner already gets: an
imported module defines symbols; a consumed contract declares headings. The
predicate never asks what the extension is, which is what representation-neutral
has to mean if it is to mean anything.

WHY THIS IS NOT A BACKLINK COUNT. Ranked by raw mentions, the top referrers of
`governance-overlay` are `vault/ucr_cif/oracle_cases.json` at 4,734 -- the W10
ANSWER KEY -- then the disposition ledger at 452, then this signal's own
projection, then this mission's own prose about this owner. A family that counted
references would have scored the owner overwhelmingly from the benchmark that
judges it, and the result would have looked like a triumph. Every edge therefore
carries a provenance class and exactly one of them promotes.

ADMISSION NEUTRALITY. This module is not consulted by `adjudicate`, so no
disposition changes and the ledger and corpus stay frozen. It reaches ranking
only through `structural_projection`, which is behind
`STRUCTURAL_RANKING_ENABLED` and is `False`. Evidence is not promotion.
"""
from __future__ import annotations

import ast
import os
import re
from collections import defaultdict
from pathlib import Path

from . import ownership_evidence as _oe

# --------------------------------------------------------------------------
# Provenance classes. Exactly one promotes.
# --------------------------------------------------------------------------
CONSUMER = "CONSUMER"            # resolves a path to the artifact and acts on it
SOURCE = "SOURCE"                # the artifact itself
PROJECTION = "PROJECTION"        # generated from a source; never counts beside it
CITATION = "CITATION"            # a mention in a message, a docstring, a config
SELF_MEASUREMENT = "SELF_MEASUREMENT"  # this mission's own prose about the owner
BENCHMARK = "BENCHMARK"          # the oracle, the ledger, the wave reports

PROMOTING = (CONSUMER,)

# Directories whose files can ACT. The vault is the estate's record, not its
# runtime: a document there may describe a relation but never performs one.
RUNTIME_DIRS = ("modules", "tools", "hooks", "commands", "agents", "skills",
                "governance", "rules")

# Markdown surfaces the runtime loads and executes as contracts. A `.md` under
# `vault/` is a record; a `.md` under `commands/` is an instruction.
CONTRACT_DIRS = ("commands", "agents", "skills")

# The benchmark and the adjudication this signal must stay independent of.
BENCHMARK_PREFIXES = ("vault/ucr_cif/", "vault/audits/ucr_cif/")
SELF_MEASUREMENT_PREFIXES = ("modules/ucr_cif/", "tools/ucr_cif_",
                             "tools/test_w9_", "tools/test_w10_",
                             "tools/test_w11_",
                             "vault/knowledge_base/ucr_cif/",
                             "vault/specs/ucr-cif-")

PROSE_EXT = (".md", ".json")

# A declaration surface, never a prose body.
_HEADING_RX = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.M)
_RULE_ID_RX = re.compile(r"\b((?:HR|PR|T|CD|MC|BL|GK|SCS)-[A-Z0-9][A-Z0-9-]{2,})\b")
_COVERS_RX = re.compile(r"^covers:\s*\[?([^\]\n]*)\]?", re.M)

# Lifecycle. Historical authority is not current authority.
_DEAD_RX = re.compile(
    r"^\s*(?:status|lifecycle)\s*:\s*(superseded|deprecated|retired|revoked)\b"
    r"|^\s*>?\s*\**(?:SUPERSEDED|DEPRECATED|RETIRED|REVOKED)\**\b",
    re.M | re.I)

_PATH_CALLS = {"Path", "open", "read_text", "read_bytes", "joinpath",
               "load", "loads", "is_file", "exists"}


def _rel(root: Path, path: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def _classify_referrer(rel: str, ext: str, hit_is_actionable: bool) -> str:
    """Provenance of an edge, decided by WHERE it comes from and WHAT it does."""
    for p in BENCHMARK_PREFIXES:
        if rel.startswith(p):
            return BENCHMARK
    for p in SELF_MEASUREMENT_PREFIXES:
        if rel.startswith(p):
            return SELF_MEASUREMENT
    top = rel.split("/", 1)[0]
    if top not in RUNTIME_DIRS:
        return CITATION
    if ext == ".md":
        return CONSUMER if top in CONTRACT_DIRS else CITATION
    if ext in (".py", ".js", ".ts", ".mjs", ".cjs", ".ps1"):
        return CONSUMER if hit_is_actionable else CITATION
    return CITATION


def _python_actionable_strings(blob: str) -> set:
    """String literals a Python file USES to reach a file, docstrings excluded.

    `HERE.parent / "modules" / "governance-overlay" / "mistake-frequency.json"`
    never appears as one literal, so the joined path cannot be matched. What can
    be matched is the set of strings the file actually builds paths out of. A
    path printed inside a message is not in that set, which is the difference
    between consuming a contract and mentioning one.
    """
    out: set = set()
    try:
        tree = ast.parse(blob)
    except (SyntaxError, ValueError):
        return out
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            for side in (node.left, node.right):
                if isinstance(side, ast.Constant) and isinstance(side.value, str):
                    out.add(side.value)
        elif isinstance(node, ast.Call):
            fn = node.func
            name = getattr(fn, "attr", None) or getattr(fn, "id", None)
            if name in _PATH_CALLS:
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        out.add(arg.value)
    return out


def _strip_comments(blob: str, ext: str) -> str:
    if ext in (".js", ".ts", ".mjs", ".cjs"):
        blob = re.sub(r"/\*.*?\*/", " ", blob, flags=re.S)
        return "\n".join(l for l in blob.splitlines()
                         if not l.lstrip().startswith("//"))
    if ext == ".ps1":
        return "\n".join(l for l in blob.splitlines()
                         if not l.lstrip().startswith("#"))
    return blob


def is_declaration_capable(blob: str) -> bool:
    """Lifecycle gate. A superseded contract governs nothing today."""
    return _DEAD_RX.search(blob or "") is None


def declaration_terms(blob: str) -> set:
    """Terms an artifact DECLARES, read from its structured surface only."""
    terms: set = set()
    for head in _HEADING_RX.findall(blob):
        for t in _oe._split_identifier(head):
            terms.add(t)
    for rid in _RULE_ID_RX.findall(blob):
        for t in _oe._split_identifier(rid):
            terms.add(t)
    for group in _COVERS_RX.findall(blob):
        for t in _oe._split_identifier(group):
            terms.add(t)
    return {t for t in terms if len(t) >= 4}


def build_edges(repo=None) -> dict:
    """Every reference to a prose artifact, typed by provenance.

    Returns `artifact_rel -> {class -> sorted[referrer_rel]}`, plus the
    per-artifact owner and whether its lifecycle permits declaring.
    """
    root = Path(repo) if repo is not None else _oe._PP_ROOT

    artifacts: dict = {}
    by_basename: dict = defaultdict(list)
    for d in _oe.SCAN_DIRS:
        base = root / d
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [x for x in dirnames
                           if x not in (".git", "__pycache__", "node_modules")]
            for fn in filenames:
                if not fn.endswith(PROSE_EXT):
                    continue
                path = Path(dirpath) / fn
                rel = _rel(root, path)
                try:
                    blob = path.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                owner = _oe._owner_of(rel)
                artifacts[rel] = {
                    "owner": owner,
                    "owner_dir": owner.split("/")[-1],
                    "basename": fn,
                    "declaration_capable": is_declaration_capable(blob),
                    "declares": sorted(declaration_terms(blob)),
                    "edges": defaultdict(set),
                }
                by_basename[fn].append(rel)

    for d in _oe.SCAN_DIRS:
        base = root / d
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [x for x in dirnames
                           if x not in (".git", "__pycache__", "node_modules")]
            for fn in filenames:
                ext = os.path.splitext(fn)[1]
                if ext not in _oe.ALL_EXT:
                    continue
                path = Path(dirpath) / fn
                rel = _rel(root, path)
                try:
                    blob = path.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                actionable = (_python_actionable_strings(blob)
                              if ext == ".py" else set())
                body = _strip_comments(blob, ext)
                for basename, candidates in by_basename.items():
                    if basename not in blob:
                        continue
                    for target in candidates:
                        if target == rel:
                            continue
                        meta = artifacts[target]
                        # The owner's directory must be named in the same file,
                        # or `core.md` would credit every owner that ships one.
                        if meta["owner_dir"] not in blob:
                            continue
                        if _oe._owner_of(rel) == meta["owner"]:
                            continue  # an owner citing itself proves nothing
                        if ext == ".py":
                            hit = any(basename in s for s in actionable)
                        else:
                            hit = basename in body
                        cls = _classify_referrer(rel, ext, hit)
                        meta["edges"][cls].add(rel)

    return {rel: {**m, "edges": {k: sorted(v) for k, v in m["edges"].items()}}
            for rel, m in artifacts.items()}


def prose_declarations(repo=None, edges=None) -> dict:
    """`term -> {owner}` for declarations that a CONSUMER edge licenses.

    An artifact nobody consumes declares nothing, however many headings it
    carries. A superseded artifact declares nothing, however strongly it reads.
    """
    edges = build_edges(repo) if edges is None else edges
    held: dict = defaultdict(set)
    for rel, meta in edges.items():
        if not meta["declaration_capable"]:
            continue
        if not any(meta["edges"].get(c) for c in PROMOTING):
            continue
        for term in meta["declares"]:
            held[term].add(meta["owner"])
    return {t: sorted(o) for t, o in held.items()}


def coverage(repo=None, edges=None) -> dict:
    """Denominators beside the numerators, so a share can be argued with."""
    edges = build_edges(repo) if edges is None else edges
    per_class = defaultdict(int)
    consumed = 0
    superseded_blocked = 0
    declaring = 0
    for meta in edges.values():
        for cls, refs in meta["edges"].items():
            per_class[cls] += len(refs)
        has_consumer = bool(any(meta["edges"].get(c) for c in PROMOTING))
        if has_consumer:
            consumed += 1
            if not meta["declaration_capable"]:
                superseded_blocked += 1
            elif meta["declares"]:
                declaring += 1
    return {
        "artifacts": len(edges),
        "artifacts_with_consumer_edge": consumed,
        "artifacts_declaring": declaring,
        "artifacts_blocked_by_lifecycle": superseded_blocked,
        "edges_by_class": {k: per_class[k] for k in sorted(per_class)},
    }
