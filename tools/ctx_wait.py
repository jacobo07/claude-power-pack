"""Phase 6 (W5): classify model calls made while a unit was WAITING, count and cost them. Shadow only: never blocks.

    python3 tools/ctx_wait.py classify <transcript.jsonl ...>

A call is the set of tool_use blocks sharing one assistant message.id (usage carries the call's processed input).
Classes (a call gets the first that matches, in this order):
  WAIT_SLEEP    Bash whose command sleeps / polls / watches (sleep N, until..., watch, tail -f, gh run watch, wait)
  WAIT_NOTIFY   Monitor / TaskOutput / TaskGet / TaskList / ScheduleWakeup / CronList: asking the harness for status
  WAIT_REASK    a Bash/Read call whose (tool, input) is byte-identical to the previous call's (a status re-ask)
  WORK          anything else, including calls with no tool_use (text-only turns are not waiting evidence)
Cost per call = processed input (input + cache_read + cache_creation) + output, exactly as the provider reported.
The classification is a HEURISTIC over command text (APPROX); processed counts are measured.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SLEEP_RE = re.compile(r'(^|[;&|\s("])(sleep\s+\d|until\s|watch\s|tail\s+-[a-zA-Z]*f|gh\s+run\s+watch|wait(\s|$)|Start-Sleep|timeout\s+\d+\s+tail)')
NOTIFY_TOOLS = {"Monitor", "TaskOutput", "TaskGet", "TaskList", "ScheduleWakeup", "CronList"}
REASK_TOOLS = {"Bash", "Read"}
CLASSES = ("WAIT_SLEEP", "WAIT_NOTIFY", "WAIT_REASK", "WORK")


def calls_of(path: Path) -> list[dict]:
    """[{mid, processed, output, uses:[(name, input_json)]}] in order, one per distinct message.id with usage."""
    order: list[str] = []
    by: dict[str, dict] = {}
    with open(path, encoding="utf-8", errors="replace") as f:
        for ln in f:
            try:
                e = json.loads(ln)
            except ValueError:
                continue
            msg = e.get("message")
            if e.get("type") != "assistant" or not isinstance(msg, dict) or not msg.get("id"):
                continue
            mid = msg["id"]
            c = by.get(mid)
            if c is None:
                c = by[mid] = {"mid": mid, "processed": None, "output": 0, "uses": []}
                order.append(mid)
            u = msg.get("usage")
            if u and c["processed"] is None:
                c["processed"] = (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
                c["output"] = u.get("output_tokens") or 0
            content = msg.get("content")
            for b in content if isinstance(content, list) else []:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    c["uses"].append((b.get("name") or "", json.dumps(b.get("input"), sort_keys=True, ensure_ascii=False)))
    return [by[m] for m in order if by[m]["processed"] is not None]


def classify_call(uses: list[tuple[str, str]], prev_uses: list[tuple[str, str]] | None) -> str:
    for name, inp in uses:
        if name == "Bash" and SLEEP_RE.search(inp):
            return "WAIT_SLEEP"
    if uses and all(n in NOTIFY_TOOLS for n, _ in uses):
        return "WAIT_NOTIFY"
    if uses and prev_uses and uses == prev_uses and all(n in REASK_TOOLS for n, _ in uses):
        return "WAIT_REASK"
    return "WORK"


def classify(path: Path) -> dict:
    cost = {c: {"calls": 0, "processed": 0, "output": 0} for c in CLASSES}
    prev = None
    calls = calls_of(path)
    for c in calls:
        k = classify_call(c["uses"], prev)
        cost[k]["calls"] += 1
        cost[k]["processed"] += c["processed"]
        cost[k]["output"] += c["output"]
        prev = c["uses"] or None
    n = len(calls)
    proc = sum(c["processed"] for c in calls)
    wait_calls = sum(cost[k]["calls"] for k in CLASSES[:3])
    wait_proc = sum(cost[k]["processed"] for k in CLASSES[:3])
    return {"calls": n, "processed": proc, "by_class": cost, "wait_calls": wait_calls, "wait_processed": wait_proc,
            "wait_call_share": round(wait_calls / n, 4) if n else None,
            "wait_processed_share": round(wait_proc / proc, 4) if proc else None}


def shadow_admission(stats: dict) -> dict:
    """SHADOW advisory for ccr_pgo admission: what a wait-aware gate WOULD flag. Verdict never changes (shadow proves safety, not savings)."""
    share = stats.get("wait_processed_share")
    if share is None:
        return {"shadow": True, "would_flag": None, "reason": "no calls: UNMEASURED, not zero"}
    flag = share >= 0.10
    return {"shadow": True, "would_flag": flag, "wait_processed_share": share,
            "reason": (f"{share:.1%} of processed tokens rode waiting calls: a wait-aware admission WOULD suggest a push-notified wait"
                       if flag else "waiting share under 10%: nothing to flag")}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("classify")
    c.add_argument("files", type=Path, nargs="+")
    a = ap.parse_args(argv)
    out = []
    for f in a.files:
        s = classify(f)
        out.append({"file": f.name, **s, "admission_shadow": shadow_admission(s)})
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
