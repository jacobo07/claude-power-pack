#!/usr/bin/env python3
"""Per-function view of a factory run (Owner ruling 2026-11-19: a one-function unit certifies with the flag arm it
matched). Writes OUT/ = symlinks to RUN's corpus.jsonl, sweep.jsonl, m2c/ + matched.tsv with one row per function at
objdiff 100% on ANY arm: `<id>\t<arm>`, the arm = the first arm in ORDER that hit 100.
usage: perfn.py RUN OUT [--order dol,ksr_sd0]"""
import argparse, json, os

ap = argparse.ArgumentParser()
ap.add_argument("run")
ap.add_argument("out")
ap.add_argument("--order", default="dol,ksr_sd0")
a = ap.parse_args()
order = a.order.split(",")
os.makedirs(a.out, exist_ok=True)
for n in ("corpus.jsonl", "sweep.jsonl", "m2c"):
    p = os.path.join(a.out, n)
    if not os.path.lexists(p):
        os.symlink(os.path.realpath(os.path.join(a.run, n)), p)
rows = []
for r in map(json.loads, open(os.path.join(a.run, "sweep.jsonl"))):
    if r.get("state") != "OK":
        continue
    arms = r.get("arms") or {}
    hit = [k for k in order if (arms.get(k) or {}).get("pct") == 100.0]
    hit += [k for k in arms if k not in order and (arms[k] or {}).get("pct") == 100.0]
    if hit:
        rows.append((r["id"], hit[0]))
rows.sort(key=lambda x: int(x[0].split(":")[1], 16))
with open(os.path.join(a.out, "matched.tsv"), "w", newline="\n") as w:
    for rid, arm in rows:
        w.write(f"{rid}\t{arm}\n")
print(json.dumps({"run": a.run, "out": a.out, "functions": len(rows)}))
