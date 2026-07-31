#!/usr/bin/env python3
"""model.py -- OSR-1: a typed model of an EXTERNAL, observed system.

Why this exists. The estate can type cognitive work (DAIF-01), locate its own
knowledge (graphify, 1,190 coordinates), model its own ensemble (cpp_ias) and
acquire external documents (crawl_os). Nothing types a third-party RUNNING
product: its surfaces, states, transitions, contracts, invariants, failure modes
and recovery paths, together with what is known about each and how well.

Three boundaries, each a prohibition rather than a preference
(vault/audits/usirc/BOUNDARY_CONTRACT.md):

1. NO SECOND GRAPH. graphify owns the semantic IR unconditionally. This module
   emits node/edge TYPES for the existing indexer via `graphify_types()`; it
   never stands up a store that competes with it. Its own JSON file is a
   per-target working set, not an index of the estate.
2. NO SECOND EPISTEMIC LADDER. ACIS owns the status of a claim. This module
   carries the status as a FIELD and enforces exactly one invariant locally --
   No-Autopromotion: a status may not rise without new evidence. The canonical
   ladder and its semantics live in vault/knowledge_base/acis/.
3. NO EVIDENCE ACQUISITION. crawl_os owns acquisition, provenance and custody.
   A node cites Evidence Object ids; it never stores an evidence body.

The unit that makes this worth having is the TRANSITION. A screenshot inventory
is a mockup; a transition (prior state, action, posterior state, evidence) is
what turns an observation into a claim a comparison can later falsify.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

# ---------------------------------------------------------------- ontology

NODE_KINDS: frozenset[str] = frozenset({
    "product", "capability", "surface", "actor", "state", "transition",
    "action", "event", "contract", "invariant", "resource", "runtime",
    "component", "dependency", "failure_mode", "recovery_path",
    "hypothesis", "opportunity",
})

EDGE_KINDS: frozenset[str] = frozenset({
    "contains", "exposes", "requires", "produces", "consumes", "triggers",
    "transitions_to", "persists", "authorizes", "renders", "depends_on",
    "recovers_through", "inferred_from", "contradicted_by",
    "intentionally_differs_from",
})

# ACIS-aligned status names. The RANK exists solely to evaluate the
# No-Autopromotion invariant; it is not a competing ladder, and this module
# never publishes a level, a score or a percentage derived from it.
STATUS_RANK: dict[str, int] = {
    "unknown": 0,
    "hypothesized": 1,
    "derived": 2,
    "observed": 3,
    "measured": 4,
    "verified": 5,
}

# A status at or above this rank asserts contact with reality and therefore
# requires at least one evidence reference. "required" is deliberately absent
# from the rank table: it is a target property, not a claim about the original,
# and conflating the two is the defect CLAE Part IV names as direction loss.
_EVIDENCE_REQUIRED_AT = STATUS_RANK["observed"]

STATUSES: frozenset[str] = frozenset(STATUS_RANK) | {"required"}


class ModelError(ValueError):
    """Raised when an operation would put the model in an invalid state."""


class ObservedSystemModel:
    """A typed, validated model of one observed external system.

    Nodes and edges only. No scoring, no verdicts, no fidelity numbers --
    DAIF-03 owns every one of those.
    """

    def __init__(self, target: str, version: str = "unpinned") -> None:
        if not target or not target.strip():
            raise ModelError("target must be a non-empty identifier")
        self.target = target.strip()
        self.version = version
        self._nodes: dict[str, dict[str, Any]] = {}
        self._edges: list[dict[str, Any]] = []

    # ------------------------------------------------------------ mutation

    def add_node(
        self,
        node_id: str,
        kind: str,
        status: str = "hypothesized",
        evidence: Iterable[str] = (),
        **attrs: Any,
    ) -> dict[str, Any]:
        if kind not in NODE_KINDS:
            raise ModelError(f"unknown node kind {kind!r}; valid: {sorted(NODE_KINDS)}")
        if status not in STATUSES:
            raise ModelError(f"unknown status {status!r}; valid: {sorted(STATUSES)}")
        if node_id in self._nodes:
            raise ModelError(f"node {node_id!r} already exists; use promote() or set_attrs()")
        refs = [str(e) for e in evidence]
        self._require_evidence(status, refs, node_id)
        node = {
            "id": node_id,
            "kind": kind,
            "status": status,
            "evidence": refs,
            "attrs": dict(attrs),
        }
        self._nodes[node_id] = node
        return node

    def add_edge(self, src: str, kind: str, dst: str, **attrs: Any) -> dict[str, Any]:
        if kind not in EDGE_KINDS:
            raise ModelError(f"unknown edge kind {kind!r}; valid: {sorted(EDGE_KINDS)}")
        for endpoint in (src, dst):
            if endpoint not in self._nodes:
                raise ModelError(f"edge endpoint {endpoint!r} is not a node in this model")
        edge = {"src": src, "kind": kind, "dst": dst, "attrs": dict(attrs)}
        self._edges.append(edge)
        return edge

    def promote(self, node_id: str, status: str, evidence: Iterable[str] = ()) -> dict[str, Any]:
        """Raise or lower a node's status.

        The No-Autopromotion invariant is enforced here and nowhere else: a
        status may only rise if this call supplies at least one evidence
        reference the node did not already carry. Carrying a claim forward is
        not verification, and a rank that rises on no new evidence is the
        laundering DAIF-03 refuses by name.
        """
        node = self._node(node_id)
        if status not in STATUSES:
            raise ModelError(f"unknown status {status!r}")
        new_refs = [str(e) for e in evidence if str(e) not in node["evidence"]]
        old_rank = STATUS_RANK.get(node["status"], 0)
        new_rank = STATUS_RANK.get(status, 0)
        if new_rank > old_rank and not new_refs:
            raise ModelError(
                f"No-Autopromotion: {node_id!r} cannot rise "
                f"{node['status']!r} -> {status!r} without new evidence"
            )
        node["evidence"].extend(new_refs)
        self._require_evidence(status, node["evidence"], node_id)
        node["status"] = status
        return node

    def set_attrs(self, node_id: str, **attrs: Any) -> dict[str, Any]:
        node = self._node(node_id)
        node["attrs"].update(attrs)
        return node

    # ------------------------------------------------------------- queries

    @property
    def nodes(self) -> list[dict[str, Any]]:
        return list(self._nodes.values())

    @property
    def edges(self) -> list[dict[str, Any]]:
        return list(self._edges)

    def node(self, node_id: str) -> dict[str, Any]:
        return self._node(node_id)

    def by_kind(self, kind: str) -> list[dict[str, Any]]:
        return [n for n in self._nodes.values() if n["kind"] == kind]

    def unresolved(self) -> list[dict[str, Any]]:
        """Nodes that are still a question rather than a finding."""
        return [
            n for n in self._nodes.values()
            if n["kind"] == "hypothesis" or STATUS_RANK.get(n["status"], 0) <= 1
        ]

    def coverage(self) -> dict[str, dict[str, int]]:
        """Capability x status counts -- the honest shape of what is known.

        Deliberately a COUNT PER CELL, never a ratio. A ratio is satisfied by
        shrinking its denominator, and a coverage percentage is the single
        easiest number in this domain to make look good by asking less.
        """
        table: dict[str, dict[str, int]] = {}
        for node in self._nodes.values():
            row = table.setdefault(node["kind"], {})
            row[node["status"]] = row.get(node["status"], 0) + 1
        return table

    def structural_gaps(self) -> list[dict[str, str]]:
        """Shapes that are wrong regardless of how much evidence exists.

        Not a quality score -- each row is a specific, checkable defect that
        `liveness` and `unknown_unknown_generator` look for in this estate's own
        code, applied here to an observed system instead.
        """
        gaps: list[dict[str, str]] = []
        out_edges: dict[str, int] = {}
        in_edges: dict[str, int] = {}
        for edge in self._edges:
            out_edges[edge["src"]] = out_edges.get(edge["src"], 0) + 1
            in_edges[edge["dst"]] = in_edges.get(edge["dst"], 0) + 1
        for node in self._nodes.values():
            nid, kind = node["id"], node["kind"]
            if kind == "state" and in_edges.get(nid) and not out_edges.get(nid):
                gaps.append({"node": nid, "gap": "state_with_entry_and_no_exit"})
            if kind == "action" and not out_edges.get(nid):
                gaps.append({"node": nid, "gap": "action_with_no_observable_effect"})
            if kind == "failure_mode" and not any(
                e["src"] == nid and e["kind"] == "recovers_through" for e in self._edges
            ):
                gaps.append({"node": nid, "gap": "failure_mode_with_no_recovery_path"})
            if kind == "contract" and not in_edges.get(nid) and not out_edges.get(nid):
                gaps.append({"node": nid, "gap": "contract_bound_to_nothing"})
        return gaps

    # ------------------------------------------------------- interop / io

    def graphify_types(self) -> dict[str, list[str]]:
        """The node and edge type vocabulary this module contributes.

        graphify owns the graph. This is the type list its indexer may register
        so an observed system is locatable by the same query path as everything
        else in the estate -- not a second index.
        """
        return {
            "node_types": sorted(f"osr.{k}" for k in NODE_KINDS),
            "edge_types": sorted(f"osr.{k}" for k in EDGE_KINDS),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "version": self.version,
            "nodes": self.nodes,
            "edges": self.edges,
        }

    def save(self, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True, ensure_ascii=False),
            encoding="utf-8",
        )
        return p

    @classmethod
    def load(cls, path: str | Path) -> "ObservedSystemModel":
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        model = cls(data["target"], data.get("version", "unpinned"))
        for node in data.get("nodes", []):
            model._nodes[node["id"]] = {
                "id": node["id"],
                "kind": node["kind"],
                "status": node.get("status", "unknown"),
                "evidence": list(node.get("evidence", [])),
                "attrs": dict(node.get("attrs", {})),
            }
        model._edges = [dict(e) for e in data.get("edges", [])]
        model.validate()
        return model

    def validate(self) -> None:
        for node in self._nodes.values():
            if node["kind"] not in NODE_KINDS:
                raise ModelError(f"node {node['id']!r} has unknown kind {node['kind']!r}")
            if node["status"] not in STATUSES:
                raise ModelError(f"node {node['id']!r} has unknown status {node['status']!r}")
            self._require_evidence(node["status"], node["evidence"], node["id"])
        ids = set(self._nodes)
        for edge in self._edges:
            if edge["kind"] not in EDGE_KINDS:
                raise ModelError(f"edge has unknown kind {edge['kind']!r}")
            if edge["src"] not in ids or edge["dst"] not in ids:
                raise ModelError(f"edge {edge['src']}->{edge['dst']} references a missing node")

    # -------------------------------------------------------------- internals

    def _node(self, node_id: str) -> dict[str, Any]:
        try:
            return self._nodes[node_id]
        except KeyError:
            raise ModelError(f"no such node: {node_id!r}") from None

    @staticmethod
    def _require_evidence(status: str, refs: list[str], node_id: str) -> None:
        if STATUS_RANK.get(status, 0) >= _EVIDENCE_REQUIRED_AT and not refs:
            raise ModelError(
                f"{node_id!r} claims status {status!r} with no evidence reference; "
                "a claim about reality cites the Evidence Object that supports it"
            )
