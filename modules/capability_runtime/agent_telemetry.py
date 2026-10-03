#!/usr/bin/env python3
"""agent_telemetry.py -- one resolver result -> one CO-12 `agent_resolution` signal (ACV C5, D3).

Spec: vault/specs/agent-capability-virtualization.md (D3); plan:
vault/plans/acv-c5-agent-telemetry-2026-10-03.md.

The adapter COPIES what the resolver decided and never recomputes it: miss, miss_ids, vetoed_by,
cache, policy, the catalog fingerprint and query_fp all come from the result dict. It adds only
what it owns -- the schema tag and a resolution_id (an identity minted here, so a later
agent_run can join on it; never a fact about the request). `ts` comes from CO-12.

Telemetry is a separate failure domain. A write that fails, or a result the mapping cannot read,
returns recorded=False; the resolver result is returned untouched either way, so a telemetry
problem can never become a miss. This file is in agent_resolver.NOT_POLICY: editing it cannot
change an answer, so it must not change the policy id that keys the resolver cache.

agent_metrics() is read-only and derived from the same signals -- there is no second store. A
cache HIT is a reuse of an earlier computation, never a new observation, and a miss count is a
count of resolver answers, not of capabilities anyone needs: that needs run outcomes (C6+).
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path
from typing import Callable, NamedTuple

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.capability_runtime import agent_resolver as R  # noqa: E402
from modules.cognitive_os import co_12_telemetry as CO12  # noqa: E402

KIND = "agent_resolution"
SCHEMA = "agent-telemetry/1"
MISS_IDS_CAP = 20                       # the list is capped; miss_ids_total keeps the true count
RESERVED = frozenset({"kind", "ts"})    # CO-12 writes these; a payload key would overwrite them


class Recorded(NamedTuple):
    result: dict          # exactly what resolve() returned
    recorded: bool        # True only when the sink confirmed the write
    resolution_id: str


def to_payload(result: dict, *, grant: str, resolution_id: str,
               goal_id: str | None = None, dispatch_id: str | None = None) -> dict:
    """The signal body. Key access is strict: a result without a field the contract names is a
    defect to surface (recorded=False), not a gap to fill with a default."""
    ids = list(result["miss_ids"])
    payload = {
        "schema": SCHEMA,
        "resolution_id": resolution_id,
        "miss": result["miss"],
        "candidate_ids": [c["id"] for c in result["candidates"]],
        "miss_ids": ids[:MISS_IDS_CAP],
        "miss_ids_total": len(ids),
        "vetoed_by": list(result["vetoed_by"]),
        "cache": result["cache"],
        "policy": result["policy"],
        "catalog_fp": result["fingerprint"],
        "query_fp": result["query_fp"],
        "grant": grant,
    }
    if goal_id is not None:
        payload["goal_id"] = goal_id
    if dispatch_id is not None:
        payload["dispatch_id"] = dispatch_id
    return payload


def resolve_and_record(task: str, max_class: str = "verifier", k: int = 3,
                       specs_dir: Path | None = None, use_cache: bool = True,
                       cache_path: Path | None = None, *,
                       sink: Callable[[str, dict], bool] | None = None,
                       goal_id: str | None = None, dispatch_id: str | None = None) -> Recorded:
    """resolve() once, then one signal for its final answer. EMPTY_TASK / UNKNOWN_CLASS raise
    from resolve() before anything is recorded. `sink` None -> CO-12 record_signal, looked up
    at call time so a test spy on the module attribute intercepts it."""
    result = R.resolve(task, max_class, k, specs_dir=specs_dir, use_cache=use_cache, cache_path=cache_path)
    rid = uuid.uuid4().hex
    try:
        payload = to_payload(result, grant=max_class, resolution_id=rid,
                             goal_id=goal_id, dispatch_id=dispatch_id)
        if RESERVED & payload.keys():
            return Recorded(result, False, rid)
        write = sink if sink is not None else CO12.record_signal
        recorded = write(KIND, payload) is True
    except Exception:  # noqa: BLE001 -- telemetry never changes the answer it describes
        recorded = False
    return Recorded(result, recorded, rid)


def agent_metrics(*, state_dir=None) -> dict:
    """Resolver telemetry, derived from CO-12 signals. UNREADABLE is not EMPTY: an unreadable
    signals file reports measured=False and no numbers at all."""
    stats: dict = {}
    try:
        sigs = CO12.load_signals(state_dir=state_dir, strict=True, stats=stats)
    except OSError as e:
        return {"measured": False, "status": "unreadable", "reason": type(e).__name__}
    # Torn lines are counted, not guessed at: a row the reader could not parse may have been one
    # of ours, so the totals below are a floor whenever unparseable_lines > 0.
    unparseable = stats.get("unparseable", 0) + sum(1 for s in sigs if not isinstance(s, dict))
    rows = [s for s in sigs if isinstance(s, dict) and s.get("kind") == KIND]
    schemas: dict = {}
    by_miss: dict = {}
    fresh = cached = cache_unknown = 0
    observations, qfps = set(), set()
    for s in rows:
        schemas[s.get("schema")] = schemas.get(s.get("schema"), 0) + 1
        if s.get("schema") != SCHEMA:
            continue                    # an unknown schema is counted, never interpreted
        slot = by_miss.setdefault(s.get("miss") or "RESOLVED", {"fresh": 0, "cached": 0})
        qfps.add(s.get("query_fp"))
        if s.get("cache") == "HIT":
            cached += 1
            slot["cached"] += 1
        elif s.get("cache") == "MISS":
            fresh += 1
            slot["fresh"] += 1
            # One request answered fresh twice (cache bypassed, partial catalog, eviction) is
            # one observation, not two.
            observations.add((s.get("query_fp"), s.get("grant"), s.get("catalog_fp"), s.get("policy")))
        else:
            cache_unknown += 1
    return {"measured": True, "status": "live" if rows else "no observations",
            "resolutions": len(rows), "fresh": fresh, "cached": cached,
            "cache_unknown": cache_unknown, "by_miss": by_miss,
            "distinct_fresh_observations": len(observations),
            "distinct_query_fp": len(qfps), "schemas_seen": schemas,
            "unparseable_lines": unparseable}
