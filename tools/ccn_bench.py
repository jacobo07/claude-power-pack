#!/usr/bin/env python3
"""CCN Phase 2: matched concurrency benchmark.

Same 4 read-only questions (vault/benchmarks/ccn/rubric.json), same pinned commit, run as `claude -p`
sequentially, two at a time (P2) and four at a time (P4), two repeats each. Cost is measured from each run's
own transcript (assistant messages deduplicated by message id). Prints CAF(P) = cost(P) / cost(seq).

  ccn_bench.py run    --out DIR [--repeats 2] [--worktree DIR] [--budget-usd 40]
  ccn_bench.py report --out DIR
  ccn_bench.py cost   TRANSCRIPT            # price one transcript (also used by the gate)

Each (repeat, mode) cell gets its own --append-system-prompt nonce, so every cell starts with a cold
system-prompt cache and shares it only with the runs of the same cell. Runs are resumable: a run already in
runs.jsonl is skipped.
"""
import argparse
import concurrent.futures as cf
import json
import os
import re
import subprocess
import sys
import time
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ccn_census  # noqa: E402

RUBRIC = os.path.join(HERE, "..", "vault", "benchmarks", "ccn", "rubric.json")
PRICE = {"input": 3.0, "read": 0.30, "w5m": 3.75, "w1h": 6.0, "output": 15.0}  # Sonnet, $/Mtok
MODES = (("seq", 1), ("P2", 2), ("P4", 4))
RAM_NEED_MB = {"seq": 0, "P2": 2500, "P4": 4000}
RUN_TIMEOUT_S = 420


def price(usage):
    """API-equivalent dollars for one usage dict."""
    cc = usage.get("cache_creation") or {}
    w1h = cc.get("ephemeral_1h_input_tokens", 0) or 0
    w5m = cc.get("ephemeral_5m_input_tokens", 0) or 0
    total_w = usage.get("cache_creation_input_tokens", 0) or 0
    if total_w > w1h + w5m:  # breakdown absent or partial: price the remainder as 5m
        w5m += total_w - w1h - w5m
    return (usage.get("input_tokens", 0) * PRICE["input"] + usage.get("cache_read_input_tokens", 0) * PRICE["read"]
            + w5m * PRICE["w5m"] + w1h * PRICE["w1h"] + usage.get("output_tokens", 0) * PRICE["output"]) / 1e6


def transcript_cost(path):
    """Tokens, calls, tool calls and dollars from one transcript, deduplicated by message id."""
    by_id = {}
    tools = 0
    for rec in ccn_census.records(path):
        msg = rec.get("message") if isinstance(rec, dict) else None
        if not isinstance(msg, dict) or msg.get("role") != "assistant":
            continue
        mid = msg.get("id") or rec.get("uuid")
        u = msg.get("usage")
        if isinstance(u, dict):
            by_id[mid] = u  # later records for the same id carry the final output count
        for blk in msg.get("content") or []:
            if isinstance(blk, dict) and blk.get("type") == "tool_use":
                tools += 1
    t = {"fresh_input": 0, "cache_read": 0, "cache_write": 0, "output": 0}
    cost = 0.0
    for u in by_id.values():
        t["fresh_input"] += u.get("input_tokens", 0) or 0
        t["cache_read"] += u.get("cache_read_input_tokens", 0) or 0
        t["cache_write"] += u.get("cache_creation_input_tokens", 0) or 0
        t["output"] += u.get("output_tokens", 0) or 0
        cost += price(u)
    return dict(t, calls=len(by_id), tool_calls=tools, cost_usd=round(cost, 5))


def grade(question, answer):
    """True when every all_of regex matches the answer."""
    return all(re.search(p, answer or "", re.I) for p in question["all_of"])


def find_transcript(session_id, cwd):
    p = os.path.join(os.path.expanduser("~/.claude/projects"), ccn_census.encode_cwd(cwd), session_id + ".jsonl")
    return p if os.path.exists(p) else None


def run_one(q, mode, repeat, nonce, wt):
    sid = str(uuid.uuid4())
    cmd = ["claude", "-p", "--model", "sonnet", "--session-id", sid, "--allowedTools", "Read", "Grep", "Glob",
           "--max-budget-usd", "1.50", "--output-format", "json", "--append-system-prompt",
           "Benchmark cell " + nonce + ". Answer from the repository files only; be brief.", q["prompt"]]
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=wt, capture_output=True, text=True, timeout=RUN_TIMEOUT_S)
        out, rc = p.stdout, p.returncode
    except subprocess.TimeoutExpired as e:
        out, rc = (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or ""), -9
    wall = time.time() - t0
    answer = ""
    try:
        answer = str(json.loads(out).get("result", ""))
    except ValueError:
        pass
    tr = find_transcript(sid, wt)
    row = {"qid": q["id"], "mode": mode, "repeat": repeat, "session_id": sid, "rc": rc, "wall_s": round(wall, 1),
           "start": t0, "answer": answer[:600], "passed": grade(q, answer), "transcript": bool(tr)}
    if tr:
        row.update(transcript_cost(tr))
    return row


def load_runs(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def cmd_run(a):
    rub = json.load(open(RUBRIC, encoding="utf-8"))
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    runs_path = os.path.join(out, "runs.jsonl")
    done = {(r["repeat"], r["mode"], r["qid"]) for r in load_runs(runs_path)}
    skipped, spent = [], sum(r.get("cost_usd", 0) for r in load_runs(runs_path))
    sha = subprocess.run(["git", "-C", a.worktree, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    json.dump({"pinned_sha": sha, "worktree": a.worktree, "rubric": RUBRIC, "started": time.time()},
              open(os.path.join(out, "meta.json"), "w"))
    for rep in range(1, a.repeats + 1):
        for mode, width in MODES:
            cell = "r%d-%s-%s" % (rep, mode, uuid.uuid4().hex[:8])
            qs = [q for q in rub["questions"] if (rep, mode, q["id"]) not in done]
            if not qs:
                continue
            free = ccn_census.free_ram_mb()
            if free is not None and free < RAM_NEED_MB[mode]:
                skipped.append({"repeat": rep, "mode": mode, "reason": "SKIPPED_RAM", "free_mb": free})
                continue
            if spent > a.budget_usd:
                skipped.append({"repeat": rep, "mode": mode, "reason": "SKIPPED_BUDGET", "spent": spent})
                continue
            for i in range(0, len(qs), width):
                wave = qs[i:i + width]
                with cf.ThreadPoolExecutor(max_workers=len(wave)) as ex:
                    rows = list(ex.map(lambda q: run_one(q, mode, rep, cell, a.worktree), wave))
                with open(runs_path, "a", encoding="utf-8") as f:
                    for r in rows:
                        f.write(json.dumps(r) + "\n")
                        spent += r.get("cost_usd", 0)
                print("wave r%d %s %s: %s spent=$%.2f" % (rep, mode, [r["qid"] for r in rows],
                      [(r["rc"], r.get("cost_usd"), r["passed"]) for r in rows], spent), flush=True)
    json.dump(skipped, open(os.path.join(out, "skipped.json"), "w"))
    print("done spent=$%.2f skipped=%s" % (spent, skipped))
    return 0


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def analyze(rows):
    """Per-mode cost/wall/quality and CAF per repeat, noise band, verdict."""
    ok = [r for r in rows if "cost_usd" in r]
    res = {"modes": {}, "caf": {}, "caf_by_repeat": {}, "verdict": None}
    for m, _ in MODES:
        rs = [r for r in ok if r["mode"] == m]
        if not rs:
            continue
        reps = sorted({r["repeat"] for r in rs})
        res["modes"][m] = {
            "runs": len(rs), "repeats": reps,
            "cost_per_repeat": {rep: round(sum(r["cost_usd"] for r in rs if r["repeat"] == rep), 4) for rep in reps},
            "mean_cost_run": round(mean([r["cost_usd"] for r in rs]), 4),
            "cache_write": sum(r["cache_write"] for r in rs), "cache_read": sum(r["cache_read"] for r in rs),
            "fresh_input": sum(r["fresh_input"] for r in rs), "output": sum(r["output"] for r in rs),
            "calls": sum(r["calls"] for r in rs), "tool_calls": sum(r["tool_calls"] for r in rs),
            "wall_batch_s": round(mean([max(r["wall_s"] for r in rs if r["repeat"] == rep) if m == "P4" else
                                        sum(r["wall_s"] for r in rs if r["repeat"] == rep) for rep in reps]), 1),
            "quality": round(sum(1 for r in rs if r["passed"]) / len(rs), 3)}
    seq = res["modes"].get("seq")
    if not seq:
        res["verdict"] = "UNJUDGED (no sequential baseline)"
        return res
    for m in ("P2", "P4"):
        if m not in res["modes"]:
            continue
        per = [res["modes"][m]["cost_per_repeat"][r] / seq["cost_per_repeat"][r]
               for r in res["modes"][m]["cost_per_repeat"] if seq["cost_per_repeat"].get(r)]
        if not per:
            continue
        caf = res["modes"][m]["mean_cost_run"] / seq["mean_cost_run"]
        noise = (max(per) - min(per)) / 2 if len(per) > 1 else None
        res["caf"][m] = round(caf, 4)
        res["caf_by_repeat"][m] = {"values": [round(x, 4) for x in per], "noise": None if noise is None else round(noise, 4)}
        res["modes"][m]["wall_ratio_vs_seq"] = round(res["modes"][m]["wall_batch_s"] / seq["wall_batch_s"], 3)
    verdicts = {}
    for m, caf in res["caf"].items():
        noise = res["caf_by_repeat"][m]["noise"]
        if noise is None:
            verdicts[m] = "UNJUDGED (one repeat: no noise band)"
        elif abs(caf - 1) <= noise:
            verdicts[m] = "NEUTRAL"
        elif caf > 1.10:
            verdicts[m] = "AMPLIFIED"
        elif caf < 1:
            verdicts[m] = "REDUCED"
        else:
            verdicts[m] = "INCONCLUSIVE (1 < CAF <= 1.10, outside noise)"
    res["verdict"] = verdicts
    return res


def cmd_report(a):
    out = os.path.abspath(a.out)
    rows = load_runs(os.path.join(out, "runs.jsonl"))
    res = analyze(rows)
    skipped = json.load(open(os.path.join(out, "skipped.json"))) if os.path.exists(os.path.join(out, "skipped.json")) else []
    res["runs_total"], res["skipped"] = len(rows), skipped
    res["failed_runs"] = [{k: r[k] for k in ("qid", "mode", "repeat", "rc")} for r in rows if r["rc"] != 0 or "cost_usd" not in r]
    json.dump(res, open(os.path.join(out, "results.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--out", required=True)
    r.add_argument("--repeats", type=int, default=2)
    r.add_argument("--worktree", required=True)
    r.add_argument("--budget-usd", type=float, default=40.0)
    rp = sub.add_parser("report")
    rp.add_argument("--out", required=True)
    c = sub.add_parser("cost")
    c.add_argument("transcript")
    a = ap.parse_args(argv)
    if a.cmd == "run":
        return cmd_run(a)
    if a.cmd == "report":
        return cmd_report(a)
    print(json.dumps(transcript_cost(a.transcript)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
