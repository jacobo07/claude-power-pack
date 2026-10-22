#!/usr/bin/env python
"""Boundary ledger (CCR v5 E2): where a unit's model calls went, read from its own transcripts.

Plan vault/plans/ccr-v5-economic-kernel-2026-10-15.md section 2, R2: about half the calls of a unit
rediscover code (gsd_mission.py was paged 24x in one session). Every call re-reads the whole context,
so a call is the unit of cost; this tool classifies calls and names the files read more than once.

  boundary_ledger.py ledger --transcript T.jsonl [--transcript ...]     per-transcript table + pooled
  boundary_ledger.py suggest --transcript T.jsonl ... [--margin 0.25]   call-profile PGO: a max_calls to lease

PGO = profile-guided: the suggested cap comes from MEASURED call counts of finished units (p80 x
(1 + margin)); the margin is a chosen value, not a measured one. Fewer than MIN_SAMPLES units gives no
suggestion (absence of a profile is not a profile). Pure and read-only; no model call.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

DISCOVERY = frozenset({"Read", "Grep", "Glob"})
WRITE = frozenset({"Edit", "Write", "NotebookEdit"})
TEST_RE = re.compile(r"\b(pytest|test_\w+\.py|npm (run )?test|unittest)\b")
MIN_SAMPLES = 3
DEFAULT_MARGIN = 0.25


def read_calls(path: Path | str) -> list[dict]:
    """Distinct model calls of a transcript, in order: {id, ts, tools:[(name, subject)]}. A call is a
    message id; its content blocks arrive on several rows and are merged. Synthetic rows are skipped."""
    calls: dict[str, dict] = {}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if '"usage"' not in line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            m = r.get("message") or {}
            if not m.get("usage") or m.get("model") == "<synthetic>":
                continue
            cid = m.get("id") or r.get("uuid")
            c = calls.setdefault(cid, {"id": cid, "ts": r.get("timestamp"), "tools": []})
            content = m.get("content")
            for blk in content if isinstance(content, list) else []:
                if isinstance(blk, dict) and blk.get("type") == "tool_use":
                    inp = blk.get("input") or {}
                    subject = inp.get("file_path") or inp.get("path") or inp.get("pattern") or inp.get("command") or ""
                    c["tools"].append((str(blk.get("name")), str(subject)))
    return list(calls.values())


def ledger(calls: list[dict]) -> dict:
    """Classify calls. discovery = every tool of the call is Read/Grep/Glob; write = any Edit/Write; test =
    a Bash command that runs a test; parallel = two or more tools in one call. `rereads` = files Read
    in 2+ calls; `reread_calls` = the calls beyond the first that read an already-read file."""
    n = len(calls)
    disc = write = test = par = 0
    seen: dict[str, int] = {}
    reread_calls = 0
    for c in calls:
        names = [t for t, _ in c["tools"]]
        disc += bool(names) and all(t in DISCOVERY for t in names)
        write += any(t in WRITE for t in names)
        test += any(t == "Bash" and TEST_RE.search(s) for t, s in c["tools"])
        par += len(names) >= 2
        hit = False
        for t, s in c["tools"]:
            if t == "Read" and s:
                seen[s] = seen.get(s, 0) + 1
                hit = hit or seen[s] > 1
        reread_calls += hit
    rereads = {f: k for f, k in sorted(seen.items(), key=lambda kv: -kv[1]) if k > 1}
    return {"calls": n, "discovery_calls": disc, "write_calls": write, "test_calls": test,
            "parallel_calls": par, "reread_calls": reread_calls,
            "rediscovery_ratio": round(reread_calls / n, 3) if n else None,
            "rereads": rereads}


def pool(ledgers: list[dict]) -> dict:
    out = {k: sum(l[k] for l in ledgers) for k in
           ("calls", "discovery_calls", "write_calls", "test_calls", "parallel_calls", "reread_calls")}
    out["rediscovery_ratio"] = round(out["reread_calls"] / out["calls"], 3) if out["calls"] else None
    return out


def suggest_max_calls(call_counts: list[int], margin: float = DEFAULT_MARGIN) -> dict:
    """PGO: p80 of measured per-unit call counts x (1 + margin), rounded up. None below MIN_SAMPLES."""
    if margin < 0:
        raise ValueError("margin must be >= 0")
    counts = sorted(int(c) for c in call_counts if isinstance(c, int) and not isinstance(c, bool) and c > 0)
    if len(counts) < MIN_SAMPLES:
        return {"max_calls": None, "n": len(counts),
                "reason": f"{len(counts)} measured unit(s) < {MIN_SAMPLES}: no call profile to suggest from"}
    p80 = counts[min(len(counts) - 1, math.ceil(0.8 * len(counts)) - 1)]
    return {"max_calls": math.ceil(round(p80 * (1 + margin), 6)), "n": len(counts), "p80": p80,
            "margin": margin, "reason": None}


def _main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="boundary_ledger")
    ap.add_argument("cmd", choices=["ledger", "suggest"])
    ap.add_argument("--transcript", action="append", required=True)
    ap.add_argument("--margin", type=float, default=DEFAULT_MARGIN)
    args = ap.parse_args(argv)
    ledgers = []
    for t in args.transcript:
        calls = read_calls(t)
        if calls:
            ledgers.append({"transcript": Path(t).name, **ledger(calls)})
    if args.cmd == "suggest":
        print(json.dumps(suggest_max_calls([l["calls"] for l in ledgers], args.margin), indent=1))
        return 0
    print(json.dumps({"pooled": pool(ledgers), "transcripts": [{**l, "rereads": dict(list(l["rereads"].items())[:5])}
                                                              for l in ledgers]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
