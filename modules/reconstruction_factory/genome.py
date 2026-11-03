"""Strategy Genome: a search strategy as data -- {ops (ordered operator names, [] = use the causal plan), width, depth, budget} -- evolved by seeded
mutation/crossover against a training set of (function, skeleton). Fitness = (solved, -compiles) measured by real searches; the genome of the best
generation is returned with every evaluation, so a result is reproducible from (seed, population, generations). depth 0 is the degenerate baseline."""
import hashlib
import json
import random

from .operators import OPS
from .search import search

BOUNDS = {"width": (1, 6), "depth": (0, 4)}


def key(g):
    return hashlib.sha256(json.dumps(g, sort_keys=True).encode()).hexdigest()[:12]


def baseline():
    return {"ops": [], "width": 1, "depth": 0, "budget": 40}


def mutate(g, rng):
    g = json.loads(json.dumps(g))
    k = rng.choice(["width", "depth", "ops_add", "ops_drop", "ops_swap"])
    if k in BOUNDS:
        lo, hi = BOUNDS[k]
        g[k] = min(hi, max(lo, g[k] + rng.choice([-1, 1])))
    elif k == "ops_add":
        g["ops"] = g["ops"] + [rng.choice(sorted(OPS))]
    elif k == "ops_drop" and g["ops"]:
        g["ops"].pop(rng.randrange(len(g["ops"])))
    elif k == "ops_swap" and len(g["ops"]) > 1:
        i, j = rng.sample(range(len(g["ops"])), 2)
        g["ops"][i], g["ops"][j] = g["ops"][j], g["ops"][i]
    g["ops"] = list(dict.fromkeys(g["ops"]))
    return g


def crossover(a, b, rng):
    return {"ops": list(dict.fromkeys(a["ops"][: len(a["ops"]) // 2 + 1] + b["ops"][len(b["ops"]) // 2:])), "width": rng.choice([a["width"], b["width"]]),
            "depth": rng.choice([a["depth"], b["depth"]]), "budget": min(a["budget"], b["budget"])}


def fitness(factory, g, train):
    solved = comp = 0
    for fn, sk in train:
        r = search(factory, fn, sk, budget=g["budget"], width=g["width"], depth=g["depth"], ops=g["ops"] or None)
        solved += r["status"] == "EXACT"
        comp += r["compiles"]
    return (solved, -comp)


def evolve(factory, train, seed=0, pop=4, gens=2, budget=40):
    rng = random.Random(seed)
    base = dict(baseline(), budget=budget)
    cache = {}

    def fit(g):
        k = key(g)
        if k not in cache:
            cache[k] = fitness(factory, g, train)
        return cache[k]
    P = [base] + [mutate(dict(base, depth=2, width=3), rng) for _ in range(pop - 1)]
    for _ in range(gens):
        P.sort(key=lambda g: (fit(g), key(g)), reverse=True)
        elite = P[: max(2, pop // 2)]
        P = elite + [mutate(crossover(rng.choice(elite), rng.choice(elite), rng), rng) for _ in range(pop - len(elite))]
    P.sort(key=lambda g: (fit(g), key(g)), reverse=True)
    return {"best": P[0], "fitness": fit(P[0]), "baseline_fitness": fit(base), "evaluated": len(cache)}
