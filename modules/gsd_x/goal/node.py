#!/usr/bin/env python3
"""Consume an Orca node manifest (orca.node-manifest/1) as a goal's view of one host (UWCP S4-22 consume half).

Read-only. A manifest is refused, never repaired, when it is malformed, older than
the caller's freshness bound, from the future, or carries a measurement past its own
max_age_ms. An `unknown` measurement stays unknown: it is never read as zero.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

SCHEMA = "orca.node-manifest/1"
CLOCK_SKEW_MS = 60_000
MEASUREMENTS = ("memory", "disk", "vram", "resident_model")
_VALUE_KEYS = {"memory": {"total_bytes", "available_bytes", "available_source"},
               "disk": {"filesystems"}, "vram": {"gpus"}, "resident_model": {"endpoints", "unanswered_ports"}}


class NodeManifestError(ValueError):
    """A manifest the consumer refuses; `.code` says why."""

    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code


@dataclass(frozen=True)
class NodeView:
    address: str
    observed_at: int
    measured: dict    # name -> value dict, only for measurements that were measured
    unknown: dict     # name -> reason, kept apart from any number
    known_heads: tuple[str, ...] | None = None   # None = the node did not say; never an empty tuple


def _int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


def _need(cond: bool, code: str, detail: str) -> None:
    if not cond:
        raise NodeManifestError(code, detail)


def _check_measurement(name: str, m, now_ms: int) -> None:
    _need(isinstance(m, dict), "malformed", f"measurements.{name} is not an object")
    if m.get("status") == "unknown":
        _need(set(m) <= {"status", "reason", "detail"} and isinstance(m.get("reason"), str) and m["reason"],
              "malformed", f"measurements.{name} unknown needs a reason")
        return
    _need(m.get("status") == "measured", "malformed", f"measurements.{name}.status is neither measured nor unknown")
    _need(set(m) == {"status", "value", "measured_at", "max_age_ms", "source"}, "malformed",
          f"measurements.{name} fields {sorted(m)}")
    _need(_int(m["measured_at"]), "malformed", f"measurements.{name}.measured_at")
    age_cap = m["max_age_ms"]
    _need(isinstance(age_cap, (int, float)) and not isinstance(age_cap, bool) and age_cap > 0,
          "malformed", f"measurements.{name}.max_age_ms")
    _need(isinstance(m["source"], str) and m["source"], "malformed", f"measurements.{name}.source")
    value = m["value"]
    _need(isinstance(value, dict) and set(value) == _VALUE_KEYS[name], "malformed", f"measurements.{name}.value shape")
    if name == "memory":
        _need(_int(value["total_bytes"]) and _int(value["available_bytes"]), "malformed", "memory bytes")
    _need(now_ms - m["measured_at"] <= age_cap, "stale_measurement",
          f"measurements.{name} is {now_ms - m['measured_at']} ms old, its own bound is {age_cap}")


def read_node_manifest(doc, now_ms: int, max_age_ms: int) -> NodeView:
    """Validate `doc` (dict, JSON text or a path) and return the host view, or raise NodeManifestError."""
    if isinstance(doc, (str, Path)) and not (isinstance(doc, str) and doc.lstrip().startswith("{")):
        try:
            doc = Path(doc).read_text(encoding="utf-8")
        except OSError as exc:
            raise NodeManifestError("unreadable", str(exc)) from exc
    if isinstance(doc, str):
        try:
            doc = json.loads(doc)
        except ValueError as exc:
            raise NodeManifestError("malformed", f"not JSON: {exc}") from exc
    _need(isinstance(doc, dict), "malformed", "manifest is not an object")
    _need(doc.get("schema") == SCHEMA, "malformed", f"schema is {doc.get('schema')!r}")
    _need(set(doc) <= {"schema", "observed_at", "node", "known_heads", "measurements"}
          and {"observed_at", "node", "measurements"} <= set(doc), "malformed", f"top-level fields {sorted(doc)}")
    _need(_int(doc["observed_at"]), "malformed", "observed_at")
    node = doc["node"]
    _need(isinstance(node, dict) and isinstance(node.get("address"), str) and node["address"],
          "malformed", "node.address")
    meas = doc["measurements"]
    _need(isinstance(meas, dict) and set(meas) == set(MEASUREMENTS), "malformed", "measurements keys")
    heads = doc.get("known_heads")
    # Mirrors orca-node-manifest-1.schema.json: absent means unknown, an empty list is never emitted.
    _need(heads is None and "known_heads" not in doc
          or isinstance(heads, list) and heads and all(isinstance(h, str) and h for h in heads),
          "malformed", "known_heads must be absent or a non-empty list of non-empty strings")
    _need(doc["observed_at"] - now_ms <= CLOCK_SKEW_MS, "from_future", f"observed_at is {doc['observed_at'] - now_ms} ms ahead")
    _need(now_ms - doc["observed_at"] <= max_age_ms, "stale_manifest",
          f"observed {now_ms - doc['observed_at']} ms ago, bound {max_age_ms}")
    for name in MEASUREMENTS:
        _check_measurement(name, meas[name], now_ms)
    return NodeView(
        address=node["address"], observed_at=doc["observed_at"],
        measured={n: meas[n]["value"] for n in MEASUREMENTS if meas[n]["status"] == "measured"},
        unknown={n: meas[n]["reason"] for n in MEASUREMENTS if meas[n]["status"] == "unknown"},
        known_heads=tuple(heads) if heads else None)
