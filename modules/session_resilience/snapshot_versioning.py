"""G3 -- Incremental Snapshot & Session Versioning Engine.

Stores session state as a baseline + a chain of deltas so capture is cheap
(small change -> small delta) and any retained version is exactly reconstructable
and restore-to-a-prior-version is possible. Operates on the canonical
StateDescription (models.py) produced by the capture systems (G1/G2/CETTG). At
RESTORE time it hands the reconstructed version to G4 to validate the recovery
(the prompt's "G4 validates the snapshot before use"). Composes -- does NOT
modify -- modules/cpc_os/snapshot.py (which renders one full pane snapshot;
G3 versions the broader description). Hermetic: persistence takes an explicit
``state_dir``; version ids are a deterministic monotonic counter (no clock/random
needed for correctness), an injectable ``ts`` records wall time when wanted.

Eight entities (dataset session_resilience_03):
  1. Delta Capture Engine      -- compute_delta / apply_delta (real diff/patch)
  2. Baseline Anchor Registry  -- periodic full anchors so replay stays bounded
  3. Snapshot Chain Manager    -- append-only ordered baseline->delta chain
  4. Version Catalog           -- enumerable restorable versions + metadata
  5. Version Restore Selector  -- choose latest / by id / by predicate
  6. Compaction & Retention    -- prune old, NEVER orphan a protected version
  7. Integrity Chain Validator -- reconstruct + end-to-end hash check; withhold
  8. Version Diff Presenter    -- human-readable difference between two versions
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from . import models

_MISSING = object()


# --- Entity 1: Delta Capture Engine -----------------------------------------
# A description is a nested dict; dicts are recursed, lists+scalars are leaves
# (lists are small here -- tabs/terminals -- so whole-list replacement keeps the
# delta proportional to real change while guaranteeing correct reconstruction).

def _walk(obj: Any, prefix: tuple = ()):
    if isinstance(obj, dict):
        for k in obj:
            yield from _walk(obj[k], prefix + (k,))
    else:
        yield prefix, obj


def _leafmap(desc: dict) -> dict[tuple, Any]:
    return dict(_walk(desc))


def _rebuild(leafmap: dict[tuple, Any]) -> dict:
    root: dict = {}
    for path, val in leafmap.items():
        d = root
        for k in path[:-1]:
            nxt = d.get(k)
            if not isinstance(nxt, dict):
                nxt = {}
                d[k] = nxt
            d = nxt
        d[path[-1]] = val
    return root


@dataclass
class Delta:
    set_ops: list[tuple[tuple, Any]] = field(default_factory=list)
    del_ops: list[tuple] = field(default_factory=list)

    def size(self) -> int:
        return len(self.set_ops) + len(self.del_ops)

    def to_jsonable(self) -> dict:
        return {
            "set": [[list(p), v] for p, v in self.set_ops],
            "del": [list(p) for p in self.del_ops],
        }

    @staticmethod
    def from_jsonable(d: dict) -> "Delta":
        return Delta(
            set_ops=[(tuple(p), v) for p, v in d.get("set", [])],
            del_ops=[tuple(p) for p in d.get("del", [])],
        )


def compute_delta(prev: dict, cur: dict) -> Delta:
    """The change that transforms ``prev`` into ``cur`` (empty if identical)."""
    a, b = _leafmap(prev), _leafmap(cur)
    set_ops = [(p, b[p]) for p in b if a.get(p, _MISSING) != b[p]]
    del_ops = [p for p in a if p not in b]
    return Delta(set_ops=set_ops, del_ops=del_ops)


def apply_delta(base: dict, delta: Delta) -> dict:
    """Reconstruct the next state from ``base`` + ``delta`` (inverse of compute)."""
    lm = _leafmap(base)
    for p in delta.del_ops:
        lm.pop(p, None)
    for p, v in delta.set_ops:
        lm[p] = v
    return _rebuild(lm)


# --- atomic JSON write (standalone; mirrors registry._atomic_write semantics) -

def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


# --- Entities 2-8: the version store ----------------------------------------

@dataclass
class VersionMeta:
    """Entity 4: Version Catalog row."""
    version_id: str
    index: int
    ts: str | None
    reason: str
    tag: str | None
    state_hash: str
    is_baseline: bool


class SessionVersionStore:
    """Baseline + delta chain with a version catalog, restore selection,
    integrity validation, and protected-aware compaction. One JSON file under
    ``state_dir`` (hermetic)."""

    def __init__(
        self,
        state_dir: Path | str,
        filename: str = "session_versions.json",
        anchor_every: int = 8,  # Entity 2: re-anchor a full baseline every N versions
        max_versions: int = 50,  # Entity 6: retention cap
    ) -> None:
        self.path = Path(state_dir) / filename
        self.anchor_every = anchor_every
        self.max_versions = max_versions
        self._data = self._load()

    # ---- persistence ----
    def _load(self) -> dict:
        if self.path.is_file():
            try:
                return json.loads(self.path.read_text(encoding="utf-8-sig"))
            except json.JSONDecodeError:
                pass
        return {"versions": [], "next_id": 0}  # each: meta + (baseline | delta)

    def _save(self) -> None:
        _atomic_write_json(self.path, self._data)

    # ---- Entity 3: Snapshot Chain Manager ----
    def record(
        self,
        description: dict,
        reason: str = "capture",
        tag: str | None = None,
        ts: str | None = None,
    ) -> str:
        """Append a new version. Stored as a full baseline if it is the first or
        an anchor point, else as a delta from the previous version."""
        versions = self._data["versions"]
        idx = len(versions)               # list position (re-derived on prune)
        nid = self._data.get("next_id", 0)  # globally monotonic; survives prune
        self._data["next_id"] = nid + 1
        vid = f"v{nid}"
        h = models.state_hash(description)
        is_anchor = (idx == 0) or (idx % self.anchor_every == 0)
        meta = {
            "version_id": vid, "index": idx, "ts": ts, "reason": reason,
            "tag": tag, "state_hash": h, "is_baseline": is_anchor,
        }
        if is_anchor:
            meta["baseline"] = models.canonical(description)
        else:
            prev = self._reconstruct_index(idx - 1)
            meta["delta"] = compute_delta(prev, description).to_jsonable()
        versions.append(meta)
        self._prune()
        self._save()
        return vid

    # ---- Entity 7: Integrity Chain Validator (internal reconstruct) ----
    def _reconstruct_index(self, index: int) -> dict:
        versions = self._data["versions"]
        if index < 0 or index >= len(versions):
            raise IndexError(f"no version at index {index}")
        # walk back to the nearest baseline, then replay forward
        start = index
        while start > 0 and not versions[start].get("is_baseline"):
            start -= 1
        base_meta = versions[start]
        if not base_meta.get("is_baseline"):
            raise ValueError("chain broken: no baseline reachable")
        state = models.canonical(base_meta["baseline"])
        for i in range(start + 1, index + 1):
            state = apply_delta(state, Delta.from_jsonable(versions[i]["delta"]))
        return state

    def reconstruct(self, version_id: str) -> dict:
        """Reconstruct a version, validated end-to-end. Raises if the recorded
        hash does not match the replay (integrity break) -- never returns a
        silently-wrong state."""
        idx = self._index_of(version_id)
        state = self._reconstruct_index(idx)
        expected = self._data["versions"][idx]["state_hash"]
        actual = models.state_hash(state)
        if actual != expected:
            raise ValueError(
                f"integrity break at {version_id}: hash {actual[:12]} != {expected[:12]}"
            )
        return state

    def _index_of(self, version_id: str) -> int:
        for v in self._data["versions"]:
            if v["version_id"] == version_id:
                return v["index"]
        raise KeyError(version_id)

    # ---- Entity 4: Version Catalog ----
    def catalog(self) -> list[VersionMeta]:
        return [
            VersionMeta(
                v["version_id"], v["index"], v.get("ts"), v.get("reason", ""),
                v.get("tag"), v["state_hash"], bool(v.get("is_baseline")),
            )
            for v in self._data["versions"]
        ]

    # ---- Entity 5: Version Restore Selector ----
    def select(self, request: str | Callable[[VersionMeta], bool] = "latest") -> str | None:
        """Choose a version: 'latest', a version_id, or a predicate over metas
        (returns the most recent match). None if nothing matches."""
        cat = self.catalog()
        if not cat:
            return None
        if request == "latest":
            return cat[-1].version_id
        if isinstance(request, str):
            return request if any(v.version_id == request for v in cat) else None
        for v in reversed(cat):
            if request(v):
                return v.version_id
        return None

    # ---- Entity 6: Compaction & Retention (never orphan a protected version) ----
    def _prune(self) -> None:
        """Keep all tagged (protected) versions + the most-recent ones up to the
        cap, then RE-CHAIN the kept set so no kept version depends on a dropped
        delta (the orphaning hazard). Re-chaining reconstructs each kept version
        to a full state and rebuilds baseline+deltas over the kept set only.
        version_id stays stable so external selections still resolve."""
        versions = self._data["versions"]
        n = len(versions)
        if n <= self.max_versions:
            return
        keep = [bool(v.get("tag")) for v in versions]  # tagged always survives
        kept_count = sum(keep)
        for i in range(n - 1, -1, -1):  # then most-recent until cap
            if kept_count >= self.max_versions:
                break
            if not keep[i]:
                keep[i] = True
                kept_count += 1
        kept_indices = [i for i in range(n) if keep[i]]
        fulls = {i: self._reconstruct_index(i) for i in kept_indices}  # before mutation
        rebuilt: list[dict] = []
        for newpos, i in enumerate(kept_indices):
            old = versions[i]
            desc = fulls[i]
            meta = {
                "version_id": old["version_id"], "index": newpos,
                "ts": old.get("ts"), "reason": old.get("reason", ""),
                "tag": old.get("tag"), "state_hash": models.state_hash(desc),
                "is_baseline": newpos == 0,
            }
            if newpos == 0:
                meta["baseline"] = models.canonical(desc)
            else:
                prev = fulls[kept_indices[newpos - 1]]
                meta["delta"] = compute_delta(prev, desc).to_jsonable()
            rebuilt.append(meta)
        self._data["versions"] = rebuilt

    # ---- Entity 8: Version Diff Presenter ----
    def diff(self, version_a: str, version_b: str) -> list[str]:
        """Human-readable difference between two versions (per-dimension)."""
        a = self.reconstruct(version_a)
        b = self.reconstruct(version_b)
        lines: list[str] = []
        for dim, extractor in models.EXTRACTORS.items():
            va, vb = extractor(a), extractor(b)
            if va != vb:
                lines.append(f"{dim}: changed")
        if not lines:
            lines.append("no perceptible difference")
        return lines
