#!/usr/bin/env python3
"""Cognitive PGO (CDC C8): telemetry ranks the next optimization.

    python tools/cognitive_pgo.py [--days 14] [--deadline 300] [--root DIR] [--out-dir DIR] [--max-files N]

Scans transcripts (newest first, all projects, mains + subagents) with session_autopsy's role classifier (C1) and writes
one JSON + one MD report: dominant tax by role / project / work class, tool n-gram motifs (n=2..4) ranked by cost x
recurrence, a debt register with interest = avoidable cost x recurrence, ROIC ranking, an irreducibility frontier with
reopen conditions, Exit-to-Determinism notes, and the unproductive-call corpus (calls with no progress, C4 definition,
exported with a causal class).

Honesty: the scan is bounded by --deadline; `coverage` says how many files were read vs found. A debt the transcripts
cannot see (Owner, Constitutional) is null (UNKNOWN), never 0. fix_cost values are declared ESTIMATES.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import session_autopsy as sa  # noqa: E402

EDITS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
SHELL = ("Bash", "PowerShell")
TRIP = 25   # C4 semantic-breaker trip_calls (vault/config/semantic-breaker.json); runs beyond it are unproductive
ALWAYS_WASTE = ("REREAD", "RECOVERY", "CONTEXT_FAULT")
OUT_DIR = HERE.parent / "vault" / "programs" / "cdc" / "evidence"

DEBT_MAP = {   # debt class -> roles whose tokens are avoidable cost of that class
    "Token": None,          # NO_PROGRESS_RUN calls only (waste roles are already counted under their own debt)
    "Context": ("REREAD", "CONTEXT_FAULT"),
    "Decision": ("PLAN",),
    "Proof": ("PROOF",),
    "Recovery": ("RECOVERY", "REPAIR"),
    "Coordination": ("CONTROL", "STATUS"),
    "Research": ("RESEARCH",),
    "Owner": (),
    "Constitutional": (),
}
# Share of the class's cost a deterministic primitive could plausibly remove, and the cost to build it in calls.
# Declared ESTIMATES (UNKNOWN until a primitive is measured); they only order the ROIC list.
AVOIDABLE = {"Token": 1.0, "Context": 0.8, "Decision": 0.1, "Proof": 0.3, "Recovery": 0.5,
             "Coordination": 0.7, "Research": 0.3}
FIX_CALLS = {"Token": 40, "Context": 25, "Decision": 60, "Proof": 30, "Recovery": 35, "Coordination": 15,
             "Research": 30}
REOPEN = {
    "NOVELTY": "reopen when a generator/template covers >=30 % of new files in a programme",
    "IMPLEMENT": "irreducible: the edit is the product; reopen only if edits repeat verbatim across sessions",
    "PLAN": "reopen when plan text repeats across sessions (cache as compiled unit)",
    "READ": "reopen when the same path set is read in >=3 sessions of one programme (precompute digest)",
    "Owner": "UNKNOWN: transcripts do not carry Owner waits; reopen with a pane-wait ledger",
    "Constitutional": "UNKNOWN: reopen when rule-citation events are logged per call",
}


def tool_label(name: str, inp: dict) -> str:
    """Tool name, with shell calls split into a stable verb class so n-grams mean something."""
    if name not in SHELL:
        return name
    cmd = inp.get("command", "") if isinstance(inp.get("command"), str) else ""
    if sa._PROOF.search(cmd):
        return name + ":proof"
    if sa._COMMIT.search(cmd):
        return name + ":commit"
    if sa._CONTROL.search(cmd):
        return name + ":control"
    return name + ":other"


def analyse_file(path: Path, tag: str) -> dict:
    items = sa._scan(path, tag)
    calls = [c for c in items if not c.get("epoch")]
    rows = sa.classify_calls(items)
    seq, per_call, unprod = [], [], []
    run, red = 0, False
    nprog = 0
    for c, r in zip(calls, rows):
        labels = [tool_label(n, i) for _, n, i in c["uses"]]
        prog = False
        for uid, n, inp in c["uses"]:
            res = c["results"].get(uid)
            cmd = inp.get("command", "") if isinstance(inp.get("command"), str) else ""
            if n in EDITS:
                prog = True
            elif n in SHELL and cmd:
                if sa._COMMIT.search(cmd) and res is not None and not sa._is_fail(res):
                    prog = True
                elif sa._PROOF.search(cmd) and res is not None:
                    bad = sa._is_fail(res)
                    if red and not bad:
                        prog = True
                    red = bad
        if prog:
            run, nprog = 0, nprog + 1
        else:
            run += 1
        cause = None
        if r["role"] in ALWAYS_WASTE:
            cause = r["role"]
        elif run > TRIP:
            cause = "NO_PROGRESS_RUN:" + r["role"]
        if cause:
            unprod.append({"tokens": r["tokens"], "cause": cause, "tools": labels, "run": run})
        for lb in labels:
            seq.append((lb, r["tokens"] / max(1, len(labels))))
        per_call.append((r["role"], r["tokens"]))
    return {"calls": per_call, "seq": seq, "unprod": unprod, "progress": nprog,
            "transitions": sum(sum(r["trans"].values()) for r in rows)}


def ngrams(seq: list, lo=2, hi=4):
    for n in range(lo, hi + 1):
        for i in range(len(seq) - n + 1):
            w = seq[i:i + n]
            yield tuple(x[0] for x in w), sum(x[1] for x in w)


def project_of(p: Path, root: Path) -> str:
    try:
        return p.relative_to(root).parts[0]
    except ValueError:
        return "?"


def collect(root: Path, days: float, deadline: float, max_files: int | None) -> tuple[list[Path], list[Path]]:
    cut = time.time() - days * 86400
    found = []
    for dp, _dn, fn in os.walk(root):
        for f in fn:
            if f.endswith(".jsonl"):
                p = Path(dp) / f
                try:
                    if p.stat().st_mtime >= cut:
                        found.append(p)
                except OSError:
                    pass
    seen, uniq = set(), []          # junctions/symlinks expose one project twice; count each real file once
    for p in sorted(found, key=lambda p: -p.stat().st_mtime):
        try:
            k = os.path.normcase(os.path.realpath(p))
        except OSError:
            k = str(p)
        if k not in seen:
            seen.add(k)
            uniq.append(p)
    found = uniq
    return found, found[:max_files] if max_files else found


def build(root: Path, days=14.0, deadline_s=300.0, max_files=None) -> dict:
    t0 = time.time()
    found, todo = collect(root, days, deadline_s, max_files)
    role_t, proj_t, class_t = Counter(), Counter(), Counter()
    role_n = Counter()
    motif_cost, motif_n, motif_sessions = Counter(), Counter(), defaultdict(set)
    debt_cost, debt_sess = Counter(), defaultdict(set)
    corpus, read = [], 0
    total = 0
    for p in todo:
        if time.time() - t0 > deadline_s:
            break
        tag = "sub:" + p.stem if "subagents" in p.parts else "main"
        try:
            a = analyse_file(p, tag)
        except Exception:      # a malformed transcript must not kill the report
            continue
        read += 1
        sid = p.stem
        proj = project_of(p, root)
        cls = "BUILD" if a["progress"] else "INVESTIGATE"
        for role, tok in a["calls"]:
            role_t[role] += tok
            role_n[role] += 1
            proj_t[proj] += tok
            class_t[cls] += tok
            total += tok
            for dc, roles in DEBT_MAP.items():
                if roles and role in roles:
                    debt_cost[dc] += tok
                    debt_sess[dc].add(sid)
        for u in a["unprod"]:
            if u["cause"].startswith("NO_PROGRESS_RUN"):
                debt_cost["Token"] += u["tokens"]
                debt_sess["Token"].add(sid)
            corpus.append({"session": sid, "project": proj, **u})
        seen = set()
        for g, c in ngrams(a["seq"]):
            motif_cost[g] += c
            motif_n[g] += 1
            seen.add(g)
        for g in seen:
            motif_sessions[g].add(sid)
    motifs = [{"motif": " > ".join(g), "n": len(g), "occurrences": motif_n[g], "sessions": len(motif_sessions[g]),
               "tokens": int(motif_cost[g]), "rank_score": int(motif_cost[g]) * len(motif_sessions[g])}
              for g in motif_cost if motif_n[g] >= 3]
    motifs.sort(key=lambda m: -m["rank_score"])
    debts = []
    for dc in DEBT_MAP:
        cost = debt_cost.get(dc)
        rec = len(debt_sess[dc])
        if dc in ("Owner", "Constitutional"):
            debts.append({"debt": dc, "cost_tokens": None, "recurrence": None, "interest": None,
                          "roic": None, "status": "UNKNOWN"})
            continue
        avoid = int((cost or 0) * AVOIDABLE[dc])
        interest = avoid * rec
        debts.append({"debt": dc, "cost_tokens": int(cost or 0), "avoidable_tokens": avoid, "recurrence": rec,
                      "interest": interest, "fix_calls_estimate": FIX_CALLS[dc],
                      "roic": interest / FIX_CALLS[dc], "status": "MEASURED"})
    debts.sort(key=lambda d: -(d["roic"] or -1))
    frontier = [{"item": k, "tokens": (int(role_t[k]) if k in role_t else None), "reopen": v} for k, v in REOPEN.items()
                if k in role_t or k in ("Owner", "Constitutional")]
    cause = Counter()
    ctok = Counter()
    for u in corpus:
        cause[u["cause"]] += 1
        ctok[u["cause"]] += u["tokens"]
    exit_notes = []
    for m in motifs[:10]:
        det = ("deterministic: one script runs the command and returns a digest" if "proof" in m["motif"]
               else "deterministic: batch the reads / return a digest" if m["motif"].startswith("Read")
               else "candidate: check for a pure function of the previous result")
        exit_notes.append({"motif": m["motif"], "note": det})
    return {"generated": time.strftime("%Y-%m-%dT%H:%M:%S"), "days": days,
            "coverage": {"found": len(found), "read": read, "complete": read == len(found),
                         "elapsed_s": round(time.time() - t0, 1)},
            "processed_tokens": total,
            "by_role": {k: {"tokens": int(v), "calls": role_n[k], "share": v / total if total else None}
                        for k, v in role_t.most_common()},
            "by_project": {k: int(v) for k, v in proj_t.most_common(15)},
            "by_work_class": {k: int(v) for k, v in class_t.items()},
            "motifs": motifs[:40], "proof_motifs": [m for m in motifs if "proof" in m["motif"]][:20], "debt_register": debts, "roic_ranking": [d["debt"] for d in debts],
            "frontier": frontier, "exit_to_determinism": exit_notes,
            "unproductive": {"calls": len(corpus), "tokens": int(sum(ctok.values())),
                             "by_cause": {k: {"calls": cause[k], "tokens": int(ctok[k])} for k in cause}},
            "_corpus": corpus}


def render_md(r: dict) -> str:
    L = ["# Cognitive PGO report (CDC C8)", "",
         f"Window {r['days']} d; read {r['coverage']['read']}/{r['coverage']['found']} transcripts "
         f"({'complete' if r['coverage']['complete'] else 'PARTIAL, newest first'}); {r['processed_tokens']:,} processed tokens.", "",
         "## Dominant tax by role", "| role | calls | tokens | share |", "|---|---|---|---|"]
    for k, v in r["by_role"].items():
        L.append(f"| {k} | {v['calls']} | {v['tokens']:,} | {(v['share'] or 0):.1%} |")
    L += ["", "## By project (top)"] + [f"- {k}: {v:,}" for k, v in r["by_project"].items()]
    L += ["", "## By work class"] + [f"- {k}: {v:,}" for k, v in r["by_work_class"].items()]
    L += ["", "## Motifs (tool n-grams, rank = tokens x sessions)", "| motif | occ | sessions | tokens |", "|---|---|---|---|"]
    for m in r["motifs"][:15]:
        L.append(f"| {m['motif']} | {m['occurrences']} | {m['sessions']} | {m['tokens']:,} |")
    L += ["", "## Proof-run motifs"] + [f"- {m['motif']}: {m['occurrences']} occ, {m['sessions']} sessions, {m['tokens']:,} tok" for m in r["proof_motifs"][:6]]
    L += ["", "## Debt register (interest = avoidable x recurrence; ROIC = interest / est. fix calls)",
          "| debt | cost | avoidable | sessions | interest | ROIC | status |", "|---|---|---|---|---|---|---|"]
    for d in r["debt_register"]:
        if d["status"] == "UNKNOWN":
            L.append(f"| {d['debt']} | UNKNOWN | - | - | - | - | UNKNOWN |")
        else:
            L.append(f"| {d['debt']} | {d['cost_tokens']:,} | {d['avoidable_tokens']:,} | {d['recurrence']} | "
                     f"{d['interest']:,} | {d['roic']:,.0f} | MEASURED (fix/avoidable ESTIMATE) |")
    L += ["", "## Irreducibility frontier"] + [f"- {f['item']} ({(str(format(f['tokens'], ',')) + ' tok') if f['tokens'] is not None else 'UNKNOWN'}): {f['reopen']}" for f in r["frontier"]]
    L += ["", "## Exit to determinism"] + [f"- {e['motif']}: {e['note']}" for e in r["exit_to_determinism"]]
    u = r["unproductive"]
    L += ["", f"## Unproductive-call corpus: {u['calls']} calls, {u['tokens']:,} tokens"]
    L += [f"- {k}: {v['calls']} calls, {v['tokens']:,} tok" for k, v in sorted(u["by_cause"].items(), key=lambda kv: -kv[1]["tokens"])]
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--days", type=float, default=14)
    ap.add_argument("--deadline", type=float, default=300)
    ap.add_argument("--root", default=str(Path.home() / ".claude" / "projects"))
    ap.add_argument("--out-dir", default=str(OUT_DIR))
    ap.add_argument("--max-files", type=int)
    a = ap.parse_args(argv)
    r = build(Path(a.root), a.days, a.deadline, a.max_files)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    corpus = r.pop("_corpus")
    (out / "cognitive-pgo.json").write_text(json.dumps(r, indent=1), encoding="utf-8")
    (out / "cognitive-pgo.md").write_text(render_md(r), encoding="utf-8")
    with open(out / "unproductive-corpus.jsonl", "w", encoding="utf-8") as fh:
        for u in corpus:
            fh.write(json.dumps(u) + "\n")
    print(f"read {r['coverage']['read']}/{r['coverage']['found']} unproductive {r['unproductive']['calls']} -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

