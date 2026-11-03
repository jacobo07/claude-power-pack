"""Beam search over single-site source rewrites from a skeleton. Candidates are scored by the judge (pct, then size gap); the first EXACT one is
returned (certification is a separate step: search finds, certify decides). Deterministic given (skeleton, budget, width). Every compile is
counted against `budget`; exhausting it returns BUDGET_EXHAUSTED with the best candidate and the Pareto front, never a pass."""
import hashlib

from . import judge as J
from .causal_diff import causal_diff
from .operators import apply_all
from .search_plan import plan as make_plan


def h(t):
    return hashlib.sha256(t.encode()).hexdigest()[:16]


def score(factory, fn, text, variant=None):
    r, c = factory.judge_text(fn, text, variant)
    if not c.ok:
        return None
    gap = J.size_gap(factory.target(fn), c.obj, factory.project.functions[fn]["symbols"])
    return {"pct": r["pct"], "exact": r["exact"], "gap": gap if gap is not None else 1 << 30, "obj": c.obj}


def pareto(items):
    """items: [(pct, gap, text, path)] -> non-dominated on (pct max, gap min)"""
    out = []
    for a in items:
        if not any((b[0] >= a[0] and b[1] <= a[1]) and (b[0] > a[0] or b[1] < a[1]) for b in items):
            out.append(a)
    return out


def search(factory, fn, skeleton, budget=200, width=4, depth=3, nsm=None, ops=None):
    sc0 = score(factory, fn, skeleton)
    if sc0 is None:
        return {"status": "SKELETON_DOES_NOT_COMPILE", "compiles": 0, "text": skeleton, "path": []}
    compiles = 1
    seen = {h(skeleton)}
    best = (sc0["pct"], sc0["gap"], skeleton, [])
    allc = [best]
    if sc0["exact"]:
        return {"status": "EXACT", "compiles": compiles, "text": skeleton, "path": [], "front": [best[:2]]}
    beam = [best]
    for _ in range(depth):
        nxt = []
        for (pct, gap, text, path) in beam:
            obj = score(factory, fn, text)
            primary = None
            if obj:
                primary = causal_diff(factory.adapter, factory.target(fn), obj["obj"], factory.project.functions[fn]["symbols"])["primary"]
            names = ops or make_plan(primary, nsm=nsm, fn=fn)
            for opn, t in apply_all(text, names):
                k = h(t)
                if k in seen:
                    continue
                seen.add(k)
                if compiles >= budget:
                    front = pareto([(a[0], a[1], a[2], a[3]) for a in allc])
                    return {"status": "BUDGET_EXHAUSTED", "compiles": compiles, "text": best[2], "pct": best[0], "path": best[3], "front": [x[:2] for x in front]}
                s = score(factory, fn, t)
                compiles += 1
                if s is None:
                    if nsm is not None:
                        nsm.record(fn, primary, opn, "COMPILE_FAILED")
                    continue
                cand = (s["pct"], s["gap"], t, path + [opn])
                allc.append(cand)
                if s["exact"]:
                    return {"status": "EXACT", "compiles": compiles, "text": t, "path": cand[3], "front": [cand[:2]]}
                if nsm is not None and s["pct"] <= pct:
                    nsm.record(fn, primary, opn, "NO_GAIN")
                nxt.append(cand)
                if (cand[0], -cand[1]) > (best[0], -best[1]):
                    best = cand
        if not nxt:
            break
        nxt.sort(key=lambda x: (-x[0], x[1], len(x[3])))
        beam = nxt[:width]
    front = pareto(allc)
    return {"status": "NOT_FOUND", "compiles": compiles, "text": best[2], "pct": best[0], "path": best[3], "front": [x[:2] for x in front]}
