"""Frontier: which unresolved blocker, if removed, unlocks how many functions - and what a PLAN of removals unlocks IN TOTAL.
Rows: {fn, blockers:[id], callers:[fn]}. A function blocked by several removed blockers is counted ONCE in a projection (the union, never the sum);
per-blocker 'blocked' is a range [sole, all + transitive_high] because transitivity is not decidable from the object (pass-through assumption on the high side only).
The shuffle control destroys blocker<->function co-occurrence; it is reported, and a ranking that survives it is flagged as degree-driven, not structural."""
import collections
import random
import re

COST = {"type": (2, 4), "class": (3, 6), "residual": (1, 2)}      # blocker kind -> resolution units [lo, hi]
SEED = 28


def kind(b):
    return b.split(":", 1)[0]


def compute(rows):
    rid = {r["fn"]: r for r in rows if r["blockers"]}
    callers = {fn: [c for c in r.get("callers", []) if c in rid] for fn, r in rid.items()}
    by = collections.defaultdict(set)
    for fn, r in rid.items():
        for b in r["blockers"]:
            by[b].add(fn)

    def ancestors(f):
        seen, st = set(), [f]
        while st:
            for c in callers.get(st.pop(), []):
                if c not in seen:
                    seen.add(c)
                    st.append(c)
        seen.discard(f)
        return seen
    out = {}
    for b, fs in by.items():
        sole = {f for f in fs if len(rid[f]["blockers"]) == 1}
        th = set()
        for f in fs:
            th |= {a for a in ancestors(f) if a not in fs}
        lo, hi = COST.get(kind(b), (2, 4))
        out[b] = {"blocker": b, "blocked_direct": [len(sole), len(fs)], "blocked_transitive_high": len(th),
                  "blocked": [len(sole), len(fs) + len(th)], "cost": [lo, hi],
                  "score": [round(len(sole) / hi, 4), round((len(fs) + len(th)) / lo, 4)], "functions": sorted(fs), "sole": sorted(sole)}
    return out


def rank(fr):
    return sorted(fr.values(), key=lambda d: (-(d["score"][0] + d["score"][1]) / 2, -d["score"][1], d["blocker"]))


def project(rows, removed):
    """Functions fully unlocked (every blocker removed) and functions touched, each counted once. Returns (unlocked, touched)."""
    rm = set(removed)
    rid = {r["fn"]: set(r["blockers"]) for r in rows if r["blockers"]}
    return sorted(f for f, bs in rid.items() if bs <= rm), sorted(f for f, bs in rid.items() if bs & rm)


def plan(rows, k):
    """Greedy: at each step remove the blocker that newly unlocks the most functions (ties by name). -> [(blocker, newly_unlocked, cumulative_unlocked)]"""
    rid = {r["fn"]: set(r["blockers"]) for r in rows if r["blockers"]}
    removed, done, out = set(), set(), []
    for _ in range(k):
        best = None
        for b in sorted({b for bs in rid.values() for b in bs} - removed):
            gain = len({f for f, bs in rid.items() if bs <= removed | {b}} - done)
            if best is None or gain > best[1]:
                best = (b, gain)
        if best is None:
            break
        removed.add(best[0])
        done = {f for f, bs in rid.items() if bs <= removed}
        out.append((best[0], best[1], len(done)))
    return out


def shuffle_control(rows, n=20):
    """Reassign the blocker column at random (blocker degrees and per-function counts preserved) and recompute the transitive-high statistic of the top 5."""
    def stat(rs):
        tp = rank(compute(rs))[:5]
        return sum(d["blocked_transitive_high"] for d in tp) / max(1, len(tp))
    real = stat(rows)
    pairs = [(r["fn"], b) for r in rows for b in r["blockers"]]
    per = []
    for p in range(n):
        rng = random.Random(SEED + p)
        cols = [b for _, b in pairs]
        rng.shuffle(cols)
        nb = collections.defaultdict(set)
        for (f, _), b in zip(pairs, cols):
            nb[f].add(b)
        per.append(stat([{"fn": r["fn"], "blockers": sorted(nb.get(r["fn"], ())), "callers": r.get("callers", [])} for r in rows]))
    return {"real": round(real, 4), "shuffled_mean": round(sum(per) / n, 4), "shuffled_max": round(max(per), 4), "falls": real > max(per)}


def rows_from_project(factory, results):
    """Rows for a Factory: blockers = residual class + the ctx type/class names the reference source mentions; callers = functions whose source calls this one.
    `results` = {fn: residual dict} for functions that are NOT yet exact (exact ones carry no blocker and are absent)."""
    P = factory.project
    names = _ctx_names(P)
    src = {fn: factory.read_source(fn) for fn in P.names()}
    rows = []
    for fn, res in sorted(results.items()):
        if not res.get("residual_class"):
            continue
        bl = ["residual:" + res["residual_class"]] + ["type:" + n for n in sorted(names) if re.search(r"\b%s\b" % re.escape(n), src[fn])]
        callers = sorted(o for o, t in src.items() if o != fn and re.search(r"\b%s\s*\(" % re.escape(fn), t))
        rows.append({"fn": fn, "blockers": bl, "callers": callers})
    return rows


def _ctx_names(P):
    import os
    out = set()
    for d in P.include_dirs:
        for root, _, files in os.walk(d):
            for n in files:
                if n.endswith((".h", ".hpp")):
                    with open(os.path.join(root, n), errors="ignore") as fh:
                        t = fh.read()
                    out |= set(re.findall(r"\}\s*(\w+)\s*;", t)) | set(re.findall(r"\b(?:struct|class)\s+(\w+)\s*[{:]", t))
    return out
