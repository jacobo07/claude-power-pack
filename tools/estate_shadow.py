#!/usr/bin/env python3
"""estate_shadow.py -- C3 shadow replay of the estate spawn governor.

Plan: vault/plans/cognitive-control-plane-2026-10-02.md section 11 (C3), s12 c8, s13.
Decider: modules/cognitive_os/scheduler.py::decide_spawn (pure, SHADOW ONLY) and its
challenger decide_spawn_v2. Data: the usage index (tools/usage_index.py) with C2
ancestry. No model call. Nothing here blocks, defers or alters a launch: it answers
what a policy WOULD have done to every recorded spawn.

Bands are frozen from a BASELINE window that precedes and excludes the judged one,
so the replay cannot tune its own thresholds (anti-Goodhart, audit G6/G10).

Avoidable cost is reported as the subtree cost of WOULD_DEFER spawns: an UPPER
BOUND on what deferral touches, never a saving -- a deferred spawn may simply run
later, and its work may have been needed.

replay-v2 judges the SAME spawns with v1 and v2, emits a policy receipt per v2
verdict (evidence class REPLAY: observational, never interventional), and
recommends NO_CHANGE unless v2's non-ALLOW set differs from v1's. Its own cost is
reported (wall seconds, index rows read): the controller must be cheaper than what
it could save, and it makes zero model calls.

CLI:
  replay    [--baseline-from ISO --baseline-to ISO] [--from ISO --to ISO] [--out PATH]
  replay-v2 [same window flags] [--out PATH] [--receipts PATH.jsonl]
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
NO_RESULT_ACTIVE_S = 3600   # a spawn that never recorded a result counts as running this long
ROOT_LOOKBACK_S = 2 * 86400  # root spend is counted over this lookback before the window


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
    prompt, and the cost of the subagent transcript they produced. A nested spawn's
    root is resolved transitively (s12 c5), never the spawning subagent's prompt."""
    prompts = {r[0]: r[1:] for r in con.execute(
        "SELECT p.prompt_id, p.kind, p.source, f.title, f.entrypoint "
        "FROM prompts p LEFT JOIN files f ON f.path = p.file")}
    sub_cost = {r[0]: (r[1], r[2] or 0) for r in con.execute(
        "SELECT s.tool_use_id, count(c.k), sum(c.cr) FROM subagents s "
        "LEFT JOIN calls c ON c.file = s.file GROUP BY s.tool_use_id")}
    have = {r[1] for r in con.execute("PRAGMA table_info(spawns)")}
    hcol = "input_hash" if "input_hash" in have else "NULL"
    resolve = fl.root_resolver(con)
    seen = Counter()
    out = []
    for tuid, ts, stype, pid, pfile, ihash in con.execute(
            f"SELECT tool_use_id, ts, subagent_type, prompt_id, file, {hcol} FROM spawns "
            "WHERE ts IS NOT NULL ORDER BY ts"):
        nested = "subagents" in Path(pfile).parts
        root_pid = resolve(pfile) if nested else pid
        seen[root_pid] += 1                 # ordinal counts spawns BEFORE the window too
        if not (start < ts <= end):
            continue
        pr = prompts.get(root_pid)
        root = fl.classify_root(pr[0], pr[1], pr[3], pr[2]) if pr else "UNKNOWN"
        calls, cr = sub_cost.get(tuid, (None, None))
        out.append({"tool_use_id": tuid, "ts": ts, "agent_type": stype, "prompt": root_pid,
                    "root": root, "ordinal": seen[root_pid], "project": fl.project_of(pfile),
                    "nested": nested, "input_hash": ihash,
                    "subtree_calls": calls, "subtree_cache_read": cr})
    return out


class Equivalents:
    """Spawns already running with the same input_hash at an instant. Running = no
    result recorded at or before t; a spawn that never recorded a result counts as
    running for NO_RESULT_ACTIVE_S. Pre-spawn data only (audit G7)."""

    def __init__(self, con):
        self.by_hash = defaultdict(list)
        for tuid, ts, h, rts in con.execute(
                "SELECT tool_use_id, ts, input_hash, result_ts FROM spawns "
                "WHERE input_hash IS NOT NULL AND ts IS NOT NULL ORDER BY ts"):
            self.by_hash[h].append((ts, tuid, rts))

    def active(self, h, t: float, tuid: str) -> int | None:
        if h is None:
            return None                      # unmeasured: never triggers
        return sum(1 for ts, other, rts in self.by_hash.get(h, ())
                   if other != tuid and ts < t
                   and ((rts is not None and rts > t)
                        or (rts is None and t - ts <= NO_RESULT_ACTIVE_S)))


class RootSpend:
    """Calls already charged to a root before an instant (lookback-bounded)."""

    def __init__(self, con, start: float, end: float):
        self.ts = defaultdict(list)
        for r in fl.load_calls(con, start - ROOT_LOOKBACK_S, end):
            if r["prompt"]:
                self.ts[r["prompt"]].append(r["ts"])
        for v in self.ts.values():
            v.sort()

    def before(self, prompt, t: float) -> int | None:
        if not prompt:
            return None
        return bisect.bisect_left(self.ts.get(prompt, []), t)


def bands_from(con, b0: float, b1: float) -> dict:
    est = Estate(con, b0, b1)
    sp = spawns_in(con, b0, b1)
    loads = [est.load(s["ts"]) for s in sp]
    per_prompt = Counter(s["prompt"] for s in sp if s["prompt"])
    spend = RootSpend(con, b0, b1)
    root_calls = [n for n in (spend.before(s["prompt"], s["ts"]) for s in sp) if n is not None]
    return {"window": [ux._iso(b0), ux._iso(b1)], "spawns": len(sp),
            "p90": {d: _pct([l[d] for l in loads], 0.90) for d in DIMS},
            "p99": {d: _pct([l[d] for l in loads], 0.99) for d in DIMS},
            "prompt_spawns_p90": _pct(list(per_prompt.values()), 0.90),
            "root_calls_p90": _pct(root_calls, 0.90)}


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


MAX_PROGRESS_ROOTS = 20     # discrimination check reads at most this many roots' transcripts


def recommend(changed: int, changed_states: dict) -> dict:
    """NO_CHANGE / REJECT / CHALLENGER for a challenger policy.

    A changed verdict is only worth having if it lands on work that did not
    advance. If every root a changed verdict touched ADVANCED (progress v1), the
    challenger cannot tell waste from progress: REJECT, recorded as negative
    evidence. Unjudged roots keep the result at CHALLENGER, never upgrade it."""
    if changed == 0:
        return {"verdict": "NO_CHANGE", "verdicts_changed": 0}
    advanced = sum(n for s, n in changed_states.items() if s.startswith("ADVANCED"))
    if advanced == changed:
        return {"verdict": "REJECT", "verdicts_changed": changed,
                "reason": "every changed verdict hit a root that advanced: no discrimination of waste"}
    return {"verdict": "CHALLENGER", "verdicts_changed": changed}


def replay_v2(con, b0, b1, start, end) -> dict:
    """v1 and v2 over the same spawns, a receipt per v2 verdict, and a recommendation.
    NO_CHANGE is a first-class result: v2 earns nothing if it judges like v1."""
    if not b1 <= start:
        raise ValueError("the baseline must end before the judged window starts")
    t0 = time.perf_counter()
    bands = bands_from(con, b0, b1)
    if not bands["spawns"]:
        return {"verdict": "UNMEASURED", "reason": "no spawns in the baseline window",
                "bands": bands}
    est = Estate(con, start, end)
    sp = spawns_in(con, start, end)
    eq = Equivalents(con)
    spend = RootSpend(con, start, end)
    transitions = Counter()
    by_prio = Counter()
    receipts = []
    unmeasured = Counter()
    upper = Counter()
    for s in sp:
        load = est.load(s["ts"])
        v1 = S.decide_spawn(S.spawn_priority(s["root"], s["agent_type"]), load, s["ordinal"], bands)
        prio = S.spawn_priority_v2(s["root"], s["agent_type"])
        feats = {"load": load, "prompt_spawns": s["ordinal"],
                 "equivalent_active": eq.active(s["input_hash"], s["ts"], s["tool_use_id"]),
                 "root_calls_before": spend.before(s["prompt"], s["ts"]),
                 "as_of": ux._iso(s["ts"]),
                 "sources": {"load": f"index calls, last {ACTIVE_S}s / 1h",
                             "equivalent_active": "index spawns.input_hash + result_ts <= t",
                             "root_calls_before": f"index calls of the root, {ROOT_LOOKBACK_S}s lookback",
                             "prompt_spawns": "index spawns ordinal within the root"}}
        for k in ("equivalent_active", "root_calls_before"):
            unmeasured[k] += feats[k] is None
        v2 = S.decide_spawn_v2(prio, load, s["ordinal"], bands,
                               equivalent_active=feats["equivalent_active"],
                               root_calls_before=feats["root_calls_before"])
        transitions[(v1.verdict, v2.verdict)] += 1
        by_prio[(prio, v2.verdict)] += 1
        effect = {"kind": "OBSERVED_SUBTREE (replay-only, not a prediction)",
                  "subtree_calls": s["subtree_calls"], "subtree_cache_read": s["subtree_cache_read"]}
        if v2.verdict != S.SPAWN_ALLOW:
            upper[v2.verdict] += s["subtree_cache_read"] or 0
        receipts.append(S.spawn_receipt(
            {"tool_use_id": s["tool_use_id"], "root_prompt": s["prompt"], "root_class": s["root"],
             "agent_type": s["agent_type"], "project": s["project"], "goal": "UNBOUND",
             "v1_verdict": v1.verdict},
            feats, bands, v2, "REPLAY", effect))
    protected_hit = sum(n for (p, verdict), n in by_prio.items()
                        if p in S.PROTECTED and verdict != S.SPAWN_ALLOW)
    changed = [r for r in receipts if r["subject"]["v1_verdict"] != r["verdict"]]
    # Discrimination check (replay-only: reads transcripts + git, never live): what
    # did the roots a changed verdict would have hit go on to do? (s12 c7 progress v1)
    import root_progress as rp                      # local: the live decider never needs it
    roots = sorted({r["subject"]["root_prompt"] for r in changed if r["subject"]["root_prompt"]})
    state_of = {p: rp.root_progress(con, p)["state"] for p in roots[:MAX_PROGRESS_ROOTS]}
    changed_states = Counter(state_of.get(r["subject"]["root_prompt"], "UNJUDGED") for r in changed)
    rec = recommend(len(changed), dict(changed_states))
    reconstructed = sum(S.replay_receipt(r).verdict == r["verdict"] for r in receipts)
    # Where would non-ALLOW work have gone (plan s14 S3)? Hindsight, so it runs only after
    # every receipt is final and is handed a fresh verdict map, never a receipt.
    import estate_displacement as ed                # local: the live decider never needs it
    verdict_of = {r["subject"]["tool_use_id"]: r["verdict"] for r in receipts}
    universe = spawns_in(con, start - ROOT_LOOKBACK_S, end + ed.LATER_HORIZON_S)
    disp = ed.displacement(con, sp, verdict_of, universe)
    return {
        "status": "SHADOW (no launch was or will be changed)",
        "policy": S.POLICY_V2, "bands_digest": S.bands_digest(bands), "bands": bands,
        "judged": {"window": [ux._iso(start), ux._iso(end)], "spawns": len(sp)},
        "v1_to_v2": {f"{a} -> {b}": n for (a, b), n in sorted(transitions.items())},
        "v2_by_priority": {f"{p} / {v}": n for (p, v), n in sorted(by_prio.items())},
        "protected_not_allowed_v2": protected_hit,
        "unknown_roots": sum(n for (p, _v), n in by_prio.items() if p == S.PRIO_UNKNOWN),
        "unmeasured_inputs": dict(unmeasured),
        "non_allow_subtree_cache_read_upper_bound": dict(upper),
        "receipts": {"total": len(receipts), "reproduced_from_receipt_alone": reconstructed},
        "recommendation": {**rec, "changed_root_progress": dict(changed_states),
                           "evidence": "REPLAY: observational; a CHALLENGER is a candidate for "
                                       "shadow, never a certified improvement"},
        "meta_overhead": {"wall_s": round(time.perf_counter() - t0, 2), "model_calls": 0,
                          "spawns_judged": len(sp)},
        "displacement": disp,
        "_receipts": receipts,
    }


def _window_args(ap):
    ap.add_argument("--db", default=str(ux.DEFAULT_DB))
    ap.add_argument("--baseline-from", default="2026-09-16T17:00:00Z")
    ap.add_argument("--baseline-to", default="2026-09-30T17:00:00Z")
    ap.add_argument("--from", dest="start", default="2026-09-30T17:00:00Z")
    ap.add_argument("--to", dest="end", default="2026-10-02T09:40:00Z")
    ap.add_argument("--out", default=None)
    ap.add_argument("--receipts", default=None)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("cmd", choices=["replay", "replay-v2"])
    _window_args(ap)
    a = ap.parse_args(argv)
    b0, b1 = ux._epoch(a.baseline_from), ux._epoch(a.baseline_to)
    s, e = ux._epoch(a.start), ux._epoch(a.end)
    if not (b1 <= s):
        ap.error("the baseline must end before the judged window starts")
    con = ux.connect(Path(a.db))
    res = replay(con, b0, b1, s, e) if a.cmd == "replay" else replay_v2(con, b0, b1, s, e)
    receipts = res.pop("_receipts", None)
    if a.receipts and receipts is not None:
        Path(a.receipts).parent.mkdir(parents=True, exist_ok=True)
        Path(a.receipts).write_text("".join(json.dumps(r) + "\n" for r in receipts),
                                    encoding="utf-8")
    text = json.dumps(res, indent=1, default=str)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
