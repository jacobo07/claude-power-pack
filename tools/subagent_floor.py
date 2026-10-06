#!/usr/bin/env python3
"""subagent_floor.py - read-only measurement of the first-call context of subagents, per agent type.

Python 3 stdlib only. Reads local Claude Code subagent transcripts and extracts ONLY the agent type and the
four usage integers of the first assistant message that carries usage. No message text is copied anywhere.

  context of a sample = input_tokens + cache_creation_input_tokens + cache_read_input_tokens
                        of the FIRST assistant message in the subagent jsonl
  grouped by agentType from the sibling <agent>.meta.json

Layout: <root>/<project>/<session>/subagents/agent-<id>.{meta.json,jsonl}
Window: --since-days N by jsonl modification time (the always-loaded prefix changes over time, so old samples
        would misstate the floor). --scope a,b keeps only projects whose directory name contains one of the
        substrings (the repos this mission runs in). --max-files caps the scan, newest first.

  subagent_floor.py [--root DIR] [--since-days 14] [--max-files 6000] [--scope InfinityOps,io-liveqa]
                    [--out PATH] [--list AGENT_TYPE] [--no-write]
  subagent_floor.py --self-test

Writes vault/config/subagent-floor.json (the only write) unless --no-write. The admission floor table
vault/config/route-floors.json is derived from that snapshot (its subagent floors are the snapshot's
`min`), and tools/test_route_admission.py fails when the two disagree: re-measure, then update both.

Provenance: promoted unchanged from InfinityOps io-liveqa 13f19a47
(vault/sidecar/live-qa/tools/subagent_floor.py, blob f266e134); only this docstring and DEFAULT_OUT moved.
"""
import argparse
import json
import math
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_OUT = HERE.parent / "vault" / "config" / "subagent-floor.json"
DEFAULT_ROOT = Path(os.path.expanduser("~")) / ".claude" / "projects"
MAX_LINES = 50
USAGE_KEYS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")


def first_context(jsonl_path, max_lines=MAX_LINES):
    """Context of the first assistant message that has a non-zero usage block, or None."""
    try:
        with open(jsonl_path, "r", encoding="utf-8", errors="replace") as fh:
            for i, line in enumerate(fh):
                if i >= max_lines:
                    break
                if '"usage"' not in line or '"assistant"' not in line:
                    continue
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(obj, dict) or obj.get("type") != "assistant":
                    continue
                msg = obj.get("message")
                usage = msg.get("usage") if isinstance(msg, dict) else None
                if not isinstance(usage, dict):
                    continue
                vals = []
                for k in USAGE_KEYS:
                    v = usage.get(k, 0)
                    vals.append(v if isinstance(v, int) and not isinstance(v, bool) else 0)
                total = sum(vals)
                if total <= 0:
                    continue
                return total
    except OSError:
        return None
    return None


def agent_type_of(jsonl_path):
    meta = Path(str(jsonl_path)[: -len(".jsonl")] + ".meta.json")
    try:
        with open(meta, "r", encoding="utf-8", errors="replace") as fh:
            obj = json.load(fh)
    except (OSError, ValueError):
        return None
    t = obj.get("agentType") if isinstance(obj, dict) else None
    return t if isinstance(t, str) and t else None


def nearest_rank(sorted_vals, q):
    n = len(sorted_vals)
    return sorted_vals[max(0, math.ceil(q * n) - 1)]


def summarize(vals):
    s = sorted(vals)
    return {"n": len(s), "min": s[0], "p50": nearest_rank(s, 0.5), "p90": nearest_rank(s, 0.9), "max": s[-1]}


def collect(root, since_days, max_files, scope, now=None, list_type=None):
    """Scan root. Returns (snapshot dict, listing rows for --list)."""
    now = time.time() if now is None else now
    cutoff = now - since_days * 86400
    cands = []
    excluded_old = 0
    excluded_scope = 0
    try:
        projects = [p for p in os.scandir(root) if p.is_dir()]
    except OSError:
        projects = []
    for proj in projects:
        in_scope = (not scope) or any(s in proj.name for s in scope)
        try:
            sessions = [s for s in os.scandir(proj.path) if s.is_dir()]
        except OSError:
            continue
        for sess in sessions:
            sub = os.path.join(sess.path, "subagents")
            try:
                entries = list(os.scandir(sub))
            except OSError:
                continue
            for e in entries:
                if not (e.name.startswith("agent-") and e.name.endswith(".jsonl")):
                    continue
                try:
                    mt = e.stat().st_mtime
                except OSError:
                    continue
                if mt < cutoff:
                    excluded_old += 1
                    continue
                cands.append((mt, e.path, in_scope))
    cands.sort(key=lambda t: -t[0])
    truncated = max(0, len(cands) - max_files)
    cands = cands[:max_files]
    by_scoped, by_all = {}, {}
    skipped = {"no_usage": 0, "no_meta": 0}
    scanned = 0
    rows = []
    for mt, path, in_scope in cands:
        scanned += 1
        ctx = first_context(path)
        if ctx is None:
            skipped["no_usage"] += 1
            continue
        atype = agent_type_of(path)
        if atype is None:
            skipped["no_meta"] += 1
            continue
        by_all.setdefault(atype, []).append(ctx)
        if in_scope:
            by_scoped.setdefault(atype, []).append(ctx)
            if list_type and atype == list_type:
                rows.append((os.path.basename(path), ctx, datetime.fromtimestamp(mt, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")))
        else:
            excluded_scope += 1
    snap = {
        "generated_at": datetime.fromtimestamp(now, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window_days": since_days,
        "scope": list(scope) if scope else "ALL",
        "samples_scanned": scanned,
        "skipped": sum(skipped.values()),
        "skipped_detail": skipped,
        "excluded_old": excluded_old,
        "excluded_out_of_scope": excluded_scope,
        "truncated_by_max_files": truncated,
        "unit": "first-call context = input_tokens + cache_creation_input_tokens + cache_read_input_tokens",
        "by_agent_type": {k: summarize(v) for k, v in sorted(by_scoped.items())},
        "by_agent_type_all_projects": {k: summarize(v) for k, v in sorted(by_all.items())},
    }
    return snap, rows


# ---------------------------------------------------------------- self-test

def _write_sample(root, project, session, agent_id, agent_type, usage_totals, age_days, with_usage=True, now=None):
    d = Path(root) / project / session / "subagents"
    d.mkdir(parents=True, exist_ok=True)
    jl = d / ("agent-%s.jsonl" % agent_id)
    meta = d / ("agent-%s.meta.json" % agent_id)
    meta.write_text(json.dumps({"agentType": agent_type, "model": "sonnet", "description": "SECRET-DESCRIPTION"}), encoding="utf-8")
    lines = [json.dumps({"type": "user", "message": {"role": "user", "content": "SECRET-PROMPT-TEXT"}})]
    if with_usage:
        # split the total across the three counters, with a zero-usage synthetic message first
        lines.append(json.dumps({"type": "assistant", "message": {"role": "assistant", "model": "<synthetic>",
                                 "content": [{"type": "text", "text": "SECRET-SYNTH"}],
                                 "usage": {"input_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}}}))
        inp = 10
        cc = usage_totals - inp - 1000
        cr = 1000
        lines.append(json.dumps({"type": "assistant", "message": {"role": "assistant",
                                 "content": [{"type": "text", "text": "SECRET-ANSWER"}],
                                 "usage": {"input_tokens": inp, "cache_creation_input_tokens": cc, "cache_read_input_tokens": cr, "output_tokens": 5}}}))
        # a later message with a different usage must NOT be used
        lines.append(json.dumps({"type": "assistant", "message": {"role": "assistant",
                                 "usage": {"input_tokens": 1, "cache_creation_input_tokens": 1, "cache_read_input_tokens": 999999}}}))
    else:
        lines.append(json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "no usage here"}]}}))
    jl.write_text("\n".join(lines) + "\n", encoding="utf-8")
    t = (time.time() if now is None else now) - age_days * 86400
    os.utime(jl, (t, t))
    return jl


def self_test():
    failures = []

    def check(cond, msg):
        if not cond:
            failures.append(msg)

    with tempfile.TemporaryDirectory(prefix="lqa_floor_selftest_") as tmp:
        now = time.time()
        proj = "C--x-InfinityOps"
        _write_sample(tmp, proj, "s1", "e1", "gsd-executor", 70000, 1, now=now)
        _write_sample(tmp, proj, "s1", "e2", "gsd-executor", 62000, 2, now=now)
        _write_sample(tmp, proj, "s2", "e3", "gsd-executor", 90000, 3, now=now)
        _write_sample(tmp, proj, "s2", "p1", "gsd-planner", 85567, 1, now=now)
        _write_sample(tmp, proj, "s2", "n1", "gsd-executor", 0, 1, with_usage=False, now=now)       # no usage -> skipped
        _write_sample(tmp, proj, "s3", "old1", "gsd-executor", 20000, 30, now=now)                  # outside the window
        _write_sample(tmp, "C--y-unrelated", "s9", "o1", "gsd-executor", 20000, 1, now=now)           # out of scope

        snap, _ = collect(tmp, 14, 6000, ["InfinityOps", "io-liveqa"], now=now)
        ex = snap["by_agent_type"].get("gsd-executor", {})
        check(ex.get("n") == 3, "executor n must be 3, got %s" % ex)
        check(ex.get("min") == 62000, "executor min must be 62000, got %s" % ex)
        check(ex.get("p50") == 70000, "executor p50 must be 70000, got %s" % ex)
        check(ex.get("max") == 90000, "executor max must be 90000, got %s" % ex)
        check(snap["skipped"] == 1, "exactly one skipped (no usage), got %s" % snap["skipped_detail"])
        check(snap["excluded_old"] == 1, "old file must be excluded, got %s" % snap["excluded_old"])
        check(snap["by_agent_type"].get("gsd-planner", {}).get("min") == 85567, "planner sample must be 85567 (first usage message, not the later one)")
        check(snap["excluded_out_of_scope"] == 1, "out-of-scope project must be excluded from the scoped table")
        allp = snap["by_agent_type_all_projects"].get("gsd-executor", {})
        check(allp.get("n") == 4 and allp.get("min") == 20000, "all-projects table must include the out-of-scope sample, got %s" % allp)
        blob = json.dumps(snap)
        for secret in ("SECRET-PROMPT-TEXT", "SECRET-ANSWER", "SECRET-SYNTH", "SECRET-DESCRIPTION", "no usage here"):
            check(secret not in blob, "snapshot leaked transcript text: %s" % secret)
        allowed = {"generated_at", "window_days", "scope", "samples_scanned", "skipped", "skipped_detail", "excluded_old",
                   "excluded_out_of_scope", "truncated_by_max_files", "unit", "by_agent_type", "by_agent_type_all_projects"}
        check(set(snap) <= allowed, "snapshot has unexpected keys: %s" % sorted(set(snap) - allowed))
        for tbl in (snap["by_agent_type"], snap["by_agent_type_all_projects"]):
            for v in tbl.values():
                check(set(v) == {"n", "min", "p50", "p90", "max"}, "per-type keys must be n,min,p50,p90,max, got %s" % sorted(v))

        # without a scope the unrelated project counts
        snap2, _ = collect(tmp, 14, 6000, None, now=now)
        check(snap2["by_agent_type"]["gsd-executor"]["n"] == 4, "unscoped executor n must be 4")

    if failures:
        for f in failures:
            print("SELF_TEST_FAIL: %s" % f)
        return 1
    print("SELF_TEST_OK executor n=3 min=62000 p50=70000 max=90000; skipped=1; old excluded; scope and no-text checked")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--since-days", type=int, default=14)
    ap.add_argument("--max-files", type=int, default=6000)
    ap.add_argument("--scope", default=None, help="comma-separated substrings of the project directory name")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--list", default=None, help="print per-sample rows (file, context, mtime) for one agent type to stdout")
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    scope = [s.strip() for s in a.scope.split(",") if s.strip()] if a.scope else None
    snap, rows = collect(Path(a.root), a.since_days, a.max_files, scope, list_type=a.list)
    text = json.dumps(snap, indent=2, sort_keys=False)
    print(text)
    if a.list:
        print("LIST %s (scoped, newest first):" % a.list)
        for name, ctx, mt in rows:
            print("  %s ctx=%d mtime=%s" % (name, ctx, mt))
    if not a.no_write:
        Path(a.out).write_text(text + "\n", encoding="utf-8")
        print("WROTE %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
