#!/usr/bin/env python
"""carriage.py -- pillars P (verification), F/G (sibling re-reads), C-tools (schema residency). Zero model calls.

PRE-REGISTERED (written and committed before any figure below was computed):

Population: every transcript holding a D-W7 call in the usage index (read-only sqlite). Calls are the index's
rows (key `<message.id>|<requestId>`), positioned in transcript order by first appearance; ONLY calls inside D-W7
carry a price, so every numerator is inside the frozen D-W7 weighted denominator (3,325,101,725). Sidechain lines
are read (the KSR original skipped them, which would drop every subagent transcript).

Carriage (the KSR construction, `vault/audits/ksr_archaeology/scripts/ctx_dead.py`): a tool result of T tokens
(chars / 3.6, ESTIMATE) is resident from the call after its admission until the next compaction or file end. Each
resident in-window call prices it by that call's own mix: read part T x 0.1 x cache_read/ctx, write part
T x 2 x cache_write/ctx (ctx = input + cache_read + cache_write).

Decision inputs (each against the frozen 3 % of D-W7 weighted):
  P  verification = read+write carriage of results of shell commands that run a test or gate
     (`turns.shell_cat == "test"`, the H classifier's rule) + the issuing tool_use's own tokens x 5 (output price)
     when its call is in D-W7. The whole-turn weight of proof-class turns (H: 6.13 %) is reported as context only:
     it prices the turn's entire prefix, which any turn pays.
  F  sibling re-derivation = read+write carriage of Read results in a SUBAGENT transcript whose identity
     (normalized path, offset, limit, sha256 of the result text) already appeared in a Read result of an
     EARLIER-spawned sibling (same parent transcript). Reported beside it, not deciding: path-only matches
     (content may differ), and parent->child identical reads.
  G  reopened only if F >= 3 % with the identity boundary above (same inputs, same content hash).
  C-tools  schema residency = read+write carriage of ToolSearch results (deferred tool schemas loaded into context).
     Always-on built-in schemas are in the system prompt, not in any transcript: UNMEASURED here, named as such.

Also reported (calibration, not deciding): all tool-output carriage by tool name.

Modes:  --measure [--json OUT]    full D-W7 run
        --selftest                detector controls (planted duplicate found, differing content not found,
                                  test command tagged, non-test not tagged); exit 1 if any fails
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "ksr_cpp"))
import turns  # noqa: E402  (H's classifier rules, W_START/W_END, DB)

CPT = 3.6
DW7_WEIGHTED = turns.DW7_WEIGHTED
DW7_CALLS = turns.DW7_CALLS


def text_len_and_text(content) -> tuple[int, str]:
    if isinstance(content, str):
        return len(content), content
    parts = []
    n = 0
    for b in content or []:
        if isinstance(b, dict):
            if b.get("type") == "text":
                parts.append(b.get("text", ""))
                n += len(b.get("text", ""))
            else:
                s = json.dumps(b, default=str)
                n += len(s)
    return n, "\n".join(parts)


def scan(fp: str, priced: dict) -> dict:
    """Per-file carriage. `priced`: {index key: (inp, cr, cw)} for this file's D-W7 calls."""
    calls: list = []          # per positioned call: (read_rate, write_rate) or (0, 0) out of window
    pos: dict = {}
    bounds: list = []
    tools: dict = {}
    results: list = []        # (admit_pos, name, input, chars, text)
    issue_out = 0.0           # P: issuing tool_use tokens x 5 for in-window calls
    try:
        fh = open(fp, encoding="utf-8", errors="replace")
    except OSError:
        return {"unreadable": True}
    with fh:
        for raw in fh:
            try:
                o = json.loads(raw)
            except ValueError:
                continue
            if not isinstance(o, dict):
                continue
            if o.get("isCompactSummary") or (o.get("type") == "system" and o.get("subtype") == "compact_boundary"):
                bounds.append(len(calls))
            m = o.get("message") if isinstance(o.get("message"), dict) else {}
            content = m.get("content") if isinstance(m.get("content"), list) else []
            if o.get("type") == "assistant" and isinstance(m.get("usage"), dict):
                k = f"{m.get('id')}|{o.get('requestId')}"
                if k not in pos:
                    pos[k] = len(calls)
                    if k in priced:
                        inp, cr, cw = priced[k]
                        ctx = inp + cr + cw
                        calls.append((cr * 0.1 / ctx if ctx else 0.0, cw * 2 / ctx if ctx else 0.0))
                    else:
                        calls.append((0.0, 0.0))
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "tool_use":
                        inp_ = c.get("input") if isinstance(c.get("input"), dict) else {}
                        tools[c.get("id")] = (c.get("name"), inp_)
                        if k in priced and c.get("name") in turns.SHELL_TOOLS and \
                                turns.shell_cat(str(inp_.get("command", ""))) == "test":
                            issue_out += len(json.dumps(inp_)) / CPT * 5
            elif o.get("type") == "user":
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "tool_result":
                        name, inp_ = tools.get(c.get("tool_use_id"), ("?", {}))
                        n, txt = text_len_and_text(c.get("content"))
                        results.append((len(calls), name, inp_, n, txt))
    n = len(calls)
    rr, rw = [0.0], [0.0]
    for a, b in calls:
        rr.append(rr[-1] + a)
        rw.append(rw[-1] + b)
    by_tool = defaultdict(float)
    test_w = search_w = 0.0
    reads = []
    for ci, name, inp_, chars, txt in results:
        end = next((b for b in bounds if b > ci), n)
        lo, hi = min(ci, n), min(end, n)
        tok = chars / CPT
        w = tok * (rr[hi] - rr[lo]) + tok * (rw[hi] - rw[lo])
        by_tool[str(name)] += w
        if name in turns.SHELL_TOOLS and turns.shell_cat(str(inp_.get("command", ""))) == "test":
            test_w += w
        elif name == "ToolSearch":
            search_w += w
        elif name == "Read" and inp_.get("file_path"):
            p = os.path.normcase(os.path.normpath(str(inp_["file_path"])))
            ident = (p, inp_.get("offset"), inp_.get("limit"))
            reads.append((ident, hashlib.sha256(txt.encode("utf-8", "replace")).hexdigest(), w))
    return {"by_tool": dict(by_tool), "test_w": test_w, "issue_out": issue_out, "search_w": search_w,
            "reads": reads, "positioned": sum(1 for k in priced if k in pos)}


def sibling_rereads(groups: dict) -> dict:
    """groups: {parent: [(spawn_ts, [(ident, sha, w), ...]), ...]} -> weighted re-read sums.
    A read counts when the same (ident, sha) [identity] or ident [path-only] was read by an EARLIER-spawned
    sibling of the same parent."""
    ident_w = path_w = 0.0
    n_ident = 0
    for _parent, sibs in groups.items():
        seen_ident: set = set()
        seen_path: set = set()
        for ts, reads in sorted(sibs, key=lambda s: s[0]):
            mine_ident, mine_path = set(), set()
            for ident, sha, w in reads:
                if (ident, sha) in seen_ident:
                    ident_w += w
                    n_ident += 1
                if ident in seen_path:
                    path_w += w
                mine_ident.add((ident, sha))
                mine_path.add(ident)
            seen_ident |= mine_ident
            seen_path |= mine_path
    return {"identity_w": ident_w, "identity_n": n_ident, "path_only_w": path_w}


def measure(out_json: str | None) -> int:
    con = turns.ro_connect()
    rows = con.execute("SELECT k, file, inp, cr, cw FROM calls WHERE ts > ? AND ts <= ?",
                       (turns.W_START, turns.W_END)).fetchall()
    by_file = defaultdict(dict)
    for k, f, inp, cr, cw in rows:
        by_file[f][k] = (inp, cr, cw)
    spawn = {r[0]: (r[1], r[2]) for r in con.execute(
        "SELECT a.file, s.file, s.ts FROM subagents a JOIN spawns s ON s.tool_use_id = a.tool_use_id")}
    con.close()
    tot_tool = defaultdict(float)
    test_w = issue = search_w = 0.0
    positioned = unreadable = 0
    groups = defaultdict(list)
    parent_reads = {}
    t0 = datetime.now().timestamp()
    for i, (fp, priced) in enumerate(by_file.items()):
        if i % 200 == 0:
            print(f"[carriage] {i}/{len(by_file)} {datetime.now().timestamp() - t0:.0f}s", file=sys.stderr, flush=True)
        r = scan(fp, priced)
        if r.get("unreadable"):
            unreadable += 1
            continue
        positioned += r["positioned"]
        for k, v in r["by_tool"].items():
            tot_tool[k] += v
        test_w += r["test_w"]
        issue += r["issue_out"]
        search_w += r["search_w"]
        if fp in spawn:
            parent, ts = spawn[fp]
            groups[parent].append((ts or 0.0, r["reads"]))
        elif r["reads"]:
            parent_reads[fp] = {(ident, sha) for ident, sha, _w in r["reads"]}
    sib = sibling_rereads(groups)
    pc_w = 0.0
    for parent, sibs in groups.items():
        pr = parent_reads.get(parent, set())
        for _ts, reads in sibs:
            pc_w += sum(w for ident, sha, w in reads if (ident, sha) in pr)
    pct = lambda x: round(100 * x / DW7_WEIGHTED, 4)
    res = {
        "window": "D-W7", "denominator_weighted": DW7_WEIGHTED,
        "control": {"positioned_calls": positioned, "dw7_calls": DW7_CALLS,
                    "positioned_equals_dw7": positioned == DW7_CALLS, "files": len(by_file),
                    "unreadable": unreadable, "sibling_groups": len(groups),
                    "subagent_files_grouped": sum(len(v) for v in groups.values())},
        "P_verification_pct_DW7": pct(test_w + issue),
        "P_parts": {"result_carriage_pct": pct(test_w), "issuing_tool_use_pct": pct(issue)},
        "F_sibling_identity_reread_pct_DW7": pct(sib["identity_w"]),
        "F_parts": {"identity_rereads": sib["identity_n"], "path_only_pct": pct(sib["path_only_w"]),
                    "parent_to_child_identical_pct": pct(pc_w)},
        "C_tools_toolsearch_schema_pct_DW7": pct(search_w),
        "all_tool_output_carriage_pct_DW7": pct(sum(tot_tool.values())),
        "by_tool_pct_DW7": {k: pct(v) for k, v in sorted(tot_tool.items(), key=lambda kv: -kv[1])[:25]},
    }
    blob = json.dumps(res, indent=1, sort_keys=True)
    if out_json:
        Path(out_json).write_text(blob, encoding="utf-8", newline="\n")
    print("result_sha256", hashlib.sha256(blob.encode()).hexdigest())
    print(json.dumps({k: v for k, v in res.items() if k != "by_tool_pct_DW7"}))
    return 0 if res["control"]["positioned_equals_dw7"] else 1


def selftest() -> int:
    a = (("c:\\x\\a.py", None, None), "h1", 10.0)
    b_same = (("c:\\x\\a.py", None, None), "h1", 7.0)
    b_diff = (("c:\\x\\a.py", None, None), "h2", 5.0)
    found = sibling_rereads({"p": [(1.0, [a]), (2.0, [b_same])]})
    differ = sibling_rereads({"p": [(1.0, [a]), (2.0, [b_diff])]})
    other_parent = sibling_rereads({"p": [(1.0, [a])], "q": [(2.0, [b_same])]})
    checks = {
        "planted identical sibling re-read found": found["identity_w"] == 7.0 and found["identity_n"] == 1,
        "differing content not an identity re-read": differ["identity_w"] == 0.0 and differ["path_only_w"] == 5.0,
        "different parents never siblings": other_parent["identity_w"] == 0.0,
        "pytest tagged test": turns.shell_cat("python -m pytest tests/ -q") == "test",
        "gate tagged test": turns.shell_cat("python tools/test_cognitive_economy_program.py --pillar H") == "test",
        "ls not tagged test": turns.shell_cat("Get-ChildItem C:\\x") != "test",
    }
    for k, v in checks.items():
        print(f"  {'ok  ' if v else 'FAIL'} {k}")
    ok = all(checks.values())
    print(f"CARRIAGE_SELFTEST={'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--measure", action="store_true")
    ap.add_argument("--json")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.measure:
        return measure(a.json)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
