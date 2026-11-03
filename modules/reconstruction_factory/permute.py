"""Permuter: seeded random walk over the same operators (decomp-permuter style). Where `search` is systematic beam expansion, `permute` draws
operator sequences at random, accepts a step when the judge score does not get worse, and restarts from the best. Reproducible: the same seed gives
the same trajectory. Returns the first EXACT or the best seen with the iteration count."""
import random

from .operators import apply_all
from .search import h, score


def permute(factory, fn, skeleton, seed=0, iters=120, restarts=4):
    rng = random.Random(seed)
    s0 = score(factory, fn, skeleton)
    if s0 is None:
        return {"status": "SKELETON_DOES_NOT_COMPILE", "iters": 0, "text": skeleton}
    best = (s0["pct"], -s0["gap"], skeleton, [])
    if s0["exact"]:
        return {"status": "EXACT", "iters": 0, "text": skeleton, "path": [], "seed": seed}
    seen = {h(skeleton)}
    n = 0
    for _ in range(restarts):
        cur = best
        for _ in range(iters // restarts):
            opts = apply_all(cur[2])
            if not opts:
                break
            opn, t = opts[rng.randrange(len(opts))]
            if h(t) in seen:
                continue
            seen.add(h(t))
            n += 1
            s = score(factory, fn, t)
            if s is None:
                continue
            cand = (s["pct"], -s["gap"], t, cur[3] + [opn])
            if s["exact"]:
                return {"status": "EXACT", "iters": n, "text": t, "path": cand[3], "seed": seed}
            if cand[:2] >= cur[:2]:
                cur = cand
            if cand[:2] > best[:2]:
                best = cand
    return {"status": "NOT_FOUND", "iters": n, "text": best[2], "pct": best[0], "path": best[3], "seed": seed}
