"""Fresh Context Tax: what a NEW mission worker session costs before it does anything useful.

Measured from the workers' own transcripts, never estimated from configuration:

  bootstrap_tokens        resident at the worker's FIRST model call (input + cache write + cache read)
  first_prompt_chars      characters of the first user message (the mission prompt / card); its
                          token share is an ESTIMATE (chars/4) and is labelled so
  fixed_tokens_est        bootstrap_tokens - first_prompt_tokens_est (system, tools, CLAUDE.md, hooks)
  tokens_at_first_action  resident at the first model call that issued a tool_use
  secs_to_first_action    first transcript row -> first tool_use row
  pct_of_window           bootstrap_tokens / --window (default 1,000,000; the window is a parameter)

One distinct worker session = one paid bootstrap; a same-session continuation pays none, and is
counted separately. A worker whose transcript cannot be found or has no usage is UNMEASURED and
excluded from every average -- it is never a zero.

    python tools/fresh_context_tax.py [--mission m-...] [--window 1000000] [--json]
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_long_run as lr  # noqa: E402

WORKER_EVENTS = ("worker_acked", "worker_adopted")


def _ts(v) -> float | None:
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00")).timestamp() if v else None
    except ValueError:
        return None


def _usage_total(u: dict) -> int | None:
    try:
        return int(u.get("input_tokens") or 0) + int(u.get("cache_creation_input_tokens") or 0) \
            + int(u.get("cache_read_input_tokens") or 0)
    except (TypeError, ValueError):
        return None


def _text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def measure_session(session_id: str, window: int, find=None) -> dict:
    find = find or lr.find_transcript
    path = find(session_id)
    if not path:
        return {"session": session_id, "state": "UNMEASURED", "reason": "transcript not found"}
    first_ts = first_prompt = boot = act_tokens = act_ts = refusal = None
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(row, dict):
                    continue
                t = _ts(row.get("timestamp"))
                if first_ts is None and t is not None:
                    first_ts = t
                msg = row.get("message") if isinstance(row.get("message"), dict) else {}
                if first_prompt is None and row.get("type") == "user" and not row.get("isMeta"):
                    txt = _text(msg.get("content"))
                    if txt:
                        first_prompt = txt
                if row.get("type") != "assistant":
                    continue
                if msg.get("model") == "<synthetic>":
                    # Not a model call: the host's own reply (quota refusal, API error). Measured
                    # 2026-09-28: 389 of 445 worker sessions' first reply was the weekly-limit
                    # refusal with zeroed usage -- read as "bootstrap 0 tokens" it hid the churn.
                    if boot is None and refusal is None:
                        refusal = _text(msg.get("content"))[:160]
                    continue
                u = msg.get("usage")
                total = _usage_total(u) if isinstance(u, dict) else None
                if boot is None and total is not None:
                    boot = total
                content = msg.get("content") or []
                if act_tokens is None and isinstance(content, list) and any(
                        isinstance(b, dict) and b.get("type") == "tool_use" for b in content):
                    act_tokens, act_ts = total, t
                if boot is not None and act_tokens is not None:
                    break
    except OSError as exc:
        return {"session": session_id, "state": "UNMEASURED", "reason": f"unreadable: {exc!r}"}
    if boot is None:
        if refusal is not None:
            return {"session": session_id, "state": "PROVIDER_REFUSED", "reason": refusal, "transcript": str(path)}
        return {"session": session_id, "state": "UNMEASURED", "reason": "no model call with usage"}
    chars = len(first_prompt or "")
    prompt_est = -(-chars // 4) if chars else 0
    return {"session": session_id, "state": "MEASURED", "transcript": str(path),
            "bootstrap_tokens": boot, "first_prompt_chars": chars, "first_prompt_tokens_est": prompt_est,
            "fixed_tokens_est": max(0, boot - prompt_est), "tokens_at_first_action": act_tokens,
            "secs_to_first_action": round(act_ts - first_ts, 1) if (act_ts and first_ts) else None,
            "pct_of_window": round(100.0 * boot / window, 2)}


def workers_by_mission(mission: str | None = None) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for e in lr.ledger_events():
        mid = e.get("mission_id") or e.get("session_id")
        if not str(mid).startswith("m-") or e.get("event") not in WORKER_EVENTS or not e.get("worker"):
            continue
        if mission and mid != mission:
            continue
        lst = out.setdefault(mid, [])
        if e["worker"] not in lst:
            lst.append(e["worker"])
    return out


def continuations_by_mission() -> dict[str, int]:
    out: dict[str, int] = {}
    for e in lr.ledger_events():
        if e.get("event") == "turn_continued":
            mid = e.get("mission_id") or e.get("session_id")
            out[mid] = out.get(mid, 0) + 1
    return out


def report(mission: str | None, window: int) -> dict:
    per_mission = workers_by_mission(mission)
    conts = continuations_by_mission()
    rows, missions = [], []
    for mid, workers in per_mission.items():
        ms = [measure_session(w, window) | {"mission": mid} for w in workers]
        rows.extend(ms)
        got = [m for m in ms if m["state"] == "MEASURED"]
        refused = sum(1 for m in ms if m["state"] == "PROVIDER_REFUSED")
        missions.append({"mission": mid, "fresh_sessions": len(workers), "measured": len(got),
                         "provider_refused": refused, "unmeasured": len(workers) - len(got) - refused,
                         "repeated_bootstrap_tokens": sum(m["bootstrap_tokens"] for m in got) if got else None,
                         "same_session_continuations": conts.get(mid, 0)})
    got = [r for r in rows if r["state"] == "MEASURED"]

    def dist(key):
        vals = [r[key] for r in got if r.get(key) is not None]
        if not vals:
            return None
        return {"n": len(vals), "median": statistics.median(vals), "min": min(vals), "max": max(vals)}

    refused = sum(1 for r in rows if r["state"] == "PROVIDER_REFUSED")
    return {"window": window, "sessions": len(rows), "measured": len(got), "provider_refused": refused,
            "unmeasured": len(rows) - len(got) - refused,
            "bootstrap_tokens": dist("bootstrap_tokens"), "fixed_tokens_est": dist("fixed_tokens_est"),
            "first_prompt_tokens_est": dist("first_prompt_tokens_est"),
            "tokens_at_first_action": dist("tokens_at_first_action"),
            "secs_to_first_action": dist("secs_to_first_action"), "pct_of_window": dist("pct_of_window"),
            "missions": missions, "rows": rows}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Fresh Context Tax per mission worker session")
    ap.add_argument("--mission")
    ap.add_argument("--window", type=int, default=1_000_000)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    r = report(a.mission, a.window)
    if a.json:
        print(json.dumps(r, indent=1))
    else:
        print(json.dumps({k: v for k, v in r.items() if k not in ("rows", "missions")}, indent=1))
        print(f"missions={len(r['missions'])}")
    return 0 if r["measured"] else 3


if __name__ == "__main__":
    sys.exit(main())
