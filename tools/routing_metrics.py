"""Routing Metrics (T8 item 29): how each continuation ROUTE of cpp-gsd-long actually performed.

The routing decision that is live in the long-run substrate is how a mission gets its next
worker: which cause launched it (INITIAL / CONTEXT_ROTATION / TURN_CONTINUATION /
PROCESS_RECOVERY), by which mechanism (fresh / resume / compact), on which model. This tool
turns the mission ledger + the workers' own transcripts into the attempt records the vendored
`genesis-routing-metrics` analyzer takes, and runs it through the node bridge.

Unit of analysis
  run      one mission epoch (taskId = "<mission>#e<epoch>")
  attempt  one `launched` event for that epoch, in order
  route    "<cause>/<mechanism>:<model>" -- every part is observed or the literal "unknown"
  status   passed = the worker's transcript shows a model call that issued a tool_use;
           failed = a provider refusal, or a worker that acked and never acted;
           unknown = no worker identity or no transcript. The vendored analyzer has no
           "unknown" status, so a run holding an unknown attempt is WITHHELD from it and listed
           under `unjudged_runs` -- it is never recorded as failed.
  history  complete only when the launch cause was recorded AND every attempt was judged.
           An incomplete run keeps its observed sums; its totals stay null (vendor semantics).
  tokens   summed over every assistant call in the worker transcript. `costUsd` is always
           null: no price is invented. Cache reads are reported beside the vendor fields
           because they dominate long-context cost and the vendor schema has no slot for them.

    python tools/routing_metrics.py [--mission m-...] [--since 2026-09-27] [--json]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))
import gsd_long_run as lr  # noqa: E402
from modules.external_assimilation import node_bridge as nb  # noqa: E402

UNKNOWN = "unknown"
WORKER_EVENTS = ("worker_acked", "worker_adopted")
TERMINAL_EVENTS = ("mission_halted", "mission_completed", "retired")


def _ts(v) -> float | None:
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00")).timestamp() if v else None
    except ValueError:
        return None


def transcript_usage(path: Path | None) -> dict:
    """Observed usage of one worker session. Never estimates."""
    if path is None:
        return {"state": "UNMEASURED", "reason": "transcript not found"}
    model = None
    calls = acted = 0
    inp = out = cread = cwrite = 0
    refusal = None
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if '"assistant"' not in line:
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(row, dict) or row.get("type") != "assistant":
                    continue
                msg = row.get("message") if isinstance(row.get("message"), dict) else {}
                if msg.get("model") == "<synthetic>":
                    if calls == 0 and refusal is None:
                        refusal = str(msg.get("content"))[:160]
                    continue
                u = msg.get("usage")
                if not isinstance(u, dict):
                    continue
                calls += 1
                model = model or msg.get("model")
                inp += int(u.get("input_tokens") or 0)
                cwrite += int(u.get("cache_creation_input_tokens") or 0)
                cread += int(u.get("cache_read_input_tokens") or 0)
                out += int(u.get("output_tokens") or 0)
                content = msg.get("content") or []
                if isinstance(content, list) and any(
                        isinstance(b, dict) and b.get("type") == "tool_use" for b in content):
                    acted += 1
    except OSError as exc:
        return {"state": "UNMEASURED", "reason": f"unreadable: {exc!r}"}
    if calls == 0:
        if refusal is not None:
            return {"state": "PROVIDER_REFUSED", "reason": refusal}
        return {"state": "UNMEASURED", "reason": "no model call with usage"}
    return {"state": "MEASURED", "model": model, "calls": calls, "tool_calls": acted,
            "input_tokens": inp + cwrite + cread, "output_tokens": out,
            "cache_read_tokens": cread, "fresh_input_tokens": inp + cwrite}


def build_attempts(events: list[dict], usage_of=None, since: float | None = None) -> tuple[list[dict], list[dict]]:
    """Ledger events -> (vendor attempt records, unjudged runs). Pure given `usage_of`."""
    usage_of = usage_of or (lambda sid: transcript_usage(lr.find_transcript(sid)))
    by_mission: dict[str, list[dict]] = {}
    for e in events:
        mid = e.get("mission_id")
        if isinstance(mid, str) and mid.startswith("m-") and e.get("session_id") == mid:
            by_mission.setdefault(mid, []).append(e)
        elif isinstance(mid, str) and mid.startswith("m-") and e.get("event") in WORKER_EVENTS:
            by_mission.setdefault(mid, []).append(e)
    attempts: list[dict] = []
    unjudged: list[dict] = []
    for mid, evs in sorted(by_mission.items()):
        evs.sort(key=lambda e: _ts(e.get("ts")) or 0.0)
        command = next((e.get("command") for e in evs if e.get("event") == "mission_prepared"), None)
        epochs: dict[int, dict] = {}
        ends: list[float] = []
        for e in evs:
            ep = e.get("epoch")
            t = _ts(e.get("ts"))
            if e.get("event") in ("launch_claimed",) + TERMINAL_EVENTS and t is not None:
                ends.append(t)
            if not isinstance(ep, int):
                continue
            slot = epochs.setdefault(ep, {"launches": [], "worker": None, "cause": None,
                                          "mechanism": None, "code": None, "quota": False})
            if e.get("event") == "launched" and t is not None:
                slot["launches"].append(t)
            elif e.get("event") in WORKER_EVENTS and e.get("worker"):
                slot["worker"] = e["worker"]
            elif e.get("event") == "launch_cause" and slot["cause"] is None:
                # The epoch's route is the cause that CREATED it. A same-session continuation
                # records a later cause on the same epoch; letting it overwrite reported a fresh
                # epoch under TURN_CONTINUATION/resume (red team R1, 2026-09-28).
                slot["cause"], slot["mechanism"] = e.get("cause"), e.get("mechanism")
            elif e.get("event") == "quota_held":
                slot["quota"] = True
            if e.get("code") and not slot["code"]:
                slot["code"] = e.get("code")
        for ep in sorted(epochs):
            slot = epochs[ep]
            if not slot["launches"] or (since and slot["launches"][0] < since):
                continue
            use = usage_of(slot["worker"]) if slot["worker"] else {"state": "UNMEASURED", "reason": "no worker acked"}
            model = use.get("model") or UNKNOWN
            cause = slot["cause"] or UNKNOWN
            route = f"{cause}/{slot['mechanism'] or UNKNOWN}:{model}"
            run_id = f"{mid}#e{ep}"
            if use["state"] == "MEASURED":
                status = "passed" if use["tool_calls"] > 0 else "failed"
            elif use["state"] == "PROVIDER_REFUSED" or slot["quota"]:
                status = "failed"
            else:
                status = None
            if status is None:
                unjudged.append({"runId": run_id, "route": route, "reason": use.get("reason")})
                continue
            complete = slot["cause"] is not None
            n = len(slot["launches"])
            for i, t0 in enumerate(slot["launches"], start=1):
                later = [t for t in ends + slot["launches"][i:] if t > t0]
                last = i == n
                rec = {"attemptId": f"{run_id}#a{i}", "runId": run_id, "taskId": run_id,
                       "taskType": "mission-epoch", "contractId": (command or UNKNOWN)[:256],
                       "contractVersion": slot["code"] or UNKNOWN, "route": route, "sequence": i,
                       # A relaunch inside one epoch, or a recovery from a dead worker, is a retry.
                       "phase": "retry" if (i > 1 or cause == "PROCESS_RECOVERY") else "initial",
                       "status": status if last else "failed",
                       "historyComplete": complete,
                       "latencyMs": round((min(later) - t0) * 1000) if later else None,
                       "usage": ({"inputTokens": use["input_tokens"], "outputTokens": use["output_tokens"],
                                  "totalTokens": use["input_tokens"] + use["output_tokens"], "costUsd": None}
                                 if last and use["state"] == "MEASURED" else None),
                       "_cacheReadTokens": use.get("cache_read_tokens") if last else None}
                attempts.append(rec)
    return attempts, unjudged


def analyze(attempts: list[dict], baseline: str | None = None, candidate: str | None = None) -> dict:
    vendor = [{k: v for k, v in a.items() if not k.startswith("_")} for a in attempts]
    opts = {"baselineRoute": baseline, "candidateRoute": candidate} if baseline and candidate else {}
    r = nb.call("routingMetrics", "analyzeRoutingMetrics", [vendor, opts], timeout=60)
    if not r.ok:
        return {"outcome": r.outcome, "error": r.error}
    value = r.value
    cache: dict[str, int] = {}
    for a in attempts:
        if a.get("_cacheReadTokens") is not None:
            cache[a["route"]] = cache.get(a["route"], 0) + a["_cacheReadTokens"]
    for g in value.get("groups", []):
        g["cacheReadTokensObserved"] = cache.get(g["route"])
    return {"outcome": "OK", "value": value}


def report(mission: str | None = None, since: str | None = None) -> dict:
    events = lr.ledger_events()
    if mission:
        events = [e for e in events if e.get("mission_id") == mission]
    since_ts = _ts(since) if since else None
    attempts, unjudged = build_attempts(events, since=since_ts)
    out = {"attempts": len(attempts), "unjudged_runs": unjudged}
    if not attempts:
        out["analysis"] = {"outcome": "EMPTY", "error": "no judgeable attempt in scope"}
        return out
    out["analysis"] = analyze(attempts)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Routing metrics per cpp-gsd-long continuation route")
    ap.add_argument("--mission")
    ap.add_argument("--since", help="ISO date; epochs launched before it are skipped")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    r = report(a.mission, a.since)
    an = r["analysis"]
    if a.json:
        print(json.dumps(r, indent=1))
    elif an.get("outcome") != "OK":
        print(f"routing metrics {an.get('outcome')}: {an.get('error')}  (unjudged runs: {len(r['unjudged_runs'])})")
    else:
        print(f"attempts={r['attempts']}  unjudged_runs={len(r['unjudged_runs'])}")
        for g in an["value"]["groups"]:
            m = g["metrics"]
            print(f"  {g['route']:<52} runs={g['runCount']:>3} pass={g['successfulRuns']:>3} "
                  f"fail={g['failedRuns']:>3} complete={g['historyComplete']!s:<5} "
                  f"in_obs={m['inputTokens']['observedTotal']} out_obs={m['outputTokens']['observedTotal']} "
                  f"cache_read={g['cacheReadTokensObserved']}")
    return 0 if an.get("outcome") in ("OK", "EMPTY") else 2


if __name__ == "__main__":
    sys.exit(main())
