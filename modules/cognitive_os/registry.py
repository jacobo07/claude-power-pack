#!/usr/bin/env python3
"""registry.py -- CO-05: Zero Token Layer & Cognitive Asset Registry.

The kernel's institutional memory: every verified, reusable conclusion becomes a
permanent asset, retrieved thereafter at ZERO new model cost. The system never
reasons the same thing twice. This is the rung CO-03's cascade reaches first.

Lifecycle (CO-05 I.2): discover -> verify -> store -> retrieve -> refresh.
- STORE only what the Production Reality Gate verified AND that cleared the
  recurrence threshold (compound-learnings: 3+). A hypothesis is not an asset;
  storing the unverified would poison CO-03's cheap rungs (the cardinal sin).
- Every asset carries a FRESHNESS ANCHOR (a file hash). Retrieval CHECKS the
  anchor: a stale asset (its source changed) is never served blind -- it is
  demoted to verify-before-use. An anchor-less asset is treated as stale (never
  auto-fresh). This is the difference between a live memory and a rotting archive.

Wired into CO-03: vault_resolver()/asset_resolver() are the router's rung-1/2,
so the zero-token rungs are ACTIVE (an empty registry simply misses -> the
cascade falls to a model, today's behavior; as assets accrue, hits compound).

Registry = vault/cognitive_os/asset_registry.jsonl (append-only runtime memory,
gitignored). Fail-open everywhere: a registry error never blocks routing.
"""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

DEFAULT_REGISTRY = _PP_ROOT / "vault" / "cognitive_os" / "asset_registry.jsonl"
RECURRENCE_THRESHOLD = 3            # compound-learnings 3+ = strong enough to store
KNOWLEDGE_KINDS = ("knowledge", "decision", "mapping", "rca")   # -> vault rung
ASSET_KINDS = ("template", "rule", "pattern", "cache")          # -> asset rung


@dataclass
class Asset:
    key: str
    kind: str
    content: str
    applicability: list = field(default_factory=list)   # keywords that match a task
    anchor: dict = field(default_factory=lambda: {"type": "none"})
    verified: bool = False
    stored_ts: str = ""
    retrievals: int = 0


def file_hash(path) -> str | None:
    """Short sha256 of a file, or None if unreadable. The freshness anchor."""
    try:
        h = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        return h[:16]
    except OSError:
        return None


def is_fresh(asset: Asset, *, hash_fn=file_hash) -> bool:
    """An asset is fresh only if its anchor still matches its source. A 'none'
    anchor is NOT auto-fresh (verify-before-use) -- never served blind."""
    a = asset.anchor or {}
    if a.get("type") == "file" and a.get("path"):
        cur = hash_fn(a["path"])
        return cur is not None and cur == a.get("hash")
    return False


def _match(task: str, applicability) -> bool:
    t = (task or "").lower()
    return any(kw.lower() in t for kw in (applicability or []))


def store_asset(key: str, kind: str, content: str, *, applicability=None,
                anchor=None, verified: bool, recurrence: int = 0,
                now: datetime | None = None, registry_path=None) -> bool:
    """Store an asset iff it is VERIFIED and met the recurrence threshold.
    Returns True if stored, False if rejected (unverified / sub-threshold).
    Best-effort I/O: an append error returns False without raising."""
    if not verified or recurrence < RECURRENCE_THRESHOLD:
        return False
    now = now or datetime.now(timezone.utc)
    asset = Asset(key=key, kind=kind, content=content,
                  applicability=list(applicability or []),
                  anchor=anchor or {"type": "none"}, verified=True,
                  stored_ts=now.isoformat())
    try:
        p = Path(registry_path) if registry_path else DEFAULT_REGISTRY
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(asset), ensure_ascii=False) + "\n")
        return True
    except OSError:
        return False


def load_assets(registry_path=None) -> list:
    p = Path(registry_path) if registry_path else DEFAULT_REGISTRY
    if not p.is_file():
        return []
    out: list[Asset] = []
    try:
        for line in p.read_text(encoding="utf-8", errors="replace").split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            out.append(Asset(**{k: d.get(k) for k in (
                "key", "kind", "content", "applicability", "anchor",
                "verified", "stored_ts", "retrievals")}))
    except OSError:
        return []
    return out


def lookup(task: str, *, kinds=None, registry_path=None, hash_fn=file_hash):
    """Best FRESH asset whose applicability matches the task (and whose kind is
    in `kinds`, if given). A stale match is skipped (never served blind).
    Returns the Asset or None. Fail-open -> None."""
    try:
        for a in load_assets(registry_path):
            if kinds and a.kind not in kinds:
                continue
            if not a.verified or not _match(task, a.applicability):
                continue
            if is_fresh(a, hash_fn=hash_fn):
                return a
        return None
    except Exception:  # noqa: BLE001 -- fail-open
        return None


def vault_resolver(task: str, *, registry_path=None, hash_fn=file_hash):
    """CO-03 rung-1: a stored verified ANSWER (knowledge/decision/mapping/rca).
    Returns the asset content (zero-token resolution) or None."""
    a = lookup(task, kinds=KNOWLEDGE_KINDS, registry_path=registry_path,
               hash_fn=hash_fn)
    return a.content if a else None


def asset_resolver(task: str, *, registry_path=None, hash_fn=file_hash):
    """CO-03 rung-2: a reusable TEMPLATE/RULE/PATTERN applied without reasoning.
    Returns the asset content or None."""
    a = lookup(task, kinds=ASSET_KINDS, registry_path=registry_path,
               hash_fn=hash_fn)
    return a.content if a else None


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("task", nargs="*")
    ap.add_argument("--registry", default=None)
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)
    if args.list:
        for a in load_assets(args.registry):
            print(f"{a.kind:10} {a.key:24} fresh={is_fresh(a)} "
                  f"appl={a.applicability}")
        return 0
    task = " ".join(args.task)
    v = vault_resolver(task, registry_path=args.registry)
    s = asset_resolver(task, registry_path=args.registry)
    print(f"vault: {v or '(miss)'}")
    print(f"asset: {s or '(miss)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
