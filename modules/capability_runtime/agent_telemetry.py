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

import json
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


# --------------------------------------------------------------------------- #
# Run accounting (ACV C6): one terminal `agent_run` signal per executed run.
# --------------------------------------------------------------------------- #
RUN_KIND = "agent_run"
# Token fields copied verbatim from the executor's result.modelUsage. Price, context window and
# provider are left out on purpose: C6 accounts resources, pricing is downstream.
USAGE_FIELDS = ("inputTokens", "outputTokens", "cacheReadInputTokens", "cacheCreationInputTokens",
                "thinkingTokens", "webSearchRequests")
CORE_USAGE = USAGE_FIELDS[:4]


def _int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def usage_from_result(result: dict | None) -> tuple[str, dict]:
    """(usage_state, per-model token fields) from ONE executor result event.

    MEASURED: every model entry carries the four core token counts. PARTIAL: modelUsage is there
    but an entry lacks one -- the missing field stays missing. UNMEASURED: no result event, or no
    or empty modelUsage. Nothing is zero-filled, estimated or summed into a new total."""
    mu = (result or {}).get("modelUsage")
    if not isinstance(mu, dict) or not mu:
        return "UNMEASURED", {}
    usage, partial = {}, False
    for model, u in mu.items():
        row = {f: u[f] for f in USAGE_FIELDS if isinstance(u, dict) and _int(u.get(f))}
        partial = partial or any(f not in row for f in CORE_USAGE)
        usage[str(model)] = row
    return ("PARTIAL" if partial else "MEASURED"), usage


def usage_from_results(results: list) -> tuple[str, dict, str | None]:
    """The run's usage from ALL its result events (real streams carry two: same session, same
    session-cumulative modelUsage, different per-turn fields). The last one is used; if the
    events disagree on session or modelUsage the total is not trustworthy -> PARTIAL."""
    if not results:
        return "UNMEASURED", {}, "no_result_event"
    state, usage = usage_from_result(results[-1])
    if len({json.dumps((r.get("session_id"), r.get("modelUsage")), sort_keys=True) for r in results}) > 1:
        return ("PARTIAL" if usage else "UNMEASURED"), usage, "result_events_disagree"
    return state, usage, None


def carrier_share(usage: dict, models_observed: dict) -> str:
    """Whether the carrier's own usage can be read off the per-model totals. modelUsage covers the
    whole session (parent + carrier), so only a carrier on a model the parent never used is
    SEPARABLE. Models are the OBSERVED message.model ids, never a configured alias."""
    parent = set(models_observed.get("parent") or [])
    carrier = set(models_observed.get("carrier") or [])
    if not carrier:
        return "UNKNOWN"
    if parent & carrier:
        return "UNSEPARABLE"
    return "SEPARABLE" if carrier <= set(usage) else "UNKNOWN"


def run_payload(*, resolution_id, run_id, run_id_source, spec, spec_hash, permission_class, carrier,
                purpose, executor_status, executor_error, harness_status, results, models_observed,
                carrier_model_configured, seconds) -> dict:
    state, usage, reason = usage_from_results(results)
    payload = {
        "schema": SCHEMA, "resolution_id": resolution_id, "run_id": run_id, "run_id_source": run_id_source,
        "spec": spec, "spec_hash": spec_hash, "permission_class": permission_class, "carrier": carrier,
        "purpose": purpose, "executor_status": executor_status, "executor_error": executor_error,
        "harness_status": harness_status, "result_events": len(results), "usage_state": state,
        "model_usage": usage, "carrier_share": carrier_share(usage, models_observed),
        "models_observed": {k: sorted(v) for k, v in models_observed.items()},
        "carrier_model_configured": carrier_model_configured, "seconds": seconds,
    }
    if reason:
        payload["usage_reason"] = reason
    return payload


def record_run(payload: dict, *, sink: Callable[[str, dict], bool] | None = None) -> bool:
    """One agent_run signal. Fail-open: False on any failure, never raises, never changes the run.
    sink None -> CO-12 record_signal looked up at call time (a test guard intercepts it)."""
    try:
        if RESERVED & payload.keys():
            return False
        write = sink if sink is not None else CO12.record_signal
        return write(RUN_KIND, payload) is True
    except Exception:  # noqa: BLE001 -- accounting never breaks the run it describes
        return False


def _run_metrics(sigs: list, resolutions: list) -> dict:
    """Run accounting, derived from the signals. Token sums cover MEASURED runs only, per model and
    category, and say so; PARTIAL and UNMEASURED runs are counted, never zero-filled. These are
    resources consumed, not value: consumption and outcome joins do not exist yet (C7)."""
    runs = [s for s in sigs if isinstance(s, dict) and s.get("kind") == RUN_KIND and s.get("schema") == SCHEMA]
    res_cache = {r.get("resolution_id"): r.get("cache") for r in resolutions if r.get("schema") == SCHEMA}
    count = lambda xs: {k: xs.count(k) for k in sorted(set(xs), key=str)}  # noqa: E731
    linked = [r for r in runs if r.get("resolution_id") in res_cache]
    tokens: dict = {}
    for r in runs:
        if r.get("usage_state") != "MEASURED":
            continue
        for model, row in (r.get("model_usage") or {}).items():
            slot = tokens.setdefault(model, {})
            for f, v in row.items():
                if _int(v):
                    slot[f] = slot.get(f, 0) + v
    per_res: dict = {}
    for r in linked:
        per_res[r["resolution_id"]] = per_res.get(r["resolution_id"], 0) + 1
    return {
        "runs": len(runs),
        "distinct_run_ids": len({r.get("run_id") for r in runs if r.get("run_id")}),
        "linked": len(linked),
        "unlinked": sum(1 for r in runs if r.get("resolution_id") is None),
        "dangling": sum(1 for r in runs if r.get("resolution_id") is not None and r.get("resolution_id") not in res_cache),
        "by_purpose": count([r.get("purpose") for r in runs]),
        "by_executor_status": count([f"{r.get('executor_status')}{'+is_error' if r.get('executor_error') else ''}"
                                     for r in runs]),
        "usage_state": count([r.get("usage_state") for r in runs]),
        "carrier_share": count([r.get("carrier_share") for r in runs]),
        "measured_tokens": tokens,
        "measured_tokens_scope": "sum over MEASURED runs only",
        "linked_by_resolution_cache": count([res_cache[r["resolution_id"]] for r in linked]),
        "resolutions_with_zero_runs": sum(1 for rid in res_cache if rid not in per_res),
        "max_runs_per_resolution": max(per_res.values(), default=0),
    }


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
            "unparseable_lines": unparseable, "runs": _run_metrics(sigs, rows)}
