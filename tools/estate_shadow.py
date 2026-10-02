#!/usr/bin/env python3
"""estate_shadow.py -- C3 shadow replay of the estate spawn governor.

Plan: vault/plans/cognitive-control-plane-2026-10-02.md section 11 (C3).
Decider: modules/cognitive_os/scheduler.py::decide_spawn (pure, SHADOW ONLY).
Data: the usage index (tools/usage_index.py) with C2 ancestry. No model call.
Nothing here blocks, defers or alters a launch: it answers what the policy WOULD
have done to every recorded spawn.

Bands are frozen from a BASELINE window that precedes and excludes the judged one,
so the replay cannot tune its own thresholds (anti-Goodhart, audit G6/G10).

Avoidable cost is reported as the subtree cost of WOULD_DEFER spawns: an UPPER
BOUND on what deferral touches, never a saving -- a deferred spawn may simply run
later, and its work may have been needed.

CLI:
  replay [--baseline-from ISO --baseline-to ISO] [--from ISO --to ISO] [--out PATH]
"""
from __future__ import annotations

import argparse
import bisect
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PP = _HERE.parent
for _p in (str(_HERE), str(_PP)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import fanout_ledger as fl  # noqa: E402
import usage_index as ux  # noqa: E402
from modules.cognitive_os import scheduler as S  # noqa: E402

ACTIVE_S = 600          # a session/subagent is active if it made a call in the last 10 min
DIMS = ("active_sessions", "active_subagents", "calls_per_h")


class Estate:
    """Sliding-window estate load from the call index (ts-sorted arrays)."""

    def __init__(self, con, start: float, end: float):
        rows = con.execute("SELECT ts, file, is_sub FROM calls WHERE ts > ? AND ts <= ? "
                           "ORDER BY ts", (start - 3600, end)).fetchall()
        self.ts = [r[0] for r in rows]
        self.file = [r[1] for r in rows]
        self.sub = [r[2] for r in rows]

    def load(self, t: float) -> dict:
        lo = bisect.bisect_right(self.ts, t - ACTIVE_S)
        hi = bisect.bisect_right(self.ts, t)
        sess = {self.file[i] for i in range(lo, hi) if not self.sub[i]}
        subs = {self.file[i] for i in range(lo, hi) if self.sub[i]}
        h0 = bisect.bisect_right(self.ts, t - 3600)
        return {"active_sessions": len(sess), "active_subagents": len(subs),
                "calls_per_h": hi - h0}


def _pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * (len(xs) - 1)))] if xs else None


def spawns_in(con, start: float, end: float) -> list[dict]:
    """Recorded spawns in (start, end] with root class, ordinal within their
    prompt, and the cost of the subagent transcript they produced."""
    prompts = {r[0]: r[1:] for r in con.execute(
        "SELECT p.prompt_id, p.kind, p.source, f.title, f.entrypoint "
        "FROM prompts p LEFT JOIN files f ON f.path = p.file")}
    sub_cost = {r[0]: (r[1], r[2] or 0) for r in con.execute(
        "SELECT s.tool_use_id, count(c.k), sum(c.cr) FROM subagents s "
        "LEFT JOIN calls c ON c.file = s.file GROUP BY s.tool_use_id")}
    seen = Counter()
    out = []
    for tuid, ts, stype, pid, pfile in con.execute(
            "SELECT tool_use_id, ts, subagent_type, prompt_id, file FROM spawns "
            "WHERE ts IS NOT NULL ORDER BY ts"):
        seen[pid] += 1                      # ordinal counts spawns BEFORE the window too
        if not (start < ts <= end):
            continue
        pr = prompts.get(pid)
        root = fl.classify_root(pr[0], pr[1], pr[3], pr[2]) if pr else "UNKNOWN"
        calls, cr = sub_cost.get(tuid, (None, None))
        out.append({"tool_use_id": tuid, "ts": ts, "agent_type": stype, "prompt": pid,
                    "root": root, "ordinal": seen[pid], "project": fl.project_of(pfile),
                    "nested": "subagents" in Path(pfile).parts,
                    "subtree_calls": calls, "subtree_cache_read": cr})
    return out


def bands_from(con, b0: float, b1: float) -> dict:
    est = Estate(con, b0, b1)
    sp = spawns_in(con, b0, b1)
    loads = [est.load(s["ts"]) for s in sp]
    per_prompt = Counter(s["prompt"] for s in sp if s["prompt"])
    return {"window": [ux._iso(b0), ux._iso(b1)], "spawns": len(sp),
            "p90": {d: _pct([l[d] for l in loads], 0.90) for d in DIMS},
            "p99": {d: _pct([l[d] for l in loads], 0.99) for d in DIMS},
            "prompt_spawns_p90": _pct(list(per_prompt.values()), 0.90)}


def replay(con, b0, b1, start, end) -> dict:
    if not b1 <= start:     # here, not only in the CLI: no caller may tune on the judged window
        raise ValueError("the baseline must end before the judged window starts")
    bands = bands_from(con, b0, b1)
    if not bands["spawns"]:
        return {"verdict": "UNMEASURED", "reason": "no spawns in the baseline window",
                "bands": bands}
    est = Estate(con, start, end)
    sp = spawns_in(con, start, end)
    table = Counter()
    deferred_cost = Counter()
    first_defer = None
    timeline = defaultdict(Counter)
    review = []
    for s in sp:
        prio = S.spawn_priority(s["root"], s["agent_type"])
        load = est.load(s["ts"])
        v = S.decide_spawn(prio, load, s["ordinal"], bands)
        table[(prio, v.verdict)] += 1
        timeline[ux._iso(s["ts"] - s["ts"] % (4 * 3600))][v.verdict] += 1
        if v.verdict == S.SPAWN_WOULD_DEFER:
            first_defer = first_defer or s["ts"]
            deferred_cost["spawns"] += 1
            deferred_cost["subtree_calls"] += s["subtree_calls"] or 0
            deferred_cost["subtree_cache_read"] += s["subtree_cache_read"] or 0
            deferred_cost["no_transcript"] += s["subtree_calls"] is None
            review.append(dict(s, priority=prio, reasons=v.reasons, load=load))
    review.sort(key=lambda r: -(r["subtree_cache_read"] or 0))
    protected_deferred = sum(n for (p, verdict), n in table.items()
                             if p in S.PROTECTED and verdict == S.SPAWN_WOULD_DEFER)
    return {
        "status": "SHADOW (no launch was or will be changed)",
        "bands": bands,
        "judged": {"window": [ux._iso(start), ux._iso(end)], "spawns": len(sp),
                   "nested_spawns": sum(s["nested"] for s in sp)},
        "verdicts": {f"{p} / {v}": n for (p, v), n in sorted(table.items())},
        "protected_deferred": protected_deferred,
        "first_would_defer": ux._iso(first_defer) if first_defer else None,
        "deferred_subtree_upper_bound": dict(deferred_cost),
        "timeline_4h": {k: dict(v) for k, v in sorted(timeline.items())},
        "false_positive_review_top15": [
            {k: r[k] for k in ("tool_use_id", "agent_type", "root", "priority", "project",
                               "ordinal", "subtree_calls", "subtree_cache_read", "reasons")}
            | {"at": ux._iso(r["ts"])} for r in review[:15]],
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("cmd", choices=["replay"])
    ap.add_argument("--db", default=str(ux.DEFAULT_DB))
    ap.add_argument("--baseline-from", default="2026-09-16T17:00:00Z")
    ap.add_argument("--baseline-to", default="2026-09-30T17:00:00Z")
    ap.add_argument("--from", dest="start", default="2026-09-30T17:00:00Z")
    ap.add_argument("--to", dest="end", default="2026-10-02T09:40:00Z")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    b0, b1 = ux._epoch(a.baseline_from), ux._epoch(a.baseline_to)
    s, e = ux._epoch(a.start), ux._epoch(a.end)
    if not (b1 <= s):
        ap.error("the baseline must end before the judged window starts")
    con = ux.connect(Path(a.db))
    res = replay(con, b0, b1, s, e)
    text = json.dumps(res, indent=1, default=str)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
