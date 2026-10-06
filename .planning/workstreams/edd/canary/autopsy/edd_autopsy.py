"""Deterministic autopsy of an EDD mission's paid model calls (read-only).

Reads every transcript under the mission's project dirs, dedupes calls by
message id, attributes each call to main/subagent, records the tools it
issued, and classifies it from tool shape alone. No model involved.
Usage: python3 edd_autopsy.py <out.json>
"""
import collections
import glob
import json
import re
import sys

ROOTS = glob.glob("/home/kobii/.claude/projects/-home-kobii-missions-edd*")


def classify(tools, cmds, text_only):
    names = set(tools)
    if names & {"Agent", "Task", "Workflow"}:
        return "SPAWN_OR_JOIN"
    if names & {"Skill", "TodoWrite", "TaskCreate", "TaskUpdate", "ToolSearch", "EnterWorktree", "ExitWorktree"}:
        return "CONTROL_LOOP"
    if names & {"Write", "Edit", "NotebookEdit"}:
        return "MUTATION"
    joined = " ".join(cmds)
    if names & {"Bash"}:
        if re.search(r"pytest|test_\w+\.py|mutation|bench", joined):
            return "TEST_OR_BENCH_CONTROL"
        if re.search(r"\bgit (commit|add)\b", joined):
            return "STATE_WRITE"
        if re.search(r"\bgit\b|gsd-tools|gsd_mission|state ", joined):
            return "STATE_READ"
        return "EVIDENCE_ACQUISITION"
    if names & {"Read", "Grep", "Glob", "WebFetch", "WebSearch"}:
        return "EVIDENCE_ACQUISITION"
    if text_only:
        return "NARRATIVE_OR_DECISION"
    return "UNKNOWN"


def main(out):
    files = sorted({f for r in ROOTS for f in glob.glob(r + "/**/*.jsonl", recursive=True)})
    calls = collections.OrderedDict()
    sub_prompt = {}
    for f in files:
        role = "sub:" + f.rsplit("/", 1)[-1][:-6] if "/subagents/" in f else "main"
        for line in open(f, encoding="utf-8", errors="replace"):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            m = r.get("message") or {}
            if r.get("type") == "user" and role != "main" and role not in sub_prompt:
                c = m.get("content")
                txt = c if isinstance(c, str) else " ".join(
                    b.get("text", "") for b in c or [] if isinstance(b, dict))
                sub_prompt[role] = (txt or "")[:240].replace("\n", " ")
            if r.get("type") != "assistant" or not m.get("id"):
                continue
            c = calls.setdefault(m["id"], {"role": role, "ts": r.get("timestamp"), "tools": [],
                                           "cmds": [], "text": 0, "usage": None, "model": m.get("model")})
            if m.get("usage"):
                c["usage"] = m["usage"]
            for b in m.get("content") or []:
                if b.get("type") == "tool_use":
                    c["tools"].append(b.get("name"))
                    inp = b.get("input") or {}
                    c["cmds"].append(str(inp.get("command") or inp.get("subagent_type") or inp.get("skill")
                                         or inp.get("file_path") or inp.get("pattern") or "")[:120])
                elif b.get("type") == "text":
                    c["text"] += len(b.get("text", ""))
    rows = []
    for mid, c in calls.items():
        u = c["usage"] or {}
        ctx = u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
        proc = ctx + u.get("output_tokens", 0)
        cat = classify(c["tools"], c["cmds"], not c["tools"])
        rows.append({"role": c["role"], "ts": c["ts"], "model": c["model"], "ctx": ctx, "out": u.get("output_tokens", 0),
                     "proc": proc, "cat": cat, "tools": c["tools"], "cmds": c["cmds"][:3]})
    agg = lambda key: {k: {"calls": len(v), "proc": sum(x["proc"] for x in v)}
                       for k, v in _group(rows, key).items()}
    summary = {
        "files": len(files), "calls": len(rows), "proc": sum(r["proc"] for r in rows),
        "first": rows and min(r["ts"] for r in rows if r["ts"]), "last": rows and max(r["ts"] for r in rows if r["ts"]),
        "by_cat": agg("cat"), "by_role": agg("role"), "by_model": agg("model"),
        "max_ctx": max((r["ctx"] for r in rows), default=0),
        "ctx_quartiles_main": _q([r["ctx"] for r in rows if r["role"] == "main"]),
        "sub_prompts": sub_prompt,
        "tool_counts": collections.Counter(t for r in rows for t in r["tools"]).most_common(),
    }
    json.dump({"summary": summary, "rows": rows}, open(out, "w"), indent=1)
    print(json.dumps({k: v for k, v in summary.items() if k != "sub_prompts"}, indent=1))


def _group(rows, key):
    g = collections.defaultdict(list)
    for r in rows:
        g[r[key]].append(r)
    return g


def _q(v):
    v = sorted(v)
    return [v[int(len(v) * p)] for p in (0, .25, .5, .75)] + [v[-1]] if v else []


if __name__ == "__main__":
    main(sys.argv[1])
