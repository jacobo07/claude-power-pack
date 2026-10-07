#!/usr/bin/env python
"""a3_pane_autopsy.py -- A3-U1: per-call autopsy of coordinating panes. Zero model calls, stdlib only.

For each session id prefix it finds ~/.claude/projects/*/<prefix>*.jsonl (subagents under
<sid>/subagents/), dedups assistant lines by `message.id|requestId`, and reports per pane:
calls, processed (input + cache_creation + cache_read + output), first-call context (floor),
median / p90 context, growth slope, the calls-vs-rent split, tool_result share by tool,
repeated Reads, calls with no edit/shell effect, Agent spawns, and a labelled ESTIMATED
counterfactual. A missing transcript is UNKNOWN (null), never zero.

Tool categories come from measure/turns.py `tool_cat` (extended, not forked). tool_result sizes are
characters / 4 -- an ESTIMATE, the transcript carries no per-result token count.

Usage: python tools/a3_pane_autopsy.py [--root DIR] [--json OUT] [--md OUT] [sid-prefix ...]
Gate:  python tools/test_a3_pane_autopsy.py
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "vault" / "programs" / "cognitive-economy" / "measure"))
import turns  # noqa: E402

DEFAULT_PANES = ("423e33b0", "b9bd9469", "886d7bb9", "0f9b771b", "e6e0eca7")
FRESH_WORKER_FLOOR = 95_695          # measured, gen3
EFFECT_CATS = {"edit", "test", "git", "shell"}
CHARS_PER_TOKEN = 4


def find_transcript(prefix: str, root: Path):
    """(main jsonl or None, [subagent jsonl]) for a session id prefix."""
    hits = sorted(p for p in root.glob(f"*/{prefix}*.jsonl") if p.is_file())
    if not hits:
        return None, []
    main = hits[0]
    return main, sorted((main.with_suffix("") / "subagents").glob("*.jsonl"))


def _result_chars(c: dict) -> int:
    body = c.get("content")
    if isinstance(body, str):
        return len(body)
    if isinstance(body, list):
        return sum(len(b.get("text", "")) if isinstance(b, dict) and b.get("type") == "text"
                   else len(json.dumps(b, default=str)) for b in body)
    return 0 if body is None else len(json.dumps(body, default=str))


def load_calls(path, dedup: bool = True):
    """(calls, result_tokens_by_tool, reads) from one transcript. `dedup` exists so the gate can
    drive a red branch. A streamed message repeats its key: the LAST line's usage wins."""
    calls: list = []
    index: dict = {}
    tool_names: dict = {}            # tool_use id -> name
    res_chars = Counter()
    read_paths: list = []            # (path, tool_use id)
    with open(path, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            try:
                o = json.loads(raw)
            except ValueError:
                continue
            if not isinstance(o, dict):
                continue
            m = o.get("message") if isinstance(o.get("message"), dict) else {}
            content = m.get("content") if isinstance(m.get("content"), list) else []
            if o.get("type") == "user":
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "tool_result":
                        res_chars[c.get("tool_use_id")] += _result_chars(c)
                continue
            if o.get("type") != "assistant" or not isinstance(m.get("usage"), dict):
                continue
            u = m["usage"]
            key = f"{m.get('id')}|{o.get('requestId')}"
            row = {"key": key, "inp": u.get("input_tokens") or 0, "cw": u.get("cache_creation_input_tokens") or 0,
                   "cr": u.get("cache_read_input_tokens") or 0, "out": u.get("output_tokens") or 0, "tools": []}
            if dedup and key in index:
                prev = calls[index[key]]
                row["tools"] = prev["tools"]
                calls[index[key]] = row
            else:
                index[key] = len(calls)
                calls.append(row)
            seen_ids = {t["id"] for t in row["tools"]}
            for c in content:
                if not isinstance(c, dict) or c.get("type") != "tool_use" or c.get("id") in seen_ids:
                    continue
                name, inp = c.get("name"), c.get("input") if isinstance(c.get("input"), dict) else {}
                cat, _ = turns.tool_cat(name, inp)
                row["tools"].append({"id": c.get("id"), "name": name, "cat": cat})
                tool_names[c.get("id")] = name
                if name == "Read" and inp.get("file_path"):
                    read_paths.append((str(inp["file_path"]), c.get("id")))
    by_tool = Counter()
    for tid, n in res_chars.items():
        by_tool[tool_names.get(tid, "UNMATCHED")] += n // CHARS_PER_TOKEN
    return calls, dict(by_tool), read_paths, {t: n // CHARS_PER_TOKEN for t, n in res_chars.items()}


def p90(vals):
    s = sorted(vals)
    return s[max(0, -(-9 * len(s) // 10) - 1)]


def slope(ys):
    """Least-squares tokens per call of context against call index."""
    n = len(ys)
    if n < 2:
        return None
    mx, my = (n - 1) / 2, sum(ys) / n
    den = sum((i - mx) ** 2 for i in range(n))
    return sum((i - mx) * (y - my) for i, y in enumerate(ys)) / den


def analyze(path, subagents=(), dedup: bool = True) -> dict:
    calls, by_tool, read_paths, per_id = load_calls(path, dedup)
    if not calls:
        return {"status": "EMPTY", "calls": 0}
    ctx = [c["inp"] + c["cw"] + c["cr"] for c in calls]
    total = sum(ctx) + sum(c["out"] for c in calls)
    floor = ctx[0]
    growth = sum(ctx) - floor * len(ctx)
    effect = [c for c in calls if any(t["cat"] in EFFECT_CATS for t in c["tools"])]
    seen, rep_n, rep_tok = set(), 0, 0
    for p, tid in read_paths:
        if p in seen:
            rep_n += 1
            rep_tok += per_id.get(tid, 0)
        seen.add(p)
    tot_res = sum(by_tool.values())
    spawns = sum(1 for c in calls for t in c["tools"] if t["name"] == "Agent")
    sub_processed = None
    if spawns:
        sub_processed = None if not subagents else sum(
            sum(x["inp"] + x["cw"] + x["cr"] + x["out"] for x in load_calls(s, dedup)[0]) for s in subagents)
    cf = len(effect) * FRESH_WORKER_FLOOR + sum(c["out"] for c in effect)
    return {
        "status": "OK", "calls": len(calls), "processed": total, "floor": floor,
        "median_ctx": int(statistics.median(ctx)), "p90_ctx": p90(ctx),
        "slope_per_call": round(slope(ctx), 1) if slope(ctx) is not None else None,
        "split": {"floor_x_calls": floor * len(ctx), "growth_above_floor": growth,
                  "output": sum(c["out"] for c in calls),
                  "rent_share": round(growth / total, 4) if total else None},
        "tool_result_tokens_est": by_tool,
        "tool_result_share": {t: round(n / tot_res, 4) for t, n in sorted(by_tool.items(), key=lambda kv: -kv[1])}
        if tot_res else {},
        "repeated_reads": {"count": rep_n, "tokens_est": rep_tok},
        "no_effect_calls": len(calls) - len(effect), "effect_calls": len(effect),
        "agent_spawns": spawns, "subagent_files": len(subagents),
        "subagent_processed": sub_processed if spawns else 0,
        "counterfactual_est": {"label": "ESTIMATED", "floor": FRESH_WORKER_FLOOR, "processed": cf,
                               "saving": total - cf},
    }


def run(prefixes, root: Path) -> dict:
    out = {}
    for p in prefixes:
        main, subs = find_transcript(p, root)
        out[p] = {"status": "UNKNOWN", "reason": "transcript not found"} if main is None else analyze(main, subs)
    return out


def _f(v):
    return "UNKNOWN" if v is None else f"{v:,}" if isinstance(v, int) else str(v)


def render(res: dict) -> str:
    L = ["| pane | calls | processed | floor | median | p90 | slope/call | rent share | no-effect | repeat reads | spawns | CF saving (EST) |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for p, r in res.items():
        if r.get("status") != "OK":
            L.append(f"| {p} | UNKNOWN | " + " | ".join(["UNKNOWN"] * 10) + " |")
            continue
        L.append(f"| {p} | {_f(r['calls'])} | {_f(r['processed'])} | {_f(r['floor'])} | {_f(r['median_ctx'])} | "
                 f"{_f(r['p90_ctx'])} | {_f(r['slope_per_call'])} | {_f(r['split']['rent_share'])} | "
                 f"{_f(r['no_effect_calls'])} | {_f(r['repeated_reads']['count'])} | {_f(r['agent_spawns'])} | "
                 f"{_f(r['counterfactual_est']['saving'])} |")
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("panes", nargs="*", default=list(DEFAULT_PANES))
    ap.add_argument("--root", default=str(Path.home() / ".claude" / "projects"))
    ap.add_argument("--json")
    ap.add_argument("--md")
    a = ap.parse_args(argv)
    res = run(a.panes, Path(a.root))
    table = render(res)
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1, sort_keys=True), encoding="utf-8", newline="\n")
    if a.md:
        Path(a.md).write_text(table + "\n", encoding="utf-8", newline="\n")
    print(table)
    return 0 if all(r.get("status") == "OK" for r in res.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
