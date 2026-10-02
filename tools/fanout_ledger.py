#!/usr/bin/env python3
"""fanout_ledger.py -- causal fan-out reports over the usage index (C2) + provider quota (C1b).

Plan: vault/plans/cognitive-control-plane-2026-10-02.md section 11.
Storage and ancestry extraction live in tools/usage_index.py (schema v2); this module
only reads it. No model call, no timestamp-based linking.

Ancestry, as recorded by the harness:
  parent call   -> the promptId of the nearest preceding user line in its own file
  subagent call -> its <agent>.meta.json toolUseId -> the parent's Agent/Task tool_use
                   -> the promptId that parent call belonged to
  root class    -> the prompt's origin.kind / turnOrigin / promptSource, or the
                   session's mission title. Anything else is UNKNOWN, by type.

Root classes:
  HUMAN        typed or queued by the Owner (origin human, promptSource typed/queued)
  CONTINUATION model-side follow-up inside a session (task-notification, peer message)
  MISSION      a Ralph / gsd mission worker (session title m-<id>-eN)
  SDK          programmatic (claude -p / SDK entrypoint) that is not a known mission
  SYSTEM       injected by the harness (promptSource system)
  UNKNOWN      no ancestry recorded (older harness lines, broken links)

CLI:
  quota                              provider quota windows + live rejections
  summary --from ISO --to ISO        calls by root class, workflow, project, model policy
  top --from ISO --to ISO [--n 10]   largest prompt trees
  prompt PROMPT_ID                   one prompt's execution tree
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import usage_index as ux  # noqa: E402

ROOT_CLASSES = ("HUMAN", "CONTINUATION", "MISSION", "SDK", "SYSTEM", "UNKNOWN")
MISSION_TITLE_PREFIX = "m-"


def classify_root(kind, source, entrypoint, title) -> str:
    """Root class of one prompt from recorded fields only (see module doc)."""
    if title and title.startswith(MISSION_TITLE_PREFIX):
        return "MISSION"
    if kind == "human" or source in ("typed", "queued"):
        return "HUMAN"
    if kind in ("task-notification", "task_notification", "peer"):
        return "CONTINUATION"
    if kind == "sdk" or source == "sdk" or entrypoint == "sdk-cli":
        return "SDK"
    if source == "system":
        return "SYSTEM"
    return "UNKNOWN"


def workflow_of(agent_type) -> str:
    """Workflow family of a subagent type. None stays UNKNOWN."""
    if not agent_type:
        return "UNKNOWN"
    if agent_type.startswith("gsd-"):
        return "GSD:" + agent_type[4:]
    if agent_type.startswith("cpp-carrier"):
        return "CARRIER"
    return agent_type


def load_calls(con, start: float, end: float, prices: dict | None = None) -> list[dict]:
    """Every call in (start, end] with its resolved ancestry. Ancestry joins only
    along recorded ids; a missing link leaves root/prompt as None (UNKNOWN)."""
    prices = prices if prices is not None else ux.load_prices()
    q = """
    SELECT c.k, c.ts, c.model, c.is_sub, c.entrypoint, c.inp, c.cw, c.cw5, c.cw1, c.cr, c.out,
           c.prompt_id, c.file, f.title, s.agent_type, s.tool_use_id, s.depth,
           sp.prompt_id, sp.model_req, sp.session, sp.file
    FROM calls c
    LEFT JOIN files f ON f.path = c.file
    LEFT JOIN subagents s ON s.file = c.file
    LEFT JOIN spawns sp ON sp.tool_use_id = s.tool_use_id
    WHERE c.ts > ? AND c.ts <= ?"""
    prompts = {r[0]: r[1:] for r in con.execute(
        "SELECT p.prompt_id, p.kind, p.source, p.file, f.title, f.entrypoint "
        "FROM prompts p LEFT JOIN files f ON f.path = p.file")}
    out = []
    for (k, ts, model, is_sub, ep, inp, cw, cw5, cw1, cr, outp, pid, file, title, atype,
         tuid, depth, sp_pid, model_req, sp_sess, sp_file) in con.execute(q, (start, end)):
        root_pid = sp_pid if is_sub else pid
        pr = prompts.get(root_pid)
        if pr is None:
            root = "UNKNOWN"
        else:
            kind, source, pfile, ptitle, pep = pr
            root = classify_root(kind, source, pep, ptitle)
        p, _how = ux.price_for(model, prices)
        unsplit = max(0, cw - cw5 - cw1)
        usd = None if p is None else (inp * p["input"] + cw5 * p["cache_write_5m"]
                                      + (cw1 + unsplit) * p["cache_write_1h"]
                                      + cr * p["cache_read"] + outp * p["output"]) / 1e6
        project = Path(sp_file if (is_sub and sp_file) else file).parent.name
        if is_sub and not sp_file:
            project = Path(file).parents[2].name
        out.append({"k": k, "ts": ts, "model": model, "is_sub": bool(is_sub), "root": root,
                    "prompt": root_pid, "cache_read": cr, "output": outp, "usd": usd,
                    "agent_type": atype if is_sub else None,
                    "linked": (not is_sub) or bool(sp_pid) or bool(tuid and sp_file),
                    "model_req": (model_req or "inherit") if is_sub and sp_file else None,
                    "depth": depth, "project": project, "file": file})
    return out


def _agg(rows) -> dict:
    return {"calls": len(rows), "subagent_calls": sum(r["is_sub"] for r in rows),
            "cache_read": sum(r["cache_read"] for r in rows),
            "usd": round(sum(r["usd"] or 0 for r in rows), 2),
            "unpriced": sum(r["usd"] is None for r in rows)}


def summary(con, start: float, end: float) -> dict:
    rows = load_calls(con, start, end)
    by_root = defaultdict(list)
    by_wf = defaultdict(list)
    by_proj = defaultdict(list)
    by_policy = defaultdict(list)
    per_prompt = defaultdict(list)
    for r in rows:
        by_root[r["root"]].append(r)
        by_proj[r["project"]].append(r)
        if r["is_sub"]:
            by_wf[workflow_of(r["agent_type"])].append(r)
            by_policy[(r["model_req"] or "UNLINKED", r["model"])].append(r)
        if r["prompt"]:
            per_prompt[r["prompt"]].append(r)
    human = [len(v) for v in per_prompt.values() if v[0]["root"] == "HUMAN"]
    sub_rows = [r for r in rows if r["is_sub"]]
    return {
        "window": [ux._iso(start), ux._iso(end)],
        "total": _agg(rows),
        "by_root_class": {k: _agg(by_root[k]) for k in ROOT_CLASSES if by_root.get(k)},
        "human_prompt_fanout": ({"prompts": len(human), "median_calls": statistics.median(human),
                                 "p90_calls": sorted(human)[int(0.9 * (len(human) - 1))],
                                 "max_calls": max(human)} if human else "UNMEASURED"),
        "subagent_links": {"linked": sum(r["linked"] for r in sub_rows),
                           "unlinked": sum(not r["linked"] for r in sub_rows),
                           "depth": dict(Counter(r["depth"] for r in sub_rows))},
        "by_workflow": dict(sorted(((k, _agg(v)) for k, v in by_wf.items()),
                                   key=lambda kv: -kv[1]["cache_read"])[:15]),
        "by_project": dict(sorted(((k, _agg(v)) for k, v in by_proj.items()),
                                  key=lambda kv: -kv[1]["cache_read"])[:10]),
        "subagent_model_policy": {f"{req} -> {served}": _agg(v)
                                  for (req, served), v in sorted(by_policy.items(),
                                                                 key=lambda kv: -len(kv[1]))[:10]},
    }


def top(con, start: float, end: float, n: int = 10) -> list[dict]:
    per = defaultdict(list)
    for r in load_calls(con, start, end):
        if r["prompt"]:
            per[r["prompt"]].append(r)
    ranked = sorted(per.items(), key=lambda kv: -sum(r["cache_read"] for r in kv[1]))[:n]
    return [dict(prompt=p, root=v[0]["root"], project=v[0]["project"], **_agg(v),
                 agents=dict(Counter(workflow_of(r["agent_type"]) for r in v if r["is_sub"])))
            for p, v in ranked]


def prompt_tree(con, prompt_id: str) -> dict:
    """One prompt's execution tree: parent calls, then each spawn and its calls."""
    pr = con.execute("SELECT session, file, ts, kind, source FROM prompts WHERE prompt_id=?",
                     (prompt_id,)).fetchone()
    if pr is None:
        return {"prompt": prompt_id, "status": "UNKNOWN_PROMPT"}
    rows = [r for r in load_calls(con, 0, time.time() + 86400) if r["prompt"] == prompt_id]
    spawns = con.execute("SELECT tool_use_id, subagent_type, model_req, ts FROM spawns "
                         "WHERE prompt_id=? ORDER BY ts", (prompt_id,)).fetchall()
    children = []
    for tuid, stype, mreq, ts in spawns:
        files = [r[0] for r in con.execute("SELECT file FROM subagents WHERE tool_use_id=?",
                                           (tuid,))]
        crow = [r for r in rows if r["is_sub"] and r["file"] in files]
        children.append({"tool_use_id": tuid, "subagent_type": stype,
                         "model_requested": mreq or "inherit", "at": ux._iso(ts) if ts else None,
                         "transcript": "FOUND" if files else "NOT_INDEXED", **_agg(crow)})
    kind, source = pr[3], pr[4]
    return {"prompt": prompt_id, "session": pr[0], "at": ux._iso(pr[2]) if pr[2] else None,
            "root": classify_root(kind, source, None, None), "origin": kind, "source": source,
            "total": _agg(rows), "parent": _agg([r for r in rows if not r["is_sub"]]),
            "spawns": children}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("cmd", choices=["quota", "summary", "top", "prompt"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--db", default=str(ux.DEFAULT_DB))
    ap.add_argument("--from", dest="start", default=None)
    ap.add_argument("--to", dest="end", default=None)
    ap.add_argument("--n", type=int, default=10)
    a = ap.parse_args(argv)
    con = ux.connect(Path(a.db))
    now = time.time()
    start = ux._epoch(a.start) if a.start else now - 86400
    end = ux._epoch(a.end) if a.end else now
    if a.cmd == "quota":
        res = ux.quota_status(con, end)
    elif a.cmd == "summary":
        res = summary(con, start, end)
    elif a.cmd == "top":
        res = top(con, start, end, a.n)
    else:
        if not a.args:
            ap.error("prompt needs a PROMPT_ID")
        res = prompt_tree(con, a.args[0])
    print(json.dumps(res, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
