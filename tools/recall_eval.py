#!/usr/bin/env python3
"""Recall eval: measure Prompt Recall against a labelled query set it did not write.

Labels live in vault/evals/recall/queries.jsonl. Each positive query names the files that
should appear in the top 5 ("mem:<file>" = a power-pack memory, "pp:<rel>" = a path under
the power-pack root, anything else = a substring of the hit path). Negatives expect nothing.

A label is checked against the disk before it is scored: a named file must exist, and a
`rule_id` must occur in at least one named file. A label that fails is INVALID, reported and
left out of every rate. That keeps a stale label from reading as a recall miss.

Every miss is classified by looking at the index, never by guessing:
  source-not-indexed  no expected file is in the index's files table
  abstained           fewer than 2 usable query terms, recall returns nothing by design
  term-gate           the expected chunk is indexed but holds fewer query terms than a hit needs
  ranking             the expected chunk passes the term gate but ranks below the top 5

The live index is never queried in place: it is copied with the sqlite backup API from a
read-only connection, so a refresh running beside us is neither blocked nor raced.

    python tools/recall_eval.py --label baseline            # live snapshot
    python tools/recall_eval.py --db <file> --label fixture  # any index
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sqlite3
import statistics
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modules.gsd_x import recall  # noqa: E402

HOME = Path.home()
LIVE_PP = HOME / ".claude" / "skills" / "claude-power-pack"
PP_CWD = str(LIVE_PP)
PP_MEM = HOME / ".claude" / "projects" / recall.project_scope(PP_CWD) / "memory"
QUERIES = ROOT / "vault" / "evals" / "recall" / "queries.jsonl"
OUT_DIR = ROOT / "vault" / "evals" / "recall"


def norm(p: str) -> str:
    return str(p).replace("\\", "/").lower()


def resolve(label: str, pp_root: Path, mem_dir: Path):
    """(substring used to match a hit path, file on disk or None for a pure substring)."""
    if label.startswith("mem:"):
        f = mem_dir / label[4:]
        return norm("memory/" + label[4:]), f
    if label.startswith("pp:"):
        return norm(label[3:]), pp_root / label[3:]
    return norm(label), None


def validate(q: dict, pp_root: Path, mem_dir: Path) -> str:
    """'' when the label is sound, else why it is not."""
    files = []
    for lab in q.get("expect", []):
        _, f = resolve(lab, pp_root, mem_dir)
        if f is not None:
            if f.is_file():
                files.append(f)
    named = [lab for lab in q.get("expect", []) if resolve(lab, pp_root, mem_dir)[1] is not None]
    if named and not files:
        return "no expected file exists: " + ", ".join(named)
    rid = q.get("rule_id")
    if rid and not any(rid in f.read_text(encoding="utf-8-sig", errors="replace") for f in files):
        return "rule id %s not found in any expected file" % rid
    return ""


def snapshot(src: Path) -> Path:
    """Copy the index through a read-only connection; the live file is never opened for write."""
    dst = Path(tempfile.mkdtemp(prefix="recall_eval_")) / "recall.db"
    s = sqlite3.connect("file:%s?mode=ro" % src.as_posix(), uri=True, timeout=5.0)
    d = sqlite3.connect(str(dst))
    try:
        s.backup(d)
    finally:
        s.close()
        d.close()
    return dst


def classify_miss(con, q: dict, subs: list) -> str:
    paths = [r[0] for r in con.execute("SELECT path FROM files")]
    indexed = [p for p in paths if any(s in norm(p) for s in subs)]
    if not indexed:
        return "source-not-indexed"
    terms = recall.select_terms(con, recall.prompt_terms(q["q"]))
    if len(terms) < 2:
        return "abstained"
    need = min(len(terms), max(recall.MIN_MATCHED, math.ceil(0.3 * len(terms))))
    best = 0
    for p in indexed:
        for title, body in con.execute("SELECT title, body FROM chunks WHERE path=?", (p,)):
            hay = set(recall._WORD.findall(recall.fold(title + " " + body)))
            best = max(best, sum(1 for t in terms if t in hay))
    return "term-gate" if best < need else "ranking"


def evaluate(db: Path, queries: list, pp_root: Path = LIVE_PP, mem_dir: Path = PP_MEM,
             default_cwd: str = PP_CWD) -> dict:
    rows, lat = [], []
    con = sqlite3.connect(str(db))
    try:
        for q in queries:
            row = {"id": q["id"], "lang": q.get("lang"), "domain": q.get("domain"),
                   "negative": bool(q.get("negative"))}
            why = validate(q, pp_root, mem_dir)
            if why:
                row.update(status="INVALID", why=why)
                rows.append(row)
                continue
            cwd = q.get("cwd") or default_cwd
            t0 = time.perf_counter()
            try:
                hits = recall.query(q["q"], cwd=cwd, db=db)
            except Exception as e:                       # counted, never swallowed into a pass
                row.update(status="ERROR", why=repr(e))
                rows.append(row)
                continue
            lat.append((time.perf_counter() - t0) * 1000)
            paths = [h["path"] for h in hits]
            here = norm("projects/" + recall.project_scope(cwd) + "/")
            row["hits"] = [{"path": h["path"], "kind": h["kind"]} for h in hits]
            row["foreign_memory"] = sum(1 for h in hits
                                        if h["kind"] == "memory" and here not in norm(h["path"]))
            row["stale"] = sum(1 for p in paths if not Path(p).exists())
            if row["negative"]:
                row["status"] = "FALSE_POSITIVE" if hits else "OK"
            else:
                subs = [resolve(lab, pp_root, mem_dir)[0] for lab in q["expect"]]
                ranks = [i + 1 for i, p in enumerate(paths) if any(s in norm(p) for s in subs)]
                row["rank"] = ranks[0] if ranks else None
                row["relevant_hits"] = len(ranks)
                row["status"] = "HIT" if ranks else "MISS"
                if not ranks:
                    row["miss_class"] = classify_miss(con, q, subs)
            rows.append(row)
    finally:
        con.close()
    return summarize(rows, lat)


def summarize(rows: list, lat: list) -> dict:
    pos = [r for r in rows if not r["negative"] and r["status"] in ("HIT", "MISS")]
    neg = [r for r in rows if r["negative"] and r["status"] in ("OK", "FALSE_POSITIVE")]
    scored = pos + neg
    returned = sum(len(r.get("hits", [])) for r in pos)
    misses = {}
    for r in pos:
        if r["status"] == "MISS":
            misses[r["miss_class"]] = misses.get(r["miss_class"], 0) + 1

    def rate(n, d):
        return round(n / d, 4) if d else None              # None = UNKNOWN, never 0

    lat_sorted = sorted(lat)
    m = {
        "positives_scored": len(pos),
        "negatives_scored": len(neg),
        "invalid_labels": sum(1 for r in rows if r["status"] == "INVALID"),
        "errors": sum(1 for r in rows if r["status"] == "ERROR"),
        "recall_at_5": rate(sum(1 for r in pos if r["status"] == "HIT"), len(pos)),
        "mrr": rate(sum(1 / r["rank"] for r in pos if r.get("rank")), len(pos)),
        # Only labelled files count as relevant, so this is a LOWER bound on precision.
        "labelled_precision_at_5_lower_bound": rate(sum(r.get("relevant_hits", 0) for r in pos), returned),
        "abstain_rate_positives": rate(sum(1 for r in pos if not r.get("hits")), len(pos)),
        "negative_false_positive_rate": rate(sum(1 for r in neg if r["status"] == "FALSE_POSITIVE"), len(neg)),
        "foreign_memory_hit_share": rate(sum(r.get("foreign_memory", 0) for r in scored),
                                         sum(len(r.get("hits", [])) for r in scored)),
        "stale_hit_share": rate(sum(r.get("stale", 0) for r in scored),
                                sum(len(r.get("hits", [])) for r in scored)),
        "latency_ms_p50": round(statistics.median(lat_sorted), 2) if lat_sorted else None,
        "latency_ms_p95": round(lat_sorted[min(len(lat_sorted) - 1, int(0.95 * len(lat_sorted)))], 2)
        if lat_sorted else None,
        "miss_classes": misses,
        "by_lang": {},
    }
    for lang in sorted({r["lang"] for r in pos if r["lang"]}):
        sub = [r for r in pos if r["lang"] == lang]
        m["by_lang"][lang] = {"n": len(sub), "recall_at_5": rate(sum(1 for r in sub if r["status"] == "HIT"), len(sub))}
    return {"metrics": m, "rows": rows}


def load(path: Path) -> list:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", help="index to measure (default: snapshot of the live index)")
    ap.add_argument("--queries", default=str(QUERIES))
    ap.add_argument("--label", required=True)
    ap.add_argument("--pp-root", default=str(LIVE_PP))
    ap.add_argument("--out", help="report path (default vault/evals/recall/report-<label>.json)")
    a = ap.parse_args(argv)
    src = Path(a.db) if a.db else recall.db_path()
    if not src.is_file():
        print("RECALL_EVAL UNKNOWN: no index at %s" % src)
        return 2
    db = src if a.db else snapshot(src)
    rep = evaluate(db, load(Path(a.queries)), pp_root=Path(a.pp_root))
    rep.update(label=a.label, index=str(src), snapshot=str(db) if not a.db else None,
               measured_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
               index_files=sqlite3.connect(str(db)).execute("SELECT count(*) FROM files").fetchone()[0])
    out = Path(a.out) if a.out else OUT_DIR / ("report-%s.json" % a.label)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(rep["metrics"], indent=1, ensure_ascii=False))
    print("report:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
